import requests
from django.conf import settings
import logging
from kavenegar import *


logger = logging.getLogger(__name__)


class KavenegarClient:
    def __init__(self):
        self.api_key = '646871784E586D7A596F4B672B594B465A58667861417A4536433455437A4E487051796D376F78423241733D'
        self.sender = ''
        self.api = KavenegarAPI(self.api_key)
        self.url = f'https://api.kavenegar.com/v1/{self.api_key}/verify/lookup.json'

    def send_sms(self, to: str, message: str):
        payload = {
            'receptor': to,
            'toekn': message,
            'template': 'movra'
        }
        try:
            response = requests.get(url=self.url,params=payload)
            result = response.json()
            if result.get('status') == 200:
                logger.info(f"SMS sent to {to}")
                return True, result.get('status'), result.get('message')
            else:
                logger.error(f"SMS failed: {result.get('status')}")
                return False, result.get('status'), result.get('message')
        except APIException as e:
            print(e)
        except HTTPException as e:
            print(e)


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
