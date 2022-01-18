from peewee import (BooleanField, CharField, DateTimeField, IntegerField,
                    Model, SqliteDatabase)


class RunLog(Model):
    id = IntegerField(primary_key=True)
    time = DateTimeField()
    level = IntegerField()
    message = CharField()

    class Meta:
        database = SqliteDatabase("log.db")


class ViewLog(Model):
    id = IntegerField(primary_key=True)
    time = DateTimeField()
    user_url = CharField(null=True)  # 可以为空
    is_mobile = BooleanField()
    is_tablet = BooleanField()
    is_pc = BooleanField()
    browser_name = CharField()
    os_name = CharField()
    language = CharField()
    ip = CharField()

    class Meta:
        database = SqliteDatabase("log.db")


def InitDB():
    RunLog.create_table()
    ViewLog.create_table()


InitDB()  # 导入模块时初始化数据库
