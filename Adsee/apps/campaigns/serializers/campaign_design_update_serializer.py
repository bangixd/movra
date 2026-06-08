from rest_framework import serializers
from campaigns.models import CampaignDesign, ProductImage
from .product_image_nested_serializer import ProductImageNestedSerializer

class CampaignDesignUpdateSerializer(serializers.ModelSerializer):
    product_images = ProductImageNestedSerializer(many=True, required=False)
    replace_product_images = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = CampaignDesign
        fields = [
            'design_type',
            'template',
            'user_uploaded_file',
            'final_design_file',
            'logo_brand',
            'designer_note',
            'status',
            'product_images',
            'replace_product_images',
        ]

    def validate(self, attrs):
        design_type = attrs.get('design_type', getattr(self.instance, 'design_type'))
        template = attrs.get('template', getattr(self.instance, 'template'))

        if design_type == CampaignDesign.DesignType.DEFAULT_TEMPLATE and not template:
            raise serializers.ValidationError({
                'template': 'در حالت Default Template انتخاب قالب ضروری است.'
            })

        if design_type != CampaignDesign.DesignType.DEFAULT_TEMPLATE and template is not None:
            raise serializers.ValidationError({
                'template': 'این فیلد فقط در حالت Default Template مجاز است.'
            })

        return attrs

    def update(self, instance, validated_data):
        product_images_data = validated_data.pop('product_images', [])
        replace = validated_data.pop('replace_product_images', False)

        # آپدیت فیلدهای دیگر
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # اگر کاربر خواست همه تصاویر قبلی پاک شود
        if replace:
            instance.product_images.all().delete()

        # تصاویر جدید را اضافه کنیم
        for img in product_images_data:
            ProductImage.objects.create(
                campaign_design=instance,
                **img
            )

        return instance
