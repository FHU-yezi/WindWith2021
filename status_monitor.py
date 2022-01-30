from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from typing import Dict, Union

from psutil import disk_usage, virtual_memory
from log_manager import AddRunLog

from config_manager import Config
from db_config import RunLog, User, ViewLog
from message_sender import SendErrorMessage, SendWarningMessage


def GetMemoryPercent():
    return round(virtual_memory().percent / 100, 2)


def GetDiskPercent():
    return round(disk_usage('/').percent / 100, 2)


def GetUserToProcessCount():
    return User.select().where(User.status == 1).count()


def GetViewsCount(time: int):
    return ViewLog.select().where(ViewLog.time > datetime.now() - timedelta(seconds=time)).count()


def GetWarnsCount(time: int):
    return RunLog.select().where(RunLog.time > datetime.now() - timedelta(seconds=time),
                                 RunLog.level == 2).count()


def GetErrorsCount(time: int):
    return RunLog.select().where(RunLog.time > datetime.now() - timedelta(seconds=time),
                                 RunLog.level == 1).count()


def GetCriticalsCount(time: int):
    return RunLog.select().where(RunLog.time > datetime.now() - timedelta(seconds=time),
                                 RunLog.level == 0).count()


def GetWarnMessageData(now: Union[int, float], limit: Union[int, float], name: str):
    title = f"{name}达到警告阈值"
    message = f"""时间：{datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}
当前值：{now}
阈值：{limit}
百分比：{round((now / limit) * 100, 2)}%
"""
    return {"title": title, "message": message}


def GetDangerousMessageData(now: Union[int, float], limit: Union[int, float], name: str) -> Dict[str, str]:
    title: str = f"{name}达到危险阈值"
    message: str = f"""时间：{datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}
当前值：{now}
阈值：{limit}
百分比：{round((now / limit) * 100, 2)}%
"""
    return {"title": title, "message": message}


