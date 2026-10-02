import uuid
from decimal import Decimal
from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db import models
from django.utils import timezone
from .models import User, Customer, Employee
from .serializers import (
    UserSerializer, CustomerProfileSerializer, EmployeeProfileSerializer,
    RegisterSerializer, LoginSerializer
)
from apps.branches.models import Branch
from apps.accounts.models import Account, AccountType
from apps.audit.models import AuditLog

class RegisterView(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['full_name'].split()[0],
            last_name=" ".join(data['full_name'].split()[1:]) if len(data['full_name'].split()) > 1 else "",
            role=User.Role.CUSTOMER,
            phone=data['phone']
        )

        customer = Customer.objects.create(
            user=user,
            customer_id=f"CUST-{uuid.uuid4().hex[:6].upper()}",
            full_name=data['full_name'],
            pan_number=data['pan_number'].upper(),
            aadhaar_last_four=data.get('aadhaar_number', '1234')[-4:],
            phone=data['phone'],
            address=data['address'],
            city=data['city'],
            state=data['state'],
            pincode=data['pincode'],
            monthly_income=data.get('monthly_income', Decimal('50000.00')),
            credit_score=750,
            credit_category="Good",
            kyc_status=Customer.KYCStatus.PENDING,
            kyc_document_type="PAN & Aadhaar",
            kyc_document_number=data['pan_number'].upper()
        )

        # Automatically establish primary savings account in default branch
        branch = Branch.objects.first()
        acc_type = AccountType.objects.filter(code='SAVINGS').first()
        if branch and acc_type:
            Account.objects.create(
                account_number=f"4821{uuid.uuid4().hex[:8].upper()[:8]}",
                customer=customer,
                branch=branch,
                account_type=acc_type,
                available_balance=Decimal('10000.00'),
                ledger_balance=Decimal('10000.00'),
                is_primary=True,
                card_variant="RuPay Platinum Contactless"
            )

        token, _ = Token.objects.get_or_create(user=user)

        AuditLog.objects.create(
            user=user,
            action="CUSTOMER_REGISTRATION",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Customer",
            record_id=customer.customer_id,
            details=f"New customer registered: {customer.full_name} ({user.username})"
        )

        return Response({
            'message': 'Registration successful.',
            'token': token.key,
            'user': UserSerializer(user).data,
            'customer': CustomerProfileSerializer(customer).data
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        AuditLog.objects.create(
            user=user,
            action="USER_LOGIN",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            details=f"User {user.username} logged in successfully as {user.role}"
        )

        resp_data = {
            'token': token.key,
            'user': UserSerializer(user).data
        }

        if hasattr(user, 'customer_profile'):
            resp_data['customer'] = CustomerProfileSerializer(user.customer_profile).data
        elif hasattr(user, 'employee_profile'):
            resp_data['employee'] = EmployeeProfileSerializer(user.employee_profile).data

        return Response(resp_data)


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass

        AuditLog.objects.create(
            user=request.user,
            action="USER_LOGOUT",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            details=f"User {request.user.username} logged out"
        )
        return Response({'message': 'Logged out successfully.'})


class MeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'user': UserSerializer(user).data
        }
        if hasattr(user, 'customer_profile'):
            data['customer'] = CustomerProfileSerializer(user.customer_profile).data
        elif hasattr(user, 'employee_profile'):
            data['employee'] = EmployeeProfileSerializer(user.employee_profile).data
        return Response(data)


from apps.notifications.models import Notification
from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer

class CustomerListView(views.APIView):
    """Employee & Admin view to inspect customers for underwriting, search, and KYC."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Requires bank staff credentials.'}, status=status.HTTP_403_FORBIDDEN)

        customers = Customer.objects.select_related('user').prefetch_related('accounts').all()

        kyc_status = request.query_params.get('kyc_status')
        if kyc_status:
            customers = customers.filter(kyc_status=kyc_status.upper())

        q = request.query_params.get('search', '').strip()
        if q:
            customers = customers.filter(
                models.Q(full_name__icontains=q) |
                models.Q(pan_number__icontains=q) |
                models.Q(customer_id__icontains=q) |
                models.Q(phone__icontains=q) |
                models.Q(user__username__icontains=q) |
                models.Q(user__email__icontains=q) |
                models.Q(accounts__account_number__icontains=q)
            ).distinct()

        serializer = CustomerProfileSerializer(customers, many=True)
        return Response(serializer.data)


class CustomerDetailView(views.APIView):
    """Employee & Admin view to inspect full customer profile, accounts, and recent transactions."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        if request.user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Requires bank staff credentials.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            customer = Customer.objects.select_related('user').prefetch_related('accounts').get(pk=pk)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        recent_txns = Transaction.objects.filter(
            models.Q(from_account__customer=customer) | models.Q(to_account__customer=customer)
        ).select_related('from_account', 'to_account').order_by('-timestamp')[:10]

        cust_data = CustomerProfileSerializer(customer).data
        return Response({
            'customer': cust_data,
            'accounts': cust_data.get('accounts', []),
            'recent_transactions': TransactionSerializer(recent_txns, many=True).data
        })


