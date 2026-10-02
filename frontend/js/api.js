/**
 * Finova Silk & Glass - Centralized API Service Client
 * Connects Frontend UI to Django REST Framework Backend
 */

const API_BASE = '/api';

class ApiService {
    static getToken() {
        return localStorage.getItem('finova_auth_token') || '';
    }

    static setToken(token) {
        if (token) {
            localStorage.setItem('finova_auth_token', token);
        } else {
            localStorage.removeItem('finova_auth_token');
        }
    }

    static getHeaders(noAuth = false) {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };
        const token = this.getToken();
        if (token && !noAuth) {
            headers['Authorization'] = `Token ${token}`;
        }
        return headers;
    }

    static async request(endpoint, options = {}) {
        const isAuthEndpoint = endpoint.startsWith('/auth/login') || endpoint.startsWith('/auth/register');
        const noAuth = options.noAuth || isAuthEndpoint;

        const url = `${API_BASE}${endpoint}`;
        const headers = {
            ...this.getHeaders(noAuth),
            ...(options.headers || {})
        };
        if (noAuth) {
            delete headers['Authorization'];
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                // If 401 on an authenticated endpoint, clear stale/invalid token
                if (response.status === 401 && !isAuthEndpoint) {
                    this.setToken('');
                }

                let errorMsg = data.error || data.detail;
                if (!errorMsg && typeof data === 'object') {
                    const values = Object.values(data).flat();
                    if (values.length > 0 && typeof values[0] === 'string') {
                        errorMsg = values.join(' ');
                    } else {
                        errorMsg = JSON.stringify(data);
                    }
                }
                if (!errorMsg) errorMsg = 'API request failed';

                // User-friendly error messages matching Finova specifications
                if (response.status === 401) {
                    if (isAuthEndpoint) {
                        errorMsg = 'Invalid username or password.';
                    } else if (errorMsg === 'Invalid token.') {
                        errorMsg = 'Your session has expired. Please sign in again.';
                    }
                }

                const err = new Error(errorMsg);
                err.status = response.status;
                err.data = data;
                throw err;
            }
            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message && error.message.includes('fetch')) {
                const networkErr = new Error('Unable to connect to the Finova backend.');
                console.error(`Network Error [${endpoint}]:`, networkErr);
                throw networkErr;
            }
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // --- Authentication ---
    static async login(username, password) {
        this.setToken(''); // Reset any existing token before new login attempt
        const data = await this.request('/auth/login/', {
            method: 'POST',
            noAuth: true,
            body: JSON.stringify({ username, password })
        });
        if (data.token) {
            this.setToken(data.token);
        }
        return data;
    }

    static async logout() {
        try {
            await this.request('/auth/logout/', { method: 'POST' });
        } catch (e) {
            console.warn('Logout notification:', e);
        } finally {
            this.setToken('');
        }
    }

    static async getMe() {
        return await this.request('/auth/me/');
    }

    // --- Core Banking & Dashboard ---
    static async getDashboard() {
        return await this.request('/dashboard/');
    }

    static async getAccounts(params = {}) {
        const query = new URLSearchParams(params).toString();
        const endpoint = query ? `/accounts/?${query}` : '/accounts/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    static async freezeAccount(accountId, reason) {
        return await this.request(`/accounts/${accountId}/freeze/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    static async unfreezeAccount(accountId, reason = '') {
        return await this.request(`/accounts/${accountId}/unfreeze/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    static async activateAccount(accountId) {
        return await this.request(`/accounts/${accountId}/activate/`, {
            method: 'POST'
        });
    }

    static async deactivateAccount(accountId, reason) {
        return await this.request(`/accounts/${accountId}/deactivate/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    static async flagAccountReview(accountId, note) {
        return await this.request(`/accounts/${accountId}/flag_review/`, {
            method: 'POST',
            body: JSON.stringify({ note })
        });
    }

    static async getAccountSummary() {
        return await this.request('/accounts/summary/');
    }

    // --- Transactions & Transfers ---
    static async getTransactions(params = {}) {
        const cleanParams = {};
        for (const [k, v] of Object.entries(params)) {
            if (v !== '' && v !== null && v !== undefined && v !== 'ALL' && v !== 'All') {
                cleanParams[k] = v;
            }
        }
        const query = new URLSearchParams(cleanParams).toString();
        const endpoint = query ? `/transactions/?${query}` : '/transactions/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    static async reverseTransaction(transactionId, reason) {
        return await this.request(`/transactions/${transactionId}/reverse/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    static async executeTransfer(transferData) {
        return await this.request('/transfers/', {
            method: 'POST',
            body: JSON.stringify(transferData)
        });
    }

    static async getBeneficiaries() {
        const res = await this.request('/beneficiaries/');
        return res.results || res;
    }

    // --- Credit & Loans ---
    static async getLoans(params = {}) {
        const cleanParams = {};
        for (const [k, v] of Object.entries(params)) {
            if (v !== '' && v !== null && v !== undefined && v !== 'ALL') {
                cleanParams[k] = v;
            }
        }
        const query = new URLSearchParams(cleanParams).toString();
        const endpoint = query ? `/loans/?${query}` : '/loans/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    static async updateLoanStatus(loanId, status, reason) {
        return await this.request(`/loans/${loanId}/update_status/`, {
            method: 'POST',
            body: JSON.stringify({ status, reason })
        });
    }

    static async getLoanPayments(loanId) {
        const res = await this.request(`/loans/${loanId}/payments/`);
        return res.results || res;
    }

    static async getLoanTypes() {
        const res = await this.request('/loan-types/');
        return res.results || res;
    }

    static async getLoanAmortization(loanId) {
        return await this.request(`/loans/${loanId}/amortization/`);
    }

    static async calculateEMI(principal, annual_rate, tenure_months) {
        return await this.request('/loans/calculate-emi/', {
            method: 'POST',
            body: JSON.stringify({
                principal: principal.toString(),
                annual_rate: annual_rate.toString(),
                tenure_months: parseInt(tenure_months)
            })
        });
    }

    static async applyForLoan(applicationData) {
        return await this.request('/loan-applications/', {
            method: 'POST',
            body: JSON.stringify(applicationData)
        });
    }

    static async payEMI(loanId, accountId, amount) {
        return await this.request('/loans/pay-emi/', {
            method: 'POST',
            body: JSON.stringify({
                loan_id: loanId,
                account_id: accountId,
                amount: amount.toString()
            })
        });
    }

    // --- Staff Underwriting & Review ---
    static async getLoanApplications(params = {}) {
        const cleanParams = {};
        for (const [k, v] of Object.entries(params)) {
            if (v !== '' && v !== null && v !== undefined && v !== 'ALL') {
                cleanParams[k] = v;
            }
        }
        const query = new URLSearchParams(cleanParams).toString();
        const endpoint = query ? `/loan-applications/?${query}` : '/loan-applications/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    static async reviewLoanApplication(applicationId, decision, notes = '', sanctionAccountId = null) {
        return await this.request(`/loan-applications/${applicationId}/review/`, {
            method: 'POST',
            body: JSON.stringify({
                decision,
                notes,
                sanction_account_id: sanctionAccountId
            })
        });
    }

    static async getCustomers(search = '', kycStatus = '') {
        const params = {};
        if (search) params.search = search;
        if (kycStatus && kycStatus !== 'ALL') params.kyc_status = kycStatus;
        const query = new URLSearchParams(params).toString();
        const endpoint = query ? `/customers/?${query}` : '/customers/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    static async getCustomerDetail(customerId) {
        return await this.request(`/customers/${customerId}/`);
    }

    static async updateCustomerKYC(customerId, kycStatus, remarks = '') {
        return await this.request(`/customers/${customerId}/kyc/`, {
            method: 'PATCH',
            body: JSON.stringify({
                kyc_status: kycStatus,
                remarks
            })
        });
    }

    // --- Admin Oversight & Branches ---
    static async getAdminStats() {
        return await this.request('/admin/stats/');
    }

    static async getBranches(params = {}) {
        const cleanParams = {};
        for (const [k, v] of Object.entries(params)) {
            if (v !== '' && v !== null && v !== undefined && v !== 'ALL') {
                cleanParams[k] = v;
            }
        }
        const query = new URLSearchParams(cleanParams).toString();
        const endpoint = query ? `/branches/?${query}` : '/branches/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    static async toggleBranchStatus(branchId) {
        return await this.request(`/branches/${branchId}/toggle_status/`, {
            method: 'POST'
        });
    }

    static async createBranch(branchData) {
        return await this.request('/branches/', {
            method: 'POST',
            body: JSON.stringify(branchData)
        });
    }

    static async updateBranch(branchId, branchData) {
        return await this.request(`/branches/${branchId}/`, {
            method: 'PATCH',
            body: JSON.stringify(branchData)
        });
    }

    static async getAuditLogs(params = {}) {
        let query = '';
        if (typeof params === 'string') {
            query = params ? `action=${encodeURIComponent(params)}` : '';
        } else {
            const cleanParams = {};
            for (const [k, v] of Object.entries(params)) {
                if (v !== '' && v !== null && v !== undefined && v !== 'ALL') {
                    cleanParams[k] = v;
                }
            }
            query = new URLSearchParams(cleanParams).toString();
        }
        const endpoint = query ? `/audit-logs/?${query}` : '/audit-logs/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    // --- Notifications ---
    static async getNotifications() {
        const res = await this.request('/notifications/');
        return res.results || res;
    }

    static async markNotificationRead(id) {
        return await this.request(`/notifications/${id}/mark_read/`, {
            method: 'PATCH'
        });
    }

    // --- Cashflow & Trajectory Time-Series ---
    static async getCashflowChart(days = 30) {
        return await this.request(`/dashboard/cashflow-chart/?days=${days}`);
    }

    // --- Employee Portal Stats ---
    static async getEmployeeStats() {
        return await this.request('/employee/stats/');
    }

    // --- KYC Verification Queue ---
    static async getKYCRequests(params = {}) {
        const cleanParams = {};
        for (const [k, v] of Object.entries(params)) {
            if (v !== '' && v !== null && v !== undefined && v !== 'ALL') {
                cleanParams[k] = v;
            }
        }
        const query = new URLSearchParams(cleanParams).toString();
        const endpoint = query ? `/kyc-requests/?${query}` : '/kyc-requests/';
        const res = await this.request(endpoint);
        return res.results || res;
    }

    static async getKYCRequestDetail(id) {
        return await this.request(`/kyc-requests/${id}/`);
    }

    static async approveKYCRequest(id, notes = '') {
        return await this.request(`/kyc-requests/${id}/approve/`, {
            method: 'POST',
            body: JSON.stringify({ notes })
        });
    }

    static async rejectKYCRequest(id, reason) {
        return await this.request(`/kyc-requests/${id}/reject/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    static async needsReviewKYCRequest(id, notes) {
        return await this.request(`/kyc-requests/${id}/needs_review/`, {
            method: 'POST',
            body: JSON.stringify({ notes })
        });
    }

    static async assignKYCRequest(id, employeeId = null) {
        return await this.request(`/kyc-requests/${id}/assign/`, {
            method: 'POST',
            body: JSON.stringify(employeeId ? { employee_id: employeeId } : {})
        });
    }

    // --- Bank Employees ---
    static async getEmployees(search = '') {
        const endpoint = search ? `/employees/?search=${encodeURIComponent(search)}` : '/employees/';
        const res = await this.request(endpoint);
        return res.results || res;
    }
}

window.ApiService = ApiService;

