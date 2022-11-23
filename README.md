# 简书 2021「风语」年度总结

不知道为什么，简书官方一直没有出 2021 年的年终总结，刚好自己有技术，就准备用自己的能力呈现一个更加完整的年终总结。

**本服务已不再进行功能更新。**

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

服务将在 80 端口启动，如需要变更端口，请修改 `docker-compose.yml` 文件。

**`config.yaml` 文件中的 `service - port` 是服务启动的端口，建议修改映射，而不是在该文件中改动服务端口**

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