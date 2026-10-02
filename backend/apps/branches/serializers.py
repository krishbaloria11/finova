from rest_framework import serializers
from .models import Branch

class BranchSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    account_count = serializers.SerializerMethodField()
    customer_count = serializers.SerializerMethodField()
    daily_transaction_volume = serializers.SerializerMethodField()
    name = serializers.CharField(source='branch_name', read_only=True)
    ifsc_code = serializers.CharField(source='ifsc', read_only=True)
    branch_id = serializers.CharField(source='branch_code', read_only=True)
    manager = serializers.CharField(source='manager_name', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'branch_code', 'branch_id', 'branch_name', 'name',
            'ifsc', 'ifsc_code', 'address', 'city', 'state', 'pincode',
            'phone', 'manager_name', 'manager', 'is_active', 'status',
            'created_at', 'employee_count', 'account_count', 'customer_count',
            'daily_transaction_volume'
        ]

    def get_employee_count(self, obj):
        return obj.employees.count() if hasattr(obj, 'employees') else 0

    def get_account_count(self, obj):
        return obj.accounts.count() if hasattr(obj, 'accounts') else 0

    def get_customer_count(self, obj):
        return obj.accounts.values('customer').distinct().count() if hasattr(obj, 'accounts') else 0

    def get_daily_transaction_volume(self, obj):
        from apps.transactions.models import Transaction
        from django.db.models import Sum
        vol = Transaction.objects.filter(
            from_account__branch=obj,
            status=Transaction.Status.COMPLETED
        ).aggregate(s=Sum('amount'))['s']
        return float(vol) if vol else 0.0

    def get_status(self, obj):
        return 'ACTIVE' if obj.is_active else 'INACTIVE'

