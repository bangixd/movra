from clients.models import ClientProfile, ClientDocument

def update_kyc_status(user):
    """
    به‌روزرسانی وضعیت KYC پروفایل بر اساس وضعیت مدارک.
    این متد بعد از هر تغییر در مدارک (آپلود جدید، تأیید/رد ادمین) فراخوانی می‌شود.
    """
    profile = user.client_profile
    docs = ClientDocument.objects.filter(user=user)

    # اگر حداقل یک مدرک رد شده باشد
    if docs.filter(status=ClientDocument.ApprovalStatus.REJECTED).exists():
        profile.kyc_step = ClientProfile.KYCStep.REJECTED
        profile.kyc_status = 'REJECTED'
    # اگر همه مدارک تأیید شده باشند و حداقل یک مدرک وجود داشته باشد
    elif docs.exists() and all(d.status == ClientDocument.ApprovalStatus.APPROVED for d in docs):
        profile.kyc_step = ClientProfile.KYCStep.APPROVED
        profile.kyc_status = 'APPROVED'
    # در غیر این صورت (در انتظار تأیید)
    else:
        profile.kyc_step = ClientProfile.KYCStep.VERIFICATION
        profile.kyc_status = 'PENDING'

    profile.save(update_fields=['kyc_step', 'kyc_status'])
