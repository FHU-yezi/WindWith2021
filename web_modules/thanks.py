from config_manager import Config
from log_manager import AddViewLog
from pywebio.output import put_markdown
from pywebio.session import info as session_info
from yaml import SafeLoader
from yaml import load as yaml_load

from .utils import GetLocalStorage, SetFooter

with open("contributors.yaml", "r", encoding="utf-8") as f:
    contributors = yaml_load(f, SafeLoader)


def Thanks():
    """鸣谢 ——「风语」
    """

    AddViewLog(session_info, GetLocalStorage("user_url"), "鸣谢")

    put_markdown("""
    # 鸣谢

    （全部简友名和代码仓库名按首字母排序）
    """)

    put_markdown("""
    ## 一期内测成员
    感谢你们在「风语」的雏形刚刚完成时参与测试，为它的开发提供了宝贵的建议。
    """)

    for name, url in contributors["phase_one_test"].items():
        put_markdown(f"[{name}]({url})")

    put_markdown("""
        ## 二期内测成员
        感谢你们对「风语」的不断打磨，使之成为一个足以公开给社区看到的项目。
    """)

    for name, url in contributors["phase_two_test"].items():
        put_markdown(f"[{name}]({url})")

    put_markdown("""
        ## 开源库
        感谢这些开源库的贡献者，你们让「风语」能够在如此短的时间内打磨成型，与大家相见。
    """)

    for name, url in contributors["opensource_repo"].items():
        put_markdown(f"[{name}]({url})")

    put_markdown("同时，感谢每一位简友对「风语」的支持，让这个产品拥有无限可能。")

    SetFooter(f"Version：{Config()['basic_data/version']} {Config()['basic_data/footer_content']}")
