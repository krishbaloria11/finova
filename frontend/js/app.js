/**
 * Finova Silk & Glass - Client-Side Controller & API Integration Engine
 * Connects frontend views to Django REST Framework backend services.
 */

// Global State
let currentRole = 'CUSTOMER';
let currentUser = null;
let currentAccounts = [];
let currentLoan = null;
let currentTransactions = [];
let baselineCashflow = { income: 148420.50, expenses: 31239.00, net_savings: 117181.50 };

// Demo credentials for seamless multi-persona switching (5 Customers, 2 Employees, 1 Admin)
const DEMO_PERSONAS = {
    sophia: { username: 'sophia', password: 'Finova@2024', role: 'CUSTOMER', name: 'Sophia Mehta', sub: 'Premier · ₹1.28L' },
    rohan: { username: 'rohan', password: 'Finova@2024', role: 'CUSTOMER', name: 'Rohan Deshmukh', sub: 'Retail · ₹35.1K' },
    aarav: { username: 'aarav', password: 'Finova@2024', role: 'CUSTOMER', name: 'Aarav Sharma', sub: 'Premier · ₹2.40L' },
    priya: { username: 'priya', password: 'Finova@2024', role: 'CUSTOMER', name: 'Priya Patel', sub: 'Healthcare · ₹64.2K' },
    vikram: { username: 'vikram', password: 'Finova@2024', role: 'CUSTOMER', name: 'Vikram Malhotra', sub: 'Commercial · ₹1.04L' },
    employee: { username: 'employee', password: 'Finova@2024', role: 'EMPLOYEE', name: 'Ramesh Iyer', sub: 'Sr. Underwriter · BLR' },
    employee2: { username: 'employee2', password: 'Finova@2024', role: 'EMPLOYEE', name: 'Ananya Rao', sub: 'KYC Officer · MUM' },
    admin: { username: 'admin', password: 'FinovaAdmin@2024', role: 'ADMIN', name: 'System Admin', sub: 'DBMS Management & Audit' }
};
DEMO_PERSONAS.CUSTOMER = DEMO_PERSONAS.sophia;
DEMO_PERSONAS.EMPLOYEE = DEMO_PERSONAS.employee;
DEMO_PERSONAS.ADMIN = DEMO_PERSONAS.admin;
const CREDENTIALS = DEMO_PERSONAS;


document.addEventListener('DOMContentLoaded', async () => {
    initNavigation();
    initQuickActions();
    initCashflowFilters();
    initTransactionFilters();
    initEMICalculator();
    initLoanApplicationWizard();
    initTransferWorkflow();
    initPayEMIWorkflow();
    initNotificationsCenter();
    initRoleSwitcher();
    initAuth();
    initEmployeePortal();
    initAdminPortal();

    // Verify existing token or present clean login modal
    const token = ApiService.getToken();
    if (token) {
        try {
            const meData = await ApiService.getMe();
            currentUser = meData.user;
            currentRole = meData.user.role || 'CUSTOMER';
            const roleSelect = document.getElementById('demo-role-selector');
            if (roleSelect) roleSelect.value = currentRole;
            hideLoginModal();
            await applyRoleSession(currentRole, meData.user);
        } catch (err) {
            console.warn('Session verification notice (clearing stale token):', err);
            ApiService.setToken('');
            currentUser = null;
            showLoginModal('CUSTOMER');
        }
    } else {
        showLoginModal('CUSTOMER');
    }
});

/**
 * Currency Formatter (Indian Rupee Format)
 */
function formatINR(val, includeDecimals = true) {
    const num = parseFloat(val) || 0;
    return '₹' + num.toLocaleString('en-IN', {
        minimumFractionDigits: includeDecimals ? 2 : 0,
        maximumFractionDigits: includeDecimals ? 2 : 0
    });
}

function formatDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatShortDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
}

/**
 * Authentication, Login Modal & Sign Out Controls
 */
function initAuth() {
    const loginForm = document.getElementById('form-auth-login');
    const btnSidebarSignout = document.getElementById('btn-sidebar-signout');
    const btnProfileSignout = document.getElementById('btn-profile-signout');

    // 1. Category Switcher (Customers (5) / Staff (2) / Admin (1))
    const catButtons = document.querySelectorAll('.persona-cat-btn');
    catButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const cat = btn.getAttribute('data-cat');
            catButtons.forEach(b => {
                b.classList.remove('bg-surface-container-lowest', 'text-primary-container', 'shadow-xs');
                b.classList.add('text-outline');
            });
            btn.classList.add('bg-surface-container-lowest', 'text-primary-container', 'shadow-xs');
            btn.classList.remove('text-outline');

            const custGrid = document.getElementById('persona-grid-customers');
            const empGrid = document.getElementById('persona-grid-employees');
            const admGrid = document.getElementById('persona-grid-admin');

            if (custGrid) custGrid.classList.toggle('hidden', cat !== 'customers');
            if (empGrid) empGrid.classList.toggle('hidden', cat !== 'employees');
            if (admGrid) admGrid.classList.toggle('hidden', cat !== 'admin');
        });
    });

    // 2. Quick Persona Cards Click (All 8 demo accounts)
    const personaButtons = document.querySelectorAll('.btn-quick-login-persona, .btn-quick-login-role');
    personaButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const username = btn.getAttribute('data-username') || (btn.getAttribute('data-role') ? (CREDENTIALS[btn.getAttribute('data-role')]?.username) : '');
            const password = btn.getAttribute('data-password') || (btn.getAttribute('data-role') ? (CREDENTIALS[btn.getAttribute('data-role')]?.password) : '');

            const uInput = document.getElementById('login-username');
            const pInput = document.getElementById('login-password');
            if (uInput && username) uInput.value = username;
            if (pInput && password) pInput.value = password;

            // Highlight active persona card
            personaButtons.forEach(b => {
                b.classList.remove('border-primary', 'border-primary/50', 'bg-primary/5');
                b.classList.add('border-outline-variant/30');
            });
            btn.classList.add('border-primary/50', 'bg-primary/5');
            btn.classList.remove('border-outline-variant/30');

            const errorBox = document.getElementById('login-error-container');
            if (errorBox) errorBox.classList.add('hidden');
        });
    });

    // 3. Login Form Submit
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('login-username');
            const passwordInput = document.getElementById('login-password');
            const submitBtn = document.getElementById('btn-login-submit');
            const errorBox = document.getElementById('login-error-container');
            const errorText = document.getElementById('login-error-text');

            const username = usernameInput ? usernameInput.value.trim() : '';
            const password = passwordInput ? passwordInput.value : '';

            if (!username || !password) return;

            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span>Signing in...</span>`;
            if (errorBox) errorBox.classList.add('hidden');

            try {
                const authData = await ApiService.login(username, password);
                currentUser = authData.user;
                currentRole = authData.user.role || 'CUSTOMER';

                // Sync header role selector dropdown
                const roleSelect = document.getElementById('demo-role-selector');
                if (roleSelect && roleSelect.querySelector(`option[value="${currentUser.username}"]`)) {
                    roleSelect.value = currentUser.username;
                }

                hideLoginModal();
                await applyRoleSession(currentRole, authData.user);
            } catch (err) {
                if (errorBox && errorText) {
                    errorText.textContent = err.message || 'Invalid username or password.';
                    errorBox.classList.remove('hidden');
                } else {
                    alert(`Login Failed: ${err.message}`);
                }
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `<span>Sign In to Finova</span><span class="material-symbols-outlined text-[18px]">arrow_forward</span>`;
            }
        });
    }

    // Sidebar & Profile Sign Out Buttons
    if (btnSidebarSignout) {
        btnSidebarSignout.addEventListener('click', handleLogout);
    }
    if (btnProfileSignout) {
        btnProfileSignout.addEventListener('click', handleLogout);
    }
}

function fillLoginCredentials(key) {
    const creds = DEMO_PERSONAS[key] || CREDENTIALS[key];
    if (!creds) return;
    const uInput = document.getElementById('login-username');
    const pInput = document.getElementById('login-password');
    if (uInput) uInput.value = creds.username;
    if (pInput) pInput.value = creds.password;

    // Highlight matching persona button
    const personaButtons = document.querySelectorAll('.btn-quick-login-persona');
    personaButtons.forEach(btn => {
        if (btn.getAttribute('data-username') === creds.username) {
            btn.classList.add('border-primary/50', 'bg-primary/5');
            btn.classList.remove('border-outline-variant/30');
        } else {
            btn.classList.remove('border-primary/50', 'bg-primary/5');
            btn.classList.add('border-outline-variant/30');
        }
    });
}

function showLoginModal(defaultRole = 'CUSTOMER') {
    const modal = document.getElementById('modal-auth-login');
    const errorBox = document.getElementById('login-error-container');
    if (errorBox) errorBox.classList.add('hidden');
    if (modal) {
        modal.classList.remove('hidden');
        fillLoginCredentials(defaultRole);
    }
}

function hideLoginModal() {
    const modal = document.getElementById('modal-auth-login');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function handleLogout() {
    try {
        await ApiService.logout();
    } catch (e) {
        console.warn('Logout notice:', e);
    } finally {
        ApiService.setToken('');
        currentUser = null;
        currentAccounts = [];
        currentLoan = null;

        // Reset sidebar user details
        const sidebarUser = document.getElementById('sidebar-user-name');
        const userLabel = document.getElementById('header-user-name');
        const userSub = document.getElementById('header-user-sub');
        if (sidebarUser) sidebarUser.textContent = 'Guest';
        if (userLabel) userLabel.textContent = 'Guest';
        if (userSub) userSub.textContent = 'Not Signed In';

        showLoginModal('CUSTOMER');
    }
}

/**
 * Role Switcher & Persona Authentication
 */
function initRoleSwitcher() {
    const roleSelect = document.getElementById('demo-role-selector');
    if (!roleSelect) return;

    roleSelect.addEventListener('change', async () => {
        const selectedRole = roleSelect.value;
        await switchRole(selectedRole);
    });
}

async function switchRole(roleOrUser) {
    const creds = DEMO_PERSONAS[roleOrUser] || CREDENTIALS[roleOrUser];
    if (!creds) return;

    try {
        const authData = await ApiService.login(creds.username, creds.password);
        currentUser = authData.user;
        currentRole = authData.user.role || creds.role;
        const roleSelect = document.getElementById('demo-role-selector');
        if (roleSelect && roleSelect.querySelector(`option[value="${creds.username}"]`)) {
            roleSelect.value = creds.username;
        }
        hideLoginModal();
        await applyRoleSession(currentRole, authData.user, creds);
    } catch (err) {
        console.error('Role authentication error:', err);
        showLoginModal(roleOrUser);
        const errorBox = document.getElementById('login-error-container');
        const errorText = document.getElementById('login-error-text');
        if (errorBox && errorText) {
            errorText.textContent = err.message || 'Invalid username or password.';
            errorBox.classList.remove('hidden');
        }
    }
}

async function applyRoleSession(role, user, persona = null) {
    const creds = persona || DEMO_PERSONAS[user.username] || DEMO_PERSONAS[role] || { name: user.username, sub: role };

    // Update UI Nav visibility & user labels
    const customerNav = document.getElementById('nav-customer-group');
    const employeeNav = document.getElementById('nav-employee-group');
    const adminNav = document.getElementById('nav-admin-group');
    const userLabel = document.getElementById('header-user-name');
    const userSub = document.getElementById('header-user-sub');
    const sidebarUser = document.getElementById('sidebar-user-name');

    const displayName = (user.first_name && user.last_name) ? `${user.first_name} ${user.last_name}` : (creds.name || user.username);
    const displaySub = creds.sub || (role === 'CUSTOMER' ? 'Retail Banking' : role);

    if (userLabel) userLabel.textContent = displayName;
    if (userSub) userSub.textContent = displaySub;
    if (sidebarUser) sidebarUser.textContent = displayName;

    const roleSelect = document.getElementById('demo-role-selector');
    if (roleSelect && roleSelect.querySelector(`option[value="${user.username}"]`)) {
        roleSelect.value = user.username;
    }

    if (role === 'CUSTOMER') {
        if (customerNav) customerNav.classList.remove('hidden');
        if (employeeNav) employeeNav.classList.add('hidden');
        if (adminNav) adminNav.classList.add('hidden');
        navigateTo('dashboard');
        await loadCustomerDashboard();
        await loadAccounts();
        await loadTransactions();
        await loadNotifications();
        await loadLoansOverview();
    } else if (role === 'EMPLOYEE') {
        if (customerNav) customerNav.classList.add('hidden');
        if (employeeNav) employeeNav.classList.remove('hidden');
        if (adminNav) adminNav.classList.add('hidden');
        navigateTo('employee-portal');
        await switchEmployeeTab('loans');
    } else if (role === 'ADMIN') {
        if (customerNav) customerNav.classList.add('hidden');
        if (employeeNav) employeeNav.classList.add('hidden');
        if (adminNav) adminNav.classList.remove('hidden');
        navigateTo('admin-portal');
        await switchAdminTab('metrics');
    }
}

/**
 * Load Customer Dashboard Live Data
 */
async function loadCustomerDashboard() {
    try {
        const data = await ApiService.getDashboard();
        if (data.is_staff) return;

        // 1. Editorial Header & Total Balance
        const greetingEl = document.getElementById('dashboard-user-greeting');
        const totalBalEl = document.getElementById('dashboard-total-balance');
        const growthEl = document.getElementById('dashboard-balance-growth');
        const captionEl = document.getElementById('dashboard-accounts-caption');

        if (greetingEl && data.customer) {
            greetingEl.textContent = `Good morning, ${data.customer.name.split(' ')[0]}`;
        }
        if (totalBalEl && data.balance) {
            totalBalEl.textContent = formatINR(data.balance.total_available);
        }
        if (growthEl && data.balance) {
            growthEl.innerHTML = `
                <span class="material-symbols-outlined text-[16px]">trending_up</span>
                <span>${data.balance.growth_this_month}</span>
            `;
        }
        if (captionEl && data.balance) {
            captionEl.textContent = `Across ${data.balance.account_count} accounts · Salary deposit expected ${data.balance.salary_expected_date}`;
        }

        // 2. Upcoming Payment Banner
        const alertBanner = document.getElementById('dashboard-alert-banner');
        const alertTitle = document.getElementById('dashboard-alert-title');
        const alertAmount = document.getElementById('dashboard-alert-amount');
        const alertText = document.getElementById('dashboard-alert-text');

        if (alertBanner && data.upcoming_payment) {
            if (data.upcoming_payment.has_payment) {
                alertBanner.classList.remove('hidden');
                if (alertTitle) alertTitle.textContent = `Payment Due in ${data.upcoming_payment.due_in_days} Days`;
                if (alertAmount) alertAmount.textContent = formatINR(data.upcoming_payment.amount);
                if (alertText) {
                    alertText.innerHTML = `Home Loan EMI auto-debit from <strong>${data.upcoming_payment.debit_from}</strong> on ${data.upcoming_payment.due_date}.`;
                }
            } else {
                alertBanner.classList.add('hidden');
            }
        }

        // 3. Credit Score Strip & Profile Details
        const creditScoreEl = document.getElementById('dashboard-credit-score');
        const creditCatEl = document.getElementById('dashboard-credit-category');
        const creditDateEl = document.getElementById('dashboard-credit-date');
        const loCibilScore = document.getElementById('loans-overview-cibil-score');
        const loCibilCat = document.getElementById('loans-overview-cibil-cat');
        const loCibilDate = document.getElementById('loans-overview-cibil-date');

        if (data.customer) {
            if (creditScoreEl) creditScoreEl.textContent = `Credit Score: ${data.customer.credit_score} / 900`;
            if (creditCatEl) creditCatEl.textContent = data.customer.credit_category;
            if (creditDateEl) creditDateEl.textContent = `CIBIL model · Updated ${data.customer.credit_updated}`;

            if (loCibilScore) loCibilScore.textContent = data.customer.credit_score;
            if (loCibilCat) loCibilCat.textContent = `${data.customer.credit_category} Standing`;
            if (loCibilDate) loCibilDate.textContent = `Updated: ${data.customer.credit_updated}, 2024`;

            // Update Profile View
            const profileName = document.getElementById('profile-name');
            const profileBadge = document.getElementById('profile-kyc-badge');
            const profileCif = document.getElementById('profile-cif');
            const profilePan = document.getElementById('profile-pan');
            const profileAadhaar = document.getElementById('profile-aadhaar');
            const profileMobile = document.getElementById('profile-mobile');
            const profileAddress = document.getElementById('profile-address');

            if (profileName) profileName.textContent = data.customer.name;
            if (profileBadge) profileBadge.textContent = `KYC ${data.customer.kyc_status}`;
            if (profileCif) profileCif.textContent = `Customer ID: ${data.customer.id} · Finova Premier Client`;
            if (profilePan && data.customer.pan_number) profilePan.textContent = data.customer.pan_number;
            if (profileAadhaar && data.customer.aadhaar_last_four) profileAadhaar.textContent = `•••• •••• ${data.customer.aadhaar_last_four}`;
            if (profileMobile && data.customer.phone) profileMobile.textContent = data.customer.phone;
            if (profileAddress && data.customer.address) {
                profileAddress.textContent = `${data.customer.address}, ${data.customer.city}, ${data.customer.state} - ${data.customer.pincode}`;
            }
        }

        // 4. Primary Account Frosted Glass Card
        if (data.primary_account) {
            const acc = data.primary_account;
            const badgeEl = document.getElementById('primary-acc-badge');
            const titleEl = document.getElementById('primary-acc-title');
            const schemeEl = document.getElementById('primary-acc-scheme');
            const availEl = document.getElementById('primary-acc-available');
            const ledgEl = document.getElementById('primary-acc-ledger');
            const ifscEl = document.getElementById('primary-acc-ifsc');

            if (badgeEl) badgeEl.textContent = acc.status === 'ACTIVE' ? 'Active' : acc.status;
            if (titleEl) titleEl.textContent = `${acc.account_type_name} •••• ${acc.account_number.slice(-4)}`;
            if (schemeEl) schemeEl.textContent = 'RuPay Platinum';
            if (availEl) availEl.textContent = formatINR(acc.available_balance);
            if (ledgEl) ledgEl.textContent = formatINR(acc.ledger_balance);
            if (ifscEl) ifscEl.textContent = acc.ifsc_code;
        }

        // 5. Other Accounts Flat List
        const otherContainer = document.getElementById('dashboard-other-accounts-container');
        if (otherContainer) {
            otherContainer.innerHTML = '';
            if (data.other_accounts && data.other_accounts.length > 0) {
                data.other_accounts.forEach(acc => {
                    const icon = acc.account_type_code === 'CURRENT' ? 'store' : 'savings';
                    const iconColor = acc.account_type_code === 'CURRENT' ? 'text-primary-container bg-primary-container/10' : 'text-secondary bg-secondary/10';
                    const desc = acc.account_type_code === 'CURRENT'
                        ? 'Business Current Facility · Zero balance penalty exempt'
                        : '4.50% p.a. interest · High-yield savings deposit';

                    const row = document.createElement('div');
                    row.className = 'group flex items-center justify-between p-4 rounded-xl bg-surface-container-lowest border border-outline-variant/20 hover:bg-surface-container-low transition-colors cursor-pointer';
                    row.onclick = () => navigateTo('accounts');
                    row.innerHTML = `
                        <div class="flex items-center gap-3.5 min-w-0">
                            <div class="w-10 h-10 rounded-xl ${iconColor} flex items-center justify-center shrink-0">
                                <span class="material-symbols-outlined text-[22px]">${icon}</span>
                            </div>
                            <div class="min-w-0 flex flex-col">
                                <div class="flex items-center gap-2">
                                    <span class="font-headline-sm text-headline-sm font-semibold text-on-surface truncate">${acc.account_type_name}</span>
                                    <span class="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-medium">•••• ${acc.account_number.slice(-4)}</span>
                                </div>
                                <p class="font-body-sm text-body-sm text-outline truncate">${desc}</p>
                            </div>
                        </div>
                        <div class="flex flex-col text-right shrink-0 pl-4">
                            <span class="font-headline-sm text-headline-sm font-bold text-on-surface">${formatINR(acc.available_balance)}</span>
                            <span class="font-label-sm text-label-sm text-secondary font-medium">Active facility</span>
                        </div>
                    `;
                    otherContainer.appendChild(row);
                });
            } else {
                otherContainer.innerHTML = `<div class="p-4 text-center text-outline font-label-sm rounded-xl bg-surface-container-lowest border border-outline-variant/20">No secondary accounts linked.</div>`;
            }
        }

        // 6. Dynamic Cashflow Time-Series Chart & Figures (Sections 5, 6 & 7)
        await loadCashflowChart(30);

        // 7. Active Loan Facility Card
        const loanCard = document.getElementById('dashboard-loan-card');
        if (data.loan_facility) {
            currentLoan = data.loan_facility;
            const loan = data.loan_facility;
            const lTitle = document.getElementById('dashboard-loan-title');
            const lSub = document.getElementById('dashboard-loan-sub');
            const lOut = document.getElementById('dashboard-loan-outstanding');
            const lProg = document.getElementById('dashboard-loan-progressbar');
            const lProgText = document.getElementById('dashboard-loan-progress-text');
            const lPrinText = document.getElementById('dashboard-loan-principal-text');
            const lEmi = document.getElementById('dashboard-loan-emi');
            const lDue = document.getElementById('dashboard-loan-duedate');

            const repaidPct = loan.principal_amount > 0
                ? Math.min(100, Math.round(((loan.principal_amount - loan.outstanding_amount) / loan.principal_amount) * 100))
                : 50;
            const repaidAmt = loan.principal_amount - loan.outstanding_amount;

            if (lTitle) lTitle.textContent = `${loan.loan_type_name} #${loan.loan_id}`;
            if (lSub) lSub.textContent = `Fixed ${loan.interest_rate}% p.a. · ${Math.round(loan.tenure_months / 12)}-Yr Floating Tenure`;
            if (lOut) lOut.textContent = formatINR(loan.outstanding_amount, false);
            if (lProg) lProg.style.width = `${repaidPct}%`;
            if (lProgText) lProgText.textContent = `Repaid ${formatINR(repaidAmt, false)} (${repaidPct}%)`;
            if (lPrinText) lPrinText.textContent = `Principal ${formatINR(loan.principal_amount, false)}`;
            if (lEmi) lEmi.textContent = `${formatINR(loan.monthly_emi, false)}/mo`;
            if (lDue) lDue.textContent = formatDate(loan.next_due_date);

            // Update Pay EMI View
            const peTitle = document.getElementById('pay-emi-title');
            const peSub = document.getElementById('pay-emi-sub');
            const peAmount = document.getElementById('pay-emi-display-amount');
            if (peTitle) peTitle.textContent = 'Upcoming EMI Payment';
            if (peSub) peSub.textContent = `${loan.loan_type_name} #${loan.loan_id} · Due ${formatDate(loan.next_due_date)}`;
            if (peAmount) peAmount.textContent = formatINR(loan.monthly_emi, false);
        } else {
            currentLoan = null;
            if (loanCard) {
                loanCard.innerHTML = `
                    <div class="flex items-start justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-primary-container/10 text-primary-container flex items-center justify-center">
                          <span class="material-symbols-outlined text-[20px]">credit_score</span>
                        </div>
                        <div>
                          <h4 class="font-label-md text-label-md font-semibold text-on-surface">No Active Loan Facilities</h4>
                          <p class="font-label-sm text-label-sm text-outline">Pre-approved credit line available</p>
                        </div>
                      </div>
                      <span class="px-2.5 py-0.5 rounded-full bg-secondary/10 text-secondary font-label-sm font-semibold">Eligible</span>
                    </div>
                    <p class="font-body-sm text-body-sm text-outline">You currently have no active debt or pending EMI liabilities. Apply for competitive retail credit instantly.</p>
                    <div class="pt-1">
                      <button type="button" class="w-full py-2.5 rounded-xl bg-primary-container text-white font-label-sm font-semibold hover:bg-primary transition-colors flex items-center justify-center gap-1.5" onclick="navigateTo('apply-for-credit')">
                        <span class="material-symbols-outlined text-[18px]">add_card</span>
                        <span>Apply for Credit Facility</span>
                      </button>
                    </div>
                `;
            }

            // Pay EMI empty notice
            const peTitle = document.getElementById('pay-emi-title');
            const peSub = document.getElementById('pay-emi-sub');
            const peAmount = document.getElementById('pay-emi-display-amount');
            if (peTitle) peTitle.textContent = 'No Outstanding EMI';
            if (peSub) peSub.textContent = 'You have zero active loan repayment obligations.';
            if (peAmount) peAmount.textContent = '₹0.00';
        }

        // 8. Frequent Payees Shortcuts
        const payeesContainer = document.getElementById('dashboard-frequent-payees-container');
        if (payeesContainer && data.frequent_payees && data.frequent_payees.length > 0) {
            payeesContainer.innerHTML = '';
            data.frequent_payees.forEach(p => {
                const btn = document.createElement('button');
                btn.className = 'group flex flex-col items-center gap-1.5 focus:outline-none';
                btn.type = 'button';
                btn.onclick = () => {
                    populateTransferFormWithBeneficiary(p);
                    navigateTo('transfer-and-pay');
                };

                const avatarHtml = p.avatar_url
                    ? `<img class="w-full h-full object-cover" alt="${p.name}" src="${p.avatar_url}"/>`
                    : `<span class="material-symbols-outlined text-[20px] text-primary-container">person</span>`;

                btn.innerHTML = `
                    <div class="relative w-12 h-12 rounded-full ring-2 ring-transparent group-hover:ring-primary-container transition-all overflow-hidden bg-surface-container flex items-center justify-center">
                        ${avatarHtml}
                    </div>
                    <span class="font-label-sm text-label-sm font-medium text-on-surface truncate w-full">${p.nickname || p.name}</span>
                `;
                payeesContainer.appendChild(btn);
            });
        }

        // 9. Recent Activity Ledger Rows
        renderDashboardTransactions(data.recent_transactions || []);

    } catch (err) {
        console.error('Failed to load dashboard:', err);
    }
}