class CustomerKYCUpdateView(views.APIView):
    """Allows bank employees and admins to review and update KYC status (Verified, Rejected, Needs Review)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        return self.patch(request, pk)

    def patch(self, request, pk):
        if request.user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Bank staff credentials required.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            customer = Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('kyc_status', '').upper().strip()
        remarks = request.data.get('remarks', '').strip()

        valid_choices = [Customer.KYCStatus.VERIFIED, Customer.KYCStatus.REJECTED, Customer.KYCStatus.PENDING, 'NEEDS_REVIEW']
        if new_status not in valid_choices:
            return Response({'error': f"Invalid KYC status choice. Valid choices are: VERIFIED, REJECTED, PENDING, NEEDS_REVIEW."}, status=status.HTTP_400_BAD_REQUEST)

        if new_status in ['REJECTED', 'NEEDS_REVIEW'] and not remarks:
            return Response({'error': 'A justification reason or underwriter note is mandatory when rejecting or requesting additional KYC review.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_status == 'NEEDS_REVIEW':
            customer.kyc_status = Customer.KYCStatus.NEEDS_REVIEW
            customer.kyc_remarks = f"[Action Required - Underwriting Review]: {remarks}"
            notif_msg = f"Your KYC documentation requires additional clarification: {remarks}"
        elif new_status == Customer.KYCStatus.VERIFIED:
            customer.kyc_status = Customer.KYCStatus.VERIFIED
            customer.kyc_remarks = remarks or "KYC documents verified and approved."
            customer.kyc_verified_at = timezone.now()
            notif_msg = "Your KYC verification has been approved. All banking facilities are fully enabled."
        else: # REJECTED or PENDING
            customer.kyc_status = new_status
            customer.kyc_remarks = remarks
            notif_msg = f"Your KYC status has been updated to {new_status.lower()}: {remarks}"

        customer.save()

        # Audit log
        AuditLog.objects.create(
            user=request.user,
            action=f"KYC_{new_status}",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Customer",
            record_id=customer.customer_id,
            details=f"Customer {customer.full_name} ({customer.customer_id}) KYC set to {new_status} by {request.user.username}. Notes: {remarks}"
        )

        # Notify Customer
        Notification.objects.create(
            user=customer.user,
            title="KYC Compliance Update",
            message=notif_msg,
            notification_type=Notification.NotificationType.SECURITY
        )

        return Response(CustomerProfileSerializer(customer).data)


from rest_framework import viewsets
from rest_framework.decorators import action
from .models import KYCRequest
from .serializers import KYCRequestSerializer


class KYCRequestViewSet(viewsets.ModelViewSet):
    """
    Bank Employee & Admin KYC Verification Case Queue.
    Handles queue inspection, deterministic assignment, approval, rejection,
    and requests for additional documents with automated customer notifications.
    """
    serializer_class = KYCRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = KYCRequest.objects.select_related(
            'customer', 'customer__user', 'assigned_employee', 'assigned_employee__user',
            'reviewed_by', 'loan_application', 'loan_application__loan_type'
        ).all()

        if user.role == User.Role.CUSTOMER:
            if hasattr(user, 'customer_profile'):
                return qs.filter(customer=user.customer_profile)
            return KYCRequest.objects.none()

        # Employee & Admin filters
        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter.upper() != 'ALL':
            qs = qs.filter(status=status_filter.upper())

        assigned_to_me = self.request.query_params.get('assigned_to_me')
        if assigned_to_me and assigned_to_me.lower() == 'true':
            qs = qs.filter(assigned_employee__user=user)

        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            qs = qs.filter(assigned_employee__employee_id=employee_id)

        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            qs = qs.filter(customer__customer_id=customer_id)

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                models.Q(request_id__icontains=search) |
                models.Q(customer__full_name__icontains=search) |
                models.Q(customer__customer_id__icontains=search) |
                models.Q(customer__pan_number__icontains=search) |
                models.Q(loan_application__application_id__icontains=search)
            )

        return qs

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Staff action: Verify & Approve Customer KYC."""
        user = request.user
        if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not user.is_superuser:
            return Response({'error': 'Unauthorized. Staff credentials required.'}, status=status.HTTP_403_FORBIDDEN)

        kyc_req = self.get_object()
        notes = request.data.get('notes', '').strip() or 'KYC documents verified and approved.'
        reviewer_emp = getattr(user, 'employee_profile', None)

        kyc_req.status = KYCRequest.Status.APPROVED
        kyc_req.reviewed_by = reviewer_emp
        kyc_req.reviewed_at = timezone.now()
        kyc_req.review_notes = notes
        kyc_req.save()

        # Update customer profile
        customer = kyc_req.customer
        customer.kyc_status = Customer.KYCStatus.VERIFIED
        customer.kyc_verified_at = timezone.now()
        customer.kyc_remarks = notes
        customer.save(update_fields=['kyc_status', 'kyc_verified_at', 'kyc_remarks', 'updated_at'])

        # Notify Customer
        Notification.objects.create(
            user=customer.user,
            title="KYC Verification Approved",
            message="Your KYC verification has been approved.",
            notification_type=Notification.NotificationType.SECURITY
        )

        # Regulatory Audit Log
        AuditLog.objects.create(
            user=request.user,
            action="KYC_APPROVED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="KYCRequest",
            record_id=kyc_req.request_id,
            details=f"KYC case {kyc_req.request_id} for {customer.full_name} ({customer.customer_id}) approved by {user.username}."
        )

        return Response(KYCRequestSerializer(kyc_req).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Staff action: Reject Customer KYC (Mandatory Reason Required)."""
        user = request.user
        if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not user.is_superuser:
            return Response({'error': 'Unauthorized. Staff credentials required.'}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'error': 'A specific rejection reason is required for KYC rejection.'}, status=status.HTTP_400_BAD_REQUEST)

        kyc_req = self.get_object()
        reviewer_emp = getattr(user, 'employee_profile', None)

        kyc_req.status = KYCRequest.Status.REJECTED
        kyc_req.rejection_reason = reason
        kyc_req.reviewed_by = reviewer_emp
        kyc_req.reviewed_at = timezone.now()
        kyc_req.save()

        customer = kyc_req.customer
        customer.kyc_status = Customer.KYCStatus.REJECTED
        customer.kyc_remarks = f"Rejected: {reason}"
        customer.save(update_fields=['kyc_status', 'kyc_remarks', 'updated_at'])

        # Notify Customer with reason
        Notification.objects.create(
            user=customer.user,
            title="KYC Verification Rejected",
            message=f"Your KYC verification was rejected. Reason: {reason}",
            notification_type=Notification.NotificationType.SECURITY
        )

        # Regulatory Audit Log
        AuditLog.objects.create(
            user=request.user,
            action="KYC_REJECTED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="KYCRequest",
            record_id=kyc_req.request_id,
            details=f"KYC case {kyc_req.request_id} for {customer.full_name} rejected by {user.username}. Reason: {reason}"
        )

        return Response(KYCRequestSerializer(kyc_req).data)

    @action(detail=True, methods=['post'])
    def needs_review(self, request, pk=None):
        """Staff action: Request Additional Review / Clarification (Notes Required)."""
        user = request.user
        if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not user.is_superuser:
            return Response({'error': 'Unauthorized. Staff credentials required.'}, status=status.HTTP_403_FORBIDDEN)

        notes = request.data.get('notes', '').strip()
        if not notes:
            return Response({'error': 'Detailed notes explaining the required review are mandatory.'}, status=status.HTTP_400_BAD_REQUEST)

        kyc_req = self.get_object()
        reviewer_emp = getattr(user, 'employee_profile', None)

        kyc_req.status = KYCRequest.Status.NEEDS_REVIEW
        kyc_req.review_notes = notes
        kyc_req.reviewed_by = reviewer_emp
        kyc_req.reviewed_at = timezone.now()
        kyc_req.save()

        customer = kyc_req.customer
        customer.kyc_status = Customer.KYCStatus.NEEDS_REVIEW
        customer.kyc_remarks = f"Action Required: {notes}"
        customer.save(update_fields=['kyc_status', 'kyc_remarks', 'updated_at'])

        # Notify Customer
        Notification.objects.create(
            user=customer.user,
            title="KYC Additional Review Required",
            message=f"Your KYC verification requires additional review: {notes}",
            notification_type=Notification.NotificationType.SECURITY
        )

        # Regulatory Audit Log
        AuditLog.objects.create(
            user=request.user,
            action="KYC_NEEDS_REVIEW",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="KYCRequest",
            record_id=kyc_req.request_id,
            details=f"KYC case {kyc_req.request_id} marked NEEDS_REVIEW by {user.username}. Notes: {notes}"
        )

        return Response(KYCRequestSerializer(kyc_req).data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign or re-assign KYC case to an employee."""
        user = request.user
        if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not user.is_superuser:
            return Response({'error': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)

        kyc_req = self.get_object()
        target_emp_id = request.data.get('employee_id')

        if target_emp_id:
            try:
                emp = Employee.objects.get(id=target_emp_id, is_active=True)
                kyc_req.assigned_employee = emp
                kyc_req.status = KYCRequest.Status.ASSIGNED
                kyc_req.save(update_fields=['assigned_employee', 'status'])
            except Employee.DoesNotExist:
                return Response({'error': 'Target employee not found or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Deterministic least-loaded assignment
            KYCRequest.assign_to_employee(kyc_req)

        return Response(KYCRequestSerializer(kyc_req).data)


class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Staff / Admin view to list all bank employees, branch affiliations,
    and current assigned KYC workload counts.
    """
    serializer_class = EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not user.is_superuser:
            return Employee.objects.none()

        qs = Employee.objects.select_related('user', 'branch').all()
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                models.Q(full_name__icontains=search) |
                models.Q(employee_id__icontains=search) |
                models.Q(designation__icontains=search) |
                models.Q(branch__branch_name__icontains=search)
            )
        return qs

    def list(self, request, *args, **kwargs):
        if request.user.role == User.Role.CUSTOMER:
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        qs = self.get_queryset()
        data = []
        for emp in qs:
            emp_data = EmployeeProfileSerializer(emp).data
            # Compute workload
            open_kyc = KYCRequest.objects.filter(
                assigned_employee=emp,
                status__in=[KYCRequest.Status.PENDING, KYCRequest.Status.ASSIGNED, KYCRequest.Status.NEEDS_REVIEW]
            ).count()
            completed_kyc = KYCRequest.objects.filter(
                assigned_employee=emp,
                status=KYCRequest.Status.APPROVED
            ).count()
            emp_data['open_kyc_count'] = open_kyc
            emp_data['completed_kyc_count'] = completed_kyc
            emp_data['total_assigned_kyc'] = open_kyc + completed_kyc
            data.append(emp_data)
        return Response(data)


