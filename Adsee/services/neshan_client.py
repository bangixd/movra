import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class NeshanClient:
    def __init__(self):
        self.api_key = settings.NESHAN_API_KEY
        self.reverse_url = settings.NESHAN_REVERSE_URL

    def reverse_geocode(self, lat: float, lng: float):
        """
        دریافت آدرس متنی از روی مختصات
        """
        headers = {
            'Api-Key': self.api_key,
        }
        params = {
            'lat': lat,
            'lng': lng,
        }
        try:
            response = requests.get(
                self.reverse_url,
                headers=headers,
                params=params,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            # ساختار پاسخ نشان:
            # {
            #   "status": "OK",
            #   "results": [
            #     {
            #       "formatted_address": "استان تهران، تهران، خیابان ولیعصر، ...",
            #       "components": {...}
            #     }
            #   ]
            # }
            if data.get('status') == 'OK' and data.get('results'):
                return {
                    'address': data['results'][0].get('formatted_address', ''),
                    'components': data['results'][0].get('components', {}),
                }
            return None
        except Exception as e:
            logger.error(f"Neshan reverse geocode failed: {e}")
            return None