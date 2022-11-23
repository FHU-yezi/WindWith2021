from datetime import datetime

from peewee import DatabaseError
from yaml import SafeLoader
from yaml import load as yaml_load

from config_manager import config
from db_config import User
from exceptions import (QueueEmptyException, QueueFullException,
                        UserAlreadyExistsException, UserBannedException,
                        UserDataDoesNotReadyException, UserDataException,
                        UserDoesNotExistException)
from log_manager import AddRunLog

MAX_QUEUE_LENGTH = 100

# 将上一次未处理完的用户状态改为 1，即未处理
changed_lines = User.update(status=1, start_process_time=None).where(User.status == 2).execute()
if changed_lines:
    AddRunLog(2, f"有 {changed_lines} 个用户的数据未处理完，已重置其状态")
else:
    AddRunLog(4, "没有用户的数据未处理完")

banned_list = list(yaml_load(open("banned.yaml", "r"), Loader=SafeLoader))

queue_length = User.select().where(User.status == 1).count()  # 获取排队中用户数量


def AddToQueue(user_url: str, user_name: str) -> None:
    global queue_length
    if user_url in banned_list and config["auth/enable_banlist"]:
        raise UserBannedException(f"{user_url}已被封禁")
    elif not config["auth/enable_banlist"]:
        AddRunLog(2, f"用户 {user_url}（{user_name}）在封禁列表中，但由于配置文件设置，未对此用户进行拦截")
    if queue_length + 1 > MAX_QUEUE_LENGTH:  # 如果队列已满
        raise QueueFullException("队列已满，请稍后再试")
    try:
        User.create(user_url=user_url, user_name=user_name,
                    status=1, data_exported=False, add_time=datetime.now())
    except DatabaseError:  # 主键是 user_url，出错意味着用户已存在
        raise UserAlreadyExistsException(f"用户 {user_url} 已存在")
    else:
        queue_length += 1  # 增加队列长度


def GetQueueLength() -> int:
    return queue_length


def GetOneToProcess() -> User:
    global queue_length
    if queue_length == 0:
        raise QueueEmptyException("队列已空")
    user = User.select().where(User.status == 1).order_by(User.add_time).get()
    user.status = 2
    user.start_process_time = datetime.now()
    user.save()
    queue_length -= 1
    return user


def ProcessFinished(user_url: str) -> None:
    try:
        user = User.select().where(User.user_url == user_url).get()
    except Exception:  # 用户不存在
        raise UserDoesNotExistException(f"用户 {user_url} 不存在")
    else:
        user.status = 3
        user.finish_process_time = datetime.now()
        user.save()


def GetUserToShowSummary(user_url: str) -> User:
    try:
        user = User.select().where(User.user_url == user_url).get()
    except Exception:  # 用户不存在
        raise UserDoesNotExistException(f"用户 {user_url} 不存在")
    else:
        if user.status in (1, 2):
            raise UserDataDoesNotReadyException(f"用户 {user_url} 的数据未就绪")
        elif user.status == 3:  # 第一次查看年终总结
            user.status = 4
            user.first_show_summary_time = datetime.now()
            user.save()
            return user
        elif user.status == 4:  # 已经查看过年终总结
            return user
        elif user.status == 5:  # 用户状态异常
            if user.exception_description:
                raise UserDataException(user.exception_description)
            else:
                raise UserDataException("未知")


def GetUserToExportData(user_url: str) -> User:
    try:
        user = User.select().where(User.user_url == user_url).get()
    except Exception:  # 用户不存在
        raise UserDoesNotExistException(f"用户 {user_url} 不存在")
    else:
        if user.status in (1, 2):
            raise UserDataDoesNotReadyException(f"用户 {user_url} 的数据未就绪")
        elif user.status in (3, 4):
            if not user.data_exported:  # 第一次导出数据
                user.data_exported = True
                user.first_data_export_time = datetime.now()
                user.save()
            return user
        elif user.status == 5:  # 用户状态异常
            if user.exception_description:
                raise UserDataException(user.exception_description)
            else:
                raise UserDataException("未知")


def SetUserStatusFailed(user_url: str, exception_description: str = None) -> None:
    try:
        user = User.select().where(User.user_url == user_url).get()
    except Exception:  # 用户不存在
        raise UserDoesNotExistException(f"用户 {user_url} 不存在")
    else:
        user.status = 5
        user.exception_description = exception_description
        user.save()
        AddRunLog(4, f"已将用户 {user.user_url} 的状态设置为失败")
