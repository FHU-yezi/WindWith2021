from typing import Dict

from exceptions import UserDataDoesNotReadyException, UserDoesNotExistException
from JianshuResearchTools.convert import UserUrlToUserSlug
from JianshuResearchTools.exceptions import InputError, ResourceError
from JianshuResearchTools.user import GetUserName
from pandas import DataFrame, read_csv
from pywebio.input import TEXT
from pywebio.output import (clear, put_button, put_image, put_link, put_text,
                            toast, use_scope)
from pywebio.pin import pin, put_input
from queue_manager import GetOneToShowSummary
from yaml import SafeLoader
from yaml import load as yaml_load

from .utils import GetLocalStorage, GetUrl, SetFooter, SetLocalStorage


def ShowSummary(basic_data: Dict, articles_data: DataFrame):
    with use_scope("output"):
        put_text("四季更替，星河流转，2021 是一个充满生机与挑战的年份。")
        put_text("简书，又陪伴你走过了一年。")
        put_image(basic_data["avatar_url"], width="100", height="100")
        put_text(f"{basic_data['name']}，欢迎进入，你的简书 2021 年度总结。")
        put_text("（↓点击下方按钮展开↓）")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text(f"时至今日，你已经在简书写下了{basic_data['articles_count']}篇文章，"
                 f"一共{round(basic_data['wordage'] / 10000, 1)}万字。")
        put_text(f"这些文字吸引了{basic_data['fans_count']}人的关注，还有{basic_data['likes_count']}个点赞。")
        put_text("创作的路上，你点亮的星火，为万千读者铺平了前路。")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text(f"现在，你拥有{basic_data['assets_count']}资产，钻贝比为{basic_data['FP / FTN']}，"
                 f"看起来你对资产系统的了解不错哦。")
        put_text(f"简书钻：{basic_data['FP_count']}；简书贝：{basic_data['FTN_count']}。")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text(f"今年，你写下了{articles_data['aslug'].count()}篇文章，{round(articles_data['wordage'].sum() / 10000, 1)}万字。")
        put_text(f"这一年，你写的文章，占总文章数的{round(basic_data['articles_count'] / articles_data['aslug'].count(), 2)}")
        put_text(f"{articles_data['likes_count'].sum()}个点赞，是你今年的成果，占你总收获的{round(articles_data['likes_count'].sum() / basic_data['likes_count'], 4) * 100}%。")
        put_text(f"你的最近一次创作在{basic_data['last_update_time']}，还记得当时写了什么吗？")
        put_text("\n")
    yield None
    with use_scope("output"):
        if basic_data['vip_type']:
            put_text(f"不知是什么原因，让你开通了{basic_data['vip_type']}会员呢？")
            put_text(f"你的会员在{basic_data['vip_expire_time']}到期，要不要考虑一下续费？")
        else:
            put_text("你貌似没有开通简书会员呢，全站去广告、发文数量上限提升等等特权，了解一下？")
        put_text("\n")
    yield None
    with use_scope("output"):
        if basic_data['badges_list']:
            put_text(f"你有这些徽章哦：{'   '.join(basic_data['badges_list'])}")
        else:
            put_text("什么？你还没有徽章？为啥不好好写文申请个创作者，或者去做岛主？")
            put_text("搞点东西装饰一下你的个人主页，何乐而不为呢？")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text(f"知道{basic_data['next_anniversary_day']}是什么日子吗？")
        put_text("是你来简书的周年纪念日哦！到时候要不要发篇文章说说自己的感想？")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text(f"在大家面前，你是{basic_data['name']}，而在简书的数据库中，你的代号是{basic_data['id']}。")
        put_text("技术，无限可能，正如你面前的这份年终总结一样。")
        put_text("虽然它在背后，但你的每一份创作体验，都少不了万千技术工作者的默默付出。")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text("这是，属于你的创作总结；")
        put_text("这是，属于你的一年；")
        put_text("这是，属于你的简书社区。")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text("愿每一行文字，都能被知晓；")
        put_text("愿每一名创作者，都能找到自己的价值；")
        put_text("愿每一份不甘，都有温暖相伴。")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text("我们是简友，我们在简书等你。")
        put_text("\n")
    yield None
    with use_scope("output"):
        put_text("年终总结，完。")
        put_text("2022，启航！")
    clear("continue_button_area")  # 移除继续按钮
    exit()


def GetAllData() -> None:
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
        with use_scope("data_input", clear=True):
            put_input("user_url", type=TEXT, value=user_url, label="您的简书用户主页链接")
            put_button("提交", color="success", onclick=GetAllData)
            put_text(f"尊敬的简友 {user_name}，我们正在努力获取您的数据，请稍后再试。")
        return
    else:
        user_slug = UserUrlToUserSlug(user_url)
        with open(f"user_data/{user_slug}/basic_data_{user_slug}.yaml", "r", encoding="utf-8") as f:
            basic_data = yaml_load(f, SafeLoader)
        with open(f"user_data/{user_slug}/article_data_{user_slug}.csv", "r", encoding="utf-8") as f:
            article_data = read_csv(f)
        clear("data_input")  # 清空数据输入区
        SetLocalStorage("user_url", user_url)  # 将用户链接保存到本地
        with use_scope("output"):  # 初始化输出区
            pass
        show_summary_obj = ShowSummary(basic_data, article_data)
        with use_scope("continue_button_area"):
            put_button("继续", color="dark", outline=True, onclick=lambda: next(show_summary_obj))


def ViewSummary():
    """我的简书 2021 年终总结 ——「风语」
    """
    user_url = GetLocalStorage("user_url")
    with use_scope("data_input", clear=True):
        put_input("user_url", type=TEXT, value=user_url, label="您的简书用户主页链接")
        put_button("提交", color="success", onclick=GetAllData)

    SetFooter("Made with PyWebIO and ♥")
