from django.utils import timezone
from datetime import timedelta
from rest_framework.viewsets import ModelViewSet, ViewSet, ReadOnlyModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from django.core.serializers.json import DjangoJSONEncoder
import json
from decimal import Decimal
from django.http import HttpResponse
import csv
from rest_framework.decorators import api_view, permission_classes
from .pricing import calculate_campaign_cost
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from trips.models import TripAnalysis, Trip
from trips.serializers import TripAnalysisSerializer
from rest_framework import generics, permissions
from rest_framework import status, filters, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from .models import CampaignDesign, Campaign, CampaignSetting, Template, CampaignArea, CampaignPricingRule,\
    CampaignInvoice, PaymentTransaction, BannerType, CampaignGoal, CampaignPackage
from services.payment_gateway import ZarinpalGateway
from .serializers import CampaignDesignSerializer, CampaignSerializer, CampaignSettingSerializer, TemplateSerializer,\
    CampaignDesignCreateSerializer, CampaignDesignUpdateSerializer,\
    CampaignAreaDetailSerializer, CampaignAreaCreateSerializer, CampaignPricingRuleSerializer,\
    CampaignCostCalculationSerializer, CampaignInvoiceReadSerializer, CampaignInvoiceCreateSerializer,\
    PaymentRequestSerializer, PaymentVerifySerializer, PaymentTransactionSerializer, BannerTypeSerializer,\
    CampaignGoalSerializer, CampaignPackageSerializer
from permissions import IsClientUser, IsOwnerOrAdmin
from vehicles.models import VehicleType
from mixins import SafeGetQuerysetMixin
from .pricing import get_rule_value
from .utils import generate_invoice_number

class CampaignViewSet(ModelViewSet):
    permission_classes = [IsClientUser, IsOwnerOrAdmin]
    serializer_class = CampaignSerializer

    def get_queryset(self):
        return Campaign.objects.filter(is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user.client_profile)

class CampaignSettingViewSet(SafeGetQuerysetMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, IsClientUser, IsOwnerOrAdmin]
    serializer_class = CampaignSettingSerializer
    queryset = CampaignSetting.objects.all() # یا فیلتر شده بر اساس campaign

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Campaign.objects.none()
        campaign_id = Campaign.objects.filter(client=self.request.user)
        if campaign_id:
            return CampaignSetting.objects.filter(campaign_id=campaign_id)
        return CampaignSetting.objects.none()

    def perform_create(self, serializer):
        campaign_id = Campaign.objects.filter(client=self.request.user.client_profile)
        campaign = Campaign.objects.get(pk=campaign_id) # یا هر روش دیگری برای دریافت Campaign
        serializer.save(campaign=campaign)

    def perform_update(self, serializer):
        campaign_id = Campaign.objects.filter(client=self.request.user.client_profile)
        campaign = Campaign.objects.get(pk=campaign_id)
        serializer.save(campaign=campaign)

class CampaignGoalListView(ListAPIView):
    queryset = CampaignGoal.objects.filter(is_active=True)
    serializer_class = CampaignGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

class BannerTypeListView(ListAPIView):
    queryset = BannerType.objects.filter(is_active=True)
    serializer_class = BannerTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class TemplateListView(ListAPIView):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

class CampaignDesignViewSet(ModelViewSet):
    permission_classes = [IsClientUser, IsOwnerOrAdmin]
    queryset = CampaignDesign.objects.select_related(
        'campaign',
        'template'
    ).all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CampaignDesignCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CampaignDesignUpdateSerializer
        return CampaignDesignSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        return qs.filter(campaign__client=self.request.user)

