from config_manager import Config
from exceptions import (QueueFullException, UserAlreadyExistsException,
                        UserBannedException)
from JianshuResearchTools.assert_funcs import (AssertUserStatusNormal,
                                               AssertUserUrl)
from JianshuResearchTools.exceptions import InputError, ResourceError
from JianshuResearchTools.user import GetUserName
from log_manager import AddRunLog, AddViewLog
from pywebio.input import TEXT
from pywebio.output import (put_button, put_link, put_markdown, put_text,
                            toast, use_scope)
from pywebio.pin import pin, put_input
from pywebio.session import info as session_info
from queue_manager import AddToQueue

from .utils import GetLocalStorage, GetUrl, SetFooter, SetLocalStorage


def JoinQueueAction():
    user_url = pin["user_url"]
    if not user_url:
        return  # 不输入链接直接点击按钮时不做任何操作

    try:
        AddRunLog(4, f"开始对 {user_url} 进行校验")
        AssertUserUrl(user_url)
        AssertUserStatusNormal(user_url)
    except (InputError, ResourceError):
        toast("输入的链接无效，请检查", color="warn")
        AddRunLog(4, f"{user_url}无效")
        return
    else:
        user_name = GetUserName(user_url, disable_check=True)
        AddRunLog(4, f"{user_url} 校验成功，对应的用户名为 {user_name}")

    try:
        AddToQueue(user_url, user_name)
    except QueueFullException:
        AddRunLog(2, f"用户 {user_url}（{user_name}）排队失败，因为队列已满")
        toast("队列已满，请稍后再试", color="warn")
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止用户频繁重试
    except UserAlreadyExistsException:
        AddRunLog(2, f"用户 {user_url}（{user_name}）排队失败，因为他已排队")
        toast("您已排队，请勿重复提交", color="warn")
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止重复提交
    except UserBannedException:
        AddRunLog(2, f"用户 {user_url}（{user_name}）排队失败，因为他已被封禁")
        toast("您已被封禁，无法查看年终总结", color="danger")
        put_markdown("""
        # 为什么？

        请简信开发者询问。您的简书账号并没有被封禁，只是无法查看这份年终总结。

        如果简书官方发布年终总结，您是可以正常查看的。
        """)
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止用户重试
    else:
        AddRunLog(3, f"用户 {user_url}（{user_name}）排队成功")
        SetLocalStorage("user_url", user_url)  # 在本地缓存用户信息
        toast("排队成功", color="success")
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止用户重复点击
        put_text(f"{user_name}，您已成功排队，请耐心等待。")
        put_link("点击前往您的年度总结", url=f"{GetUrl().replace('?app=JoinQueue', '')}?app=ViewSummary")


def JoinQueue():
    """排队 ——「风语」
    """
    AddViewLog(session_info, user_url=GetLocalStorage("user_url"), page_name="排队")

    put_markdown("# 排队 ——「风语」")
    put_input("user_url", type=TEXT, label="您的简书用户主页链接",
              value=GetLocalStorage("user_url"), placeholder="https://www.jianshu.com/u/xxxxxx")
    with use_scope("submit_button", clear=True):
        put_button("提交", color="success", onclick=JoinQueueAction)

    SetFooter(Config()["basic_data/footer_content"])
