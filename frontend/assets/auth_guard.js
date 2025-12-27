// frontend/assets/auth_guard.js

async function requireAuth(allowedRoles = []) {
  const tokenType = localStorage.getItem("token_type") || "bearer";
  const token = localStorage.getItem("access_token");
  const role = localStorage.getItem("role");
  const userId = localStorage.getItem("user_id");

  // 1) 沒 token：直接踢回登入頁
  if (!token || !role || !userId) {
    window.location.href = "/login.html";
    return;
  }

  // 2) 有允許角色限制：不符合也踢回登入頁
  if (allowedRoles.length > 0 && !allowedRoles.includes(role)) {
    localStorage.clear();
    window.location.href = "/login.html";
    return;
  }

  // 3) 跟後端確認 token 是否有效（避免只改 localStorage 就闖關）
  try {
    const resp = await fetch("/api/auth/me", {
      headers: {
        "Authorization": `${tokenType} ${token}`
      }
    });

    if (!resp.ok) {
      localStorage.clear();
      window.location.href = "/login.html";
      return;
    }

    // 可選：更新顯示用資訊
    const data = await resp.json();
    localStorage.setItem("role", data.role);
    localStorage.setItem("user_id", data.user_id);
    localStorage.setItem("display_name", data.display_name ?? "");

  } catch (e) {
    // 後端掛了 or 網路問題 → 保守做法：踢回登入
    window.location.href = "/login.html";
  }
}

function logout() {
  localStorage.clear();
  window.location.href = "/login.html";
}
