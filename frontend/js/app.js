// StockSense Main Application Controller & Router

const viewMap = {
  'dashboard': 'view-dashboard',
  'products-stock': 'view-products',
  'products': 'view-products',
  'receipts': 'view-receipts',
  'deliveries': 'view-deliveries',
  'internal-transfers': 'view-transfers',
  'transfers': 'view-transfers',
  'adjustments': 'view-adjustments',
  'move-history': 'view-move-history',
  'warehouses': 'view-settings',
  'locations': 'view-settings',
  'my-profile': 'view-my-profile',
  'settings': 'view-settings',
  'import': 'view-import',
  'reports': 'view-reports',
  'operation-detail': 'view-operation-detail',
  'users': 'view-users'
};

let currentRoute = 'dashboard';
let alertPollTimer = null;

function navigateView(routeKey, params = {}) {
  const token = window.getToken ? window.getToken() : null;
  if (!token) {
    if (window.showAuthScreen) window.showAuthScreen('login');
    return;
  }

  const user = window.getAuthUser ? window.getAuthUser() : null;
  if (routeKey === 'users' && (!user || user.role !== 'manager')) {
    if (window.triggerToast) window.triggerToast("Access Denied", "Only managers can access user settings.");
    routeKey = 'dashboard';
  }

  const targetId = viewMap[routeKey] || 'view-dashboard';
  currentRoute = routeKey;

  // Hide all views
  document.querySelectorAll('.stocksense-view').forEach(el => {
    el.classList.add('hidden');
    el.classList.remove('flex');
  });

  // Reveal target view
  const targetEl = document.getElementById(targetId);
  if (targetEl) {
    targetEl.classList.remove('hidden');
    targetEl.classList.add('flex');
  }

  // Update App Shell Sidebar links active pill styling
  document.querySelectorAll('aside nav a, aside [data-path]').forEach(link => {
    const path = link.getAttribute('data-path');
    if (path === routeKey || 
       (routeKey === 'products' && path === 'products-stock') || 
       (routeKey === 'transfers' && path === 'internal-transfers')) {
      link.className = "flex items-center gap-3 px-3 py-2 rounded-xl bg-primary-container text-on-primary-container font-headline-sm transition-all shadow-sm";
    } else {
      link.className = "flex items-center gap-3 px-3 py-2 rounded-xl text-on-surface-variant font-body-md text-body-md hover:bg-surface-container hover:text-on-surface transition-all";
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Apply role permissions to UI
  applyRolePermissions();

  // Trigger page load handlers if available
  if (routeKey === 'dashboard' && window.loadDashboard) window.loadDashboard(params);
  if ((routeKey === 'products' || routeKey === 'products-stock') && window.loadProducts) window.loadProducts(params);
  if (routeKey === 'receipts' && window.loadOperationsPage) window.loadOperationsPage('receipt', params);
  if (routeKey === 'deliveries' && window.loadOperationsPage) window.loadOperationsPage('delivery', params);
  if ((routeKey === 'transfers' || routeKey === 'internal-transfers') && window.loadOperationsPage) window.loadOperationsPage('internal', params);
  if (routeKey === 'adjustments' && window.loadOperationsPage) window.loadOperationsPage('adjustment', params);
  if (routeKey === 'move-history' && window.loadMoveHistory) window.loadMoveHistory(params);
  if ((routeKey === 'warehouses' || routeKey === 'locations' || routeKey === 'settings') && window.loadSettings) window.loadSettings(params);
  if (routeKey === 'users' && window.loadUsersPage) window.loadUsersPage();
  if (routeKey === 'import' && window.loadImportPage) window.loadImportPage(params);
  if (routeKey === 'reports' && window.loadReportsPage) window.loadReportsPage(params);
  if (routeKey === 'operation-detail' && window.loadOperationDetail) window.loadOperationDetail(params.id);
  if (routeKey === 'my-profile' && window.loadProfilePage) window.loadProfilePage();
}

// Header & User Profile Management
function updateHeaderUser() {
  const user = window.getAuthUser ? window.getAuthUser() : null;
  if (!user) return;

  const nameEl = document.getElementById('header-user-name');
  const roleEl = document.getElementById('header-user-role');
  const badgeEl = document.getElementById('header-user-badge');

  if (nameEl) nameEl.textContent = user.name || user.email;
  if (roleEl) roleEl.textContent = user.role === 'manager' ? 'Warehouse Manager' : 'Inventory Staff';

  if (badgeEl) {
    badgeEl.textContent = user.role.toUpperCase();
    badgeEl.className = user.role === 'manager'
      ? "px-2.5 py-0.5 rounded-full bg-primary-container text-on-primary-container font-bold text-xs uppercase shrink-0"
      : "px-2.5 py-0.5 rounded-full bg-secondary-container text-on-secondary-container font-bold text-xs uppercase shrink-0";
  }
}

function applyRolePermissions() {
  const user = window.getAuthUser ? window.getAuthUser() : null;
  if (!user) return;

  const isManager = (user.role === 'manager');

  // Sidebar Users link
  const navUsers = document.getElementById('nav-users');
  if (navUsers) {
    navUsers.style.display = isManager ? 'flex' : 'none';
  }

  // Settings Add Location button
  const btnAddLoc = document.getElementById('btn-add-location');
  if (btnAddLoc) {
    btnAddLoc.style.display = isManager ? 'flex' : 'none';
  }

  // Import confirm button
  const importConfirmBtn = document.getElementById('import-btn-confirm');
  if (importConfirmBtn && !isManager) {
    importConfirmBtn.style.display = 'none';
  }

  // Product archive button
  const archiveBtn = document.getElementById('panel-btn-archive');
  if (archiveBtn && !isManager) {
    archiveBtn.style.display = 'none';
  }
}

function loadProfilePage() {
  const user = window.getAuthUser ? window.getAuthUser() : null;
  if (!user) return;

  const nameEl = document.getElementById('profile-display-name');
  const emailEl = document.getElementById('profile-display-email');
  const roleEl = document.getElementById('profile-display-role');
  const badgeEl = document.getElementById('profile-display-badge');
  const idEl = document.getElementById('profile-display-id');
  const createdEl = document.getElementById('profile-display-created');
  const initialEl = document.getElementById('profile-avatar-initial');

  if (nameEl) nameEl.textContent = user.name;
  if (emailEl) emailEl.textContent = user.email;
  if (roleEl) roleEl.textContent = user.role === 'manager' ? 'Warehouse Manager' : 'Inventory Staff';
  if (badgeEl) badgeEl.textContent = user.role.toUpperCase();
  if (idEl) idEl.textContent = `#${user.id}`;
  if (createdEl) createdEl.textContent = new Date(user.created_at).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
  if (initialEl) initialEl.textContent = (user.name || 'U').charAt(0).toUpperCase();
}

// Notification Bell & Alerts Polling
async function pollAlerts() {
  const token = window.getToken ? window.getToken() : null;
  if (!token) return;

  try {
    const data = await window.api.get('/alerts/count');
    const badge = document.getElementById('alert-bell-badge');
    if (badge) {
      if (data && data.unread > 0) {
        badge.textContent = data.unread;
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    }
  } catch (e) {
    // Ignore error on polling
  }
}

async function toggleAlertDropdown() {
  const dropdown = document.getElementById('alert-dropdown');
  if (!dropdown) return;
  
  if (dropdown.classList.contains('hidden')) {
    dropdown.classList.remove('hidden');
    await loadAlertsDropdown();
  } else {
    dropdown.classList.add('hidden');
  }
}

async function loadAlertsDropdown() {
  const container = document.getElementById('alert-dropdown-list');
  if (!container) return;
  container.innerHTML = `<div class="p-4 text-center text-on-surface-variant font-label-sm">Loading notifications...</div>`;

  try {
    const alerts = await window.api.get('/alerts?include_resolved=false');
    if (!alerts || alerts.length === 0) {
      container.innerHTML = `<div class="p-4 text-center text-on-surface-variant font-label-sm">No new notifications</div>`;
      return;
    }

    container.innerHTML = alerts.map(a => `
      <div class="p-3 border-b border-surface-container hover:bg-surface-container-low cursor-pointer transition-colors ${a.read ? 'opacity-60' : 'bg-surface-container-lowest font-semibold'}"
           onclick="handleAlertClick(${a.id}, ${a.product_id || 'null'}, ${a.operation_id || 'null'})">
        <div class="flex items-center justify-between text-xs text-on-surface-variant mb-1">
          <span class="uppercase font-bold text-primary">${a.kind.replace('_', ' ')}</span>
          <span>${new Date(a.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>
        <p class="text-sm text-on-surface">${a.message}</p>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<div class="p-4 text-center text-error font-label-sm">Failed to load alerts</div>`;
  }
}

async function handleAlertClick(alertId, productId, operationId) {
  try {
    await window.api.post(`/alerts/${alertId}/read`);
    pollAlerts();
  } catch(e){}

  const dropdown = document.getElementById('alert-dropdown');
  if (dropdown) dropdown.classList.add('hidden');

  if (productId) {
    navigateView('products', { productId });
  } else if (operationId) {
    navigateView('operation-detail', { id: operationId });
  }
}

async function markAllAlertsRead() {
  try {
    await window.api.post('/alerts/read-all');
    pollAlerts();
    await loadAlertsDropdown();
    if (window.triggerToast) window.triggerToast("Alerts", "All notifications marked as read.");
  } catch(e){}
}

// Global SKU Header Search
function setupHeaderSearch() {
  const searchInput = document.getElementById('header-sku-search');
  if (!searchInput) return;

  searchInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      const q = searchInput.value.trim();
      if (!q) return;

      try {
        const product = await window.api.get(`/products/sku/${encodeURIComponent(q)}`);
        if (product && product.id) {
          navigateView('products', { productId: product.id });
          searchInput.value = '';
        }
      } catch (err) {
        // Handled gracefully
      }
    }
  });
}

function initAppAfterLogin() {
  updateHeaderUser();
  applyRolePermissions();
  pollAlerts();
  if (alertPollTimer) clearInterval(alertPollTimer);
  alertPollTimer = setInterval(pollAlerts, 30000);
}

// Initialization on DOM Content Loaded
document.addEventListener('DOMContentLoaded', async () => {
  // Sidebar links listener
  document.querySelectorAll('aside [data-path]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const route = link.getAttribute('data-path');
      navigateView(route);
    });
  });

  setupHeaderSearch();

  const token = window.getToken ? window.getToken() : null;
  if (!token) {
    window.showAuthScreen('login');
    return;
  }

  // Validate existing token with /auth/me
  try {
    const meUser = await window.api.getMe();
    window.setAuth(token, meUser);
    window.showAppShell();
    initAppAfterLogin();
    navigateView('dashboard');
  } catch (err) {
    window.clearAuth();
    window.showAuthScreen('login');
  }
});

window.navigateView = navigateView;
window.updateHeaderUser = updateHeaderUser;
window.applyRolePermissions = applyRolePermissions;
window.loadProfilePage = loadProfilePage;
window.initAppAfterLogin = initAppAfterLogin;
window.toggleAlertDropdown = toggleAlertDropdown;
window.markAllAlertsRead = markAllAlertsRead;
window.handleAlertClick = handleAlertClick;