class CampaignAreaViewSet(ModelViewSet):
    permission_classes = [IsClientUser, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CampaignArea.objects.none()
        queryset = CampaignArea.objects.select_related(
            "campaign",
            "city",
            "neighborhood",
            "suggested_route",
        ).filter(
            campaign__client=user
        )

        campaign_id = self.request.query_params.get("campaign")
        area_type = self.request.query_params.get("area_type")
        city_id = self.request.query_params.get("city")
        neighborhood_id = self.request.query_params.get("neighborhood")

        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)

        if area_type:
            queryset = queryset.filter(area_type=area_type)

        if city_id:
            queryset = queryset.filter(city_id=city_id)

        if neighborhood_id:
            queryset = queryset.filter(neighborhood_id=neighborhood_id)

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CampaignAreaDetailSerializer
        return CampaignAreaCreateSerializer

    def perform_create(self, serializer):
        campaign = serializer.validated_data["campaign"]

        if campaign.client_id != self.request.user.id:
            raise PermissionDenied("You do not have permission to use this campaign.")

        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()

        if instance.campaign.client_id != self.request.user.id:
            raise PermissionDenied("You do not have permission to edit this area.")

        campaign = serializer.validated_data.get("campaign", instance.campaign)
        if campaign.client_id != self.request.user.id:
            raise PermissionDenied("You do not have permission to move this area to this campaign.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.campaign.client_id != self.request.user.id:
            raise PermissionDenied("You do not have permission to delete this area.")
        instance.delete()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        campaign = serializer.validated_data["campaign"]

        if campaign.client_id != request.user.id:
            raise PermissionDenied("You do not have permission to use this campaign.")

        existing = CampaignArea.objects.filter(campaign=campaign).first()

        if existing:
            update_serializer = self.get_serializer(existing, data=request.data)
            update_serializer.is_valid(raise_exception=True)
            self.perform_update(update_serializer)

            output = CampaignAreaDetailSerializer(
                existing,
                context=self.get_serializer_context()
            )
            return Response(output.data, status=status.HTTP_200_OK)

        self.perform_create(serializer)
        output = CampaignAreaDetailSerializer(
            serializer.instance,
            context=self.get_serializer_context()
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

class CampaignPricingRuleViewSet(ModelViewSet):
    queryset = CampaignPricingRule.objects.all().order_by("key")
    serializer_class = CampaignPricingRuleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["key", "title"]
    ordering_fields = ["key", "created_at", "updated_at"]
    ordering = ["key"]

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsClientUser])
def campaign_cost(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id, brand_name__client__user=request.user)
    # بررسی وجود مراحل ضروری
    if not hasattr(campaign, 'setting') or not hasattr(campaign, 'design') or not hasattr(campaign, 'area'):
        return Response({'error': 'لطفاً همه مراحل (تنظیمات، طراحی، مسیر) را تکمیل کنید.'}, status=400)
    cost = calculate_campaign_cost(campaign)
    return Response(cost)

#-------------PAYMENT------------#

