from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime
from os import mkdir, path
from sys import platform as sys_platform
from threading import Thread
from time import sleep
from typing import Dict, List

import jieba
import jieba.posseg as pseg
from httpx import HTTPError
from JianshuResearchTools.article import GetArticleText, GetArticleWordage
from JianshuResearchTools.convert import (ArticleSlugToArticleUrl,
                                          UserUrlToUserSlug)
from JianshuResearchTools.user import (GetUserAllArticlesInfo,
                                       GetUserAllBasicData,
                                       GetUserArticlesCount)
from pandas import DataFrame
from wordcloud import WordCloud
from yaml import dump as yaml_dump

from config_manager import Config
from db_config import User
from exceptions import (GetUserArticleDataException, GetUserBasicDataException,
                        GetUserWordCloudException, QueueEmptyException)
from log_manager import AddRunLog
from queue_manager import GetOneToProcess, ProcessFinished, SetUserStatusFailed

jieba.setLogLevel(jieba.logging.ERROR)  # 关闭 jieba 的日志输出
if not Config()["perf/enable_jieba_parallel"]:
    AddRunLog(2, "由于配置文件设置，多进程分词已禁用")
elif sys_platform == "win32":
    AddRunLog(2, "由于当前系统不支持，多进程分词已禁用")
else:
    AddRunLog(3, "已开启多进程分词")
    jieba.enable_parallel(2)

if Config()["word_split/enable_stopwords"]:
    with open("wordcloud_assets/stopwords.txt", "r", encoding="utf-8") as f:
        STOPWORDS = [x.replace("\n", "") for x in f.readlines()]  # 预加载停用词词库
    AddRunLog(4, "加载停用词成功")
else:
    AddRunLog(2, "由于配置文件设置，停用词功能已禁用")

if Config()["word_split/enable_hotwords"]:
    jieba.load_userdict("wordcloud_assets/hotwords.txt")  # 将热点词加入词库
    AddRunLog(4, "加载热点词成功")
else:
    AddRunLog(2, "由于配置文件设置，热点词功能已禁用")

if not path.exists(f"{Config()['service/data_path']}/user_data"):
    mkdir(f"{Config()['service/data_path']}/user_data")


def GetUserArticleData(user_url: str) -> DataFrame:
    start_time = datetime(2021, 1, 1, 0, 0, 0)
    end_time = datetime(2021, 12, 31, 23, 59, 59)
    fail_times = 0

    while fail_times < 3:
        result = DataFrame()
        try:
            for item in GetUserAllArticlesInfo(user_url, count=50):  # 增加单次请求量，提高性能
                item_release_time = item["release_time"].replace(tzinfo=None)
                if item_release_time > end_time:  # 文章发布时间晚于 2021 年
                    pass  # 文章是按照时间倒序排列的，此时不做任何处理
                elif item_release_time < start_time:  # 文章发布时间早于 2021 年
                    if not item["is_top"]:
                        break  # 非置顶文章的发布时间早于 2021 年，则不再继续查询
                else:  # 文章发布时间在 2021 年内
                    try:
                        item["wordage"] = GetArticleWordage(ArticleSlugToArticleUrl(item["aslug"]), disable_check=True)
                    except IndexError as e:  # 极少数概率下会由于请求的文章状态异常导致报错，此时跳过该文章的信息获取
                        AddRunLog(2, f"获取 {user_url} 的文章：{ArticleSlugToArticleUrl(item['aslug'])} 信息时发生错误：{e}，已跳过该文章")
                        continue
                    else:
                        result = result.append(item, ignore_index=True, sort=False)  # 将新的文章追加到 DataFrame 中
        except HTTPError as e:
            fail_times += 1
            AddRunLog(2, f"获取 {user_url} 的文章信息时发生错误：{e}，这是第 {fail_times} 次出错，10 秒后重试")
            sleep(10)
            continue
        else:
            if len(result) == 0:
                raise GetUserArticleDataException("用户没有在 2021 年发布文章")
            return result
    raise GetUserBasicDataException("获取文章信息时连续三次失败")


