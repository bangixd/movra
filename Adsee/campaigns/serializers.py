from rest_framework import serializers
from .models import CampaignDesign, ProductImage, Template, Campaign, CampaignSetting, CampaignArea,\
    CampaignPricingRule, CampaignInvoice, PaymentTransaction
from clients.models import ClientProfile
from brands.models import Brand
from geo.models import City, Neighborhood, SuggestedRoute
from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField
from .utils import generate_invoice_number
from django.utils import timezone
from print_shops.serializers import PrintShopProfileSerializer


class BrandMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']


class ClientProfileMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['id', 'full_name']


class CampaignSerializer(serializers.ModelSerializer):
    client_detail = ClientProfileMiniSerializer(source='client', read_only=True)
    brand_detail = BrandMiniSerializer(source='brand_name', read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id',
            'client',
            'client_detail',
            'slogan',
            'brand_name',
            'brand_detail',
            'description',
            'start_date',
            'end_date',
            'status',
            'is_deleted',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['client', 'is_deleted', 'created_at', 'updated_at', 'start_date', 'end_date']

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'end_date must be greater than or equal to start_date.'
            })

        return attrs


class CampaignBriefSerializer(serializers.ModelSerializer):
    """برای نمایش خلاصه کمپین در لیست راننده"""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    area_type = serializers.CharField(source='area.area_type', read_only=True)
    max_driver = serializers.CharField(source='campaignsetting.max_driver', read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'slogan', 'brand_name', 'area_type',
            'start_date', 'end_date', 'max_driver'
        ]


class CampaignSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignSetting
        fields = [
            'id',
            'campaign',
            'active_days',
            'activity_hours_per_day',
            'max_driver',
            'vehicle_type',
        ]
        read_only_fields = ['id', 'campaign']

    def validate(self, attrs):
        """
        اعتبارسنجی‌های سفارشی برای داده‌های ورودی.
        """
        activity_hours_per_day = attrs.get('activity_hours_per_day', getattr(self.instance, 'activity_hours_per_day', None))
        vehicle_type = attrs.get('vehicle_type', getattr(self.instance, 'vehicle_type', None))

        # اعتبارسنجی ۱: اطمینان از اینکه activity_hours_per_day منطقی است
        # اگر محدودیت خاصی مثلاً بیشتر از ۱۲ ساعت در روز نباشد، اینجا اضافه می‌شود.
        if activity_hours_per_day and (activity_hours_per_day.hour > 12 or (activity_hours_per_day.hour == 12 and activity_hours_per_day.minute > 0)):
             raise serializers.ValidationError({
                 "activity_hours_per_day": "ساعات فعالیت روزانه نباید بیشتر از ۱۲ ساعت باشد."
             })

        if not vehicle_type:
            raise serializers.ValidationError({
                "vehicle_type": "نوع خودرو الزامی است."
            })

        return attrs

    def create(self, validated_data):
        """
        وقتی داده‌ها اعتبارسنجی شدند، یک نمونه جدید ایجاد می‌کند.
        """
        return CampaignSetting.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        وقتی داده‌ها اعتبارسنجی شدند، نمونه موجود را به‌روزرسانی می‌کند.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'name', 'variant', 'preview_image']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            'id',
            'campaign_design',
            'image',
        ]
        read_only_fields = ['id']


class CampaignDesignSerializer(serializers.ModelSerializer):
    print_shop_detail = PrintShopProfileSerializer(source='print_shop', read_only=True)
    template_detail = TemplateSerializer(source='template', read_only=True)
    product_images = ProductImageSerializer(many=True, read_only=True)

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
            'created_at',
            'updated_at',
            'product_images',
            'print_status',
            'estimated_ready_date'
        ]


class ProductImageNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']


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


class CityMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name"]


class NeighborhoodMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Neighborhood
        fields = ["id", "name", "city"]


class SuggestedRouteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuggestedRoute
        fields = ["id", "name"]


class CampaignAreaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignArea
        fields = [
            "id",
            "campaign",
            "area_type",
            "city",
            "neighborhood",
            "center_point",
            "radius_meter",
            "suggested_route",
            "region_polygon",
        ]

    def validate_campaign(self, campaign):
        request = self.context.get("request")
        if request and campaign.owner_id != request.user.id:
            raise serializers.ValidationError("You do not have access to this campaign.")
        return campaign

    def validate(self, attrs):
        instance = getattr(self, "instance", None)

        area_type = attrs.get("area_type", getattr(instance, "area_type", None))
        city = attrs.get("city", getattr(instance, "city", None))
        neighborhood = attrs.get("neighborhood", getattr(instance, "neighborhood", None))
        center_point = attrs.get("center_point", getattr(instance, "center_point", None))
        radius_meter = attrs.get("radius_meter", getattr(instance, "radius_meter", None))
        suggested_route = attrs.get("suggested_route", getattr(instance, "suggested_route", None))
        region_polygon = attrs.get("region_polygon", getattr(instance, "region_polygon", None))
        campaign = attrs.get("campaign", getattr(instance, "campaign", None))

        if not area_type:
            raise serializers.ValidationError({"area_type": "This field is required."})

        # OneToOne validation for create
        if not instance and campaign and CampaignArea.objects.filter(campaign=campaign).exists():
            raise serializers.ValidationError({
                "campaign": "A CampaignArea already exists for this campaign."
            })

        # Optional consistency checks
        if neighborhood and city and neighborhood.city_id != city.id:
            raise serializers.ValidationError({
                "neighborhood": "This neighborhood does not belong to the selected city."
            })

        if area_type == CampaignArea.AreaType.CIRCLE:
            errors = {}

            if not city:
                errors["city"] = "This field is required for CIRCLE."
            if not neighborhood:
                errors["neighborhood"] = "This field is required for CIRCLE."
            if not center_point:
                errors["center_point"] = "This field is required for CIRCLE."
            if not radius_meter:
                errors["radius_meter"] = "This field is required for CIRCLE."
            elif radius_meter <= 0:
                errors["radius_meter"] = "radius_meter must be greater than 0."

            if suggested_route:
                errors["suggested_route"] = "This field must not be set for CIRCLE."
            if region_polygon:
                errors["region_polygon"] = "This field must not be set for CIRCLE."

            if errors:
                raise serializers.ValidationError(errors)

        elif area_type == CampaignArea.AreaType.SUGGESTED_ROUTE:
            errors = {}

            if not city:
                errors["city"] = "This field is required for SUGGESTED_ROUTE."
            if not neighborhood:
                errors["neighborhood"] = "This field is required for SUGGESTED_ROUTE."
            if not suggested_route:
                errors["suggested_route"] = "This field is required for SUGGESTED_ROUTE."

            if center_point:
                errors["center_point"] = "This field must not be set for SUGGESTED_ROUTE."
            if radius_meter:
                errors["radius_meter"] = "This field must not be set for SUGGESTED_ROUTE."
            if region_polygon:
                errors["region_polygon"] = "This field must not be set for SUGGESTED_ROUTE."

            # Optional route consistency checks
            if suggested_route and city and getattr(suggested_route, "city_id", None) not in [None, city.id]:
                errors["suggested_route"] = "This route does not belong to the selected city."

            if suggested_route and neighborhood and getattr(suggested_route, "neighborhood_id", None) not in [None, neighborhood.id]:
                errors["suggested_route"] = "This route does not belong to the selected neighborhood."

            if errors:
                raise serializers.ValidationError(errors)

        elif area_type == CampaignArea.AreaType.FREE_AREA:
            errors = {}

            if not region_polygon:
                errors["region_polygon"] = "This field is required for FREE_AREA."

            if city:
                errors["city"] = "This field must not be set for FREE_AREA."
            if neighborhood:
                errors["neighborhood"] = "This field must not be set for FREE_AREA."
            if center_point:
                errors["center_point"] = "This field must not be set for FREE_AREA."
            if radius_meter:
                errors["radius_meter"] = "This field must not be set for FREE_AREA."
            if suggested_route:
                errors["suggested_route"] = "This field must not be set for FREE_AREA."

            if errors:
                raise serializers.ValidationError(errors)

        else:
            raise serializers.ValidationError({
                "area_type": "Invalid area_type."
            })

        return attrs


class CampaignAreaDetailSerializer(serializers.ModelSerializer):
    city = CityMiniSerializer(read_only=True)
    neighborhood = NeighborhoodMiniSerializer(read_only=True)
    suggested_route = SuggestedRouteMiniSerializer(read_only=True)

    targeting_geometry = GeometryField(source="get_targeting_area_geometry", read_only=True)

    class Meta:
        model = CampaignArea
        fields = [
            "id",
            "campaign",
            "area_type",
            "city",
            "neighborhood",
            "center_point",
            "radius_meter",
            "suggested_route",
            "region_polygon",
            "targeting_geometry",
            "created_at",
            "updated_at",
        ]


class CampaignAreaSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = CampaignArea
        fields = [
            "id",
            "campaign",
            "area_type",

            # City + Neighborhood
            "city",
            "neighborhood",

            # Circle
            "center_point",
            "radius_meter",

            # Suggested Route
            "suggested_route",

            # Free Polygon
            "region_polygon",

            "created_at",
            "updated_at",
        ]

        geo_field = "region_polygon"  # فقط برای FREE_AREA استفاده می‌شود

    # ----------------- VALIDATION -----------------

    def validate(self, attrs):
        area_type = attrs.get("area_type") or self.instance.area_type if self.instance else None

        city = attrs.get("city")
        neighborhood = attrs.get("neighborhood")

        center_point = attrs.get("center_point")
        radius_meter = attrs.get("radius_meter")

        suggested_route = attrs.get("suggested_route")
        region_polygon = attrs.get("region_polygon")

        # ------------------- CIRCLE -------------------
        if area_type == CampaignArea.AreaType.CIRCLE:
            missing = []
            if not city:
                missing.append("city")
            if not neighborhood:
                missing.append("neighborhood")
            if not center_point:
                missing.append("center_point")
            if not radius_meter:
                missing.append("radius_meter")

            if missing:
                raise serializers.ValidationError({
                    "detail": f"For CIRCLE mode, these fields are required: {', '.join(missing)}"
                })

            # فیلدهای نباید پر شوند
            forbidden = {
                "suggested_route": suggested_route,
                "region_polygon": region_polygon,
            }
            for name, value in forbidden.items():
                if value:
                    raise serializers.ValidationError({
                        name: f"{name} must NOT be provided when area_type is CIRCLE."
                    })

        # ------------------- SUGGESTED ROUTE -------------------
        elif area_type == CampaignArea.AreaType.SUGGESTED_ROUTE:
            if not city or not neighborhood:
                raise serializers.ValidationError({
                    "detail": "city and neighborhood are required for SUGGESTED_ROUTE."
                })

            if not suggested_route:
                raise serializers.ValidationError({
                    "suggested_route": "This field is required for SUGGESTED_ROUTE."
                })

            forbidden = {
                "center_point": center_point,
                "radius_meter": radius_meter,
                "region_polygon": region_polygon,
            }
            for name, value in forbidden.items():
                if value:
                    raise serializers.ValidationError({
                        name: f"{name} must NOT be provided when area_type is SUGGESTED_ROUTE."
                    })

        # ------------------- FREE POLYGON -------------------
        elif area_type == CampaignArea.AreaType.FREE_AREA:
            if not region_polygon:
                raise serializers.ValidationError({
                    "region_polygon": "region_polygon is required for FREE_AREA."
                })

            forbidden = {
                "city": city,
                "neighborhood": neighborhood,
                "center_point": center_point,
                "radius_meter": radius_meter,
                "suggested_route": suggested_route,
            }
            for name, value in forbidden.items():
                if value:
                    raise serializers.ValidationError({
                        name: f"{name} must NOT be provided when area_type is FREE_AREA."
                    })

        else:
            raise serializers.ValidationError({
                "area_type": "Invalid area_type."
            })

        return attrs


class CampaignPricingRuleSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = CampaignPricingRule
        fields = [
            "id",
            "key",
            "title",
            "value_type",
            "value",
            "is_active",
            "meta",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "value"]

    def get_value(self, obj):
        return obj.value

    def validate(self, attrs):
        value_type = attrs.get("value_type", getattr(self.instance, "value_type", None))

        # برای create/update، مقدار را از context/initial_data می‌خوانیم
        raw_value = self.initial_data.get("value", None)

        if value_type == CampaignPricingRule.ValueType.DECIMAL:
            attrs["_parsed_value"] = raw_value
        elif value_type == CampaignPricingRule.ValueType.INTEGER:
            attrs["_parsed_value"] = raw_value
        elif value_type == CampaignPricingRule.ValueType.BOOLEAN:
            attrs["_parsed_value"] = raw_value
        elif value_type == CampaignPricingRule.ValueType.TEXT:
            attrs["_parsed_value"] = raw_value
        elif value_type == CampaignPricingRule.ValueType.JSON:
            attrs["_parsed_value"] = raw_value
        else:
            raise serializers.ValidationError({"value_type": "Unsupported value_type."})

        return attrs

    def create(self, validated_data):
        value = validated_data.pop("_parsed_value", None)
        rule = CampaignPricingRule(**validated_data)
        rule.set_value(value)
        rule.save()
        return rule

    def update(self, instance, validated_data):
        value = validated_data.pop("_parsed_value", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        if value is not None:
            instance.set_value(value)

        instance.save()
        return instance


class CampaignCostCalculationSerializer(serializers.Serializer):
    drivers_count = serializers.IntegerField(min_value=1)
    days_count = serializers.IntegerField(min_value=1)
    hours_per_day = serializers.IntegerField(min_value=1)
    vehicle_type_id = serializers.IntegerField()
    design_type = serializers.ChoiceField(choices=["READY_TEMPLATE", "UPLOADED_DESIGN", "CUSTOM_DESIGN"])
    area_type = serializers.ChoiceField(choices=["FREE", "SUGGESTED_ROUTE", "CIRCLE"])


class CampaignInvoiceReadSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)
    client_name = serializers.SerializerMethodField()
    campaign_cost_summary = serializers.SerializerMethodField()

    class Meta:
        model = CampaignInvoice
        fields = [
            'id', 'campaign', 'campaign_title', 'client_name',
            'campaign_cost', 'campaign_cost_summary',
            'invoice_number', 'status',
            'subtotal_price', 'discount_amount', 'tax_amount', 'total_price',
            'expires_at', 'paid_at', 'snapshot', 'created_at'
        ]
        read_only_fields = fields  # کلاً read-only، چون این فقط برای نمایشه

    def get_client_name(self, obj):
        # فرض: هر campaign یه brand داره، هر brand یه client داره
        return obj.campaign.brand.client.get_full_name()

    def get_campaign_cost_summary(self, obj):
        # می‌تونی خلاصه‌ای از campaign_cost برگردونی
        # ولی چون snapshot داری، شاید لازم نباشه
        return {
            "subtotal": str(obj.subtotal_price),
            "discount": str(obj.discount_amount),
            "tax": str(obj.tax_amount),
            "total": str(obj.total_price)
        }


class CampaignInvoiceCreateSerializer(serializers.ModelSerializer):
    campaign = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.all()  # یا محدودشده به کمپین‌های آماده فاکتور
    )

    class Meta:
        model = CampaignInvoice
        fields = ['campaign']  # فقط campaign از سمت فرستنده
        # سایر فیلدها در create مقداردهی می‌شن

    def validate_campaign(self, campaign):
        # مثلاً چک کن که کمپین قبلاً فاکتور نداره (چون OneToOne)
        if CampaignInvoice.objects.filter(campaign=campaign).exists():
            raise serializers.ValidationError("این کمپین از قبل فاکتور دارد.")
        # چک کن که وضعیت کمپین قابل صدور فاکتور باشه
        return campaign

    def create(self, validated_data):
        campaign = validated_data['campaign']

        # گرفتن آخرین CampaignCost مرتبط با کمپین
        campaign_cost = campaign.costs.last()  # یا campaign.campaign_cost اگر OneToOne هست
        if not campaign_cost:
            raise serializers.ValidationError("هزینه‌ای برای این کمپین محاسبه نشده است.")

        # محاسبه مبالغ بر اساس CampaignCost
        # فرض: CampaignCost شامل subtotal, discount, tax, total به‌عنوان فیلد/متد
        subtotal = campaign_cost.subtotal_price
        discount = campaign_cost.discount_amount
        tax = campaign_cost.tax_amount
        total = campaign_cost.total_price

        # ساختن snapshot از آیتم‌ها و قوانین
        snapshot_data = {
            "cost_items": list(campaign_cost.items.values()),  # فرضاً items رابطه‌ست
            "pricing_rules": "..."  # می‌تونی خلاصه‌ای از قوانین ذخیره کنی
        }

        # تولید شماره فاکتور
        invoice_number = generate_invoice_number(campaign)

        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            campaign_cost=campaign_cost,
            invoice_number=invoice_number,
            status=CampaignInvoice.Status.ISSUED,
            subtotal_price=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            total_price=total,
            expires_at=timezone.now() + timedelta(days=15),
            snapshot=snapshot_data,
        )
        return invoice

class PaymentRequestSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField(required=True)

class PaymentVerifySerializer(serializers.Serializer):
    authority = serializers.CharField(max_length=200, required=True)
    status = serializers.CharField(max_length=10, required=True)  # OK / NOK

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ['id', 'invoice', 'authority', 'ref_id', 'amount', 'status', 'created_at']
        read_only_fields = fields