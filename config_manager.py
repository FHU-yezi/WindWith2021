from os import path as os_path

from yaml import SafeLoader
from yaml import dump as yaml_dump
from yaml import load as yaml_load

_DEFAULT_CONFIG = {
    "basic_data": {
        "version": "0.0.0",
        "footer_content": "Made with PyWebIO and ♥"
    },
    "service": {
        "port": 80
    },
    "debug": {
        "enable_debug": False,
        "print_log_level": 3
    },
    "word_split": {
        "enable_stopwords": True,
        "enable_hotwords": True
    },
    "auth": {
        "enable_banlist": True
    },
    "notification": {
        "enable": False,
        "closable": True,
        "title": None,
        "content": None
    },
    "status_monitor": {
        "enable_status_monitor": True,
        "memory_percent_warn": 0.7,
        "memory_percent_error": 0.8,
        "disk_percent_warn": 0.8,
        "disk_percent_error": 0.9,
        "user_to_process_warn": 30,
        "user_to_process_error": 50,
        "user_failed_warn": 5,
        "user_failed_error": 10,
        "views_count_last_60_seconds_warn": 60,
        "views_count_last_60_seconds_error": 100,
        "views_count_last_5_minutes_warn": 200,
        "views_count_last_5_minutes_error": 300,
        "views_count_last_30_minutes_warn": 1500,
        "views_count_last_30_minutes_error": 2000,
        "warns_count_last_5_minutes_warn": 10,
        "warns_count_last_5_minutes_error": 20,
        "errors_count_last_5_minutes_warn": 3,
        "errors_count_last_5_minutes_error": 5,
        "criticals_count_last_5_minutes_warn": 1,
        "criticals_count_last_5_minutes_error": 3,
    },
    "message": {
      "enable_message_sender": True,
      "app_id": "",
      "app_secret": "",
      "email": ""
    },
    "perf": {
        "enable_jieba_parallel": True,
        "data_getters_max_count": 5
    }
}


class Config():
    def __new__(cls) -> "Config":
        # 单例模式
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not os_path.exists("config.yaml"):  # 没有配置文件
            with open("config.yaml", "w", encoding="utf-8") as f:
                yaml_dump(_DEFAULT_CONFIG, f, allow_unicode=True, indent=4)
            self._config_dict = _DEFAULT_CONFIG
        else:  # 有配置文件
            with open("config.yaml", "r", encoding="utf-8") as f:
                self._config_dict = yaml_load(f, Loader=SafeLoader)

    def __getitem__(self, item):
        item_path = item.split("/")
        result = self._config_dict
        for now_path in item_path:
            result = result[now_path]
        return result

    def refresh(self):
        self.__init__()


def InitConfig():
    Config()  # 初始化日志文件


InitConfig()
