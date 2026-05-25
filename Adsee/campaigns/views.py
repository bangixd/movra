from django.utils import timezone
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, filters, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from .models import CampaignDesign, Campaign, CampaignSetting, Template, CampaignArea, CampaignPricingRule,\
    CampaignCost, CampaignInvoice, PaymentTransaction
from services.payment_gateway import ZarinpalGateway
from .serializers import CampaignDesignSerializer, CampaignSerializer, CampaignSettingSerializer, TemplateSerializer,\
    CampaignDesignCreateSerializer, CampaignDesignUpdateSerializer,\
    CampaignAreaDetailSerializer, CampaignAreaCreateSerializer, CampaignPricingRuleSerializer,\
    CampaignCostCalculationSerializer, CampaignInvoiceReadSerializer, CampaignInvoiceCreateSerializer,\
    PaymentRequestSerializer, PaymentVerifySerializer, PaymentTransactionSerializer
from .services.campaign_pricing_service import CampaignPricingService
from permissions import IsClientUser, IsOwnerOrAdmin
from vehicles.models import VehicleType
from mixins import SafeGetQuerysetMixin


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


class TemplateViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrAdmin,]
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer


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
    permission_classes = [IsOwnerOrAdmin,]

    queryset = CampaignPricingRule.objects.all().order_by("key")
    serializer_class = CampaignPricingRuleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["key", "title"]
    ordering_fields = ["key", "created_at", "updated_at"]
    ordering = ["key"]


class CampaignCostViewSet(ViewSet):
    permission_classes = [IsClientUser, IsOwnerOrAdmin]

    @action(detail=True, methods=["post"], url_path="calculate-cost")
    def calculate_cost(self, request, pk=None):
        campaign = Campaign.objects.get(pk=pk)

        serializer = CampaignCostCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        vehicle = VehicleType.objects.get(pk=data["vehicle_type_id"])

        cost, created = CampaignCost.objects.get_or_create(campaign=campaign)

        cost.drivers_count = data["drivers_count"]
        cost.days_count = data["days_count"]
        cost.hours_per_day = data["hours_per_day"]
        cost.vehicle_type = vehicle
        cost.design_type = data["design_type"]
        cost.area_type = data["area_type"]
        cost.save()

        CampaignPricingService.refresh_cost(cost)

        return Response({
            "campaign_id": campaign.id,
            "cost_id": cost.id,
            "subtotal_price": str(cost.subtotal_price),
            "tax_amount": str(cost.tax_amount),
            "total_price": str(cost.total_price),
            "status": cost.status,
            "items": [
                {
                    "item_type": item.item_type,
                    "title": item.title,
                    "quantity": str(item.quantity),
                    "unit_price": str(item.unit_price),
                    "total_price": str(item.total_price),
                    "meta": item.meta,
                }
                for item in cost.items.all()
            ],
        }, status=status.HTTP_200_OK)


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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice = CampaignInvoice.objects.get(
                id=serializer.validated_data['invoice_id'],
                campaign__brand__client__user=request.user,
                status=CampaignInvoice.Status.ISSUED
            )
        except CampaignInvoice.DoesNotExist:
            return Response({"error": "فاکتور معتبر نیست"}, status=404)

        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'Invoice {invoice.invoice_number}',
            mobile=request.user.phone
        )

        if success:
            # ذخیره تراکنش
            PaymentTransaction.objects.create(
                invoice=invoice,
                authority=payment_url_or_error.split('/')[-1],  # استخراج authority از URL
                amount=invoice.total_price,
                status=PaymentTransaction.Status.PENDING
            )
            return Response({'payment_url': payment_url_or_error}, status=200)
        else:
            return Response({"error": error or "خطا در اتصال به درگاه"}, status=400)


class PaymentVerifyView(APIView):
    permission_classes = []  # از آنجایی که زرین‌پال callback را GET می‌زند، احراز هویت ندارد

    def get(self, request):
        # زرین‌پال پارامترهای Authority و Status را در query string برمی‌گرداند
        authority = request.query_params.get('Authority')
        status_param = request.query_params.get('Status')

        if not authority or not status_param:
            return Response({"error": "پارامترها نامعتبر"}, status=400)

        try:
            transaction = PaymentTransaction.objects.get(authority=authority)
        except PaymentTransaction.DoesNotExist:
            return Response({"error": "تراکنش یافت نشد"}, status=404)

        if status_param == 'OK':
            gateway = ZarinpalGateway()
            success, ref_id = gateway.verify_payment(authority, transaction.amount)
            if success:
                transaction.status = PaymentTransaction.Status.SUCCESSFUL
                transaction.ref_id = ref_id
                transaction.save()

                # به‌روزرسانی فاکتور
                transaction.invoice.status = CampaignInvoice.Status.PAID
                transaction.invoice.paid_at = timezone.now()
                transaction.invoice.save()

                return Response({'message': 'پرداخت موفق بود', 'ref_id': ref_id}, status=200)
            else:
                transaction.status = PaymentTransaction.Status.FAILED
                transaction.response_data = {'error': ref_id}
                transaction.save()
                return Response({'error': 'تأیید پرداخت ناموفق'}, status=400)
        else:
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.save()
            return Response({'error': 'پرداخت توسط کاربر لغو شد'}, status=400)