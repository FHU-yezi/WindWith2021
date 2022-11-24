> 停止维护声明
>
> 该项目已于 2022 年 11 月 26 日停止维护，不再发布功能与安全性更新。
>
> 由于简书接口变动，目前数据采集功能已不可用。

# 简书 2021「风语」年度总结

不知道为什么，简书官方一直没有出 2021 年的年终总结，刚好自己有技术，就准备用自己的能力呈现一个更加完整的年终总结。

# 开源库

- Web 服务：PyWebIO
- 数据获取：JianshuResearchTools
- 数据处理：Pandas
- 数据库 ORM：Peewee
- 图表：PyEcharts
- 分词：Jieba
- 词云图：Wordcloud

# 部署

## 推荐方式：Docker Compose

请修改 `config.yaml` 文件，将其中的 `service - data_path` 改为 `/data`（Docker Compose 在部署过程中会自动创建 `Volume` 并映射到该目录，用于存放数据与日志）。

```
docker compose up -d
```

服务将在 80 端口启动，如需要变更端口，请修改 `config.yaml` 和 `docker-compose.yml` 文件。

## 手动部署

```
poetry install --no-dev
```

或

```
pip install -r requirements.txt
```

```
python main.py
```

如需要修改端口，请更改 `config.yaml` 文件中的 `service - port` 项。（该文件会在第一次运行时自动生成）