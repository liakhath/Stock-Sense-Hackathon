// Products & Catalog Page Handler

let currentSelectedProductId = null;
let currentProductData = null;

async function loadProducts(params = {}) {
  await populateProductFilterDropdowns();
  
  if (params.stock_status) {
    const statusSelect = document.getElementById('products-filter-status');
    if (statusSelect) statusSelect.value = params.stock_status;
  }

  await fetchProductsList();

  if (params.productId) {
    selectProductById(params.productId);
  }
}

async function populateProductFilterDropdowns() {
  try {
    const [warehouses, categories] = await Promise.all([
      window.api.get('/warehouses'),
      window.api.get('/products/categories')
    ]);

    const whSelect = document.getElementById('products-filter-warehouse');
    if (whSelect) {
      const cur = whSelect.value;
      whSelect.innerHTML = `<option value="">All Warehouses</option>` +
        (warehouses || []).map(w => `<option value="${w}">${w}</option>`).join('');
      whSelect.value = cur;
    }

    const catSelect = document.getElementById('products-filter-category');
    if (catSelect) {
      const cur = catSelect.value;
      catSelect.innerHTML = `<option value="">All Categories</option>` +
        (categories || []).map(c => `<option value="${c}">${c}</option>`).join('');
      catSelect.value = cur;
    }
  } catch (e) {
    console.error("Error populating product filter dropdowns", e);
  }
}

async function fetchProductsList() {
  const tableBody = document.getElementById('products-table-body');
  if (!tableBody) return;

  const q = document.getElementById('products-search-q')?.value || '';
  const category = document.getElementById('products-filter-category')?.value || '';
  const warehouse = document.getElementById('products-filter-warehouse')?.value || '';
  const stock_status = document.getElementById('products-filter-status')?.value || '';
  const include_archived = document.getElementById('products-toggle-archived')?.checked ? 'true' : 'false';

  try {
    const products = await window.api.get('/products', { q, category, warehouse, stock_status, include_archived });
    
    // Update summary counts
    const totalItemsEl = document.getElementById('products-summary-total-items');
    const totalUnitsEl = document.getElementById('products-summary-total-units');
    const lowStockCountEl = document.getElementById('products-summary-low-stock');
    const outOfStockCountEl = document.getElementById('products-summary-out-of-stock');

    if (products) {
      if (totalItemsEl) totalItemsEl.textContent = products.length.toLocaleString();
      if (totalUnitsEl) totalUnitsEl.textContent = products.reduce((sum, p) => sum + (p.on_hand || 0), 0).toLocaleString();
      if (lowStockCountEl) lowStockCountEl.textContent = products.filter(p => p.stock_status === 'low_stock').length.toLocaleString();
      if (outOfStockCountEl) outOfStockCountEl.textContent = products.filter(p => p.stock_status === 'out_of_stock').length.toLocaleString();
    }

    if (!products || products.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-on-surface-variant font-label-md">No products found matching filters</td></tr>`;
      return;
    }

    tableBody.innerHTML = products.map(p => {
      let badgeClass = "bg-primary-container/30 text-on-primary-fixed-variant";
      let statusLabel = "In Stock";
      if (p.stock_status === 'low_stock') {
        badgeClass = "bg-tertiary-container/30 text-on-tertiary-container";
        statusLabel = "Low Stock";
      } else if (p.stock_status === 'out_of_stock') {
        badgeClass = "bg-error-container text-on-error-container";
        statusLabel = "Out of Stock";
      }

      if (!p.active) {
        statusLabel += " (Archived)";
        badgeClass += " opacity-60";
      }

      return `
        <tr class="hover:bg-surface-container-low/70 cursor-pointer transition-colors ${p.id === currentSelectedProductId ? 'bg-surface-container-low/50' : ''}"
            onclick="selectProductById(${p.id})">
          <td class="py-3 px-4">
            <div class="flex flex-col">
              <span class="font-headline-sm text-body-lg font-bold text-on-surface">${p.name}</span>
              <span class="font-mono text-body-sm text-on-surface-variant">${p.sku} ${!p.active ? '<span class="text-error">(Archived)</span>' : ''}</span>
            </div>
          </td>
          <td class="py-3 px-4 text-on-surface-variant">${p.category || 'General'}</td>
          <td class="py-3 px-4 text-right font-semibold">${p.on_hand} ${p.uom || ''}</td>
          <td class="py-3 px-4 text-right text-on-surface-variant">${(p.on_hand - p.available) || 0}</td>
          <td class="py-3 px-4 text-right font-bold ${p.available <= 0 ? 'text-error' : 'text-primary'}">${p.available}</td>
          <td class="py-3 px-4 text-center">
            <span class="px-2.5 py-0.5 rounded-full ${badgeClass} font-label-sm text-label-sm font-semibold">${statusLabel}</span>
          </td>
        </tr>
      `;
    }).join('');

    // If a product was selected, re-select it or select first item
    if (currentSelectedProductId && products.some(p => p.id === currentSelectedProductId)) {
      selectProductById(currentSelectedProductId);
    } else if (products.length > 0) {
      selectProductById(products[0].id);
    }

  } catch (e) {
    tableBody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-error font-label-md">Failed to load products</td></tr>`;
  }
}

