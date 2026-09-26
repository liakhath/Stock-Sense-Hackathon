// Dashboard Page Handler

async function loadDashboard() {
  await Promise.all([
    loadDashboardKpis(),
    loadDashboardOperations(),
    loadDashboardLowStock(),
    loadDashboardFilterOptions()
  ]);
}

async function loadDashboardKpis() {
  try {
    const kpis = await window.api.get('/dashboard/kpis');
    if (!kpis) return;

    const elTotalStock = document.getElementById('kpi-total-stock');
    const elInventoryValue = document.getElementById('kpi-inventory-value');
    const elLowStock = document.getElementById('kpi-low-stock');
    const elOutOfStock = document.getElementById('kpi-out-of-stock');
    const elPendingReceipts = document.getElementById('kpi-pending-receipts');
    const elPendingDeliveries = document.getElementById('kpi-pending-deliveries');
    const elTransfersScheduled = document.getElementById('kpi-transfers-scheduled');
    const elAdjustmentsAwaiting = document.getElementById('kpi-adjustments-awaiting');

    if (elTotalStock) elTotalStock.textContent = (kpis.total_products_in_stock || 0).toLocaleString();
    if (elInventoryValue) elInventoryValue.textContent = formatMoney(kpis.inventory_value || 0);
    if (elLowStock) elLowStock.textContent = (kpis.low_stock_items || 0).toLocaleString();
    if (elOutOfStock) elOutOfStock.textContent = (kpis.out_of_stock_items || 0).toLocaleString();
    if (elPendingReceipts) elPendingReceipts.textContent = (kpis.pending_receipts || 0).toLocaleString();
    if (elPendingDeliveries) elPendingDeliveries.textContent = (kpis.pending_deliveries || 0).toLocaleString();
    if (elTransfersScheduled) elTransfersScheduled.textContent = (kpis.internal_transfers_scheduled || 0).toLocaleString();
    if (elAdjustmentsAwaiting) elAdjustmentsAwaiting.textContent = (kpis.adjustments_awaiting_approval || 0).toLocaleString();
  } catch (e) {
    console.error("Error loading dashboard KPIs", e);
  }
}

async function loadDashboardFilterOptions() {
  try {
    const [warehouses, categories] = await Promise.all([
      window.api.get('/warehouses'),
      window.api.get('/products/categories')
    ]);

    const whSelect = document.getElementById('dash-filter-warehouse');
    if (whSelect) {
      const current = whSelect.value;
      whSelect.innerHTML = `<option value="">All Warehouses</option>` +
        (warehouses || []).map(w => `<option value="${w}">${w}</option>`).join('');
      whSelect.value = current;
    }

    const catSelect = document.getElementById('dash-filter-category');
    if (catSelect) {
      const current = catSelect.value;
      catSelect.innerHTML = `<option value="">All Categories</option>` +
        (categories || []).map(c => `<option value="${c}">${c}</option>`).join('');
      catSelect.value = current;
    }
  } catch (e) {
    console.error("Error loading filter options", e);
  }
}

