from config_manager import config
from log_manager import AddViewLog
from pywebio.output import put_markdown
from pywebio.session import info as session_info

from .utils import GetLocalStorage, SetFooter


def LetterToJianshuers():
    """写给简友们的信 ——「风语」
    """
    AddViewLog(session_info, user_url=GetLocalStorage("user_url"), page_name="写给简友们的信")

    with open("letter_to_jianshuers.md", "r", encoding="utf-8") as f:
        put_markdown(f.read())

    SetFooter(f"Version：{config['basic_data/version']} {config['basic_data/footer_content']}")
