import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AnalyticsServiceClient:
    def __init__(self):
        self.base_url = settings.ANALYTICS_SERVICE_URL
        self.api_key = settings.ANALYTICS_API_KEY

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def check_conn(self):
        payload = {
            "bucket_seconds": 300,
            "points": [
                {
                    "lat": 35.7219,
                    "lon": 51.3347,
                    "speed": 45,
                    "heading": 120,
                    "timestamp": 1715172000
                }
            ]
        }
        resp = requests.post(f"{self.base_url}/analyze-trip",
                             json=payload, headers=self._headers())
        if not resp.ok:
            print("ERROR:", resp.status_code, resp.text)  # ← اضافه کن
        resp.raise_for_status()
        return resp.json()

    def register_vehicle(self, vehicle_id: str, vehicle_display_name: str = "", **extra_fields):
        """ ثبت یک خودروی جدید در سرویس خارجی """
        payload = {
            "vehicle_id": vehicle_id,
            "vehicle_display_name": vehicle_display_name or vehicle_id,
            **extra_fields

        }
        try:
            resp = requests.post(
                f"{self.base_url}/vehicles",
                json=payload,
                headers=self._headers(),
                timeout=5
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Vehicle registration failed: {e}")
            return None

    def send_single_location(self, vehicle_id: str, campaign_id: str,
                             session_id: str, lat: float, lon: float,
                             speed: float, heading: float, timestamp: int,
                             vehicle_display_name: str = ""):
        """ ارسال یک نقطه GPS تکی """
        payload = {
            "vehicle_id": vehicle_id,
            "vehicle_display_name": vehicle_display_name or vehicle_id,
            "campaign_id": campaign_id,
            "session_id": session_id,
            "lat": lat,
            "lon": lon,
            "speed": speed,
            "heading": heading,
            "timestamp": timestamp
        }
        resp = requests.post(
            f"{self.base_url}/gps-points",
            json=payload,
            headers=self._headers(),
            timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def calculate_earnings(self, vehicle_id: str, start_ts: int, end_ts: int):
        """ دریافت درآمد محاسبه‌شده برای بازه‌ی زمانی """
        resp = requests.get(
            f"{self.base_url}/vehicles/{vehicle_id}/analysis/earnings",
            params={"start_ts": start_ts, "end_ts": end_ts},
            headers=self._headers(),
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()   # {"earnings": 12345.67}