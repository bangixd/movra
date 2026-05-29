import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Adsee.settings')

app = Celery('Adsee')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'expire-invoices-every-5-minutes': {
        'task': 'services.tasks.expire_pending_invoices',
        'schedule': crontab(minute='*/5'),
    },
}