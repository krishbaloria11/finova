from decimal import Decimal
from rest_framework import serializers
from .models import Transaction, Beneficiary

class TransactionSerializer(serializers.ModelSerializer):
    from_account_masked = serializers.CharField(source='from_account.masked_account_number', read_only=True)
    to_account_masked = serializers.CharField(source='to_account.masked_account_number', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'from_account', 'from_account_masked',
            'to_account', 'to_account_masked', 'beneficiary_name',
            'beneficiary_account', 'beneficiary_ifsc', 'transaction_type',
            'category', 'amount', 'balance_after', 'status',
            'remarks', 'reference_number', 'timestamp'
        ]
        read_only_fields = fields


class TransferRequestSerializer(serializers.Serializer):
    from_account_id = serializers.IntegerField()
    beneficiary_name = serializers.CharField(max_length=120)
    to_account_number = serializers.CharField(max_length=24)
    confirm_account_number = serializers.CharField(max_length=24)
    to_ifsc = serializers.CharField(max_length=11)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('1.00'))
    category = serializers.ChoiceField(
        choices=Transaction.Category.choices,
        default=Transaction.Category.TRANSFER
    )
    remarks = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, data):
        if data['to_account_number'].strip() != data['confirm_account_number'].strip():
            raise serializers.ValidationError({"confirm_account_number": "Account numbers do not match."})
        if len(data['to_ifsc'].strip()) != 11:
            raise serializers.ValidationError({"to_ifsc": "IFSC code must be exactly 11 characters long (e.g. FINO0001234)."})
        return data


class BeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'account_number', 'ifsc_code', 'bank_name',
            'nickname', 'avatar_url', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']