/**
 * Fetch and Render Cashflow Chart Data from REST API (Sections 5 & 6)
 */
async function loadCashflowChart(days = 30) {
    try {
        const chartData = await ApiService.getCashflowChart(days);
        if (!chartData) return;

        // Headline values directly from backend
        const incEl = document.getElementById('dashboard-cashflow-income');
        const expEl = document.getElementById('dashboard-cashflow-expenses');
        const savEl = document.getElementById('dashboard-cashflow-savings');

        if (incEl) incEl.textContent = '+' + formatINR(chartData.total_inflow);
        if (expEl) expEl.textContent = '-' + formatINR(chartData.total_outflow);
        if (savEl) {
            const net = chartData.net_cashflow;
            savEl.textContent = (net >= 0 ? '+' : '-') + formatINR(Math.abs(net));
        }

        renderDynamicCashflowChart(chartData, days);
    } catch (err) {
        console.error('Failed to load cashflow chart:', err);
    }
}

/**
 * Render Dynamic Cashflow Time-Series Chart (Section 5 & 6)
 * Generates dynamic SVG curve, gradient fill, grid, data nodes, and tooltip based on live backend data.
 */
function renderDynamicCashflowChart(chartData, days = 30) {
    const svg = document.getElementById('dashboard-cashflow-svg');
    const emptyEl = document.getElementById('dashboard-cashflow-empty');
    const labelsEl = document.getElementById('dashboard-cashflow-labels');
    const tooltip = document.getElementById('dashboard-cashflow-tooltip');

    if (!svg) return;

    const points = chartData && Array.isArray(chartData.points) ? chartData.points : [];

    const hasActivity = points.length > 0 && (
        chartData.total_inflow > 0 || chartData.total_outflow > 0 || chartData.transaction_count > 0
    );

    if (!hasActivity) {
        svg.classList.add('hidden');
        if (emptyEl) {
            emptyEl.classList.remove('hidden');
            const msg = document.getElementById('dashboard-cashflow-empty-msg');
            if (msg) msg.textContent = `No transaction activity recorded in the previous ${days} days.`;
        }
        if (labelsEl) labelsEl.innerHTML = '';
        return;
    }

    if (emptyEl) emptyEl.classList.add('hidden');
    svg.classList.remove('hidden');

    const W = 500;
    const H = 130;
    const padX = 24;
    const padTop = 14;
    const padBottom = 16;
    const chartW = W - padX * 2;
    const chartH = H - padTop - padBottom;

    const balances = points.map(p => parseFloat(p.running_balance) || 0);
    let minVal = Math.min(...balances);
    let maxVal = Math.max(...balances);

    if (minVal === maxVal) {
        minVal = Math.max(0, minVal - 1000);
        maxVal = maxVal + 1000;
    } else {
        const span = maxVal - minVal;
        minVal = Math.max(0, minVal - span * 0.1);
        maxVal = maxVal + span * 0.1;
    }

    const n = points.length;
    const coords = points.map((p, i) => {
        const x = padX + (n === 1 ? chartW / 2 : (i / (n - 1)) * chartW);
        const val = parseFloat(p.running_balance) || 0;
        const norm = (val - minVal) / (maxVal - minVal || 1);
        const y = padTop + chartH - (norm * chartH);
        return { x, y, point: p };
    });

    // Build SVG curve path using cubic bezier smoothing
    let pathD = `M ${coords[0].x.toFixed(1)},${coords[0].y.toFixed(1)}`;
    if (coords.length === 1) {
        pathD += ` L ${coords[0].x.toFixed(1)},${coords[0].y.toFixed(1)}`;
    } else {
        for (let i = 0; i < coords.length - 1; i++) {
            const p0 = coords[i === 0 ? 0 : i - 1];
            const p1 = coords[i];
            const p2 = coords[i + 1];
            const p3 = coords[i + 2 < coords.length ? i + 2 : i + 1];

            const cp1x = p1.x + (p2.x - p0.x) / 6;
            const cp1y = p1.y + (p2.y - p0.y) / 6;
            const cp2x = p2.x - (p3.x - p1.x) / 6;
            const cp2y = p2.y - (p3.y - p1.y) / 6;

            pathD += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
        }
    }

    const areaD = `${pathD} L ${coords[coords.length - 1].x.toFixed(1)},${(H - padBottom).toFixed(1)} L ${coords[0].x.toFixed(1)},${(H - padBottom).toFixed(1)} Z`;

    const gridY1 = padTop;
    const gridY2 = padTop + chartH / 2;
    const gridY3 = padTop + chartH;

    let circlesSvg = coords.map((c, i) => {
        return `
            <circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="4"
                    fill="#ffffff" stroke="#1d4ed8" stroke-width="2.5"
                    class="chart-node cursor-pointer transition-all duration-150"
                    data-idx="${i}" />
        `;
    }).join('');

    svg.innerHTML = `
        <defs>
            <linearGradient id="softAreaGrad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#1d4ed8" stop-opacity="0.22"></stop>
                <stop offset="100%" stop-color="#1d4ed8" stop-opacity="0.01"></stop>
            </linearGradient>
        </defs>
        <!-- Horizontal Grid Lines -->
        <line x1="${padX}" y1="${gridY1.toFixed(1)}" x2="${W - padX}" y2="${gridY1.toFixed(1)}" stroke="#c4c5d7" stroke-dasharray="3 4" stroke-opacity="0.35" />
        <line x1="${padX}" y1="${gridY2.toFixed(1)}" x2="${W - padX}" y2="${gridY2.toFixed(1)}" stroke="#c4c5d7" stroke-dasharray="3 4" stroke-opacity="0.35" />
        <line x1="${padX}" y1="${gridY3.toFixed(1)}" x2="${W - padX}" y2="${gridY3.toFixed(1)}" stroke="#c4c5d7" stroke-dasharray="3 4" stroke-opacity="0.35" />
        
        <!-- Gradient Area Fill -->
        <path d="${areaD}" fill="url(#softAreaGrad)" />
        
        <!-- Primary Line -->
        <path d="${pathD}" fill="none" stroke="#1d4ed8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
        
        <!-- Interactive Nodes -->
        ${circlesSvg}
    `;

    // Interactive tooltip bindings
    svg.querySelectorAll('.chart-node').forEach(node => {
        const idx = parseInt(node.getAttribute('data-idx'), 10);
        const p = points[idx];
        if (!p) return;

        node.addEventListener('mouseenter', () => {
            node.setAttribute('r', '6');
            node.setAttribute('stroke-width', '3');
            if (tooltip) {
                tooltip.classList.remove('hidden');
                tooltip.innerHTML = `
                    <div class="font-bold text-on-surface">${p.display_date || p.date}</div>
                    <div class="text-[11px] text-outline pt-0.5">Bal: <strong class="text-on-surface">${formatINR(p.running_balance)}</strong></div>
                    <div class="flex items-center gap-2 pt-0.5 text-[10px]">
                        ${p.inflow > 0 ? `<span class="text-secondary font-semibold">+${formatINR(p.inflow)}</span>` : ''}
                        ${p.outflow > 0 ? `<span class="text-error font-semibold">-${formatINR(p.outflow)}</span>` : ''}
                        ${p.inflow === 0 && p.outflow === 0 ? `<span class="text-outline">No flow activity</span>` : ''}
                    </div>
                `;
                const containerRect = svg.parentElement.getBoundingClientRect();
                const nodeRect = node.getBoundingClientRect();
                const left = nodeRect.left - containerRect.left + 8;
                const top = nodeRect.top - containerRect.top - 55;
                tooltip.style.left = `${Math.max(10, Math.min(containerRect.width - 150, left))}px`;
                tooltip.style.top = `${Math.max(5, top)}px`;
            }
        });

        node.addEventListener('mouseleave', () => {
            node.setAttribute('r', '4');
            node.setAttribute('stroke-width', '2.5');
            if (tooltip) tooltip.classList.add('hidden');
        });
    });

    // Render X-axis Date Labels (Start, Middle, End)
    if (labelsEl) {
        if (points.length <= 1) {
            labelsEl.innerHTML = `<span>${points[0] ? (points[0].display_date || points[0].date) : ''}</span>`;
        } else {
            const first = points[0].display_date || points[0].date;
            const mid = points[Math.floor(points.length / 2)].display_date || points[Math.floor(points.length / 2)].date;
            const last = points[points.length - 1].display_date || points[points.length - 1].date;
            labelsEl.innerHTML = `
                <span>${first}</span>
                <span>${mid}</span>
                <span>${last}</span>
            `;
        }
    }
}

/**
 * Render Dashboard Recent Transactions
 */
function renderDashboardTransactions(transactions) {
    const container = document.getElementById('dashboard-txns-container');
    if (!container) return;

    if (!transactions || transactions.length === 0) {
        container.innerHTML = `<div class="p-6 text-center text-outline font-label-md">No recent transactions recorded.</div>`;
        return;
    }

    container.innerHTML = '';
    transactions.forEach(t => {
        const isCredit = t.transaction_type === 'CREDIT';
        const sign = isCredit ? '+' : '-';
        const amtColor = isCredit ? 'text-secondary' : 'text-on-surface';
        const iconBg = isCredit ? 'bg-secondary/10 text-secondary' : 'bg-surface-container text-on-surface';

        let iconName = 'receipt_long';
        let categoryName = t.category;
        if (t.category === 'SALARY') { iconName = 'domain'; categoryName = 'Monthly Salary Credit'; }
        else if (t.category === 'SHOPPING') { iconName = 'shopping_bag'; categoryName = 'Shopping & Card'; }
        else if (t.category === 'EMI_PAYMENT' || t.category === 'EMI_BILLS') { iconName = 'home'; categoryName = 'Loan EMI Auto-debit'; }
        else if (t.category === 'TRANSFER') { iconName = 'sync_alt'; categoryName = 'Fund Transfer'; }
        else if (t.category === 'INVESTMENT' || t.category === 'INTEREST') { iconName = 'savings'; categoryName = 'Interest Payout'; }

        const accDisplay = t.from_account_masked ? `Savings •••• ${t.from_account_masked.slice(-4)}` : 'Direct Credit';

        const row = document.createElement('div');
        row.className = 'txn-row flex flex-col sm:grid sm:grid-cols-12 px-6 py-4 items-start sm:items-center gap-2 sm:gap-0 hover:bg-surface-container-low/50 transition-colors';
        row.setAttribute('data-category', (t.category || '').toLowerCase());

        row.innerHTML = `
            <div class="sm:col-span-4 flex items-center gap-3.5">
                <div class="w-9 h-9 rounded-xl ${iconBg} flex items-center justify-center shrink-0">
                    <span class="material-symbols-outlined text-[19px]">${iconName}</span>
                </div>
                <div class="flex flex-col min-w-0">
                    <span class="font-body-md text-body-md font-semibold text-on-surface truncate">${t.beneficiary_name || 'Bank Transaction'}</span>
                    <span class="font-label-sm text-label-sm text-outline sm:hidden">${categoryName}</span>
                </div>
            </div>
            <div class="sm:col-span-2 text-on-surface-variant font-label-sm text-label-sm hidden sm:block">${categoryName}</div>
            <div class="sm:col-span-2 text-on-surface-variant font-label-sm text-label-sm">${accDisplay}</div>
            <div class="sm:col-span-1 text-on-surface-variant font-label-sm text-label-sm">${formatShortDate(t.timestamp)}</div>
            <div class="sm:col-span-1 flex sm:justify-center items-center gap-1.5">
                <span class="w-2 h-2 rounded-full ${t.status === 'COMPLETED' ? 'bg-secondary' : 'bg-amber-500'}"></span>
                <span class="font-label-sm text-label-sm ${t.status === 'COMPLETED' ? 'text-secondary' : 'text-amber-700'} font-medium">${t.status}</span>
            </div>
            <div class="sm:col-span-2 sm:text-right font-headline-sm text-headline-sm font-semibold ${amtColor}">${sign}${formatINR(t.amount)}</div>
        `;
        container.appendChild(row);
    });
}

/**
 * Load Accounts View
 */
