from django.db import models
from support.models.support_FAQ_category_model import FAQCategory


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
