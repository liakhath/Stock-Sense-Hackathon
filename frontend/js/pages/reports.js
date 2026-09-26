// Reports Page Handler

async function loadReportsPage() {
  await Promise.all([
    fetchMoversReport(),
    fetchValuationReport()
  ]);
}

async function fetchMoversReport() {
  const daysSelect = document.getElementById('reports-movers-days');
  const days = daysSelect ? daysSelect.value : '30';

  try {
    const data = await window.api.get('/reports/movers', { days, top: 5 });
    if (!data) return;

    renderMoversTable('reports-fast-movers-body', data.fast_movers);
    renderMoversTable('reports-slow-movers-body', data.slow_movers);
    renderMoversTable('reports-dead-stock-body', data.dead_stock);

  } catch (e) {
    console.error("Error loading movers report", e);
  }
}

function renderMoversTable(tableId, items) {
  const container = document.getElementById(tableId);
  if (!container) return;

  if (!items || items.length === 0) {
    container.innerHTML = `<tr><td colspan="6" class="py-3 text-center text-xs text-on-surface-variant">No data available</td></tr>`;
    return;
  }

  container.innerHTML = items.map(i => `
    <tr class="border-b border-surface-container hover:bg-surface-container-low transition-colors">
      <td class="py-2.5 px-3 font-semibold text-sm text-on-surface">${i.name} <span class="text-xs font-mono text-on-surface-variant">(${i.sku})</span></td>
      <td class="py-2.5 px-3 text-xs text-on-surface-variant">${i.category || '-'}</td>
      <td class="py-2.5 px-3 text-right text-xs">${i.on_hand}</td>
      <td class="py-2.5 px-3 text-right text-xs font-bold text-primary">${i.shipped}</td>
      <td class="py-2.5 px-3 text-right text-xs font-mono">${formatMoney(i.stock_value)}</td>
      <td class="py-2.5 px-3 text-right text-xs font-semibold">${i.days_of_cover !== null ? i.days_of_cover + 'd' : 'N/A'}</td>
    </tr>
  `).join('');
}

async function fetchValuationReport() {
  try {
    const data = await window.api.get('/reports/valuation');
    if (!data) return;

    const totalEl = document.getElementById('reports-valuation-total');
    if (totalEl) totalEl.textContent = formatMoney(data.total);

    // Render Category Breakdown Bars
    const catContainer = document.getElementById('reports-valuation-category');
    if (catContainer) {
      const maxVal = Math.max(...(data.by_category || []).map(c => c.value), 1);
      catContainer.innerHTML = (data.by_category || []).map(c => {
        const pct = Math.round((c.value / maxVal) * 100);
        return `
          <div class="flex flex-col gap-1">
            <div class="flex justify-between text-xs font-semibold text-on-surface">
              <span>${c.name}</span>
              <span>${formatMoney(c.value)}</span>
            </div>
            <div class="w-full bg-surface-container rounded-full h-2 overflow-hidden">
              <div class="bg-primary-container h-full rounded-full" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Render Warehouse Breakdown Bars
    const whContainer = document.getElementById('reports-valuation-warehouse');
    if (whContainer) {
      const maxVal = Math.max(...(data.by_warehouse || []).map(w => w.value), 1);
      whContainer.innerHTML = (data.by_warehouse || []).map(w => {
        const pct = Math.round((w.value / maxVal) * 100);
        return `
          <div class="flex flex-col gap-1">
            <div class="flex justify-between text-xs font-semibold text-on-surface">
              <span>${w.name}</span>
              <span>${formatMoney(w.value)}</span>
            </div>
            <div class="w-full bg-surface-container rounded-full h-2 overflow-hidden">
              <div class="bg-tertiary-container h-full rounded-full" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }).join('');
    }

  } catch (e) {
    console.error("Error loading valuation report", e);
  }
}

function exportStockCsv() {
  window.api.download('/reports/export/stock.csv', 'stock_valuation_report.csv');
}

window.loadReportsPage = loadReportsPage;
window.fetchMoversReport = fetchMoversReport;
window.fetchValuationReport = fetchValuationReport;
window.exportStockCsv = exportStockCsv;
