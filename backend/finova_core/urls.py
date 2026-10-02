"""
URL Configuration for Finova Silk & Glass Banking and Loan Management System.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    RegisterView, LoginView, LogoutView, MeView,
    CustomerListView, CustomerDetailView, CustomerKYCUpdateView,
    KYCRequestViewSet, EmployeeViewSet
)
from apps.users.dashboard_views import (
    DashboardView, AdminStatsView, CashflowChartView, EmployeeStatsView
)
from apps.branches.views import BranchViewSet
from apps.accounts.views import AccountViewSet, AccountTypeListView
from apps.transactions.views import (
    TransactionViewSet, TransferExecuteView, BeneficiaryViewSet
)
from apps.loans.views import (
    LoanViewSet, LoanTypeViewSet, LoanApplicationViewSet,
    LoanReviewView, EMICalculatorView, PayEMIView
)
from apps.notifications.views import NotificationViewSet
from apps.audit.views import AuditLogViewSet

# API Router
router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'beneficiaries', BeneficiaryViewSet, basename='beneficiary')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'loan-types', LoanTypeViewSet, basename='loan-type')
router.register(r'loan-applications', LoanApplicationViewSet, basename='loan-application')
router.register(r'kyc-requests', KYCRequestViewSet, basename='kyc-request')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication Endpoints
    path('api/auth/register/', RegisterView.as_view(), name='auth-register'),
    path('api/auth/login/', LoginView.as_view(), name='auth-login'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/me/', MeView.as_view(), name='auth-me'),

    # Core Banking Endpoints
    path('api/dashboard/', DashboardView.as_view(), name='dashboard-summary'),
    path('api/dashboard/cashflow-chart/', CashflowChartView.as_view(), name='dashboard-cashflow-chart'),
    path('api/account-types/', AccountTypeListView.as_view(), name='account-types'),
    path('api/transfers/', TransferExecuteView.as_view(), name='execute-transfer'),

    # Credit & Loan Endpoints
    path('api/loans/calculate-emi/', EMICalculatorView.as_view(), name='calculate-emi'),
    path('api/loans/pay-emi/', PayEMIView.as_view(), name='pay-emi'),
    path('api/loan-applications/<int:pk>/review/', LoanReviewView.as_view(), name='loan-review'),

    # Customer & KYC Underwriting (Employee / Admin)
    path('api/customers/', CustomerListView.as_view(), name='customer-list'),
    path('api/customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('api/customers/<int:pk>/kyc/', CustomerKYCUpdateView.as_view(), name='customer-kyc-update'),

    # Staff & Admin Management
    path('api/employee/stats/', EmployeeStatsView.as_view(), name='employee-stats'),
    path('api/admin/stats/', AdminStatsView.as_view(), name='admin-stats'),

    # Router generated CRUD API endpoints
    path('api/', include(router.urls)),

    # Frontend Single Page App
    path('', TemplateView.as_view(template_name='index.html'), name='frontend-home'),
]
