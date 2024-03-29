from pywebio.output import put_markdown
from pywebio.session import info as session_info

from config_manager import config
from log_manager import AddViewLog

from .utils import get_localstorage, set_footer


def LetterToJianshuers():
    """写给简友们的信 ——「风语」"""
    AddViewLog(
        session_info,
        user_url=get_localstorage("user_url"),
        page_name="写给简友们的信",
    )

    with open("letter_to_jianshuers.md", "r", encoding="utf-8") as f:
        put_markdown(f.read())

    set_footer(
        f"Version：{config.basic_data.version} {config.basic_data.footer_content}"
    )
