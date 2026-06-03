#!/bin/bash
set -e

# اعمال مایگریشن‌ها
python manage.py migrate --noinput

# جمع‌آوری فایل‌های استاتیک
python manage.py collectstatic --noinput --clear

exec "$@"