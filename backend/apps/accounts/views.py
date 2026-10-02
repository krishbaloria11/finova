from decimal import Decimal
from rest_framework import viewsets, views, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from .models import Account, AccountType
from .serializers import AccountSerializer, AccountTypeSerializer
from apps.users.models import User
from apps.audit.models import AuditLog

class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Account.objects.select_related('customer', 'customer__user', 'branch', 'account_type').all()

        if user.role == User.Role.CUSTOMER:
            if hasattr(user, 'customer_profile'):
                return qs.filter(customer=user.customer_profile)
            return Account.objects.none()

        # Employee & Admin filters
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            qs = qs.filter(customer__customer_id=customer_id)

        acc_status = self.request.query_params.get('status')
        if acc_status:
            qs = qs.filter(status=acc_status.upper())

        account_type = self.request.query_params.get('account_type')
        if account_type:
            qs = qs.filter(account_type__code=account_type.upper())

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(account_number__icontains=search) |
                Q(customer__full_name__icontains=search) |
                Q(customer__pan_number__icontains=search) |
                Q(customer__phone__icontains=search) |
                Q(customer__customer_id__icontains=search) |
                Q(customer__user__username__icontains=search)
            )

        return qs

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Demonstrates DBMS SQL Aggregation (SUM, COUNT) across customer accounts.
        """
        qs = self.get_queryset()
        aggregates = qs.aggregate(
            total_available=Sum('available_balance'),
            total_ledger=Sum('ledger_balance'),
            account_count=Count('id')
        )
        return Response({
            'total_available_balance': aggregates['total_available'] or Decimal('0.00'),
            'total_ledger_balance': aggregates['total_ledger'] or Decimal('0.00'),
            'total_accounts': aggregates['account_count'] or 0,
            'currency': 'INR'
        })

    @action(detail=True, methods=['post'])
    def freeze(self, request, pk=None):
        """Admin action: Freeze account to block outgoing transfers and withdrawals."""
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Admin permissions required to freeze accounts.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'error': 'A valid reason is required to freeze an account.'}, status=status.HTTP_400_BAD_REQUEST)

        prev_status = account.status
        account.status = Account.Status.FROZEN
        account.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user=request.user,
            action="ACCOUNT_FROZEN",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Account",
            record_id=account.account_number,
            details=f"Account {account.account_number} ({account.customer.full_name}) frozen. Prev: {prev_status}. Reason: {reason}"
        )

        return Response({
            'message': f"Account {account.account_number} successfully frozen.",
            'account': AccountSerializer(account).data
        })

    @action(detail=True, methods=['post'])
    def unfreeze(self, request, pk=None):
        """Admin action: Unfreeze account and restore to ACTIVE status."""
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Admin permissions required to unfreeze accounts.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        reason = request.data.get('reason', '').strip() or 'Administrative review completed'

        prev_status = account.status
        account.status = Account.Status.ACTIVE
        account.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user=request.user,
            action="ACCOUNT_UNFROZEN",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Account",
            record_id=account.account_number,
            details=f"Account {account.account_number} ({account.customer.full_name}) unfrozen to ACTIVE. Prev: {prev_status}. Reason: {reason}"
        )

        return Response({
            'message': f"Account {account.account_number} successfully restored to ACTIVE.",
            'account': AccountSerializer(account).data
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Admin action: Activate an account."""
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Admin permissions required.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        account.status = Account.Status.ACTIVE
        account.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user=request.user,
            action="ACCOUNT_ACTIVATED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Account",
            record_id=account.account_number,
            details=f"Account {account.account_number} marked ACTIVE by {request.user.username}"
        )

        return Response({
            'message': f"Account {account.account_number} is now ACTIVE.",
            'account': AccountSerializer(account).data
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Admin action: Deactivate (close/dormant) an account."""
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Admin permissions required.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'error': 'A reason is required to deactivate an account.'}, status=status.HTTP_400_BAD_REQUEST)

        account.status = Account.Status.CLOSED
        account.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user=request.user,
            action="ACCOUNT_DEACTIVATED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Account",
            record_id=account.account_number,
            details=f"Account {account.account_number} deactivated/closed. Reason: {reason}"
        )

        return Response({
            'message': f"Account {account.account_number} has been deactivated.",
            'account': AccountSerializer(account).data
        })

    @action(detail=True, methods=['post'])
    def flag_review(self, request, pk=None):
        """Employee / Admin service action: Flag account for risk or compliance review."""
        if request.user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Bank staff credentials required.'}, status=status.HTTP_403_FORBIDDEN)

        account = self.get_object()
        note = request.data.get('note', '').strip()
        if not note:
            return Response({'error': 'Service note or review reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

        AuditLog.objects.create(
            user=request.user,
            action="ACCOUNT_SERVICE_FLAG",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Account",
            record_id=account.account_number,
            details=f"Staff {request.user.username} logged internal service note for account {account.account_number}: {note}"
        )

        return Response({
            'message': f"Account {account.account_number} flagged for review with audit note logged.",
            'account': AccountSerializer(account).data
        })


class AccountTypeListView(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        types = AccountType.objects.all()
        return Response(AccountTypeSerializer(types, many=True).data)