async function loadAccounts() {
    try {
        const accounts = await ApiService.getAccounts();
        currentAccounts = accounts;

        // 1. Populate Transfer "From Account" and Pay EMI "From Account" selects
        populateAccountSelects(accounts);

        // 2. Render Cards in #view-accounts
        const container = document.getElementById('accounts-cards-container');
        if (!container) return;

        container.innerHTML = '';
        accounts.forEach(acc => {
            const isPrimary = acc.is_primary;
            const badgeClass = isPrimary ? 'bg-secondary/10 text-secondary' : 'bg-primary-container/10 text-primary-container';
            const badgeText = isPrimary ? 'Active · Primary' : acc.account_type_name;

            const card = document.createElement('div');
            card.className = 'glass-card p-6 rounded-2xl flex flex-col justify-between space-y-5';
            card.innerHTML = `
                <div>
                    <div class="flex justify-between items-start">
                        <span class="px-2.5 py-0.5 rounded-full ${badgeClass} font-label-sm font-semibold">${badgeText}</span>
                        <span class="font-label-sm text-outline font-medium">IFSC: ${acc.ifsc_code}</span>
                    </div>
                    <h3 class="font-headline-sm text-on-surface font-semibold pt-2">${acc.account_type_name}</h3>
                    <p class="font-body-sm text-outline">•••• ${acc.account_number.slice(-4)} · RuPay Platinum</p>
                </div>
                <div>
                    <p class="font-label-sm text-outline">Available Balance</p>
                    <p class="font-financial-numeric text-on-surface font-bold tracking-tight">${formatINR(acc.available_balance)}</p>
                    <p class="font-body-sm text-outline pt-1">Book / Ledger Balance: ${formatINR(acc.ledger_balance)}</p>
                </div>
                <div class="pt-3 border-t border-outline-variant/20 flex gap-2">
                    <button class="flex-1 py-2 rounded-lg bg-surface-container font-label-sm font-medium hover:bg-surface-container-high transition-colors text-on-surface" type="button" onclick="navigateTo('transactions')">Ledger</button>
                    <button class="flex-1 py-2 rounded-lg bg-primary-container text-white font-label-sm font-medium hover:bg-primary transition-colors" type="button" onclick="selectFromAccountForTransfer(${acc.id}); navigateTo('transfer-and-pay');">Send Money</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error('Failed to load accounts:', err);
    }
}

function populateAccountSelects(accounts) {
    const transferSelect = document.getElementById('transfer-from-account');
    const emiSelect = document.getElementById('pay-emi-account-select');

    if (transferSelect) {
        transferSelect.innerHTML = '';
        accounts.forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.id;
            opt.textContent = `${acc.account_type_name} •••• ${acc.account_number.slice(-4)} (Avail: ${formatINR(acc.available_balance)})`;
            transferSelect.appendChild(opt);
        });
    }

    if (emiSelect) {
        emiSelect.innerHTML = '';
        accounts.forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.id;
            opt.textContent = `${acc.account_type_name} •••• ${acc.account_number.slice(-4)} (Avail: ${formatINR(acc.available_balance)})`;
            emiSelect.appendChild(opt);
        });
    }
}

function selectFromAccountForTransfer(accId) {
    const select = document.getElementById('transfer-from-account');
    if (select) select.value = accId;
}

/**
 * Load Transactions View with Search & Filter
 */
async function loadTransactions(category = '', search = '') {
    try {
        const params = {};
        if (category && category !== 'All') params.category = category;
        if (search) params.search = search;

        const txns = await ApiService.getTransactions(params);
        currentTransactions = txns;
        const container = document.getElementById('transactions-table-rows');
        if (!container) return;

        if (!txns || txns.length === 0) {
            container.innerHTML = `<div class="p-6 text-center text-outline font-label-md">No transactions found matching criteria.</div>`;
            return;
        }

        container.innerHTML = '';
        txns.forEach(t => {
            const isCredit = t.transaction_type === 'CREDIT';
            const sign = isCredit ? '+' : '-';
            const amtColor = isCredit ? 'text-secondary' : 'text-on-surface';

            const row = document.createElement('div');
            row.className = 'grid grid-cols-12 px-6 py-4 items-center hover:bg-surface-container-low/50 transition-colors';
            row.innerHTML = `
                <span class="col-span-4 font-semibold text-on-surface truncate">${t.beneficiary_name || 'Bank Transaction'}</span>
                <span class="col-span-2 text-outline text-label-sm">${t.category}</span>
                <span class="col-span-2 text-on-surface-variant text-label-sm">${t.from_account_masked || 'Direct Credit'}</span>
                <span class="col-span-1 text-outline text-label-sm">${formatShortDate(t.timestamp)}</span>
                <span class="col-span-1 text-center text-secondary text-label-sm font-semibold">${t.status}</span>
                <span class="col-span-2 text-right font-headline-sm font-bold ${amtColor}">${sign}${formatINR(t.amount)}</span>
            `;
            container.appendChild(row);
        });
    } catch (err) {
        console.error('Failed to load transactions:', err);
    }
}

/**
 * Setup Transaction Filters
 */
function initTransactionFilters() {
    const searchInput = document.getElementById('transactions-search-input');
    const categorySelect = document.getElementById('transactions-category-select');

    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            loadTransactions(categorySelect ? categorySelect.value : '', e.target.value.trim());
        }, 300));
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            loadTransactions(e.target.value, searchInput ? searchInput.value.trim() : '');
        });
    }

    // Dashboard Transaction Category Filter Pills
    const filterPills = document.querySelectorAll('.txn-filter-pill');
    filterPills.forEach(pill => {
        pill.addEventListener('click', () => {
            filterPills.forEach(p => {
                p.classList.remove('bg-on-surface', 'text-surface', 'font-semibold', 'shadow-sm');
                p.classList.add('bg-surface-container-lowest', 'text-on-surface-variant', 'border', 'border-outline-variant/30');
            });
            pill.classList.remove('bg-surface-container-lowest', 'text-on-surface-variant', 'border', 'border-outline-variant/30');
            pill.classList.add('bg-on-surface', 'text-surface', 'font-semibold', 'shadow-sm');

            const filter = (pill.getAttribute('data-filter') || 'all').toLowerCase();
            const txnRows = document.querySelectorAll('#dashboard-txns-container .txn-row');
            txnRows.forEach(row => {
                const rowCat = (row.getAttribute('data-category') || '').toLowerCase();
                if (filter === 'all' || rowCat === filter || (filter === 'credits' && (rowCat === 'salary' || rowCat === 'investment')) || (filter === 'transfer' && rowCat === 'transfer') || (filter === 'emi_bills' && (rowCat === 'emi_payment' || rowCat === 'emi_bills'))) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

/**
 * Populate Transfer Form with clicked Beneficiary
 */
function populateTransferFormWithBeneficiary(b) {
    const bName = document.getElementById('transfer-beneficiary');
    const bAcc = document.getElementById('transfer-account');
    const bConf = document.getElementById('transfer-confirm-account');
    const bIfsc = document.getElementById('transfer-ifsc');

    if (bName) bName.value = b.name;
    if (bAcc) bAcc.value = b.account_number;
    if (bConf) bConf.value = b.account_number;
    if (bIfsc) bIfsc.value = b.ifsc_code;
}

/**
 * Money Transfer Workflow
 */
function initTransferWorkflow() {
    const btnReview = document.getElementById('transfer-btn-review');
    const reviewModal = document.getElementById('transfer-review-modal');
    const btnCancel = document.getElementById('transfer-btn-cancel');
    const btnConfirm = document.getElementById('transfer-btn-confirm');
    const resultModal = document.getElementById('transfer-result-modal');
    const btnResultClose = document.getElementById('transfer-result-btn-close');

    if (btnReview && reviewModal) {
        btnReview.addEventListener('click', (e) => {
            e.preventDefault();
            const fromSelect = document.getElementById('transfer-from-account');
            const fromAccText = fromSelect && fromSelect.options[fromSelect.selectedIndex] ? fromSelect.options[fromSelect.selectedIndex].text : '';
            const beneficiary = document.getElementById('transfer-beneficiary')?.value.trim();
            const accNum = document.getElementById('transfer-account')?.value.trim();
            const confirmAcc = document.getElementById('transfer-confirm-account')?.value.trim();
            const ifsc = document.getElementById('transfer-ifsc')?.value.trim();
            const amount = parseFloat(document.getElementById('transfer-amount')?.value) || 0;

            if (!beneficiary) { alert('Please enter beneficiary name.'); return; }
            if (!accNum) { alert('Please enter beneficiary account number.'); return; }
            if (accNum !== confirmAcc) { alert('Account numbers do not match.'); return; }
            if (!ifsc || ifsc.length !== 11) { alert('Please enter a valid 11-digit IFSC code (e.g. FINO0001234).'); return; }
            if (amount <= 0) { alert('Please enter a valid transfer amount greater than zero.'); return; }

            const summaryEl = document.getElementById('transfer-modal-summary');
            if (summaryEl) {
                summaryEl.innerHTML = `
                    <div class="space-y-2 text-body-sm">
                        <div class="flex justify-between border-b border-outline-variant/20 pb-1.5">
                            <span class="text-outline">Paying to:</span>
                            <span class="font-semibold text-on-surface">${beneficiary}</span>
                        </div>
                        <div class="flex justify-between border-b border-outline-variant/20 pb-1.5">
                            <span class="text-outline">Beneficiary Account:</span>
                            <span class="font-semibold text-on-surface">${accNum}</span>
                        </div>
                        <div class="flex justify-between border-b border-outline-variant/20 pb-1.5">
                            <span class="text-outline">IFSC Code:</span>
                            <span class="font-semibold text-on-surface">${ifsc.toUpperCase()}</span>
                        </div>
                        <div class="flex justify-between border-b border-outline-variant/20 pb-1.5">
                            <span class="text-outline">Debited From:</span>
                            <span class="font-semibold text-on-surface">${fromAccText}</span>
                        </div>
                        <div class="flex justify-between pt-1">
                            <span class="text-outline font-semibold">Total Amount:</span>
                            <span class="font-bold text-headline-sm text-primary-container">${formatINR(amount)}</span>
                        </div>
                    </div>
                `;
            }
            reviewModal.classList.remove('hidden');
        });

        if (btnCancel) {
            btnCancel.addEventListener('click', () => {
                reviewModal.classList.add('hidden');
            });
        }

        if (btnConfirm) {
            btnConfirm.addEventListener('click', async () => {
                btnConfirm.disabled = true;
                btnConfirm.innerHTML = `<span>Processing...</span>`;

                const fromSelect = document.getElementById('transfer-from-account');
                const fromAccId = parseInt(fromSelect ? fromSelect.value : 1);
                const beneficiary = document.getElementById('transfer-beneficiary')?.value.trim();
                const accNum = document.getElementById('transfer-account')?.value.trim();
                const confirmAcc = document.getElementById('transfer-confirm-account')?.value.trim();
                const ifsc = document.getElementById('transfer-ifsc')?.value.trim().toUpperCase();
                const amount = document.getElementById('transfer-amount')?.value;
                const remarks = document.getElementById('transfer-remarks')?.value.trim() || 'Simulated Transfer';

                try {
                    const result = await ApiService.executeTransfer({
                        from_account_id: fromAccId,
                        to_account_number: accNum,
                        confirm_account_number: confirmAcc,
                        to_ifsc: ifsc,
                        beneficiary_name: beneficiary,
                        amount: amount,
                        category: 'TRANSFER',
                        remarks: remarks
                    });

                    reviewModal.classList.add('hidden');

                    // Show Result Modal
                    if (resultModal) {
                        const txn = result.transaction;
                        const detailsEl = document.getElementById('transfer-result-details');
                        if (detailsEl) {
                            detailsEl.innerHTML = `
                                <div class="space-y-1.5">
                                    <div class="flex justify-between"><span class="text-outline">Transaction ID:</span> <strong class="text-primary-container">${txn.transaction_id}</strong></div>
                                    <div class="flex justify-between"><span class="text-outline">Amount Sent:</span> <strong class="text-on-surface">${formatINR(txn.amount)}</strong></div>
                                    <div class="flex justify-between"><span class="text-outline">Remaining Balance:</span> <strong class="text-secondary">${formatINR(txn.balance_after)}</strong></div>
                                    <div class="flex justify-between"><span class="text-outline">Reference:</span> <span class="text-outline">${txn.reference_number}</span></div>
                                </div>
                            `;
                        }
                        resultModal.classList.remove('hidden');
                    } else {
                        alert(`Transfer of ${formatINR(amount)} successful! Ref ID: ${result.transaction.transaction_id}`);
                    }

                    // Refresh live data
                    await loadCustomerDashboard();
                    await loadAccounts();
                    await loadTransactions();
                    await loadNotifications();

                } catch (err) {
                    alert(`Transfer Error: ${err.message}`);
                } finally {
                    btnConfirm.disabled = false;
                    btnConfirm.innerHTML = `<span>Authorize & Send</span><span class="material-symbols-outlined text-[18px]">lock</span>`;
                }
            });
        }

        if (btnResultClose && resultModal) {
            btnResultClose.addEventListener('click', () => {
                resultModal.classList.add('hidden');
                navigateTo('transactions');
            });
        }
    }
}

/**
 * Pay EMI Workflow
 */
function initPayEMIWorkflow() {
    const btnPay = document.getElementById('pay-emi-btn-submit');
    if (!btnPay) return;

    btnPay.addEventListener('click', async () => {
        if (!currentLoan) {
            alert('No active loan facility available to settle.');
            return;
        }

        const accSelect = document.getElementById('pay-emi-account-select');
        const accId = parseInt(accSelect ? accSelect.value : 1);
        const emiAmount = currentLoan.monthly_emi;

        if (!confirm(`Confirm debit of ${formatINR(emiAmount)} from your account to pay EMI for Loan #${currentLoan.loan_id}?`)) {
            return;
        }

        btnPay.disabled = true;
        btnPay.innerHTML = `<span>Processing Settlement...</span>`;

        try {
            const result = await ApiService.payEMI(currentLoan.id, accId, emiAmount);
            alert(`Payment of ${formatINR(emiAmount)} successful! Receipt #${result.payment.receipt_number}. Remaining principal: ${formatINR(result.payment.remaining_balance)}`);

            // Refresh live views
            await loadCustomerDashboard();
            await loadAccounts();
            await loadTransactions();
            await loadNotifications();
            navigateTo('loans-overview');

        } catch (err) {
            alert(`EMI Payment Error: ${err.message}`);
        } finally {
            btnPay.disabled = false;
            btnPay.innerHTML = `<span>Pay Installment Now</span><span class="material-symbols-outlined text-[18px]">verified</span>`;
        }
    });
}

/**
 * Load Loans Overview Data (Active Facilities, Repayment Health, CIBIL)
 */
async function loadLoansOverview() {
    try {
        const loans = await ApiService.getLoans();
        const activeLoan = Array.isArray(loans) ? loans.find(l => l.status === 'ACTIVE') || loans[0] : null;

        const loTitle = document.getElementById('loans-overview-title');
        const loSub = document.getElementById('loans-overview-sub');
        const loDue = document.getElementById('loans-overview-duedate');
        const loOut = document.getElementById('loans-overview-outstanding');
        const loRep = document.getElementById('loans-overview-repaid');
        const loEmi = document.getElementById('loans-overview-emi');
        const loProgText = document.getElementById('loans-overview-progress-text');
        const loProg = document.getElementById('loans-overview-progressbar');
        const loServ = document.getElementById('loans-overview-servicing');
        const loTenureText = document.getElementById('loans-overview-tenure-text');
        const loBadge = document.getElementById('loans-overview-badge');

        if (activeLoan) {
            const repaidPct = activeLoan.principal_amount > 0
                ? Math.min(100, Math.round(((activeLoan.principal_amount - activeLoan.outstanding_amount) / activeLoan.principal_amount) * 100))
                : 50;
            const repaidAmt = activeLoan.principal_amount - activeLoan.outstanding_amount;

            if (loTitle) loTitle.textContent = `${activeLoan.loan_type_name} #${activeLoan.loan_id}`;
            if (loSub) loSub.textContent = `Sanctioned: ${formatINR(activeLoan.principal_amount)} @ ${activeLoan.interest_rate}% p.a. (Fixed)`;
            if (loDue) loDue.textContent = formatDate(activeLoan.next_due_date);
            if (loOut) loOut.textContent = formatINR(activeLoan.outstanding_amount, false);
            if (loRep) loRep.textContent = formatINR(repaidAmt, false);
            if (loEmi) loEmi.textContent = `${formatINR(activeLoan.monthly_emi, false)}/mo`;
            if (loProgText) loProgText.textContent = `Progress: ${repaidPct}% Repaid`;
            if (loTenureText) loTenureText.textContent = `Tenure: ${activeLoan.tenure_months} Installments`;
            if (loProg) loProg.style.width = `${repaidPct}%`;
            if (loServ && activeLoan.servicing_account_number) {
                loServ.textContent = `Savings •••• ${activeLoan.servicing_account_number.slice(-4)}`;
            }
            if (loBadge) {
                loBadge.textContent = 'Active Loan Facility';
                loBadge.className = 'px-2.5 py-0.5 rounded-full bg-secondary/10 text-secondary font-label-sm font-semibold';
            }
        } else {
            if (loTitle) loTitle.textContent = 'No Active Loan Facilities';
            if (loSub) loSub.textContent = 'Zero current outstanding debt · Ready for new applications';
            if (loDue) loDue.textContent = 'N/A';
            if (loOut) loOut.textContent = '₹0.00';
            if (loRep) loRep.textContent = '₹0.00';
            if (loEmi) loEmi.textContent = '₹0.00/mo';
            if (loProgText) loProgText.textContent = 'Progress: 100% Clear';
            if (loTenureText) loTenureText.textContent = 'No pending installments';
            if (loProg) loProg.style.width = '0%';
            if (loBadge) {
                loBadge.textContent = 'Debt Free';
                loBadge.className = 'px-2.5 py-0.5 rounded-full bg-primary-container/10 text-primary-container font-label-sm font-semibold';
            }
        }
    } catch (err) {
        console.error('Error loading loans overview:', err);
    }
}

/**
 * 7-Step Loan Application Wizard
 */
function initLoanApplicationWizard() {
    let currentStep = 1;
    const totalSteps = 7;

    const btnNext = document.getElementById('wizard-btn-next');
    const btnBack = document.getElementById('wizard-btn-back');
    const stepCards = document.querySelectorAll('.wizard-step-card');
    const stepIndicators = document.querySelectorAll('.wizard-step-indicator');
    const reviewBox = document.getElementById('wizard-review-summary');
    const successModal = document.getElementById('wizard-success-modal');
    const btnSuccessClose = document.getElementById('wizard-success-btn-close');

    function updateWizard() {
        stepCards.forEach(card => {
            const stepNum = parseInt(card.getAttribute('data-step'));
            if (stepNum === currentStep) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });

        stepIndicators.forEach(ind => {
            const stepNum = parseInt(ind.getAttribute('data-step-indicator'));
            if (stepNum === currentStep) {
                ind.classList.add('bg-primary-container', 'text-white', 'font-bold');
                ind.classList.remove('bg-surface-container', 'text-outline');
            } else if (stepNum < currentStep) {
                ind.classList.add('bg-secondary', 'text-white');
                ind.classList.remove('bg-surface-container', 'text-outline', 'bg-primary-container');
            } else {
                ind.classList.remove('bg-primary-container', 'bg-secondary', 'text-white', 'font-bold');
                ind.classList.add('bg-surface-container', 'text-outline');
            }
        });

        if (btnBack) {
            btnBack.disabled = (currentStep === 1);
            btnBack.style.visibility = (currentStep === 1) ? 'hidden' : 'visible';
        }

        if (btnNext) {
            if (currentStep === totalSteps) {
                btnNext.innerHTML = `<span>Submit Application</span><span class="material-symbols-outlined text-[18px]">check_circle</span>`;
            } else {
                btnNext.innerHTML = `<span>Continue</span><span class="material-symbols-outlined text-[18px]">arrow_forward</span>`;
            }
        }

        // Fill review summary at step 7
        if (currentStep === totalSteps && reviewBox) {
            const loanTypeRadio = document.querySelector('input[name="wizard-loan-type"]:checked');
            const loanTypeName = loanTypeRadio ? loanTypeRadio.value : 'Home Loan';
            const amount = document.getElementById('wizard-amount')?.value || '2500000';
            const tenure = document.getElementById('wizard-tenure')?.value || '120';
            const emp = document.getElementById('wizard-employment')?.value || 'Salaried';
            const income = document.getElementById('wizard-income')?.value || '145000';

            reviewBox.innerHTML = `
                <div class="grid grid-cols-2 gap-3 text-body-sm">
                    <div><span class="text-outline">Facility:</span> <strong class="text-on-surface">${loanTypeName}</strong></div>
                    <div><span class="text-outline">Sanction Amount:</span> <strong class="text-on-surface">${formatINR(amount, false)}</strong></div>
                    <div><span class="text-outline">Tenure:</span> <strong class="text-on-surface">${tenure} Months (${Math.round(tenure / 12)} Yrs)</strong></div>
                    <div><span class="text-outline">Proposed Rate:</span> <strong class="text-secondary">8.25% p.a. (Fixed)</strong></div>
                    <div><span class="text-outline">Applicant:</span> <strong class="text-on-surface">${currentUser?.first_name ? currentUser.first_name + ' ' + currentUser.last_name : 'Sophia Mehta'}</strong></div>
                    <div><span class="text-outline">Employment:</span> <strong class="text-on-surface">${emp}</strong></div>
                    <div><span class="text-outline">Monthly Income:</span> <strong class="text-on-surface">${formatINR(income, false)}</strong></div>
                    <div><span class="text-outline">Bureau CIBIL:</span> <strong class="text-secondary">785 (Excellent)</strong></div>
                </div>
            `;
        }
    }

    if (btnNext) {
        btnNext.addEventListener('click', async () => {
            if (currentStep < totalSteps) {
                currentStep++;
                updateWizard();
            } else {
                // Submit to backend
                btnNext.disabled = true;
                btnNext.innerHTML = `<span>Submitting...</span>`;

                const loanTypeRadio = document.querySelector('input[name="wizard-loan-type"]:checked');
                const facilityName = loanTypeRadio ? loanTypeRadio.value : 'Home Loan';
                const amount = document.getElementById('wizard-amount')?.value || '2500000';
                const tenure = document.getElementById('wizard-tenure')?.value || '120';
                const emp = document.getElementById('wizard-employment')?.value || 'Salaried';
                const income = document.getElementById('wizard-income')?.value || '145000';

                // Map facility name to LoanType ID (1: Home Loan, 2: Personal Loan, 3: Education Loan)
                let loanTypeId = 1;
                if (facilityName.includes('Personal')) loanTypeId = 2;
                else if (facilityName.includes('Education')) loanTypeId = 3;

                try {
                    const appData = await ApiService.applyForLoan({
                        loan_type: loanTypeId,
                        requested_amount: amount,
                        tenure_months: parseInt(tenure),
                        employment_type: emp,
                        employer_name: 'Tata Consultancy Services',
                        monthly_income: income,
                        existing_obligations: '0',
                        purpose: `Application for ${facilityName}`
                    });

                    if (successModal) {
                        const detailsBox = document.getElementById('wizard-success-details');
                        if (detailsBox) {
                            detailsBox.innerHTML = `
                                <div class="space-y-1 text-body-sm">
                                    <div><span class="text-outline">Application ID:</span> <strong class="text-primary-container">${appData.application_id}</strong></div>
                                    <div><span class="text-outline">Facility:</span> <strong class="text-on-surface">${facilityName}</strong></div>
                                    <div><span class="text-outline">Requested Principal:</span> <strong class="text-on-surface">${formatINR(appData.requested_amount, false)}</strong></div>
                                    <div><span class="text-outline">Estimated EMI:</span> <strong class="text-secondary">${formatINR(appData.calculated_emi, false)}/mo</strong></div>
                                    <div><span class="text-outline">KYC Verification:</span> <span class="px-2 py-0.5 rounded bg-primary-container/10 text-primary-container font-semibold font-label-sm">CASE ROUTED TO UNDERWRITING</span></div>
                                    <div><span class="text-outline">Status:</span> <span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-900 font-semibold font-label-sm">UNDER REVIEW</span></div>
                                </div>
                            `;
                        }
                        successModal.classList.remove('hidden');
                        await loadNotifications();
                    } else {
                        alert(`Loan Application #${appData.application_id} submitted! KYC verification case created and assigned to operations officer.`);
                        await loadNotifications();
                        navigateTo('loans-overview');
                    }

                    // Reset wizard to Step 1
                    currentStep = 1;
                    updateWizard();

                } catch (err) {
                    alert(`Loan Application Error: ${err.message}`);
                } finally {
                    btnNext.disabled = false;
                    btnNext.innerHTML = `<span>Submit Application</span><span class="material-symbols-outlined text-[18px]">check_circle</span>`;
                }
            }
        });
    }

    if (btnBack) {
        btnBack.addEventListener('click', () => {
            if (currentStep > 1) {
                currentStep--;
                updateWizard();
            }
        });
    }

    if (btnSuccessClose && successModal) {
        btnSuccessClose.addEventListener('click', () => {
            successModal.classList.add('hidden');
            navigateTo('loans-overview');
        });
    }

    updateWizard();
}

/**
 * Mathematical Reducing-Balance EMI Calculator
 * E = P * r * (1 + r)^n / ((1 + r)^n - 1)
 */
