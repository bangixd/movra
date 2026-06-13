import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MeliPayamakClient:
    def __init__(self):
        self.base_url = 'https://console.melipayamak.com/api/send'
        self.key_url = settings.MELIPAYAMAK_KEY
        self.from_number = settings.MELIPAYAMAK_FROM

    def send_sms(self, to: str, message: str):
        """
        ارسال یک پیامک تکی
        to: شماره گیرنده (مثلاً '09120001122')
        message: متن پیامک
        """

        payload = {
            'from': self.from_number,
            'to': to,
            'text': message,
        }
        try:
            response = requests.post(
                f'{self.base_url}/simple/{self.key_url}',
                json=payload,
                timeout=10
            )
            result = response.json()
            if result.get('status') == 'عملیات موفق':
                logger.info(f"SMS sent to {to}")
                return True, result.get('status'), result.get('recId')
            else:
                logger.error(f"SMS failed: {result.get('status')}")
                return False, result.get('status'), result.get('recId')
        except Exception as e:
            logger.error(f"SMS sending exception: {e}")
            return False, str(e)

