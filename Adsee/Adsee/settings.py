import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# GDAL_LIBRARY_PATH
GDAL_LIBRARY_PATH = os.getenv("GDAL_LIBRARY_PATH")
GEOS_LIBRARY_PATH = os.getenv("GEOS_LIBRARY_PATH")

# EXTERNAL API
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL")
ANALYTICS_API_KEY = os.getenv("ANALYTICS_API_KEY")


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True" # Default to False if not set

ALLOWED_HOSTS = []
#ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',


    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework_gis',

    "drf_yasg",

    "django_filters",
    "corsheaders",
    "django_ratelimit",

    # My apps
    "accounts",
    "drivers",
    "clients",
    "brands",
    "campaigns",
    "vehicles",
    "geo",
    "trips",
    "print_shops",
    "notifications",

]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',
]

ROOT_URLCONF = 'Adsee.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Adsee.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# import dj_database_url
# DATABASES = {
#     'default': dj_database_url.config(
#         default=os.environ.get('DATABASE_URL')
#     )
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

# مسیر فایل‌های استاتیک و مدیا
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        'rest_framework.authentication.SessionAuthentication', # debug mode
        # 'rest_framework.authentication.SessionAuthentication', # debug mode

    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
        'rest_framework.permissions.AllowAny',
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',  # برای کاربران ناشناس (بر اساس IP)
        'rest_framework.throttling.UserRateThrottle'  # برای کاربران لاگین شده (بر اساس user ID)
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',  #  10 درخواست در دقیقه برای کاربران ناشناس
        'user': '100/minute',  #  100 درخواست در دقیقه برای کاربران لاگین
        'otp_request': '1/minute',
        'otp_verify': '1/minute',
    }
}


# JWT setting
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1), # زمان اعتبار توکن دسترسی
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),    # زمان اعتبار توکن بازسازی
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.getenv("SIGNING_KEY"),
    "VERIFY_SIGNATURE": True,
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_WEB_TOKEN_IN_CALL_ARGS": False,

    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SAMESITE": "Lax", # یا "Strict"
    "AUTH_COOKIE_NAME": "access_token",
    "REFRESH_COOKIE_NAME": "refresh_token",
    "REFRESH_COOKIE_SECURE": True,
    "REFRESH_COOKIE_HTTP_ONLY": True,
    "REFRESH_COOKIE_SAMESITE": "Lax",
}

AUTH_USER_MODEL = "accounts.User"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # مثال برای فرانت‌اند React در پورت 3000
    "http://127.0.0.1:3000",
    # هر دامنه دیگری که فرانت‌اندت روی آن اجرا می‌شود
]

# OTP and SMS
OTP_CODE_EXPIRY_MINUTES = os.getenv("OTP_CODE_EXPIRY_MINUTES")

# CACHES
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        }
    }
}

#DRF-YASG swagger
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic',
        },
        'Bearer': {
            'in': 'header',
            'name': 'Authorization',
            'type': 'apiKey',
        },
    }
}


# CELERY
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tehran'

# ZARINPAL
ZARINPAL_MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID")          # از زرین‌پال دریافت کن
ZARINPAL_SANDBOX = os.getenv("ZARINPAL_SANDBOX")                             # در محیط واقعی False کن
ZARINPAL_CALLBACK_URL = os.getenv("ZARINPAL_CALLBACK_URL")   # آدرس بازگشت