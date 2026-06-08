from django.db import models
from django.utils import timezone
from .campaign_goal_model import CampaignGoal

class Campaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        WAITING_FOR_DESIGN = "WAITING_FOR_DESIGN"
        WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"
        ACTIVE = "ACTIVE"
        PAUSED = "PAUSED"
        COMPLETED = "COMPLETED"
        REJECTED = "REJECTED"

    goal = models.ForeignKey(CampaignGoal, on_delete=models.SET_NULL, null=True, blank=True)

    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="campaigns"
    )

    slogan = models.CharField(max_length=255)
    brand_name = models.ForeignKey(
        'brands.Brand',
        on_delete=models.PROTECT,
        related_name='campaigns'
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.DRAFT)

    is_deleted = models.BooleanField(default=False)

    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.slogan} - {self.client_id}"

    def is_active_now(self):
        now = timezone.localtime()
        return (
            self.status == self.Status.ACTIVE
            and self.start_date <= now.date() <= self.end_date
        )