async function loadDashboardOperations() {
  const tableBody = document.getElementById('dash-operations-table');
  if (!tableBody) return;

  const type = document.getElementById('dash-filter-type')?.value || '';
  const status = document.getElementById('dash-filter-status')?.value || '';
  const warehouse = document.getElementById('dash-filter-warehouse')?.value || '';
  const category = document.getElementById('dash-filter-category')?.value || '';

  try {
    const ops = await window.api.get('/operations', { type, status, warehouse, category });
    if (!ops || ops.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="8" class="py-6 text-center text-on-surface-variant font-label-md">No matching operations found</td></tr>`;
      return;
    }

    tableBody.innerHTML = ops.slice(0, 10).map(op => {
      const totalQty = (op.lines || []).reduce((sum, l) => sum + l.qty, 0);
      const firstLine = op.lines && op.lines[0] ? `${op.lines[0].product_name || 'Product'} (${op.lines[0].sku || ''})` : 'No items';
      const itemDesc = op.lines && op.lines.length > 1 ? `${firstLine} +${op.lines.length - 1} more` : firstLine;
      
      let statusBadge = `bg-surface-container text-on-surface-variant`;
      if (op.status === 'ready') statusBadge = `bg-primary-container/30 text-on-primary-fixed-variant`;
      if (op.status === 'done') statusBadge = `bg-primary-container text-on-primary-container`;
      if (op.status === 'waiting') statusBadge = `bg-tertiary-container/30 text-on-tertiary-container`;
      if (op.status === 'canceled') statusBadge = `bg-error-container/30 text-on-error-container`;

      const typeLabel = op.type ? op.type.charAt(0).toUpperCase() + op.type.slice(1) : 'Operation';

      return `
        <tr class="hover:bg-surface-container-low/60 transition-colors cursor-pointer" onclick="navigateView('operation-detail', { id: ${op.id} })">
          <td class="py-3.5 px-4 font-mono font-semibold text-primary">${op.ref}</td>
          <td class="py-3.5 px-4"><span class="px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">${typeLabel}</span></td>
          <td class="py-3.5 px-4 font-medium text-on-surface">${itemDesc}</td>
          <td class="py-3.5 px-4 text-on-surface-variant text-xs">${op.partner || op.reason || op.note || 'Standard Move'}</td>
          <td class="py-3.5 px-4 text-right font-bold text-on-surface">${totalQty}</td>
          <td class="py-3.5 px-4 text-on-surface-variant text-xs">${new Date(op.created_at).toLocaleDateString()}</td>
          <td class="py-3.5 px-4"><span class="px-2.5 py-0.5 rounded-full ${statusBadge} font-label-sm text-label-sm font-semibold capitalize">${op.status}</span></td>
          <td class="py-3.5 px-4 text-center"><button class="text-label-sm font-label-sm text-primary font-bold hover:underline" onclick="event.stopPropagation(); navigateView('operation-detail', { id: ${op.id} })">Inspect</button></td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    tableBody.innerHTML = `<tr><td colspan="8" class="py-6 text-center text-error font-label-md">Error loading operations</td></tr>`;
  }
}

async function loadDashboardLowStock() {
  const container = document.getElementById('dash-low-stock-list');
  if (!container) return;

  try {
    const items = await window.api.get('/products/low-stock');
    if (!items || items.length === 0) {
      container.innerHTML = `<div class="p-4 text-center text-on-surface-variant font-label-sm">All inventory within safe levels!</div>`;
      return;
    }

    container.innerHTML = items.slice(0, 5).map(item => {
      const coverText = (item.days_of_cover !== null && item.days_of_cover !== undefined) ? `${item.days_of_cover} days` : '—';

      return `
        <div class="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-low hover:bg-surface-container transition-colors">
          <div class="flex flex-col">
            <span class="font-label-md text-label-md font-semibold text-on-surface">${item.name} (${item.sku})</span>
            <span class="font-label-sm text-label-sm ${item.available <= 0 ? 'text-error' : 'text-tertiary'} font-medium">
              Available: ${item.available} / Min: ${item.min_qty} (Cover: ${coverText})
            </span>
          </div>
          <span class="px-2 py-1 rounded bg-surface-container text-on-surface-variant text-xs font-mono font-bold">Rec: +${item.suggested_order_qty}</span>
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div class="p-4 text-center text-error font-label-sm">Error loading low stock list</div>`;
  }
}

async function handleAutoReorder() {
  try {
    const locations = await window.api.get('/locations');
    if (!locations || locations.length === 0) {
      if (window.triggerToast) window.triggerToast("Auto-Reorder Failed", "No warehouse locations found.");
      return;
    }

    // Modal or select first location
    const locId = locations[0].id;
    const op = await window.api.post(`/operations/reorder?location_id=${locId}`);
    
    if (!op) {
      if (window.triggerToast) window.triggerToast("Auto-Reorder", "Nothing needs reordering at this time.");
    } else {
      if (window.triggerToast) window.triggerToast("Reorder Draft Created", `Created receipt operation ${op.ref}`);
      navigateView('operation-detail', { id: op.id });
    }
  } catch (e) {
    // API errors caught by api.js
  }
}

window.loadDashboard = loadDashboard;
window.loadDashboardOperations = loadDashboardOperations;
window.handleAutoReorder = handleAutoReorder;
