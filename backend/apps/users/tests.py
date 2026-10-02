from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User, Customer
from apps.branches.models import Branch
from apps.accounts.models import Account, AccountType
from apps.loans.models import LoanType, Loan

class APIEndpointsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.branch = Branch.objects.create(
            branch_code="BLR01",
            branch_name="Bengaluru Indiranagar",
            ifsc="FINO0001234",
            address="100ft Road",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            manager_name="Vikram Sengupta"
        )
        self.acc_type = AccountType.objects.create(
            code="SAVINGS",
            name="Primary Savings",
            interest_rate_pa=Decimal("4.00")
        )
        self.user = User.objects.create_user(
            username="test_sophia",
            email="sophia@example.com",
            password="Finova@2024",
            role=User.Role.CUSTOMER
        )
        self.customer = Customer.objects.create(
            user=self.user,
            customer_id="CUST-482109",
            full_name="Sophia Mehta",
            pan_number="ABCPM1234F",
            aadhaar_last_four="4821",
            phone="9845012345",
            address="Koramangala",
            city="Bengaluru",
            state="Karnataka",
            pincode="560034",
            monthly_income=Decimal("145000.00"),
            credit_score=785,
            credit_category="Excellent"
        )
        self.account = Account.objects.create(
            account_number="482190824821",
            customer=self.customer,
            branch=self.branch,
            account_type=self.acc_type,
            available_balance=Decimal("42650.30"),
            ledger_balance=Decimal("43100.00"),
            is_primary=True
        )

    def test_auth_login(self):
        url = reverse('auth-login')
        response = self.client.post(url, {'username': 'test_sophia', 'password': 'Finova@2024'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'test_sophia')

    def test_customer_dashboard_api(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['balance']['total_available'])), Decimal("42650.30"))
        self.assertEqual(response.data['customer']['name'], "Sophia Mehta")
        self.assertEqual(response.data['customer']['credit_score'], 785)

    def test_calculate_emi_api(self):
        url = reverse('calculate-emi')
        payload = {
            'principal': '1000000.00',
            'annual_rate': '8.25',
            'tenure_months': 120
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('monthly_emi', response.data)
        self.assertIn('total_payable', response.data)
        self.assertIn('sample_schedule', response.data)

    def test_auth_login_with_stale_token_header_succeeds(self):
        """Simulate client with stale or invalid token header logging in."""
        url = reverse('auth-login')
        self.client.credentials(HTTP_AUTHORIZATION='Token stale_or_invalid_token_12345')
        response = self.client.post(url, {'username': 'test_sophia', 'password': 'Finova@2024'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'test_sophia')

    def test_auth_register_with_stale_token_header_succeeds(self):
        """Simulate client with stale token registering a new account."""
        url = reverse('auth-register')
        self.client.credentials(HTTP_AUTHORIZATION='Token stale_or_invalid_token_12345')
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Finova@2024',
            'full_name': 'New Customer',
            'phone': '9876543210',
            'pan_number': 'ABCDE1234F',
            'address': '123 Main St',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560001'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)


    def test_calculate_emi_with_stale_token_succeeds(self):
        """Public endpoint must allow calculation even if stale token is sent in header."""
        url = reverse('calculate-emi')
        self.client.credentials(HTTP_AUTHORIZATION='Token stale_or_invalid_token_12345')
        payload = {
            'principal': '1000000.00',
            'annual_rate': '8.25',
            'tenure_months': 120
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