async function selectProductById(productId) {
  currentSelectedProductId = productId;
  const panel = document.getElementById('product-detail-panel');
  if (!panel) return;

  try {
    const [product, stockData, ledgerData] = await Promise.all([
      window.api.get(`/products/${productId}`),
      window.api.get(`/products/${productId}/stock`),
      window.api.get(`/ledger`, { product_id: productId, limit: 5 })
    ]);

    currentProductData = product;

    // Render basic panel info
    document.getElementById('panel-name').textContent = product.name;
    document.getElementById('panel-sku').textContent = product.sku;
    document.getElementById('panel-category').textContent = product.category || 'General';
    document.getElementById('panel-onhand').textContent = stockData.on_hand;
    document.getElementById('panel-reserved').textContent = stockData.reserved;
    document.getElementById('panel-available').textContent = stockData.available;
    document.getElementById('panel-uom').textContent = product.uom || 'units';

    const badge = document.getElementById('panel-badge');
    if (badge) {
      if (product.stock_status === 'out_of_stock') {
        badge.textContent = 'Out of Stock';
        badge.className = 'px-3 py-1 rounded-full font-label-sm text-label-sm font-semibold bg-error-container text-on-error-container';
      } else if (product.stock_status === 'low_stock') {
        badge.textContent = 'Low Stock';
        badge.className = 'px-3 py-1 rounded-full font-label-sm text-label-sm font-semibold bg-tertiary-container/30 text-on-tertiary-container';
      } else {
        badge.textContent = 'In Stock';
        badge.className = 'px-3 py-1 rounded-full font-label-sm text-label-sm font-semibold bg-primary-container/30 text-on-primary-fixed-variant';
      }
    }

    // Editable form fields
    const inputName = document.getElementById('panel-edit-name');
    const inputCategory = document.getElementById('panel-edit-category');
    const inputUom = document.getElementById('panel-edit-uom');
    const inputMinQty = document.getElementById('panel-edit-min-qty');
    const inputReorderQty = document.getElementById('panel-edit-reorder-qty');
    const inputUnitCost = document.getElementById('panel-edit-unit-cost');

    if (inputName) inputName.value = product.name;
    if (inputCategory) inputCategory.value = product.category;
    if (inputUom) inputUom.value = product.uom;
    if (inputMinQty) inputMinQty.value = product.min_qty;
    if (inputReorderQty) inputReorderQty.value = product.reorder_qty;
    if (inputUnitCost) inputUnitCost.value = product.unit_cost;

    // Archive / Restore button
    const archiveBtn = document.getElementById('panel-btn-archive');
    if (archiveBtn) {
      archiveBtn.textContent = product.active ? 'Archive Product' : 'Restore Product';
      archiveBtn.className = product.active 
        ? 'w-full py-2 px-3 rounded-xl bg-error-container/30 text-on-error-container hover:bg-error-container font-label-md font-semibold transition-colors'
        : 'w-full py-2 px-3 rounded-xl bg-primary-container/30 text-on-primary-container hover:bg-primary-container font-label-md font-semibold transition-colors';
    }

    // Render stock by location table
    const locTable = document.getElementById('panel-location-stock-body');
    if (locTable) {
      if (!stockData.by_location || stockData.by_location.length === 0) {
        locTable.innerHTML = `<tr><td colspan="4" class="py-2 text-center text-on-surface-variant text-xs">No location stock recorded</td></tr>`;
      } else {
        locTable.innerHTML = stockData.by_location.map(loc => `
          <tr class="border-b border-surface-container">
            <td class="py-1.5 px-2 text-xs font-medium">${loc.warehouse} / ${loc.location}</td>
            <td class="py-1.5 px-2 text-xs text-right">${loc.on_hand}</td>
            <td class="py-1.5 px-2 text-xs text-right text-on-surface-variant">${loc.reserved}</td>
            <td class="py-1.5 px-2 text-xs text-right font-bold text-primary">${loc.available}</td>
          </tr>
        `).join('');
      }
    }

    // Render recent product move history
    const ledgerTable = document.getElementById('panel-ledger-body');
    if (ledgerTable) {
      if (!ledgerData || ledgerData.length === 0) {
        ledgerTable.innerHTML = `<tr><td colspan="4" class="py-2 text-center text-on-surface-variant text-xs">No moves logged</td></tr>`;
      } else {
        ledgerTable.innerHTML = ledgerData.map(m => `
          <tr class="border-b border-surface-container">
            <td class="py-1.5 px-2 text-xs font-mono text-primary">${m.operation_ref || 'Direct'}</td>
            <td class="py-1.5 px-2 text-xs uppercase">${m.operation_type || 'Move'}</td>
            <td class="py-1.5 px-2 text-xs text-right font-bold">${m.qty > 0 ? '+' + m.qty : m.qty}</td>
            <td class="py-1.5 px-2 text-xs text-on-surface-variant">${new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</td>
          </tr>
        `).join('');
      }
    }

  } catch (e) {
    console.error("Error loading product detail", e);
  }
}

