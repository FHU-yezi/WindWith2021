from JianshuResearchTools.objects import set_cache_status
from pywebio import start_server
from pywebio.output import popup, put_link, put_markdown
from pywebio.session import info as session_info

from config_manager import config
from data_getter import init as data_getter_init
from log_manager import AddRunLog, AddViewLog
from web_modules.article_data_export import ArticleDataExport
from web_modules.join_queue import JoinQueue
from web_modules.letter_to_jianshuers import LetterToJianshuers
from web_modules.thanks import Thanks
from web_modules.utils import get_localstorage, get_url, set_footer
from web_modules.view_summary import ViewSummary

AddRunLog(3, f"版本号：{config.basic_data.version}")


data_getter_init()
AddRunLog(3, "数据获取线程启动成功")

set_cache_status(False)
AddRunLog(4, "已禁用 JRT 缓存")


def index():
    """「风语」—— 简书 2021 年度总结
    """

    put_markdown("""
    # 「风语」—— 简书 2021 年度总结

    > 风起叶落，语存元夜。

    这是一名技术工作者呈现给社区的年度总结。
    """)
    AddViewLog(session_info, user_url=get_localstorage("user_url"), page_name="主页")

    put_markdown("""
    # 排队

    **为什么要排队？**

    生成年度总结所需的数据量较多，为避免给简书服务器造成压力，我们对请求频率进行了限制。

    同时，排队也可以帮助我们更好的分配服务器资源，让大家的年终总结生成效率得到提高。

    一般情况下，提交排队申请五分钟后即可查看年终总结。
    """)

    put_link("点击前往排队页面", url=f"{get_url()}?app=JoinQueue")

    put_markdown("""
    # 查看年终总结

    记得先排队哦~

    如果年终总结尚未生成，请稍等几分钟，可以趁着这段时间，看看下面的那封信。
    """)

    put_link("查看年终总结", url=f"{get_url()}?app=ViewSummary")

    put_markdown("""
    # 文章数据导出

    为了帮助大家分析自己的文章数据，我们提供数据导出功能。

    数据获取完成之后就可以生成了哦，支持 Excel 和 CSV 格式。
    """)

    put_link("文章数据导出", url=f"{get_url()}?app=ArticleDataExport")

    put_markdown("""
    # 写给简友们的信

    这是「风语」的开发者写给大家的信，里面有开发这个项目的心路历程，和对简书生态的期望。
    """)

    put_link("查看信件", url=f"{get_url()}?app=LetterToJianshuers")

    put_markdown("""
    # 「风语」专题

    该专题收录了简友们的「风语」年度总结，欢迎投稿。
    """)

    put_link("前往专题", url="https://www.jianshu.com/c/5cb0d11d6013", new_window=True)
    put_markdown("""
    # 写给简友们的信

    这是「风语」的开发者写给大家的信，里面有开发这个项目的心路历程，和对简书生态的期望。
    """)

    put_link("查看信件", url=f"{get_url()}?app=LetterToJianshuers")

    put_markdown("""
    # 鸣谢

    感谢每个对「风语」做出贡献的内测成员和开发者，感谢每个简友对「风语」的关注。
    """)

    put_link("查看鸣谢页面", url=f"{get_url()}?app=Thanks")

    put_markdown("""
    # 反馈

    如果您对「风语」有任何意见或建议，请填写下方表单。

    再渺小的声音，都不应该被忽略。
    """)

    put_link("填写反馈表单", url="https://wenjuan.feishu.cn/m?t=sFAVCWGHdDzi-x0b0", new_window=True)

    set_footer(f"Version：{config.basic_data.version} {config.basic_data.footer_content}")

    if config.notification.enable:
        AddRunLog(4, f"展示了公告信息，标题：{config.notification.title}")
        popup(title=config.notification.title, content=config.notification.content,
              size="large", closable=config.notification.closable)


SERVICES = [
    JoinQueue,
    ViewSummary,
    ArticleDataExport,
    LetterToJianshuers,
    Thanks,
    index
]

AddRunLog(3, "启动服务......")
start_server(SERVICES, port=config.service.port)
