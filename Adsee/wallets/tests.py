from django.test import TestCase
from accounts.models import User
from wallet.models import Wallet

class WalletSignalTest(TestCase):
    def test_wallet_created_automatically(self):
        user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.assertTrue(Wallet.objects.filter(user=user).exists())