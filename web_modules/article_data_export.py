from datetime import datetime
from tempfile import TemporaryDirectory

from JianshuResearchTools.convert import UserUrlToUserSlug
from JianshuResearchTools.exceptions import InputError, ResourceError
from JianshuResearchTools.objects import User
from pandas import DataFrame, read_csv
from pywebio.input import TEXT
from pywebio.output import (
    clear,
    put_button,
    put_link,
    put_text,
    toast,
    use_scope,
)
from pywebio.pin import pin, put_input
from pywebio.session import download
from pywebio.session import info as session_info

from config_manager import config
from exceptions import (
    UserDataDoesNotReadyException,
    UserDataException,
    UserDoesNotExistException,
)
from log_manager import AddRunLog, AddViewLog
from queue_manager import GetUserToExportData

from .utils import (
    CleanUserUrl,
    GetLocalStorage,
    GetUrl,
    SetFooter,
    SetLocalStorage,
)


def ExportArticleData(format: str) -> None:
    user_url = CleanUserUrl(pin.user_url)
    if not user_url:  # 输入框为空
        return

    try:
        AddRunLog(4, f"开始对 {user_url} 进行校验")
        user = User(user_url)
    except (InputError, ResourceError):
        toast("输入的链接无效，请检查", color="warn")
        AddRunLog(4, f"{user_url} 无效")
        return
    else:
        user_name = user.name
        AddRunLog(4, f"{user_url} 有效")

    try:
        user = GetUserToExportData(user_url)
    except UserDoesNotExistException:
        toast("您未加入队列，请先排队", color="warn")
        with use_scope("data_input", clear=True):
            put_input("user_url", type=TEXT, label="您的简书用户主页链接")
            put_button(
                "提交",
                color="success",
                onclick=ExportArticleData,
                disabled=True,
            )  # 禁用提交按钮
        put_link("点击前往排队页面", url=f"{GetUrl()}?app=JoinQueue")
        AddRunLog(4, f"{user_url}（{user_name}）未排队")
        return
    except UserDataDoesNotReadyException:
        toast("您的数据还未获取完成，请稍后再试", color="warn")
        with use_scope("data_input", clear=True):
            put_input("user_url", type=TEXT, value=user_url, label="您的简书用户主页链接")
            put_button("提交", color="success", onclick=ExportArticleData)
            put_text(f"尊敬的简友 {user_name}，我们正在努力获取您的数据，请稍后再试。")
        AddRunLog(4, f"{user_url}（{user_name}）的数据未就绪")
        return
    except UserDataException as e:
        AddRunLog(2, f"用户 {user_url}（{user_name}）导出文章数据失败，因为他的数据存在异常：{e}")
        clear("data_input")  # 清空数据输入区
        with use_scope("output"):
            put_text(f"抱歉，我们无法为您导出文章数据，因为您的数据存在以下异常：{e}。")
            put_text("如需帮助，请联系开发者。")
        exit()
    else:
        SetLocalStorage("user_url", user.user_url)  # 将用户链接保存到本地
        AddRunLog(4, f"{user_url}（{user_name}）的数据已就绪")
        user_slug = UserUrlToUserSlug(user.user_url)

        articles_data_path = f"{config.service.data_path}/user_data/{user_slug}/article_data_{user_slug}.csv"
        with open(articles_data_path, "r", encoding="utf-8") as f:
            articles_data: DataFrame = read_csv(f)
        AddRunLog(4, f"成功加载 {user.user_url}（{user.user_name}）的文章数据")

        del articles_data["user"]  # 删除无用的的用户信息
        articles_data["release_time"] = articles_data["release_time"].apply(
            lambda x: datetime.fromisoformat(x).replace(tzinfo=None)
        )  # 去除 datetime 对象中的时区信息
        # True / False => 是 / 否
        articles_data["is_top"] = articles_data["is_top"].apply(
            lambda x: "是" if x else "否"
        )
        articles_data["paid"] = articles_data["paid"].apply(lambda x: "是" if x else "否")
        articles_data["commentable"] = articles_data["commentable"].apply(
            lambda x: "是" if x else "否"
        )

        # 更改文章数据的列名
        articles_data.rename(
            columns={
                "aid": "文章 ID",
                "title": "标题",
                "aslug": "文章 Slug",
                "release_time": "发布时间",
                "first_image_url": "题图链接",
                "summary": "摘要",
                "views_count": "阅读量",
                "likes_count": "获赞量",
                "is_top": "置顶",
                "paid": "付费",
                "commentable": "允许评论",
                "total_fp_amount": "获钻量",
                "comments_count": "评论量",
                "rewards_count": "赞赏量",
                "wordage": "字数",
            },
            inplace=True,
        )

        with TemporaryDirectory() as temp_dir:
            if format == "excel":
                file_name = f"{user.user_name}的文章数据.xlsx"
                articles_data.to_excel(f"{temp_dir}/{file_name}", encoding="utf-8")
            elif format == "csv":
                file_name = f"{user.user_name}的文章数据.csv"
                articles_data.to_csv(f"{temp_dir}/{file_name}", encoding="utf-8")

            with open(f"{temp_dir}/{file_name}", "rb") as f:
                download(file_name, f.read())


def ArticleDataExport():
    """文章数据导出 ——「风语」"""
    user_url = GetLocalStorage("user_url")
    AddViewLog(session_info, user_url, "文章数据导出")

    AddRunLog(4, f"获取到用户本地存储的数据为：{user_url}")
    with use_scope("data_input", clear=True):
        put_input("user_url", type=TEXT, value=user_url, label="您的简书用户主页链接")
        put_button(
            "下载 Excel 格式",
            color="success",
            onclick=lambda: ExportArticleData("excel"),
        )
        put_button(
            "下载 CSV 格式",
            color="success",
            onclick=lambda: ExportArticleData("csv"),
        )

    SetFooter(config.basic_data.footer_content)
