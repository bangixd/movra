import requests
from django.conf import settings

class AnalyticsServiceClient:
    def __init__(self):
        self.base_url = settings.ANALYTICS_SERVICE_URL
        self.api_key = settings.ANALYTICS_API_KEY

    def _headers(self):
        return {"x-api-key": self.api_key, "Content-Type": "application/json"}

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

    def send_single_location(self, vehicle_id, campaign_id, session_id,
                             lat, lon, speed, heading, timestamp,
                             display_name=""):
        payload = {
            "vehicle_id": vehicle_id,
            "vehicle_display_name": display_name,
            "campaign_id": campaign_id,
            "session_id": session_id,
            "lat": lat,
            "lon": lon,
            "speed": speed,
            "heading": heading,
            "timestamp": timestamp
        }
        resp = requests.post(f"{self.base_url}/gps-points",
                             json=payload, headers=self._headers())
        if not response.ok:
            print("ERROR:", response.status_code, response.text)  # ← اضافه کن
        resp.raise_for_status()
        return resp.json()

    def calculate_earnings(self, vehicle_id, start_ts, end_ts):
        resp = requests.get(
            f"{self.base_url}/vehicles/{vehicle_id}/analysis/earnings",
            params={"start_ts": start_ts, "end_ts": end_ts},
            headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()