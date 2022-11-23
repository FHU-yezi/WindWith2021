from datetime import datetime

from peewee import DatabaseError
from pywebio.session import info

from config_manager import config
from db_config import RunLog, ViewLog

LEVEL_INT_TO_TEXT = {
    0: "CRITICAL",
    1: "ERROR",
    2: "WARNING",
    3: "INFO",
    4: "DEBUG",
}


def AddRunLog(level: int, message: str):
    RunLog.create(time=datetime.now(), level=level, message=message)
    if config.debug.enable_debug and config.debug.print_log_level >= level:
        print(f"[{datetime.now()}] [{LEVEL_INT_TO_TEXT[level]}] {message}")


def AddViewLog(session_info: info, user_url: str = None, page_name: str = None):
    try:
        ViewLog.create(
            time=datetime.now(),
            user_url=user_url,
            page_name=page_name,
            is_mobile=session_info.user_agent.is_mobile,
            is_tablet=session_info.user_agent.is_tablet,
            is_pc=session_info.user_agent.is_pc,
            browser_name=session_info.user_agent.browser.family,
            os_name=session_info.user_agent.os.family,
            language=session_info.user_language,
            ip=session_info.user_ip,
        )
        AddRunLog(4, f"添加了一条新的访问记录，页面为：{page_name}，用户 IP 为：{session_info.user_ip}")
    except DatabaseError:
        AddRunLog(1, "添加访问日志时出错")
