import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 10

class AnalyticsServiceClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None,
                 session: Optional[requests.Session] = None, timeout: int = DEFAULT_TIMEOUT):
        """Analytics service client.

        base_url and api_key can be injected for testing; otherwise read from Django settings.
        A requests.Session with retry logic is used for connection pooling and resilience.
        """
        self.base_url = base_url or settings.ANALYTICS_SERVICE_URL
        self.api_key = api_key or settings.ANALYTICS_API_KEY
        self.timeout = timeout
        self.session = session or self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = kwargs.pop("headers", None) or self._headers()
        timeout = kwargs.pop("timeout", self.timeout)
        try:
            resp = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                logger.debug("Non-JSON response from %s: %s", url, resp.text)
                return resp.text
        except requests.exceptions.RequestException as e:
            logger.exception("Analytics request failed: %s %s", method, url)
            raise

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
        resp = self._request("POST", "/analyze-trip", json=payload)
        return resp

    def register_vehicle(self, vehicle_id: str, display_name: str = "", **extra_fields):
        """ ثبت یک خودروی جدید در سرویس خارجی """
        payload = {
            "vehicle_id": vehicle_id,
            "display_name": display_name or vehicle_id,
            **extra_fields

        }
        try:
            resp = self._request("POST", "/vehicles", json=payload, timeout=5)
            return resp
        except requests.exceptions.RequestException as e:
            logger.error("Vehicle registration failed: %s", e)
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
        return self._request("POST", "/gps-points", json=payload, timeout=5)

    def calculate_earnings(self, vehicle_id: str, start_ts: int, end_ts: int):
        """ دریافت درآمد محاسبه‌شده برای بازه‌ی زمانی """
        return self._request("GET", f"/vehicles/{vehicle_id}/analysis/earnings",
                            params={"start_ts": start_ts, "end_ts": end_ts})

    def send_batch_locations(self, points: list):
        """
        ارسال دسته‌ای GPS
        points: لیست دیکشنری‌های حاوی vehicle_id, campaign_id, session_id, lat, lon, speed, heading, timestamp
        """
        return self._request("POST", "/gps-points/batch", json=points)

    def get_analysis_summary(self, vehicle_id: str, start_ts: int, end_ts: int):
        """خلاصهٔ تحلیل (active_time, distance, exposure, impressions, confidence)"""
        return self._request("GET", f"/vehicles/{vehicle_id}/analysis/summary",
                            params={"start_ts": start_ts, "end_ts": end_ts})

    def get_analysis_full(self, vehicle_id: str, start_ts: int, end_ts: int, bucket_seconds=300):
        """گزارش کامل تحلیل"""
        return self._request("GET", f"/vehicles/{vehicle_id}/analysis",
                            params={"start_ts": start_ts, "end_ts": end_ts, "bucket_seconds": bucket_seconds})

    def create_analysis_run(self, vehicle_id: str, start_ts: int, end_ts: int):
        """ایجاد snapshot برای تسویه (analysis-run)"""
        return self._request("POST", f"/vehicles/{vehicle_id}/analysis-runs",
                            json={"start_ts": start_ts, "end_ts": end_ts})