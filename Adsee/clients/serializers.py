from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import ClientProfile


class ClientProfileSerializer(serializers.ModelSerializer):
    # --- فیلدهای نمایشی برای TextChoices ---
    # این فیلدها مقدار خوانای انتخاب شده را نمایش می‌دهند
    advertiser_type_display = serializers.SerializerMethodField()
    kyc_status_display = serializers.SerializerMethodField()

    # --- فیلدهای URL برای تصاویر ---
    # برای نمایش URL تصاویر به جای داده‌های خام
    avatar_url = serializers.SerializerMethodField()
    id_or_registration_copy_url = serializers.SerializerMethodField()
    primary_ad_image_url = serializers.SerializerMethodField()
    primary_ad_banner_url = serializers.SerializerMethodField()
    advertising_license_copy_url = serializers.SerializerMethodField()

    # --- فیلدهای فقط‌خواندنی (Read-only) ---
    # برای جلوگیری از تغییر مستقیم این فیلدها از طریق API
    kyc_updated_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            # --- فیلدهای اصلی مدل ---
            'user', # ارتباط با کاربر (فقط برای نمایش یا تنظیم در صورت نیاز)

            # --- نوع تبلیغ‌دهنده ---
            'advertiser_type',
            'advertiser_type_display', # نمایش خوانا

            # --- اطلاعات هویتی ---
            'full_name',
            'national_id',
            'company_name',
            'national_economic_code',
            'registration_number',

            # --- مدارک احراز هویت ---
            'avatar', # فیلد اصلی برای آپلود
            'avatar_url', # URL تصویر آپلود شده
            'id_or_registration_copy',
            'id_or_registration_copy_url',

            # --- وضعیت KYC ---
            'kyc_status',
            'kyc_status_display', # نمایش خوانا
            'kyc_reject_reason',

            # --- متریال تبلیغاتی ---
            'primary_ad_image',
            'primary_ad_image_url',
            'primary_ad_banner',
            'primary_ad_banner_url',
            'advertising_description',
            'advertising_license_copy',
            'advertising_license_copy_url',

            # --- وضعیت فعالیت ---
            'is_advertising_active',

            # --- زمان‌ها (فقط برای نمایش) ---
            'created_at',
            'updated_at',
            'kyc_updated_at',
        ]

        # --- تنظیمات اضافی برای فیلدهای خاص ---
        # اگر می‌خواهید فیلد 'user' به صورت ID نمایش داده شود و قابل تنظیم باشد:
        extra_kwargs = {
            'user': {'write_only': True}, # کاربر فقط می‌تواند ID را ارسال کند، نه اینکه آن را بخواند
            'national_id': {'validators': [RegexValidator(r"^\d{10}$", message="کد ملی باید ۱۰ رقمی باشد.")]}, # دوباره تعریف Validator اگر لازم باشد
            # می‌توانید اینجا برای فیلدهای دیگر هم validator یا source را تعریف کنید
        }

    # --- متدهای کمکی برای نمایش مقادیر TextChoices ---
    def get_advertiser_type_display(self, obj):
        return obj.get_advertiser_type_display()

    def get_kyc_status_display(self, obj):
        return obj.get_kyc_status_display()

    # --- متدهای کمکی برای تولید URL تصاویر ---
    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_id_or_registration_copy_url(self, obj):
        if obj.id_or_registration_copy:
            return obj.id_or_registration_copy.url
        return None

    def get_primary_ad_image_url(self, obj):
        if obj.primary_ad_image:
            return obj.primary_ad_image.url
        return None

    def get_primary_ad_banner_url(self, obj):
        if obj.primary_ad_banner:
            return obj.primary_ad_banner.url
        return None

    def get_advertising_license_copy_url(self, obj):
        if obj.advertising_license_copy:
            return obj.advertising_license_copy.url
        return None

    # --- متد clean برای اعتبارسنجی‌های شرطی ---
    def clean(self):
        cleaned_data = super().clean()
        advertiser_type = cleaned_data.get('advertiser_type')

        # اعتبارسنجی فیلدهای حقیقی
        if advertiser_type == ClientProfile.AdvertiserType.REAL:
            full_name = cleaned_data.get('full_name')
            national_id = cleaned_data.get('national_id')

            if not full_name:
                raise serializers.ValidationError({"full_name": "نام کامل برای تبلیغ‌دهنده حقیقی الزامی است."})
            if not national_id:
                raise serializers.ValidationError({"national_id": "کد ملی برای تبلیغ‌دهنده حقیقی الزامی است."})
            if not cleaned_data.get('id_or_registration_copy'):
                 raise serializers.ValidationError({"id_or_registration_copy": "کپی مدرک هویتی (کارت ملی) برای تبلیغ‌دهنده حقیقی الزامی است."})

        # اعتبارسنجی فیلدهای حقوقی
        elif advertiser_type == ClientProfile.AdvertiserType.LEGAL:
            company_name = cleaned_data.get('company_name')
            national_economic_code = cleaned_data.get('national_economic_code')
            registration_number = cleaned_data.get('registration_number')

            if not company_name:
                raise serializers.ValidationError({"company_name": "نام شرکت برای تبلیغ‌دهنده حقوقی الزامی است."})
            # کد اقتصادی و شماره ثبت اختیاری هستند ولی اگر باشند باید فرمتشان درست باشد (اینجا صرفا چک می‌کنیم که خالی نباشند اگر وارد شده باشند)
            if national_economic_code and len(national_economic_code) < 5: # مثال: کد اقتصادی معمولا طولانی تر است
                 raise serializers.ValidationError({"national_economic_code": "کد اقتصادی وارد شده معتبر نیست."})
            if registration_number and len(registration_number) < 2: # مثال: شماره ثبت
                 raise serializers.ValidationError({"registration_number": "شماره ثبت وارد شده معتبر نیست."})
            if not cleaned_data.get('id_or_registration_copy'):
                 raise serializers.ValidationError({"id_or_registration_copy": "کپی مدرک ثبت شرکت/مجوز برای تبلیغ‌دهنده حقوقی الزامی است."})

        # اعتبارسنجی کلی برای KYC
        kyc_status = cleaned_data.get('kyc_status')
        if kyc_status == ClientProfile.KYCStatus.REJECTED:
            kyc_reject_reason = cleaned_data.get('kyc_reject_reason')
            if not kyc_reject_reason:
                raise serializers.ValidationError({"kyc_reject_reason": "دلیل رد شدن KYC الزامی است وقتی وضعیت رد شده باشد."})

        # اگر آواتار آپلود شد، باید فرمت مناسبی داشته باشد (اینجا به صورت کلی چک می‌شود)
        avatar = cleaned_data.get('avatar')
        if avatar:
            # می‌توانید محدودیت‌های بیشتری اینجا اضافه کنید، مثلاً حجم فایل یا نوع تصویر
            pass

        return cleaned_data

    # def create(self, validated_data):
    #     # اگر user در validated_data نباشد (مثلاً در ClientProfileList که فقط لیست برمی‌گرداند)
    #     # اما در ClientProfileDetail (POST) و MyClientProfileDetail (POST) user را خودمان تنظیم می‌کنیم
    #     # این بخش برای اطمینان بیشتر است
    #     user = validated_data.pop('user', None) # user را از داده‌ها جدا می‌کنیم
    #     if user and not self.context.get('request').user.is_anonymous:
    #          # اگر user در داده‌ها بود و کاربر فعلی لاگین است
    #          # اطمینان حاصل می‌کنیم که user ارسالی همان کاربر فعلی است (برای امنیت)
    #          if user != self.context.get('request').user:
    #              raise serializers.ValidationError("شما نمی‌توانید پروفایل کاربر دیگری را ایجاد یا ویرایش کنید.")
    #     elif not self.context.get('request').user.is_anonymous:
    #         # اگر user در داده‌ها نبود، کاربر فعلی را تنظیم می‌کنیم
    #         user = self.context.get('request').user
    #     else:
    #         # اگر کاربر لاگین نیست و user هم در داده‌ها نیست، خطا می‌دهیم
    #         raise serializers.ValidationError("کاربر برای ایجاد پروفایل الزامی است.")
    #
    #     # تنظیم زمان‌های ایجاد و به‌روزرسانی
    #     # اگر این فیلدها در validated_data باشند، ممکن است هنگام به‌روزرسانی مشکل ایجاد کنند
    #     # اما در هنگام ایجاد، معمولا باید توسط خود Django (default, auto_now) مدیریت شوند.
    #     # اگر بخواهید به صورت دستی تنظیم کنید:
    #     # now = timezone.now()
    #     # validated_data['created_at'] = now
    #     # validated_data['updated_at'] = now
    #     # validated_data['kyc_updated_at'] = now
    #
    #     # ایجاد پروفایل
    #     client_profile = ClientProfile.objects.create(user=user, **validated_data)
    #     return client_profile

    # --- متد update برای تنظیم خودکار برخی فیلدها ---
    # def update(self, instance, validated_data):
    #     # در هنگام به‌روزرسانی، برخی فیلدها ممکن است نیاز به تنظیمات خاصی داشته باشند
    #     # مثلاً اگر kyc_status تغییر کند، kyc_updated_at باید به‌روز شود.
    #     if 'kyc_status' in validated_data and validated_data['kyc_status'] != instance.kyc_status:
    #         validated_data['kyc_updated_at'] = timezone.now()
    #
    #     # اگر فایل‌های تصویری آپلود شدند، Django به صورت خودکار آن‌ها را مدیریت می‌کند.
    #     # اما اگر بخواهید حذف فایل‌های قدیمی را مدیریت کنید، باید این منطق را اضافه کنید.
    #
    #     # به‌روزرسانی instance با داده‌های معتبر
    #     return super().update(instance, validated_data)

