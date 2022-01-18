from typing import Dict

from exceptions import UserDataDoesNotReadyException, UserDoesNotExistException
from JianshuResearchTools.convert import UserUrlToUserSlug
from JianshuResearchTools.exceptions import InputError, ResourceError
from JianshuResearchTools.user import GetUserName
from pandas import DataFrame, read_csv
from pywebio.input import TEXT
from pywebio.output import (put_button, put_link, put_markdown, put_text,
                            toast, use_scope)
from pywebio.pin import pin, put_input
from queue_manager import GetOneToShowSummary
from yaml import SafeLoader
from yaml import load as yaml_load

from .utils import GetLocalStorage, GetUrl, SetFooter


def GetAllData(user_url: str = None) -> None:
    if not user_url:
        user_url = pin["user_url"]  # 从输入框中获取 user_url
    if not user_url:  # 输入框为空
        return

    try:
        user_name = GetUserName(user_url)
    except (InputError, ResourceError):
        toast("输入的链接无效，请检查", color="warn")
        return

    try:
        user_url = GetOneToShowSummary(user_url)  # 将数据库中的用户状态更改为已查看年度总结
    except UserDoesNotExistException:
        toast("您未加入队列，请先排队", color="warn")
        with use_scope("data_input", clear=True):
            put_input("user_url", type=TEXT, label="您的简书用户主页链接")
            put_button("提交", color="success", onclick=GetAllData, disabled=True)  # 禁用提交按钮
        put_link("点击前往排队页面", url=f"{GetUrl().replace('?app=ViewSummary', '')}?app=JoinQueue")
        return
    except UserDataDoesNotReadyException:
        toast("您的数据还未获取完成，请稍后再试", color="warn")
        put_text(f"尊敬的简友 {user_name}，我们正在努力获取您的数据，请稍后再试")
        return
    else:
        user_slug = UserUrlToUserSlug(user_url)
        with open(f"user_data/{user_slug}/basic_data_{user_slug}.yaml", "r", encoding="utf-8") as f:
            basic_data = yaml_load(f, SafeLoader)
        with open(f"user_data/{user_slug}/article_data_{user_slug}.csv", "r", encoding="utf-8") as f:
            article_data = read_csv(f)
        with use_scope("data_input", clear=True):
            pass  # 清空数据输入区
        ShowSummary(basic_data, article_data)  # 调用显示年终总结函数


def ShowSummary(basic_data: Dict, article_data: DataFrame) -> None:
    put_text(basic_data)
    from pywebio.output import put_html
    put_html(article_data[:10].to_html())


def ViewSummary():
    """我的简书 2021 年终总结 ——「风语」
    """
    user_url = GetLocalStorage("user_url")
    SetFooter("Made with PyWebIO and ♥")
    with use_scope("data_input", clear=True):
        if not user_url:
            put_input("user_url", type=TEXT, label="您的简书用户主页链接")
            put_button("提交", color="success", onclick=GetAllData)
        else:
            GetAllData(user_url)
