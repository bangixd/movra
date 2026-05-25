import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ZarinpalGateway:
    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.sandbox = settings.ZARINPAL_SANDBOX

        if self.sandbox:
            self.base_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate'
        else:
            self.base_url = 'https://api.zarinpal.com/pg/rest/WebGate'

    def send_request(self, amount, description, email=None, mobile=None):
        """
        ارسال درخواست پرداخت به زرین‌پال
        برگشت: (success, authority/error_message, status_code)
        """
        data = {
            'MerchantID': self.merchant_id,
            'Amount': int(amount),  # به تومان (عدد صحیح)
            'Description': description,
            'CallbackURL': self.callback_url,
        }
        if email:
            data['Email'] = email
        if mobile:
            data['Mobile'] = mobile

        try:
            response = requests.post(
                f'{self.base_url}/PaymentRequest.json',
                json=data,
                timeout=10
            )
            result = response.json()
            if result.get('Status') == 100:
                authority = result['Authority']
                payment_url = f'https://sandbox.zarinpal.com/pg/StartPay/{authority}' if self.sandbox else f'https://www.zarinpal.com/pg/StartPay/{authority}'
                return True, payment_url, None
            else:
                error = f"Error {result.get('Status')}: {result}"
                return False, None, error
        except Exception as e:
            logger.error(f"Zarinpal request failed: {e}")
            return False, None, str(e)

    def verify_payment(self, authority, amount):
        """
        تأیید تراکنش پس از بازگشت از درگاه
        """
        data = {
            'MerchantID': self.merchant_id,
            'Authority': authority,
            'Amount': int(amount),
        }
        try:
            response = requests.post(
                f'{self.base_url}/PaymentVerification.json',
                json=data,
                timeout=10
            )
            result = response.json()
            if result.get('Status') == 100:
                return True, result.get('RefID')
            else:
                return False, result.get('Status')
        except Exception as e:
            logger.error(f"Zarinpal verification failed: {e}")
            return False, str(e)