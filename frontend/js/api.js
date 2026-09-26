// StockSense API Client
const API = "http://localhost:8000/api";
const AUTH_KEY = "stocksense_auth";

function getAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function getToken() {
  const auth = getAuth();
  return auth ? auth.token : null;
}

function getAuthUser() {
  const auth = getAuth();
  return auth ? auth.user : null;
}

function getCurrentUser() {
  const user = getAuthUser();
  return user ? user.email : "";
}

function setAuth(token, user) {
  localStorage.setItem(AUTH_KEY, JSON.stringify({ token, user }));
  if (window.updateHeaderUser) {
    window.updateHeaderUser();
  }
  if (window.applyRolePermissions) {
    window.applyRolePermissions();
  }
}

function clearAuth() {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem("stocksense_user");
}

function formatMoney(amount) {
  if (amount === null || amount === undefined || isNaN(amount)) return "₹0";
  const num = Number(amount);
  return "₹" + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function showOfflineBanner(show) {
  let banner = document.getElementById("api-offline-banner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "api-offline-banner";
    banner.className = "fixed top-0 left-0 right-0 z-[110] bg-error text-on-error px-4 py-2 text-center font-bold text-sm shadow-md flex items-center justify-center gap-2";
    banner.innerHTML = `<span class="material-symbols-outlined text-[20px]">cloud_off</span> <span>API Offline - Cannot connect to backend server at http://localhost:8000/api</span>`;
    document.body.prepend(banner);
  }
  banner.style.display = show ? "flex" : "none";
}

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API}${endpoint}`;
  const headers = options.headers || {};
  
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  options.headers = headers;

  try {
    const res = await fetch(url, options);
    showOfflineBanner(false);

    if (res.status === 204) {
      return null;
    }

    const contentType = res.headers.get("content-type") || "";
    let data = null;
    if (contentType.includes("application/json")) {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      if (res.status === 401) {
        const isAuthPublic = endpoint.includes("/auth/login") || 
                             endpoint.includes("/auth/signup") || 
                             endpoint.includes("/auth/forgot-password") || 
                             endpoint.includes("/auth/reset-password");
        if (!isAuthPublic) {
          clearAuth();
          if (window.triggerToast) {
            window.triggerToast("Session expired", "Please log in again.");
          }
          if (window.showAuthScreen) {
            window.showAuthScreen("login");
          }
        }
      }
      handleApiError(res.status, data);
      const err = new Error(typeof data === "object" && data.detail ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)) : `HTTP ${res.status}`);
      err.status = res.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      showOfflineBanner(true);
      if (window.triggerToast) {
        window.triggerToast("API Offline", "Could not connect to the backend server.");
      }
    }
    throw err;
  }
}

function handleApiError(status, data) {
  if (!window.triggerToast) return;

  if (status === 422 && data && Array.isArray(data.detail)) {
    // Validation errors
    data.detail.forEach(item => {
      const field = item.loc ? item.loc[item.loc.length - 1] : "field";
      window.triggerToast(`Validation Error (${field})`, item.msg);
    });
  } else if (data && data.detail) {
    const detailMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    if (status === 403) {
      window.triggerToast("Access Denied", detailMsg);
    } else if (status === 401) {
      window.triggerToast("Authentication Required", detailMsg);
    } else {
      window.triggerToast(`Error (${status})`, detailMsg);
    }
  } else {
    window.triggerToast("Server Error", `Request failed with status ${status}`);
  }
}

const api = {
  get: (path, params = {}) => {
    const url = new URL(path.startsWith("http") ? path : `${API}${path}`);
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
        url.searchParams.append(k, params[k]);
      }
    });
    return request(url.toString(), { method: "GET" });
  },

  post: (path, body = {}) => {
    return request(path, {
      method: "POST",
      body: JSON.stringify(body)
    });
  },

  patch: (path, body = {}) => {
    return request(path, {
      method: "PATCH",
      body: JSON.stringify(body)
    });
  },

  upload: async (file, params = {}) => {
    const url = new URL(`${API}/import/products`);
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
        url.searchParams.append(k, params[k]);
      }
    });
    const formData = new FormData();
    formData.append("file", file);

    return request(url.toString(), {
      method: "POST",
      body: formData
    });
  },

  download: async (path, filename) => {
    const url = path.startsWith("http") ? path : `${API}${path}`;
    try {
      const headers = {};
      const token = getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(url, { headers });
      if (!res.ok) {
        let errData = {};
        try { errData = await res.json(); } catch(e){}
        handleApiError(res.status, errData);
        return;
      }
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = filename || "download.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
      if (window.triggerToast) {
        window.triggerToast("Download Started", `${filename} downloaded successfully.`);
      }
    } catch (err) {
      if (window.triggerToast) {
        window.triggerToast("Download Failed", err.message);
      }
    }
  },

  checkHealth: async () => {
    try {
      const data = await request("/health", { method: "GET" });
      if (data && data.status === "ok") {
        showOfflineBanner(false);
        return data;
      }
    } catch(e) {
      showOfflineBanner(true);
    }
    return null;
  },

  // Auth endpoints
  login: (email, password) => {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  },

  signup: (name, email, password) => {
    return request("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ name, email, password })
    });
  },

  forgotPassword: (email) => {
    return request("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email })
    });
  },

  resetPassword: (email, code, new_password) => {
    return request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ email, code, new_password })
    });
  },

  getMe: () => {
    return request("/auth/me", { method: "GET" });
  },

  changePassword: (current_password, new_password) => {
    return request("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password })
    });
  },

  getUsers: () => {
    return request("/auth/users", { method: "GET" });
  },

  createUser: (data) => {
    return request("/auth/users", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  updateUser: (userId, data) => {
    return request(`/auth/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(data)
    });
  }
};

window.api = api;
window.getAuth = getAuth;
window.getToken = getToken;
window.getAuthUser = getAuthUser;
window.getCurrentUser = getCurrentUser;
window.setAuth = setAuth;
window.clearAuth = clearAuth;
