// StockSense Authentication & Session Controller

let pendingResetEmail = "";

function showAuthScreen(subview = 'login') {
  const authShell = document.getElementById('auth-shell');
  const appShell = document.getElementById('app-shell');
  
  if (authShell) authShell.classList.remove('hidden');
  if (appShell) appShell.classList.add('hidden');

  showAuthSubview(subview);
}

function showAppShell() {
  const authShell = document.getElementById('auth-shell');
  const appShell = document.getElementById('app-shell');
  
  if (authShell) authShell.classList.add('hidden');
  if (appShell) appShell.classList.remove('hidden');
}

function showAuthSubview(name) {
  const views = ['login', 'signup', 'forgot-step1', 'forgot-step2'];
  views.forEach(v => {
    const el = document.getElementById(`auth-subview-${v}`);
    if (el) el.classList.add('hidden');
  });

  const target = document.getElementById(`auth-subview-${name}`);
  if (target) target.classList.remove('hidden');

  // Clear errors
  ['login-error', 'signup-error', 'forgot-step1-error', 'forgot-step2-error'].forEach(id => {
    const errEl = document.getElementById(id);
    if (errEl) {
      errEl.classList.add('hidden');
      errEl.textContent = '';
    }
  });
}

function setFormError(id, msg) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = msg;
    el.classList.remove('hidden');
  }
}

function fillDemoCredentials(role) {
  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');
  
  if (role === 'manager') {
    if (emailInput) emailInput.value = 'manager@stocksense.demo';
    if (passwordInput) passwordInput.value = 'demo1234';
  } else if (role === 'staff') {
    if (emailInput) emailInput.value = 'staff@stocksense.demo';
    if (passwordInput) passwordInput.value = 'demo1234';
  }
}

async function handleLoginSubmit(event) {
  if (event) event.preventDefault();

  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');
  const submitBtn = document.getElementById('login-submit-btn');

  const email = emailInput ? emailInput.value.trim() : '';
  const password = passwordInput ? passwordInput.value : '';

  if (!email || !password) {
    setFormError('login-error', 'Please enter both email and password.');
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in...';
  }

  try {
    const res = await window.api.login(email, password);
    window.setAuth(res.access_token, res.user);
    showAppShell();
    if (window.initAppAfterLogin) {
      window.initAppAfterLogin();
    }
    window.navigateView('dashboard');
    if (window.triggerToast) {
      window.triggerToast("Welcome Back", `Logged in as ${res.user.name} (${res.user.role.toUpperCase()})`);
    }
  } catch (err) {
    const msg = err.data && err.data.detail ? err.data.detail : (err.message || 'Login failed');
    setFormError('login-error', msg);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  }
}

async function handleSignupSubmit(event) {
  if (event) event.preventDefault();

  const nameInput = document.getElementById('signup-name');
  const emailInput = document.getElementById('signup-email');
  const passwordInput = document.getElementById('signup-password');
  const confirmInput = document.getElementById('signup-password-confirm');
  const submitBtn = document.getElementById('signup-submit-btn');

  const name = nameInput ? nameInput.value.trim() : '';
  const email = emailInput ? emailInput.value.trim() : '';
  const password = passwordInput ? passwordInput.value : '';
  const confirm = confirmInput ? confirmInput.value : '';

  if (!name || !email || !password) {
    setFormError('signup-error', 'All fields are required.');
    return;
  }

  if (password !== confirm) {
    setFormError('signup-error', 'Passwords do not match.');
    return;
  }

  if (password.length < 8) {
    setFormError('signup-error', 'Password must be at least 8 characters long.');
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';
  }

  try {
    const res = await window.api.signup(name, email, password);
    window.setAuth(res.access_token, res.user);
    showAppShell();
    if (window.initAppAfterLogin) {
      window.initAppAfterLogin();
    }
    window.navigateView('dashboard');
    if (window.triggerToast) {
      window.triggerToast("Account Created", `Welcome to StockSense, ${res.user.name}!`);
    }
  } catch (err) {
    const msg = err.data && err.data.detail ? (typeof err.data.detail === 'string' ? err.data.detail : JSON.stringify(err.data.detail)) : (err.message || 'Signup failed');
    setFormError('signup-error', msg);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Account';
    }
  }
}

