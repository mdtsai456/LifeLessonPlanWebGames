/** API 呼叫。
 * 不要手動設定 FormData 的 Content-Type。否則瀏覽器不會附加 boundary。
 * 登入的 401 表示帳密錯誤。其他端點的 401 表示 token 失效。
 */
import {
  MARKET_SHOPPING,
  TEACHER_KEY,
  TOKEN_KEY,
  rememberIntended,
  render,
  s,
  view,
} from "./state.js";

const DEMO_GAMES = [
  { code: "MarketShopping", name: "超市購物" },
  { code: "MarketShoppingBudgetMode", name: "超市購物預算模式" },
  { code: "MemoryMatch", name: "記憶配對" },
  { code: "PairVacuum", name: "配對吸塵" },
  { code: "SortArena", name: "分類競技場" },
  { code: "DecisionParkour", name: "決策跑酷" },
];

let demoMaterials = {};
let demoWorkflow = null;
let demoNextMaterialId = 1;

/** 使用 file:、網址含 demo，或健康檢查失敗時，改用示範資料。 */
async function useDemoFrontend() {
  if (location.protocol === "file:") {
    return true;
  }
  if (new URLSearchParams(location.search).has("demo")) {
    return true;
  }
  try {
    const response = await fetch("/api/health");
    return !response.ok;
  } catch {
    return true;
  }
}

function demoMaterialBody(gameCode) {
  return {
    game: gameCode,
    tag: "",
    tags: [],
    items: {},
    Start_NPC_Name: "",
    Start_Dialogues: [""],
    basketOrder: [],
    prices: {},
    budget: "",
  };
}

function emptyDemoWorkflow() {
  return {
    startNpcName: "",
    startDialogues: [""],
    storylines: [
      {
        name: "故事線1",
        order: 1,
        steps: [
          {
            game: MARKET_SHOPPING,
            gameMaterialCustomizationId: null,
            order: 1,
            endNpcName: "",
            endDialogues: [""],
          },
        ],
      },
    ],
  };
}

/** 把示範老師、六款遊戲、素材清單與故事線放進記憶體。 */
function enterDemo() {
  s.demo = true;
  s.token = "demo";
  s.teacher = { id: 0, username: "示範老師" };
  s.games = DEMO_GAMES.map((game) => ({ ...game }));
  s.students = [{ id: 1, username: "小明" }];
  s.assignLibrary = [];
  s.tags = [];
  s.materials = [];
  s.materialConfigId = null;
  s.addingMaterialConfig = false;
  s.materialLists = {};
  s.materialListsStudentId = null;
  s.storylines = [];
  s.workflowStartNpcName = "";
  s.workflowStartDialogues = [""];
  s.error = "";
  view.studentId = 1;
  view.gameCode = null;
  view.storylineIndex = 0;
  view.workflowIndex = 0;
  view.editingStart = false;
  demoMaterials = {};
  demoNextMaterialId = 1;
  DEMO_GAMES.forEach((game) => {
    demoMaterials[game.code] = [{ id: demoNextMaterialId, ...demoMaterialBody(game.code) }];
    demoNextMaterialId += 1;
  });
  demoWorkflow = emptyDemoWorkflow();
}

function demoGameCode(path) {
  const matched = path.match(/\/games\/([^/]+)/);
  return matched ? decodeURIComponent(matched[1]) : "";
}

function demoReadBody(options) {
  if (typeof options.body !== "string") {
    return {};
  }
  try {
    return JSON.parse(options.body);
  } catch {
    return {};
  }
}

