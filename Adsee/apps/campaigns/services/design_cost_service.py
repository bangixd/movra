from decimal import Decimal
from campaigns.services.pricing import get_rule_value


class DesignCostService:
    """سرویس محاسبهٔ هزینهٔ طراحی"""

    @staticmethod
    def calculate(design_data: dict) -> Decimal:
        """
        محاسبهٔ هزینهٔ طراحی بر اساس نوع طراحی
        """
        design_type = design_data.get('design_type')

        cost_map = {
            'DEFAULT_TEMPLATE': get_rule_value('DESIGN_BASE_COST', Decimal('50000')),
            'CUSTOM_DESIGN': get_rule_value('DESIGN_CUSTOM_COST', Decimal('200000')),
            'USER_UPLOAD': get_rule_value('DESIGN_UPLOAD_COST', Decimal('0')),
        }

        return cost_map.get(design_type, Decimal('0'))