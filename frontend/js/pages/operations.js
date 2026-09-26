// Operations Handler (Receipts, Deliveries, Transfers, Adjustments, and Operation Detail)

let currentOpType = 'receipt';
let activeOpDetail = null;
let createLineItems = [];
let cachedLocationsMap = null;

async function getLocationsMap() {
  if (cachedLocationsMap) return cachedLocationsMap;
  try {
    const locations = await window.api.get('/locations');
    cachedLocationsMap = {};
    (locations || []).forEach(l => {
      cachedLocationsMap[l.id] = `${l.warehouse} / ${l.name}`;
    });
  } catch (e) {
    cachedLocationsMap = {};
  }
  return cachedLocationsMap;
}

async function loadOperationsPage(type, params = {}) {
  currentOpType = type;
  await fetchOperationsList();
}

async function fetchOperationsList() {
  const containerId = `${currentOpType}s-table-body`;
  let tableBody = document.getElementById(containerId);
  if (!tableBody) {
    tableBody = document.getElementById(`op-list-table-body`);
  }
  if (!tableBody) return;

  const statusFilter = document.getElementById(`${currentOpType}s-filter-status`)?.value || '';

  try {
    const ops = await window.api.get('/operations', { type: currentOpType, status: statusFilter });
    
    if (!ops || ops.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-on-surface-variant font-label-md">No ${currentOpType} operations found</td></tr>`;
      return;
    }

    tableBody.innerHTML = ops.map(op => {
      const lineSummary = (op.lines || []).map(l => `${l.product_name || 'Item'} (x${l.qty})`).join(', ');
      
      let badgeClass = "bg-surface-container text-on-surface-variant";
      if (op.status === 'ready') badgeClass = "bg-primary-container/30 text-on-primary-fixed-variant";
      if (op.status === 'done') badgeClass = "bg-primary-container text-on-primary-container";
      if (op.status === 'waiting') badgeClass = "bg-tertiary-container/30 text-on-tertiary-container";
      if (op.status === 'canceled') badgeClass = "bg-error-container/30 text-on-error-container";

      return `
        <tr class="hover:bg-surface-container-low/70 cursor-pointer transition-colors" onclick="navigateView('operation-detail', { id: ${op.id} })">
          <td class="py-3.5 px-4 font-mono font-semibold text-primary">${op.ref}</td>
          <td class="py-3.5 px-4 font-medium text-on-surface">${lineSummary}</td>
          <td class="py-3.5 px-4 text-on-surface-variant text-xs">${op.partner || op.reason || op.note || '-'}</td>
          <td class="py-3.5 px-4 text-on-surface-variant text-xs">${new Date(op.created_at).toLocaleString()}</td>
          <td class="py-3.5 px-4 text-on-surface-variant text-xs">${op.created_by}</td>
          <td class="py-3.5 px-4"><span class="px-2.5 py-0.5 rounded-full ${badgeClass} font-label-sm text-label-sm font-semibold capitalize">${op.status}</span></td>
          <td class="py-3.5 px-4 text-center">
            <button class="text-label-sm font-label-sm text-primary font-bold hover:underline" onclick="event.stopPropagation(); navigateView('operation-detail', { id: ${op.id} })">Inspect</button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    tableBody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-error font-label-md">Error loading operations</td></tr>`;
  }
}

// Operation Detail View Handler
async function loadOperationDetail(id) {
  const container = document.getElementById('view-operation-detail');
  if (!container) return;

  try {
    const [op, locMap] = await Promise.all([
      window.api.get(`/operations/${id}`),
      getLocationsMap()
    ]);
    activeOpDetail = op;
    renderOperationDetail(op, locMap);
  } catch (e) {
    console.error("Error loading operation detail", e);
  }
}

function resolveLocationName(locId, isSource, opType, locMap) {
  if (!locId) {
    if (opType === 'receipt' && isSource) return 'Vendor';
    if (opType === 'delivery' && !isSource) return 'Customer';
    if (opType === 'adjustment') return 'Adjustment';
    return isSource ? 'Vendor' : 'Customer';
  }
  return (locMap && locMap[locId]) ? locMap[locId] : `Location #${locId}`;
}

function renderOperationDetail(op, locMap) {
  const refEl = document.getElementById('op-detail-ref');
  const typeEl = document.getElementById('op-detail-type');
  const statusBadge = document.getElementById('op-detail-status-badge');
  const metaEl = document.getElementById('op-detail-meta');
  const approvalBanner = document.getElementById('op-detail-approval-banner');
  const reversalBanner = document.getElementById('op-detail-reversal-banner');
  const actionButtons = document.getElementById('op-detail-action-buttons');
  const linesTable = document.getElementById('op-detail-lines-body');

  if (refEl) refEl.textContent = op.ref;
  if (typeEl) typeEl.textContent = op.type ? op.type.toUpperCase() : '';
  
  if (statusBadge) {
    statusBadge.textContent = op.status;
    let badgeClass = "bg-surface-container text-on-surface-variant";
    if (op.status === 'ready') badgeClass = "bg-primary-container/30 text-on-primary-fixed-variant";
    if (op.status === 'done') badgeClass = "bg-primary-container text-on-primary-container";
    if (op.status === 'waiting') badgeClass = "bg-tertiary-container/30 text-on-tertiary-container";
    if (op.status === 'canceled') badgeClass = "bg-error-container/30 text-on-error-container";
    statusBadge.className = `px-3 py-1 rounded-full font-label-sm text-label-sm font-bold capitalize ${badgeClass}`;
  }

  if (metaEl) {
    const srcName = resolveLocationName(op.src_location_id, true, op.type, locMap);
    const dstName = resolveLocationName(op.dst_location_id, false, op.type, locMap);
    const locInfo = `${srcName} → ${dstName}`;

    metaEl.innerHTML = `
      <div><strong>Partner / Reason:</strong> ${op.partner || op.reason || 'N/A'}</div>
      <div><strong>Note:</strong> ${op.note || 'N/A'}</div>
      <div><strong>Locations:</strong> ${locInfo}</div>
      <div><strong>Created by:</strong> ${op.created_by} at ${new Date(op.created_at).toLocaleString()}</div>
      ${op.validated_by ? `<div><strong>Validated by:</strong> ${op.validated_by} at ${new Date(op.validated_at).toLocaleString()}</div>` : ''}
      ${op.approved_by ? `<div><strong>Approved by:</strong> ${op.approved_by}</div>` : ''}
    `;
  }

  // Approval banner
  if (approvalBanner) {
    if (op.needs_approval && !op.approved_by) {
      const isCreator = (getCurrentUser() === op.created_by);
      approvalBanner.classList.remove('hidden');
      approvalBanner.innerHTML = `
        <div class="p-4 rounded-xl bg-tertiary-container/20 border border-tertiary-container flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-tertiary">gavel</span>
            <span class="font-headline-sm text-on-surface font-semibold">Awaiting Manager Approval</span>
          </div>
          <button class="px-4 py-2 rounded-xl bg-tertiary-container text-on-tertiary-container font-bold text-sm hover:brightness-105 ${isCreator ? 'opacity-50 cursor-not-allowed' : ''}"
                  ${isCreator ? 'disabled title="Cannot approve your own operation"' : `onclick="handleApproveOp(${op.id})"`}>
            Approve Operation
          </button>
        </div>
      `;
    } else {
      approvalBanner.classList.add('hidden');
    }
  }

  // Reversal Banner Links
  if (reversalBanner) {
    let revHtml = '';
    if (op.reverses_id) {
      revHtml += `<div class="p-3 bg-surface-container-low rounded-lg text-sm text-primary">Reversal of Operation ID #${op.reverses_id} <button class="underline font-bold ml-2" onclick="navigateView('operation-detail', {id: ${op.reverses_id}})">View Original</button></div>`;
    }
    if (op.reversed_by_id) {
      revHtml += `<div class="p-3 bg-surface-container-low rounded-lg text-sm text-error">Reversed by Operation ID #${op.reversed_by_id} <button class="underline font-bold ml-2" onclick="navigateView('operation-detail', {id: ${op.reversed_by_id}})">View Reversal</button></div>`;
    }
    reversalBanner.innerHTML = revHtml;
  }

  // Action Buttons
  if (actionButtons) {
    let btns = '';
    if (op.status === 'draft') {
      btns += `<button class="px-4 py-2 bg-surface-container hover:bg-surface-container-high rounded-xl font-bold text-sm" onclick="handleConfirmOp(${op.id})">Confirm</button>`;
      btns += `<button class="px-4 py-2 bg-primary-container text-on-primary-container hover:brightness-105 rounded-xl font-bold text-sm" onclick="handleValidateOp(${op.id})">Validate</button>`;
      btns += `<button class="px-4 py-2 bg-error-container/30 text-error hover:bg-error-container rounded-xl font-bold text-sm" onclick="handleCancelOp(${op.id})">Cancel</button>`;
    } else if (op.status === 'waiting') {
      btns += `<button class="px-4 py-2 bg-tertiary-container text-on-tertiary-container hover:brightness-105 rounded-xl font-bold text-sm" onclick="handleCheckAvailabilityOp(${op.id})">Check Availability</button>`;
      btns += `<button class="px-4 py-2 bg-error-container/30 text-error hover:bg-error-container rounded-xl font-bold text-sm" onclick="handleCancelOp(${op.id})">Cancel</button>`;
    } else if (op.status === 'ready') {
      btns += `<button class="px-4 py-2 bg-primary-container text-on-primary-container hover:brightness-105 rounded-xl font-bold text-sm" onclick="handleValidateOp(${op.id})">Validate</button>`;
      btns += `<button class="px-4 py-2 bg-error-container/30 text-error hover:bg-error-container rounded-xl font-bold text-sm" onclick="handleCancelOp(${op.id})">Cancel</button>`;
    } else if (op.status === 'done' && !op.reverses_id && !op.reversed_by_id) {
      btns += `<button class="px-4 py-2 bg-secondary-container text-on-secondary-container hover:brightness-105 rounded-xl font-bold text-sm flex items-center gap-1" onclick="handleReverseOp(${op.id})"><span class="material-symbols-outlined text-[18px]">undo</span><span>Reverse Operation</span></button>`;
    }
    actionButtons.innerHTML = btns;
  }

  // Lines table
  if (linesTable) {
    linesTable.innerHTML = (op.lines || []).map(l => `
      <tr class="border-b border-surface-container">
        <td class="py-3 px-4 font-bold text-on-surface">${l.product_name || 'Product'}</td>
        <td class="py-3 px-4 font-mono text-xs text-on-surface-variant">${l.sku || 'SKU'}</td>
        <td class="py-3 px-4 text-right font-bold text-primary">${l.qty}</td>
      </tr>
    `).join('');
  }
}

// Workflow Actions
async function handleConfirmOp(id) {
  try {
    const updated = await window.api.post(`/operations/${id}/confirm`);
    const locMap = await getLocationsMap();
    renderOperationDetail(updated, locMap);
    if (window.triggerToast) window.triggerToast("Operation Confirmed", `Status updated to ${updated.status}`);
  } catch(e){}
}

async function handleCheckAvailabilityOp(id) {
  try {
    const updated = await window.api.post(`/operations/${id}/check-availability`);
    const locMap = await getLocationsMap();
    renderOperationDetail(updated, locMap);
    if (window.triggerToast) window.triggerToast("Availability Checked", `Status updated to ${updated.status}`);
  } catch(e){}
}

async function handleValidateOp(id) {
  try {
    const updated = await window.api.post(`/operations/${id}/validate`);
    const locMap = await getLocationsMap();
    renderOperationDetail(updated, locMap);
    if (window.triggerToast) window.triggerToast("Operation Validated", "Stock position updated in ledger.");
  } catch (err) {
    if (err.status === 409) {
      // 409 Insufficient Stock: refresh op detail (stays in waiting)
      loadOperationDetail(id);
    }
  }
}

async function handleApproveOp(id) {
  try {
    const updated = await window.api.post(`/operations/${id}/approve`);
    const locMap = await getLocationsMap();
    renderOperationDetail(updated, locMap);
    if (window.triggerToast) window.triggerToast("Operation Approved", "Manager approval granted.");
  } catch(e){}
}

async function handleCancelOp(id) {
  try {
    const updated = await window.api.post(`/operations/${id}/cancel`);
    const locMap = await getLocationsMap();
    renderOperationDetail(updated, locMap);
    if (window.triggerToast) window.triggerToast("Operation Canceled", "Operation has been canceled.");
  } catch(e){}
}

async function handleReverseOp(id) {
  const note = prompt("Enter a reason/note for reversing this operation:");
  if (note === null) return;

  try {
    const newOp = await window.api.post(`/operations/${id}/reverse`, { note });
    if (window.triggerToast) window.triggerToast("Reversal Created", `Reversal operation ${newOp.ref} generated.`);
    navigateView('operation-detail', { id: newOp.id });
  } catch(e){}
}

// Create Operation Modal Handling
async function openCreateOperationModal(type) {
  currentOpType = type;
  createLineItems = [];

  const modal = document.getElementById('create-operation-modal');
  if (!modal) return;

  const title = document.getElementById('create-op-modal-title');
  if (title) title.textContent = `Create New ${type.charAt(0).toUpperCase() + type.slice(1)}`;

  // Populate locations
  try {
    const locations = await window.api.get('/locations');
    const locOptions = (locations || []).map(l => `<option value="${l.id}">${l.warehouse} / ${l.name}</option>`).join('');
    
    const srcSelect = document.getElementById('create-op-src-loc');
    const dstSelect = document.getElementById('create-op-dst-loc');
    const locSelect = document.getElementById('create-op-loc');

    if (srcSelect) srcSelect.innerHTML = locOptions;
    if (dstSelect) dstSelect.innerHTML = locOptions;
    if (locSelect) locSelect.innerHTML = locOptions;

    // Show/hide fields based on type
    const partnerGroup = document.getElementById('create-op-partner-group');
    const transferLocGroup = document.getElementById('create-op-transfer-loc-group');
    const singleLocGroup = document.getElementById('create-op-single-loc-group');
    const reasonGroup = document.getElementById('create-op-reason-group');

    if (partnerGroup) partnerGroup.classList.toggle('hidden', type !== 'receipt' && type !== 'delivery');
    if (transferLocGroup) transferLocGroup.classList.toggle('hidden', type !== 'internal');
    if (singleLocGroup) singleLocGroup.classList.toggle('hidden', type === 'internal');
    if (reasonGroup) reasonGroup.classList.toggle('hidden', type !== 'adjustment');

  } catch(e){}

  renderCreateLineItems();
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeCreateOperationModal() {
  const modal = document.getElementById('create-operation-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function addScanSkuLine() {
  const input = document.getElementById('create-op-sku-scan');
  if (!input) return;
  const sku = input.value.trim();
  if (!sku) return;

  try {
    const product = await window.api.get(`/products/sku/${encodeURIComponent(sku)}`);
    if (product) {
      // Fetch location on hand if adjustment
      let onHandAtLoc = null;
      if (currentOpType === 'adjustment') {
        const locId = Number(document.getElementById('create-op-loc')?.value);
        if (locId) {
          const stock = await window.api.get(`/products/${product.id}/stock`);
          const locStock = (stock.by_location || []).find(l => l.location_id === locId);
          onHandAtLoc = locStock ? locStock.on_hand : 0;
        }
      }

      createLineItems.push({
        product_id: product.id,
        name: product.name,
        sku: product.sku,
        qty: 1,
        on_hand: onHandAtLoc
      });
      input.value = '';
      renderCreateLineItems();
    }
  } catch(e){}
}

function renderCreateLineItems() {
  const container = document.getElementById('create-op-lines-container');
  if (!container) return;

  if (createLineItems.length === 0) {
    container.innerHTML = `<div class="p-3 text-center text-xs text-on-surface-variant">No items added yet. Scan SKU or search product above.</div>`;
    return;
  }

  container.innerHTML = createLineItems.map((item, idx) => `
    <div class="flex items-center justify-between p-2.5 bg-surface-container-low rounded-lg gap-2 text-sm">
      <div class="flex flex-col flex-1">
        <span class="font-semibold text-on-surface">${item.name} (${item.sku})</span>
        ${item.on_hand !== null && item.on_hand !== undefined ? `<span class="text-xs text-on-surface-variant">Current On Hand: ${item.on_hand}</span>` : ''}
      </div>
      <div class="flex items-center gap-2">
        <label class="text-xs font-semibold text-on-surface-variant">${currentOpType === 'adjustment' ? 'Counted Qty:' : 'Qty:'}</label>
        <input type="number" min="0" value="${item.qty}" class="w-20 px-2 py-1 bg-surface-container text-on-surface rounded text-right text-sm outline-none font-bold"
               onchange="createLineItems[${idx}].qty = Number(this.value)" />
        <button class="text-error hover:bg-error-container/30 p-1 rounded" onclick="createLineItems.splice(${idx},1); renderCreateLineItems();">
          <span class="material-symbols-outlined text-[18px]">delete</span>
        </button>
      </div>
    </div>
  `).join('');
}

async function submitCreateOperation() {
  if (createLineItems.length === 0) {
    if (window.triggerToast) window.triggerToast("Line Items Required", "Please add at least one line item.");
    return;
  }

  const note = document.getElementById('create-op-note')?.value.trim() || '';

  let endpoint = '';
  let payload = {};

  if (currentOpType === 'receipt') {
    endpoint = '/operations/receipts';
    payload = {
      location_id: Number(document.getElementById('create-op-loc')?.value),
      partner: document.getElementById('create-op-partner')?.value.trim() || '',
      note,
      lines: createLineItems.map(l => ({ product_id: l.product_id, qty: l.qty }))
    };
  } else if (currentOpType === 'delivery') {
    endpoint = '/operations/deliveries';
    payload = {
      location_id: Number(document.getElementById('create-op-loc')?.value),
      partner: document.getElementById('create-op-partner')?.value.trim() || '',
      note,
      lines: createLineItems.map(l => ({ product_id: l.product_id, qty: l.qty }))
    };
  } else if (currentOpType === 'internal') {
    const from_location_id = Number(document.getElementById('create-op-src-loc')?.value);
    const to_location_id = Number(document.getElementById('create-op-dst-loc')?.value);
    if (from_location_id === to_location_id) {
      if (window.triggerToast) window.triggerToast("Invalid Transfer", "Source and destination locations must differ.");
      return;
    }
    endpoint = '/operations/transfers';
    payload = {
      from_location_id,
      to_location_id,
      note,
      lines: createLineItems.map(l => ({ product_id: l.product_id, qty: l.qty }))
    };
  } else if (currentOpType === 'adjustment') {
    endpoint = '/operations/adjustments';
    const reason = document.getElementById('create-op-reason')?.value;
    if (!reason) {
      if (window.triggerToast) window.triggerToast("Missing Reason", "Adjustment reason is required.");
      return;
    }
    payload = {
      location_id: Number(document.getElementById('create-op-loc')?.value),
      reason,
      note,
      lines: createLineItems.map(l => ({ product_id: l.product_id, qty: l.qty }))
    };
  }

  try {
    const newOp = await window.api.post(endpoint, payload);
    closeCreateOperationModal();
    if (window.triggerToast) window.triggerToast("Operation Created", `Created ${newOp.ref}`);
    navigateView('operation-detail', { id: newOp.id });
  } catch(e){}
}

window.loadOperationsPage = loadOperationsPage;
window.fetchOperationsList = fetchOperationsList;
window.loadOperationDetail = loadOperationDetail;
window.renderOperationDetail = renderOperationDetail;
window.handleConfirmOp = handleConfirmOp;
window.handleCheckAvailabilityOp = handleCheckAvailabilityOp;
window.handleValidateOp = handleValidateOp;
window.handleApproveOp = handleApproveOp;
window.handleCancelOp = handleCancelOp;
window.handleReverseOp = handleReverseOp;
window.openCreateOperationModal = openCreateOperationModal;
window.closeCreateOperationModal = closeCreateOperationModal;
window.addScanSkuLine = addScanSkuLine;
window.renderCreateLineItems = renderCreateLineItems;
window.submitCreateOperation = submitCreateOperation;
