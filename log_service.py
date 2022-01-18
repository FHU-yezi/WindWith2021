from db_config import RunLog, ViewLog
from datetime import datetime
from peewee import DatabaseError
from pywebio.session import info

"""
日志等级定义：
0：CRITICAL
1：ERROR
2：WARNING
3：INFO
4：DEBUG
"""


def AddRunLog(level:int, message: str):
    RunLog.create(time=datetime.now(), level=level, message=message)


def AddViewLog(unique_code: str, session_info: info):
    try:
        ViewLog.create(time=datetime.now(),
                       unique_code=unique_code,
                       is_mobile=session_info.is_mobile,
                       is_tablet=session_info.is_tablet,
                       is_pc=session_info.is_pc,
                       browser_name=session_info.browser.family,
                       os_name=session_info.os.family,
                       language=session_info.user_language,
                       ip=session_info.user_ip)
    except DatabaseError:
        AddRunLog(1, "添加访问日志时出错")
