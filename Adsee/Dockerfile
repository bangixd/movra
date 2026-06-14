# Dockerfile
FROM ubuntu:jammy

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN echo "deb [trusted=yes] https://repo.abrha.net/ubuntu jammy main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb [trusted=yes] https://repo.abrha.net/ubuntu jammy-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb [trusted=yes] https://repo.abrha.net/ubuntu jammy-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb [trusted=yes] https://repo.abrha.net/ubuntu jammy-security main restricted universe multiverse" >> /etc/apt/sources.list


RUN echo 'Acquire::https::Verify-Peer "false";' > /etc/apt/apt.conf.d/99ignore-cert && \
    echo 'Acquire::https::Verify-Host "false";' >> /etc/apt/apt.conf.d/99ignore-cert

# حالا apt می‌تواند از HTTPS بدون مشکل دانلود کند
RUN apt-get update && apt-get install -y ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# (اختیاری) حالا که ca-certificates نصب شد، می‌توانید فایل موقت را حذف کنید
# تا امنیت TLS دوباره برقرار شود:
RUN rm -f /etc/apt/apt.conf.d/99ignore-cert

# نصب پیش‌نیازهای سیستم
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-dev python3.11-venv \
    gcc g++ libpq-dev \
    gdal-bin libgdal-dev \
    && rm -rf /var/lib/apt/lists/* \


ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
ENV PIP_INDEX_URL=https://mirror.abrha.net/repository/pypi/simple
ENV PIP_TRUSTED_HOST=mirror.abrha.net

# create a virtual environment with Python 3.11
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# now pip is available
RUN pip install --upgrade pip

WORKDIR /app


COPY requirements.txt .
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt


COPY . .

# کپی اسکریپت ورود
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]