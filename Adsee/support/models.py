from django.db import models
from django.conf import settings


class SupportContent(models.Model):
    class ContentType(models.TextChoices):
        CONTACT = 'CONTACT', 'تماس با ما'
        FAQ = 'FAQ', 'سوالات متداول'
        RULES = 'RULES', 'قوانین و مقررات شهری'  # جدید

    type = models.CharField(max_length=20, choices=ContentType.choices)
    title = models.CharField(max_length=200)
    body = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(upload_to='support/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class SiteSetting(models.Model):
    # اطلاعات اصلی برند
    brand_name = models.CharField(max_length=200, verbose_name="نام برند")
    brand_logo = models.ImageField(upload_to='site/', blank=True, null=True, verbose_name="لوگو")
    about_text = models.TextField(verbose_name="متن درباره ما")
    about_image = models.ImageField(upload_to='site/', blank=True, null=True, verbose_name="تصویر درباره ما")

    # راه‌های ارتباطی
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")

    # شبکه‌های اجتماعی (به‌صورت JSON)
    social_links = models.JSONField(default=dict, blank=True, verbose_name="شبکه‌های اجتماعی")
    # مثال:
    # {
    #     "instagram": "https://instagram.com/...",
    #     "telegram": "https://t.me/...",
    #     "twitter": "https://twitter.com/..."
    # }

    # میزان جایزه برای دعوت از دوستان رانندگان
    referral_reward_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50000,
        verbose_name="مبلغ جایزه دعوت از دوستان (تومان)"
    )


    is_active = models.BooleanField(default=True, verbose_name="فعال")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.brand_name


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'باز'
        CLOSED = 'CLOSED', 'بسته'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200, verbose_name="موضوع")
    name = models.CharField(max_length=100, verbose_name="نام و نام خانوادگی")
    phone = models.CharField(max_length=15, verbose_name="شماره تماس")
    message = models.TextField(verbose_name="پیام")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تیکت پشتیبانی"
        verbose_name_plural = "تیکت‌های پشتیبانی"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.user.phone}"


class FAQCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="آیکون")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "دسته‌بندی سوالات"
        verbose_name_plural = "دسته‌بندی‌های سوالات"
        ordering = ['order']

    def __str__(self):
        return self.name


class FAQItem(models.Model):
    category = models.ForeignKey(
        FAQCategory,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name="دسته‌بندی"
    )
    question = models.CharField(max_length=300, verbose_name="سوال")
    answer = models.TextField(verbose_name="پاسخ")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"
        ordering = ['category', 'order']

    def __str__(self):
        return self.question