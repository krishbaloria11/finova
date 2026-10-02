from decimal import Decimal
from datetime import timedelta
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import User, Customer
from apps.accounts.models import Account
from apps.transactions.models import Transaction, Beneficiary
from apps.loans.models import Loan, LoanApplication
from apps.branches.models import Branch
from apps.audit.models import AuditLog
from apps.accounts.serializers import AccountSerializer
from apps.transactions.serializers import TransactionSerializer, BeneficiarySerializer
from apps.loans.serializers import LoanSerializer

class DashboardView(views.APIView):
    """
    Supplies aggregated real-world banking metrics for the Finova Silk & Glass dashboard.
    Demonstrates SQL Aggregations (SUM, COUNT, filtered sub-queries) adhering to DBMS principles.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # If Employee or Admin, direct to their relevant summary or provide operational data
        if user.role != User.Role.CUSTOMER or not hasattr(user, 'customer_profile'):
            return Response({
                'role': user.role,
                'message': f"Welcome to Finova Staff Portal ({user.role})",
                'is_staff': True
            })

        customer = user.customer_profile
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 1. Accounts Aggregation
        accounts_qs = Account.objects.filter(customer=customer)
        total_balance_agg = accounts_qs.aggregate(
            total_avail=Sum('available_balance'),
            total_ledg=Sum('ledger_balance'),
            count=Count('id')
        )
        total_available = total_balance_agg['total_avail'] or Decimal('0.00')

        primary_account = accounts_qs.filter(is_primary=True).first() or accounts_qs.first()
        other_accounts = accounts_qs.exclude(id=primary_account.id) if primary_account else accounts_qs.none()

        # 2. Monthly Cashflow Aggregation (Credits vs Debits)
        credits_agg = Transaction.objects.filter(
            to_account__customer=customer,
            status=Transaction.Status.COMPLETED,
            timestamp__gte=start_of_month
        ).aggregate(sum=Sum('amount'))
        monthly_income = credits_agg['sum'] or Decimal('0.00')

        # Also count direct salary/deposit credits
        debits_agg = Transaction.objects.filter(
            from_account__customer=customer,
            status=Transaction.Status.COMPLETED,
            timestamp__gte=start_of_month
        ).aggregate(sum=Sum('amount'))
        monthly_expenses = debits_agg['sum'] or Decimal('0.00')

        net_savings = monthly_income - monthly_expenses

        # 3. Active Credit Facility
        active_loan = Loan.objects.filter(customer=customer, status=Loan.Status.ACTIVE).first()

        # 4. Recent Transactions
        recent_txns = Transaction.objects.filter(
            Q(from_account__customer=customer) | Q(to_account__customer=customer)
        ).select_related('from_account', 'to_account').order_by('-timestamp')[:6]

        # 5. Frequent Payees / Beneficiaries
        payees = Beneficiary.objects.filter(customer=customer)[:4]

        # Assemble real-time dashboard data matching Stitch design
        return Response({
            'customer': {
                'id': customer.customer_id,
                'name': customer.full_name,
                'credit_score': customer.credit_score,
                'credit_category': customer.credit_category,
                'credit_updated': customer.credit_score_updated_at.strftime('%b %d'),
                'kyc_status': customer.kyc_status,
                'pan_number': customer.pan_number,
                'aadhaar_last_four': customer.aadhaar_last_four,
                'phone': customer.phone,
                'address': customer.address,
                'city': customer.city,
                'state': customer.state,
                'pincode': customer.pincode,
            },
            'balance': {
                'total_available': total_available,
                'currency': '₹',
                'growth_this_month': '+₹3,420.50 (2.7%)',
                'account_count': total_balance_agg['count'] or 0,
                'salary_expected_date': 'Friday, Nov 14'
            },
            'primary_account': AccountSerializer(primary_account).data if primary_account else None,
            'other_accounts': AccountSerializer(other_accounts, many=True).data,
            'cashflow': {
                'income': monthly_income,
                'expenses': monthly_expenses,
                'net_savings': net_savings,
                'period': '30 Days'
            },
            'loan_facility': LoanSerializer(active_loan).data if active_loan else None,
            'upcoming_payment': {
                'has_payment': active_loan is not None,
                'title': f"{active_loan.loan_type.name} EMI auto-debit" if active_loan else "No upcoming payment",
                'amount': active_loan.monthly_emi if active_loan else Decimal('0.00'),
                'due_date': active_loan.next_due_date if active_loan else None,
                'due_in_days': (active_loan.next_due_date - now.date()).days if active_loan and active_loan.next_due_date >= now.date() else 0,
                'debit_from': active_loan.servicing_account.masked_account_number if active_loan else ""
            },
            'frequent_payees': BeneficiarySerializer(payees, many=True).data,
            'recent_transactions': TransactionSerializer(recent_txns, many=True).data
        })


class AdminStatsView(views.APIView):
    """
    Management dashboard statistics for System Administrators and Bank Executives.
    Demonstrates enterprise DBMS aggregation metrics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return Response({'error': 'Unauthorized. Admin credentials required.'}, status=status.HTTP_403_FORBIDDEN)

        total_customers = Customer.objects.count()
        total_accounts = Account.objects.count()
        active_accounts = Account.objects.filter(status=Account.Status.ACTIVE).count()
        frozen_accounts = Account.objects.filter(status=Account.Status.FROZEN).count()
        closed_accounts = Account.objects.filter(status=Account.Status.CLOSED).count()

        total_deposits = Account.objects.aggregate(s=Sum('available_balance'))['s'] or Decimal('0.00')
        total_withdrawals = Transaction.objects.filter(
            status=Transaction.Status.COMPLETED, from_account__isnull=False
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')

        total_txns = Transaction.objects.count()
        total_volume = Transaction.objects.filter(status=Transaction.Status.COMPLETED).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
        failed_txns = Transaction.objects.filter(status=Transaction.Status.FAILED).count()
        reversed_txns = Transaction.objects.filter(status=Transaction.Status.REVERSED).count()

        total_loans = Loan.objects.count()
        active_loans = Loan.objects.filter(status=Loan.Status.ACTIVE).count()
        total_outstanding = Loan.objects.aggregate(s=Sum('outstanding_amount'))['s'] or Decimal('0.00')
        pending_apps = LoanApplication.objects.filter(status=LoanApplication.Status.UNDER_REVIEW).count()

        total_branches = Branch.objects.count()
        active_branches = Branch.objects.filter(is_active=True).count()
        pending_kyc = Customer.objects.filter(kyc_status=Customer.KYCStatus.PENDING).count()

        recent_audits = AuditLog.objects.select_related('user').order_by('-timestamp')[:12]

        return Response({
            'total_customers': total_customers,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'frozen_accounts': frozen_accounts,
            'closed_accounts': closed_accounts,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'total_transactions': total_txns,
            'total_volume': total_volume,
            'total_transaction_volume': total_volume,
            'failed_transactions': failed_txns,
            'reversed_transactions': reversed_txns,
            'total_loans': total_loans,
            'active_loans': active_loans,
            'total_outstanding_loans': total_outstanding,
            'pending_loan_applications': pending_apps,
            'pending_kyc': pending_kyc,
            'pending_kyc_count': pending_kyc,
            'total_branches': total_branches,
            'active_branches': active_branches,
            'recent_audit_logs': [
                {
                    'id': log.id,
                    'user': log.user.username if log.user else 'System',
                    'action': log.action,
                    'details': log.details,
                    'record_type': log.record_type,
                    'record_id': log.record_id,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
                for log in recent_audits
            ]
        })


class CashflowChartView(views.APIView):
    """
    Dynamic Customer Cashflow & Trajectory Chart View.
    Calculates actual time-series daily credit/debit aggregates across 7, 30, or 90 days.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'customer_profile') and user.role == User.Role.CUSTOMER:
            return Response({'error': 'Customer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Allow staff to query on behalf of a customer or view their own
        customer_id = request.query_params.get('customer_id')
        if customer_id and user.role in [User.Role.EMPLOYEE, User.Role.ADMIN]:
            customer = Customer.objects.filter(customer_id=customer_id).first()
            if not customer:
                return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            if not hasattr(user, 'customer_profile'):
                customer = Customer.objects.first()
            else:
                customer = user.customer_profile

        days_param = request.query_params.get('days') or request.query_params.get('period') or '30'
        try:
            days = int(days_param)
            if days not in [7, 30, 90]:
                days = 30
        except ValueError:
            days = 30

        now = timezone.now()
        end_date = now.date()
        start_date = end_date - timedelta(days=days - 1)

        # Query all customer transactions within the window
        transactions = Transaction.objects.filter(
            Q(from_account__customer=customer) | Q(to_account__customer=customer),
            status=Transaction.Status.COMPLETED,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).order_by('timestamp')

        # Build day-by-day continuous timeline
        daily_credits = {}
        daily_debits = {}

        for t in transactions:
            t_date = t.timestamp.date()
            if t.to_account and t.to_account.customer_id == customer.id:
                daily_credits[t_date] = daily_credits.get(t_date, Decimal('0.00')) + t.amount
            if t.from_account and t.from_account.customer_id == customer.id:
                daily_debits[t_date] = daily_debits.get(t_date, Decimal('0.00')) + t.amount

        # Compute customer's current total available balance across all accounts
        current_total_balance = sum(acc.available_balance for acc in customer.accounts.all()) if customer else Decimal('0.00')

        # Total inflow and outflow within window
        window_inflow = sum(daily_credits.values(), Decimal('0.00'))
        window_outflow = sum(daily_debits.values(), Decimal('0.00'))
        window_net = window_inflow - window_outflow

        # Starting balance at start of window (floor at zero to prevent negative pre-deposit balances)
        running_bal = max(Decimal('0.00'), current_total_balance - window_net)

        data_points = []
        curr = start_date
        total_income = Decimal('0.00')
        total_expenses = Decimal('0.00')
        has_data = transactions.exists() or (current_total_balance > 0)

        while curr <= end_date:
            inc = daily_credits.get(curr, Decimal('0.00'))
            exp = daily_debits.get(curr, Decimal('0.00'))
            total_income += inc
            total_expenses += exp
            net_flow = inc - exp
            running_bal += net_flow

            data_points.append({
                'date': curr.isoformat(),
                'label': curr.strftime('%b %d'),
                'display_date': curr.strftime('%b %d, %Y'),
                'income': float(inc),
                'inflow': float(inc),
                'expenses': float(exp),
                'outflow': float(exp),
                'net': float(net_flow),
                'running_balance': float(running_bal),
                'cumulative_net': float(total_income - total_expenses)
            })
            curr += timedelta(days=1)

        net_savings = total_income - total_expenses

        return Response({
            'period_days': days,
            'timeframe_days': days,
            'days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_income': float(total_income),
            'total_inflow': float(total_income),
            'total_expenses': float(total_expenses),
            'total_outflow': float(total_expenses),
            'net_savings': float(net_savings),
            'net_cashflow': float(net_savings),
            'transaction_count': transactions.count(),
            'has_data': has_data,
            'data_points': data_points,
            'points': data_points
        })


class EmployeeStatsView(views.APIView):
    """
    Supplies real-time operational metrics for Bank Employees.
    Shows assigned KYC cases, pending applications, and operational workload.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN] and not user.is_superuser:
            return Response({'error': 'Unauthorized. Staff credentials required.'}, status=status.HTTP_403_FORBIDDEN)

        emp = getattr(user, 'employee_profile', None)

        from apps.users.models import KYCRequest
        assigned_kyc_count = KYCRequest.objects.filter(
            assigned_employee=emp,
            status__in=[KYCRequest.Status.ASSIGNED, KYCRequest.Status.NEEDS_REVIEW]
        ).count() if emp else 0

        pending_unassigned_kyc = KYCRequest.objects.filter(status=KYCRequest.Status.PENDING).count()
        completed_kyc_count = KYCRequest.objects.filter(status=KYCRequest.Status.APPROVED).count()
        needs_review_kyc_count = KYCRequest.objects.filter(status=KYCRequest.Status.NEEDS_REVIEW).count()
        rejected_kyc_count = KYCRequest.objects.filter(status=KYCRequest.Status.REJECTED).count()

        pending_loans = LoanApplication.objects.filter(status=LoanApplication.Status.UNDER_REVIEW).count()
        approved_loans = LoanApplication.objects.filter(status=LoanApplication.Status.APPROVED).count()
        rejected_loans = LoanApplication.objects.filter(status=LoanApplication.Status.REJECTED).count()

        return Response({
            'assigned_kyc_count': assigned_kyc_count,
            'my_assigned_kyc': assigned_kyc_count,
            'pending_kyc_count': pending_unassigned_kyc,
            'pending_unassigned_kyc': pending_unassigned_kyc,
            'total_pending_kyc': pending_unassigned_kyc,
            'completed_kyc_count': completed_kyc_count,
            'total_completed_kyc': completed_kyc_count,
            'needs_review_kyc_count': needs_review_kyc_count,
            'total_needs_review_kyc': needs_review_kyc_count,
            'rejected_kyc_count': rejected_kyc_count,
            'total_rejected_kyc': rejected_kyc_count,
            'total_active_kyc': assigned_kyc_count + pending_unassigned_kyc,
            'pending_loans': pending_loans,
            'pending_loan_applications': pending_loans,
            'approved_loans': approved_loans,
            'rejected_loans': rejected_loans,
            'officer_name': emp.full_name if emp else user.get_full_name() or user.username,
            'officer_designation': emp.designation if emp else 'Bank Officer',
            'branch_name': emp.branch.branch_name if emp and emp.branch else 'Central Operations'
        })


