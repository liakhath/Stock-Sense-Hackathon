// StockSense API Client
const API = "http://localhost:8000/api";

let currentUser = localStorage.getItem("stocksense_user") || "manager";

function setCurrentUser(user) {
  currentUser = user;
  localStorage.setItem("stocksense_user", user);
  if (window.updateHeaderUser) {
    window.updateHeaderUser();
  }
}

function getCurrentUser() {
  return currentUser;
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
  headers["X-User"] = currentUser;
  
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
    window.triggerToast(`Error (${status})`, detailMsg);
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
      const res = await fetch(url, {
        headers: { "X-User": currentUser }
      });
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
        return true;
      }
    } catch(e) {
      showOfflineBanner(true);
    }
    return false;
  }
};

window.api = api;