/** 示範模式不呼叫後端。素材清單是陣列。流程是 storylines.steps。 */
function demoRespond(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  if (path === "/api/me") {
    return s.teacher;
  }
  if (path === "/api/games") {
    return s.games;
  }
  if (path === "/api/students" && method === "GET") {
    return s.students;
  }
  if (path.includes("/library")) {
    return [];
  }
  if (path.includes("/tags/") && path.endsWith("/materials")) {
    return { materials: [] };
  }
  if (path.includes("/tags")) {
    return [];
  }
  if (path.includes("/workflow")) {
    if (method === "PUT") {
      const body = demoReadBody(options);
      demoWorkflow = {
        startNpcName: typeof body.startNpcName === "string" ? body.startNpcName : "",
        startDialogues: Array.isArray(body.startDialogues) ? body.startDialogues : [""],
        storylines: Array.isArray(body.storylines) ? body.storylines : emptyDemoWorkflow().storylines,
      };
    }
    if (!demoWorkflow) {
      demoWorkflow = emptyDemoWorkflow();
    }
    return demoWorkflow;
  }
  if (path.endsWith("/materials/default")) {
    return demoMaterialBody(demoGameCode(path));
  }
  if (path.includes("/materials")) {
    const gameCode = demoGameCode(path);
    if (!demoMaterials[gameCode]) {
      demoMaterials[gameCode] = [];
    }
    const list = demoMaterials[gameCode];
    const idMatch = path.match(/\/materials\/(\d+)$/);
    if (method === "POST") {
      const created = {
        ...demoMaterialBody(gameCode),
        ...demoReadBody(options),
        id: demoNextMaterialId,
      };
      demoNextMaterialId += 1;
      list.push(created);
      return created;
    }
    if (idMatch) {
      const id = Number(idMatch[1]);
      const index = list.findIndex((item) => item.id === id);
      if (method === "PUT") {
        const updated = {
          ...(index >= 0 ? list[index] : demoMaterialBody(gameCode)),
          ...demoReadBody(options),
          id,
        };
        if (index >= 0) {
          list[index] = updated;
        } else {
          list.push(updated);
        }
        return updated;
      }
      return index >= 0 ? list[index] : null;
    }
    return list;
  }
  if (method === "POST" && path.includes("/auth/logout")) {
    return { status: "ok" };
  }
  return {};
}

async function api(path, options = {}) {
  if (s.demo) {
    return demoRespond(path, options);
  }
  const { isLogin = false, ...init } = options;
  const headers = {};
  if (s.token) {
    headers.Authorization = `Bearer ${s.token}`;
  }
  if (!(init.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(path, { ...init, headers });
  if (response.status === 401 && !isLogin) {
    clearSession();
    rememberIntended();
    s.error = "登入已失效，請重新登入";
    render();
    throw new Error(s.error);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    throw new Error(typeof detail === "string" ? detail : `伺服器錯誤（${response.status}）`);
  }
  if (response.status === 204) {
    return null;
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TEACHER_KEY);
  s.token = null;
  s.teacher = null;
  s.games = [];
  s.students = [];
  s.tags = [];
  s.materials = [];
  s.materialConfigId = null;
  s.addingMaterialConfig = false;
  s.materialLists = {};
  s.materialListsStudentId = null;
  s.storylines = [];
  s.workflowStartNpcName = "";
  s.workflowStartDialogues = [""];
  s.assignLibrary = [];
  s.demo = false;
  s.assignLibTag = null;
  s.libTabScroll = 0;
  s.assignment = {
    tag: "",
    tags: [],
    items: {},
    Start_NPC_Name: "",
    Start_Dialogues: [""],
    basketOrder: [],
    prices: {},
    budget: "",
  };
  s.memoryPreview = "board";
  view.gameCode = null;
  view.tagCode = null;
  view.studentId = null;
  view.storylineIndex = 0;
  view.workflowIndex = 0;
  view.editingStart = false;
}

async function loadGames() {
  s.games = await api("/api/games");
}

/** 登入後讀取這位老師的學生。目前選取的學生不在名單時改選第一位。 */
async function loadStudents() {
  s.students = (await api("/api/students")).map((student) => ({
    ...student,
    id: Number(student.id),
  }));
  if (view.studentId == null || !s.students.some((student) => student.id === view.studentId)) {
    view.studentId = s.students[0]?.id ?? null;
  }
}

export {
  api,
  clearSession,
  enterDemo,
  loadGames,
  loadStudents,
  useDemoFrontend,
};