async function handleForgotPasswordSubmit(event) {
  if (event) event.preventDefault();

  const emailInput = document.getElementById('forgot-email');
  const submitBtn = document.getElementById('forgot-submit-btn');
  const email = emailInput ? emailInput.value.trim() : '';

  if (!email) {
    setFormError('forgot-step1-error', 'Please enter your registered email address.');
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending code...';
  }

  try {
    const res = await window.api.forgotPassword(email);
    pendingResetEmail = email;

    const demoBox = document.getElementById('forgot-demo-code-box');
    const demoVal = document.getElementById('forgot-demo-code-val');
    const codeInput = document.getElementById('forgot-code');

    if (res.demo_code) {
      if (demoBox) demoBox.classList.remove('hidden');
      if (demoVal) demoVal.textContent = res.demo_code;
      if (codeInput) codeInput.value = res.demo_code;
    } else {
      if (demoBox) demoBox.classList.add('hidden');
      if (codeInput) codeInput.value = '';
    }

    const emailDisplay = document.getElementById('forgot-step2-email-display');
    if (emailDisplay) emailDisplay.textContent = email;

    showAuthSubview('forgot-step2');
    if (window.triggerToast) {
      window.triggerToast("Reset Code Sent", res.message || "A 6-digit code has been sent.");
    }
  } catch (err) {
    const msg = err.data && err.data.detail ? err.data.detail : (err.message || 'Request failed');
    setFormError('forgot-step1-error', msg);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Send Reset Code';
    }
  }
}

async function handleResetPasswordSubmit(event) {
  if (event) event.preventDefault();

  const codeInput = document.getElementById('forgot-code');
  const newPassInput = document.getElementById('forgot-new-password');
  const confirmInput = document.getElementById('forgot-confirm-password');
  const submitBtn = document.getElementById('forgot-reset-submit-btn');

  const code = codeInput ? codeInput.value.trim() : '';
  const newPassword = newPassInput ? newPassInput.value : '';
  const confirm = confirmInput ? confirmInput.value : '';

  if (!code || !newPassword) {
    setFormError('forgot-step2-error', 'Please enter the 6-digit code and a new password.');
    return;
  }

  if (newPassword !== confirm) {
    setFormError('forgot-step2-error', 'Passwords do not match.');
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Resetting password...';
  }

  try {
    const res = await window.api.resetPassword(pendingResetEmail, code, newPassword);
    if (window.triggerToast) {
      window.triggerToast("Password Reset Successful", res.message || "Password updated. You can log in now.");
    }
    showAuthSubview('login');
    const loginEmail = document.getElementById('login-email');
    if (loginEmail) loginEmail.value = pendingResetEmail;
    const loginPass = document.getElementById('login-password');
    if (loginPass) loginPass.value = '';
  } catch (err) {
    const msg = err.data && err.data.detail ? err.data.detail : (err.message || 'Password reset failed');
    setFormError('forgot-step2-error', msg);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Reset Password';
    }
  }
}

async function submitChangePassword() {
  const curPassInput = document.getElementById('profile-current-password');
  const newPassInput = document.getElementById('profile-new-password');
  const confirmInput = document.getElementById('profile-confirm-password');

  const current_password = curPassInput ? curPassInput.value : '';
  const new_password = newPassInput ? newPassInput.value : '';
  const confirm = confirmInput ? confirmInput.value : '';

  if (!current_password || !new_password) {
    if (window.triggerToast) window.triggerToast("Missing Fields", "Please enter your current and new password.");
    return;
  }

  if (new_password !== confirm) {
    if (window.triggerToast) window.triggerToast("Mismatch", "New password and confirmation do not match.");
    return;
  }

  try {
    const res = await window.api.changePassword(current_password, new_password);
    if (window.triggerToast) window.triggerToast("Success", res.message || "Password changed successfully.");
    if (curPassInput) curPassInput.value = '';
    if (newPassInput) newPassInput.value = '';
    if (confirmInput) confirmInput.value = '';
  } catch (err) {
    // Already toasted by api.js
  }
}

function handleLogout() {
  window.clearAuth();
  if (window.alertPollTimer) {
    clearInterval(window.alertPollTimer);
    window.alertPollTimer = null;
  }
  showAuthScreen('login');
  if (window.triggerToast) {
    window.triggerToast("Logged Out", "You have been safely signed out.");
  }
}

window.showAuthScreen = showAuthScreen;
window.showAppShell = showAppShell;
window.showAuthSubview = showAuthSubview;
window.fillDemoCredentials = fillDemoCredentials;
window.handleLoginSubmit = handleLoginSubmit;
window.handleSignupSubmit = handleSignupSubmit;
window.handleForgotPasswordSubmit = handleForgotPasswordSubmit;
window.handleResetPasswordSubmit = handleResetPasswordSubmit;
window.submitChangePassword = submitChangePassword;
window.handleLogout = handleLogout;
