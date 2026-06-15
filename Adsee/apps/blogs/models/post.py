from django.db import models


class Author(models.Model):
    """مدل نویسندهٔ پست‌های وبلاگ"""
    full_name = models.CharField(max_length=150)
    bio = models.TextField(blank=True, null=True, help_text="بیوگرافی کوتاه نویسنده")
    avatar = models.ImageField(upload_to='blog/authors/', blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.full_name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, allow_unicode=True)
    author = models.ForeignKey(
        'Author',
        on_delete=models.CASCADE,
        related_name='blog_posts',
        null=True, blank=True
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posts'
    )
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    estimated_reading_time = models.PositiveIntegerField(
        default=0,
        help_text="زمان مطالعه به دقیقه"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def full_text(self):
        return ' '.join(block.text for block in self.blocks.filter(block_type__in=['text', 'heading', 'quote']))


class PostBlock(models.Model):
    class BlockType(models.TextChoices):
        HEADING = 'heading', 'Heading'
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'
        QUOTE = 'quote', 'Quote'

    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='blocks'
    )
    block_type = models.CharField(max_length=20, choices=BlockType.choices, default=BlockType.TEXT)
    title = models.CharField(max_length=255, blank=True, help_text="For heading blocks")
    text = models.TextField(blank=True, help_text="For text/quote blocks")
    image = models.ImageField(upload_to='blog/blocks/', blank=True, null=True, help_text="For image blocks")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.get_block_type_display()} - {self.post.title}"