class CampaignInvoiceViewSet(ModelViewSet):
    queryset = CampaignInvoice.objects.all()
    permission_classes = [IsOwnerOrAdmin, IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return CampaignInvoiceCreateSerializer
        return CampaignInvoiceReadSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CampaignInvoice.objects.none()
        if user.is_staff:
            return CampaignInvoice.objects.all()
        # کلاینت: فقط فاکتورهای برندهای خودش
        return CampaignInvoice.objects.filter(campaign__brand_name__client=user)

    @action(detail=True, methods=['patch'])
    def pay(self, request, pk=None):
        """ علامت‌گذاری فاکتور به‌عنوان پرداخت‌شده (فقط ادمین یا پرداخت درگاه) """
        invoice = self.get_object()
        if invoice.status != CampaignInvoice.Status.ISSUED:
            return Response({"error": "فاکتور قابل پرداخت نیست."}, status=status.HTTP_400_BAD_REQUEST)
        invoice.status = CampaignInvoice.Status.PAID
        invoice.paid_at = timezone.now()
        invoice.save()
        return Response(self.get_serializer(invoice).data)

class PaymentRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def post(self, request):
        campaign_id = request.data.get('campaign_id')
        campaign = get_object_or_404(Campaign, id=campaign_id, brand_name__client__user=request.user)

        # ۱. محاسبهٔ هزینه
        cost = calculate_campaign_cost(campaign)
        total = cost['total']

        # یافتن فاکتور ISSUED موجود
        existing_invoice = CampaignInvoice.objects.filter(
            campaign=campaign,
            status=CampaignInvoice.Status.ISSUED
        ).first()

        if existing_invoice:
            if existing_invoice.is_expired:
                # منقضی شده → آن را EXPIRED کن و خطا بده
                existing_invoice.status = CampaignInvoice.Status.EXPIRED
                existing_invoice.save()
                return Response(
                    {"error": "فاکتور منقضی شده است. لطفاً دوباره درخواست دهید."},
                    status=400
                )
            else:
                # فاکتور معتبر پرداخت‌نشده وجود دارد
                return Response(
                    {"error": "یک فاکتور فعال برای این کمپین وجود دارد. لطفاً پرداخت را تکمیل کنید."},
                    status=400
                )

        # ایجاد فاکتور جدید
        snapshot = json.loads(json.dumps(cost, cls=DjangoJSONEncoder))
        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            invoice_number=generate_invoice_number(),
            subtotal_price=cost['subtotal'],
            discount_amount=cost.get('discount', 0),
            tax_amount=cost['tax'],
            total_price=total,
            expires_at=timezone.now() + timedelta(minutes=15),
            snapshot=snapshot,
            status=CampaignInvoice.Status.ISSUED,
        )

        # ۳. اتصال به زرین‌پال
        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=total,
            description=f'کمپین {campaign.slogan}',
            mobile=request.user.phone
        )

        if success:
            PaymentTransaction.objects.create(
                invoice=invoice,
                authority=payment_url_or_error.split('/')[-1],
                amount=total,
                status=PaymentTransaction.Status.INITIATED
            )
            return Response({
                'payment_url': payment_url_or_error,
                'invoice_id': invoice.id
            }, status=200)
        else:
            invoice.status = CampaignInvoice.Status.VOID  # یا حذف
            invoice.save()
            return Response({"error": error or "خطا در اتصال به درگاه"}, status=400)

