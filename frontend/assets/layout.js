// frontend/assets/layout.js

function getSession() {
  return {
    role: localStorage.getItem("role") || "",
    user_id: localStorage.getItem("user_id") || "",
    display_name: localStorage.getItem("display_name") || "",
  };
}

function roleLabel(role) {
  return ({ teacher:"老師", student:"學生", master:"HR" }[role] || role || "未知");
}

function navItemsByRole(role) {
  if (role === "student") {
    return [
      { href: "/student/index.html", text: "學生首頁" },
      { href: "/student/self.html", text: "自我評分" },
      { href: "/student/peer.html", text: "同儕評分" },
    ];
  }
  if (role === "teacher") {
    return [
      { href: "/teacher/index.html", text: "全班完成度" },
      { href: "/teacher/score.html", text: "老師評分" },
    ];
  }

  if (role === "master") {
    return [
      { href: "/master/index.html", text: "HR首頁" },
      { href: "/master/summary.html", text: "加權總分" },
      { href: "/master/analyze.html", text: "各項指標說明" },
      { href: "/master/match.html", text: "趣味分析" },      
      // 之後：儀表板、雷達圖、趣味分析
    ];
  }
  return [{ href: "/login.html", text: "回登入" }];
}

function renderLayout({ title = "" } = {}) {
  const s = getSession();
  const name = s.display_name || s.user_id || "Unknown";
  const navItems = navItemsByRole(s.role)
    .map(i => `<a href="${i.href}">${i.text}</a>`)
    .join("");

  document.getElementById("app").innerHTML = `
    <div class="topbar">
      <div class="container inner">
        <div class="brand">360績效互評系統</div>
        <div class="userbox">
          <span>${roleLabel(s.role)}｜${name}</span>
          <button class="btn" id="logoutBtn">登出</button>
        </div>
      </div>
    </div>

    <div class="container">
      <div class="grid">
        <aside class="card nav">
          <div class="h2">導覽</div>
          ${navItems}
        </aside>

        <section class="card">
          <div class="h1">${title}</div>
          <div id="page"></div>
        </section>
      </div>
    </div>
  `;

  document.getElementById("logoutBtn").addEventListener("click", () => {
    localStorage.clear();
    window.location.href = "/login.html";
  });
}


function apiFetch(url, options = {}) {
  const token = localStorage.getItem("access_token");
  const tokenType = localStorage.getItem("token_type") || "bearer";

  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `${tokenType} ${token}`;
  }

  return fetch(url, { ...options, headers });
}