function initEMICalculator() {
    const amountInput = document.getElementById('calc-amount');
    const amountSlider = document.getElementById('calc-amount-slider');
    const rateInput = document.getElementById('calc-rate');
    const rateSlider = document.getElementById('calc-rate-slider');
    const tenureInput = document.getElementById('calc-tenure');
    const tenureSlider = document.getElementById('calc-tenure-slider');

    if (!amountInput || !rateInput || !tenureInput) return;

    function syncAndCalculate() {
        const principal = parseFloat(amountInput.value) || 2500000;
        const rate = parseFloat(rateInput.value) || 8.25;
        const tenureMonths = parseInt(tenureInput.value) || 240;

        const monthlyRate = rate / (12 * 100);
        let emi = 0;
        if (monthlyRate === 0) {
            emi = principal / tenureMonths;
        } else {
            emi = (principal * monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) /
                  (Math.pow(1 + monthlyRate, tenureMonths) - 1);
        }

        const totalPayable = emi * tenureMonths;
        const totalInterest = totalPayable - principal;

        const emiDisplay = document.getElementById('calc-display-emi');
        const interestDisplay = document.getElementById('calc-display-interest');
        const totalDisplay = document.getElementById('calc-display-total');

        if (emiDisplay) emiDisplay.textContent = formatINR(Math.round(emi), false) + '/mo';
        if (interestDisplay) interestDisplay.textContent = formatINR(Math.round(totalInterest), false);
        if (totalDisplay) totalDisplay.textContent = formatINR(Math.round(totalPayable), false);
    }

    if (amountSlider) {
        amountSlider.addEventListener('input', () => { amountInput.value = amountSlider.value; syncAndCalculate(); });
        amountInput.addEventListener('input', () => { amountSlider.value = amountInput.value; syncAndCalculate(); });
    }
    if (rateSlider) {
        rateSlider.addEventListener('input', () => { rateInput.value = rateSlider.value; syncAndCalculate(); });
        rateInput.addEventListener('input', () => { rateSlider.value = rateInput.value; syncAndCalculate(); });
    }
    if (tenureSlider) {
        tenureSlider.addEventListener('input', () => { tenureInput.value = tenureSlider.value; syncAndCalculate(); });
        tenureInput.addEventListener('input', () => { tenureSlider.value = tenureInput.value; syncAndCalculate(); });
    }

    syncAndCalculate();
}

/**
 * Notifications Center
 */
async function loadNotifications() {
    try {
        const notifications = await ApiService.getNotifications();
        const container = document.getElementById('notifications-list-container');
        if (!container) return;

        if (!notifications || notifications.length === 0) {
            container.innerHTML = `<div class="p-6 text-center text-outline font-label-md">No notifications at this time.</div>`;
            return;
        }

        container.innerHTML = '';
        notifications.forEach(n => {
            let iconBox = 'bg-primary-container/10 text-primary-container';
            let icon = 'notifications';

            if (n.notification_type === 'TRANSFER_SUCCESS') {
                iconBox = 'bg-secondary/10 text-secondary';
                icon = 'payments';
            } else if (n.notification_type === 'PAYMENT_DUE') {
                iconBox = 'bg-amber-500/10 text-amber-800';
                icon = 'schedule';
            } else if (n.notification_type === 'SECURITY' || n.notification_type === 'SECURITY_ALERT') {
                iconBox = 'bg-error/10 text-error';
                icon = 'shield';
            }

            const item = document.createElement('div');
            item.className = `p-5 flex items-start gap-4 hover:bg-surface-container-low/60 transition-colors cursor-pointer ${n.is_read ? 'opacity-70' : ''}`;
            item.onclick = async () => {
                if (!n.is_read) {
                    await ApiService.markNotificationRead(n.id);
                    item.classList.add('opacity-70');
                }
            };

            item.innerHTML = `
                <div class="w-10 h-10 rounded-xl ${iconBox} flex items-center justify-center shrink-0">
                    <span class="material-symbols-outlined text-[20px]">${icon}</span>
                </div>
                <div class="flex-1">
                    <div class="flex justify-between items-baseline">
                        <h4 class="font-label-md font-semibold text-on-surface">${n.title}</h4>
                        <span class="font-label-sm text-outline">${formatShortDate(n.created_at)}</span>
                    </div>
                    <p class="font-body-sm text-on-surface-variant pt-0.5">${n.message}</p>
                </div>
            `;
            container.appendChild(item);
        });
    } catch (err) {
        console.error('Failed to load notifications:', err);
    }
}

function initNotificationsCenter() {
    const btnMarkAll = document.getElementById('btn-notifications-mark-all');
    if (btnMarkAll) {
        btnMarkAll.addEventListener('click', async () => {
            try {
                await ApiService.markAllNotificationsRead();
                await loadNotifications();
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        });
    }
}

/**
 * ========================================================
 * REGULATORY MODALS & ACTION PROMPTS
 * ========================================================
 */
function promptActionModal({ title, subtitle, desc, label, placeholder, confirmText, confirmClass, icon, requireReason = true }) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modal-action-prompt');
        const titleEl = document.getElementById('prompt-modal-title');
        const subEl = document.getElementById('prompt-modal-subtitle');
        const descEl = document.getElementById('prompt-modal-desc');
        const labelEl = document.getElementById('prompt-modal-input-label');
        const textarea = document.getElementById('prompt-modal-textarea');
        const btnCancel = document.getElementById('btn-prompt-modal-cancel');
        const btnConfirm = document.getElementById('btn-prompt-modal-confirm');
        const iconEl = document.getElementById('prompt-modal-icon');

        if (!modal) {
            const fallback = prompt(`${title}\n${desc || ''}\n${label || 'Reason:'}`, '');
            resolve(fallback);
            return;
        }

        if (titleEl) titleEl.textContent = title || 'Confirm Action';
        if (subEl) subEl.textContent = subtitle || '';
        if (descEl) descEl.textContent = desc || '';
        if (labelEl) labelEl.textContent = label || 'Justification / Reason:';
        if (textarea) {
            textarea.value = '';
            textarea.placeholder = placeholder || 'Enter mandatory compliance reason...';
        }
        if (iconEl) iconEl.textContent = icon || 'verified_user';
        if (btnConfirm) {
            btnConfirm.textContent = confirmText || 'Confirm';
            btnConfirm.className = `px-5 py-2 rounded-xl font-label-md font-semibold text-white transition-colors ${confirmClass || 'bg-primary-container hover:bg-primary'}`;
        }

        modal.classList.remove('hidden');
        if (textarea) textarea.focus();

        const cleanup = () => {
            modal.classList.add('hidden');
            if (btnCancel) btnCancel.onclick = null;
            if (btnConfirm) btnConfirm.onclick = null;
        };

        if (btnCancel) {
            btnCancel.onclick = () => {
                cleanup();
                resolve(null);
            };
        }

        if (btnConfirm) {
            btnConfirm.onclick = () => {
                const val = textarea ? textarea.value.trim() : '';
                if (requireReason && !val) {
                    alert('A justification/reason is required for this regulatory action.');
                    if (textarea) textarea.focus();
                    return;
                }
                cleanup();
                resolve(val || true);
            };
        }
    });
}

function showGenericDetailModal({ title, icon, contentHtml }) {
    const modal = document.getElementById('modal-generic-detail');
    const titleEl = document.getElementById('generic-detail-title');
    const iconEl = document.getElementById('generic-detail-icon');
    const contentEl = document.getElementById('generic-detail-content');
    const btnClose = document.getElementById('btn-generic-detail-close');

    if (!modal) return;
    if (titleEl) titleEl.textContent = title || 'Record Details';
    if (iconEl) iconEl.textContent = icon || 'info';
    if (contentEl) contentEl.innerHTML = contentHtml;

    modal.classList.remove('hidden');
    if (btnClose) {
        btnClose.onclick = () => modal.classList.add('hidden');
    }
}

function showBranchFormModal(branch = null) {
    const modal = document.getElementById('modal-branch-form');
    const form = document.getElementById('form-branch-edit');
    const titleEl = document.getElementById('branch-modal-title');
    const btnClose = document.getElementById('btn-branch-form-close');
    const btnCancel = document.getElementById('btn-branch-form-cancel');

    if (!modal || !form) return;

    const idInput = document.getElementById('branch-form-id');
    const codeInput = document.getElementById('branch-form-code');
    const nameInput = document.getElementById('branch-form-name');
    const ifscInput = document.getElementById('branch-form-ifsc');
    const cityInput = document.getElementById('branch-form-city');
    const managerInput = document.getElementById('branch-form-manager');
    const addressInput = document.getElementById('branch-form-address');

    if (branch) {
        if (titleEl) titleEl.textContent = 'Edit Branch Details';
        if (idInput) idInput.value = branch.id;
        if (codeInput) codeInput.value = branch.branch_code;
        if (nameInput) nameInput.value = branch.name;
        if (ifscInput) ifscInput.value = branch.ifsc_code;
        if (cityInput) cityInput.value = branch.city;
        if (managerInput) managerInput.value = branch.manager_name || '';
        if (addressInput) addressInput.value = branch.address || '';
    } else {
        if (titleEl) titleEl.textContent = 'Register Bank Branch';
        form.reset();
        if (idInput) idInput.value = '';
    }

    modal.classList.remove('hidden');

    const closeModal = () => modal.classList.add('hidden');
    if (btnClose) btnClose.onclick = closeModal;
    if (btnCancel) btnCancel.onclick = closeModal;

    form.onsubmit = async (e) => {
        e.preventDefault();
        const payload = {
            branch_code: codeInput.value.trim().toUpperCase(),
            name: nameInput.value.trim(),
            ifsc_code: ifscInput.value.trim().toUpperCase(),
            city: cityInput.value.trim(),
            manager_name: managerInput.value.trim(),
            address: addressInput.value.trim()
        };

        const branchId = idInput.value;
        try {
            if (branchId) {
                await ApiService.updateBranch(branchId, payload);
                alert(`Branch ${payload.name} updated successfully!`);
            } else {
                await ApiService.createBranch(payload);
                alert(`New branch ${payload.name} registered successfully!`);
            }
            closeModal();
            await loadAdminBranches();
        } catch (err) {
            alert(`Failed to save branch: ${err.message}`);
        }
    };
}

/**
 * ========================================================
 * EMPLOYEE PORTAL (OPS & UNDERWRITING)
 * ========================================================
 */
let currentEmployeeTab = 'loans';

function initEmployeePortal() {
    // Tab switching
    document.querySelectorAll('.employee-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            switchEmployeeTab(tab);
        });
    });

    // 1. Underwriting listeners
    const loanFilter = document.getElementById('employee-loan-status-filter');
    if (loanFilter) {
        loanFilter.addEventListener('change', () => loadEmployeeLoans());
    }
    const btnRefreshLoans = document.getElementById('btn-refresh-employee-loans');
    if (btnRefreshLoans) {
        btnRefreshLoans.addEventListener('click', () => loadEmployeeLoans());
    }

    // 2. KYC listeners
    const kycFilter = document.getElementById('employee-kyc-status-filter');
    if (kycFilter) {
        kycFilter.addEventListener('change', () => loadEmployeeKYC());
    }
    const btnRefreshKyc = document.getElementById('btn-refresh-employee-kyc');
    if (btnRefreshKyc) {
        btnRefreshKyc.addEventListener('click', () => loadEmployeeKYC());
    }

    // 3. Customer Lookup listeners
    const custSearchInput = document.getElementById('employee-customer-search-input');
    const btnCustSearch = document.getElementById('btn-employee-customer-search');
    if (btnCustSearch && custSearchInput) {
        btnCustSearch.addEventListener('click', () => loadEmployeeCustomers(custSearchInput.value.trim()));
        custSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                loadEmployeeCustomers(custSearchInput.value.trim());
            }
        });
    }

    // 4. Ledger listeners
    const btnLedgerFilter = document.getElementById('btn-employee-ledger-filter');
    if (btnLedgerFilter) {
        btnLedgerFilter.addEventListener('click', () => loadEmployeeLedger());
    }
    const btnLedgerExport = document.getElementById('btn-employee-ledger-export');
    if (btnLedgerExport) {
        btnLedgerExport.addEventListener('click', () => exportTransactionsToCSV());
    }
}

async function switchEmployeeTab(tab) {
    currentEmployeeTab = tab;

    // Subtab button state
    document.querySelectorAll('.employee-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === tab) {
            btn.classList.add('active', 'text-primary-container', 'bg-surface-container-lowest', 'shadow-sm', 'font-semibold');
            btn.classList.remove('text-outline', 'font-medium');
        } else {
            btn.classList.remove('active', 'text-primary-container', 'bg-surface-container-lowest', 'shadow-sm', 'font-semibold');
            btn.classList.add('text-outline', 'font-medium');
        }
    });

    // Sidebar items
    document.querySelectorAll('.employee-nav-item').forEach(link => {
        if (link.getAttribute('data-employee-tab') === tab) {
            link.classList.remove('text-on-surface-variant', 'font-label-md');
            link.classList.add('bg-surface-container-low', 'text-primary-container', 'font-semibold');
        } else {
            link.classList.remove('bg-surface-container-low', 'text-primary-container', 'font-semibold');
            link.classList.add('text-on-surface-variant', 'font-label-md');
        }
    });

    // Panels
    document.querySelectorAll('.employee-tab-panel').forEach(p => p.classList.add('hidden'));
    const panel = document.getElementById(`employee-panel-${tab}`);
    if (panel) panel.classList.remove('hidden');

    await loadEmployeeStats();

    if (tab === 'loans') await loadEmployeeLoans();
    else if (tab === 'kyc') await loadEmployeeKYC();
    else if (tab === 'customers') await loadEmployeeCustomers();
    else if (tab === 'ledger') await loadEmployeeLedger();
}

/**
 * 1. Employee: Loan Applications Underwriting
 */
