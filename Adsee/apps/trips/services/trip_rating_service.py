from trips.models import Trip


class TripRatingService:
    """سرویس امتیازدهی به راننده"""

    @staticmethod
    def rate_trip(user, trip_id: int, rating: int, feedback: str = '') -> Trip:
        if rating not in range(1, 6):
            raise ValueError("امتیاز باید بین ۱ تا ۵ باشد")

        trip = Trip.objects.get(
            id=trip_id,
            campaign__brand_name__client__user=user,
            status=Trip.Status.COMPLETED
        )
        trip.rating = rating
        trip.feedback = feedback
        trip.save()
        return trip