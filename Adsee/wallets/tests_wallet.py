# wallet/tests_wallet.py
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User, ClientProfile
from wallet.models import Wallet, Transaction

class ClientWalletTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.wallet = Wallet.objects.get(user=self.client_user)
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    def test_deposit(self):
        response = self.api.post('/api/wallet/deposit/', {'amount': 100000}, format='json')
        self.assertEqual(response.status_code, 200)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100000)
        self.assertTrue(Transaction.objects.filter(transaction_type='DEPOSIT').exists())

    def test_withdrawal(self):
        self.wallet.balance = 50000
        self.wallet.save()
        response = self.api.post('/api/wallet/withdraw/', {'amount': 30000}, format='json')
        self.assertEqual(response.status_code, 200)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 20000)
        tx = Transaction.objects.get(transaction_type='WITHDRAWAL')
        self.assertEqual(tx.amount, 30000)