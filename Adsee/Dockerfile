# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# نصب پیش‌نیازهای سیستم
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev \
    gdal-bin libgdal-dev \
    && rm -rf /var/lib/apt/lists/* \

ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# کپی اسکریپت ورود
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]