async function loadEmployeeLoans() {
    const container = document.getElementById('employee-loan-queue-container');
    const filterEl = document.getElementById('employee-loan-status-filter');
    const status = filterEl ? filterEl.value : 'ALL';

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading application queue...</div>`;

    try {
        const params = {};
        if (status && status !== 'ALL') params.status = status;
        const apps = await ApiService.getLoanApplications(params);

        if (!apps || apps.length === 0) {
            container.innerHTML = `
                <div class="p-10 text-center flex flex-col items-center">
                    <span class="material-symbols-outlined text-[40px] text-outline mb-2">assignment_turned_in</span>
                    <p class="font-headline-sm text-on-surface font-semibold">Queue is clear</p>
                    <p class="font-body-sm text-outline pt-1">No loan applications matching the selected criteria.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        apps.forEach(app => {
            const isReview = app.status === 'UNDER_REVIEW';
            let badgeClass = 'bg-amber-500/10 text-amber-900';
            if (app.status === 'APPROVED') badgeClass = 'bg-secondary/10 text-secondary';
            if (app.status === 'REJECTED') badgeClass = 'bg-error/10 text-error';

            const item = document.createElement('div');
            item.className = 'p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:bg-surface-container-low/40 transition-colors';

            let actionsHtml = `<span class="px-3 py-1 rounded-lg ${badgeClass} font-label-sm font-semibold uppercase">${app.status.replace('_', ' ')}</span>`;

            if (isReview) {
                actionsHtml = `
                    <div class="flex flex-wrap items-center gap-2">
                        <button type="button" class="btn-emp-app-detail px-3 py-1.5 rounded-xl border border-outline-variant/30 text-on-surface hover:bg-surface-container-high font-label-sm font-semibold transition-colors" data-id="${app.id}">
                            View Dossier
                        </button>
                        <button type="button" class="btn-emp-app-reject px-3.5 py-1.5 rounded-xl bg-error-container/40 text-error font-label-sm font-semibold hover:bg-error-container transition-colors" data-id="${app.id}">
                            Reject
                        </button>
                        <button type="button" class="btn-emp-app-approve px-4 py-1.5 rounded-xl bg-primary-container text-white font-label-sm font-semibold hover:bg-primary transition-colors flex items-center gap-1" data-id="${app.id}">
                            <span class="material-symbols-outlined text-[16px]">check</span> Sanction &amp; Disburse
                        </button>
                    </div>
                `;
            } else {
                actionsHtml += `
                    <button type="button" class="btn-emp-app-detail ml-3 px-3 py-1.5 rounded-xl border border-outline-variant/30 text-on-surface hover:bg-surface-container-high font-label-sm font-semibold transition-colors" data-id="${app.id}">
                        View Dossier
                    </button>
                `;
            }

            item.innerHTML = `
                <div class="space-y-1">
                    <div class="flex items-center gap-2.5">
                        <span class="font-headline-sm font-bold text-on-surface">${app.customer_name || 'Applicant'}</span>
                        <span class="px-2 py-0.5 rounded ${badgeClass} font-label-sm font-semibold text-[11px]">${app.status.replace('_', ' ')}</span>
                    </div>
                    <p class="font-body-sm text-outline">Application #${app.application_id} · ${app.loan_type_name} · ${formatINR(app.requested_amount, false)} @ ${app.proposed_interest_rate}% (${app.tenure_months} Mo)</p>
                    <p class="font-label-sm text-on-surface-variant">Income: ${formatINR(app.monthly_income, false)}/mo (${app.employer_name || app.employment_type}) · Calculated EMI: ${formatINR(app.calculated_emi, false)}/mo · PAN: ${app.pan_number}</p>
                    ${app.underwriting_notes ? `<p class="font-label-sm text-outline italic pt-0.5">Remarks: "${app.underwriting_notes}"</p>` : ''}
                </div>
                <div class="flex items-center gap-2 shrink-0">
                    ${actionsHtml}
                </div>
            `;
            container.appendChild(item);
        });

        // Bind application action buttons
        container.querySelectorAll('.btn-emp-app-approve').forEach(btn => {
            btn.onclick = async () => {
                const appId = btn.getAttribute('data-id');
                const reason = await promptActionModal({
                    title: 'Approve & Disburse Credit Facility',
                    subtitle: `Application #${appId}`,
                    desc: 'Sanctions this credit facility, generates amortization schedule, and atomically disburses the full principal into the borrower primary checking account.',
                    label: 'Underwriting Sanction Notes:',
                    placeholder: 'Approved based on verified KYC documents, debt-to-income ratio < 40%, and clean bureau standing.',
                    confirmText: 'Sanction & Disburse',
                    confirmClass: 'bg-secondary hover:bg-secondary/90',
                    icon: 'verified',
                    requireReason: true
                });
                if (!reason) return;
                try {
                    await ApiService.reviewLoanApplication(appId, 'APPROVED', reason);
                    alert(`Credit Application #${appId} sanctioned & disbursed successfully!`);
                    await loadEmployeeLoans();
                } catch (err) {
                    alert(`Sanctioning failed: ${err.message}`);
                }
            };
        });

        container.querySelectorAll('.btn-emp-app-reject').forEach(btn => {
            btn.onclick = async () => {
                const appId = btn.getAttribute('data-id');
                const reason = await promptActionModal({
                    title: 'Reject Credit Application',
                    subtitle: `Application #${appId}`,
                    desc: 'Declines credit facility. A compliance notification is recorded.',
                    label: 'Mandatory Rejection Justification:',
                    placeholder: 'e.g. Inadequate debt service coverage ratio / incomplete documentation',
                    confirmText: 'Reject Application',
                    confirmClass: 'bg-error hover:bg-red-700',
                    icon: 'cancel',
                    requireReason: true
                });
                if (!reason) return;
                try {
                    await ApiService.reviewLoanApplication(appId, 'REJECTED', reason);
                    alert(`Application #${appId} rejected.`);
                    await loadEmployeeLoans();
                } catch (err) {
                    alert(`Action failed: ${err.message}`);
                }
            };
        });

        container.querySelectorAll('.btn-emp-app-detail').forEach(btn => {
            btn.onclick = () => {
                const appId = btn.getAttribute('data-id');
                const app = apps.find(a => String(a.id) === String(appId));
                if (!app) return;
                showGenericDetailModal({
                    title: `Credit Dossier #${app.application_id}`,
                    icon: 'rate_review',
                    contentHtml: `
                        <div class="grid grid-cols-2 gap-4 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Applicant Name</span><strong class="text-on-surface font-semibold">${app.customer_name || 'N/A'}</strong></div>
                            <div><span class="text-outline text-label-sm block">Status</span><span class="px-2 py-0.5 rounded bg-primary-container/10 text-primary-container font-label-sm font-semibold">${app.status}</span></div>
                            <div><span class="text-outline text-label-sm block">Facility Scheme</span><strong class="text-on-surface font-semibold">${app.loan_type_name}</strong></div>
                            <div><span class="text-outline text-label-sm block">Requested Principal</span><strong class="text-secondary font-semibold text-lg">${formatINR(app.requested_amount, false)}</strong></div>
                            <div><span class="text-outline text-label-sm block">Interest Rate &amp; Tenure</span><span class="text-on-surface">${app.proposed_interest_rate}% p.a. · ${app.tenure_months} Months</span></div>
                            <div><span class="text-outline text-label-sm block">Calculated Monthly EMI</span><span class="text-on-surface font-semibold">${formatINR(app.calculated_emi, false)}/mo</span></div>
                        </div>
                        <div class="grid grid-cols-2 gap-4 pt-2 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Employment Type</span><span class="text-on-surface">${app.employment_type || 'N/A'}</span></div>
                            <div><span class="text-outline text-label-sm block">Employer Name</span><span class="text-on-surface">${app.employer_name || 'Self-Employed / Professional'}</span></div>
                            <div><span class="text-outline text-label-sm block">Monthly Income</span><span class="text-on-surface">${formatINR(app.monthly_income, false)}</span></div>
                            <div><span class="text-outline text-label-sm block">PAN Number</span><span class="text-on-surface uppercase font-mono font-medium">${app.pan_number || 'N/A'}</span></div>
                        </div>
                        <div class="pt-2">
                            <span class="text-outline text-label-sm block">Loan Purpose &amp; Underwriting Notes</span>
                            <p class="text-on-surface font-body-sm pt-1">${app.purpose || 'General personal credit facility'}</p>
                            ${app.underwriting_notes ? `<p class="mt-2 p-3 rounded-xl bg-surface-container-low border border-outline-variant/20 text-on-surface-variant font-label-sm"><strong>Underwriter Remark:</strong> ${app.underwriting_notes}</p>` : ''}
                        </div>
                    `
                });
            };
        });

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading queue: ${err.message}</div>`;
    }
}

/**
 * 2. Employee: Dynamic Dashboard Stats Grid (Section 16)
 */
async function loadEmployeeStats() {
    try {
        const stats = await ApiService.getEmployeeStats();
        if (!stats) return;

        const assEl = document.getElementById('emp-stat-assigned-kyc');
        const pendEl = document.getElementById('emp-stat-pending-kyc');
        const revEl = document.getElementById('emp-stat-needs-review-kyc');
        const compEl = document.getElementById('emp-stat-completed-kyc');
        const loanEl = document.getElementById('emp-stat-pending-loans');

        if (assEl) assEl.textContent = stats.my_assigned_kyc ?? '--';
        if (pendEl) pendEl.textContent = stats.total_pending_kyc ?? '--';
        if (revEl) revEl.textContent = stats.total_needs_review_kyc ?? '--';
        if (compEl) compEl.textContent = stats.total_completed_kyc ?? '--';
        if (loanEl) loanEl.textContent = stats.pending_loan_applications ?? '--';
    } catch (err) {
        console.error('Failed to load employee stats:', err);
    }
}

/**
 * 3. Employee: KYC Verification Queue & Operations (Sections 11, 12 & 13)
 */
async function loadEmployeeKYC() {
    const container = document.getElementById('employee-kyc-container');
    const filterEl = document.getElementById('employee-kyc-status-filter');
    const statusVal = filterEl ? filterEl.value : 'ALL';

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading KYC verification requests...</div>`;

    try {
        const params = {};
        if (statusVal === 'ASSIGNED_TO_ME') {
            params.assigned = 'me';
        } else if (statusVal !== 'ALL') {
            params.status = statusVal;
        }

        const requests = await ApiService.getKYCRequests(params);

        if (!requests || requests.length === 0) {
            container.innerHTML = `
                <div class="p-10 text-center flex flex-col items-center">
                    <span class="material-symbols-outlined text-[40px] text-outline mb-2">verified</span>
                    <p class="font-headline-sm text-on-surface font-semibold">No KYC Requests Found</p>
                    <p class="font-body-sm text-outline pt-1">All applications in this category have been processed or queue is empty.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        requests.forEach(r => {
            let badgeClass = 'bg-amber-500/10 text-amber-900';
            if (r.status === 'APPROVED') badgeClass = 'bg-secondary/10 text-secondary';
            if (r.status === 'REJECTED') badgeClass = 'bg-error/10 text-error';
            if (r.status === 'NEEDS_REVIEW') badgeClass = 'bg-amber-900/10 text-amber-900';
            if (r.status === 'ASSIGNED') badgeClass = 'bg-primary-container/10 text-primary-container';

            const isAssignedToCurrent = currentUser && (
                r.assigned_employee_id === currentUser.id ||
                r.assigned_employee_name?.toLowerCase().includes((currentUser.first_name || '').toLowerCase())
            );

            const item = document.createElement('div');
            item.className = 'p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:bg-surface-container-low/40 transition-colors border-b border-outline-variant/15';

            item.innerHTML = `
                <div class="space-y-1">
                    <div class="flex items-center gap-2.5">
                        <span class="font-headline-sm font-bold text-on-surface">${r.customer_name}</span>
                        <span class="px-2 py-0.5 rounded ${badgeClass} font-label-sm font-semibold text-[11px]">${r.status}</span>
                        ${r.assigned_employee_name ? `
                            <span class="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-[11px]">
                                Officer: ${r.assigned_employee_name} ${isAssignedToCurrent ? '(You)' : ''}
                            </span>
                        ` : '<span class="px-2 py-0.5 rounded bg-error-container/30 text-error font-label-sm text-[11px]">Unassigned</span>'}
                    </div>
                    <p class="font-body-sm text-outline">
                        Case: <strong class="font-mono text-on-surface">${r.request_id}</strong> ·
                        CIF: <span class="font-mono">${r.customer_cif}</span> ·
                        Phone: ${r.customer_phone || 'N/A'} ·
                        Submitted: ${formatDate(r.submitted_at)}
                    </p>
                    <p class="font-label-sm text-on-surface-variant">
                        PAN: <span class="font-mono uppercase font-medium">${r.customer_pan || 'N/A'}</span> ·
                        Aadhaar: <span class="font-mono">•••• •••• ${r.customer_aadhaar_last_four || 'XXXX'}</span> ·
                        Monthly Income: <strong class="font-semibold">${formatINR(r.customer_monthly_income)}</strong>
                    </p>
                    ${r.loan_application_id ? `
                        <p class="font-label-sm text-primary-container font-medium pt-0.5">
                            Connected Facility: Loan #${r.loan_application_id} (${formatINR(r.loan_requested_amount)}) · Purpose: ${r.loan_purpose || 'General Credit'}
                        </p>
                    ` : ''}
                    ${r.rejection_reason ? `<p class="font-label-sm text-error font-medium italic pt-0.5">Rejection Reason: "${r.rejection_reason}"</p>` : ''}
                    ${r.review_notes ? `<p class="font-label-sm text-amber-900 font-medium italic pt-0.5">Review Notes: "${r.review_notes}"</p>` : ''}
                </div>
                <div class="flex flex-wrap items-center gap-2 shrink-0">
                    <button type="button" class="btn-emp-kyc-detail px-3 py-1.5 rounded-xl border border-outline-variant/30 text-on-surface hover:bg-surface-container-high font-label-sm font-semibold transition-colors" data-id="${r.id}">
                        Dossier
                    </button>
                    ${r.status !== 'APPROVED' ? `
                        <button type="button" class="btn-emp-kyc-review px-3.5 py-1.5 rounded-xl bg-amber-500/10 text-amber-900 font-label-sm font-semibold hover:bg-amber-500/20 transition-colors" data-id="${r.id}" data-name="${r.customer_name}">
                            Needs Review
                        </button>
                        <button type="button" class="btn-emp-kyc-reject px-3.5 py-1.5 rounded-xl bg-error-container/40 text-error font-label-sm font-semibold hover:bg-error-container transition-colors" data-id="${r.id}" data-name="${r.customer_name}">
                            Reject
                        </button>
                        <button type="button" class="btn-emp-kyc-verify px-4 py-1.5 rounded-xl bg-secondary text-white font-label-sm font-semibold hover:bg-secondary/90 transition-colors flex items-center gap-1" data-id="${r.id}" data-name="${r.customer_name}">
                            <span class="material-symbols-outlined text-[16px]">check_circle</span> Approve
                        </button>
                    ` : ''}
                </div>
            `;
            container.appendChild(item);
        });

        // Wire Dossier
        container.querySelectorAll('.btn-emp-kyc-detail').forEach(btn => {
            btn.onclick = () => {
                const reqId = btn.getAttribute('data-id');
                const r = requests.find(x => String(x.id) === String(reqId));
                if (!r) return;
                showGenericDetailModal({
                    title: `KYC Case Dossier: ${r.customer_name}`,
                    icon: 'badge',
                    contentHtml: `
                        <div class="grid grid-cols-2 gap-4 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Customer CIF</span><strong class="text-on-surface font-semibold font-mono">${r.customer_cif}</strong></div>
                            <div><span class="text-outline text-label-sm block">Full Name</span><strong class="text-on-surface font-semibold">${r.customer_name}</strong></div>
                            <div><span class="text-outline text-label-sm block">PAN Identifier</span><strong class="text-on-surface font-semibold font-mono uppercase">${r.customer_pan || 'N/A'}</strong></div>
                            <div><span class="text-outline text-label-sm block">Aadhaar (Last 4)</span><strong class="text-on-surface font-semibold font-mono">•••• •••• ${r.customer_aadhaar_last_four || 'XXXX'}</strong></div>
                            <div><span class="text-outline text-label-sm block">Monthly Income</span><strong class="text-on-surface font-semibold">${formatINR(r.customer_monthly_income)}</strong></div>
                            <div><span class="text-outline text-label-sm block">Credit Score</span><strong class="text-primary-container font-semibold">${r.customer_credit_score} / 900 (${r.customer_credit_category})</strong></div>
                        </div>
                        <div class="pt-3 space-y-2">
                            <div><span class="text-outline text-label-sm block">Case Tracking ID</span><span class="font-mono text-sm font-bold text-on-surface">${r.request_id}</span></div>
                            <div><span class="text-outline text-label-sm block">Assigned Officer</span><span class="text-sm font-medium text-on-surface">${r.assigned_employee_name || 'Unassigned'} (${r.assigned_employee_designation || 'Staff'})</span></div>
                            <div><span class="text-outline text-label-sm block">Current Status</span><span class="text-sm font-bold text-on-surface">${r.status}</span></div>
                            ${r.loan_application_id ? `<div><span class="text-outline text-label-sm block">Linked Loan Facility</span><span class="text-sm font-medium text-primary-container">Application #${r.loan_application_id} - ${formatINR(r.loan_requested_amount)}</span></div>` : ''}
                            ${r.rejection_reason ? `<div><span class="text-error text-label-sm block">Rejection Justification</span><span class="text-sm font-medium text-error">${r.rejection_reason}</span></div>` : ''}
                            ${r.review_notes ? `<div><span class="text-amber-900 text-label-sm block">Compliance Review Notes</span><span class="text-sm font-medium text-amber-900">${r.review_notes}</span></div>` : ''}
                        </div>
                    `
                });
            };
        });

        // Wire Approve
        container.querySelectorAll('.btn-emp-kyc-verify').forEach(btn => {
            btn.onclick = async () => {
                const reqId = btn.getAttribute('data-id');
                const custName = btn.getAttribute('data-name');
                const notes = await promptActionModal({
                    title: 'Approve Customer KYC',
                    subtitle: `Customer: ${custName}`,
                    desc: 'Confirms that official identity proofs (PAN & Aadhaar) match government registry records. The customer will receive an in-app notification confirming approval.',
                    label: 'Verification Remarks (Optional):',
                    placeholder: 'Official documents reviewed and verified.',
                    confirmText: 'Approve KYC',
                    confirmClass: 'bg-secondary hover:bg-secondary/90',
                    icon: 'verified_user',
                    requireReason: false
                });
                if (notes === null) return;
                try {
                    await ApiService.approveKYCRequest(reqId, notes || 'Verified and approved by banking officer.');
                    alert(`KYC for ${custName} approved successfully.`);
                    await loadEmployeeKYC();
                    await loadEmployeeStats();
                } catch (err) {
                    alert(`Approval failed: ${err.message}`);
                }
            };
        });

        // Wire Needs Review
        container.querySelectorAll('.btn-emp-kyc-review').forEach(btn => {
            btn.onclick = async () => {
                const reqId = btn.getAttribute('data-id');
                const custName = btn.getAttribute('data-name');
                const notes = await promptActionModal({
                    title: 'Flag KYC for Additional Review',
                    subtitle: `Customer: ${custName}`,
                    desc: 'Flags customer dossier for compliance manager scrutiny or customer document clarification. Mandatory notes explaining the requirement are mandatory.',
                    label: 'Mandatory Review Notes / Clarification Required:',
                    placeholder: 'e.g. Income tax return acknowledgement mismatch with salary slip',
                    confirmText: 'Request Clarification',
                    confirmClass: 'bg-amber-600 hover:bg-amber-700',
                    icon: 'warning',
                    requireReason: true
                });
                if (!notes) return;
                try {
                    await ApiService.needsReviewKYCRequest(reqId, notes);
                    alert(`KYC for ${custName} flagged for additional review.`);
                    await loadEmployeeKYC();
                    await loadEmployeeStats();
                } catch (err) {
                    alert(`Action failed: ${err.message}`);
                }
            };
        });

        // Wire Reject
        container.querySelectorAll('.btn-emp-kyc-reject').forEach(btn => {
            btn.onclick = async () => {
                const reqId = btn.getAttribute('data-id');
                const custName = btn.getAttribute('data-name');
                const reason = await promptActionModal({
                    title: 'Reject Customer KYC',
                    subtitle: `Customer: ${custName}`,
                    desc: 'Rejects submitted KYC documentation. The customer will receive an official notification with this justification. Mandatory rejection reason required.',
                    label: 'Mandatory Rejection Reason:',
                    placeholder: 'e.g. Expired government ID / Altered document scan',
                    confirmText: 'Reject KYC',
                    confirmClass: 'bg-error hover:bg-red-700',
                    icon: 'cancel',
                    requireReason: true
                });
                if (!reason) return;
                try {
                    await ApiService.rejectKYCRequest(reqId, reason);
                    alert(`KYC for ${custName} rejected.`);
                    await loadEmployeeKYC();
                    await loadEmployeeStats();
                } catch (err) {
                    alert(`Rejection failed: ${err.message}`);
                }
            };
        });

    } catch (err) {
        console.error('Failed to load KYC requests:', err);
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading KYC queue: ${err.message}</div>`;
    }
}

/**
 * 3. Employee: Customer Lookup & Account Inspection
 */
async function loadEmployeeCustomers(searchQuery = '') {
    const container = document.getElementById('employee-customers-container');
    if (!container) return;

    container.innerHTML = `<div class="p-8 text-center text-outline">Searching customer directory...</div>`;

    try {
        const customers = await ApiService.getCustomers(searchQuery);

        if (!customers || customers.length === 0) {
            container.innerHTML = `
                <div class="p-10 text-center flex flex-col items-center">
                    <span class="material-symbols-outlined text-[40px] text-outline mb-2">person_off</span>
                    <p class="font-headline-sm text-on-surface font-semibold">No Customers Found</p>
                    <p class="font-body-sm text-outline pt-1">Try searching by client name, PAN, account number, or email.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        customers.forEach(c => {
            const item = document.createElement('div');
            item.className = 'p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface-container-low/40 transition-colors';

            const accCount = c.accounts ? c.accounts.length : 0;

            item.innerHTML = `
                <div class="space-y-1">
                    <div class="flex items-center gap-2.5">
                        <span class="font-headline-sm font-bold text-on-surface">${c.name}</span>
                        <span class="px-2 py-0.5 rounded bg-primary-container/10 text-primary-container font-label-sm font-semibold text-[11px]">CIF: ${c.id}</span>
                        <span class="px-2 py-0.5 rounded ${c.kyc_status === 'VERIFIED' ? 'bg-secondary/10 text-secondary' : 'bg-amber-500/10 text-amber-900'} font-label-sm font-semibold text-[11px]">${c.kyc_status}</span>
                    </div>
                    <p class="font-body-sm text-outline">Username: ${c.username} · Phone: ${c.phone || 'N/A'} · Email: ${c.email || 'N/A'}</p>
                    <p class="font-label-sm text-on-surface-variant">PAN: <span class="font-mono uppercase font-medium">${c.pan_number || 'N/A'}</span> · City: ${c.city || 'N/A'} · Accounts: <strong>${accCount} active facility(s)</strong></p>
                </div>
                <div class="shrink-0">
                    <button type="button" class="btn-emp-inspect-customer px-4 py-2 rounded-xl bg-primary-container text-white font-label-sm font-semibold hover:bg-primary transition-colors flex items-center gap-1.5" data-id="${c.id}">
                        <span class="material-symbols-outlined text-[18px]">account_box</span> View Accounts &amp; Profile
                    </button>
                </div>
            `;
            container.appendChild(item);
        });

        container.querySelectorAll('.btn-emp-inspect-customer').forEach(btn => {
            btn.onclick = async () => {
                const cId = btn.getAttribute('data-id');
                btn.disabled = true;
                btn.textContent = 'Loading...';
                try {
                    const detail = await ApiService.getCustomerDetail(cId);
                    const cust = detail.customer;
                    const accounts = detail.accounts || [];
                    const txns = detail.recent_transactions || [];

                    let accountsHtml = accounts.map(a => `
                        <tr class="border-b border-outline-variant/20 hover:bg-surface-container-low/30">
                            <td class="py-2.5 px-3 font-mono font-medium text-on-surface">${a.account_number}</td>
                            <td class="py-2.5 text-on-surface-variant">${a.account_type_name || a.account_type}</td>
                            <td class="py-2.5 text-right font-semibold text-on-surface">${formatINR(a.available_balance)}</td>
                            <td class="py-2.5 text-right text-outline">${formatINR(a.ledger_balance)}</td>
                            <td class="py-2.5 text-center">
                                <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${a.status === 'ACTIVE' ? 'bg-secondary/10 text-secondary' : 'bg-amber-500/10 text-amber-900'}">${a.status}</span>
                            </td>
                        </tr>
                    `).join('');

                    if (accounts.length === 0) {
                        accountsHtml = `<tr><td colspan="5" class="py-4 text-center text-outline">No accounts on record.</td></tr>`;
                    }

                    let txnsHtml = txns.map(t => `
                        <tr class="border-b border-outline-variant/20 hover:bg-surface-container-low/30 text-[12px]">
                            <td class="py-2 px-3 font-mono text-outline">${t.reference_number || t.transaction_id}</td>
                            <td class="py-2 text-outline">${formatDate(t.timestamp)}</td>
                            <td class="py-2 text-on-surface font-medium">${t.beneficiary_name || 'Transfer'}</td>
                            <td class="py-2 text-right font-semibold ${t.transaction_type === 'CREDIT' ? 'text-secondary' : 'text-on-surface'}">${formatINR(t.amount)}</td>
                            <td class="py-2 text-center"><span class="px-1.5 py-0.5 rounded text-[10px] font-semibold ${t.status === 'COMPLETED' ? 'bg-secondary/10 text-secondary' : 'bg-amber-500/10 text-amber-900'}">${t.status}</span></td>
                        </tr>
                    `).join('');

                    if (txns.length === 0) {
                        txnsHtml = `<tr><td colspan="5" class="py-3 text-center text-outline">No recent transactions.</td></tr>`;
                    }

                    showGenericDetailModal({
                        title: `Customer Dossier: ${cust.name}`,
                        icon: 'person_search',
                        contentHtml: `
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-2xl bg-surface-container-low border border-outline-variant/20">
                                <div><span class="text-outline text-[11px] block">Customer ID</span><strong class="font-mono text-on-surface">${cust.id}</strong></div>
                                <div><span class="text-outline text-[11px] block">Phone Number</span><span class="text-on-surface">${cust.phone || 'N/A'}</span></div>
                                <div><span class="text-outline text-[11px] block">PAN Number</span><span class="font-mono uppercase font-semibold text-on-surface">${cust.pan_number || 'N/A'}</span></div>
                                <div><span class="text-outline text-[11px] block">KYC Status</span><span class="font-semibold text-secondary">${cust.kyc_status}</span></div>
                            </div>
                            
                            <div class="pt-4">
                                <h4 class="font-headline-sm text-[16px] font-bold text-on-surface mb-2">Banking Accounts (${accounts.length})</h4>
                                <div class="overflow-x-auto border border-outline-variant/20 rounded-xl">
                                    <table class="w-full text-left text-sm font-body-sm">
                                        <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                                            <tr>
                                                <th class="py-2 px-3">Account Number</th>
                                                <th class="py-2">Type</th>
                                                <th class="py-2 text-right">Available</th>
                                                <th class="py-2 text-right">Ledger</th>
                                                <th class="py-2 text-center">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody class="divide-y divide-outline-variant/10">
                                            ${accountsHtml}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div class="pt-4">
                                <h4 class="font-headline-sm text-[16px] font-bold text-on-surface mb-2">Recent Transactions</h4>
                                <div class="overflow-x-auto border border-outline-variant/20 rounded-xl">
                                    <table class="w-full text-left text-sm font-body-sm">
                                        <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                                            <tr>
                                                <th class="py-2 px-3">Ref #</th>
                                                <th class="py-2">Date</th>
                                                <th class="py-2">Counterparty</th>
                                                <th class="py-2 text-right">Amount</th>
                                                <th class="py-2 text-center">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody class="divide-y divide-outline-variant/10">
                                            ${txnsHtml}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        `
                    });
                } catch (err) {
                    alert(`Failed to load customer profile: ${err.message}`);
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = `<span class="material-symbols-outlined text-[18px]">account_box</span> View Accounts &amp; Profile`;
                }
            };
        });

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error searching directory: ${err.message}</div>`;
    }
}

/**
 * 4. Employee: Real-Time Core Banking Ledger
 */
async function loadEmployeeLedger() {
    const container = document.getElementById('employee-ledger-table-container');
    const searchInput = document.getElementById('employee-ledger-search');
    const catSelect = document.getElementById('employee-ledger-category');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading transaction ledger...</div>`;

    const params = {};
    if (searchInput && searchInput.value.trim()) params.search = searchInput.value.trim();
    if (catSelect && catSelect.value !== 'ALL') params.category = catSelect.value;

    try {
        const txns = await ApiService.getTransactions(params);

        if (!txns || txns.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No ledger transactions match the criteria.</div>`;
            return;
        }

        let rowsHtml = txns.map(t => {
            const isCredit = t.transaction_type === 'CREDIT';
            let badgeClass = 'bg-secondary/10 text-secondary';
            if (t.status === 'REVERSED') badgeClass = 'bg-amber-500/10 text-amber-900';
            if (t.status === 'FAILED') badgeClass = 'bg-error/10 text-error';

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors">
                    <td class="py-3 px-4 font-mono text-[13px] text-on-surface font-medium">${t.reference_number || t.transaction_id}</td>
                    <td class="py-3 px-3 text-outline text-[13px]">${formatDate(t.timestamp)}</td>
                    <td class="py-3 px-3 font-semibold text-on-surface">${t.beneficiary_name || 'Bank Transfer'}</td>
                    <td class="py-3 px-3 text-outline text-[13px]">${t.category}</td>
                    <td class="py-3 px-3 text-right font-financial-numeric font-bold ${isCredit ? 'text-secondary' : 'text-on-surface'}">${formatINR(t.amount)}</td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${badgeClass}">${t.status}</span>
                    </td>
                    <td class="py-3 px-3 text-right">
                        <button type="button" class="btn-ledger-row-detail px-2.5 py-1 rounded-lg border border-outline-variant/30 text-outline hover:text-on-surface font-label-sm" data-id="${t.id}">
                            Inspect
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Txn Reference</th>
                        <th class="py-3 px-3">Date</th>
                        <th class="py-3 px-3">Beneficiary / Party</th>
                        <th class="py-3 px-3">Category</th>
                        <th class="py-3 px-3 text-right">Amount</th>
                        <th class="py-3 px-3 text-center">Status</th>
                        <th class="py-3 px-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

        container.querySelectorAll('.btn-ledger-row-detail').forEach(btn => {
            btn.onclick = () => {
                const tId = btn.getAttribute('data-id');
                const t = txns.find(x => String(x.id) === String(tId));
                if (!t) return;
                showGenericDetailModal({
                    title: `Ledger Entry: ${t.reference_number || t.transaction_id}`,
                    icon: 'receipt_long',
                    contentHtml: `
                        <div class="grid grid-cols-2 gap-4 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Reference #</span><strong class="font-mono text-on-surface">${t.reference_number || t.transaction_id}</strong></div>
                            <div><span class="text-outline text-label-sm block">Status</span><span class="px-2 py-0.5 rounded bg-primary-container/10 text-primary-container font-label-sm font-semibold">${t.status}</span></div>
                            <div><span class="text-outline text-label-sm block">Category / Type</span><span class="text-on-surface font-medium">${t.category} (${t.transaction_type})</span></div>
                            <div><span class="text-outline text-label-sm block">Amount</span><strong class="text-xl font-bold ${t.transaction_type === 'CREDIT' ? 'text-secondary' : 'text-on-surface'}">${formatINR(t.amount)}</strong></div>
                            <div><span class="text-outline text-label-sm block">Timestamp</span><span class="text-on-surface">${new Date(t.timestamp).toLocaleString('en-IN')}</span></div>
                            <div><span class="text-outline text-label-sm block">Balance After</span><span class="text-on-surface font-semibold">${formatINR(t.balance_after)}</span></div>
                        </div>
                        <div class="pt-3">
                            <span class="text-outline text-label-sm block">Remarks / Narrative</span>
                            <p class="text-on-surface font-body-sm pt-1">${t.remarks || 'Standard core banking transfer ledger posting.'}</p>
                        </div>
                    `
                });
            };
        });

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading ledger: ${err.message}</div>`;
    }
}

/**
 * ========================================================
 * ADMIN PORTAL (DBMS MANAGEMENT & OPERATIONS OVERSIGHT)
 * ========================================================
 */
let currentAdminTab = 'metrics';

function initAdminPortal() {
    // Tab switching
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            switchAdminTab(tab);
        });
    });

    // 1. Customer Directory (Sections 18, 19, 20)
    const btnCustFilter = document.getElementById('btn-admin-customers-filter');
    if (btnCustFilter) {
        btnCustFilter.addEventListener('click', () => loadAdminCustomers());
    }
    const searchCustInput = document.getElementById('admin-customers-search');
    if (searchCustInput) {
        searchCustInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') loadAdminCustomers(); });
    }
    const filterCustKyc = document.getElementById('admin-customers-kyc-filter');
    if (filterCustKyc) {
        filterCustKyc.addEventListener('change', () => loadAdminCustomers());
    }

    // 2. Customer Accounts
    const btnAccFilter = document.getElementById('btn-admin-accounts-filter');
    if (btnAccFilter) {
        btnAccFilter.addEventListener('click', () => loadAdminAccounts());
    }

    // 3. Transaction Oversight
    const btnTxnFilter = document.getElementById('btn-admin-txn-filter');
    if (btnTxnFilter) {
        btnTxnFilter.addEventListener('click', () => loadAdminTransactions());
    }

    // 4. Credit Facilities
    const btnLoanFilter = document.getElementById('btn-admin-loans-filter');
    if (btnLoanFilter) {
        btnLoanFilter.addEventListener('click', () => loadAdminLoans());
    }

    // 5. KYC Oversight (Sections 18, 19, 20)
    const btnKycFilter = document.getElementById('btn-admin-kyc-filter');
    if (btnKycFilter) {
        btnKycFilter.addEventListener('click', () => loadAdminKYC());
    }
    const searchKycInput = document.getElementById('admin-kyc-search');
    if (searchKycInput) {
        searchKycInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') loadAdminKYC(); });
    }
    const statusKycSelect = document.getElementById('admin-kyc-status');
    if (statusKycSelect) {
        statusKycSelect.addEventListener('change', () => loadAdminKYC());
    }

    // 6. Employees & Workload (Sections 18, 19, 20)
    const btnEmpFilter = document.getElementById('btn-admin-employees-filter');
    if (btnEmpFilter) {
        btnEmpFilter.addEventListener('click', () => loadAdminEmployees());
    }
    const searchEmpInput = document.getElementById('admin-employees-search');
    if (searchEmpInput) {
        searchEmpInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') loadAdminEmployees(); });
    }

    // 7. Audit Log
    const btnAuditFilter = document.getElementById('btn-admin-audit-filter');
    if (btnAuditFilter) {
        btnAuditFilter.addEventListener('click', () => loadAdminAuditLogs());
    }

    // 8. Branch Facilities
    const btnAddBranch = document.getElementById('btn-admin-add-branch');
    if (btnAddBranch) {
        btnAddBranch.addEventListener('click', () => showBranchFormModal(null));
    }
    const btnBranchFilter = document.getElementById('btn-admin-branches-filter');
    if (btnBranchFilter) {
        btnBranchFilter.addEventListener('click', () => loadAdminBranches());
    }
    const searchBranchInput = document.getElementById('admin-branches-search');
    if (searchBranchInput) {
        searchBranchInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') loadAdminBranches(); });
    }
    const statusBranchSelect = document.getElementById('admin-branches-status');
    if (statusBranchSelect) {
        statusBranchSelect.addEventListener('change', () => loadAdminBranches());
    }
}

async function switchAdminTab(tab) {
    currentAdminTab = tab;

    // Subtab buttons
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === tab) {
            btn.classList.add('active', 'text-primary-container', 'bg-surface-container-lowest', 'shadow-sm', 'font-semibold');
            btn.classList.remove('text-outline', 'font-medium');
        } else {
            btn.classList.remove('active', 'text-primary-container', 'bg-surface-container-lowest', 'shadow-sm', 'font-semibold');
            btn.classList.add('text-outline', 'font-medium');
        }
    });

    // Sidebar items
    document.querySelectorAll('.admin-nav-item').forEach(link => {
        if (link.getAttribute('data-admin-tab') === tab) {
            link.classList.remove('text-on-surface-variant', 'font-label-md');
            link.classList.add('bg-surface-container-low', 'text-primary-container', 'font-semibold');
        } else {
            link.classList.remove('bg-surface-container-low', 'text-primary-container', 'font-semibold');
            link.classList.add('text-on-surface-variant', 'font-label-md');
        }
    });

    // Panels
    document.querySelectorAll('.admin-tab-panel').forEach(p => p.classList.add('hidden'));
    const panel = document.getElementById(`admin-panel-${tab}`);
    if (panel) panel.classList.remove('hidden');

    if (tab === 'metrics') await loadAdminOverview();
    else if (tab === 'customers') await loadAdminCustomers();
    else if (tab === 'accounts') await loadAdminAccounts();
    else if (tab === 'transactions') await loadAdminTransactions();
    else if (tab === 'loans') await loadAdminLoans();
    else if (tab === 'kyc') await loadAdminKYC();
    else if (tab === 'employees') await loadAdminEmployees();
    else if (tab === 'branches') await loadAdminBranches();
    else if (tab === 'audit') await loadAdminAuditLogs();
}

/**
 * 1. Admin: System Metrics & Database Overview
 */
async function loadAdminOverview() {
    try {
        const stats = await ApiService.getAdminStats();

        const cEl = document.getElementById('admin-stat-customers');
        const kycEl = document.getElementById('admin-stat-kyc-pending');
        const aEl = document.getElementById('admin-stat-accounts');
        const aSubEl = document.getElementById('admin-stat-accounts-sub');
        const dEl = document.getElementById('admin-stat-deposits');
        const wEl = document.getElementById('admin-stat-withdrawals');
        const lEl = document.getElementById('admin-stat-loans');
        const lSubEl = document.getElementById('admin-stat-loans-sub');
        const vEl = document.getElementById('admin-stat-volume');
        const tEl = document.getElementById('admin-stat-txn-count');
        const bEl = document.getElementById('admin-stat-branches');

        if (cEl) cEl.textContent = stats.total_customers;
        if (kycEl) kycEl.textContent = `Pending KYC: ${stats.pending_kyc || 0}`;
        if (aEl) aEl.textContent = stats.total_accounts;
        if (aSubEl) aSubEl.textContent = `Active: ${stats.active_accounts || 0} · Frozen: ${stats.frozen_accounts || 0} · Closed: ${stats.closed_accounts || 0}`;
        if (dEl) dEl.textContent = formatINR(stats.total_deposits, false);
        if (wEl) wEl.textContent = `Total Outflows: ${formatINR(stats.total_withdrawals || 0, false)}`;
        if (lEl) lEl.textContent = formatINR(stats.total_outstanding_loans, false);
        if (lSubEl) lSubEl.textContent = `Active Facilities: ${stats.active_loans || 0} · Queue: ${stats.pending_loan_applications || 0}`;
        if (vEl) vEl.textContent = formatINR(stats.total_transaction_volume || 0, false);
        if (tEl) tEl.textContent = `${stats.total_transactions || 0} Txns (${stats.failed_transactions || 0} Failed, ${stats.reversed_transactions || 0} Reversed)`;
        if (bEl) bEl.textContent = `${stats.total_branches || 1} Active Branches`;

    } catch (err) {
        console.error('Failed to load admin stats:', err);
    }
}

/**
 * 2. Admin: Customer Directory & Relationship Management (Sections 18, 19, 20)
 */
async function loadAdminCustomers() {
    const container = document.getElementById('admin-customers-table-container');
    const searchInput = document.getElementById('admin-customers-search');
    const filterEl = document.getElementById('admin-customers-kyc-filter');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading customers...</div>`;

    const searchVal = searchInput ? searchInput.value.trim() : '';
    const kycVal = filterEl ? filterEl.value : 'ALL';

    try {
        const customers = await ApiService.getCustomers(searchVal, kycVal);

        if (!customers || customers.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No customer records found matching filter.</div>`;
            return;
        }

        let rowsHtml = customers.map(c => {
            let kycBadge = 'bg-amber-500/10 text-amber-900';
            if (c.kyc_status === 'VERIFIED') kycBadge = 'bg-secondary/10 text-secondary';
            if (c.kyc_status === 'REJECTED') kycBadge = 'bg-error/10 text-error';
            if (c.kyc_status === 'NEEDS_REVIEW') kycBadge = 'bg-amber-900/10 text-amber-900';

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors">
                    <td class="py-3 px-4">
                        <strong class="text-on-surface font-semibold block">${c.name}</strong>
                        <span class="text-[11px] text-outline font-mono">CIF: ${c.id} · @${c.username}</span>
                    </td>
                    <td class="py-3 px-3">
                        <span class="text-on-surface font-medium block">${c.phone || 'N/A'}</span>
                        <span class="text-[11px] text-outline">${c.email || 'N/A'}</span>
                    </td>
                    <td class="py-3 px-3">
                        <span class="font-mono text-on-surface font-medium block uppercase">${c.pan_number || 'PAN Pending'}</span>
                        <span class="text-[11px] text-outline">Aadhaar: •••• ${c.aadhaar_last_four || 'XXXX'}</span>
                    </td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2.5 py-0.5 rounded text-[11px] font-semibold uppercase ${kycBadge}">${c.kyc_status}</span>
                    </td>
                    <td class="py-3 px-3 text-center">
                        <span class="font-semibold text-primary-container">${c.credit_score}</span>
                        <span class="text-[11px] text-outline block">${c.credit_category || 'N/A'}</span>
                    </td>
                    <td class="py-3 px-3 text-right font-financial-numeric font-bold text-on-surface">${formatINR(c.monthly_income)}</td>
                    <td class="py-3 px-4 text-right">
                        <button type="button" class="btn-adm-cust-detail px-3 py-1 rounded-lg border border-outline-variant/30 text-on-surface hover:bg-surface-container-high font-label-sm font-semibold transition-colors" data-id="${c.id}">
                            Dossier
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Customer Name &amp; CIF</th>
                        <th class="py-3 px-3">Contact</th>
                        <th class="py-3 px-3">Government ID</th>
                        <th class="py-3 px-3 text-center">KYC Status</th>
                        <th class="py-3 px-3 text-center">Credit Score</th>
                        <th class="py-3 px-3 text-right">Monthly Income</th>
                        <th class="py-3 px-4 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

        container.querySelectorAll('.btn-adm-cust-detail').forEach(btn => {
            btn.onclick = () => {
                const cId = btn.getAttribute('data-id');
                const c = customers.find(x => String(x.id) === String(cId));
                if (!c) return;
                showGenericDetailModal({
                    title: `Customer Record: ${c.name}`,
                    icon: 'person',
                    contentHtml: `
                        <div class="grid grid-cols-2 gap-4 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Full Legal Name</span><strong class="text-on-surface font-semibold">${c.name}</strong></div>
                            <div><span class="text-outline text-label-sm block">Customer Identifier</span><strong class="text-on-surface font-semibold font-mono">${c.id}</strong></div>
                            <div><span class="text-outline text-label-sm block">PAN Card</span><strong class="text-on-surface font-semibold font-mono uppercase">${c.pan_number || 'N/A'}</strong></div>
                            <div><span class="text-outline text-label-sm block">Aadhaar (Last 4)</span><strong class="text-on-surface font-semibold font-mono">•••• •••• ${c.aadhaar_last_four || 'XXXX'}</strong></div>
                            <div><span class="text-outline text-label-sm block">KYC Verification</span><strong class="text-on-surface font-semibold">${c.kyc_status}</strong></div>
                            <div><span class="text-outline text-label-sm block">Credit Profile</span><strong class="text-primary-container font-semibold">${c.credit_score} / 900 (${c.credit_category})</strong></div>
                        </div>
                        <div class="pt-3 space-y-1">
                            <div><span class="text-outline text-label-sm block">Registered Address</span><span class="text-sm font-medium text-on-surface">${c.address || 'N/A'}, ${c.city || ''} ${c.state || ''} - ${c.pincode || ''}</span></div>
                            <div><span class="text-outline text-label-sm block">Phone &amp; Email</span><span class="text-sm font-medium text-on-surface">${c.phone || 'N/A'} · ${c.email || 'N/A'}</span></div>
                        </div>
                    `
                });
            };
        });

    } catch (err) {
        console.error('Failed to load admin customers:', err);
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading customers: ${err.message}</div>`;
    }
}

/**
 * 3. Admin: Customer & Account Controls (Freeze / Unfreeze / Activate / Deactivate)
 */
async function loadAdminAccounts() {
    const container = document.getElementById('admin-accounts-table-container');
    const searchInput = document.getElementById('admin-accounts-search');
    const statusSelect = document.getElementById('admin-accounts-status');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading customer accounts...</div>`;

    const params = {};
    if (searchInput && searchInput.value.trim()) params.search = searchInput.value.trim();
    if (statusSelect && statusSelect.value !== 'ALL') params.status = statusSelect.value;

    try {
        const accounts = await ApiService.getAccounts(params);

        if (!accounts || accounts.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No accounts found matching filter.</div>`;
            return;
        }

        let rowsHtml = accounts.map(a => {
            let statusBadge = 'bg-secondary/10 text-secondary';
            if (a.status === 'FROZEN') statusBadge = 'bg-amber-500/10 text-amber-900';
            if (a.status === 'CLOSED') statusBadge = 'bg-error/10 text-error';

            let actionBtns = '';
            if (a.status === 'ACTIVE') {
                actionBtns = `
                    <button type="button" class="btn-adm-freeze px-3 py-1 rounded-lg bg-amber-500/10 text-amber-900 font-label-sm font-semibold hover:bg-amber-500/20 transition-colors" data-id="${a.id}" data-num="${a.account_number}">
                        Freeze
                    </button>
                    <button type="button" class="btn-adm-deactivate px-3 py-1 rounded-lg bg-error-container/40 text-error font-label-sm font-semibold hover:bg-error-container transition-colors" data-id="${a.id}" data-num="${a.account_number}">
                        Deactivate
                    </button>
                `;
            } else if (a.status === 'FROZEN') {
                actionBtns = `
                    <button type="button" class="btn-adm-unfreeze px-3 py-1 rounded-lg bg-secondary text-white font-label-sm font-semibold hover:bg-secondary/90 transition-colors" data-id="${a.id}" data-num="${a.account_number}">
                        Unfreeze
                    </button>
                    <button type="button" class="btn-adm-deactivate px-3 py-1 rounded-lg bg-error-container/40 text-error font-label-sm font-semibold hover:bg-error-container transition-colors" data-id="${a.id}" data-num="${a.account_number}">
                        Deactivate
                    </button>
                `;
            } else if (a.status === 'CLOSED') {
                actionBtns = `
                    <button type="button" class="btn-adm-activate px-3 py-1 rounded-lg bg-primary-container text-white font-label-sm font-semibold hover:bg-primary transition-colors" data-id="${a.id}" data-num="${a.account_number}">
                        Re-activate
                    </button>
                `;
            }

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors">
                    <td class="py-3 px-4">
                        <strong class="font-mono text-on-surface font-semibold block">${a.account_number}</strong>
                        <span class="text-[11px] text-outline">${a.account_type_name || a.account_type}</span>
                    </td>
                    <td class="py-3 px-3">
                        <strong class="text-on-surface font-semibold block">${a.customer_name || 'Account Holder'}</strong>
                        <span class="text-[11px] text-outline font-mono">${a.pan_number || 'PAN Pending'}</span>
                    </td>
                    <td class="py-3 px-3 text-right font-financial-numeric font-bold text-on-surface">${formatINR(a.available_balance)}</td>
                    <td class="py-3 px-3 text-right text-outline font-medium">${formatINR(a.ledger_balance)}</td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2.5 py-0.5 rounded text-[11px] font-semibold uppercase ${statusBadge}">${a.status}</span>
                    </td>
                    <td class="py-3 px-4 text-right">
                        <div class="flex items-center justify-end gap-1.5">
                            ${actionBtns}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Account Number &amp; Scheme</th>
                        <th class="py-3 px-3">Customer &amp; Identity</th>
                        <th class="py-3 px-3 text-right">Available Balance</th>
                        <th class="py-3 px-3 text-right">Ledger Balance</th>
                        <th class="py-3 px-3 text-center">Status</th>
                        <th class="py-3 px-4 text-right">Administrative Controls</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

        // Bind Freeze
        container.querySelectorAll('.btn-adm-freeze').forEach(btn => {
            btn.onclick = async () => {
                const accId = btn.getAttribute('data-id');
                const accNum = btn.getAttribute('data-num');
                const reason = await promptActionModal({
                    title: 'Freeze Customer Account',
                    subtitle: `Account #${accNum}`,
                    desc: 'Freezing immediately halts debit transfers and outgoing withdrawals to prevent financial fraud while preserving positive balance integrity.',
                    label: 'Mandatory Compliance Freeze Reason:',
                    placeholder: 'e.g. Unusual high-velocity transfer activity flagged by AML rule engine',
                    confirmText: 'Freeze Account',
                    confirmClass: 'bg-amber-600 hover:bg-amber-700',
                    icon: 'lock',
                    requireReason: true
                });
                if (!reason) return;
                try {
                    await ApiService.freezeAccount(accId, reason);
                    alert(`Account #${accNum} frozen successfully.`);
                    await loadAdminAccounts();
                    await loadAdminOverview();
                } catch (err) {
                    alert(`Freeze action failed: ${err.message}`);
                }
            };
        });

        // Bind Unfreeze
        container.querySelectorAll('.btn-adm-unfreeze').forEach(btn => {
            btn.onclick = async () => {
                const accId = btn.getAttribute('data-id');
                const accNum = btn.getAttribute('data-num');
                const reason = await promptActionModal({
                    title: 'Unfreeze Customer Account',
                    subtitle: `Account #${accNum}`,
                    desc: 'Restores transacting permissions to the customer account.',
                    label: 'Mandatory Resolution Reason:',
                    placeholder: 'e.g. Identity re-verified and compliance investigation cleared',
                    confirmText: 'Unfreeze Account',
                    confirmClass: 'bg-secondary hover:bg-secondary/90',
                    icon: 'lock_open',
                    requireReason: true
                });
                if (!reason) return;
                try {
                    await ApiService.unfreezeAccount(accId, reason);
                    alert(`Account #${accNum} unfrozen successfully.`);
                    await loadAdminAccounts();
                    await loadAdminOverview();
                } catch (err) {
                    alert(`Unfreeze action failed: ${err.message}`);
                }
            };
        });

        // Bind Deactivate
        container.querySelectorAll('.btn-adm-deactivate').forEach(btn => {
            btn.onclick = async () => {
                const accId = btn.getAttribute('data-id');
                const accNum = btn.getAttribute('data-num');
                const reason = await promptActionModal({
                    title: 'Deactivate Banking Account',
                    subtitle: `Account #${accNum}`,
                    desc: 'Marks account as CLOSED. Account cannot perform transacting operations until administratively reactivated.',
                    label: 'Mandatory Deactivation Reason:',
                    placeholder: 'e.g. Customer request or administrative branch closure',
                    confirmText: 'Deactivate Account',
                    confirmClass: 'bg-error hover:bg-red-700',
                    icon: 'block',
                    requireReason: true
                });
                if (!reason) return;
                try {
                    await ApiService.deactivateAccount(accId, reason);
                    alert(`Account #${accNum} deactivated.`);
                    await loadAdminAccounts();
                    await loadAdminOverview();
                } catch (err) {
                    alert(`Deactivation failed: ${err.message}`);
                }
            };
        });

        // Bind Activate
        container.querySelectorAll('.btn-adm-activate').forEach(btn => {
            btn.onclick = async () => {
                const accId = btn.getAttribute('data-id');
                const accNum = btn.getAttribute('data-num');
                const reason = await promptActionModal({
                    title: 'Activate Banking Account',
                    subtitle: `Account #${accNum}`,
                    desc: 'Restores CLOSED account back to ACTIVE operational status.',
                    label: 'Activation Reason:',
                    placeholder: 'Re-activated upon customer formal written petition',
                    confirmText: 'Activate Account',
                    confirmClass: 'bg-primary-container hover:bg-primary',
                    icon: 'check_circle',
                    requireReason: true
                });
                if (!reason) return;
                try {
                    await ApiService.activateAccount(accId, reason);
                    alert(`Account #${accNum} activated.`);
                    await loadAdminAccounts();
                    await loadAdminOverview();
                } catch (err) {
                    alert(`Activation failed: ${err.message}`);
                }
            };
        });

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading accounts: ${err.message}</div>`;
    }
}

/**
 * 3. Admin: Transaction Oversight & Compensating Reversals
 */
async function loadAdminTransactions() {
    const container = document.getElementById('admin-txn-table-container');
    const searchInput = document.getElementById('admin-txn-search');
    const statusSelect = document.getElementById('admin-txn-status');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading transactions...</div>`;

    const params = {};
    if (searchInput && searchInput.value.trim()) params.search = searchInput.value.trim();
    if (statusSelect && statusSelect.value !== 'ALL') params.status = statusSelect.value;

    try {
        const txns = await ApiService.getTransactions(params);

        if (!txns || txns.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No transactions found matching filter.</div>`;
            return;
        }

        let rowsHtml = txns.map(t => {
            const isCredit = t.transaction_type === 'CREDIT';
            let badgeClass = 'bg-secondary/10 text-secondary';
            if (t.status === 'REVERSED') badgeClass = 'bg-amber-500/10 text-amber-900';
            if (t.status === 'FAILED') badgeClass = 'bg-error/10 text-error';

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors">
                    <td class="py-3 px-4 font-mono text-[13px] text-on-surface font-medium">${t.reference_number || t.transaction_id}</td>
                    <td class="py-3 px-3 text-outline text-[13px]">${formatDate(t.timestamp)}</td>
                    <td class="py-3 px-3 font-semibold text-on-surface">${t.beneficiary_name || 'Transfer'}</td>
                    <td class="py-3 px-3 text-outline text-[13px]">${t.category} (${t.transaction_type})</td>
                    <td class="py-3 px-3 text-right font-financial-numeric font-bold ${isCredit ? 'text-secondary' : 'text-on-surface'}">${formatINR(t.amount)}</td>
                    <td class="py-3 px-3 text-right font-mono text-outline text-[13px]">${formatINR(t.balance_after)}</td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2 py-0.5 rounded text-[11px] font-semibold uppercase ${badgeClass}">${t.status}</span>
                    </td>
                    <td class="py-3 px-4 text-right">
                        <div class="flex items-center justify-end gap-1.5">
                            <button type="button" class="btn-adm-txn-inspect px-2.5 py-1 rounded-lg border border-outline-variant/30 text-outline hover:text-on-surface font-label-sm" data-id="${t.id}">
                                Audit
                            </button>
                            ${t.status === 'COMPLETED' ? `
                                <button type="button" class="btn-adm-txn-reverse px-2.5 py-1 rounded-lg bg-error-container/40 text-error hover:bg-error-container font-label-sm font-semibold transition-colors" data-id="${t.id}" data-ref="${t.reference_number || t.transaction_id}" data-amount="${t.amount}">
                                    Reverse
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Txn Reference</th>
                        <th class="py-3 px-3">Date</th>
                        <th class="py-3 px-3">Counterparty</th>
                        <th class="py-3 px-3">Category</th>
                        <th class="py-3 px-3 text-right">Amount</th>
                        <th class="py-3 px-3 text-right">Balance After</th>
                        <th class="py-3 px-3 text-center">Status</th>
                        <th class="py-3 px-4 text-right">Admin Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

        // Bind Inspect
        container.querySelectorAll('.btn-adm-txn-inspect').forEach(btn => {
            btn.onclick = () => {
                const tId = btn.getAttribute('data-id');
                const t = txns.find(x => String(x.id) === String(tId));
                if (!t) return;
                showGenericDetailModal({
                    title: `Audit Ledger: ${t.reference_number || t.transaction_id}`,
                    icon: 'receipt_long',
                    contentHtml: `
                        <div class="grid grid-cols-2 gap-4 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Reference Number</span><strong class="font-mono text-on-surface">${t.reference_number || t.transaction_id}</strong></div>
                            <div><span class="text-outline text-label-sm block">Status</span><span class="px-2 py-0.5 rounded bg-primary-container/10 text-primary-container font-label-sm font-semibold">${t.status}</span></div>
                            <div><span class="text-outline text-label-sm block">Counterparty / Beneficiary</span><strong class="text-on-surface">${t.beneficiary_name || 'N/A'}</strong></div>
                            <div><span class="text-outline text-label-sm block">Amount</span><strong class="text-xl font-bold text-secondary">${formatINR(t.amount)}</strong></div>
                            <div><span class="text-outline text-label-sm block">Timestamp</span><span class="text-on-surface">${new Date(t.timestamp).toLocaleString('en-IN')}</span></div>
                            <div><span class="text-outline text-label-sm block">Balance Following Txn</span><span class="text-on-surface font-semibold">${formatINR(t.balance_after)}</span></div>
                        </div>
                        <div class="pt-3">
                            <span class="text-outline text-label-sm block">Remarks &amp; Audit Reference</span>
                            <p class="text-on-surface font-body-sm pt-1">${t.remarks || 'Standard ledger transaction record.'}</p>
                        </div>
                    `
                });
            };
        });

        // Bind Reversal
        container.querySelectorAll('.btn-adm-txn-reverse').forEach(btn => {
            btn.onclick = async () => {
                const tId = btn.getAttribute('data-id');
                const ref = btn.getAttribute('data-ref');
                const amt = btn.getAttribute('data-amount');

                const reason = await promptActionModal({
                    title: 'Execute Financial Transaction Reversal',
                    subtitle: `Ref #${ref} (${formatINR(amt)})`,
                    desc: 'This ACID operation restores debited funds to the sender, claws back credited funds from the counterparty (verifying solvency), marks the original transaction as REVERSED, issues a compensating ledger entry, and creates an immutable regulatory audit log.',
                    label: 'Mandatory Regulatory Reversal Reason:',
                    placeholder: 'e.g. Erroneous duplicate debit requested by customer / fraudulent transfer clawback',
                    confirmText: 'Execute Reversal',
                    confirmClass: 'bg-error hover:bg-red-700',
                    icon: 'history',
                    requireReason: true
                });
                if (!reason) return;

                try {
                    const result = await ApiService.reverseTransaction(tId, reason);
                    alert(`Transaction #${ref} reversed successfully!\nCompensating Reversal Ref: ${result.reversal_reference}`);
                    await loadAdminTransactions();
                    await loadAdminAccounts();
                    await loadAdminOverview();
                } catch (err) {
                    alert(`Reversal failed: ${err.message}`);
                }
            };
        });

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading transactions: ${err.message}</div>`;
    }
}

/**
 * 4. Admin: Credit Facilities Management
 */
async function loadAdminLoans() {
    const container = document.getElementById('admin-loans-table-container');
    const statusSelect = document.getElementById('admin-loans-status');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading credit facilities...</div>`;

    const params = {};
    if (statusSelect && statusSelect.value !== 'ALL') params.status = statusSelect.value;

    try {
        const loans = await ApiService.getLoans(params);

        if (!loans || loans.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No credit facilities matching the selected filter.</div>`;
            return;
        }

        let rowsHtml = loans.map(l => {
            let badgeClass = 'bg-secondary/10 text-secondary';
            if (l.status === 'UNDER_REVIEW') badgeClass = 'bg-amber-500/10 text-amber-900';
            if (l.status === 'CLOSED') badgeClass = 'bg-outline/10 text-outline';
            if (l.status === 'DEFAULTED') badgeClass = 'bg-error/10 text-error';

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors">
                    <td class="py-3 px-4 font-mono font-medium text-on-surface">
                        ${l.loan_id}
                        <span class="block text-[11px] text-outline font-sans">${l.loan_type_name || l.loan_type}</span>
                    </td>
                    <td class="py-3 px-3 font-semibold text-on-surface">${l.borrower_name || 'Borrower'}</td>
                    <td class="py-3 px-3 text-right font-financial-numeric font-bold text-on-surface">${formatINR(l.principal_amount, false)}</td>
                    <td class="py-3 px-3 text-right font-financial-numeric font-bold text-primary-container">${formatINR(l.outstanding_principal, false)}</td>
                    <td class="py-3 px-3 text-right font-medium text-on-surface">${formatINR(l.emi_amount, false)}/mo</td>
                    <td class="py-3 px-3 text-center text-outline text-[13px]">${l.interest_rate}% · ${l.tenure_months}M</td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2 py-0.5 rounded text-[11px] font-semibold uppercase ${badgeClass}">${l.status.replace('_', ' ')}</span>
                    </td>
                    <td class="py-3 px-4 text-right">
                        <div class="flex items-center justify-end gap-1.5">
                            <button type="button" class="btn-adm-loan-schedule px-2.5 py-1 rounded-lg border border-outline-variant/30 text-outline hover:text-on-surface font-label-sm" data-id="${l.id}">
                                Repayments
                            </button>
                            <button type="button" class="btn-adm-loan-status px-2.5 py-1 rounded-lg bg-surface-container-low hover:bg-surface-container-high text-on-surface font-label-sm font-semibold transition-colors" data-id="${l.id}" data-lid="${l.loan_id}" data-status="${l.status}">
                                Status
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Facility ID &amp; Type</th>
                        <th class="py-3 px-3">Borrower</th>
                        <th class="py-3 px-3 text-right">Sanctioned Principal</th>
                        <th class="py-3 px-3 text-right">Outstanding</th>
                        <th class="py-3 px-3 text-right">EMI</th>
                        <th class="py-3 px-3 text-center">Rate / Tenure</th>
                        <th class="py-3 px-3 text-center">Status</th>
                        <th class="py-3 px-4 text-right">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

        // Bind Repayment Schedule
        container.querySelectorAll('.btn-adm-loan-schedule').forEach(btn => {
            btn.onclick = async () => {
                const loanId = btn.getAttribute('data-id');
                btn.disabled = true;
                try {
                    const payments = await ApiService.getLoanPayments(loanId);
                    let payRows = payments.map(p => `
                        <tr class="border-b border-outline-variant/10 text-[12px]">
                            <td class="py-2 px-3 font-mono">${p.installment_number || 1}</td>
                            <td class="py-2">${formatDate(p.payment_date)}</td>
                            <td class="py-2 text-right font-semibold">${formatINR(p.amount_paid)}</td>
                            <td class="py-2 text-right text-outline">${formatINR(p.principal_component)}</td>
                            <td class="py-2 text-right text-outline">${formatINR(p.interest_component)}</td>
                            <td class="py-2 text-center"><span class="px-1.5 py-0.5 rounded text-[10px] bg-secondary/10 text-secondary font-semibold">${p.payment_status || 'PAID'}</span></td>
                        </tr>
                    `).join('');

                    if (payments.length === 0) {
                        payRows = `<tr><td colspan="6" class="py-4 text-center text-outline">No repayments recorded yet for this facility.</td></tr>`;
                    }

                    showGenericDetailModal({
                        title: `Repayment Ledger: Facility #${loanId}`,
                        icon: 'payments',
                        contentHtml: `
                            <div class="overflow-x-auto border border-outline-variant/20 rounded-xl">
                                <table class="w-full text-left text-sm font-body-sm">
                                    <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                                        <tr>
                                            <th class="py-2 px-3">Inst #</th>
                                            <th class="py-2">Date</th>
                                            <th class="py-2 text-right">Amount Paid</th>
                                            <th class="py-2 text-right">Principal</th>
                                            <th class="py-2 text-right">Interest</th>
                                            <th class="py-2 text-center">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-outline-variant/10">
                                        ${payRows}
                                    </tbody>
                                </table>
                            </div>
                        `
                    });
                } catch (err) {
                    alert(`Failed to load repayment schedule: ${err.message}`);
                } finally {
                    btn.disabled = false;
                }
            };
        });

        // Bind Status Update
        container.querySelectorAll('.btn-adm-loan-status').forEach(btn => {
            btn.onclick = async () => {
                const loanId = btn.getAttribute('data-id');
                const loanRef = btn.getAttribute('data-lid');
                const curStatus = btn.getAttribute('data-status');

                const newStatus = prompt(`Update Status for Facility #${loanRef}\nCurrent: ${curStatus}\nEnter new status [ACTIVE, UNDER_REVIEW, CLOSED, DEFAULTED]:`, curStatus);
                if (!newStatus || newStatus === curStatus) return;

                const validStatuses = ['ACTIVE', 'UNDER_REVIEW', 'CLOSED', 'DEFAULTED'];
                if (!validStatuses.includes(newStatus.toUpperCase())) {
                    alert(`Invalid status. Must be one of: ${validStatuses.join(', ')}`);
                    return;
                }

                const reason = await promptActionModal({
                    title: 'Update Loan Facility Status',
                    subtitle: `Facility #${loanRef} -> ${newStatus.toUpperCase()}`,
                    desc: 'Updates the regulatory operating state of this credit facility.',
                    label: 'Mandatory Supervisory Reason:',
                    placeholder: 'e.g. Account suspended due to non-repayment notice / Facility settled in full',
                    confirmText: 'Update Facility',
                    confirmClass: 'bg-primary-container hover:bg-primary',
                    icon: 'real_estate_agent',
                    requireReason: true
                });
                if (!reason) return;

                try {
                    await ApiService.updateLoanStatus(loanId, newStatus.toUpperCase(), reason);
                    alert(`Loan #${loanRef} status updated to ${newStatus.toUpperCase()}!`);
                    await loadAdminLoans();
                    await loadAdminOverview();
                } catch (err) {
                    alert(`Status update failed: ${err.message}`);
                }
            };
        });

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading loans: ${err.message}</div>`;
    }
}

/**
 * 5. Admin: Institutional KYC & Verification Oversight (Sections 18, 19, 20)
 */
async function loadAdminKYC() {
    const container = document.getElementById('admin-kyc-table-container');
    const searchInput = document.getElementById('admin-kyc-search');
    const statusSelect = document.getElementById('admin-kyc-status');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading KYC requests...</div>`;

    const params = {};
    if (searchInput && searchInput.value.trim()) params.search = searchInput.value.trim();
    if (statusSelect && statusSelect.value !== 'ALL') params.status = statusSelect.value;

    try {
        const requests = await ApiService.getKYCRequests(params);

        if (!requests || requests.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No KYC requests found matching filter.</div>`;
            return;
        }

        let rowsHtml = requests.map(r => {
            let badgeClass = 'bg-amber-500/10 text-amber-900';
            if (r.status === 'APPROVED') badgeClass = 'bg-secondary/10 text-secondary';
            if (r.status === 'REJECTED') badgeClass = 'bg-error/10 text-error';
            if (r.status === 'NEEDS_REVIEW') badgeClass = 'bg-amber-900/10 text-amber-900';
            if (r.status === 'ASSIGNED') badgeClass = 'bg-primary-container/10 text-primary-container';

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors">
                    <td class="py-3 px-4">
                        <strong class="font-mono text-on-surface font-semibold block">${r.request_id}</strong>
                        <span class="text-[11px] text-outline">Sub: ${formatDate(r.submitted_at)}</span>
                    </td>
                    <td class="py-3 px-3">
                        <strong class="text-on-surface font-semibold block">${r.customer_name}</strong>
                        <span class="text-[11px] text-outline font-mono">CIF: ${r.customer_cif}</span>
                    </td>
                    <td class="py-3 px-3">
                        <span class="text-on-surface font-medium block">${r.assigned_employee_name || 'Unassigned'}</span>
                        <span class="text-[11px] text-outline">${r.assigned_employee_designation || 'Pending Queue'}</span>
                    </td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2.5 py-0.5 rounded text-[11px] font-semibold uppercase ${badgeClass}">${r.status}</span>
                    </td>
                    <td class="py-3 px-3">
                        ${r.loan_application_id ? `
                            <span class="font-mono text-primary-container font-semibold block">App #${r.loan_application_id}</span>
                            <span class="text-[11px] text-outline">${formatINR(r.loan_requested_amount)}</span>
                        ` : '<span class="text-outline text-[11px]">Direct Onboarding</span>'}
                    </td>
                    <td class="py-3 px-3">
                        <span class="text-outline text-xs block">${r.reviewed_at ? formatDate(r.reviewed_at) : 'Awaiting Review'}</span>
                        ${r.rejection_reason ? `<span class="text-error text-[11px] truncate block max-w-xs" title="${r.rejection_reason}">Reason: ${r.rejection_reason}</span>` : ''}
                        ${r.review_notes ? `<span class="text-amber-900 text-[11px] truncate block max-w-xs" title="${r.review_notes}">Notes: ${r.review_notes}</span>` : ''}
                    </td>
                    <td class="py-3 px-4 text-right">
                        <button type="button" class="btn-adm-kyc-detail px-3 py-1 rounded-lg border border-outline-variant/30 text-on-surface hover:bg-surface-container-high font-label-sm font-semibold transition-colors" data-id="${r.id}">
                            Inspect
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Request ID &amp; Date</th>
                        <th class="py-3 px-3">Customer &amp; CIF</th>
                        <th class="py-3 px-3">Assigned Officer</th>
                        <th class="py-3 px-3 text-center">Status</th>
                        <th class="py-3 px-3">Linked Loan</th>
                        <th class="py-3 px-3">Audit Details</th>
                        <th class="py-3 px-4 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

        container.querySelectorAll('.btn-adm-kyc-detail').forEach(btn => {
            btn.onclick = () => {
                const reqId = btn.getAttribute('data-id');
                const r = requests.find(x => String(x.id) === String(reqId));
                if (!r) return;
                showGenericDetailModal({
                    title: `KYC Audit: ${r.request_id}`,
                    icon: 'verified_user',
                    contentHtml: `
                        <div class="grid grid-cols-2 gap-4 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Applicant Name</span><strong class="text-on-surface font-semibold">${r.customer_name}</strong></div>
                            <div><span class="text-outline text-label-sm block">CIF Identifier</span><strong class="text-on-surface font-semibold font-mono">${r.customer_cif}</strong></div>
                            <div><span class="text-outline text-label-sm block">Assigned Officer</span><strong class="text-on-surface font-semibold">${r.assigned_employee_name || 'Unassigned'}</strong></div>
                            <div><span class="text-outline text-label-sm block">Verification Status</span><strong class="text-on-surface font-semibold">${r.status}</strong></div>
                        </div>
                        <div class="pt-3 space-y-2">
                            <div><span class="text-outline text-label-sm block">Submitted Timestamp</span><span class="text-sm font-medium text-on-surface">${formatDate(r.submitted_at)}</span></div>
                            <div><span class="text-outline text-label-sm block">Review Timestamp</span><span class="text-sm font-medium text-on-surface">${r.reviewed_at ? formatDate(r.reviewed_at) : 'Pending'}</span></div>
                            ${r.rejection_reason ? `<div><span class="text-error text-label-sm block">Rejection Reason</span><span class="text-sm font-medium text-error">${r.rejection_reason}</span></div>` : ''}
                            ${r.review_notes ? `<div><span class="text-amber-900 text-label-sm block">Compliance Review Notes</span><span class="text-sm font-medium text-amber-900">${r.review_notes}</span></div>` : ''}
                        </div>
                    `
                });
            };
        });

    } catch (err) {
        console.error('Failed to load admin KYC:', err);
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading KYC requests: ${err.message}</div>`;
    }
}

/**
 * 6. Admin: Banking Staff & Operational Workload (Sections 18, 19, 20)
 */
async function loadAdminEmployees() {
    const container = document.getElementById('admin-employees-table-container');
    const searchInput = document.getElementById('admin-employees-search');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading banking staff...</div>`;

    const params = {};
    if (searchInput && searchInput.value.trim()) params.search = searchInput.value.trim();

    try {
        const employees = await ApiService.getEmployees(params);

        if (!employees || employees.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No banking staff found.</div>`;
            return;
        }

        let rowsHtml = employees.map(emp => {
            const statusBadge = emp.is_active ? 'bg-secondary/10 text-secondary' : 'bg-error/10 text-error';

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors">
                    <td class="py-3 px-4">
                        <strong class="text-on-surface font-semibold block">${emp.full_name}</strong>
                        <span class="text-[11px] text-outline font-mono">ID: ${emp.employee_id} · @${emp.username}</span>
                    </td>
                    <td class="py-3 px-3">
                        <span class="text-on-surface font-medium block">${emp.designation}</span>
                        <span class="text-[11px] text-outline">${emp.branch_name || 'Main Branch'}</span>
                    </td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2.5 py-0.5 rounded text-[11px] font-semibold uppercase ${statusBadge}">${emp.is_active ? 'Active' : 'Inactive'}</span>
                    </td>
                    <td class="py-3 px-3 text-center font-financial-numeric font-bold text-primary-container">
                        ${emp.open_kyc_count ?? 0}
                    </td>
                    <td class="py-3 px-3 text-center font-financial-numeric font-bold text-secondary">
                        ${emp.completed_kyc_count ?? 0}
                    </td>
                    <td class="py-3 px-3 text-center font-financial-numeric font-bold text-on-surface">
                        ${emp.total_assigned_kyc ?? 0}
                    </td>
                    <td class="py-3 px-4 text-right">
                        <button type="button" class="btn-adm-emp-detail px-3 py-1 rounded-lg border border-outline-variant/30 text-on-surface hover:bg-surface-container-high font-label-sm font-semibold transition-colors" data-id="${emp.id}">
                            Profile
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Staff Member &amp; ID</th>
                        <th class="py-3 px-3">Designation &amp; Branch</th>
                        <th class="py-3 px-3 text-center">Status</th>
                        <th class="py-3 px-3 text-center">Active KYC Cases</th>
                        <th class="py-3 px-3 text-center">Completed Reviews</th>
                        <th class="py-3 px-3 text-center">Total Workload</th>
                        <th class="py-3 px-4 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

        container.querySelectorAll('.btn-adm-emp-detail').forEach(btn => {
            btn.onclick = () => {
                const empId = btn.getAttribute('data-id');
                const emp = employees.find(x => String(x.id) === String(empId));
                if (!emp) return;
                showGenericDetailModal({
                    title: `Staff Profile: ${emp.full_name}`,
                    icon: 'badge',
                    contentHtml: `
                        <div class="grid grid-cols-2 gap-4 pb-4 border-b border-outline-variant/20">
                            <div><span class="text-outline text-label-sm block">Officer Name</span><strong class="text-on-surface font-semibold">${emp.full_name}</strong></div>
                            <div><span class="text-outline text-label-sm block">Employee ID</span><strong class="text-on-surface font-semibold font-mono">${emp.employee_id}</strong></div>
                            <div><span class="text-outline text-label-sm block">Designation</span><strong class="text-on-surface font-semibold">${emp.designation}</strong></div>
                            <div><span class="text-outline text-label-sm block">Branch Assignment</span><strong class="text-on-surface font-semibold">${emp.branch_name || 'N/A'}</strong></div>
                            <div><span class="text-outline text-label-sm block">Active Cases</span><strong class="text-primary-container font-semibold">${emp.open_kyc_count} cases</strong></div>
                            <div><span class="text-outline text-label-sm block">Completed Reviews</span><strong class="text-secondary font-semibold">${emp.completed_kyc_count} completed</strong></div>
                        </div>
                        <div class="pt-3 space-y-1">
                            <div><span class="text-outline text-label-sm block">Work Email</span><span class="text-sm font-medium text-on-surface">${emp.email || 'N/A'}</span></div>
                            <div><span class="text-outline text-label-sm block">System Username</span><span class="text-sm font-mono text-on-surface font-medium">${emp.username}</span></div>
                        </div>
                    `
                });
            };
        });

    } catch (err) {
        console.error('Failed to load admin employees:', err);
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading staff: ${err.message}</div>`;
    }
}

/**
 * 7. Admin: Immutable Regulatory Audit Trail
 */
async function loadAdminAuditLogs() {
    const container = document.getElementById('admin-audit-logs-container');
    const searchInput = document.getElementById('admin-audit-search');
    const actionSelect = document.getElementById('admin-audit-action');

    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-outline">Loading audit logs...</div>`;

    const params = {};
    if (searchInput && searchInput.value.trim()) params.search = searchInput.value.trim();
    if (actionSelect && actionSelect.value !== 'ALL') params.action = actionSelect.value;

    try {
        const logs = await ApiService.getAuditLogs(params);

        if (!logs || logs.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline">No regulatory audit logs recorded matching filter.</div>`;
            return;
        }

        let rowsHtml = logs.map(l => {
            let statusBadge = l.status === 'SUCCESS' ? 'bg-secondary/10 text-secondary' : 'bg-error/10 text-error';

            return `
                <tr class="border-b border-outline-variant/15 hover:bg-surface-container-low/40 transition-colors text-[13px]">
                    <td class="py-3 px-4 font-mono text-[12px] text-outline">${new Date(l.timestamp).toLocaleString('en-IN')}</td>
                    <td class="py-3 px-3 font-semibold text-on-surface">${l.actor_username || 'SYSTEM'}</td>
                    <td class="py-3 px-3">
                        <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-surface-container-high text-on-surface font-mono">${l.action}</span>
                    </td>
                    <td class="py-3 px-3 font-mono text-outline text-[12px]">${l.record_type || 'CORE'}:${l.record_id || '--'}</td>
                    <td class="py-3 px-3 font-mono text-outline text-[12px]">${l.ip_address || '127.0.0.1'}</td>
                    <td class="py-3 px-3 text-on-surface max-w-xs truncate">${l.details || l.description || '--'}</td>
                    <td class="py-3 px-4 text-center">
                        <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${statusBadge}">${l.status || 'SUCCESS'}</span>
                    </td>
                </tr>
            `;
        }).join('');

        container.innerHTML = `
            <table class="w-full text-left text-sm font-body-sm">
                <thead class="bg-surface-container-low text-outline text-[11px] uppercase font-semibold">
                    <tr>
                        <th class="py-3 px-4">Timestamp</th>
                        <th class="py-3 px-3">Actor</th>
                        <th class="py-3 px-3">Action</th>
                        <th class="py-3 px-3">Entity</th>
                        <th class="py-3 px-3">Source IP</th>
                        <th class="py-3 px-3">Details / Narrative</th>
                        <th class="py-3 px-4 text-center">Result</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/10">
                    ${rowsHtml}
                </tbody>
            </table>
        `;

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md">Error loading audit logs: ${err.message}</div>`;
    }
}

/**
 * 6. Admin: Branch Network Facilities
 */
async function loadAdminBranches() {
    const container = document.getElementById('admin-branches-container');
    if (!container) return;

    const searchInput = document.getElementById('admin-branches-search');
    const statusSelect = document.getElementById('admin-branches-status');

    const params = {};
    if (searchInput && searchInput.value.trim()) params.search = searchInput.value.trim();
    if (statusSelect && statusSelect.value && statusSelect.value !== 'ALL') {
        params.status = statusSelect.value;
    }

    container.innerHTML = `<div class="p-8 text-center text-outline col-span-3">Loading branches...</div>`;

    try {
        const branches = await ApiService.getBranches(params);

        if (!branches || branches.length === 0) {
            container.innerHTML = `<div class="p-10 text-center text-outline col-span-3">No matching branch facilities found.</div>`;
            return;
        }

        container.innerHTML = '';
        branches.forEach(b => {
            const card = document.createElement('div');
            card.className = 'glass-card p-5 rounded-2xl flex flex-col justify-between space-y-4 hover:shadow-md transition-shadow';

            card.innerHTML = `
                <div>
                    <div class="flex items-center justify-between">
                        <span class="px-2.5 py-0.5 rounded font-mono font-semibold text-[12px] bg-primary-container/10 text-primary-container">${b.branch_code || b.branch_id || 'BRANCH'}</span>
                        <span class="px-2.5 py-0.5 rounded text-[11px] font-semibold uppercase ${b.is_active ? 'bg-secondary/10 text-secondary' : 'bg-outline/20 text-outline'}">${b.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <h4 class="font-headline-sm font-bold text-on-surface pt-2.5">${b.name || b.branch_name}</h4>
                    <p class="font-body-sm text-outline text-[13px] pt-0.5">IFSC: <span class="font-mono uppercase font-medium text-on-surface">${b.ifsc_code || b.ifsc}</span> · ${b.city}</p>
                    <p class="font-label-sm text-on-surface-variant pt-2">Manager: <strong class="text-on-surface">${b.manager_name || 'Branch Manager'}</strong></p>
                    <p class="font-label-sm text-outline pt-0.5">${b.address || 'Address pending'}</p>
                </div>
                <div class="pt-3 border-t border-outline-variant/20 flex flex-col gap-2.5">
                    <div class="grid grid-cols-2 gap-1.5 text-[11px] text-outline">
                        <div>Staff: <strong class="text-on-surface">${b.employee_count || 0}</strong></div>
                        <div>Accounts: <strong class="text-on-surface">${b.account_count || 0}</strong></div>
                        <div>Customers: <strong class="text-on-surface">${b.customer_count || 0}</strong></div>
                        <div>Daily Vol: <strong class="text-secondary">${formatINR(b.daily_transaction_volume || 0, false)}</strong></div>
                    </div>
                    <div class="flex items-center justify-end gap-1.5 pt-1 border-t border-outline-variant/10">
                        <button type="button" class="btn-adm-branch-edit px-2.5 py-1 rounded-lg border border-outline-variant/30 text-on-surface hover:bg-surface-container-high font-label-sm" data-id="${b.id}">
                            Edit
                        </button>
                        <button type="button" class="btn-adm-branch-toggle px-2.5 py-1 rounded-lg ${b.is_active ? 'bg-error-container/40 text-error hover:bg-error-container' : 'bg-secondary/15 text-secondary hover:bg-secondary/25'} font-label-sm font-semibold transition-colors" data-id="${b.id}" data-name="${b.name || b.branch_name}" data-active="${b.is_active}">
                            ${b.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });

        // Bind Edit
        container.querySelectorAll('.btn-adm-branch-edit').forEach(btn => {
            btn.onclick = () => {
                const bId = btn.getAttribute('data-id');
                const branch = branches.find(x => String(x.id) === String(bId));
                if (branch) showBranchFormModal(branch);
            };
        });

        // Bind Toggle
        container.querySelectorAll('.btn-adm-branch-toggle').forEach(btn => {
            btn.onclick = async () => {
                const bId = btn.getAttribute('data-id');
                const bName = btn.getAttribute('data-name');
                const isActive = btn.getAttribute('data-active') === 'true';

                const reason = await promptActionModal({
                    title: `${isActive ? 'Deactivate' : 'Activate'} Branch Facility`,
                    subtitle: bName,
                    desc: `Are you sure you want to ${isActive ? 'deactivate' : 'activate'} this physical branch facility?`,
                    label: 'Operational Reason:',
                    placeholder: 'Administrative status update for branch network',
                    confirmText: isActive ? 'Deactivate' : 'Activate',
                    confirmClass: isActive ? 'bg-error hover:bg-red-700' : 'bg-secondary hover:bg-secondary/90',
                    icon: 'hub',
                    requireReason: false
                });
                if (reason === null) return;

                try {
                    await ApiService.toggleBranchStatus(bId, reason || 'Status toggled from admin operations console.');
                    alert(`Branch "${bName}" status updated!`);
                    await loadAdminBranches();
                    await loadAdminOverview();
                } catch (err) {
                    alert(`Action failed: ${err.message}`);
                }
            };
        });

    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-error font-label-md col-span-3">Error loading branches: ${err.message}</div>`;
    }
}

/**
 * Statement CSV Exporter
 */
async function exportTransactionsToCSV() {
    try {
        let txns = currentTransactions;
        if (!txns || txns.length === 0) {
            txns = await ApiService.getTransactions();
        }

        if (!txns || txns.length === 0) {
            alert('No recorded transactions found to export.');
            return;
        }

        const headers = ['Transaction ID', 'Beneficiary', 'Category', 'Type', 'Amount (INR)', 'Balance After (INR)', 'Status', 'Date', 'Remarks'];
        const csvRows = [headers.join(',')];

        txns.forEach(t => {
            const row = [
                `"${t.transaction_id || ''}"`,
                `"${(t.beneficiary_name || '').replace(/"/g, '""')}"`,
                `"${t.category || ''}"`,
                `"${t.transaction_type || ''}"`,
                t.amount || 0,
                t.balance_after || 0,
                `"${t.status || ''}"`,
                `"${t.timestamp || ''}"`,
                `"${(t.remarks || '').replace(/"/g, '""')}"`
            ];
            csvRows.push(row.join(','));
        });

        const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Finova_Statement_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (err) {
        alert(`Export failed: ${err.message}`);
    }
}

/**
 * Navigation & View Switching
 */
function initNavigation() {
    const navLinks = document.querySelectorAll('aside nav a[data-path], [data-nav-target]');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPath = link.getAttribute('data-path') || link.getAttribute('data-nav-target');
            const empTab = link.getAttribute('data-employee-tab');
            const admTab = link.getAttribute('data-admin-tab');
            if (targetPath) {
                navigateTo(targetPath);
                if (targetPath === 'employee-portal' && empTab) {
                    switchEmployeeTab(empTab);
                } else if (targetPath === 'admin-portal' && admTab) {
                    switchAdminTab(admTab);
                }
            }
        });
    });

    const initialHash = window.location.hash.replace('#', '') || 'dashboard';
    navigateTo(initialHash);
}

function navigateTo(path) {
    if (path === 'loan-application' || path === 'apply-loan') path = 'apply-for-credit';
    if (path === 'loans') path = 'loans-overview';
    if (path === 'profile' || path === 'security') path = 'security-and-profile';
    if (path === 'transfer') path = 'transfer-and-pay';

    const allViews = document.querySelectorAll('.app-view');
    allViews.forEach(view => view.classList.add('hidden'));

    const activeView = document.getElementById(`view-${path}`);
    if (activeView) {
        activeView.classList.remove('hidden');
        window.location.hash = path;
    } else {
        const defaultView = document.getElementById('view-dashboard');
        if (defaultView) defaultView.classList.remove('hidden');
    }

    if (path === 'support') {
        loadSupportBranches();
    } else if (path === 'loans-overview') {
        loadLoansOverview();
    } else if (path === 'accounts') {
        loadAccounts();
    } else if (path === 'transactions') {
        loadTransactions();
    } else if (path === 'notifications') {
        loadNotifications();
    }

    const asideLinks = document.querySelectorAll('aside nav a[data-path]');
    asideLinks.forEach(link => {
        const linkPath = link.getAttribute('data-path');
        if (linkPath === path) {
            link.classList.remove('text-on-surface-variant', 'font-label-md');
            link.classList.add('bg-surface-container-low', 'text-primary-container', 'font-semibold');
            link.setAttribute('aria-current', 'page');
        } else {
            link.classList.remove('bg-surface-container-low', 'text-primary-container', 'font-semibold');
            link.classList.add('text-on-surface-variant', 'font-label-md');
            link.removeAttribute('aria-current');
        }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Load Support Branch Locations Dynamically
 */
async function loadSupportBranches() {
    const container = document.getElementById('support-branches-container');
    if (!container) return;
    try {
        const branches = await ApiService.getBranches();
        if (!branches || branches.length === 0) return;
        container.innerHTML = branches.map(b => `
            <div class="glass-card p-6 rounded-2xl space-y-3">
                <div class="flex items-center justify-between">
                    <h4 class="font-headline-sm font-semibold text-on-surface">${b.branch_name}</h4>
                    <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-secondary/10 text-secondary uppercase">${b.status}</span>
                </div>
                <p class="font-label-sm text-primary-container font-semibold">IFSC: ${b.ifsc_code} · Code: ${b.branch_code}</p>
                <p class="font-body-sm text-outline">${b.address}, ${b.city}, ${b.state} - ${b.pincode}</p>
                <p class="font-body-sm text-on-surface font-medium">Branch Manager: ${b.manager_name || 'Designated Officer'}</p>
                <p class="font-label-sm text-outline">Contact: ${b.contact_phone || '1800-FINOVA-SUPPORT'}</p>
            </div>
        `).join('');
    } catch (err) {
        console.warn('Failed to load support branches:', err);
    }
}

/**
 * Quick Action Button Bindings
 */
function initQuickActions() {
    document.querySelectorAll('.btn-quick-transfer').forEach(btn => {
        btn.addEventListener('click', () => navigateTo('transfer-and-pay'));
    });

    document.querySelectorAll('.btn-quick-pay-emi').forEach(btn => {
        btn.addEventListener('click', () => navigateTo('pay-emi'));
    });

    document.querySelectorAll('.btn-quick-apply-loan').forEach(btn => {
        btn.addEventListener('click', () => navigateTo('apply-for-credit'));
    });

    document.querySelectorAll('.btn-bell-notifications').forEach(btn => {
        btn.addEventListener('click', () => navigateTo('notifications'));
    });

    // Global Search Header
    const searchHeader = document.getElementById('header-global-search');
    if (searchHeader) {
        searchHeader.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const q = searchHeader.value.trim();
                navigateTo('transactions');
                const tInput = document.getElementById('transactions-search-input');
                if (tInput) tInput.value = q;
                loadTransactions('', q);
            }
        });
    }

    // CSV Statement Exports
    const btnTxnExport = document.getElementById('transactions-btn-export');
    if (btnTxnExport) {
        btnTxnExport.addEventListener('click', exportTransactionsToCSV);
    }

    const btnStmtDownload = document.getElementById('dashboard-btn-download-statement');
    if (btnStmtDownload) {
        btnStmtDownload.addEventListener('click', exportTransactionsToCSV);
    }
}

/**
 * Cashflow Timeframe Segmented Control (Sections 5 & 6)
 */
function initCashflowFilters() {
    const timeframeButtons = document.querySelectorAll('.cashflow-tf-btn');
    timeframeButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            timeframeButtons.forEach(b => {
                b.classList.remove('bg-surface-container-lowest', 'shadow-sm', 'text-on-surface', 'font-semibold');
                b.classList.add('text-outline', 'font-medium');
            });
            btn.classList.remove('text-outline', 'font-medium');
            btn.classList.add('bg-surface-container-lowest', 'shadow-sm', 'text-on-surface', 'font-semibold');

            const days = parseInt(btn.getAttribute('data-days'), 10) || 30;
            await loadCashflowChart(days);
        });
    });
}

window.navigateTo = navigateTo;
window.exportTransactionsToCSV = exportTransactionsToCSV;
window.handleLogout = handleLogout;
window.loadCashflowChart = loadCashflowChart;
window.renderDynamicCashflowChart = renderDynamicCashflowChart;
window.switchEmployeeTab = switchEmployeeTab;
window.switchAdminTab = switchAdminTab;
window.loadEmployeeStats = loadEmployeeStats;
window.loadEmployeeLoans = loadEmployeeLoans;
window.loadEmployeeKYC = loadEmployeeKYC;
window.loadEmployeeCustomers = loadEmployeeCustomers;
window.loadEmployeeLedger = loadEmployeeLedger;
window.loadAdminOverview = loadAdminOverview;
window.loadAdminCustomers = loadAdminCustomers;
window.loadAdminAccounts = loadAdminAccounts;
window.loadAdminTransactions = loadAdminTransactions;
window.loadAdminLoans = loadAdminLoans;
window.loadAdminKYC = loadAdminKYC;
window.loadAdminEmployees = loadAdminEmployees;
window.loadAdminAuditLogs = loadAdminAuditLogs;
window.loadAdminBranches = loadAdminBranches;
window.loadLoansOverview = loadLoansOverview;

