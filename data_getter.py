from datetime import datetime
from os import mkdir, path
from threading import Thread
from time import sleep
from typing import Dict

from JianshuResearchTools.article import GetArticleWordage
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
    result["gender"] = {0: "未知", 1: "男", 2: "女"}[data["gender"]]
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
    result["last_update_time"] = data["last_update_time"]
    result["next_anniversary_day"] = data["next_anniversary_day"]
    result["vip_type"] = data["vip_info"]["vip_type"]
    result["vip_expire_date"] = data["vip_info"]["expire_date"]
    return result

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
            if not path.exists(user_slug):  # 避免获取到中途时服务重启导致文件夹已存在报错
                mkdir(f"user_data/{user_slug}")

        article_data = GetUserArticleData(user_url)
        article_data.to_csv(f"user_data/{user_slug}/article_data_{user_slug}.csv", index=False)
        basic_data = GetUserBasicData(user_url)
        with open(f"user_data/{user_slug}/basic_data_{user_slug}.yaml", "w", encoding="utf-8") as f:
            yaml_dump(basic_data, f, indent=4, allow_unicode=True)

        ProcessFinished(user_url)  # 如果数据获取完整，就将用户状态改为 3，表示已完成数据获取


def init():
    main_thread = Thread(target=main, daemon=True)  # 设置为守护线程，避免造成主线程无法退出
    main_thread.start()
    AddRunLog(3, "初始化数据获取主线程成功")