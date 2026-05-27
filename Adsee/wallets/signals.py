from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from trips.models import Trip
from .models import Wallet, Transaction

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet_for_user(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(user=instance)


@receiver(post_save, sender=Trip)
def create_income_transaction(sender, instance, created, **kwargs):
    if instance.status == Trip.Status.COMPLETED and instance.earnings > 0:
        wallet = instance.driver.user.wallet
        # جلوگیری از ایجاد تراکنش تکراری
        if not Transaction.objects.filter(trip=instance, transaction_type=Transaction.TransactionType.INCOME).exists():
            Transaction.objects.create(
                wallet=wallet,
                amount=instance.earnings,
                transaction_type=Transaction.TransactionType.INCOME,
                status=Transaction.Status.SUCCESS,
                description=f'درآمد سفر #{instance.id}',
                trip=instance
            )
            wallet.balance += instance.earnings
            wallet.total_earnings += instance.earnings
            wallet.save()