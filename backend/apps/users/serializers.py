from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Customer, Employee

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']
        read_only_fields = ['id', 'role']


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    name = serializers.CharField(source='full_name', read_only=True)
    accounts = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'customer_id', 'full_name', 'name', 'pan_number', 'aadhaar_last_four',
            'phone', 'address', 'city', 'state', 'pincode', 'monthly_income',
            'credit_score', 'credit_category', 'credit_score_updated_at',
            'kyc_status', 'kyc_document_type', 'kyc_document_number',
            'kyc_verified_at', 'kyc_remarks', 'created_at', 'user', 'accounts'
        ]
        read_only_fields = ['id', 'customer_id', 'credit_score', 'credit_category', 'kyc_status']

    def get_accounts(self, obj):
        from apps.accounts.serializers import AccountSerializer
        return AccountSerializer(obj.accounts.all(), many=True).data



class EmployeeProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    branch_ifsc = serializers.CharField(source='branch.ifsc', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'designation', 'department',
            'branch', 'branch_name', 'branch_ifsc', 'is_active', 'user'
        ]


class KYCRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_pan = serializers.CharField(source='customer.pan_number', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_cif = serializers.CharField(source='customer.customer_id', read_only=True)
    customer_monthly_income = serializers.DecimalField(source='customer.monthly_income', max_digits=12, decimal_places=2, read_only=True)
    assigned_employee_name = serializers.CharField(source='assigned_employee.full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)
    loan_application_id = serializers.CharField(source='loan_application.application_id', read_only=True)
    loan_type_name = serializers.CharField(source='loan_application.loan_type.name', read_only=True)
    requested_amount = serializers.DecimalField(source='loan_application.requested_amount', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        from .models import KYCRequest
        model = KYCRequest
        fields = [
            'id', 'request_id', 'customer', 'customer_name', 'customer_pan', 'customer_phone',
            'customer_cif', 'customer_monthly_income', 'loan_application', 'loan_application_id',
            'loan_type_name', 'requested_amount', 'assigned_employee', 'assigned_employee_name',
            'status', 'document_type', 'document_number', 'submitted_at', 'reviewed_at',
            'reviewed_by', 'reviewed_by_name', 'review_notes', 'rejection_reason'
        ]
        read_only_fields = ['id', 'request_id', 'submitted_at', 'reviewed_at', 'reviewed_by']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=15)
    pan_number = serializers.CharField(max_length=10)
    aadhaar_number = serializers.CharField(max_length=16, required=False, default="1234")
    address = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=80)
    state = serializers.CharField(max_length=80)
    pincode = serializers.CharField(max_length=10)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2, default=50000.00)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError("Invalid credentials. Please verify username and password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive or disabled.")
        attrs['user'] = user
        return attrs