class PaymentVerifyView(APIView):
    permission_classes = []  # زرین‌پال احراز هویت ندارد

    def get(self, request):
        authority = request.query_params.get('Authority')
        status_param = request.query_params.get('Status')

        if not authority or not status_param:
            return Response({"error": "پارامترها نامعتبر"}, status=400)

        try:
            transaction = PaymentTransaction.objects.get(authority=authority)
        except PaymentTransaction.DoesNotExist:
            return Response({"error": "تراکنش یافت نشد"}, status=404)

        invoice = transaction.invoice

        if status_param == 'OK':
            gateway = ZarinpalGateway()
            success, ref_id = gateway.verify_payment(authority, invoice.total_price)

            if success:
                transaction.status = PaymentTransaction.Status.SUCCESSFUL
                transaction.ref_id = ref_id
                transaction.save()

                # به‌روزرسانی فاکتور
                invoice.status = CampaignInvoice.Status.PAID
                invoice.paid_at = timezone.now()
                invoice.save()

                # 🔥 فعال‌سازی کمپین
                campaign = transaction.invoice.campaign
                campaign.status = Campaign.Status.ACTIVE
                campaign.save()

                # اعمال تغییرات بر اساس نوع modification
                self._apply_modifications(invoice)

                return Response({
                    'message': 'پرداخت موفق بود',
                    'ref_id': ref_id,
                    'status': 'success'
                }, status=200)
            else:
                transaction.status = PaymentTransaction.Status.FAILED
                transaction.response_data = {'error': ref_id}
                transaction.save()
                return Response({'error': 'تأیید پرداخت ناموفق'}, status=400)
        else:
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.save()
            return Response({
                'error': 'پرداخت توسط کاربر لغو شد',
                'status': 'cancelled'
            }, status=400)

    def _apply_modifications(self, invoice):
        """اعمال تغییرات پس از پرداخت موفق"""
        if not invoice.modification_type:
            return

        campaign = invoice.campaign
        mod_data = invoice.modification_data

        if invoice.modification_type == 'EXTEND':
            from datetime import datetime
            new_end_date = datetime.fromisoformat(mod_data['new_end_date']).date()
            campaign.end_date = new_end_date
            campaign.save()
            campaign.setting.active_days += mod_data['additional_days']
            campaign.setting.save()

        elif invoice.modification_type == 'ADD_VEHICLES':
            campaign.setting.max_driver = mod_data['new_max_driver']
            campaign.setting.save()

        elif invoice.modification_type == 'CHANGE_DESIGN':
            # اعمال تغییرات طراحی
            new_design_data = mod_data['new_design']

            # تبدیل شناسه‌های foreign key به اشیاء
            if 'template' in new_design_data and new_design_data['template']:
                new_design_data['template'] = Template.objects.get(id=new_design_data['template'])
            if 'banner_type' in new_design_data and new_design_data['banner_type']:
                new_design_data['banner_type'] = BannerType.objects.get(id=new_design_data['banner_type'])

            if hasattr(campaign, 'design'):
                # ویرایش طراحی موجود
                design = campaign.design
                for key, value in new_design_data.items():
                    setattr(design, key, value)
                design.save()
            else:
                # ایجاد طراحی جدید
                CampaignDesign.objects.create(
                    campaign=campaign,
                    **new_design_data
                )

#------------ANALYSIS-----------#

class CampaignAnalysisListView(generics.ListAPIView):
    """
    لیست تحلیل سفرهای یک کمپین خاص.
    فقط کلاینت صاحب کمپین یا ادمین می‌تواند ببیند.
    """
    serializer_class = TripAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        campaign_id = self.kwargs.get('campaign_id')
        user = self.request.user

        # ادمین همه را ببیند
        if user.is_staff:
            return TripAnalysis.objects.filter(trip__campaign_id=campaign_id)

        # کلاینت فقط تحلیل‌های کمپین‌های خودش
        return TripAnalysis.objects.filter(
            trip__campaign_id=campaign_id,
            trip__campaign__brand__client__user=user
        )

class CampaignAnalysisCSVView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request, campaign_id):
        user = request.user
        # ابتدا کمپین را واکشی می‌کنیم تا از وجود آن و مالکیت مطمئن شویم
        campaign = get_object_or_404(Campaign, id=campaign_id)

        # بررسی دسترسی: ادمین یا کلاینت صاحب کمپین
        if not user.is_staff and campaign.client.user != user:
            return Response({"error": "شما به این کمپین دسترسی ندارید."}, status=403)

        # تحلیل‌های سفرهای کامل‌شدهٔ این کمپین
        analyses = TripAnalysis.objects.filter(
            trip__campaign=campaign,
            trip__status=Trip.Status.COMPLETED
        ).select_related('trip__driver__user', 'trip__vehicle', 'trip__campaign')

        # ساخت خروجی CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="campaign_{campaign_id}_analysis.csv"'
        response.write('\ufeff'.encode('utf8'))  # BOM برای نمایش فارسی درست
        writer = csv.writer(response)

        # هدر
        writer.writerow([
            'شناسه سفر', 'نام راننده', 'پلاک خودرو', 'عنوان کمپین',
            'زمان شروع', 'زمان پایان',
            'مدت فعال (ثانیه)', 'مسافت (کیلومتر)', 'امتیاز نمایش',
            'تخمین تعداد مشاهده', 'درآمد (تومان)'
        ])

        for analysis in analyses:
            trip = analysis.trip
            writer.writerow([
                trip.id,
                trip.driver.full_name if trip.driver else '',
                trip.vehicle.plate_number if trip.vehicle else '',
                campaign.slogan,
                trip.start_time.strftime('%Y-%m-%d %H:%M:%S') if trip.start_time else '',
                trip.end_time.strftime('%Y-%m-%d %H:%M:%S') if trip.end_time else '',
                analysis.active_seconds,
                analysis.distance_km,
                analysis.exposure_score,
                analysis.estimated_impressions,
                trip.earnings
            ])

        return response

