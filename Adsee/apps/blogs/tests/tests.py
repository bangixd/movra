from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from accounts.models import User
from blogs.models import Category, Post, PostBlock


class BlogModelTest(TestCase):
    """تست مدل‌های وبلاگ"""

    def setUp(self):
        print("\n========== SETUP BLOG MODELS ==========")
        self.user = User.objects.create_user(phone='09120001122', role=User.Role.ADMIN)
        self.category = Category.objects.create(name='تکنولوژی', slug='technology')
        self.post = Post.objects.create(
            title='پست اول',
            slug='post-1',
            author=self.user,
            category=self.category,
            is_published=True,
            published_at=timezone.now()
        )
        print("✅ مدل‌ها آماده شدند")

    def test_category_creation(self):
        print("\n--- TEST: Category Creation ---")
        self.assertEqual(self.category.name, 'تکنولوژی')
        self.assertEqual(self.category.slug, 'technology')
        print("✅ دسته‌بندی درست ساخته شد")

    def test_post_creation(self):
        print("\n--- TEST: Post Creation ---")
        self.assertEqual(self.post.title, 'پست اول')
        self.assertEqual(self.post.author, self.user)
        self.assertTrue(self.post.is_published)
        print("✅ پست درست ساخته شد")

    def test_post_blocks(self):
        print("\n--- TEST: Post Blocks ---")
        block1 = PostBlock.objects.create(
            post=self.post,
            block_type=PostBlock.BlockType.HEADING,
            title='فصل اول',
            order=1
        )
        block2 = PostBlock.objects.create(
            post=self.post,
            block_type=PostBlock.BlockType.TEXT,
            text='این یک متن است',
            order=2
        )
        self.assertEqual(self.post.blocks.count(), 2)
        self.assertEqual(self.post.blocks.first().block_type, 'heading')
        print("✅ بلوک‌های پست درست متصل شدند")


class BlogAPITest(TestCase):
    """تست APIهای عمومی وبلاگ"""

    def setUp(self):
        print("\n========== SETUP BLOG API ==========")
        self.client = APIClient()
        self.user = User.objects.create_user(phone='09120001122', role=User.Role.ADMIN)
        self.category = Category.objects.create(name='کسب‌و‌کار', slug='business')
        self.post = Post.objects.create(
            title='پست عمومی',
            slug='public-post',
            author=self.user,
            category=self.category,
            is_published=True,
            published_at=timezone.now()
        )
        PostBlock.objects.create(post=self.post, block_type='text', text='متن عمومی', order=1)
        self.list_url = '/v1/blogs/'
        self.detail_url = f'/v1/blogs/{self.post.id}/'
        self.categories_url = '/v1/blogs/categories/'
        print("✅ API آماده شد")

    def test_list_posts(self):
        print("\n--- TEST: List Posts ---")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'پست عمومی')
        print("✅ لیست پست‌ها برگشت داده شد")

    def test_filter_posts_by_category(self):
        print("\n--- TEST: Filter Posts by Category ---")
        # یک پست دیگر در دسته‌بندی دیگر
        other_cat = Category.objects.create(name='عمومی', slug='general')
        Post.objects.create(
            title='پست دیگر',
            slug='other',
            author=self.user,
            category=other_cat,
            is_published=True
        )
        response = self.client.get(self.list_url, {'category': 'business'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'پست عمومی')
        print("✅ فیلتر دسته‌بندی درست کار کرد")

    def test_retrieve_post_detail(self):
        print("\n--- TEST: Retrieve Post Detail ---")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('blocks', response.data)
        self.assertEqual(len(response.data['blocks']), 1)
        self.assertEqual(response.data['blocks'][0]['text'], 'متن عمومی')
        print("✅ جزئیات پست با بلوک‌ها برگشت داده شد")

    def test_list_categories(self):
        print("\n--- TEST: List Categories ---")
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'کسب‌و‌کار')
        print("✅ لیست دسته‌بندی‌ها برگشت داده شد")