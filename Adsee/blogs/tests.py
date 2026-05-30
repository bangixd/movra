from django.test import TestCase
from rest_framework.test import APIClient
from .models import Post

class BlogTest(TestCase):
    def setUp(self):
        self.post1 = Post.objects.create(title="اول", slug="first", content="متن اول", is_published=True)
        self.post2 = Post.objects.create(title="دوم", slug="second", content="متن دوم", is_published=False)
        self.client = APIClient()

    def test_public_list_shows_only_published(self):
        response = self.client.get('/api/blog/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "اول")

    def test_public_detail(self):
        response = self.client.get('/api/blog/first/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['content'], "متن اول")

    def test_unpublished_not_visible(self):
        response = self.client.get('/api/blog/second/')
        self.assertEqual(response.status_code, 404)

    def test_admin_can_create_post(self):
        from accounts.models import User
        admin = User.objects.create_superuser(phone='09990000000', password='admin')
        self.client.force_authenticate(user=admin)
        response = self.client.post('/api/blog/admin/', {
            'title': 'سوم',
            'slug': 'third',
            'content': '...',
            'is_published': True
        }, format='json')
        self.assertEqual(response.status_code, 201)