def GetUserBasicData(user_url: str) -> Dict:
    # 处理 JRT 的数据错误
    fail_times = 0
    while fail_times < 3:
        result = {}
        try:
            data = GetUserAllBasicData(user_url)
        except HTTPError as e:
            fail_times += 1
            AddRunLog(2, f"获取 {user_url} 的基础信息时发生错误：{e}，这是第 {fail_times} 次出错，10 秒后重试")
            sleep(10)
            continue
        else:
            break
    else:  # 三次失败
        raise GetUserBasicDataException("获取基础信息时连续三次失败")

    result["id"] = data["articles_count"]["id"]
    result["slug"] = data["articles_count"]["slug"]
    result["url"] = data["url"]
    result["name"] = data["name"]
    result["gender"] = {0: "未知", 1: "男", 2: "女", 3: "未知"}[data["gender"]]
    result["avatar_url"] = data["articles_count"]["avatar"]
    result["background_image_url"] = data["articles_count"]["background_image"]
    result["FP_count"] = round(data["FP_count"], 2)
    result["FTN_count"] = round(data["FTN_count"], 2)
    result["FP / FTN"] = round(result["FP_count"] / result["FTN_count"], 2)
    result["assets_count"] = round(data["assets_count"], 2)
    result["followers_count"] = data["followers_count"]
    result["fans_count"] = data["fans_count"]
    result["likes_count"] = data["likes_count"]
    result["wordage"] = data["wordage"]
    result["articles_count"] = GetUserArticlesCount(user_url, disable_check=True)
    result["introduction_text"] = data["introduction_text"]
    result["badges_list"] = data["badges_list"]
    result["next_anniversary_day"] = data["next_anniversary_day"]
    result["vip_type"] = data["vip_info"]["vip_type"]
    result["vip_expire_time"] = data["vip_info"]["expire_date"]
    return result


def GetUserWordcloud(articles_list: List[str], user_slug: str) -> WordCloud:
    allow_word_types = ("Ag", "a", "ad", "an", "dg", "g",
                        "i", "j", "l", "Ng", "n", "nr",
                        "ns", "nt", "nz", "tg", "vg", "v",
                        "vd", "vn", "un")
    words_count: Counter = Counter()
    for article_url in articles_list:
        fail_times = 0
        while fail_times < 3:
            try:
                cutted_text = pseg.cut(GetArticleText(article_url, disable_check=True))
            except HTTPError as e:
                fail_times += 1
                AddRunLog(2, f"获取 {user_slug} 的文章内容时发生错误：{e}，这是第 {fail_times} 次出错，10 秒后重试")
                sleep(10)
                continue
            else:
                break
        else:  # 三次失败
            raise GetUserWordCloudException("获取文章内容时连续三次失败")

        # 只保留非单字词，且这些词必须不在停用词列表里，并属于特定词性
        cutted_text = (x.word for x in cutted_text if len(x.word) > 1
                       and x.flag in allow_word_types and x.word not in STOPWORDS)
        words_count += Counter(cutted_text)

    wordcloud = WordCloud(font_path="wordcloud_assets/font.otf", width=1280, height=720,
                          background_color="white", max_words=100)
    if words_count.most_common(1)[0][1] <= 10:  # 文章中的最高频词没有达到可生成词云的数量
        raise GetUserWordCloudException("用户文章中的最高频词没有达到可生成词云的数量")
    else:
        return wordcloud.generate_from_frequencies(
            {key: value for key, value in words_count.items() if value > 10}
        )


