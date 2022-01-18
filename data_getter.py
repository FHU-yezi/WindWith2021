from datetime import datetime
from os import mkdir, path
from threading import Thread
from time import sleep
from typing import Dict

from JianshuResearchTools.convert import UserUrlToUserSlug
from JianshuResearchTools.user import (GetUserAllArticlesInfo,
                                       GetUserAllBasicData)
from pandas import DataFrame
from yaml import dump as yaml_dump

from exceptions import QueueEmptyException
from log_service import AddRunLog
from queue_manager import ProcessFinished, GetOneToProcess


def GetUserArticleData(user_url: str) -> DataFrame:
    result = []
    for part in GetUserAllArticlesInfo(user_url, count=50):  # 增加单次请求量，提高性能
        for item in part:
            if item["release_time"].replace(tzinfo=None) >= datetime(2021, 1, 1, 0, 0, 0):
                result.append(item)
        if part[-1]["release_time"].replace(tzinfo=None) >= datetime(2021, 1, 1, 0, 0, 0):
            break  # 如果某一项的时间早于 2021 年，则已经采集了所有 2021 年的文章
    return DataFrame(result)


def GetUserBasicData(user_url: str) -> Dict:
    return GetUserAllBasicData(user_url)


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
