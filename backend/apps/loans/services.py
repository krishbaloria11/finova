import math
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import Account
from apps.transactions.models import Transaction
from apps.loans.models import Loan, LoanApplication, LoanPayment
from apps.audit.models import AuditLog

class LoanService:
    """
    Financial mathematics & transactional underwriting service for loans.
    """

    @staticmethod
    def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> dict:
        """
        Calculates standard reducing balance Equated Monthly Installment (EMI):
        E = P * r * (1 + r)^n / ((1 + r)^n - 1)
        where:
        P = Principal loan amount
        r = Monthly interest rate (annual_rate / 12 / 100)
        n = Tenure in months
        """
        p = float(principal)
        r = float(annual_rate) / (12.0 * 100.0)
        n = int(tenure_months)

        if n <= 0:
            raise ValidationError("Tenure must be at least 1 month.")

        if r == 0:
            emi = p / n
        else:
            emi = (p * r * math.pow(1 + r, n)) / (math.pow(1 + r, n) - 1)

        total_payable = emi * n
        total_interest = total_payable - p

        dec_emi = Decimal(str(round(emi, 2))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        dec_total_payable = Decimal(str(round(total_payable, 2))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        dec_total_interest = Decimal(str(round(total_interest, 2))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'principal': principal,
            'annual_rate': annual_rate,
            'tenure_months': tenure_months,
            'monthly_emi': dec_emi,
            'total_interest': dec_total_interest,
            'total_payable': dec_total_payable
        }

    @staticmethod
    def generate_amortization_schedule(principal: Decimal, annual_rate: Decimal, tenure_months: int, limit: int = 12) -> list:
        """
        Generates month-by-month loan repayment schedule.
        """
        calc = LoanService.calculate_emi(principal, annual_rate, tenure_months)
        emi = calc['monthly_emi']
        monthly_rate = Decimal(str(float(annual_rate) / (12.0 * 100.0)))

        schedule = []
        balance = principal

        for month in range(1, min(tenure_months + 1, limit + 1)):
            interest = (balance * monthly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            principal_paid = emi - interest
            if principal_paid > balance:
                principal_paid = balance
                emi = principal_paid + interest
            ending_balance = max(Decimal('0.00'), balance - principal_paid)

            schedule.append({
                'month': month,
                'beginning_balance': balance,
                'emi': emi,
                'principal_paid': principal_paid,
                'interest_paid': interest,
                'ending_balance': ending_balance
            })
            balance = ending_balance
            if balance <= 0:
                break

        return schedule

    @classmethod
    def pay_emi(
        cls,
        loan_id: int,
        account_id: int,
        amount: Decimal,
        user = None,
        ip_address: str = "127.0.0.1"
    ) -> LoanPayment:
        """
        Executes an atomic EMI installment or prepayment debit.
        """
        with transaction.atomic():
            try:
                loan = Loan.objects.select_for_update().get(id=loan_id)
            except Loan.DoesNotExist:
                raise ValidationError("Loan facility not found.")

            try:
                account = Account.objects.select_for_update().get(id=account_id)
            except Account.DoesNotExist:
                raise ValidationError("Payment account not found.")

            if account.customer_id != loan.customer_id:
                raise ValidationError("Payment account does not belong to the loan borrower.")

            if account.available_balance < amount:
                raise ValidationError(
                    f"Insufficient funds in account. Available: ₹{account.available_balance:,.2f}, Required: ₹{amount:,.2f}"
                )

            if loan.outstanding_amount <= Decimal('0.00'):
                raise ValidationError("This loan is already fully settled.")

            # Calculate principal vs interest portion
            monthly_rate = Decimal(str(float(loan.interest_rate) / (12.0 * 100.0)))
            interest_portion = (loan.outstanding_amount * monthly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if interest_portion > amount:
                interest_portion = amount
            principal_portion = amount - interest_portion

            # Deduct from account
            account.available_balance -= amount
            account.ledger_balance -= amount
            account.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

            # Update loan balances
            loan.outstanding_amount = max(Decimal('0.00'), loan.outstanding_amount - principal_portion)
            loan.repaid_amount += amount

            # Check if settled
            if loan.outstanding_amount == Decimal('0.00'):
                loan.status = Loan.Status.COMPLETED
            else:
                # Advance next due date by 1 month
                loan.next_due_date = loan.next_due_date + relativedelta(months=1)

            loan.save(update_fields=['outstanding_amount', 'repaid_amount', 'status', 'next_due_date', 'updated_at'])

            # Create banking ledger transaction
            txn_id = f"TXN{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            Transaction.objects.create(
                transaction_id=txn_id,
                from_account=account,
                to_account=None,
                beneficiary_name=f"Finova {loan.loan_type.name} EMI",
                transaction_type=Transaction.TransactionType.EMI_PAYMENT,
                category=Transaction.Category.EMI_BILLS,
                amount=amount,
                balance_after=account.available_balance,
                status=Transaction.Status.COMPLETED,
                remarks=f"Auto-debit / Installment for Loan #{loan.loan_id}",
                reference_number=f"EMI-REF-{uuid.uuid4().hex[:8].upper()}",
                timestamp=timezone.now()
            )

            # Create LoanPayment record
            payment_ref = f"PMT-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            receipt_ref = f"RCPT-{uuid.uuid4().hex[:8].upper()}"
            payment_record = LoanPayment.objects.create(
                payment_id=payment_ref,
                loan=loan,
                account=account,
                amount_paid=amount,
                principal_component=principal_portion,
                interest_component=interest_portion,
                installment_number=loan.payments.count() + 1,
                payment_date=timezone.now(),
                status=LoanPayment.Status.SUCCESSFUL,
                receipt_number=receipt_ref,
                remarks=f"EMI installment for {loan.loan_id}"
            )

            # Audit record
            AuditLog.objects.create(
                user=user,
                action="EMI_PAID",
                ip_address=ip_address,
                record_type="LoanPayment",
                record_id=payment_ref,
                details=f"Paid ₹{amount:,.2f} for loan {loan.loan_id}. Remaining balance: ₹{loan.outstanding_amount:,.2f}"
            )

            return payment_record

    @classmethod
    def review_application(
        cls,
        application_id: int,
        decision: str,
        reviewer_employee,
        review_notes: str = "",
        sanction_account_id: int = None
    ) -> LoanApplication:
        """
        Employee/Admin loan underwriting decision (APPROVE or REJECT).
        If approved, establishes the active sanctioned Loan facility.
        """
        with transaction.atomic():
            app = LoanApplication.objects.select_for_update().get(id=application_id)

            if app.status not in [LoanApplication.Status.SUBMITTED, LoanApplication.Status.UNDER_REVIEW]:
                raise ValidationError(f"Application is already finalized with status: {app.status}")

            app.reviewed_by = reviewer_employee
            app.reviewed_at = timezone.now()
            app.review_notes = review_notes

            decision_norm = 'APPROVE' if decision in ['APPROVE', 'APPROVED'] else ('REJECT' if decision in ['REJECT', 'REJECTED'] else decision)

            if decision_norm == 'APPROVE':
                app.status = LoanApplication.Status.APPROVED
                app.save()

                # Determine servicing account
                customer = app.customer
                servicing_acc = None
                if sanction_account_id:
                    servicing_acc = Account.objects.get(id=sanction_account_id, customer=customer)
                else:
                    servicing_acc = customer.accounts.filter(is_primary=True).first() or customer.accounts.first()

                if not servicing_acc:
                    raise ValidationError("Customer must possess at least one active bank account to sanction a loan.")

                # Calculate terms
                calc = cls.calculate_emi(app.requested_amount, app.proposed_interest_rate, app.tenure_months)

                # Generate Loan ID
                code_prefix = app.loan_type.code[:2].upper()
                loan_num = f"{code_prefix}-{timezone.now().strftime('%y%m')}{uuid.uuid4().hex[:4].upper()}"

                today = timezone.now().date()
                end_date = today + relativedelta(months=app.tenure_months)
                next_due = today + relativedelta(months=1)

                Loan.objects.create(
                    loan_id=loan_num,
                    customer=customer,
                    loan_type=app.loan_type,
                    application=app,
                    servicing_account=servicing_acc,
                    principal_amount=app.requested_amount,
                    interest_rate=app.proposed_interest_rate,
                    tenure_months=app.tenure_months,
                    monthly_emi=calc['monthly_emi'],
                    total_payable=calc['total_payable'],
                    total_interest=calc['total_interest'],
                    outstanding_amount=app.requested_amount,
                    repaid_amount=Decimal('0.00'),
                    start_date=today,
                    end_date=end_date,
                    next_due_date=next_due,
                    auto_debit=True,
                    status=Loan.Status.ACTIVE
                )

                # Disburse loan amount to customer account
                servicing_acc.available_balance += app.requested_amount
                servicing_acc.ledger_balance += app.requested_amount
                servicing_acc.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

                # Create disbursement ledger entry
                Transaction.objects.create(
                    transaction_id=f"DSB{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    from_account=None,
                    to_account=servicing_acc,
                    beneficiary_name=f"Finova {app.loan_type.name} Disbursement",
                    transaction_type=Transaction.TransactionType.LOAN_DISBURSEMENT,
                    category=Transaction.Category.TRANSFER,
                    amount=app.requested_amount,
                    balance_after=servicing_acc.available_balance,
                    status=Transaction.Status.COMPLETED,
                    remarks=f"Principal disbursement for loan {loan_num}",
                    timestamp=timezone.now()
                )

            elif decision_norm == 'REJECT':
                app.status = LoanApplication.Status.REJECTED
                app.save()
            elif decision_norm in ['UNDER_REVIEW', 'REVIEW', 'NEEDS_REVIEW']:
                app.status = LoanApplication.Status.UNDER_REVIEW
                app.save()
            else:
                raise ValidationError("Decision must be either 'APPROVE', 'REJECT', or 'UNDER_REVIEW'.")


            # Audit entry
            AuditLog.objects.create(
                user=reviewer_employee.user if reviewer_employee else None,
                action=f"LOAN_{decision}",
                record_type="LoanApplication",
                record_id=app.application_id,
                details=f"Loan application {app.application_id} {decision.lower()}d. Notes: {review_notes}"
            )

            return app
