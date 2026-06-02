from decimal import Decimal
from .models import CampaignPricingRule, Campaign, CampaignDesign

def get_rule_value(key, default=Decimal('0')):
    rule = CampaignPricingRule.objects.filter(key=key, is_active=True).first()
    return rule.value if rule else default

def calculate_campaign_cost(campaign):
    setting = campaign.setting
    try:
        design = campaign.design
    except CampaignDesign.DoesNotExist:
        design = None
    try:
        area = campaign.area
    except Campaign.area.RelatedObjectDoesNotExist:
        area = None
    vehicle_type = setting.vehicle_type

    # هزینه طراحی
    if design is None:
        design_cost = 0
    else:
        if design.design_type == 'DEFAULT_TEMPLATE':
            design_cost = get_rule_value('DESIGN_BASE_COST', Decimal('100000'))
        elif design.design_type == 'CUSTOM_DESIGN':
            design_cost = get_rule_value('DESIGN_CUSTOM_COST', Decimal('500000'))
        else:  # USER_UPLOAD
            design_cost = get_rule_value('DESIGN_UPLOAD_COST', Decimal('130000'))

    # هزینه مسیر
    if area is None:
        area_cost = 0
    else:
        if area.area_type == 'CIRCLE':
            area_cost = get_rule_value('AREA_CIRCLE_COST_PER_KM', Decimal('100000')) * Decimal(area.radius_meter / 1000)
        elif area.area_type == 'SUGGESTED_ROUTE':
            area_cost = get_rule_value('AREA_SUGGESTED_ROUTE_COST_PER_KM', Decimal('150000')) * Decimal(10)  # مثال
        else:  # FREE_AREA
            area_cost = get_rule_value('AREA_FREE_COST_MULTIPLIER', Decimal('2')) * Decimal('500000')  # پایه شهر

    # هزینه خودرو
    vehicle_hourly_rate = vehicle_type.base_hourly_rate
    total_hours = setting.active_days * setting.activity_hours_per_day.hour
    vehicle_cost = vehicle_hourly_rate * total_hours * setting.max_driver

    # هزینه راننده (می‌تواند جداگانه باشد، ولی فعلاً داخل vehicle_cost گنجانده شده)
    driver_cost = get_rule_value('DRIVER_COST_PER_DAY', Decimal('0')) * setting.active_days * setting.max_driver

    subtotal = design_cost + area_cost + vehicle_cost + driver_cost
    discount = Decimal('0')  # بعداً می‌توان تخفیف اعمال کرد
    tax = subtotal * Decimal('0.09')  # ۹٪ مالیات (مثال)
    total = subtotal + tax

    return {
        'design': float(design_cost),
        'area': float(area_cost),
        'vehicle': float(vehicle_cost),
        'driver': float(driver_cost),
        'subtotal': float(subtotal),
        'tax': float(tax),
        'total': float(total)
    }