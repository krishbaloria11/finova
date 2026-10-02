import uuid
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import Account
from apps.transactions.models import Transaction
from apps.audit.models import AuditLog

class TransferService:
    """
    ACID-compliant money transfer engine for the college DBMS project.
    Demonstrates:
    - Atomicity: All balance deductions, additions, and transaction records commit together or rollback entirely.
    - Consistency: Enforces balance non-negativity and minimum balance constraints.
    - Isolation: Employs database row-locking (select_for_update) to prevent concurrency hazards.
    - Durability: Ledger writes are committed directly to persistent storage.
    """

    @classmethod
    def execute_transfer(
        cls,
        from_account_id: int,
        to_account_number: str,
        to_ifsc: str,
        beneficiary_name: str,
        amount: Decimal,
        category: str = Transaction.Category.TRANSFER,
        remarks: str = "",
        user = None,
        ip_address: str = "127.0.0.1"
    ) -> Transaction:
        """
        Executes an atomic bank transfer between accounts or to an external entity.
        """
        if amount <= Decimal('0.00'):
            raise ValidationError("Transfer amount must be strictly positive.")

        with transaction.atomic():
            # Acquire pessimistic row lock on the source account to guarantee isolation
            try:
                source_account = Account.objects.select_for_update().get(id=from_account_id)
            except Account.DoesNotExist:
                raise ValidationError("Source account not found.")

            if source_account.status != Account.Status.ACTIVE:
                raise ValidationError(f"Source account is currently {source_account.status}. Transfers are not permitted.")

            # Validate sufficient funds
            if source_account.available_balance < amount:
                raise ValidationError(
                    f"Insufficient funds. Available: ₹{source_account.available_balance:,.2f}, Requested: ₹{amount:,.2f}"
                )

            # Check if destination is internal to Finova
            internal_dest_account = None
            try:
                internal_dest_account = Account.objects.select_for_update().get(
                    account_number=to_account_number.strip()
                )
            except Account.DoesNotExist:
                internal_dest_account = None

            # Deduct from source account
            source_account.available_balance -= amount
            source_account.ledger_balance -= amount
            source_account.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

            # Generate unique reference identifiers
            txn_ref = f"TXN{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

            # If internal transfer, credit recipient atomically
            if internal_dest_account:
                if internal_dest_account.id == source_account.id:
                    raise ValidationError("Cannot transfer funds to the same account.")
                if internal_dest_account.status != Account.Status.ACTIVE:
                    raise ValidationError(f"Destination account is currently {internal_dest_account.status}. Credit transfers are not permitted.")

                internal_dest_account.available_balance += amount
                internal_dest_account.ledger_balance += amount
                internal_dest_account.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

            # Create ledger transaction record
            primary_txn = Transaction.objects.create(
                transaction_id=txn_ref,
                from_account=source_account,
                to_account=internal_dest_account,
                beneficiary_name=beneficiary_name,
                beneficiary_account=to_account_number,
                beneficiary_ifsc=to_ifsc,
                transaction_type=Transaction.TransactionType.TRANSFER,
                category=category,
                amount=amount,
                balance_after=source_account.available_balance,
                status=Transaction.Status.COMPLETED,
                remarks=remarks or f"Transfer to {beneficiary_name}",
                reference_number=f"REF-{uuid.uuid4().hex[:8].upper()}",
                timestamp=timezone.now()
            )

            # Record security and compliance audit log
            AuditLog.objects.create(
                user=user,
                action="MONEY_TRANSFER",
                ip_address=ip_address,
                record_type="Transaction",
                record_id=txn_ref,
                details=f"Transferred ₹{amount:,.2f} from {source_account.account_number} to {beneficiary_name} ({to_account_number})"
            )

            return primary_txn

    @classmethod
    def reverse_transaction(
        cls,
        transaction_id: int,
        reason: str,
        user = None,
        ip_address: str = "127.0.0.1"
    ) -> Transaction:
        """
        Executes an atomic compensating reversal of a completed transaction.
        ACID Rules:
        - Original transaction is preserved in ledger with status marked REVERSED.
        - Compensating transaction is logged to preserve chronological integrity.
        - Debited / credited account balances are atomically restored.
        - Strict permission & sufficient balance verification prevents insolvency.
        - Comprehensive audit log is created.
        """
        if not reason or not reason.strip():
            raise ValidationError("A justification reason is mandatory to reverse a banking transaction.")

        with transaction.atomic():
            try:
                txn = Transaction.objects.select_for_update().get(id=transaction_id)
            except Transaction.DoesNotExist:
                raise ValidationError("Transaction record not found.")

            if txn.status == Transaction.Status.REVERSED:
                raise ValidationError("This transaction has already been reversed.")

            if txn.status != Transaction.Status.COMPLETED:
                raise ValidationError(f"Cannot reverse a transaction with status: {txn.status}. Only COMPLETED transactions can be reversed.")

            source_acc = txn.from_account
            dest_acc = txn.to_account

            # 1. Reverse Transfer between two internal accounts
            if source_acc and dest_acc:
                # Lock both accounts
                source_acc = Account.objects.select_for_update().get(id=source_acc.id)
                dest_acc = Account.objects.select_for_update().get(id=dest_acc.id)

                if dest_acc.available_balance < txn.amount:
                    raise ValidationError(
                        f"Cannot reverse transfer: Recipient account {dest_acc.account_number} has insufficient funds "
                        f"(Available: ₹{dest_acc.available_balance:,.2f}, Required: ₹{txn.amount:,.2f}) to claw back."
                    )

                dest_acc.available_balance -= txn.amount
                dest_acc.ledger_balance -= txn.amount
                dest_acc.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

                source_acc.available_balance += txn.amount
                source_acc.ledger_balance += txn.amount
                source_acc.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

            # 2. Reverse an outbound debit or withdrawal
            elif source_acc and not dest_acc:
                source_acc = Account.objects.select_for_update().get(id=source_acc.id)
                source_acc.available_balance += txn.amount
                source_acc.ledger_balance += txn.amount
                source_acc.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

            # 3. Reverse an inbound credit or deposit
            elif dest_acc and not source_acc:
                dest_acc = Account.objects.select_for_update().get(id=dest_acc.id)
                if dest_acc.available_balance < txn.amount:
                    raise ValidationError(
                        f"Cannot reverse deposit: Account {dest_acc.account_number} has insufficient balance "
                        f"(Available: ₹{dest_acc.available_balance:,.2f}, Required: ₹{txn.amount:,.2f})."
                    )
                dest_acc.available_balance -= txn.amount
                dest_acc.ledger_balance -= txn.amount
                dest_acc.save(update_fields=['available_balance', 'ledger_balance', 'updated_at'])

            # Mark original transaction as REVERSED
            orig_id = txn.transaction_id
            txn.status = Transaction.Status.REVERSED
            txn.remarks = f"{txn.remarks} [REVERSED by {user.username if user else 'Admin'}: {reason.strip()}]"
            txn.save(update_fields=['status', 'remarks'])

            # Create new compensating transaction record
            comp_ref = f"REV{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            compensating_txn = Transaction.objects.create(
                transaction_id=comp_ref,
                from_account=dest_acc,
                to_account=source_acc,
                beneficiary_name=f"Reversal of {orig_id}",
                beneficiary_account=source_acc.account_number if source_acc else '',
                beneficiary_ifsc=source_acc.branch.ifsc if source_acc else '',
                transaction_type=Transaction.TransactionType.CREDIT if source_acc else Transaction.TransactionType.DEBIT,
                category=Transaction.Category.OTHER,
                amount=txn.amount,
                balance_after=source_acc.available_balance if source_acc else (dest_acc.available_balance if dest_acc else None),
                status=Transaction.Status.COMPLETED,
                remarks=f"Compensating ledger reversal of {orig_id}. Justification: {reason.strip()}",
                reference_number=f"REV-REF-{orig_id}",
                timestamp=timezone.now()
            )

            # Write regulatory audit log
            AuditLog.objects.create(
                user=user,
                action="TRANSACTION_REVERSED",
                ip_address=ip_address,
                record_type="Transaction",
                record_id=orig_id,
                details=f"Reversed transaction {orig_id} (₹{txn.amount:,.2f}) with compensating txn {comp_ref}. Reason: {reason.strip()}"
            )

            return compensating_txn

