from django.test import TestCase
from rest_framework.test import APIClient
from support.models import FAQCategory, FAQItem

class FAQAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat1 = FAQCategory.objects.create(name='عمومی', order=1)
        self.cat2 = FAQCategory.objects.create(name='حساب کاربری', order=2)
        FAQItem.objects.create(category=self.cat1, question='سوال ۱', answer='پاسخ ۱', order=1)
        FAQItem.objects.create(category=self.cat1, question='سوال ۲', answer='پاسخ ۲', order=2)
        FAQItem.objects.create(category=self.cat2, question='سوال ۳', answer='پاسخ ۳', order=1)

    def test_faq_list(self):
        response = self.client.get('/v1/support/faq/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # دو دسته
        self.assertEqual(response.data[0]['name'], 'عمومی')
        self.assertEqual(len(response.data[0]['faqs']), 2)  # دو سوال در دسته عمومی
        self.assertEqual(response.data[1]['faqs'][0]['question'], 'سوال ۳')