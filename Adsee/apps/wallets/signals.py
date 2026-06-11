from django.db.models.signals import post_save
from decimal import Decimal
from django.dispatch import receiver
from django.conf import settings
from trips.models import Trip
from .models import Wallet, Transaction, ReferralReward
from support.models import SiteSetting

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

@receiver(post_save, sender=Trip)
def process_referral_reward(sender, instance, created, **kwargs):
    if instance.status == Trip.Status.COMPLETED and instance.earnings > 0:
        driver = instance.driver
        # بررسی کن که این اولین سفر تکمیل‌شدهٔ این راننده است
        completed_trips = Trip.objects.filter(
            driver=driver,
            status=Trip.Status.COMPLETED
        ).exclude(id=instance.id).count()

        if completed_trips == 0 and driver.referred_by:
            # جلوگیری از ایجاد جایزه تکراری
            if not ReferralReward.objects.filter(trip=instance).exists():
                # خواندن مبلغ از SiteSetting
                site_setting = SiteSetting.objects.filter(is_active=True).first()
                reward_amount = site_setting.referral_reward_amount if site_setting else 50000                # ثبت جایزه
                ReferralReward.objects.create(
                    driver=driver.referred_by,
                    referred_driver=driver,
                    trip=instance,
                    amount=reward_amount
                )
                # واریز به کیف پول
                wallet = driver.referred_by.user.wallet
                wallet.balance += reward_amount
                wallet.total_earnings += reward_amount
                wallet.save()
                # ثبت تراکنش
                Transaction.objects.create(
                    wallet=wallet,
                    amount=reward_amount,
                    transaction_type=Transaction.TransactionType.BONUS,
                    status=Transaction.Status.SUCCESS,
                    description=f'جایزه دعوت راننده {driver.full_name}',
                    trip=instance
                )

@receiver(post_save, sender=Transaction)
def update_wallet_balance(sender, instance, created, **kwargs):
    if not created:   # فقط بار اول
        return
    if instance.status == Transaction.Status.SUCCESS:
        wallet = instance.wallet
        if instance.transaction_type == Transaction.TransactionType.INCOME:
            wallet.balance += Decimal(instance.amount)
            wallet.total_earnings += Decimal(instance.amount)
        elif instance.transaction_type == Transaction.TransactionType.WITHDRAWAL:
            wallet.balance -= Decimal(instance.amount)
        wallet.save()