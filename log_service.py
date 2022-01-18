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


def AddRunLog(level: int, message: str):
    RunLog.create(time=datetime.now(), level=level, message=message)


def AddViewLog(session_info: info, user_url: str = None):
    try:
        ViewLog.create(time=datetime.now(),
                       user_url=user_url,
                       is_mobile=session_info.user_agent.is_mobile,
                       is_tablet=session_info.user_agent.is_tablet,
                       is_pc=session_info.user_agent.is_pc,
                       browser_name=session_info.user_agent.browser.family,
                       os_name=session_info.user_agent.os.family,
                       language=session_info.user_language,
                       ip=session_info.user_ip)
    except DatabaseError:
        AddRunLog(1, "添加访问日志时出错")
