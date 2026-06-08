from services.neshan_client import NeshanClient


class GeocodingService:
    """Service for geocoding operations"""

    @staticmethod
    def reverse_geocode(lat: float, lng: float) -> dict:
        """
        Convert latitude/longitude to a human-readable address.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            dict: Address data from Neshan API

        Raises:
            ValueError: if lat/lng are invalid
            ConnectionError: if the external API fails
        """
        if not lat or not lng:
            raise ValueError("عرض و طول جغرافیایی الزامی است")

        client = NeshanClient()
        result = client.reverse_geocode(lat, lng)

        if not result:
            raise ConnectionError("دریافت آدرس با خطا مواجه شد")

        return result