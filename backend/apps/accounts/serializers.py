from rest_framework import serializers
from .models import AccountType, Account

class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    account_type_code = serializers.CharField(source='account_type.code', read_only=True)
    interest_rate = serializers.DecimalField(source='account_type.interest_rate_pa', max_digits=5, decimal_places=2, read_only=True)
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    ifsc = serializers.CharField(read_only=True)
    masked_account_number = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)

    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'masked_account_number', 'customer', 'customer_name',
            'branch', 'branch_name', 'ifsc', 'account_type', 'account_type_name',
            'account_type_code', 'interest_rate', 'available_balance', 'ledger_balance',
            'currency', 'card_variant', 'status', 'is_primary', 'opened_date'
        ]
        read_only_fields = [
            'id', 'account_number', 'available_balance', 'ledger_balance', 'opened_date'
        ]
