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
        "port": 80,
        "data_path": "./"
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
    "perf": {
        "enable_jieba_parallel": True,
        "data_getters_max_count": 5
    },
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