def GetDataJob(user: User):
    user_slug = UserUrlToUserSlug(user.user_url)

    if not path.exists(f"{Config()['service/data_path']}/user_data/{user_slug}"):  # 避免获取到中途时服务重启导致文件夹已存在报错
        mkdir(f"{Config()['service/data_path']}/user_data/{user_slug}")

    AddRunLog(3, f"开始执行 {user.user_url}（{user.user_name}）的数据获取任务")

    AddRunLog(4, f"开始获取 {user.user_url}（{user.user_name}）的基础数据")
    try:
        basic_data = GetUserBasicData(user.user_url)
    except GetUserBasicDataException as e:
        AddRunLog(1, f"获取 {user.user_url}（{user.user_name}）的基础数据时发生错误：{e}")
        SetUserStatusFailed(user.user_url, str(e))
        return  # 终止运行
    else:
        with open(f"{Config()['service/data_path']}/user_data/{user_slug}/basic_data_{user_slug}.yaml", "w", encoding="utf-8") as f:
            yaml_dump(basic_data, f, indent=4, allow_unicode=True)
        AddRunLog(4, f"获取 {user.user_url}（{user.user_name}）的基础数据完成")

    AddRunLog(4, f"开始获取 {user.user_url}（{user.user_name}）的文章数据")
    try:
        article_data = GetUserArticleData(user.user_url)
    except GetUserArticleDataException as e:
        AddRunLog(1, f"获取 {user.user_url}（{user.user_name}）的文章数据时发生错误：{e}")
        SetUserStatusFailed(user.user_url, str(e))
        return  # 终止运行
    else:
        article_data.to_csv(f"{Config()['service/data_path']}//user_data/{user_slug}/article_data_{user_slug}.csv", index=False)
        AddRunLog(4, f"获取 {user.user_url}（{user.user_name}）的文章数据完成，共 {len(article_data)} 条")

    AddRunLog(4, f"开始为 {user.user_url}（{user.user_name}）生成词云图")
    try:
        wordcloud_img = GetUserWordcloud((ArticleSlugToArticleUrl(x) for x in list(article_data["aslug"])), user_slug)
    except GetUserWordCloudException as e:
        AddRunLog(1, f"为 {user.user_url}（{user.user_name}）生成词云图时发生错误：{e}")
        SetUserStatusFailed(user.user_url, str(e))
        return  # 终止运行
    else:
        wordcloud_img.to_file(f"{Config()['service/data_path']}//user_data/{user_slug}/wordcloud_{user_slug}.png")
        AddRunLog(4, f"为 {user.user_url}（{user.user_name}）生成词云图成功")

    ProcessFinished(user.user_url)  # 如果数据获取完整，就将用户状态改为 3，表示已完成数据获取
    AddRunLog(3, f"{user.user_url}（{user.user_name}）的数据获取任务执行完毕")
    AddRunLog(4, f"{user.user_url}（{user.user_name}）的数据获取线程结束运行")


def main():
    pool = ThreadPoolExecutor(max_workers=Config()["perf/data_getters_max_count"], thread_name_prefix="data_getter-")
    futures = []
    AddRunLog(4, f"数据获取线程池创建成功，最大线程数：{Config()['perf/data_getters_max_count']}")
    while True:
        try:
            for user, future in futures[:]:  # 创建拷贝，防止删除元素导致迭代出错
                try:
                    exception_obj = future.exception(timeout=0)  # 获取数据获取线程引发的异常
                except TimeoutError:  # 该线程还未执行完毕
                    continue
                else:
                    if exception_obj:
                        AddRunLog(1, f"{user.user_url}（{user.user_name}）的数据获取线程中出现未捕获的异常：{exception_obj}")
                        SetUserStatusFailed(user.user_url, "数据获取过程中的未知异常")  # 将用户状态设置为失败
                    futures.remove((user, future))  # 将 Future 对象从列表中移除
            user = GetOneToProcess()
        except QueueEmptyException:
            sleep(0.3)  # 队列为空，等待一段时间
            continue
        else:
            future = pool.submit(GetDataJob, user)
            futures.append((user, future))
            AddRunLog(4, f"启动了新的数据获取线程：{user.user_url}（{user.user_name}）")


def init():
    data_getter_thread = Thread(target=main, daemon=True)  # 设置为守护线程，避免造成主线程无法退出
    data_getter_thread.start()
