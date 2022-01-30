from queue import Queue
from threading import Thread
from time import sleep
from typing import Dict, Tuple

from httpx import HTTPError
from httpx import post as httpx_post

from config_manager import Config
from log_manager import AddRunLog

message_queue: Queue = Queue()


def GetMessageSendConfig() -> Tuple[str, str, str]:
    if not all((Config()["message"]["app_id"],
                Config()["message"]["app_secret"],
                Config()["message"]["email"])):
        raise ValueError("消息发送服务配置错误")
    app_id: str = Config()["message"]["app_id"]
    app_secret: str = Config()["message"]["app_secret"]
    email: str = Config()["message"]["email"]
    return app_id, app_secret, email


def GetAuthorizationCode(app_id: str, app_secret: str) -> str:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {"app_id": app_id, "app_secret": app_secret}
    response = httpx_post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                          headers=headers, json=data)
    response.raise_for_status()
    result = f"Bearer {response.json()['tenant_access_token']}"
    AddRunLog(4, "成功获取飞书授权码")
    return result


def SendTextMessage(message: str) -> None:
    data = {
        "msg_type": "text",
        "content": {"text": message}
    }
    AddRunLog(4, f"一条文本消息加入队列，内容为：{message}")
    message_queue.put(data)


def SendWarningMessage(title: str, message: str) -> None:
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "orange"
            },
            "elements": [{
                "tag": "markdown",
                "content": message
            }]
        }
    }
    AddRunLog(4, f"一条警告消息加入队列，标题为：{title}，内容为：{message}")
    message_queue.put(data)


def SendErrorMessage(title: str, message: str) -> None:
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "red"
            },
            "elements": [{
                "tag": "markdown",
                "content": message
            }]
        }
    }
    AddRunLog(4, f"一条错误消息加入队列，标题为：{title}，内容为：{message}")
    message_queue.put(data)


def _SendMessageByFeishu(authorization_code: str, email: str, data: Dict) -> None:
    headers = {"Content-Type": "application/json; charset=utf-8",
               "Authorization": authorization_code}
    data["email"] = email

    response = httpx_post("https://open.feishu.cn/open-apis/message/v4/send/",
                          headers=headers, json=data)
    response.raise_for_status()
    if response.json()["code"] == 0:
        AddRunLog(3, f"发送了一条飞书消息，message_id：{response.json()['data']['message_id']}")
    else:
        AddRunLog(1, f"发送飞书消息失败，错误码：{response.json()['code']}")


def main() -> None:
    while True:
        data = message_queue.get(block=True)  # 阻塞获取待发送的消息
        if not Config()["message/enable_message_sender"]:
            AddRunLog(2, "有待发送的消息，但消息发送已被禁用")
            message_queue.put(data)  # 把消息放回队列
            sleep(30)  # 等待三十秒后再次尝试
            continue
        try:
            app_id, app_secret, email = GetMessageSendConfig()
        except ValueError:
            AddRunLog(1, "消息发送服务配置错误")
            message_queue.put(data)  # 把消息放回队列
            sleep(180)  # 等待三分钟后再次尝试发送
            continue

        try:
            authorization_code = GetAuthorizationCode(app_id, app_secret)
        except HTTPError as e:
            AddRunLog(1, f"获取授权码时发生错误：{str(e)}")
            message_queue.put(data)  # 把消息放回队列
            sleep(30)  # 等待三十秒后再次尝试发送
            continue

        try:
            _SendMessageByFeishu(authorization_code, email, data)
        except HTTPError as e:
            AddRunLog(1, f"发送飞书消息时发生错误：{str(e)}")
            message_queue.put(data)  # 把消息放回队列
            sleep(30)  # 等待三十秒后再次尝试发送
            continue


def init() -> None:
    message_send_thread = Thread(target=main, daemon=True)  # 设置为守护线程，避免造成主线程无法退出
    message_send_thread.start()
