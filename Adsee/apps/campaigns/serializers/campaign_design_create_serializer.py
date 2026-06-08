from rest_framework import serializers
from campaigns.models import CampaignDesign, ProductImage
from campaigns.serializers import ProductImageNestedSerializer

class CampaignDesignCreateSerializer(serializers.ModelSerializer):
    product_images = ProductImageNestedSerializer(many=True, required=False)

    class Meta:
        model = CampaignDesign
        fields = [
            'campaign',
            'design_type',
            'template',
            'user_uploaded_file',
            'designer_note',
            'logo_brand',
            'product_images',
        ]

    def validate(self, attrs):
        design_type = attrs.get('design_type')
        template = attrs.get('template')

        if design_type == CampaignDesign.DesignType.DEFAULT_TEMPLATE:
            if not template:
                raise serializers.ValidationError({
                    'template': 'برای حالت Default Template انتخاب قالب الزامی است.'
                })
        else:
            if template is not None:
                raise serializers.ValidationError({
                    'template': 'این فیلد فقط برای Default Template مجاز است.'
                })

        return attrs

    def create(self, validated_data):
        product_images_data = validated_data.pop('product_images', [])
        campaign_design = CampaignDesign.objects.create(**validated_data)
        # ساخت عکس‌ها
        for image_data in product_images_data:
            ProductImage.objects.create(
                campaign_design=campaign_design,
                **image_data
            )

        return campaign_design
