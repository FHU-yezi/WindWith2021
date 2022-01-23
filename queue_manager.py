from datetime import datetime

from peewee import DatabaseError
from yaml import SafeLoader
from yaml import load as yaml_load

from db_config import UserQueue
from exceptions import (QueueEmptyException, QueueFullException,
                        UserAlreadyExistsException, UserBannedException,
                        UserDataDoesNotReadyException,
                        UserDoesNotExistException)

MAX_QUEUE_LENGTH = 100

banned_list = [x for x in yaml_load(open("banned.yaml", "r"), Loader=SafeLoader)]

queue_length = UserQueue.select().where(UserQueue.status == 1).count()  # 获取排队中用户数量


def AddToQueue(user_url: str, user_name: str) -> None:
    global queue_length
    if user_url in banned_list:
        raise UserBannedException(f"{user_url}已被封禁")
    if queue_length + 1 > MAX_QUEUE_LENGTH:  # 如果队列已满
        raise QueueFullException("队列已满，请稍后再试")
    try:
        UserQueue.create(user_url=user_url, user_name=user_name, status=1, add_time=datetime.now())
    except DatabaseError:  # 主键是 user_url，出错意味着用户已存在
        raise UserAlreadyExistsException(f"用户 {user_url} 已存在")
    else:
        queue_length += 1  # 增加队列长度


def GetQueueLength() -> int:
    return queue_length


def GetOneToProcess() -> UserQueue:
    global queue_length
    if queue_length == 0:
        raise QueueEmptyException("队列已空")
    user = UserQueue.select().where(UserQueue.status == 1).order_by(UserQueue.add_time).get()
    user.status = 2
    user.start_process_time = datetime.now()
    user.save()
    queue_length -= 1
    return user


def ProcessFinished(user_url: str) -> None:
    try:
        user = UserQueue.select().where(UserQueue.user_url == user_url).get()
    except Exception:  # 用户不存在
        raise UserDoesNotExistException(f"用户 {user_url} 不存在")
    else:
        user.status = 3
        user.finish_process_time = datetime.now()
        user.save()


def GetOneToShowSummary(user_url: str) -> UserQueue:
    try:
        user = UserQueue.select().where(UserQueue.user_url == user_url).get()
    except Exception:  # 用户不存在
        raise UserDoesNotExistException(f"用户 {user_url} 不存在")
    else:
        if user.status in (1, 2):
            raise UserDataDoesNotReadyException(f"用户 {user_url} 的数据未就绪")
        elif user.status == 4:  # 已经查看过年终总结
            return user
        else:
            user.status = 4
            user.first_show_summary_time = datetime.now()
            user.save()
            return user
