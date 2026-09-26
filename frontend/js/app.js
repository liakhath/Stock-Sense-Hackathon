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
  'warehouses': 'view-warehouses',
  'locations': 'view-locations',
  'my-profile': 'view-my-profile',
  'settings': 'view-settings',
  'import': 'view-import',
  'reports': 'view-reports',
  'operation-detail': 'view-operation-detail',
  'login': 'view-login'
};

let currentRoute = 'dashboard';

function navigateView(routeKey, params = {}) {
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
    } else if (path !== 'login') {
      link.className = "flex items-center gap-3 px-3 py-2 rounded-xl text-on-surface-variant font-body-md text-body-md hover:bg-surface-container hover:text-on-surface transition-all";
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Trigger page load handlers if available
  if (routeKey === 'dashboard' && window.loadDashboard) window.loadDashboard(params);
  if ((routeKey === 'products' || routeKey === 'products-stock') && window.loadProducts) window.loadProducts(params);
  if (routeKey === 'receipts' && window.loadOperationsPage) window.loadOperationsPage('receipt', params);
  if (routeKey === 'deliveries' && window.loadOperationsPage) window.loadOperationsPage('delivery', params);
  if ((routeKey === 'transfers' || routeKey === 'internal-transfers') && window.loadOperationsPage) window.loadOperationsPage('internal', params);
  if (routeKey === 'adjustments' && window.loadOperationsPage) window.loadOperationsPage('adjustment', params);
  if (routeKey === 'move-history' && window.loadMoveHistory) window.loadMoveHistory(params);
  if ((routeKey === 'warehouses' || routeKey === 'locations' || routeKey === 'settings') && window.loadSettings) window.loadSettings(params);
  if (routeKey === 'import' && window.loadImportPage) window.loadImportPage(params);
  if (routeKey === 'reports' && window.loadReportsPage) window.loadReportsPage(params);
  if (routeKey === 'operation-detail' && window.loadOperationDetail) window.loadOperationDetail(params.id);
  if (routeKey === 'my-profile' && window.loadProfilePage) window.loadProfilePage();
}

// Header & User Profile Management
function updateHeaderUser() {
  const currentUser = getCurrentUser();
  const nameEl = document.getElementById('header-user-name');
  const roleEl = document.getElementById('header-user-role');
  const profileSelector = document.getElementById('profile-user-select');

  const displayName = currentUser === 'manager' ? 'Marcus Vance' : 'Alex Rivers';
  const displayRole = currentUser === 'manager' ? 'Warehouse Manager' : 'Inventory Staff';
  const badgeText = currentUser === 'manager' ? 'MGR' : 'STF';

  if (nameEl) nameEl.textContent = displayName;
  if (roleEl) roleEl.textContent = displayRole;
  if (profileSelector) profileSelector.value = currentUser;

  const currentBadge = document.getElementById('header-user-badge');
  if (currentBadge) currentBadge.textContent = badgeText;
}

window.updateHeaderUser = updateHeaderUser;

// Notification Bell & Alerts Polling
let alertPollTimer = null;

async function pollAlerts() {
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
        // Handle 404 / Error gracefully (already toasted by api.js)
      }
    }
  });
}

// Initialization on DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
  // Sidebar links listener
  document.querySelectorAll('aside [data-path]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const route = link.getAttribute('data-path');
      navigateView(route);
    });
  });

  updateHeaderUser();
  setupHeaderSearch();

  // Initial health check
  window.api.checkHealth();

  // Initial alert poll and interval
  pollAlerts();
  if (alertPollTimer) clearInterval(alertPollTimer);
  alertPollTimer = setInterval(pollAlerts, 30000);

  // Default route
  navigateView('dashboard');
});

window.navigateView = navigateView;
window.toggleAlertDropdown = toggleAlertDropdown;
window.markAllAlertsRead = markAllAlertsRead;
window.handleAlertClick = handleAlertClick;
