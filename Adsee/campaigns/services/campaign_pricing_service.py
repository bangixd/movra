from decimal import Decimal
from django.db import transaction
from ..models import CampaignPricingRule, CampaignCost, CampaignCostItem


class CampaignPricingService:
    DEFAULTS = {
        "tax_percent": Decimal("9"),
        "ready_template_design_price": Decimal("300000"),
        "custom_design_price": Decimal("2000000"),
        "uploaded_design_price": Decimal("500000"),
        "free_area_price": Decimal("300000"),
        "suggested_route_price": Decimal("800000"),
        "circle_area_price": Decimal("500000"),
    }

    @classmethod
    def get_rule_value(cls, key, default=None):
        rule = CampaignPricingRule.objects.filter(key=key, is_active=True).first()
        if not rule:
            return default
        return rule.value

    @classmethod
    def get_decimal_rule(cls, key, default=Decimal("0")):
        value = cls.get_rule_value(key, default)
        if value is None:
            return default
        return Decimal(str(value))

    @classmethod
    def calculate_execution(cls, cost: CampaignCost):
        if not cost.vehicle_type:
            return Decimal("0"), Decimal("0")

        unit_price = getattr(cost.vehicle_type, "hourly_price", Decimal("0"))
        quantity = Decimal(cost.drivers_count * cost.days_count * cost.hours_per_day)
        return Decimal(unit_price), quantity

    @classmethod
    def calculate_design(cls, cost: CampaignCost):
        if cost.design_type == "CUSTOM_DESIGN":
            return cls.get_decimal_rule("custom_design_price", cls.DEFAULTS["custom_design_price"])
        if cost.design_type == "UPLOADED_DESIGN":
            return cls.get_decimal_rule("uploaded_design_price", cls.DEFAULTS["uploaded_design_price"])
        if cost.design_type == "READY_TEMPLATE":
            return cls.get_decimal_rule("ready_template_design_price", cls.DEFAULTS["ready_template_design_price"])
        return Decimal("0")

    @classmethod
    def calculate_area(cls, cost: CampaignCost):
        if cost.area_type == "SUGGESTED_ROUTE":
            return cls.get_decimal_rule("suggested_route_price", cls.DEFAULTS["suggested_route_price"])
        if cost.area_type == "CIRCLE":
            return cls.get_decimal_rule("circle_area_price", cls.DEFAULTS["circle_area_price"])
        return cls.get_decimal_rule("free_area_price", cls.DEFAULTS["free_area_price"])

    @classmethod
    @transaction.atomic
    def refresh_cost(cls, cost: CampaignCost):
        cost.items.all().delete()

        subtotal = Decimal("0")

        # Execution
        execution_unit_price, execution_qty = cls.calculate_execution(cost)
        execution_total = execution_unit_price * execution_qty

        CampaignCostItem.objects.create(
            campaign_cost=cost,
            item_type=CampaignCostItem.ItemType.EXECUTION,
            title="Campaign Execution",
            quantity=execution_qty,
            unit_price=execution_unit_price,
            total_price=execution_total,
            meta={
                "drivers_count": cost.drivers_count,
                "days_count": cost.days_count,
                "hours_per_day": cost.hours_per_day,
                "vehicle_type_id": cost.vehicle_type_id,
            }
        )
        subtotal += execution_total

        # Design
        design_price = cls.calculate_design(cost)
        CampaignCostItem.objects.create(
            campaign_cost=cost,
            item_type=CampaignCostItem.ItemType.DESIGN,
            title="Design Cost",
            quantity=Decimal("1"),
            unit_price=design_price,
            total_price=design_price,
            meta={"design_type": cost.design_type}
        )
        subtotal += design_price

        # Area
        area_price = cls.calculate_area(cost)
        CampaignCostItem.objects.create(
            campaign_cost=cost,
            item_type=CampaignCostItem.ItemType.AREA,
            title="Area Cost",
            quantity=Decimal("1"),
            unit_price=area_price,
            total_price=area_price,
            meta={"area_type": cost.area_type}
        )
        subtotal += area_price

        tax_percent = cls.get_decimal_rule("tax_percent", cls.DEFAULTS["tax_percent"])
        tax_amount = subtotal * (tax_percent / Decimal("100"))
        total_price = subtotal + tax_amount

        cost.subtotal_price = subtotal
        cost.tax_amount = tax_amount
        cost.total_price = total_price
        cost.status = CampaignCost.Status.CONFIGURING
        cost.save(update_fields=["subtotal_price", "tax_amount", "total_price", "status", "updated_at"])

        return cost
