/**
 * 共用常數與可變狀態。ES module 不能跨檔重新綁定 let。可變值放在 s。
 */
export const TOKEN_KEY = "llp-token";
export const TEACHER_KEY = "llp-teacher";
export const INTENDED_KEY = "llp-intended";
// 與 library.py PLACEHOLDER_COLORS 相同。
export const THEME_COLORS = ["#3d8b5c", "#2f7fd1", "#d45b8c", "#e07a2f", "#8b6914", "#4f7d8c", "#7a4bd4"];
/** 不含 gameCode 的頁面。未知 hash 當作首頁。 */
export const SIMPLE_PAGES = new Set(["home", "students", "workflow"]);
export const MEMORY_MATCH = "MemoryMatch";
export const PAIR_VACUUM = "PairVacuum";
export const DECISION_PARKOUR = "DecisionParkour";
export const SORT_ARENA = "SortArena";
export const MARKET_SHOPPING = "MarketShopping";
export const MARKET_BUDGET = "MarketShoppingBudgetMode";
export const ASSIGN_GAMES = new Set([
  MEMORY_MATCH,
  PAIR_VACUUM,
  DECISION_PARKOUR,
  SORT_ARENA,
  MARKET_SHOPPING,
  MARKET_BUDGET,
]);
export const THEME_SLOTS = ["theme_1", "theme_2", "theme_3", "theme_4"];
export const DISTRACTOR_SLOTS = [
  "distractor_1",
  "distractor_2",
  "distractor_3",
  "distractor_4",
  "distractor_5",
];
export const MEMORY_SLOTS = [...THEME_SLOTS, ...DISTRACTOR_SLOTS];
export const VACUUM_SLOTS = ["slot_1", "slot_2", "slot_3", "slot_4", "slot_5"];
export const PARKOUR_THEME_SLOTS = ["theme_1", "theme_2", "theme_3", "theme_4", "theme_5", "theme_6"];
export const PARKOUR_DISTRACTOR_SLOTS = [
  "distractor_1",
  "distractor_2",
  "distractor_3",
  "distractor_4",
  "distractor_5",
  "distractor_6",
  "distractor_7",
  "distractor_8",
  "distractor_9",
  "distractor_10",
  "distractor_11",
  "distractor_12",
];
export const PARKOUR_SLOTS = [...PARKOUR_THEME_SLOTS, ...PARKOUR_DISTRACTOR_SLOTS];
export const SORT_SLOTS = [
  "bin_1_1",
  "bin_1_2",
  "bin_1_3",
  "bin_1_4",
  "bin_1_5",
  "bin_2_1",
  "bin_2_2",
  "bin_2_3",
  "bin_2_4",
  "bin_2_5",
  "bin_3_1",
  "bin_3_2",
  "bin_3_3",
  "bin_3_4",
  "bin_3_5",
  "bin_4_1",
  "bin_4_2",
  "bin_4_3",
  "bin_4_4",
  "bin_4_5",
];
export const MARKET_SHELF_GROUPS = [
  { prefix: "shelf_regular", label: "普通貨架", count: 21 },
  { prefix: "shelf_veg", label: "蔬菜冷藏櫃", count: 4 },
  { prefix: "shelf_fruit", label: "水果櫃", count: 8 },
  { prefix: "shelf_meat", label: "肉類冷藏櫃", count: 4 },
  { prefix: "shelf_milk", label: "牛奶冷藏櫃", count: 1 },
  { prefix: "shelf_rice", label: "米櫃", count: 2 },
];
export const MARKET_SLOTS = MARKET_SHELF_GROUPS.flatMap((group) =>
  Array.from({ length: group.count }, (_, index) => `${group.prefix}_${index + 1}`),
);

export const view = {
  gameCode: null,
  tagCode: null,
  studentId: null,
  storylineIndex: 0,
  workflowIndex: 0,
  editingStart: false,
};

export const s = {
  token: localStorage.getItem(TOKEN_KEY),
  teacher: null,
  games: [],
  students: [],
  tags: [],
  materials: [],
  /** null 表示這份沒有 id。下次儲存使用 POST。 */
  materialConfigId: null,
  /** true 時，配置頁從 Default 開始編輯。下次儲存使用 POST。 */
  addingMaterialConfig: false,
  materialLists: {},
  materialListsStudentId: null,
  storylines: [],
  workflowStartNpcName: "",
  workflowStartDialogues: [""],
  demo: false,
  assignLibrary: [],
  assignLibTag: null,
  libTabScroll: 0,
  assignment: {
    tag: "",
    tags: [],
    items: {},
    Start_NPC_Name: "",
    Start_Dialogues: [""],
    basketOrder: [],
    prices: {},
    budget: "",
  },
  memoryPreview: "board",
  loginDraft: { username: "", password: "" },
  addingTheme: false,
  error: "",
  loading: false,
};

s.teacher = readStoredTeacher();

function readStoredTeacher() {
  if (!localStorage.getItem(TOKEN_KEY)) {
    return null;
  }
  const raw = localStorage.getItem(TEACHER_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") {
      return parsed;
    }
  } catch {
    return null;
  }
  return { username: raw };
}

function currentGame() {
  return s.games.find((game) => game.code === view.gameCode) ?? s.games[0] ?? null;
}

function currentTag() {
  return s.tags.find((tag) => tag.code === view.tagCode) ?? s.tags[0] ?? null;
}

/** 空 hash 當作首頁。 */
function hashPath() {
  return location.hash.replace(/^#/, "") || "home";
}

/** 把 hash 轉成頁面。未知路徑當作首頁。 */
function parseRoute() {
  const raw = hashPath();
  if (SIMPLE_PAGES.has(raw)) {
    return { page: raw, gameCode: null };
  }
  if (raw === "materials") {
    return { page: "materials", gameCode: null };
  }
  if (raw.startsWith("materials/")) {
    const code = raw.slice("materials/".length);
    if (code) {
      return { page: "materials", gameCode: code };
    }
  }
  if (raw === "assign") {
    return { page: "assign", gameCode: null };
  }
  if (raw.startsWith("assign/")) {
    const code = raw.slice("assign/".length);
    if (code) {
      return { page: "assign", gameCode: code };
    }
  }
  return { page: "home", gameCode: null };
}

/** 未登入時把已知目標頁寫入 sessionStorage。登入後再開該頁。首頁與未知路徑不寫入。 */
function rememberIntended() {
  const raw = hashPath();
  if (raw === "home") {
    return;
  }
  if (
    SIMPLE_PAGES.has(raw) ||
    raw === "materials" ||
    raw.startsWith("materials/") ||
    raw === "assign" ||
    raw.startsWith("assign/")
  ) {
    sessionStorage.setItem(INTENDED_KEY, raw);
  }
}

/** 清掉關卡頁的故事線、選線前開場與步驟選取。 */
function clearWorkflowState() {
  s.storylines = [];
  s.workflowStartNpcName = "";
  s.workflowStartDialogues = [""];
  view.storylineIndex = 0;
  view.workflowIndex = 0;
  view.editingStart = false;
}

/** app.js 啟動時註冊 render。 */
let registeredRender = () => {};

function bindRender(draw) {
  registeredRender = draw;
}

/** 其他模組經由此函式重繪。 */
const render = () => {
  registeredRender();
};

export {
  readStoredTeacher,
  currentGame,
  currentTag,
  hashPath,
  parseRoute,
  rememberIntended,
  clearWorkflowState,
  bindRender,
  render,
};
