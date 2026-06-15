import logging
from typing import Tuple, Union

import requests
from django.conf import settings
from kavenegar import KavenegarAPI, APIException, HTTPException

logger = logging.getLogger(__name__)

SMS_SUCCESS_RESPONSE = 200
MELIPAYAMAK_SUCCESS_STATUS = 'عملیات موفق'
DEFAULT_TIMEOUT = 10



class KavenegarClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.KAVENEGAR_API_KEY
        self.api = KavenegarAPI(self.api_key)
        self.url = f'https://api.kavenegar.com/v1/{self.api_key}/verify/lookup.json'

    def send_sms(self, to: str, message: str) -> Tuple[bool, Union[int, str], str]:
        """
        Send SMS via Kavenegar.

        Args:
            to: Recipient phone number
            message: SMS text content

        Returns:
            Tuple of (success: bool, status: int|str, message: str)
        """
        payload = {
            'receptor': to,
            'toekn': message,
            'template': 'movra'
        }
        try:
            response = requests.get(url=self.url, params=payload, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            is_success = result.get('status') == SMS_SUCCESS_RESPONSE
            if is_success:
                logger.info("SMS sent to %s (status: %s)", to, result.get('status'))
            else:
                logger.error("SMS failed for %s: %s", to, result.get('status'))
            
            return is_success, result.get('status'), result.get('message', '')
        except (APIException, HTTPException) as e:
            logger.exception("Kavenegar API exception: %s", e)
            return False, str(e), ''
        except requests.RequestException as e:
            logger.exception("Kavenegar request failed: %s", e)
            return False, str(e), ''


class MeliPayamakClient:
    def __init__(self, base_url: str = None, key_url: str = None, from_number: str = None):
        """
        Initialize MeliPayamak SMS client.
        
        Args can be injected for testing; otherwise read from Django settings.
        """
        self.base_url = base_url or 'https://console.melipayamak.com/api/send'
        self.key_url = key_url or settings.MELIPAYAMAK_KEY
        self.from_number = from_number or settings.MELIPAYAMAK_FROM

    def send_sms(self, to: str, message: str) -> Tuple[bool, str, str]:
        """
        Send a single SMS via MeliPayamak.

        Args:
            to: Recipient phone number (e.g., '09120001122')
            message: SMS text content

        Returns:
            Tuple of (success: bool, status: str, receipt_id: str)
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
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            is_success = result.get('status') == MELIPAYAMAK_SUCCESS_STATUS
            if is_success:
                logger.info("SMS sent to %s (receipt: %s)", to, result.get('recId'))
            else:
                logger.error("SMS failed for %s: %s", to, result.get('status'))
            
            return is_success, result.get('status', ''), result.get('recId', '')
        except requests.RequestException as e:
            logger.exception("SMS sending failed: %s", e)
            return False, str(e), ''