def main():
    recent_no_time_limit_monitor_error_time = None
    recent_60_seconds_monitor_error_time = None
    recent_5_minutes_monitor_error_time = None
    recent_30_minutes_monitor_error_time = None

    while True:
        if not Config()["status_monitor/enable_status_monitor"]:
            AddRunLog(2, "服务状态监控已关闭")
            sleep(300)  # 五分钟后再次尝试
            continue

        if recent_no_time_limit_monitor_error_time:
            AddRunLog(2, "由于上一次监控触发过无时间限制监控指标的告警，监控服务停止 60 秒。")
            sleep(60)
            recent_no_time_limit_monitor_error_time = None
            continue
        elif recent_60_seconds_monitor_error_time:
            AddRunLog(2, "由于上一次监控触发过 60 秒监控指标的告警，监控服务停止 60 秒。")
            sleep(60)
            recent_60_seconds_monitor_error_time = None
            continue
        elif recent_5_minutes_monitor_error_time:
            AddRunLog(2, "由于上一次监控触发过 5 分钟监控指标的告警，监控服务停止 5 分钟。")
            sleep(5 * 60)
            recent_5_minutes_monitor_error_time = None
            continue
        elif recent_30_minutes_monitor_error_time:
            AddRunLog(2, "由于上一次监控触发过 30 分钟监控指标的告警，监控服务停止 30 分钟。")
            sleep(30 * 60)
            recent_30_minutes_monitor_error_time = None
            continue

        memory_now = GetMemoryPercent()
        memory_percent_warn = Config()["status_monitor/memory_percent_warn"]
        memory_percent_error = Config()["status_monitor/memory_percent_error"]
        if memory_now > memory_percent_warn:
            SendWarningMessage(**GetWarnMessageData(memory_now, memory_percent_warn, "内存占用率"))
            recent_no_time_limit_monitor_error_time = datetime.now()
        elif memory_now > memory_percent_error:
            SendErrorMessage(**GetDangerousMessageData(memory_now, memory_percent_error, "内存占用率"))
            recent_no_time_limit_monitor_error_time = datetime.now()

        disk_now = GetDiskPercent()
        disk_percent_warn = Config()["status_monitor/disk_percent_warn"]
        disk_percent_error = Config()["status_monitor/disk_percent_error"]
        if disk_now > disk_percent_warn:
            SendWarningMessage(**GetWarnMessageData(disk_now, disk_percent_warn, "磁盘占用率"))
            recent_no_time_limit_monitor_error_time = datetime.now()
        elif disk_now > disk_percent_error:
            SendErrorMessage(**GetDangerousMessageData(disk_now, disk_percent_error, "磁盘占用率"))
            recent_no_time_limit_monitor_error_time = datetime.now()

        user_to_process_now = GetUserToProcessCount()
        user_to_process_warn = Config()["status_monitor/user_to_process_warn"]
        user_to_process_error = Config()["status_monitor/user_to_process_error"]
        if user_to_process_now > user_to_process_warn:
            SendWarningMessage(**GetWarnMessageData(user_to_process_now, user_to_process_warn, "待处理用户数据数量"))
            recent_no_time_limit_monitor_error_time = datetime.now()
        elif user_to_process_now > user_to_process_error:
            SendErrorMessage(**GetDangerousMessageData(user_to_process_now, user_to_process_error, "待处理用户数据数量"))
            recent_no_time_limit_monitor_error_time = datetime.now()

        views_count_last_60_seconds = GetViewsCount(60)
        views_count_last_60_seconds_warn = Config()["status_monitor/views_count_last_60_seconds_warn"]
        views_count_last_60_seconds_error = Config()["status_monitor/views_count_last_60_seconds_error"]
        if views_count_last_60_seconds > views_count_last_60_seconds_warn:
            SendWarningMessage(**GetWarnMessageData(views_count_last_60_seconds, views_count_last_60_seconds_warn, "60 秒访问量"))
            recent_60_seconds_monitor_error_time = datetime.now()
        elif views_count_last_60_seconds > views_count_last_60_seconds_error:
            SendErrorMessage(**GetDangerousMessageData(views_count_last_60_seconds, views_count_last_60_seconds_error, "60 秒访问量"))
            recent_60_seconds_monitor_error_time = datetime.now()

        views_count_last_5_minutes = GetViewsCount(5 * 60)
        views_count_last_5_minutes_warn = Config()["status_monitor/views_count_last_5_minutes_warn"]
        views_count_last_5_minutes_error = Config()["status_monitor/views_count_last_5_minutes_error"]
        if views_count_last_5_minutes > views_count_last_5_minutes_warn:
            SendWarningMessage(**GetWarnMessageData(views_count_last_5_minutes, views_count_last_5_minutes_warn, "5 分钟访问量"))
            recent_5_minutes_monitor_error_time = datetime.now()
        elif views_count_last_5_minutes > views_count_last_5_minutes_error:
            SendErrorMessage(**GetDangerousMessageData(views_count_last_5_minutes, views_count_last_5_minutes_error, "5 分钟访问量"))
            recent_5_minutes_monitor_error_time = datetime.now()

        views_count_last_30_minutes = GetViewsCount(30 * 60)
        views_count_last_30_minutes_warn = Config()["status_monitor/views_count_last_30_minutes_warn"]
        views_count_last_30_minutes_error = Config()["status_monitor/views_count_last_30_minutes_error"]
        if views_count_last_30_minutes > views_count_last_30_minutes_warn:
            SendWarningMessage(**GetWarnMessageData(views_count_last_30_minutes, views_count_last_30_minutes_warn, "30 分钟访问量"))
            recent_30_minutes_monitor_error_time = datetime.now()
        elif views_count_last_30_minutes > views_count_last_30_minutes_error:
            SendErrorMessage(**GetDangerousMessageData(views_count_last_30_minutes, views_count_last_30_minutes_error, "30 分钟访问量"))
            recent_30_minutes_monitor_error_time = datetime.now()

        warns_count_last_5_minutes_now = GetWarnsCount(5 * 60)
        warns_count_last_5_minutes_warn = Config()["status_monitor/warns_count_last_5_minutes_warn"]
        warns_count_last_5_minutes_error = Config()["status_monitor/warns_count_last_5_minutes_error"]
        if warns_count_last_5_minutes_now > warns_count_last_5_minutes_warn:
            SendWarningMessage(**GetWarnMessageData(warns_count_last_5_minutes_now, warns_count_last_5_minutes_warn, "5 分钟警告数量"))
            recent_5_minutes_monitor_error_time = datetime.now()
        elif warns_count_last_5_minutes_now > warns_count_last_5_minutes_error:
            SendErrorMessage(**GetDangerousMessageData(warns_count_last_5_minutes_now, warns_count_last_5_minutes_error, "5 分钟警告数量"))
            recent_5_minutes_monitor_error_time = datetime.now()

        errors_count_last_5_minutes_now = GetErrorsCount(5 * 60)
        errors_count_last_5_minutes_warn = Config()["status_monitor/errors_count_last_5_minutes_warn"]
        errors_count_last_5_minutes_error = Config()["status_monitor/errors_count_last_5_minutes_error"]
        if errors_count_last_5_minutes_now > errors_count_last_5_minutes_warn:
            SendWarningMessage(**GetWarnMessageData(errors_count_last_5_minutes_now, errors_count_last_5_minutes_warn, "5 分钟错误数量"))
            recent_5_minutes_monitor_error_time = datetime.now()
        elif errors_count_last_5_minutes_now > errors_count_last_5_minutes_error:
            SendErrorMessage(**GetDangerousMessageData(errors_count_last_5_minutes_now, errors_count_last_5_minutes_error, "5 分钟错误数量"))
            recent_5_minutes_monitor_error_time = datetime.now()

        criticals_count_last_5_minutes_now = GetCriticalsCount(5 * 60)
        criticals_count_last_5_minutes_warn = Config()["status_monitor/criticals_count_last_5_minutes_warn"]
        criticals_count_last_5_minutes_error = Config()["status_monitor/criticals_count_last_5_minutes_error"]
        if criticals_count_last_5_minutes_now > criticals_count_last_5_minutes_warn:
            SendWarningMessage(**GetWarnMessageData(criticals_count_last_5_minutes_now, criticals_count_last_5_minutes_warn, "5 分钟关键错误数量"))
            recent_5_minutes_monitor_error_time = datetime.now()
        elif criticals_count_last_5_minutes_now > criticals_count_last_5_minutes_error:
            SendErrorMessage(**GetDangerousMessageData(criticals_count_last_5_minutes_now, criticals_count_last_5_minutes_error, "5 分钟关键错误数量"))
            recent_5_minutes_monitor_error_time = datetime.now()

        sleep(60)


def init():
    status_monitor_thread = Thread(target=main, daemon=True)  # 设置为守护线程，避免造成主线程无法退出
    status_monitor_thread.start()
