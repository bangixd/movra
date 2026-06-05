from django.contrib import admin
from .models import DriverDocument

@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'status', 'submitted_at', 'reviewed_at']
    list_filter = ['status', 'document_type']
    readonly_fields = ['submitted_at']