class CampaignPackageListView(ListAPIView):
    queryset = CampaignPackage.objects.filter(is_active=True)
    serializer_class = CampaignPackageSerializer
    permission_classes = [IsAuthenticated, IsClientUser]

#---------------CAMPAIGN SETTING---------------#

class CampaignPauseView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id, brand_name__client__user=request.user)
        if campaign.status not in [Campaign.Status.ACTIVE, Campaign.Status.PAUSED]:
            return Response({"error": "وضعیت کمپین اجازهٔ توقف نمی‌دهد"}, status=400)
        if campaign.status == Campaign.Status.ACTIVE:
            campaign.status = Campaign.Status.PAUSED
        else:
            campaign.status = Campaign.Status.ACTIVE
        campaign.save()
        return Response({"status": campaign.status})

class CampaignBannerImagesView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id, brand_name__client__user=request.user)
        trips = Trip.objects.filter(campaign=campaign, sticker_image__isnull=False)
        data = []
        for trip in trips:
            data.append({
                'driver_name': trip.driver.full_name,
                'sticker_image': request.build_absolute_uri(trip.sticker_image.url) if trip.sticker_image else None,
                'driver_car_image': request.build_absolute_uri(trip.driver_car_image.url) if trip.driver_car_image else None,
            })
        return Response(data)

class CampaignExtendView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # فقط کمپین‌های فعال، متوقف‌شده یا پیش‌نویس قابل تمدید هستند
        if campaign.status not in [Campaign.Status.ACTIVE, Campaign.Status.PAUSED, Campaign.Status.DRAFT]:
            return Response(
                {"error": "در وضعیت فعلی امکان تمدید کمپین وجود ندارد"},
                status=status.HTTP_400_BAD_REQUEST
            )

        additional_days = request.data.get('days')
        if not additional_days:
            return Response({"error": "تعداد روز تمدید الزامی است"}, status=400)
        try:
            additional_days = int(additional_days)
            if additional_days <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "تعداد روز باید یک عدد صحیح مثبت باشد"}, status=400)

        # محاسبهٔ هزینهٔ تمدید (فقط هزینهٔ خودرو و راننده برای روزهای اضافه)
        # فرض می‌کنیم هزینهٔ پایه از روی تنظیمات کمپین محاسبه می‌شود
        base_cost = calculate_campaign_cost(campaign)
        # هزینهٔ یک روز = (هزینهٔ خودرو + هزینهٔ راننده) / تعداد روزهای فعلی
        daily_vehicle_driver_cost = (
            base_cost['vehicle'] + base_cost['driver']
        ) / campaign.setting.active_days
        extra_amount = Decimal(daily_vehicle_driver_cost * additional_days)

        # ایجاد فاکتور با نوع EXTEND
        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            invoice_number=generate_invoice_number(),
            subtotal_price=extra_amount,
            discount_amount=Decimal('0'),
            tax_amount=extra_amount * Decimal('0.09'),
            total_price=extra_amount * Decimal('1.09'),
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.ISSUED,
            modification_type='EXTEND',
            modification_data={
                'additional_days': additional_days,
                'new_end_date': (
                    campaign.end_date + timedelta(days=additional_days)
                ).isoformat() if campaign.end_date else None,
                'extra_amount': float(extra_amount),
            },
            snapshot={
                'extra_cost': float(extra_amount),
                'total': float(extra_amount * Decimal('1.09')),
            }
        )

        # اتصال به زرین‌پال
        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'تمدید کمپین {campaign.slogan}',
            mobile=request.user.phone
        )

        if success:
            PaymentTransaction.objects.create(
                invoice=invoice,
                authority=payment_url_or_error.split('/')[-1],
                amount=invoice.total_price,
                status=PaymentTransaction.Status.INITIATED
            )
            return Response({
                'payment_url': payment_url_or_error,
                'invoice_id': invoice.id,
                'extra_amount': float(extra_amount),
                'total': float(invoice.total_price),
            }, status=status.HTTP_200_OK)
        else:
            invoice.status = CampaignInvoice.Status.VOID
            invoice.save()
            return Response(
                {"error": error or "خطا در اتصال به درگاه پرداخت"},
                status=status.HTTP_400_BAD_REQUEST
            )

