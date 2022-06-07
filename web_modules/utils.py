from pywebio.session import eval_js, run_js


def LinkInHTML(name: str, link: str) -> str:
    """
    获取 HTML 格式的链接
    """
    return f'<a href="{link}" style="color: #0056B3">{name}</a>'


def SetFooter(html: str) -> None:
    """
    设置底栏内容
    """
    run_js(f"$('footer').html('{html}')")


def GetUrl() -> str:
    """
    获取当前 URL
    """
    return eval_js("window.location.href").split("?")[0]


def SetLocalStorage(key: str, value: str) -> None:
    """
    设置 localStorage
    """
    run_js(f"localStorage.setItem('{key}', '{value}')")


def GetLocalStorage(key: str) -> str:
    """
    获取 localStorage
    """
    return eval_js(f"localStorage.getItem('{key}')")


def CleanUserUrl(user_url: str) -> str:
    """清理 user_url，去除其中的空格和无用参数
    """
    user_url = user_url.strip()
    return user_url.split("?")[0]
