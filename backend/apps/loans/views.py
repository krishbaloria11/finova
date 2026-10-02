import uuid
from decimal import Decimal
from rest_framework import viewsets, views, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from .models import LoanType, LoanApplication, Loan, LoanPayment
from .serializers import (
    LoanTypeSerializer, LoanApplicationSerializer, LoanSerializer,
    LoanPaymentSerializer, EMICalculatorSerializer, PayEMISerializer
)
from .services import LoanService
from apps.users.models import User
from apps.notifications.models import Notification

class LoanTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer
    permission_classes = [permissions.AllowAny]


from apps.audit.models import AuditLog
from django.db.models import Q

class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Loan.objects.select_related('customer', 'loan_type', 'servicing_account').all()
        if user.role == User.Role.CUSTOMER:
            if hasattr(user, 'customer_profile'):
                return qs.filter(customer=user.customer_profile)
            return Loan.objects.none()

        loan_status = self.request.query_params.get('status')
        if loan_status:
            qs = qs.filter(status=loan_status.upper())

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(loan_id__icontains=search) |
                Q(customer__full_name__icontains=search) |
                Q(customer__pan_number__icontains=search) |
                Q(customer__customer_id__icontains=search)
            )

        return qs

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        loan = self.get_object()
        payments = loan.payments.all()
        return Response(LoanPaymentSerializer(payments, many=True).data)

    @action(detail=True, methods=['get'])
    def amortization(self, request, pk=None):
        loan = self.get_object()
        schedule = LoanService.generate_amortization_schedule(
            loan.principal_amount,
            loan.interest_rate,
            loan.tenure_months,
            limit=24
        )
        return Response(schedule)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Admin action: Update loan facility status (e.g. Suspend/Hold or Close)."""
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Admin permissions required.'}, status=status.HTTP_403_FORBIDDEN)

        loan = self.get_object()
        new_status = request.data.get('status', '').upper().strip()
        reason = request.data.get('reason', '').strip()

        valid_statuses = [Loan.Status.ACTIVE, Loan.Status.UNDER_REVIEW, Loan.Status.CLOSED, Loan.Status.DEFAULTED]
        if new_status not in valid_statuses:
            return Response({'error': f"Invalid status choice. Valid choices are: {', '.join(valid_statuses)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not reason:
            return Response({'error': 'A justification reason is required to update loan facility status.'}, status=status.HTTP_400_BAD_REQUEST)

        prev_status = loan.status
        loan.status = new_status
        loan.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user=request.user,
            action="LOAN_FACILITY_STATUS_UPDATED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Loan",
            record_id=loan.loan_id,
            details=f"Loan facility {loan.loan_id} status changed from {prev_status} to {new_status}. Reason: {reason}"
        )

        return Response({
            'message': f"Loan {loan.loan_id} status updated to {new_status}.",
            'loan': LoanSerializer(loan).data
        })


class LoanApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = LoanApplication.objects.select_related('customer', 'loan_type', 'reviewed_by').all()
        if user.role == User.Role.CUSTOMER:
            if hasattr(user, 'customer_profile'):
                return qs.filter(customer=user.customer_profile)
            return LoanApplication.objects.none()

        app_status = self.request.query_params.get('status')
        if app_status:
            qs = qs.filter(status=app_status.upper())

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(application_id__icontains=search) |
                Q(customer__full_name__icontains=search) |
                Q(customer__pan_number__icontains=search)
            )

        return qs


    def create(self, request, *args, **kwargs):
        if not hasattr(request.user, 'customer_profile'):
            return Response({'error': 'Only registered customers may apply for loans.'}, status=status.HTTP_403_FORBIDDEN)

        customer = request.user.customer_profile
        data = request.data.copy()

        # Resolve loan type
        try:
            loan_type = LoanType.objects.get(id=data.get('loan_type'))
        except (LoanType.DoesNotExist, ValueError):
            return Response({'error': 'Invalid loan type selected.'}, status=status.HTTP_400_BAD_REQUEST)

        amount = Decimal(str(data.get('requested_amount', 0)))
        tenure = int(data.get('tenure_months', 12))
        rate = loan_type.base_interest_rate

        # Calculate EMI automatically
        calc = LoanService.calculate_emi(amount, rate, tenure)

        app_id = f"LA-{uuid.uuid4().hex[:6].upper()}"

        application = LoanApplication.objects.create(
            application_id=app_id,
            customer=customer,
            loan_type=loan_type,
            requested_amount=amount,
            tenure_months=tenure,
            proposed_interest_rate=rate,
            calculated_emi=calc['monthly_emi'],
            purpose=data.get('purpose', f'Application for {loan_type.name}'),
            employment_type=data.get('employment_type', 'Salaried'),
            employer_name=data.get('employer_name', ''),
            monthly_income=Decimal(str(data.get('monthly_income', customer.monthly_income))),
            existing_obligations=Decimal(str(data.get('existing_obligations', 0))),
            pan_number=data.get('pan_number', customer.pan_number),
            aadhaar_number=data.get('aadhaar_number', customer.aadhaar_last_four),
            residential_address=data.get('residential_address', customer.address),
            kyc_document_type=data.get('kyc_document_type', 'PAN & Income Proof'),
            kyc_document_number=data.get('kyc_document_number', customer.pan_number),
            status=LoanApplication.Status.UNDER_REVIEW
        )

        # Section 10 & 11: Real KYC Assignment Workflow
        from apps.users.models import KYCRequest
        kyc_req = KYCRequest.objects.create(
            request_id=f"KYC-{app_id[3:]}",
            customer=customer,
            loan_application=application,
            status=KYCRequest.Status.PENDING,
            document_type=data.get('kyc_document_type', 'PAN & Income Proof'),
            document_number=data.get('kyc_document_number', customer.pan_number)
        )
        assigned_officer = KYCRequest.assign_to_employee(kyc_req)
        assigned_name = assigned_officer.full_name if assigned_officer else "Operations Officer"

        Notification.objects.create(
            user=request.user,
            title="Loan Application & KYC Assigned",
            message=f"Your {loan_type.name} application #{app_id} for ₹{amount:,.2f} is under review. KYC verification assigned to Officer {assigned_name}.",
            notification_type=Notification.NotificationType.LOAN_UPDATE
        )

        resp_data = LoanApplicationSerializer(application).data
        resp_data['kyc_request_id'] = kyc_req.request_id
        return Response(resp_data, status=status.HTTP_201_CREATED)


class LoanReviewView(views.APIView):
    """
    Employee and Admin underwriting view to Approve or Reject a Loan Application.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not user.is_superuser:
            return Response({'error': 'Unauthorized. Requires bank underwriting privileges.'}, status=status.HTTP_403_FORBIDDEN)

        decision = request.data.get('decision', '').upper()
        notes = request.data.get('notes', '')
        sanction_acc_id = request.data.get('sanction_account_id')

        reviewer = getattr(user, 'employee_profile', None)

        try:
            app = LoanService.review_application(
                application_id=pk,
                decision=decision,
                reviewer_employee=reviewer,
                review_notes=notes,
                sanction_account_id=sanction_acc_id
            )

            # Notify customer
            Notification.objects.create(
                user=app.customer.user,
                title=f"Loan Application {decision}",
                message=f"Your loan application #{app.application_id} has been {decision.lower()}d.",
                notification_type=Notification.NotificationType.LOAN_UPDATE
            )

            return Response(LoanApplicationSerializer(app).data)

        except ValidationError as e:
            return Response({'error': str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Review failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EMICalculatorView(views.APIView):
    """
    Standard Equated Monthly Installment (EMI) mathematical calculation engine.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EMICalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = LoanService.calculate_emi(
            principal=data['principal'],
            annual_rate=data['annual_rate'],
            tenure_months=data['tenure_months']
        )
        schedule = LoanService.generate_amortization_schedule(
            principal=data['principal'],
            annual_rate=data['annual_rate'],
            tenure_months=data['tenure_months'],
            limit=12
        )
        result['sample_schedule'] = schedule
        return Response(result)


class PayEMIView(views.APIView):
    """
    Atomic EMI payment transaction.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PayEMISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payment = LoanService.pay_emi(
                loan_id=data['loan_id'],
                account_id=data['account_id'],
                amount=data['amount'],
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )

            Notification.objects.create(
                user=request.user,
                title="EMI Payment Successful",
                message=f"₹{data['amount']:,.2f} received towards loan #{payment.loan.loan_id}. Receipt #{payment.receipt_number}",
                notification_type=Notification.NotificationType.PAYMENT_DUE
            )

            return Response({
                'message': 'EMI payment processed successfully.',
                'payment': LoanPaymentSerializer(payment).data
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'error': str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Payment failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