class CampaignAddVehiclesView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # فقط کمپین‌های فعال، متوقف‌شده یا پیش‌نویس
        if campaign.status not in [Campaign.Status.ACTIVE, Campaign.Status.PAUSED, Campaign.Status.DRAFT]:
            return Response(
                {"error": "در وضعیت فعلی امکان افزایش خودرو وجود ندارد"},
                status=status.HTTP_400_BAD_REQUEST
            )

        additional_vehicles = request.data.get('count')
        if not additional_vehicles:
            return Response({"error": "تعداد خودروی اضافی الزامی است"}, status=400)
        try:
            additional_vehicles = int(additional_vehicles)
            if additional_vehicles <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "تعداد باید یک عدد صحیح مثبت باشد"}, status=400)

        # محاسبهٔ هزینهٔ افزایش خودرو (فقط هزینهٔ راننده برای خودروهای جدید)
        base_cost = calculate_campaign_cost(campaign)
        per_vehicle_cost = get_rule_value('DRIVER_COST_PER_DAY', Decimal('200000')) * campaign.setting.active_days
        extra_amount = Decimal(per_vehicle_cost * additional_vehicles)

        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            invoice_number=generate_invoice_number(),
            subtotal_price=extra_amount,
            discount_amount=Decimal('0'),
            tax_amount=extra_amount * Decimal('0.09'),
            total_price=extra_amount * Decimal('1.09'),
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.ISSUED,
            modification_type='ADD_VEHICLES',
            modification_data={
                'additional_vehicles': additional_vehicles,
                'new_max_driver': campaign.setting.max_driver + additional_vehicles,
                'extra_amount': float(extra_amount),
            },
            snapshot={
                'extra_cost': float(extra_amount),
                'total': float(extra_amount * Decimal('1.09')),
            }
        )
        print(invoice.snapshot, '///////////////////////////////')

        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'افزایش خودرو کمپین {campaign.slogan}',
            mobile=request.user.phone
        )

        if success:
            PaymentTransaction.objects.create(
                invoice=invoice,
                authority=payment_url_or_error.split('/')[-1],
                amount=invoice.total_price,
                status=PaymentTransaction.Status.INITIATED
            )
            return Response({
                'payment_url': payment_url_or_error,
                'invoice_id': invoice.id,
                'extra_amount': float(extra_amount),
                'total': float(invoice.total_price),
            }, status=status.HTTP_200_OK)
        else:
            invoice.status = CampaignInvoice.Status.VOID
            invoice.save()
            return Response(
                {"error": error or "خطا در اتصال به درگاه پرداخت"},
                status=status.HTTP_400_BAD_REQUEST
            )

