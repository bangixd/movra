from rest_framework import serializers
from campaigns.models import CampaignDesign
from print_shops.serializers import PrintShopProfileSerializer
from .template_serializer import TemplateSerializer
from .product_image_serializer import ProductImageSerializer

class CampaignDesignSerializer(serializers.ModelSerializer):
    print_shop_detail = PrintShopProfileSerializer(source='print_shop', read_only=True)
    template_detail = TemplateSerializer(source='template', read_only=True)
    product_images = ProductImageSerializer(many=True, read_only=True)
    banner_type = serializers.PrimaryKeyRelatedField(read_only=True)


    class Meta:
        model = CampaignDesign
        fields = [
            'id',
            'campaign',
            'design_type',
            'template',
            'template_detail',
            'user_uploaded_file',
            'final_design_file',
            'banner_type',
            'logo_brand',
            'designer_note',
            'status',
            'product_images',
            'created_at',
            'updated_at',
            'print_shop', 'print_shop_detail',
            'print_status', 'estimated_ready_date',
        ]
        read_only_fields = [
            'id',
            'campaign',
            'created_at',
            'updated_at',
            'product_images',
            'print_status',
            'estimated_ready_date'
        ]
