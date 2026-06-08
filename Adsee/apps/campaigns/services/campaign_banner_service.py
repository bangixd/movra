from trips.models import Trip


class CampaignBannerService:
    """سرویس مدیریت تصاویر بنر کمپین"""

    @staticmethod
    def get_banner_images(campaign, request=None):
        """
        برگرداندن لیست تصاویر بنرهای نصب‌شده برای یک کمپین

        Args:
            campaign: نمونهٔ کمپین
            request: (اختیاری) برای ساخت absolute URI

        Returns:
            list[dict]: لیست دیکشنری‌های حاوی اطلاعات راننده و تصاویر
        """
        trips = Trip.objects.filter(
            campaign=campaign,
            sticker_image__isnull=False
        ).select_related('driver')

        data = []
        for trip in trips:
            item = {
                'driver_name': trip.driver.full_name if trip.driver else '',
                'sticker_image': None,
                'driver_car_image': None,
            }
            # ساخت absolute URI فقط اگر request داده شده باشد
            if request:
                if trip.sticker_image:
                    item['sticker_image'] = request.build_absolute_uri(trip.sticker_image.url)
                if trip.driver_car_image:
                    item['driver_car_image'] = request.build_absolute_uri(trip.driver_car_image.url)
            else:
                # اگر request نبود، همان URL نسبی را برگردان
                if trip.sticker_image:
                    item['sticker_image'] = trip.sticker_image.url
                if trip.driver_car_image:
                    item['driver_car_image'] = trip.driver_car_image.url

            data.append(item)
        return data