async function saveProductEdits() {
  if (!currentSelectedProductId || !currentProductData) return;

  const name = document.getElementById('panel-edit-name')?.value;
  const category = document.getElementById('panel-edit-category')?.value;
  const uom = document.getElementById('panel-edit-uom')?.value;
  const min_qty = Number(document.getElementById('panel-edit-min-qty')?.value);
  const reorder_qty = Number(document.getElementById('panel-edit-reorder-qty')?.value);
  const unit_cost = Number(document.getElementById('panel-edit-unit-cost')?.value);

  const payload = {};
  if (name !== currentProductData.name) payload.name = name;
  if (category !== currentProductData.category) payload.category = category;
  if (uom !== currentProductData.uom) payload.uom = uom;
  if (min_qty !== currentProductData.min_qty) payload.min_qty = min_qty;
  if (reorder_qty !== currentProductData.reorder_qty) payload.reorder_qty = reorder_qty;
  if (unit_cost !== currentProductData.unit_cost) payload.unit_cost = unit_cost;

  if (Object.keys(payload).length === 0) {
    if (window.triggerToast) window.triggerToast("No Changes", "No fields were modified.");
    return;
  }

  try {
    await window.api.patch(`/products/${currentSelectedProductId}`, payload);
    if (window.triggerToast) window.triggerToast("Product Updated", "Product details saved successfully.");
    await fetchProductsList();
  } catch (e) {
    // API toast error
  }
}

async function toggleArchiveProduct() {
  if (!currentSelectedProductId || !currentProductData) return;

  const newActiveState = !currentProductData.active;
  try {
    await window.api.patch(`/products/${currentSelectedProductId}`, { active: newActiveState });
    if (window.triggerToast) {
      window.triggerToast("Product Status Changed", newActiveState ? "Product restored." : "Product archived.");
    }
    await fetchProductsList();
  } catch (e) {}
}

// Create Product Modal Handling
async function openCreateProductModal() {
  const modal = document.getElementById('create-product-modal');
  if (!modal) return;

  // Populate locations dropdown
  try {
    const locations = await window.api.get('/locations');
    const locSelect = document.getElementById('create-product-location');
    if (locSelect) {
      locSelect.innerHTML = (locations || []).map(l => `<option value="${l.id}">${l.warehouse} / ${l.name}</option>`).join('');
    }
  } catch (e) {}

  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeCreateProductModal() {
  const modal = document.getElementById('create-product-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function handleInitialStockChange() {
  const stockInput = document.getElementById('create-product-initial-stock');
  const locContainer = document.getElementById('create-product-location-container');
  if (!stockInput || !locContainer) return;

  const val = Number(stockInput.value || 0);
  if (val > 0) {
    locContainer.classList.remove('hidden');
  } else {
    locContainer.classList.add('hidden');
  }
}

async function submitCreateProduct() {
  const name = document.getElementById('create-product-name')?.value.trim();
  const sku = document.getElementById('create-product-sku')?.value.trim();
  const category = document.getElementById('create-product-category')?.value.trim();
  const uom = document.getElementById('create-product-uom')?.value.trim();
  const min_qty = Number(document.getElementById('create-product-min-qty')?.value || 0);
  const reorder_qty = Number(document.getElementById('create-product-reorder-qty')?.value || 0);
  const unit_cost = Number(document.getElementById('create-product-unit-cost')?.value || 0);
  const initial_stock = Number(document.getElementById('create-product-initial-stock')?.value || 0);
  const location_id = initial_stock > 0 ? Number(document.getElementById('create-product-location')?.value) : null;

  if (!name || !sku || !category || !uom) {
    if (window.triggerToast) window.triggerToast("Missing Fields", "Name, SKU, Category and UOM are required.");
    return;
  }

  const payload = {
    name, sku, category, uom, min_qty, reorder_qty, unit_cost, initial_stock, location_id
  };

  try {
    const newProduct = await window.api.post('/products', payload);
    closeCreateProductModal();
    if (window.triggerToast) window.triggerToast("Product Created", `Created ${newProduct.name} (${newProduct.sku})`);
    currentSelectedProductId = newProduct.id;
    await fetchProductsList();
  } catch (e) {
    // API toast error
  }
}

window.loadProducts = loadProducts;
window.fetchProductsList = fetchProductsList;
window.selectProductById = selectProductById;
window.saveProductEdits = saveProductEdits;
window.toggleArchiveProduct = toggleArchiveProduct;
window.openCreateProductModal = openCreateProductModal;
window.closeCreateProductModal = closeCreateProductModal;
window.handleInitialStockChange = handleInitialStockChange;
window.submitCreateProduct = submitCreateProduct;
