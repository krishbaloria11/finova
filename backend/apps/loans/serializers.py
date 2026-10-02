from decimal import Decimal
from rest_framework import serializers
from .models import LoanType, LoanApplication, Loan, LoanPayment

class LoanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = '__all__'


class LoanApplicationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    loan_type_name = serializers.CharField(source='loan_type.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True, default='')

    class Meta:
        model = LoanApplication
        fields = [
            'id', 'application_id', 'customer', 'customer_name',
            'loan_type', 'loan_type_name', 'requested_amount',
            'tenure_months', 'proposed_interest_rate', 'calculated_emi',
            'purpose', 'employment_type', 'employer_name', 'monthly_income',
            'existing_obligations', 'pan_number', 'aadhaar_number',
            'residential_address', 'kyc_document_type', 'kyc_document_number',
            'status', 'reviewed_by_name', 'review_notes',
            'submitted_at', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'application_id', 'calculated_emi', 'status',
            'reviewed_by_name', 'review_notes', 'submitted_at', 'reviewed_at'
        ]


class LoanSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    loan_type_name = serializers.CharField(source='loan_type.name', read_only=True)
    servicing_account_masked = serializers.CharField(source='servicing_account.masked_account_number', read_only=True)
    repayment_progress = serializers.FloatField(source='repayment_progress_percentage', read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'loan_id', 'customer', 'customer_name', 'loan_type', 'loan_type_name',
            'servicing_account', 'servicing_account_masked', 'principal_amount',
            'interest_rate', 'tenure_months', 'monthly_emi', 'total_payable',
            'total_interest', 'outstanding_amount', 'repaid_amount',
            'repayment_progress', 'start_date', 'end_date', 'next_due_date',
            'auto_debit', 'status', 'created_at'
        ]
        read_only_fields = fields


class LoanPaymentSerializer(serializers.ModelSerializer):
    loan_id = serializers.CharField(source='loan.loan_id', read_only=True)

    class Meta:
        model = LoanPayment
        fields = [
            'id', 'payment_id', 'loan', 'loan_id', 'account',
            'amount_paid', 'principal_component', 'interest_component',
            'installment_number', 'payment_date', 'status', 'receipt_number', 'remarks'
        ]
        read_only_fields = fields


class EMICalculatorSerializer(serializers.Serializer):
    principal = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('10000.00'))
    annual_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('1.00'), max_value=Decimal('40.00'))
    tenure_months = serializers.IntegerField(min_value=6, max_value=360)


class PayEMISerializer(serializers.Serializer):
    loan_id = serializers.IntegerField()
    account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('100.00'))