class CampaignChangeDesignView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # کمپین باید در وضعیتی باشد که امکان تغییر طراحی وجود داشته باشد
        if campaign.status not in [Campaign.Status.DRAFT, Campaign.Status.ACTIVE, Campaign.Status.PAUSED]:
            return Response(
                {"error": "در وضعیت فعلی امکان تغییر بنر وجود ندارد"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # اعتبارسنجی داده‌های طراحی جدید
        design_serializer = CampaignDesignSerializer(data=request.data)
        if not design_serializer.is_valid():
            return Response(design_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_design_data = design_serializer.validated_data

        # محاسبهٔ هزینهٔ طراحی جدید
        new_design_cost = self._calculate_design_cost(new_design_data)

        # محاسبهٔ هزینهٔ طراحی قدیم (اگر طراحی قبلی وجود داشته باشد)
        old_design_cost = Decimal('0')
        if hasattr(campaign, 'design'):
            old_design = campaign.design
            old_design_data = {
                'design_type': old_design.design_type,
                'template': old_design.template_id,
                'banner_type': old_design.banner_type_id,
            }
            old_design_cost = self._calculate_design_cost(old_design_data)

        # مابه‌التفاوت
        extra_amount = Decimal(new_design_cost - old_design_cost)

        if extra_amount <= 0:
            # بدون نیاز به پرداخت اضافی، مستقیماً تغییرات را اعمال کن
            self._apply_design_changes(campaign, new_design_data)
            return Response(
                {"message": "تغییرات طراحی با موفقیت اعمال شد", "paid": False},
                status=status.HTTP_200_OK
            )

        # ایجاد فاکتور برای مابه‌التفاوت
        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            invoice_number=generate_invoice_number(),
            subtotal_price=extra_amount,
            discount_amount=Decimal('0'),
            tax_amount=extra_amount * Decimal('0.09'),
            total_price=extra_amount * Decimal('1.09'),
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.ISSUED,
            modification_type='CHANGE_DESIGN',
            modification_data={
                'new_design': new_design_data,
                'new_design_cost': float(new_design_cost),
                'old_design_cost': float(old_design_cost),
                'extra_amount': float(extra_amount),
            },
            snapshot={
                'extra_cost': float(extra_amount),
                'total': float(extra_amount * Decimal('1.09')),
            }
        )

        # اتصال به زرین‌پال
        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'تغییر بنر کمپین {campaign.slogan}',
            mobile=request.user.phone
        )

        if success:
            PaymentTransaction.objects.create(
                invoice=invoice,
                authority=payment_url_or_error.split('/')[-1],
                amount=invoice.total_price,
                status=PaymentTransaction.Status.INITIATED
            )
            return Response({
                'payment_url': payment_url_or_error,
                'invoice_id': invoice.id,
                'extra_amount': float(extra_amount),
                'total': float(invoice.total_price),
            }, status=status.HTTP_200_OK)
        else:
            # اگر اتصال به زرین‌پال ناموفق بود، فاکتور را حذف یا void کن
            invoice.status = CampaignInvoice.Status.VOID
            invoice.save()
            return Response(
                {"error": error or "خطا در اتصال به درگاه پرداخت"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _calculate_design_cost(self, design_data):
        """محاسبهٔ هزینهٔ طراحی بر اساس نوع طراحی"""
        from .pricing import get_rule_value

        design_type = design_data.get('design_type')

        if design_type == 'DEFAULT_TEMPLATE':
            return get_rule_value('DESIGN_BASE_COST', Decimal('50000'))
        elif design_type == 'CUSTOM_DESIGN':
            return get_rule_value('DESIGN_CUSTOM_COST', Decimal('200000'))
        elif design_type == 'USER_UPLOAD':
            return get_rule_value('DESIGN_UPLOAD_COST', Decimal('0'))

        return Decimal('0')

    def _apply_design_changes(self, campaign, new_design_data):
        """اعمال تغییرات طراحی روی کمپین"""
        if hasattr(campaign, 'design'):
            # ویرایش طراحی موجود
            design = campaign.design
            for key, value in new_design_data.items():
                setattr(design, key, value)
            design.save()
        else:
            # ایجاد طراحی جدید
            CampaignDesign.objects.create(
                campaign=campaign,
                **new_design_data
            )