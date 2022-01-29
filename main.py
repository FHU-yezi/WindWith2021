from pywebio import start_server
from pywebio.output import put_link, put_markdown
from pywebio.session import info as session_info

from config_manager import Config
from data_getter import init as data_getter_init
from log_manager import AddRunLog, AddViewLog
from web_modules.join_queue import JoinQueue
from web_modules.utils import GetUrl, SetFooter
from web_modules.view_summary import ViewSummary

AddRunLog(3, f"版本号：{Config()['basic_data/version']}")


data_getter_init()  # 初始化数据获取线程
AddRunLog(3, "初始化数据获取线程成功")


def index():
    """「风语」—— 简书 2021 年度总结
    """

    put_markdown("""
    # 「风语」—— 简书 2021 年度总结

    > 你在简书遇到的一切美好，风都记得。

    这不是官方的年度总结。

    我是一名技术工作者，今年简书的年度总结迟迟没有上线，而且 2019 和 2020 的年度总结都不太完整，于是就想着用自己的技术能力，为社区呈现一份不一样的年度总结。

    这是我第一次开发这种项目，如果有不完美，请大家多多包涵。
    """)
    AddViewLog(session_info)

    put_markdown("""
    # 排队

    **为什么要排队？**

    生成年度总结所需要的数据量较多，为避免给简书服务器造成压力，请求频率会被限制。

    一般情况下，提交排队申请五分钟后就可以查看到年终总结。
    """)

    put_link("登记排队", url=f"{GetUrl()}?app=JoinQueue")

    put_markdown("# 查看年终总结")

    put_link("查看年终总结", url=f"{GetUrl()}?app=ViewSummary")

    SetFooter(f"Version：{Config()['basic_data/version']} {Config()['basic_data/footer_content']}")


AddRunLog(3, "启动服务......")
start_server([JoinQueue, ViewSummary, index], port=Config()["service/port"])
