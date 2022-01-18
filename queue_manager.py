from db_config import UserQueue
from datetime import datetime
from yaml import load as yaml_load
from yaml import SafeLoader
from peewee import DatabaseError
from exceptions import QueueFullException, UserAlreadyExistsException, UserBannedException, QueueEmptyException

MAX_QUEUE_LENGTH = 100

banned_list = [x for x in yaml_load(open("banned.yaml", "r"), Loader=SafeLoader)]

queue_length = UserQueue.select().where(UserQueue.status == 1).count()  # 获取排队中用户数量


def AddToQueue(user_url: str) -> None:
    global queue_length
    if user_url in banned_list:
        raise UserBannedException(f"{user_url}已被封禁")
    if queue_length + 1 > MAX_QUEUE_LENGTH:  # 如果队列已满
        raise QueueFullException("队列已满，请稍后再试")
    try:
        UserQueue.create(user_url=user_url, status=1, add_time=datetime.now())
    except DatabaseError:  # 主键是 user_url，出错意味着用户已存在
        raise UserAlreadyExistsException(f"用户 {user_url} 已存在")
    else:
        queue_length += 1  # 增加队列长度


def GetQueueLength() -> int:
    return queue_length


def GetOneFromQueue() -> UserQueue:
    global queue_length
    if queue_length == 0:
        raise QueueEmptyException("队列已空")
    user_queue = UserQueue.select().where(UserQueue.status == 1).order_by(UserQueue.add_time).get()
    user_queue.status = 2
    user_queue.start_process_time = datetime.now()
    user_queue.save()
    queue_length -= 1
    return user_queue
