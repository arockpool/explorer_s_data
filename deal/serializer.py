from rest_framework import serializers
from explorer_s_common.utils import DynamicFieldsModelSerializer, height_to_datetime, format_fil
from deal.models import Deal


class DealSerializer(DynamicFieldsModelSerializer):
    record_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        if result_dict.get('start_epoch'):
            result_dict['start_height'] = result_dict['start_epoch']
            result_dict['start_epoch'] = height_to_datetime(result_dict['start_epoch'], True)
        if result_dict.get('end_epoch'):
            result_dict['end_height'] = result_dict['end_epoch']
            result_dict['end_epoch'] = height_to_datetime(result_dict['end_epoch'], True)
        if result_dict.get('client_collateral') and result_dict.get('client_collateral') != '0':
            result_dict['client_collateral'] = format_fil(result_dict['client_collateral'])
        if result_dict.get('provider_collateral') and result_dict.get('provider_collateral') != '0':
            result_dict['provider_collateral'] = format_fil(result_dict['provider_collateral'])
        return result_dict

    class Meta:
        model = Deal
        exclude = ("id", "sector_start_epoch", "last_updated_epoch", "slash_epoch", "create_time", "update_time")


class DealModeSerializer(DynamicFieldsModelSerializer):
    pass

    class Meta:
        model = Deal
        fields = '__all__'