from rest_framework import viewsets, views, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.core.exceptions import ValidationError
from .models import Transaction, Beneficiary
from .serializers import (
    TransactionSerializer, TransferRequestSerializer, BeneficiarySerializer
)
from .services import TransferService
from apps.users.models import User
from apps.notifications.models import Notification

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Transaction.objects.select_related('from_account', 'to_account', 'from_account__customer', 'to_account__customer').all()

        if user.role == User.Role.CUSTOMER:
            if hasattr(user, 'customer_profile'):
                cust = user.customer_profile
                qs = qs.filter(
                    Q(from_account__customer=cust) | Q(to_account__customer=cust)
                )
            else:
                return Transaction.objects.none()

        # Query Filters for Customer, Employee & Admin
        category = self.request.query_params.get('category')
        if category and category != 'All':
            qs = qs.filter(category=category)

        txn_type = self.request.query_params.get('type')
        if txn_type:
            qs = qs.filter(transaction_type=txn_type)

        txn_status = self.request.query_params.get('status')
        if txn_status:
            qs = qs.filter(status=txn_status.upper())

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(beneficiary_name__icontains=search) |
                Q(transaction_id__icontains=search) |
                Q(reference_number__icontains=search) |
                Q(remarks__icontains=search)
            )

        account_id = self.request.query_params.get('account_id')
        if account_id:
            qs = qs.filter(Q(from_account_id=account_id) | Q(to_account_id=account_id))

        account_number = self.request.query_params.get('account_number')
        if account_number:
            qs = qs.filter(
                Q(from_account__account_number=account_number) |
                Q(to_account__account_number=account_number) |
                Q(beneficiary_account=account_number)
            )

        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            qs = qs.filter(
                Q(from_account__customer__customer_id=customer_id) |
                Q(to_account__customer__customer_id=customer_id)
            )

        min_amount = self.request.query_params.get('min_amount')
        if min_amount:
            try:
                qs = qs.filter(amount__gte=float(min_amount))
            except ValueError:
                pass

        max_amount = self.request.query_params.get('max_amount')
        if max_amount:
            try:
                qs = qs.filter(amount__lte=float(max_amount))
            except ValueError:
                pass

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        return qs

    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        """Admin action: Reverse a completed transaction with compensating ledger entry."""
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Admin permissions required to reverse transactions.'}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'error': 'A justification reason is required to reverse a transaction.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comp_txn = TransferService.reverse_transaction(
                transaction_id=pk,
                reason=reason,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            return Response({
                'message': 'Transaction successfully reversed with compensating ledger entry.',
                'status': 'REVERSED',
                'reversal_reference': comp_txn.reference_number,
                'compensating_transaction': TransactionSerializer(comp_txn).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'error': str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Reversal failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class TransferExecuteView(views.APIView):
    """
    Executes an atomic bank money transfer with ACID protection.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            txn = TransferService.execute_transfer(
                from_account_id=data['from_account_id'],
                to_account_number=data['to_account_number'],
                to_ifsc=data['to_ifsc'],
                beneficiary_name=data['beneficiary_name'],
                amount=data['amount'],
                category=data.get('category', Transaction.Category.TRANSFER),
                remarks=data.get('remarks', ''),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )

            # Create notification
            Notification.objects.create(
                user=request.user,
                title="Transfer Successful",
                message=f"₹{data['amount']:,.2f} transferred to {data['beneficiary_name']} successfully.",
                notification_type=Notification.NotificationType.TRANSFER_SUCCESS
            )

            return Response({
                'message': 'Transfer completed successfully.',
                'transaction': TransactionSerializer(txn).data
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'error': str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Transfer failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BeneficiaryViewSet(viewsets.ModelViewSet):
    serializer_class = BeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'customer_profile'):
            return Beneficiary.objects.filter(customer=user.customer_profile)
        return Beneficiary.objects.none()

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'customer_profile'):
            raise ValidationError("Only customer profiles can register beneficiaries.")
        serializer.save(customer=self.request.user.customer_profile)
