from collections import Counter
from datetime import datetime
from os import mkdir, path
from sys import platform as sys_platform
from threading import Thread
from time import sleep
from typing import Dict, List

import jieba
import jieba.posseg as pseg
from JianshuResearchTools.article import GetArticleText, GetArticleWordage
from JianshuResearchTools.convert import (ArticleSlugToArticleUrl,
                                          UserUrlToUserSlug)
from JianshuResearchTools.user import (GetUserAllArticlesInfo,
                                       GetUserAllBasicData,
                                       GetUserArticlesCount)
from pandas import DataFrame
from wordcloud import WordCloud
from yaml import dump as yaml_dump

from exceptions import QueueEmptyException
from log_service import AddRunLog
from queue_manager import GetOneToProcess, ProcessFinished

jieba.setLogLevel(jieba.logging.ERROR)  # 关闭 jieba 的日志输出
if sys_platform != "win32":
    AddRunLog(3, "已开启多进程分词")
    jieba.enable_parallel(2)
else:
    AddRunLog(2, "由于当前系统不支持，多进程分词已禁用")

with open("wordcloud_assets/stopwords.txt", "r", encoding="utf-8") as f:
    STOPWORDS = [x.replace("\n", "") for x in f.readlines()]  # 预加载停用词词库
AddRunLog(4, "加载停用词成功")

jieba.load_userdict("wordcloud_assets/hotwords.txt")  # 将热点词加入词库
AddRunLog(4, "加载热点词成功")


def GetUserArticleData(user_url: str) -> DataFrame:
    result = DataFrame()
    start_time = datetime(2021, 1, 1, 0, 0, 0)
    end_time = datetime(2021, 12, 31, 23, 59, 59)
    for item in GetUserAllArticlesInfo(user_url, count=50):  # 增加单次请求量，提高性能
        item_release_time = item["release_time"].replace(tzinfo=None)
        if item_release_time > end_time:  # 文章发布时间晚于 2021 年
            pass  # 文章是按照时间倒序排列的，此时不做任何处理
        elif item_release_time < start_time:  # 文章发布时间早于 2021 年
            if item["is_top"]:  # 置顶文章
                pass  # 置顶文章永远排在最前面，此时不做任何处理
            else:  # 非置顶文章
                break  # 非置顶文章的发布时间早于 2021 年，则不再继续查询
        else:  # 文章发布时间在 2021 年内
            item["wordage"] = GetArticleWordage(ArticleSlugToArticleUrl(item["aslug"]), disable_check=True)
            result = result.append(item, ignore_index=True, sort=False)  # 将新的文章追加到 DataFrame 中
    return result


def GetUserBasicData(user_url: str) -> Dict:
    # 处理 JRT 的数据错误
    result = {}
    data = GetUserAllBasicData(user_url)
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
    # 数据存在问题，暂时不获取
    # result["last_update_time"] = data["last_update_time"]
    result["next_anniversary_day"] = data["next_anniversary_day"]
    result["vip_type"] = data["vip_info"]["vip_type"]
    result["vip_expire_time"] = data["vip_info"]["expire_date"]
    return result


def GetWordcloud(articles_list: List[str], user_slug: str) -> None:
    allow_word_types = ("Ag", "a", "ad", "an", "dg", "g",
                        "i", "j", "l", "Ng", "n", "nr",
                        "ns", "nt", "nz", "tg", "vg", "v",
                        "vd", "vn", "un")
    words_count: Counter = Counter()
    for article_url in articles_list:
        cutted_text = pseg.cut(GetArticleText(article_url, disable_check=True))
        # 只保留非单字词，且这些词必须不在停用词列表里，并属于特定词性
        cutted_text = (x.word for x in cutted_text if len(x.word) > 1
                       and x.flag in allow_word_types and x.word not in STOPWORDS)
        words_count += Counter(cutted_text)
    wordcloud = WordCloud(font_path="wordcloud_assets/font.otf", width=1280, height=720,
                          background_color="white", max_words=100)
    # 筛选出现五次以上的词
    img = wordcloud.generate_from_frequencies({key: value for key, value in words_count.items() if value > 10})
    img.to_file(f"user_data/{user_slug}/wordcloud_{user_slug}.png")


def main():
    if not path.exists("user_data"):
        mkdir("user_data")

    while True:
        try:
            user = GetOneToProcess()
        except QueueEmptyException:
            sleep(0.3)  # 队列为空，等待一段时间
            continue
        else:
            user_slug = UserUrlToUserSlug(user.user_url)
            if not path.exists(f"user_data/{user_slug}"):  # 避免获取到中途时服务重启导致文件夹已存在报错
                mkdir(f"user_data/{user_slug}")

        AddRunLog(3, f"开始执行数据获取任务，user_slug：{user_slug}")

        AddRunLog(4, f"开始获取 {user.user_url}（{user.user_name}）的基础数据")
        basic_data = GetUserBasicData(user.user_url)
        with open(f"user_data/{user_slug}/basic_data_{user_slug}.yaml", "w", encoding="utf-8") as f:
            yaml_dump(basic_data, f, indent=4, allow_unicode=True)
        AddRunLog(4, f"获取 {user.user_url}（{user.user_name}）的基础数据完成")

        AddRunLog(4, f"开始获取 {user.user_url}（{user.user_name}）的文章数据")
        article_data = GetUserArticleData(user.user_url)
        article_data.to_csv(f"user_data/{user_slug}/article_data_{user_slug}.csv", index=False)
        AddRunLog(4, f"获取 {user.user_url}（{user.user_name}）的文章数据完成，共 {len(article_data)} 条")

        AddRunLog(4, f"开始为 {user.user_url}（{user.user_name}）生成词云图")
        GetWordcloud((ArticleSlugToArticleUrl(x) for x in list(article_data["aslug"])), user_slug)
        AddRunLog(4, f"为 {user.user_url}（{user.user_name}）生成词云图完成")

        ProcessFinished(user.user_url)  # 如果数据获取完整，就将用户状态改为 3，表示已完成数据获取
        AddRunLog(3, f"数据获取任务执行完毕，user_slug：{user_slug}")


def init():
    main_thread = Thread(target=main, daemon=True)  # 设置为守护线程，避免造成主线程无法退出
    main_thread.start()
