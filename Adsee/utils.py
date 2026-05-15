from kavenegar import *
import os
from datetime import datetime
import requests
import uuid
import json


def send_otp_sms(phone_number, otp_code):
    print(f"Sending OTP {otp_code} to {phone_number}")
    api = KavenegarAPI('726551794F4E726648364C4863614245757548795271704547714B755551754D64584F786E6E617A6967593D')
    params = {'sender': '2000660110',
                'receptor': phone_number,
                'message': f'کد تایید شما : {otp_code}'}
    response = api.sms_send(params)
    print(response)
    return response


def product_image_upload_path(instance, filename):
    return f'products/user_{instance.user.id}/{filename}'


def upload_document_path(instance, filename):
    """
    مسیر آپلود فایل‌ها را بر اساس نوع مدرک، شناسه کاربر و تاریخ تعیین می‌کند.
    """
    user_id = instance.user.id
    doc_type = instance.document_type
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # حفظ نام اصلی فایل یا ایجاد نام منحصر به فرد
    base, ext = os.path.splitext(filename)
    return f'kyc_documents/{user_id}/{doc_type}/{timestamp}{ext}'


# EXTERNAL_API_KEY = "your_api_key_here"
def send_kyc_to_external_service(user_profile, documents):
    # آماده‌سازی داده‌ها برای ارسال
    if user_profile.user.role == 'Driver':
        EXTERNAL_API_URL = "https://external-kyc-service.com/verify/kyc"
        payload = {
            "driver_id": str(user_profile.user.id), # شناسه کاربر شما
            "request_id": str(uuid.uuid4()), # یک شناسه یکتا برای این درخواست
            "documents": [
                {
                    "type": doc.document_type,
                    "file_url": doc.file.url # یا خود فایل را base64 encode کنید
                } for doc in documents
            ],
            "driver_details": { # اطلاعات تکمیلی راننده
                "name": user_profile.user.get_full_name(),
                "national_id": user_profile.national_id_number, # اگر در پروفایل ذخیره شده
                # ... سایر اطلاعات ...
            }
        }
    elif user_profile.user.role == 'Client':
        if user_profile.advertiser_type == 'Real':
            EXTERNAL_API_URL = "https://external-kyc-service.com/verify/kyc"
            payload = {
                "driver_id": str(user_profile.user.id), # شناسه کاربر شما
                "request_id": str(uuid.uuid4()), # یک شناسه یکتا برای این درخواست
                "documents": [
                    {
                        "type": doc.document_type,
                        "file_url": doc.file.url # یا خود فایل را base64 encode کنید
                    } for doc in documents
                ],
                "driver_details": { # اطلاعات تکمیلی راننده
                    "name": user_profile.user.get_full_name(),
                    "national_id": user_profile.national_id_number, # اگر در پروفایل ذخیره شده
                    # ... سایر اطلاعات ...
                }
            }
        elif user_profile.advertiser_type == 'Legal':
            EXTERNAL_API_URL = "https://external-kyc-service.com/verify/kyc"
            payload = {
                "driver_id": str(user_profile.user.id), # شناسه کاربر شما
                "request_id": str(uuid.uuid4()), # یک شناسه یکتا برای این درخواست
                "documents": [
                    {
                        "type": doc.document_type,
                        "file_url": doc.file.url # یا خود فایل را base64 encode کنید
                    } for doc in documents
                ],
                "driver_details": { # اطلاعات تکمیلی راننده
                    "name": user_profile.user.get_full_name(),
                    "national_id": user_profile.national_id_number, # اگر در پروفایل ذخیره شده
                    # ... سایر اطلاعات ...
                }
            }

    headers = {
        "Authorization": f"Bearer {EXTERNAL_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        # اگر سرویس خارجی فایل را مستقیم می‌گیرد (multipart/form-data)
        # files = {'national_id_file': open(documents[0].file.path, 'rb'), ...}
        # response = requests.post(EXTERNAL_API_URL, files=files, headers=headers)

        # اگر سرویس خارجی JSON می‌گیرد (مثلاً با URL فایل‌ها)
        response = requests.post(EXTERNAL_API_URL, json=payload, headers=headers)
        response.raise_for_status() # بررسی خطاها

        result = response.json()
        request_id = result.get('request_id') # یا هر کلیدی که سرویس برمی‌گرداند

        # ذخیره request_id و وضعیت اولیه در دیتابیس خودتان
        # مثلاً یک مدل جدید KycVerificationRequest بسازید
        # KycVerificationRequest.objects.create(
        #     driver_profile=driver_profile,
        #     external_request_id=request_id,
        #     status='SUBMITTED', # وضعیت اولیه
        #     submitted_at=timezone.now()
        # )

        # توی این قسمت باید با استفاده از سلری یک ورکر ایجاد کنم تا مراحل ارسال و دریافت پاسخ رو خودش خودکار انجام بده

        return request_id, True

    except requests.exceptions.RequestException as e:
        print(f"Error sending KYC to external service: {e}")
        # ثبت خطا در لاگ سیستم شما
        return None, False


# def check_kyc_status(request_id):
#     external_status_url = f"{EXTERNAL_API_URL}/{request_id}"
#     headers = {"Authorization": f"Bearer {EXTERNAL_API_KEY}"}
#
#     try:
#         response = requests.get(external_status_url, headers=headers)
#         response.raise_for_status()
#         result = response.json()
#
#         external_status = result.get('status') # مثلاً 'APPROVED', 'REJECTED', 'PENDING'
#         external_reject_reason = result.get('reject_reason')
#
#         # بروزرسانی وضعیت در دیتابیس شما
#         kyc_request = KycVerificationRequest.objects.get(external_request_id=request_id)
#         kyc_request.status = external_status
#         kyc_request.reject_reason = external_reject_reason
#         if external_status in ['APPROVED', 'REJECTED']:
#             kyc_request.reviewed_at = timezone.now()
#         kyc_request.save()
#
#         # بروزرسانی وضعیت کلی DriverProfile
#         profile = kyc_request.driver_profile
#         if external_status == 'APPROVED':
#             profile.kyc_status = 'APPROVED'
#             profile.kyc_reject_reason = None
#         elif external_status == 'REJECTED':
#             profile.kyc_status = 'REJECTED'
#             profile.kyc_reject_reason = external_reject_reason
#         else: # PENDING
#             profile.kyc_status = 'PENDING'
#
#         profile.kyc_reviewed_at = timezone.now()
#         profile.save()
#
#         return external_status, True
#
#     except requests.exceptions.RequestException as e:
#         print(f"Error checking KYC status for {request_id}: {e}")
#         return None, False
#     except KycVerificationRequest.DoesNotExist:
#         print(f"KycVerificationRequest not found for {request_id}")
#         return None, False