// Settings (Warehouses & Locations) Page Handler

async function loadSettings() {
  await fetchWarehousesAndLocations();
}

async function fetchWarehousesAndLocations() {
  const container = document.getElementById('settings-warehouses-container');
  if (!container) return;

  try {
    const [warehouses, locations] = await Promise.all([
      window.api.get('/warehouses'),
      window.api.get('/locations')
    ]);

    if (!warehouses || warehouses.length === 0) {
      container.innerHTML = `<div class="p-4 text-center text-on-surface-variant font-label-md">No warehouses provisioned</div>`;
      return;
    }

    container.innerHTML = warehouses.map(wh => {
      const whLocs = (locations || []).filter(l => l.warehouse === wh);

      return `
        <div class="bg-surface-container-lowest p-6 rounded-xl shadow-sm border border-surface-container flex flex-col gap-4">
          <div class="flex items-center justify-between border-b border-surface-container pb-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-primary-container/20 text-primary flex items-center justify-center font-bold">
                <span class="material-symbols-outlined">warehouse</span>
              </div>
              <div class="flex flex-col">
                <h3 class="font-headline-sm text-headline-sm font-bold text-on-surface">${wh}</h3>
                <span class="font-label-sm text-label-sm text-on-surface-variant">${whLocs.length} Active Storage Locations</span>
              </div>
            </div>
            <button class="px-3 py-1.5 rounded-lg bg-primary-container text-on-primary-container font-label-md font-bold text-xs hover:brightness-105"
                    onclick="openAddLocationModal('${wh}')">
              + Add Location
            </button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            ${whLocs.length === 0 ? `<div class="col-span-3 text-xs text-on-surface-variant py-2">No locations created yet in this warehouse</div>` : ''}
            ${whLocs.map(l => `
              <div class="p-3 bg-surface-container-low rounded-xl border border-surface-container flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-outline text-[18px]">place</span>
                  <span class="font-semibold text-sm text-on-surface">${l.name}</span>
                </div>
                <span class="font-mono text-xs text-on-surface-variant">ID: ${l.id}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }).join('');

    // Update warehouse options in Add Location Modal dropdown
    const selectWh = document.getElementById('add-loc-warehouse-select');
    if (selectWh) {
      selectWh.innerHTML = warehouses.map(w => `<option value="${w}">${w}</option>`).join('') + `<option value="__NEW__">+ Add New Warehouse...</option>`;
    }

  } catch (e) {
    container.innerHTML = `<div class="p-4 text-center text-error font-label-md">Failed to load settings</div>`;
  }
}

function handleAddLocationWarehouseChange() {
  const selectWh = document.getElementById('add-loc-warehouse-select');
  const newWhContainer = document.getElementById('add-loc-new-warehouse-container');
  if (!selectWh || !newWhContainer) return;

  if (selectWh.value === '__NEW__') {
    newWhContainer.classList.remove('hidden');
  } else {
    newWhContainer.classList.add('hidden');
  }
}

function openAddLocationModal(defaultWh = '') {
  const modal = document.getElementById('add-location-modal');
  if (!modal) return;

  const selectWh = document.getElementById('add-loc-warehouse-select');
  if (selectWh && defaultWh) {
    selectWh.value = defaultWh;
    handleAddLocationWarehouseChange();
  }

  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeAddLocationModal() {
  const modal = document.getElementById('add-location-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function submitAddLocation() {
  const selectWh = document.getElementById('add-loc-warehouse-select');
  const newWhInput = document.getElementById('add-loc-new-warehouse-input');
  const locNameInput = document.getElementById('add-loc-name-input');

  let warehouse = selectWh ? selectWh.value : '';
  if (warehouse === '__NEW__') {
    warehouse = newWhInput ? newWhInput.value.trim() : '';
  }

  const name = locNameInput ? locNameInput.value.trim() : '';

  if (!warehouse || !name) {
    if (window.triggerToast) window.triggerToast("Missing Fields", "Warehouse name and location name are required.");
    return;
  }

  try {
    const loc = await window.api.post('/locations', { warehouse, name });
    closeAddLocationModal();
    if (window.triggerToast) window.triggerToast("Location Provisioned", `Added ${loc.name} to ${loc.warehouse}`);
    await fetchWarehousesAndLocations();
  } catch(e){}
}

window.loadSettings = loadSettings;
window.fetchWarehousesAndLocations = fetchWarehousesAndLocations;
window.handleAddLocationWarehouseChange = handleAddLocationWarehouseChange;
window.openAddLocationModal = openAddLocationModal;
window.closeAddLocationModal = closeAddLocationModal;
window.submitAddLocation = submitAddLocation;
