from rest_framework import serializers
from campaigns.models import CampaignPricingRule

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
