"""
Safe Development-Only Demo Reset Command for Finova Silk & Glass Banking System.
Restores the local database to the pristine presentation state for college DBMS demonstrations.
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.db import transaction

from apps.users.models import User, Customer, Employee, KYCRequest
from apps.branches.models import Branch
from apps.accounts.models import AccountType, Account
from apps.transactions.models import Transaction, Beneficiary
from apps.loans.models import LoanType, Loan, LoanApplication, LoanPayment
from apps.notifications.models import Notification
from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = (
        "SAFE DEVELOPMENT-ONLY: Restores the fictional demo database to its original "
        "presentation state for live demonstration and evaluation."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for confirmation before resetting local demo data.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bypass safety engine check (for automated test environments).',
        )

    def handle(self, *args, **options):
        # 1. Environment Safety Verification
        if not settings.DEBUG:
            raise CommandError(
                "SAFETY ABORT: Cannot run reset_demo_data when DEBUG=False. "
                "This command is strictly restricted to local development and academic demo environments."
            )

        db_engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
        is_sqlite = 'sqlite' in db_engine.lower()
        if not is_sqlite and not options.get('force'):
            raise CommandError(
                f"SAFETY ABORT: Default database engine is '{db_engine}', not SQLite. "
                "Refusing to execute reset_demo_data against external/production database without --force."
            )

        # 2. Interactive Confirmation Prompt (if interactive)
        if not options.get('no_input') and not options.get('force'):
            self.stdout.write(self.style.WARNING(
                "\n=======================================================\n"
                " FINOVA DEMO DATA RESET — ACADEMIC SIMULATION SYSTEM\n"
                "=======================================================\n"
                "This will reset all local demo transactions, loans, accounts,\n"
                "and notifications to their initial presentation state.\n"
                "NO real money or external banking data is involved.\n"
                "All 5 demo customers, 2 employees, and admin will be restored.\n"
            ))
            confirm = input("Are you sure you want to restore the clean demo state? [y/N]: ").strip().lower()
            if confirm not in ['y', 'yes']:
                self.stdout.write(self.style.NOTICE("Reset aborted by user."))
                return

        self.stdout.write(self.style.NOTICE("Beginning atomic demo data restoration..."))

        # 3. Atomic Reset & Re-seeding
        with transaction.atomic():
            # Delete dependent transaction and loan activity
            LoanPayment.objects.all().delete()
            Transaction.objects.all().delete()
            Loan.objects.all().delete()
            LoanApplication.objects.all().delete()
            KYCRequest.objects.all().delete()
            Notification.objects.all().delete()
            Beneficiary.objects.all().delete()
            AuditLog.objects.all().delete()

            # Delete accounts and customer/employee profiles
            Account.objects.all().delete()
            Customer.objects.all().delete()
            Employee.objects.all().delete()

            # Delete demo user accounts
            demo_usernames = [
                'sophia', 'rohan', 'aarav', 'priya', 'vikram',
                'employee', 'employee2', 'admin',
                'sender', 'recipient', 'borrower', 'officer'
            ]
            User.objects.filter(username__in=demo_usernames).delete()

            self.stdout.write(self.style.SUCCESS("[CLEAN] Temporary simulation state cleared."))

            # Re-run the authoritative base seed command
            call_command('seed_demo_data')

            # Re-run the expansion seed command (5 customers, 2 employees, KYC queue)
            call_command('seed_expansion_demo_data')

        self.stdout.write(self.style.SUCCESS(
            "\n[SUCCESS] Finova demo database successfully restored to original presentation state!\n"
            "Demo personas ready:\n"
            "  - Customer 1: sophia     / Finova@2024 (Balance: INR 1,28,450.80, Home Loan #HL-4091)\n"
            "  - Customer 2: rohan      / Finova@2024 (Balance: INR 35,000.00, Pending Loan LA-2024-9182)\n"
            "  - Customer 3: aarav      / Finova@2024 (Balance: INR 1,95,400.00, Active Loan LN-PL-331902)\n"
            "  - Customer 4: priya      / Finova@2024 (Balance: INR 64,250.00, Home Loan App LA-2024-5528)\n"
            "  - Customer 5: vikram     / Finova@2024 (Balance: INR 88,700.00, Current Account Trade Txns)\n"
            "  - Employee 1: employee   / Finova@2024 (Senior Credit Underwriter & KYC Officer)\n"
            "  - Employee 2: employee2  / Finova@2024 (KYC & Operations Officer)\n"
            "  - Admin:      admin      / FinovaAdmin@2024 (Executive DBMS Management & Audit Trail)\n"
        ))
