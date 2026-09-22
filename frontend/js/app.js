/** 路由、側欄、畫面繪製、啟動。 */
import { api, clearSession, enterDemo, loadGames, loadStudents, useDemoFrontend } from "./api.js";
import {
  assignPage,
  bindLibTabScroller,
  clearMaterialConfigState,
  loadAssignLibrary,
  loadAssignment,
  loadStudentMaterialLists,
} from "./assign.js";
import { closeModal, el } from "./dom.js";
import { libraryPage, loadTags } from "./library.js";
import {
  ASSIGN_GAMES,
  INTENDED_KEY,
  TEACHER_KEY,
  TOKEN_KEY,
  bindRender,
  clearWorkflowState,
  hashPath,
  parseRoute,
  rememberIntended,
  s,
  view,
} from "./state.js";
import { studentsPage } from "./students.js";
import { loadWorkflow, selectedWorkflowStep, workflowPage } from "./workflow.js";
function goTo(page) {
  location.hash = page;
}

function navButton(game, page) {
  const route = parseRoute();
  const active = route.page === page && view.gameCode === game.code;
  return el("button", {
    class: active ? "nav-btn sub active" : "nav-btn sub",
    type: "button",
    text: game.name,
    onclick: () => goTo(`${page}/${game.code}`),
  });
}

function openAssignConfig(game, configId) {
  s.addingMaterialConfig = false;
  s.materialConfigId = configId;
  s.error = "";
  view.gameCode = game.code;
  const hash = `assign/${game.code}`;
  if (hashPath() === hash) {
    handleRoute();
    return;
  }
  goTo(hash);
}

function addAssignConfig(game) {
  if (view.studentId == null) {
    s.error = "請先新增並選擇學生";
    render();
    return;
  }
  s.addingMaterialConfig = true;
  s.materialConfigId = null;
  s.error = "";
  view.gameCode = game.code;
  const hash = `assign/${game.code}`;
  if (hashPath() === hash) {
    handleRoute();
    return;
  }
  goTo(hash);
}

let navConfigDrag = false;

function configRowActive(game, config) {
  const route = parseRoute();
  if (
    route.page === "assign" &&
    view.gameCode === game.code &&
    !s.addingMaterialConfig &&
    s.materialConfigId === config.id
  ) {
    return true;
  }
  if (route.page !== "workflow") {
    return false;
  }
  const step = selectedWorkflowStep();
  return step?.game === game.code && step?.gameMaterialCustomizationId === config.id;
}

/** 側欄一款遊戲的配置列。文字是遊戲代號與 id。加號進入新增狀態。 */
function assignGameBlock(game) {
  const list = s.materialLists[game.code] ?? [];
  return el(
    "div",
    { class: "nav-game-block" },
    el("p", { class: "nav-game-name", text: game.name }),
    el(
      "div",
      { class: "nav-config-list" },
      ...list.map((config) =>
        el("div", {
          class: configRowActive(game, config) ? "nav-config-item is-active" : "nav-config-item",
          role: "button",
          tabindex: "0",
          draggable: "true",
          text: `${game.code} ${config.id}`,
          onclick: () => {
            if (navConfigDrag) {
              return;
            }
            openAssignConfig(game, config.id);
          },
          onkeydown: (event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              openAssignConfig(game, config.id);
            }
          },
          ondragstart: (event) => {
            navConfigDrag = true;
            const payload = `config:${game.code}:${config.id}`;
            event.dataTransfer.setData("text/plain", payload);
            event.dataTransfer.setData("text", payload);
            event.dataTransfer.effectAllowed = "copy";
          },
          ondragend: () => {
            window.setTimeout(() => {
              navConfigDrag = false;
            }, 0);
          },
        }),
      ),
      el("button", {
        class: "nav-config-add",
        type: "button",
        text: "+",
        "aria-label": `新增${game.name}配置`,
        onclick: () => addAssignConfig(game),
      }),
    ),
  );
}

