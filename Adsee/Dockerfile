#FROM osgeo/gdal:ubuntu-small-3.8.4
#FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.3
FROM docker.arvancloud.ir/osgeo/gdal:ubuntu-small-latest


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# جایگزینی مخازن رسمی اوبونتو با آینه داخلی ایران
RUN echo "deb https://repo.abrha.net/ubuntu jammy main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb https://repo.abrha.net/ubuntu jammy-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb https://repo.abrha.net/ubuntu jammy-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb https://repo.abrha.net/ubuntu jammy-security main restricted universe multiverse" >> /etc/apt/sources.list

# نصب پیش‌نیازهای کامپایل و PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev python3-pip \
    && rm -rf /var/lib/apt/lists/*

# تنظیم مسیر GDAL (معمولاً خودکار شناسایی می‌شود، اما این خط هم بی‌ضرر است)
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

WORKDIR /app

COPY requirements.txt .
#ENV PIP_INDEX_URL=https://mirror-pypi.runflare.com/simple
ENV PIP_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]