from collections import Counter
from datetime import datetime
from os import mkdir, path
from threading import Thread
from time import sleep
from typing import Dict, List
from wordcloud import WordCloud

import jieba
from JianshuResearchTools.article import GetArticleText, GetArticleWordage
from JianshuResearchTools.convert import (ArticleSlugToArticleUrl,
                                          UserUrlToUserSlug)
from JianshuResearchTools.user import (GetUserAllArticlesInfo,
                                       GetUserAllBasicData,
                                       GetUserArticlesCount)
from pandas import DataFrame
from yaml import dump as yaml_dump

from exceptions import QueueEmptyException
from log_service import AddRunLog
from queue_manager import GetOneToProcess, ProcessFinished

jieba.setLogLevel(jieba.logging.ERROR)  # 关闭 jieba 的日志输出

with open("wordcloud_assets/stopwords.txt", "r", encoding="utf-8") as f:
    STOPWORDS = [x.replace("\n", "") for x in f.readlines()]  # 预加载停用词词库

with open("wordcloud_assets/hotwords.txt", "r", encoding="utf-8") as f:
    for word in f.readlines():
        jieba.add_word(word.replace("\n", ""))  # 将热点词加入词库

def GetUserArticleData(user_url: str) -> DataFrame:
    result = []
    for part in GetUserAllArticlesInfo(user_url, count=50):  # 增加单次请求量，提高性能
        for item in part:
            if item["release_time"].replace(tzinfo=None) >= datetime(2021, 1, 1, 0, 0, 0):
                item["wordage"] = GetArticleWordage(ArticleSlugToArticleUrl(item["aslug"]))
                result.append(item)
        if part[-1]["release_time"].replace(tzinfo=None) >= datetime(2021, 1, 1, 0, 0, 0):
            break  # 如果某一项的时间早于 2021 年，则已经采集了所有 2021 年的文章
    return DataFrame(result)


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
    result["articles_count"] = GetUserArticlesCount(user_url)
    result["introduction_text"] = data["introduction_text"]
    result["badges_list"] = data["badges_list"]
    # 数据存在问题，暂时不获取
    # result["last_update_time"] = data["last_update_time"]
    result["next_anniversary_day"] = data["next_anniversary_day"]
    result["vip_type"] = data["vip_info"]["vip_type"]
    result["vip_expire_time"] = data["vip_info"]["expire_date"]
    return result


def GetWordcloud(articles_list: List[str], user_slug: str) -> None:
    words_count = Counter()
    for article_url in articles_list:
        cutted_text = jieba.cut(GetArticleText(article_url))
        cutted_text = (word for word in cutted_text if len(word) > 1 and word not in STOPWORDS)
        words_count += Counter(cutted_text)
    wordcloud = WordCloud(font_path="wordcloud_assets/font.otf", width=1920, height=1080, background_color="white")
    # 筛选出现五次以上的词
    img = wordcloud.generate_from_frequencies({key: value for key, value in words_count.items() if value > 5})
    img.to_file(f"user_data/{user_slug}/wordcloud_{user_slug}.png")

def main():
    if not path.exists("user_data"):
        mkdir("user_data")

    while True:
        try:
            user_url = GetOneToProcess()
        except QueueEmptyException:
            sleep(0.3)  # 队列为空，等待一段时间
            continue
        else:
            user_slug = UserUrlToUserSlug(user_url)
            if not path.exists(f"user_data/{user_slug}"):  # 避免获取到中途时服务重启导致文件夹已存在报错
                mkdir(f"user_data/{user_slug}")

        AddRunLog(3, f"开始执行数据获取任务，user_slug：{user_slug}")
        article_data = GetUserArticleData(user_url)
        article_data.to_csv(f"user_data/{user_slug}/article_data_{user_slug}.csv", index=False)
        GetWordcloud((ArticleSlugToArticleUrl(x) for x in list(article_data["aslug"])), user_slug)
        basic_data = GetUserBasicData(user_url)
        with open(f"user_data/{user_slug}/basic_data_{user_slug}.yaml", "w", encoding="utf-8") as f:
            yaml_dump(basic_data, f, indent=4, allow_unicode=True)

        ProcessFinished(user_url)  # 如果数据获取完整，就将用户状态改为 3，表示已完成数据获取
        AddRunLog(3, f"数据获取任务执行完毕，user_slug：{user_slug}")


def init():
    main_thread = Thread(target=main, daemon=True)  # 设置为守护线程，避免造成主线程无法退出
    main_thread.start()
    AddRunLog(3, "初始化数据获取主线程成功")
