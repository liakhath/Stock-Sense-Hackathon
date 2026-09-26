// Import Products Page Handler

let selectedImportFile = null;
let importPreviewData = null;

function loadImportPage() {
  resetImportState();
}

function resetImportState() {
  selectedImportFile = null;
  importPreviewData = null;

  const fileInput = document.getElementById('import-file-input');
  const fileNameEl = document.getElementById('import-file-name');
  const previewSection = document.getElementById('import-preview-section');

  if (fileInput) fileInput.value = '';
  if (fileNameEl) fileNameEl.textContent = 'No file selected';
  if (previewSection) previewSection.classList.add('hidden');
}

function downloadImportTemplate() {
  window.api.download('/import/products/template', 'products_import_template.csv');
}

function handleImportFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {
    if (window.triggerToast) window.triggerToast("File Too Large", "Maximum allowed file size is 5MB.");
    event.target.value = '';
    return;
  }

  selectedImportFile = file;
  const fileNameEl = document.getElementById('import-file-name');
  if (fileNameEl) fileNameEl.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
}

async function previewImportFile() {
  if (!selectedImportFile) {
    if (window.triggerToast) window.triggerToast("No File", "Please select a .csv or .xlsx file to upload.");
    return;
  }

  const create_locations = document.getElementById('import-create-locations-toggle')?.checked ? 'true' : 'false';

  try {
    const res = await window.api.upload(selectedImportFile, { dry_run: 'true', create_locations });
    importPreviewData = res;
    renderImportPreview(res);
  } catch(e){}
}

function renderImportPreview(res) {
  const previewSection = document.getElementById('import-preview-section');
  if (!previewSection) return;

  previewSection.classList.remove('hidden');

  document.getElementById('import-summary-total').textContent = res.total_rows;
  document.getElementById('import-summary-created').textContent = res.created;
  document.getElementById('import-summary-updated').textContent = res.updated;
  document.getElementById('import-summary-skipped').textContent = res.skipped;

  const errTable = document.getElementById('import-errors-body');
  if (errTable) {
    if (!res.errors || res.errors.length === 0) {
      errTable.innerHTML = `<tr><td colspan="2" class="py-2 text-center text-primary font-semibold text-xs">No errors detected!</td></tr>`;
    } else {
      errTable.innerHTML = res.errors.map(err => `
        <tr class="border-b border-surface-container">
          <td class="py-1.5 px-3 font-bold text-error text-xs">Row ${err.row}</td>
          <td class="py-1.5 px-3 text-xs text-on-surface">${err.message}</td>
        </tr>
      `).join('');
    }
  }

  const warnTable = document.getElementById('import-warnings-body');
  if (warnTable) {
    if (!res.warnings || res.warnings.length === 0) {
      warnTable.innerHTML = `<tr><td colspan="2" class="py-2 text-center text-on-surface-variant text-xs">No warnings</td></tr>`;
    } else {
      warnTable.innerHTML = res.warnings.map(w => `
        <tr class="border-b border-surface-container">
          <td class="py-1.5 px-3 font-bold text-tertiary text-xs">Row ${w.row}</td>
          <td class="py-1.5 px-3 text-xs text-on-surface">${w.message}</td>
        </tr>
      `).join('');
    }
  }

  // Confirm button disabled if severe errors exist or no valid rows; hidden for staff
  const confirmBtn = document.getElementById('import-btn-confirm');
  if (confirmBtn) {
    const user = window.getAuthUser ? window.getAuthUser() : null;
    const isManager = user && user.role === 'manager';
    if (!isManager) {
      confirmBtn.style.display = 'none';
      let notice = document.getElementById('import-mgr-notice');
      if (!notice) {
        notice = document.createElement('div');
        notice.id = 'import-mgr-notice';
        notice.className = 'text-xs text-on-surface-variant font-semibold italic flex items-center gap-1';
        notice.innerHTML = '<span class="material-symbols-outlined text-[16px]">info</span> Only managers can confirm import.';
        confirmBtn.parentNode.insertBefore(notice, confirmBtn);
      }
      notice.style.display = 'flex';
    } else {
      confirmBtn.style.display = 'inline-flex';
      const notice = document.getElementById('import-mgr-notice');
      if (notice) notice.style.display = 'none';
      confirmBtn.disabled = (res.created === 0 && res.updated === 0);
    }
  }
}

async function confirmImportFile() {
  if (!selectedImportFile) return;

  const user = window.getAuthUser ? window.getAuthUser() : null;
  if (!user || user.role !== 'manager') {
    if (window.triggerToast) window.triggerToast("Access Denied", "Only managers can confirm import.");
    return;
  }

  const create_locations = document.getElementById('import-create-locations-toggle')?.checked ? 'true' : 'false';

  try {
    const res = await window.api.upload(selectedImportFile, { dry_run: 'false', create_locations });
    if (window.triggerToast) {
      window.triggerToast("Import Complete", `Successfully imported products. Created: ${res.created}, Updated: ${res.updated}.`);
    }
    resetImportState();
    navigateView('products');
  } catch(e){}
}

window.loadImportPage = loadImportPage;
window.downloadImportTemplate = downloadImportTemplate;
window.handleImportFileSelect = handleImportFileSelect;
window.previewImportFile = previewImportFile;
window.confirmImportFile = confirmImportFile;
