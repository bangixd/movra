from django.db import models

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
