// StockSense Users Management Page Handler (Managers Only)

let usersListCache = [];

async function loadUsersPage() {
  const currentUser = window.getAuthUser ? window.getAuthUser() : null;
  if (!currentUser || currentUser.role !== 'manager') {
    if (window.triggerToast) window.triggerToast("Access Denied", "Only managers can access user management.");
    if (window.navigateView) window.navigateView('dashboard');
    return;
  }

  await fetchUsersList();
}

async function fetchUsersList() {
  const tableBody = document.getElementById('users-table-body');
  if (!tableBody) return;

  tableBody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-on-surface-variant font-label-md">Loading team members...</td></tr>`;

  try {
    const users = await window.api.getUsers();
    usersListCache = users || [];

    if (!users || users.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-on-surface-variant font-label-md">No user accounts found.</td></tr>`;
      return;
    }

    const currentAuthUser = window.getAuthUser ? window.getAuthUser() : null;

    tableBody.innerHTML = users.map(u => {
      const isSelf = currentAuthUser && (currentAuthUser.id === u.id || currentAuthUser.email === u.email);
      const createdDate = new Date(u.created_at).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
      const avatarInitial = (u.name || 'U').charAt(0).toUpperCase();

      return `
        <tr class="border-b border-surface-container hover:bg-surface-container-low/60 transition-colors">
          <td class="py-3.5 px-4">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-xs uppercase shrink-0">
                ${avatarInitial}
              </div>
              <div class="flex flex-col">
                <span class="font-bold text-sm text-on-surface flex items-center gap-1.5">
                  ${u.name}
                  ${isSelf ? '<span class="text-[10px] bg-secondary-container text-on-secondary-container px-1.5 py-0.2 rounded font-bold">YOU</span>' : ''}
                </span>
                <span class="font-mono text-xs text-on-surface-variant">${u.email}</span>
              </div>
            </div>
          </td>
          <td class="py-3.5 px-4">
            <select onchange="handleUserRoleChange(${u.id}, this.value)" 
                    class="px-2.5 py-1 text-xs rounded-lg font-bold border border-surface-container bg-surface-container-low text-on-surface outline-none cursor-pointer">
              <option value="manager" ${u.role === 'manager' ? 'selected' : ''}>Manager</option>
              <option value="staff" ${u.role === 'staff' ? 'selected' : ''}>Staff</option>
            </select>
          </td>
          <td class="py-3.5 px-4">
            ${u.active 
              ? '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-primary-container/20 text-primary"><span class="w-1.5 h-1.5 rounded-full bg-primary"></span>Active</span>'
              : '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-error-container/30 text-error"><span class="w-1.5 h-1.5 rounded-full bg-error"></span>Disabled</span>'
            }
          </td>
          <td class="py-3.5 px-4 text-xs text-on-surface-variant">
            ${createdDate}
          </td>
          <td class="py-3.5 px-4 text-right">
            <button onclick="handleUserToggleActive(${u.id}, ${u.active})"
                    class="px-3 py-1 rounded-lg text-xs font-bold transition-colors ${u.active ? 'bg-error-container/30 text-error hover:bg-error-container' : 'bg-primary-container/30 text-on-primary-container hover:bg-primary-container'}">
              ${u.active ? 'Deactivate' : 'Activate'}
            </button>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-error font-label-md">Failed to load users: ${err.message || 'Error'}</td></tr>`;
  }
}

async function handleUserRoleChange(userId, newRole) {
  try {
    const updated = await window.api.updateUser(userId, { role: newRole });
    if (window.triggerToast) window.triggerToast("Role Updated", `Role changed to ${updated.role} for ${updated.name}`);
    await fetchUsersList();
  } catch (err) {
    // If backend 400 (e.g. self demote), fetchUsersList will revert dropdown
    await fetchUsersList();
  }
}

async function handleUserToggleActive(userId, currentActive) {
  try {
    const nextActive = !currentActive;
    const updated = await window.api.updateUser(userId, { active: nextActive });
    if (window.triggerToast) {
      window.triggerToast("Status Changed", `${updated.name} is now ${updated.active ? 'active' : 'disabled'}.`);
    }
    await fetchUsersList();
  } catch (err) {
    await fetchUsersList();
  }
}

function openAddUserModal() {
  const modal = document.getElementById('add-user-modal');
  const errBox = document.getElementById('add-user-error');
  if (errBox) {
    errBox.classList.add('hidden');
    errBox.textContent = '';
  }
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

function closeAddUserModal() {
  const modal = document.getElementById('add-user-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function submitAddUser() {
  const nameInput = document.getElementById('add-user-name');
  const emailInput = document.getElementById('add-user-email');
  const passInput = document.getElementById('add-user-password');
  const roleSelect = document.getElementById('add-user-role');
  const errBox = document.getElementById('add-user-error');

  const name = nameInput ? nameInput.value.trim() : '';
  const email = emailInput ? emailInput.value.trim() : '';
  const password = passInput ? passInput.value : '';
  const role = roleSelect ? roleSelect.value : 'staff';

  if (!name || !email || !password) {
    if (errBox) {
      errBox.textContent = 'Name, email, and password are required.';
      errBox.classList.remove('hidden');
    }
    return;
  }

  try {
    const newUser = await window.api.createUser({ name, email, password, role });
    closeAddUserModal();
    if (nameInput) nameInput.value = '';
    if (emailInput) emailInput.value = '';
    if (passInput) passInput.value = '';
    if (window.triggerToast) {
      window.triggerToast("User Created", `Successfully provisioned ${newUser.name} as ${newUser.role.toUpperCase()}`);
    }
    await fetchUsersList();
  } catch (err) {
    const msg = err.data && err.data.detail ? (typeof err.data.detail === 'string' ? err.data.detail : JSON.stringify(err.data.detail)) : (err.message || 'Failed to create user');
    if (errBox) {
      errBox.textContent = msg;
      errBox.classList.remove('hidden');
    }
  }
}

window.loadUsersPage = loadUsersPage;
window.fetchUsersList = fetchUsersList;
window.handleUserRoleChange = handleUserRoleChange;
window.handleUserToggleActive = handleUserToggleActive;
window.openAddUserModal = openAddUserModal;
window.closeAddUserModal = closeAddUserModal;
window.submitAddUser = submitAddUser;
