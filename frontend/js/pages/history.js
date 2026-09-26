// Move History Page Handler

async function loadMoveHistory(params = {}) {
  await populateHistoryFilters();
  await fetchMoveHistory();
}

async function populateHistoryFilters() {
  try {
    const [products, locations] = await Promise.all([
      window.api.get('/products?include_archived=true'),
      window.api.get('/locations')
    ]);

    const prodSelect = document.getElementById('history-filter-product');
    if (prodSelect) {
      const cur = prodSelect.value;
      prodSelect.innerHTML = `<option value="">All Products</option>` +
        (products || []).map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join('');
      prodSelect.value = cur;
    }

    const locSelect = document.getElementById('history-filter-location');
    if (locSelect) {
      const cur = locSelect.value;
      locSelect.innerHTML = `<option value="">All Locations</option>` +
        (locations || []).map(l => `<option value="${l.id}">${l.warehouse} / ${l.name}</option>`).join('');
      locSelect.value = cur;
    }

    // Build location lookup map for display
    window.locationMap = {};
    (locations || []).forEach(l => {
      window.locationMap[l.id] = `${l.warehouse} / ${l.name}`;
    });
  } catch (e) {
    console.error("Error populating history filters", e);
  }
}

async function fetchMoveHistory() {
  const tableBody = document.getElementById('history-table-body');
  if (!tableBody) return;

  const product_id = document.getElementById('history-filter-product')?.value || '';
  const location_id = document.getElementById('history-filter-location')?.value || '';
  const type = document.getElementById('history-filter-type')?.value || '';
  const user = document.getElementById('history-filter-user')?.value || '';
  const since = document.getElementById('history-filter-since')?.value || '';
  const until = document.getElementById('history-filter-until')?.value || '';

  try {
    const moves = await window.api.get('/ledger', { product_id, location_id, type, user, since, until, limit: 100 });
    
    if (!moves || moves.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-on-surface-variant font-label-md">No ledger records found</td></tr>`;
      return;
    }

    // Fetch product lookup map if needed
    if (!window.productMap) {
      const products = await window.api.get('/products?include_archived=true');
      window.productMap = {};
      (products || []).forEach(p => {
        window.productMap[p.id] = `${p.name} (${p.sku})`;
      });
    }

    tableBody.innerHTML = moves.map(m => {
      const timeStr = new Date(m.timestamp).toLocaleString();
      const prodStr = window.productMap ? (window.productMap[m.product_id] || `Product #${m.product_id}`) : `Product #${m.product_id}`;
      
      let fromStr = m.from_location_id && window.locationMap ? (window.locationMap[m.from_location_id] || `Loc #${m.from_location_id}`) : 'Vendor';
      let toStr = m.to_location_id && window.locationMap ? (window.locationMap[m.to_location_id] || `Loc #${m.to_location_id}`) : 'Customer';
      
      if (m.operation_type === 'adjustment') {
        if (!m.from_location_id) fromStr = 'Adjustment';
        if (!m.to_location_id) toStr = 'Adjustment';
      }

      const routeStr = `${fromStr} → ${toStr}`;
      const qtyStr = m.qty > 0 ? `+${m.qty}` : `${m.qty}`;
      const qtyClass = m.qty > 0 ? 'text-primary font-bold' : 'text-error font-bold';

      return `
        <tr class="hover:bg-surface-container-low/60 transition-colors">
          <td class="py-3 px-4 font-mono text-xs text-on-surface-variant">${timeStr}</td>
          <td class="py-3 px-4 font-mono font-semibold text-primary">
            ${m.operation_id ? `<button class="hover:underline" onclick="navigateView('operation-detail', {id: ${m.operation_id}})">${m.operation_ref || `#${m.operation_id}`}</button>` : (m.operation_ref || 'Direct')}
          </td>
          <td class="py-3 px-4 uppercase text-xs font-semibold text-on-surface-variant">${m.operation_type || 'move'}</td>
          <td class="py-3 px-4 font-medium text-on-surface">${prodStr}</td>
          <td class="py-3 px-4 text-on-surface-variant text-xs">${routeStr}</td>
          <td class="py-3 px-4 text-right ${qtyClass}">${qtyStr}</td>
          <td class="py-3 px-4 text-xs text-on-surface-variant">${m.user}</td>
        </tr>
      `;
    }).join('');

  } catch (e) {
    tableBody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-error font-label-md">Error loading move history</td></tr>`;
  }
}

function exportLedgerCsv() {
  const product_id = document.getElementById('history-filter-product')?.value || '';
  const type = document.getElementById('history-filter-type')?.value || '';
  const user = document.getElementById('history-filter-user')?.value || '';

  const path = `/reports/export/ledger.csv?product_id=${encodeURIComponent(product_id)}&type=${encodeURIComponent(type)}&user=${encodeURIComponent(user)}`;
  window.api.download(path, 'ledger_export.csv');
}

window.loadMoveHistory = loadMoveHistory;
window.fetchMoveHistory = fetchMoveHistory;
window.exportLedgerCsv = exportLedgerCsv;
