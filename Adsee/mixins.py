class SafeGetQuerysetMixin:
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.model.objects.none()
        return super().get_queryset()