/** 側欄選學生。在關卡頁或配置頁換學生時，重新讀取該頁資料。 */
function studentSelect() {
  const select = el("select", { class: "nav-select", "aria-label": "選擇學生" });
  if (s.students.length === 0) {
    select.append(el("option", { value: "", text: "請先新增學生" }));
  }
  s.students.forEach((student) => {
    select.append(el("option", { value: student.id, text: student.username }));
  });
  select.value = view.studentId == null ? "" : String(view.studentId);
  select.addEventListener("change", async () => {
    view.studentId = select.value ? Number(select.value) : null;
    view.storylineIndex = 0;
    view.workflowIndex = 0;
    view.editingStart = false;
    s.addingMaterialConfig = false;
    s.materialConfigId = null;
    s.materialLists = {};
    s.materialListsStudentId = null;
    s.error = "";
    try {
      await loadStudentMaterialLists();
    } catch (err) {
      s.error = err.message;
    }
    if (parseRoute().page === "workflow") {
      try {
        await loadWorkflow();
      } catch (err) {
        s.error = err.message;
        clearWorkflowState();
      }
    }
    if (parseRoute().page === "assign") {
      try {
        await loadAssignment();
      } catch (err) {
        s.error = err.message;
        clearMaterialConfigState();
      }
    }
    render();
  });
  return select;
}

function renderNav() {
  const route = parseRoute();
  document.getElementById("nav").replaceChildren(
    el("p", { class: "brand", text: "LifeLessonPlan" }),
    el("button", {
      class: route.page === "home" ? "nav-btn active" : "nav-btn",
      type: "button",
      text: "首頁",
      onclick: () => goTo("home"),
    }),
    el("p", { class: "nav-section", text: "學生" }),
    studentSelect(),
    el("p", { class: "nav-section", text: "關卡流程" }),
    el("button", {
      class: route.page === "workflow" ? "nav-btn active" : "nav-btn",
      type: "button",
      text: "關卡配置",
      onclick: () => goTo("workflow"),
    }),
    el("p", { class: "nav-section", text: "遊戲配置" }),
    ...s.games.map((game) => assignGameBlock(game)),
    el("p", { class: "nav-section", text: "素材庫" }),
    ...s.games.map((game) => navButton(game, "materials")),
    el("button", {
      class: route.page === "students" ? "nav-btn active" : "nav-btn",
      type: "button",
      text: "學生",
      onclick: () => goTo("students"),
    }),
    el("button", { class: "nav-btn logout", type: "button", text: "登出", onclick: signOut }),
  );
}

function homePage() {
  const name = s.teacher?.username ?? "";
  return el(
    "section",
    {},
    el("p", { class: "eyebrow", text: "首頁" }),
    el("h2", { text: `你好，${name}` }),
    el("p", { class: "muted", text: "左邊「素材庫」可以管理各遊戲的分類與素材。" }),
  );
}

function renderContent() {
  const route = parseRoute();
  const content = document.getElementById("content");
  if (route.page === "materials") {
    content.replaceChildren(libraryPage());
    return;
  }
  if (route.page === "students") {
    content.replaceChildren(studentsPage());
    return;
  }
  if (route.page === "workflow") {
    content.replaceChildren(workflowPage());
    return;
  }
  if (route.page === "assign") {
    content.replaceChildren(assignPage());
    return;
  }
  content.replaceChildren(homePage());
}

async function signIn() {
  s.error = "";
  let result;
  try {
    result = await api("/api/auth/login", {
      isLogin: true,
      method: "POST",
      body: JSON.stringify({
        username: s.loginDraft.username.trim(),
        password: s.loginDraft.password,
      }),
    });
  } catch (err) {
    s.error = err.message;
    render();
    return;
  }
  s.token = result.token;
  s.teacher = result.teacher;
  localStorage.setItem(TOKEN_KEY, s.token);
  localStorage.setItem(TEACHER_KEY, JSON.stringify(s.teacher));
  s.loginDraft = { username: "", password: "" };
  const intended = sessionStorage.getItem(INTENDED_KEY) || "home";
  sessionStorage.removeItem(INTENDED_KEY);
  try {
    await loadGames();
    await loadStudents();
  } catch (err) {
    s.error = err.message;
  }
  if (hashPath() === intended) {
    await handleRoute();
    return;
  }
  location.hash = intended;
}

