from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User
from django.core.exceptions import ValidationError
import re


class UserCreationForm(forms.ModelForm):
    """
    فرم ساخت کاربر در ادمین
    """
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("phone", "role")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2

    def clean_phone(self):
        """
        ولیدیشن شماره موبایل:
        - باید ۱۱ رقم باشد
        - با ۰۹ شروع شود (یا فقط ۹)
        """
        phone = self.cleaned_data.get("phone")
        if phone:
            # حذف کاراکترهای اضافی مثل فاصله یا خط تیره
            phone = re.sub(r"[^\d]", "", phone)

            # بررسی طول و شروع با ۰۹ یا ۹
            if not (phone.startswith("09") and len(phone) == 11) and not (phone.startswith("9") and len(phone) == 10):
                raise ValidationError(
                    "Invalid phone number format. It should be 11 digits starting with '09' or 10 digits starting with '9'.")
            # اگر با 9 شروع میشه، 0 به اولش اضافه کن
            if phone.startswith("9") and len(phone) == 10:
                phone = "0" + phone

            # بررسی اینکه شماره قبلا در دیتابیس وجود نداشته باشد (موقع ساخت)
            if User.objects.filter(phone=phone).exists():
                raise ValidationError("This phone number is already registered.")

        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    فرم ویرایش کاربر در ادمین
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            "phone",
            "password",
            "role",
            "is_active",
            "is_staff",
        )

    def clean_phone(self):
        """
        ولیدیشن شماره موبایل موقع ویرایش:
        - طول ۱۱ رقم و شروع با ۰۹
        - باید منحصر به فرد باشد (مگر اینکه خود کاربر باشد)
        """
        phone = self.cleaned_data.get("phone")
        user_id = self.instance.pk  # گرفتن آیدی کاربر فعلی

        if phone:
            phone = re.sub(r"[^\d]", "", phone)

            if not (phone.startswith("09") and len(phone) == 11):
                raise ValidationError("Invalid phone number format. It should be 11 digits starting with '09'.")

            # چک کردن اینکه این شماره موبایل متعلق به کاربر دیگری نباشد
            if User.objects.exclude(pk=user_id).filter(phone=phone).exists():
                raise ValidationError("This phone number is already registered.")

        return phone

    def clean_password(self):
        return self.initial["password"]
