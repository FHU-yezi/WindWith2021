from pywebio.output import put_markdown, put_button, toast, put_text, use_scope
from pywebio.pin import put_input, pin
from pywebio.input import TEXT
from exceptions import QueueFullException, UserAlreadyExistsException, UserBannedException
from log_service import AddRunLog
from web_modules.utils import SetFooter
from JianshuResearchTools.user import GetUserName
from JianshuResearchTools.exceptions import ResourceError, InputError
from queue_manager import AddToQueue


def JoinQueueAction():
    if not pin["user_url"]:
        return  # 不输入链接直接点击按钮时不做任何操作

    try:
        user_name = GetUserName(pin["user_url"])
    except (InputError, ResourceError):
        toast("输入的链接无效，请检查", color="warn")
        return

    try:
        AddToQueue(pin["user_url"])
    except QueueFullException:
        AddRunLog(2, f"用户 {pin['user_url']} 加入排队失败，因为队列已满")
        toast("队列已满，请稍后再试", color="warn")
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止用户频繁重试
    except UserAlreadyExistsException:
        AddRunLog(2, f"用户 {pin['user_url']} 加入排队失败，因为他已加入队列")
        toast("您已加入队列，请勿重复提交", color="warn")
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止重复提交
    except UserBannedException:
        AddRunLog(2, f"用户 {pin['user_url']} 加入排队失败，因为他已被封禁")
        toast("您已被封禁，无法查看年终总结", color="danger")
        put_markdown("""
        # 为什么？

        请简信开发者询问。您的简书账号并没有被封禁，只是无法查看这份年终总结。

        如果简书官方发布年终总结，您是可以正常查看的。
        """)
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止用户重试
    else:
        AddRunLog(3, f"用户 {pin['user_url']} 加入排队成功")
        toast("加入排队成功", color="success")
        with use_scope("submit_button", clear=True):
            put_button("提交", color="success", disabled=True, onclick=JoinQueueAction)  # 禁用按钮，防止用户重复点击
        put_text(f"{user_name}，您已成功加入排队，请耐心等待。")


def JoinQueue():
    """加入排队 ——「风语」
    """

    put_markdown("# 加入排队 ——「风语」")
    put_input("user_url", type=TEXT, label="您的简书用户主页链接", placeholder="https://www.jianshu.com/u/xxxxxx")
    with use_scope("submit_button", clear=True):
        put_button("提交", color="success", onclick=JoinQueueAction)

    SetFooter("Made with PyWebIO and ♥")