async function signOut() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch {
    // 後端 token 已失效時，仍在本地登出。
  }
  clearSession();
  sessionStorage.removeItem(INTENDED_KEY);
  s.error = "";
  closeModal();
  location.hash = "home";
  render();
}

function loginPage() {
  const username = el("input", { value: s.loginDraft.username, "aria-label": "帳號" });
  const password = el("input", {
    type: "password",
    value: s.loginDraft.password,
    "aria-label": "密碼",
  });
  return el(
    "form",
    {
      class: "card login-card",
      onsubmit: (event) => {
        event.preventDefault();
        s.loginDraft.username = username.value;
        s.loginDraft.password = password.value;
        signIn();
      },
    },
    el("p", { class: "eyebrow", text: "老師後台" }),
    el("h1", { text: "LifeLessonPlan" }),
    el("p", { class: "muted", text: "登入後會回到你原本要去的頁面。" }),
    el("label", {}, "帳號", username),
    el("label", {}, "密碼", password),
    s.error ? el("p", { class: "error", text: s.error }) : null,
    el("button", { type: "submit", text: "登入" }),
  );
}

function render() {
  const shell = document.getElementById("app-shell");
  const login = document.getElementById("login");
  if (!s.token) {
    clearWorkflowState();
    clearMaterialConfigState();
    shell.hidden = true;
    login.hidden = false;
    login.replaceChildren(loginPage());
    closeModal();
    return;
  }
  login.hidden = true;
  login.replaceChildren();
  shell.hidden = false;
  renderNav();
  renderContent();
  bindLibTabScroller();
}

function resolveGameCode(route) {
  if (route.gameCode && s.games.some((game) => game.code === route.gameCode)) {
    return route.gameCode;
  }
  return s.games[0]?.code ?? null;
}

async function handleRoute() {
  if (!s.token) {
    rememberIntended();
    render();
    return;
  }
  const route = parseRoute();
  if (!s.games.length) {
    try {
      await loadGames();
    } catch (err) {
      s.error = err.message;
    }
  }
  if (route.page === "students" || route.page === "workflow" || route.page === "assign") {
    try {
      await loadStudents();
    } catch (err) {
      s.error = err.message;
      s.students = [];
    }
  }
  if (view.studentId) {
    try {
      await loadStudentMaterialLists();
    } catch (err) {
      s.error = err.message;
    }
  }
  if (route.page === "workflow") {
    try {
      await loadWorkflow();
    } catch (err) {
      s.error = err.message;
      clearWorkflowState();
    }
    render();
    return;
  }
  if (route.page === "assign") {
    const nextGame = resolveGameCode(route);
    if (nextGame && route.gameCode !== nextGame) {
      location.hash = `assign/${nextGame}`;
      return;
    }
    view.gameCode = nextGame;
    if (ASSIGN_GAMES.has(nextGame)) {
      try {
        await loadAssignLibrary();
        await loadAssignment();
      } catch (err) {
        s.error = err.message;
        s.assignLibrary = [];
        clearMaterialConfigState();
      }
    }
    render();
    return;
  }
  if (route.page !== "materials") {
    render();
    return;
  }
  const nextGame = resolveGameCode(route);
  if (nextGame && route.gameCode !== nextGame) {
    location.hash = `materials/${nextGame}`;
    return;
  }
  if (view.gameCode !== nextGame) {
    view.tagCode = null;
  }
  view.gameCode = nextGame;
  s.addingTheme = false;
  try {
    await loadTags();
  } catch (err) {
    s.error = err.message;
    s.tags = [];
    s.materials = [];
  }
  render();
}

async function start() {
  if (await useDemoFrontend()) {
    enterDemo();
    await handleRoute();
    return;
  }
  if (!s.token) {
    rememberIntended();
    render();
    return;
  }
  try {
    s.teacher = await api("/api/me");
    localStorage.setItem(TEACHER_KEY, JSON.stringify(s.teacher));
    await loadGames();
    await loadStudents();
  } catch {
    rememberIntended();
  }
  await handleRoute();
}

// 其他模組的 render 呼叫此函式。
bindRender(render);

window.addEventListener("hashchange", () => {
  handleRoute();
});

start();

export {
  render,
  handleRoute,
  goTo,
};
