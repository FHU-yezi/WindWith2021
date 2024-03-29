FROM python:3.10.8-slim

ENV TZ Asia/Shanghai

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    -r requirements.txt \
    --no-cache-dir \
    --no-compile \
    --disable-pip-version-check \
    --quiet \
    -i https://mirrors.aliyun.com/pypi/simple

COPY . .

CMD ["python", "main.py"]
