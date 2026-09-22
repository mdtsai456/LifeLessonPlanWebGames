/** 為學生設定各遊戲格子與開場 NPC 對話。 */
import { api } from "./api.js";
import { el, materialPreview, pageHeader } from "./dom.js";
import {
  ASSIGN_GAMES,
  DECISION_PARKOUR,
  DISTRACTOR_SLOTS,
  MARKET_BUDGET,
  MARKET_SHELF_GROUPS,
  MARKET_SHOPPING,
  MARKET_SLOTS,
  MEMORY_MATCH,
  MEMORY_SLOTS,
  PAIR_VACUUM,
  PARKOUR_DISTRACTOR_SLOTS,
  PARKOUR_SLOTS,
  PARKOUR_THEME_SLOTS,
  SORT_ARENA,
  SORT_SLOTS,
  THEME_SLOTS,
  VACUUM_SLOTS,
  currentGame,
  render,
  s,
  view,
} from "./state.js";

const assignLibCards = new Map();

function assignSlots() {
  switch (view.gameCode) {
    case MEMORY_MATCH:
      return MEMORY_SLOTS;
    case PAIR_VACUUM:
      return VACUUM_SLOTS;
    case DECISION_PARKOUR:
      return PARKOUR_SLOTS;
    case SORT_ARENA:
      return SORT_SLOTS;
    case MARKET_SHOPPING:
    case MARKET_BUDGET:
      return MARKET_SLOTS;
    default:
      return [];
  }
}

function emptyAssignment() {
  return {
    tag: "",
    tags: [],
    items: Object.fromEntries(assignSlots().map((key) => [key, ""])),
    Start_NPC_Name: "",
    Start_Dialogues: [""],
    basketOrder: [],
    prices: {},
    budget: "",
  };
}

function assignmentFromApi(payload) {
  const items = {};
  assignSlots().forEach((key) => {
    items[key] = payload.items?.[key] ? itemCodeFromValue(String(payload.items[key])) : "";
  });
  const lines = Array.isArray(payload.Start_Dialogues)
    ? payload.Start_Dialogues.map((line) => (typeof line === "string" ? line : "")).filter(
        (line) => line.trim().length > 0,
      )
    : [];
  const tags = Array.isArray(payload.tags)
    ? payload.tags.filter((code) => typeof code === "string" && code)
    : [];
  const basketOrder = Array.isArray(payload.basketOrder)
    ? payload.basketOrder.filter((code) => typeof code === "string" && code)
    : [];
  const prices = {};
  if (payload.prices && typeof payload.prices === "object") {
    Object.entries(payload.prices).forEach(([code, value]) => {
      const price = Number(value);
      if (Number.isFinite(price)) {
        prices[code] = price;
      }
    });
  }
  const budget =
    payload.budget == null || payload.budget === "" ? "" : String(payload.budget);
  return {
    tag: typeof payload.tag === "string" ? payload.tag : "",
    tags,
    items,
    Start_NPC_Name: typeof payload.Start_NPC_Name === "string" ? payload.Start_NPC_Name : "",
    Start_Dialogues: lines.length > 0 ? lines : [""],
    basketOrder,
    prices,
    budget,
  };
}

async function loadAssignLibrary() {
  assignLibCards.clear();
  if (!ASSIGN_GAMES.has(view.gameCode)) {
    s.assignLibrary = [];
    s.assignLibTag = null;
    return;
  }
  s.assignLibrary = await api(`/api/games/${view.gameCode}/library`);
}

/** 清單依 id 由小到大，略過沒有 id 的列。 */
function materialConfigList(payload) {
  if (!Array.isArray(payload)) {
    throw new Error("素材清單格式不對");
  }
  return payload
    .filter((item) => item && item.id != null)
    .map((item) => ({ ...item, id: Number(item.id) }))
    .filter((item) => Number.isInteger(item.id))
    .sort((a, b) => a.id - b.id);
}

function syncAssignBrowseTag() {
  const browseTag = view.gameCode === SORT_ARENA ? s.assignment.tags[0] : s.assignment.tag;
  s.assignLibTag = s.assignLibrary.some((tag) => tag.code === browseTag)
    ? browseTag
    : s.assignLibrary[0]?.code ?? null;
}

function clearMaterialConfigState() {
  s.materialConfigId = null;
  s.addingMaterialConfig = false;
  s.assignment = emptyAssignment();
}

/** 換學生時讀六款遊戲的素材清單，供側欄使用。 */
async function loadStudentMaterialLists() {
  const studentId = view.studentId;
  if (!studentId) {
    s.materialLists = {};
    s.materialListsStudentId = null;
    return;
  }
  if (s.materialListsStudentId === studentId) {
    return;
  }
  const lists = {};
  await Promise.all(
    [...ASSIGN_GAMES].map(async (code) => {
      lists[code] = materialConfigList(
        await api(`/api/students/${studentId}/games/${code}/materials`),
      );
    }),
  );
  if (view.studentId !== studentId) {
    return;
  }
  s.materialLists = lists;
  s.materialListsStudentId = studentId;
}

/** 新增狀態用 Default。有指定 id 就用那一筆。否則有列時選 id 最小的一筆。 */
async function loadAssignment() {
  if (!ASSIGN_GAMES.has(view.gameCode) || !view.studentId) {
    clearMaterialConfigState();
    return;
  }
  const studentId = view.studentId;
  const gameCode = view.gameCode;
  const adding = s.addingMaterialConfig;
  const requestedId = s.materialConfigId;
  const payload = await api(`/api/students/${studentId}/games/${gameCode}/materials`);
  if (view.studentId !== studentId || view.gameCode !== gameCode) {
    return;
  }
  const configs = materialConfigList(payload);
  s.materialLists[gameCode] = configs;
  if (adding) {
    s.addingMaterialConfig = true;
    await startNewMaterialConfig();
    return;
  }
  const chosen = configs.find((item) => item.id === requestedId);
  if (chosen) {
    s.materialConfigId = chosen.id;
    s.assignment = assignmentFromApi(chosen);
  } else if (configs.length === 0) {
    const defaults = await api(`/api/games/${gameCode}/materials/default`);
    if (view.studentId !== studentId || view.gameCode !== gameCode) {
      return;
    }
    s.materialConfigId = null;
    s.assignment = assignmentFromApi(defaults);
  } else {
    s.materialConfigId = configs[0].id;
    s.assignment = assignmentFromApi(configs[0]);
  }
  s.addingMaterialConfig = false;
  syncAssignBrowseTag();
}

/** 清除 id。配置改回 Default。下一筆儲存使用 POST。 */
async function startNewMaterialConfig() {
  if (!view.studentId || !ASSIGN_GAMES.has(view.gameCode)) {
    return;
  }
  const studentId = view.studentId;
  const gameCode = view.gameCode;
  try {
    const payload = await api(`/api/games/${gameCode}/materials/default`);
    if (view.studentId !== studentId || view.gameCode !== gameCode) {
      return;
    }
    s.materialConfigId = null;
    s.assignment = assignmentFromApi(payload);
    syncAssignBrowseTag();
    setAssignError("");
  } catch (err) {
    if (view.studentId !== studentId || view.gameCode !== gameCode) {
      return;
    }
    setAssignError(err.message);
  }
  if (view.studentId !== studentId || view.gameCode !== gameCode) {
    return;
  }
  render();
}

function memoryMaterial(code) {
  if (!code) {
    return null;
  }
  for (const tag of s.assignLibrary) {
    const found = tag.materials.find((item) => item.code === code);
    if (found) {
      return found;
    }
  }
  return { code, name: code, image_url: "" };
}

function themeHasMaterial(tagCode, materialCode) {
  const tag = s.assignLibrary.find((item) => item.code === tagCode);
  return Boolean(tag?.materials.some((item) => item.code === materialCode));
}

/** 格子值可能是 MAT003 或 /static/.../MAT003.png。畫面格子用大寫代碼。 */
function itemCodeFromValue(value) {
  const text = String(value || "").replaceAll("\\", "/");
  const match = text.match(/MAT[0-9]+/i);
  if (match) {
    return match[0].toUpperCase();
  }
  for (const tag of s.assignLibrary) {
    const found = (tag.materials ?? []).find(
      (item) => item.image_url === text || item.model_url === text || item.code === text,
    );
    if (found) {
      return found.code;
    }
  }
  return text;
}

/** 存檔送 /static/ 實際檔路徑。不寫 IP。 */
function itemStaticUrl(code) {
  const material = memoryMaterial(code);
  if (material?.image_url) {
    return material.image_url;
  }
  if (material?.model_url) {
    return material.model_url;
  }
  return code;
}

function materialTagCode(materialCode) {
  for (const tag of s.assignLibrary) {
    if (tag.materials.some((item) => item.code === materialCode)) {
      return tag.code;
    }
  }
  return null;
}

function applyThemeTag(tagCode, themeSlots, distractorSlots) {
  s.assignment.tag = tagCode;
  themeSlots.forEach((key) => {
    if (s.assignment.items[key] && !themeHasMaterial(tagCode, s.assignment.items[key])) {
      s.assignment.items[key] = "";
    }
  });
  distractorSlots.forEach((key) => {
    if (s.assignment.items[key] && themeHasMaterial(tagCode, s.assignment.items[key])) {
      s.assignment.items[key] = "";
    }
  });
}

function assignCanSave() {
  if (!view.studentId) {
    return false;
  }
  const filled = assignSlots().every((key) => s.assignment.items[key]);
  switch (view.gameCode) {
    case MEMORY_MATCH:
    case PAIR_VACUUM:
      return filled && Boolean(s.assignment.tag);
    case DECISION_PARKOUR:
      return filled && Boolean(s.assignment.tag);
    case SORT_ARENA:
      return filled && s.assignment.tags.length === 4;
    case MARKET_SHOPPING:
    case MARKET_BUDGET: {
      const filledKeys = MARKET_SLOTS.filter((key) => s.assignment.items[key]);
      if (filledKeys.length < 1) {
        return false;
      }
      const codes = new Set(filledKeys.map((key) => s.assignment.items[key]));
      const pricesOk = [...codes].every((code) => {
        const raw = s.assignment.prices[code];
        if (raw === "" || raw == null) {
          return false;
        }
        const price = Number(raw);
        return Number.isFinite(price) && price >= 0;
      });
      if (!pricesOk) {
        return false;
      }
      if (view.gameCode === MARKET_SHOPPING) {
        return (
          s.assignment.basketOrder.length > 0 &&
          s.assignment.basketOrder.every((code) => codes.has(code))
        );
      }
      return Number(s.assignment.budget) > 0;
    }
    default:
      return false;
  }
}

function setAssignError(message) {
  s.error = message;
  const node = document.getElementById("assign-error");
  if (!node) {
    return;
  }
  node.hidden = !message;
  node.textContent = message;
}

function fillSlotTile(node) {
  const slotKey = node.getAttribute("data-slot");
  if (!slotKey) {
    return;
  }
  const code = s.assignment.items[slotKey] || "";
  if (node.getAttribute("data-item") === code) {
    return;
  }
  node.setAttribute("data-item", code);
  let next;
  switch (view.gameCode) {
    case MARKET_SHOPPING:
    case MARKET_BUDGET:
      next = marketSlotTile(slotKey);
      break;
    default:
      next = memorySlotTile(slotKey, "");
      break;
  }
  node.replaceChildren(...next.children);
}

function refreshSlotCounts() {
  document.querySelectorAll("[data-count]").forEach((node) => {
    const kind = node.getAttribute("data-count");
    switch (kind) {
      case "theme":
        node.textContent = `正確格子 ${THEME_SLOTS.filter((key) => s.assignment.items[key]).length}/4`;
        break;
      case "wrong":
        node.textContent = `錯誤格子 ${DISTRACTOR_SLOTS.filter((key) => s.assignment.items[key]).length}/5`;
        break;
      case "vacuum":
        node.textContent = `吸塵格子 ${VACUUM_SLOTS.filter((key) => s.assignment.items[key]).length}/5`;
        break;
      default: {
        const group = MARKET_SHELF_GROUPS.find((item) => item.prefix === kind);
        if (group) {
          const keys = Array.from({ length: group.count }, (_, index) => `${group.prefix}_${index + 1}`);
          const filled = keys.filter((key) => s.assignment.items[key]).length;
          node.textContent = `${group.label} ${filled}/${group.count}`;
        }
        break;
      }
    }
  });
}

/** 依 s.assignment 更新現有配置頁節點。不重建整頁。 */
function syncAssignDom() {
  document.querySelectorAll("[data-slot]").forEach(fillSlotTile);
  refreshSlotCounts();
  refreshAssignSaveButton();
  refreshNpcLines();
  refreshMarketBasket();
  const errorNode = document.getElementById("assign-error");
  if (errorNode) {
    errorNode.hidden = !s.error;
    errorNode.textContent = s.error || "";
  }
  const npcName = document.querySelector(".npc-panel input");
  if (npcName) {
    npcName.value = s.assignment.Start_NPC_Name;
  }
  const budget = document.querySelector(".market-budget input");
  if (budget) {
    budget.value = s.assignment.budget;
  }
  document.querySelectorAll("[data-slot] .slot-price input").forEach((input) => {
    const slotKey = input.closest("[data-slot]")?.getAttribute("data-slot");
    const code = slotKey ? s.assignment.items[slotKey] : "";
    const priceValue = !code || s.assignment.prices[code] == null ? "" : String(s.assignment.prices[code]);
    input.value = priceValue;
  });
  switch (view.gameCode) {
    case DECISION_PARKOUR:
      refreshParkourThemePicker();
      break;
    case SORT_ARENA:
      refreshSortThemePicker();
      refreshSortBinTitles();
      break;
    default:
      break;
  }
}

/** 正確格全空時，第一個拖入的素材決定題目主題。素材庫分頁只篩選，不改主題。 */
function placeThemeSlots(slotKey, materialCode, allSlots, themeSlots, distractorSlots) {
  const firstThemeDrop =
    themeSlots.includes(slotKey) && themeSlots.every((key) => !s.assignment.items[key]);
  const nextTag = firstThemeDrop ? materialTagCode(materialCode) || s.assignment.tag : s.assignment.tag;
  const inTheme = themeHasMaterial(nextTag, materialCode);
  if (themeSlots.includes(slotKey) && !inTheme) {
    setAssignError("正確格只能放這個主題的素材");
    return;
  }
  if (distractorSlots.includes(slotKey) && inTheme) {
    setAssignError("錯誤格不能放題目主題的素材");
    return;
  }
  const used = allSlots.find((key) => key !== slotKey && s.assignment.items[key] === materialCode);
  if (used) {
    setAssignError("這個素材已經在其他格子");
    return;
  }
  if (firstThemeDrop && nextTag) {
    applyThemeTag(nextTag, themeSlots, distractorSlots);
  }
  s.assignment.items[slotKey] = materialCode;
  setAssignError("");
  syncAssignDom();
}

function placeMemory(slotKey, materialCode) {
  placeThemeSlots(slotKey, materialCode, MEMORY_SLOTS, THEME_SLOTS, DISTRACTOR_SLOTS);
}

function placeVacuum(slotKey, materialCode) {
  placeThemeSlots(slotKey, materialCode, VACUUM_SLOTS, VACUUM_SLOTS, []);
}

function refreshParkourThemePicker() {
  document.querySelectorAll(".memory-theme-pick .tab").forEach((tab, index) => {
    tab.classList.toggle("active", s.assignLibrary[index]?.code === s.assignment.tag);
  });
}

function setParkourTag(tagCode) {
  applyThemeTag(tagCode, PARKOUR_THEME_SLOTS, PARKOUR_DISTRACTOR_SLOTS);
  setAssignError("");
  syncAssignDom();
}

function placeParkour(slotKey, materialCode) {
  if (!s.assignment.tag) {
    setAssignError("請先選擇題目主題");
    return;
  }
  const inTheme = themeHasMaterial(s.assignment.tag, materialCode);
  if (PARKOUR_THEME_SLOTS.includes(slotKey) && !inTheme) {
    setAssignError("題目格只能放這個主題的素材");
    return;
  }
  if (PARKOUR_DISTRACTOR_SLOTS.includes(slotKey) && inTheme) {
    setAssignError("干擾格不能放題目主題的素材");
    return;
  }
  const used = PARKOUR_SLOTS.find((key) => key !== slotKey && s.assignment.items[key] === materialCode);
  if (used) {
    setAssignError("這個素材已經在其他格子");
    return;
  }
  s.assignment.items[slotKey] = materialCode;
  setAssignError("");
  syncAssignDom();
}

function remapFilled(oldIds, newIds) {
  const next = Object.fromEntries(SORT_SLOTS.map((key) => [key, ""]));
  newIds.forEach((id, newIndex) => {
    const oldIndex = oldIds.indexOf(id);
    if (oldIndex < 0) {
      return;
    }
    for (let slotIndex = 1; slotIndex <= 5; slotIndex += 1) {
      next[`bin_${newIndex + 1}_${slotIndex}`] = s.assignment.items[`bin_${oldIndex + 1}_${slotIndex}`] || "";
    }
  });
  return next;
}

function refreshSortThemePicker() {
  const pick = document.querySelector(".memory-theme-pick");
  if (!pick) {
    return;
  }
  const title = pick.querySelector(".memory-slot-title");
  if (title) {
    title.textContent = `分類主題 ${s.assignment.tags.length}/4`;
  }
  pick.querySelectorAll(".tabs .tab").forEach((tab, index) => {
    const tag = s.assignLibrary[index];
    if (!tag) {
      return;
    }
    const pickIndex = s.assignment.tags.indexOf(tag.code);
    const picked = pickIndex >= 0;
    tab.classList.toggle("picked", picked);
    tab.textContent = picked ? `${pickIndex + 1}. ${tag.name}` : tag.name;
  });
}

function refreshSortBinTitles() {
  const titles = document.querySelectorAll(
    ".memory-assign .market-shelf-scroll .market-shelf-group > .memory-slot-title",
  );
  titles.forEach((node, index) => {
    const tagCode = s.assignment.tags[index];
    const theme = s.assignLibrary.find((tag) => tag.code === tagCode);
    node.textContent = theme ? theme.name : `分類 ${index + 1}`;
  });
}

function toggleSortTag(tagCode) {
  if (s.assignment.tags.includes(tagCode)) {
    const nextIds = s.assignment.tags.filter((item) => item !== tagCode);
    s.assignment.items = remapFilled(s.assignment.tags, nextIds);
    s.assignment.tags = nextIds;
    setAssignError("");
    syncAssignDom();
    return;
  }
  if (s.assignment.tags.length >= 4) {
    setAssignError("已選滿 4 個主題，請先取消一個再換");
    return;
  }
  s.assignment.tags = s.assignment.tags.concat(tagCode);
  setAssignError("");
  refreshSortThemePicker();
  refreshSortBinTitles();
  refreshAssignSaveButton();
}

function placeSort(slotKey, materialCode) {
  if (s.assignment.tags.length !== 4) {
    setAssignError("請先選滿 4 個分類主題");
    return;
  }
  const binIndex = Number(slotKey.split("_")[1]) - 1;
  const tagCode = s.assignment.tags[binIndex];
  if (!themeHasMaterial(tagCode, materialCode)) {
    setAssignError("這個格子只能放這個分類的素材");
    return;
  }
  const used = SORT_SLOTS.find((key) => key !== slotKey && s.assignment.items[key] === materialCode);
  if (used) {
    setAssignError("這個素材已經在其他格子");
    return;
  }
  s.assignment.items[slotKey] = materialCode;
  setAssignError("");
  syncAssignDom();
}

function clearMemorySlot(slotKey) {
  s.assignment.items[slotKey] = "";
  setAssignError("");
  syncAssignDom();
}

function clearAssignSlots() {
  assignSlots().forEach((key) => {
    s.assignment.items[key] = "";
  });
  s.assignment.basketOrder = [];
  setAssignError("");
  syncAssignDom();
}

function addStartDialogueLine() {
  s.assignment.Start_Dialogues.push("");
  refreshNpcLines();
}

function deleteStartDialogueLine(lineIndex) {
  s.assignment.Start_Dialogues.splice(lineIndex, 1);
  if (s.assignment.Start_Dialogues.length === 0) {
    s.assignment.Start_Dialogues.push("");
  }
  refreshNpcLines();
}

async function saveAssignment() {
  if (!view.studentId || !ASSIGN_GAMES.has(view.gameCode)) {
    return;
  }
  const studentId = view.studentId;
  const gameCode = view.gameCode;
  const configId = s.materialConfigId;
  try {
    const payloadBody = {
      game: view.gameCode,
      items: Object.fromEntries(assignSlots().map((key) => [key, itemStaticUrl(s.assignment.items[key])])),
      Start_NPC_Name: s.assignment.Start_NPC_Name,
      Start_Dialogues: s.assignment.Start_Dialogues,
    };
    if (view.gameCode === MARKET_SHOPPING || view.gameCode === MARKET_BUDGET) {
      payloadBody.items = Object.fromEntries(
        MARKET_SLOTS.filter((key) => s.assignment.items[key]).map((key) => [
          key,
          itemStaticUrl(s.assignment.items[key]),
        ]),
      );
      const prices = {};
      MARKET_SLOTS.forEach((key) => {
        const code = s.assignment.items[key];
        if (code) {
          prices[code] = Number(s.assignment.prices[code]);
        }
      });
      payloadBody.prices = prices;
      payloadBody.basketOrder =
        view.gameCode === MARKET_SHOPPING ? s.assignment.basketOrder.slice() : [];
      if (view.gameCode === MARKET_BUDGET) {
        payloadBody.budget = Number(s.assignment.budget);
      }
    } else if (view.gameCode === SORT_ARENA) {
      payloadBody.tags = s.assignment.tags;
    } else {
      payloadBody.tag = s.assignment.tag;
    }
    const path =
      configId == null
        ? `/api/students/${studentId}/games/${gameCode}/materials`
        : `/api/students/${studentId}/games/${gameCode}/materials/${configId}`;
    const payload = await api(path, {
      method: configId == null ? "POST" : "PUT",
      body: JSON.stringify(payloadBody),
    });
    if (view.studentId !== studentId || view.gameCode !== gameCode || s.materialConfigId !== configId) {
      return;
    }
    const savedId = payload && payload.id != null ? Number(payload.id) : configId;
    if (!Number.isInteger(savedId)) {
      throw new Error("伺服器沒有回傳配置");
    }
    if (!s.materialLists[gameCode]) {
      s.materialLists[gameCode] = [];
    }
    const configs = s.materialLists[gameCode];
    const previous = configs.find((item) => item.id === savedId) ?? {};
    const stored = { ...previous, ...payload, id: savedId };
    const index = configs.findIndex((item) => item.id === savedId);
    if (index >= 0) {
      configs[index] = stored;
    } else {
      configs.push(stored);
    }
    configs.sort((a, b) => a.id - b.id);
    s.materialConfigId = savedId;
    s.addingMaterialConfig = false;
    s.assignment = assignmentFromApi(payload);
    syncAssignBrowseTag();
    setAssignError("");
    render();
  } catch (err) {
    if (view.studentId !== studentId || view.gameCode !== gameCode) {
      return;
    }
    setAssignError(err.message);
  }
}

function refreshAssignSaveButton() {
  const button = document.getElementById("save-assignment");
  if (button) {
    button.disabled = !assignCanSave();
  }
}

function placeMarket(slotKey, materialCode) {
  s.assignment.items[slotKey] = materialCode;
  setAssignError("");
  syncAssignDom();
}

function clearMarketSlot(slotKey) {
  s.assignment.items[slotKey] = "";
  s.assignment.basketOrder = s.assignment.basketOrder.filter((code) =>
    MARKET_SLOTS.some((key) => s.assignment.items[key] === code),
  );
  setAssignError("");
  syncAssignDom();
}

function addMarketBasket(code) {
  if (!code || s.assignment.basketOrder.includes(code)) {
    return;
  }
  s.assignment.basketOrder.push(code);
  setAssignError("");
  refreshMarketBasket();
  refreshAssignSaveButton();
}

function moveMarketBasket(index, dir) {
  const next = index + dir;
  if (next < 0 || next >= s.assignment.basketOrder.length) {
    return;
  }
  const current = s.assignment.basketOrder[index];
  s.assignment.basketOrder[index] = s.assignment.basketOrder[next];
  s.assignment.basketOrder[next] = current;
  refreshMarketBasket();
  refreshAssignSaveButton();
}

function removeMarketBasket(index) {
  s.assignment.basketOrder.splice(index, 1);
  refreshMarketBasket();
  refreshAssignSaveButton();
}

function marketBudgetField() {
  return el(
    "label",
    { class: "market-budget" },
    "預算",
    el("input", {
      inputmode: "decimal",
      value: s.assignment.budget,
      placeholder: "例如：100",
      oninput: (event) => {
        s.assignment.budget = event.target.value;
        refreshAssignSaveButton();
      },
    }),
  );
}

function marketBasketPanel() {
  const placed = [];
  MARKET_SLOTS.forEach((key) => {
    const code = s.assignment.items[key];
    if (code && !placed.includes(code)) {
      placed.push(code);
    }
  });
  const unused = placed.filter((code) => !s.assignment.basketOrder.includes(code));
  const rows = s.assignment.basketOrder.map((code, index) => {
    const material = memoryMaterial(code);
    const name = material?.name || code;
    return el(
      "div",
      { class: "basket-row" },
      el("span", { text: `${index + 1}. ${name}` }),
      el("button", {
        class: "ghost",
        type: "button",
        text: "上移",
        disabled: index === 0,
        onclick: () => moveMarketBasket(index, -1),
      }),
      el("button", {
        class: "ghost",
        type: "button",
        text: "下移",
        disabled: index === s.assignment.basketOrder.length - 1,
        onclick: () => moveMarketBasket(index, 1),
      }),
      el("button", {
        class: "ghost",
        type: "button",
        text: "刪除",
        onclick: () => removeMarketBasket(index),
      }),
    );
  });
  const addButtons = unused.map((code) => {
    const material = memoryMaterial(code);
    return el("button", {
      class: "tab",
      type: "button",
      text: material?.name || code,
      onclick: () => addMarketBasket(code),
    });
  });
  return el(
    "div",
    { class: "market-basket" },
    el("p", { class: "memory-slot-title", text: `購物清單 ${s.assignment.basketOrder.length}` }),
    rows.length > 0 ? rows : el("p", { class: "muted", text: "先上架商品，再加入清單" }),
    addButtons.length > 0 ? el("div", { class: "tabs" }, ...addButtons) : null,
  );
}

function refreshMarketBasket() {
  const current = document.querySelector(".market-basket");
  if (!current) {
    return;
  }
  current.replaceWith(marketBasketPanel());
}

function marketSlotTile(slotKey) {
  const code = s.assignment.items[slotKey] || "";
  const material = memoryMaterial(code);
  const tile = el("div", {
    class: "slot-tile",
    "data-slot": slotKey,
    "data-item": code,
    ondragover: (event) => event.preventDefault(),
    ondrop: (event) => {
      event.preventDefault();
      const code = event.dataTransfer.getData("text/plain");
      if (code) {
        placeMarket(slotKey, code);
      }
    },
  });
  if (!material || !code) {
    tile.append(el("span", { class: "muted", text: "拖進來" }));
    return tile;
  }
  const theme = s.assignLibrary.find((tag) => tag.materials.some((item) => item.code === code));
  const priceValue = s.assignment.prices[code] == null ? "" : String(s.assignment.prices[code]);
  tile.append(
    materialPreview(material, theme),
    el("strong", { text: material.name }),
    el(
      "label",
      { class: "slot-price" },
      "$",
      el("input", {
        inputmode: "decimal",
        value: priceValue,
        placeholder: "0",
        oninput: (event) => {
          s.assignment.prices[code] = event.target.value;
          refreshAssignSaveButton();
        },
      }),
    ),
    el("button", {
      class: "ghost slot-clear",
      type: "button",
      text: "×",
      "aria-label": `移除 ${material.name}`,
      onclick: () => clearMarketSlot(slotKey),
    }),
  );
  return tile;
}

function assignHeader(game, extra) {
  return el(
    "header",
    { class: "page-header" },
    el(
      "div",
      {},
      el("p", { class: "eyebrow", text: "遊戲配置" }),
      el(
        "div",
        { class: "title-row" },
        el("h2", { text: game.name }),
        s.materialConfigId == null ? el("span", { class: "unsaved-mark", text: "尚未儲存" }) : null,
      ),
    ),
    extra ?? null,
  );
}

function assignShell(game, sectionClass, rule, board) {
  const saveBtn = el("button", {
    id: "save-assignment",
    type: "button",
    text: "儲存配置",
    disabled: !assignCanSave(),
    onclick: saveAssignment,
  });
  const clearBtn = el("button", {
    class: "ghost",
    type: "button",
    text: "清除全部格子",
    disabled: !view.studentId,
    onclick: clearAssignSlots,
  });
  return el(
    "section",
    { class: sectionClass },
    assignHeader(game, el("div", { class: "toolbar" }, saveBtn, clearBtn)),
    el("p", {
      id: "assign-error",
      class: "error",
      hidden: !s.error,
      text: s.error || "",
    }),
    rule,
    el(
      "div",
      { class: "memory-layout" },
      el(
        "div",
        { class: "memory-preview", onclick: () => setMemoryPreview("board") },
        el("img", {
          class: "memory-preview-img",
          src: memoryPreviewSrc(),
          alt: memoryPreviewAlt(),
        }),
      ),
      startNpcPanel(),
      el("div", { class: "card memory-card", onclick: () => setMemoryPreview("board") }, ...board),
      memoryLibraryPanel(),
    ),
  );
}

function marketAssignPage(game) {
  const isBudget = view.gameCode === MARKET_BUDGET;
  const groups = MARKET_SHELF_GROUPS.map((group) => {
    const keys = Array.from({ length: group.count }, (_, index) => `${group.prefix}_${index + 1}`);
    const filled = keys.filter((key) => s.assignment.items[key]).length;
    return el(
      "div",
      { class: "market-shelf-group" },
      el("p", {
        class: "memory-slot-title",
        "data-count": group.prefix,
        text: `${group.label} ${filled}/${group.count}`,
      }),
      el("div", { class: "slot-grid market-shelves" }, ...keys.map((key) => marketSlotTile(key))),
    );
  });
  return assignShell(
    game,
    "memory-assign is-wide",
    el(
      "div",
      { class: "memory-rule" },
      el("h3", {
        class: "memory-rule-title",
        text: isBudget ? "在預算內選購貨架上的商品" : "依購物清單順序在貨架上拿取指定商品",
      }),
      el("p", {
        class: "muted memory-rule-copy",
        text: isBudget
          ? "從素材庫把商品拖上貨架，填寫價格與預算。學生在額度內選購。"
          : "從素材庫把商品拖上貨架，填寫價格，再把已上架商品加入購物清單。學生須依清單順序拿對商品。",
      }),
      isBudget ? marketBudgetField() : null,
    ),
    [
      el("p", { class: "eyebrow", text: "貨架配置" }),
      isBudget ? null : marketBasketPanel(),
      el("div", { class: "market-shelf-scroll" }, ...groups),
    ],
  );
}

function memorySlotTile(slotKey, kind, onPlace) {
  const code = s.assignment.items[slotKey] || "";
  const material = memoryMaterial(code);
  const place = onPlace || placeMemory;
  const tile = el("div", {
    class: `slot-tile ${kind}`,
    "data-slot": slotKey,
    "data-item": code,
    ondragover: (event) => event.preventDefault(),
    ondrop: (event) => {
      event.preventDefault();
      const code = event.dataTransfer.getData("text/plain");
      if (code) {
        place(slotKey, code);
      }
    },
  });
  if (!material || !code) {
    tile.append(el("span", { class: "muted", text: "拖進來" }));
    return tile;
  }
  tile.append(
    materialPreview(
      material,
      s.assignLibrary.find((tag) => tag.materials.some((item) => item.code === code)),
    ),
    el("strong", { text: material.name }),
    el("button", {
      class: "ghost slot-clear",
      type: "button",
      text: "×",
      "aria-label": `移除 ${material.name}`,
      onclick: () => clearMemorySlot(slotKey),
    }),
  );
  return tile;
}

function memoryPreviewSrc() {
  const isNpc = s.memoryPreview === "npc";
  switch (view.gameCode) {
    case MARKET_SHOPPING:
    case MARKET_BUDGET:
      return isNpc ? "images/market-npc.png" : "images/market-board.png";
    default:
      return isNpc ? "images/memory-npc.png" : "images/memory-board.png";
  }
}

function memoryPreviewAlt() {
  if (s.memoryPreview === "npc") {
    return "NPC 說話畫面";
  }
  switch (view.gameCode) {
    case MARKET_SHOPPING:
    case MARKET_BUDGET:
      return "貨架畫面";
    default:
      return "遊戲畫面";
  }
}

function setMemoryPreview(mode) {
  if (mode !== "board" && mode !== "npc") {
    return;
  }
  if (s.memoryPreview === mode) {
    return;
  }
  s.memoryPreview = mode;
  const image = document.querySelector(".memory-preview-img");
  if (!image) {
    return;
  }
  image.src = memoryPreviewSrc();
  image.alt = memoryPreviewAlt();
}

function npcLineRow(text, lineIndex) {
  return el(
    "div",
    { class: "npc-line" },
    el("textarea", {
      rows: "2",
      placeholder: "例如：請找出四個可以吃的食物",
      text,
      oninput: (event) => {
        s.assignment.Start_Dialogues[lineIndex] = event.target.value;
      },
    }),
    el("button", {
      class: "ghost",
      type: "button",
      text: "刪除",
      onclick: () => deleteStartDialogueLine(lineIndex),
    }),
  );
}

function refreshNpcLines() {
  const box = document.querySelector(".npc-lines");
  if (!box) {
    return;
  }
  const lines = s.assignment.Start_Dialogues;
  if (box.children.length === lines.length) {
    [...box.children].forEach((row, index) => {
      const textarea = row.querySelector("textarea");
      if (textarea && textarea.value !== lines[index]) {
        textarea.value = lines[index];
      }
    });
    return;
  }
  box.replaceChildren(...lines.map((text, lineIndex) => npcLineRow(text, lineIndex)));
}

function startNpcPanel() {
  return el(
    "div",
    {
      class: "card npc-panel",
      onclick: () => setMemoryPreview("npc"),
    },
    el("p", { class: "eyebrow", text: "NPC 對話" }),
    el(
      "label",
      {},
      "NPC 名字",
      el("input", {
        value: s.assignment.Start_NPC_Name,
        placeholder: "例如：阿姨",
        oninput: (event) => {
          s.assignment.Start_NPC_Name = event.target.value;
        },
      }),
    ),
    el(
      "div",
      { class: "npc-lines" },
      ...s.assignment.Start_Dialogues.map((text, lineIndex) => npcLineRow(text, lineIndex)),
    ),
    el("button", {
      class: "ghost npc-add",
      type: "button",
      text: "新增對白",
      onclick: addStartDialogueLine,
    }),
  );
}

function updateLibTabScrollButtons(scroller) {
  const track = scroller.querySelector(".tab-scroller-track");
  const prev = scroller.querySelector("[data-dir='-1']");
  const next = scroller.querySelector("[data-dir='1']");
  if (!track || !prev || !next) {
    return;
  }
  const maxScroll = track.scrollWidth - track.clientWidth;
  prev.disabled = track.scrollLeft <= 2;
  next.disabled = track.scrollLeft >= maxScroll - 2;
}

/** 節點進入 DOM 後才能還原 scrollLeft。 */
function bindLibTabScroller() {
  const scroller = document.querySelector(".memory-lib .tab-scroller");
  if (!scroller) {
    return;
  }
  const track = scroller.querySelector(".tab-scroller-track");
  if (!track) {
    return;
  }
  track.scrollLeft = s.libTabScroll;
  track.addEventListener("scroll", () => {
    s.libTabScroll = track.scrollLeft;
    updateLibTabScrollButtons(scroller);
  });
  updateLibTabScrollButtons(scroller);
  const pick = document.querySelector(".memory-theme-pick .tab-scroller");
  if (!pick) {
    return;
  }
  const pickTrack = pick.querySelector(".tab-scroller-track");
  if (!pickTrack) {
    return;
  }
  pickTrack.addEventListener("scroll", () => updateLibTabScrollButtons(pick));
  updateLibTabScrollButtons(pick);
}

function scrollLibTabs(dir) {
  const track = document.querySelector(".memory-lib .tab-scroller-track");
  if (!track) {
    return;
  }
  const amount = Math.max(180, Math.floor(track.clientWidth * 0.7));
  track.scrollBy({ left: dir * amount, behavior: "smooth" });
}

function scrollThemePickTabs(dir) {
  const track = document.querySelector(".memory-theme-pick .tab-scroller-track");
  if (!track) {
    return;
  }
  const amount = Math.max(180, Math.floor(track.clientWidth * 0.7));
  track.scrollBy({ left: dir * amount, behavior: "smooth" });
}

function themePickScroller(tabs) {
  return el(
    "div",
    { class: "tab-scroller" },
    el("button", {
      class: "tab-scroll-btn",
      type: "button",
      "aria-label": "上一個分類",
      "data-dir": "-1",
      text: "〈",
      onclick: (event) => {
        event.stopPropagation();
        scrollThemePickTabs(-1);
      },
    }),
    el("div", { class: "tab-scroller-track" }, el("div", { class: "tabs" }, tabs)),
    el("button", {
      class: "tab-scroll-btn",
      type: "button",
      "aria-label": "下一個分類",
      "data-dir": "1",
      text: "〉",
      onclick: (event) => {
        event.stopPropagation();
        scrollThemePickTabs(1);
      },
    }),
  );
}

function memoryLibraryCards(tag) {
  const cached = assignLibCards.get(tag?.code);
  if (cached) {
    return cached;
  }
  const cards = (tag?.materials ?? []).map((material) =>
    el(
      "button",
      {
        class: "card drag-card",
        type: "button",
        draggable: "true",
        ondragstart: (event) => {
          event.dataTransfer.setData("text/plain", material.code);
        },
      },
      materialPreview(material, tag),
      el("strong", { text: material.name }),
    ),
  );
  if (tag?.code) {
    assignLibCards.set(tag.code, cards);
  }
  return cards;
}

function refreshAssignLibraryPanel() {
  const panel = document.querySelector(".memory-lib");
  if (!panel) {
    return;
  }
  const active = s.assignLibrary.find((tag) => tag.code === s.assignLibTag) ?? s.assignLibrary[0];
  const tabs = panel.querySelectorAll(".tabs .tab");
  const current = [...tabs].find((tab) => tab.classList.contains("active"));
  const currentIndex = [...tabs].indexOf(current);
  if (current && s.assignLibrary[currentIndex]?.code === active?.code) {
    return;
  }
  tabs.forEach((tab, index) => {
    tab.classList.toggle("active", s.assignLibrary[index]?.code === active?.code);
  });
  const grid = panel.querySelector(".palette-grid");
  if (grid) {
    grid.replaceChildren(...memoryLibraryCards(active));
  }
}

function memoryLibraryPanel() {
  const active = s.assignLibrary.find((tag) => tag.code === s.assignLibTag) ?? s.assignLibrary[0];
  const tabs = s.assignLibrary.map((tag) =>
    el("button", {
      class: tag.code === active?.code ? "tab active" : "tab",
      type: "button",
      text: tag.name,
      onclick: () => {
        s.assignLibTag = tag.code;
        refreshAssignLibraryPanel();
      },
    }),
  );
  const cards = memoryLibraryCards(active);
  return el(
    "div",
    { class: "card memory-card memory-lib" },
    el(
      "div",
      { class: "memory-lib-head" },
      el("p", { class: "eyebrow", text: "素材庫" }),
      el(
        "div",
        { class: "tab-scroller" },
        el("button", {
          class: "tab-scroll-btn",
          type: "button",
          "aria-label": "上一個分類",
          "data-dir": "-1",
          text: "〈",
          onclick: () => scrollLibTabs(-1),
        }),
        el("div", { class: "tab-scroller-track" }, el("div", { class: "tabs" }, tabs)),
        el("button", {
          class: "tab-scroll-btn",
          type: "button",
          "aria-label": "下一個分類",
          "data-dir": "1",
          text: "〉",
          onclick: () => scrollLibTabs(1),
        }),
      ),
    ),
    el("div", { class: "memory-lib-scroll" }, el("div", { class: "palette-grid" }, ...cards)),
  );
}

function memoryAssignPage(game) {
  return assignShell(
    game,
    "memory-assign",
    el(
      "div",
      { class: "memory-rule" },
      el("h3", { class: "memory-rule-title", text: "在九個格子中讓學生翻出四個正確的格子" }),
      el("p", {
        class: "muted memory-rule-copy",
        text: "玩家須在空中按下方向鍵來敲開格子，一次最多能翻開四個格子，當翻開的四個格子都是正確的格子時過關",
      }),
    ),
    [
      el("p", {
        class: "memory-slot-title",
        "data-count": "theme",
        text: `正確格子 ${THEME_SLOTS.filter((key) => s.assignment.items[key]).length}/4`,
      }),
      el("div", { class: "slot-grid memory-ok" }, ...THEME_SLOTS.map((key) => memorySlotTile(key, "slot-correct"))),
      el("p", {
        class: "memory-slot-title",
        "data-count": "wrong",
        text: `錯誤格子 ${DISTRACTOR_SLOTS.filter((key) => s.assignment.items[key]).length}/5`,
      }),
      el(
        "div",
        { class: "slot-grid memory-ng" },
        ...DISTRACTOR_SLOTS.map((key) => memorySlotTile(key, "slot-wrong")),
      ),
    ],
  );
}

function vacuumAssignPage(game) {
  return assignShell(
    game,
    "memory-assign",
    el(
      "div",
      { class: "memory-rule" },
      el("h3", { class: "memory-rule-title", text: "用吸塵器吸起五個同一類的物品" }),
      el("p", {
        class: "muted memory-rule-copy",
        text: "把五個同一分類的物品拖進格子。第一個拖入的物品決定分類。學生必須吸起這五個物品。",
      }),
    ),
    [
      el("p", { class: "eyebrow", text: "物品配置" }),
      el("p", {
        class: "memory-slot-title",
        "data-count": "vacuum",
        text: `吸塵格子 ${VACUUM_SLOTS.filter((key) => s.assignment.items[key]).length}/5`,
      }),
      el(
        "div",
        { class: "slot-grid memory-ok vacuum-slots" },
        ...VACUUM_SLOTS.map((key) => memorySlotTile(key, "slot-correct", placeVacuum)),
      ),
    ],
  );
}

function parkourThemePicker() {
  const tabs = s.assignLibrary.map((tag) =>
    el("button", {
      class: tag.code === s.assignment.tag ? "tab active" : "tab",
      type: "button",
      text: tag.name,
      onclick: () => setParkourTag(tag.code),
    }),
  );
  return el(
    "div",
    { class: "memory-theme-pick" },
    el("p", { class: "memory-slot-title", text: "題目主題" }),
    themePickScroller(tabs),
  );
}

function parkourAssignPage(game) {
  const rows = [1, 2, 3, 4, 5, 6].map((index) =>
    el(
      "div",
      { class: "market-shelf-group" },
      el("p", { class: "memory-slot-title", text: `第 ${index} 列` }),
      el(
        "div",
        { class: "slot-grid parkour-rows" },
        memorySlotTile(`theme_${index}`, "slot-correct", placeParkour),
        memorySlotTile(`distractor_${2 * index - 1}`, "slot-wrong", placeParkour),
        memorySlotTile(`distractor_${2 * index}`, "slot-wrong", placeParkour),
      ),
    ),
  );
  return assignShell(
    game,
    "memory-assign is-wide",
    el(
      "div",
      { class: "memory-rule" },
      el("h3", { class: "memory-rule-title", text: "在六段路途中選對正確的那一條" }),
      el("p", {
        class: "muted memory-rule-copy",
        text: "每列左邊是正確選項，右邊兩格是干擾。學生跑步時要選對正確的路。",
      }),
    ),
    [
      el("p", { class: "eyebrow", text: "物品配置" }),
      parkourThemePicker(),
      el("div", { class: "market-shelf-scroll" }, ...rows),
    ],
  );
}

function sortThemePicker() {
  const tabs = s.assignLibrary.map((tag) => {
    const pickIndex = s.assignment.tags.indexOf(tag.code);
    const picked = pickIndex >= 0;
    return el("button", {
      class: picked ? "tab picked" : "tab",
      type: "button",
      text: picked ? `${pickIndex + 1}. ${tag.name}` : tag.name,
      onclick: () => toggleSortTag(tag.code),
    });
  });
  return el(
    "div",
    { class: "memory-theme-pick" },
    el("p", { class: "memory-slot-title", text: `分類主題 ${s.assignment.tags.length}/4` }),
    themePickScroller(tabs),
  );
}

function sortAssignPage(game) {
  const groups = [1, 2, 3, 4].map((bin) => {
    const tagCode = s.assignment.tags[bin - 1];
    const theme = s.assignLibrary.find((tag) => tag.code === tagCode);
    const title = theme ? theme.name : `分類 ${bin}`;
    const keys = [1, 2, 3, 4, 5].map((slotIndex) => `bin_${bin}_${slotIndex}`);
    return el(
      "div",
      { class: "market-shelf-group" },
      el("p", { class: "memory-slot-title", text: title }),
      el(
        "div",
        { class: "slot-grid sort-slots" },
        ...keys.map((key) => memorySlotTile(key, "slot-correct", placeSort)),
      ),
    );
  });
  return assignShell(
    game,
    "memory-assign is-wide",
    el(
      "div",
      { class: "memory-rule" },
      el("h3", { class: "memory-rule-title", text: "把物品推到對應的四個分類" }),
      el("p", {
        class: "muted memory-rule-copy",
        text: "先選四個分類主題，每個分類拖五個素材。學生須把物品推到正確的分類。",
      }),
    ),
    [
      el("p", { class: "eyebrow", text: "物品配置" }),
      sortThemePicker(),
      el("div", { class: "market-shelf-scroll" }, ...groups),
    ],
  );
}

/** 已支援的遊戲顯示編輯頁。未知遊戲顯示稍後提供。 */
function assignPage() {
  const game = currentGame();
  if (!game) {
    return el(
      "section",
      {},
      pageHeader("遊戲配置", "找不到遊戲"),
      el("p", { class: "muted", text: "請確認資料庫有 Game 資料。" }),
    );
  }
  if (!view.studentId) {
    return el(
      "section",
      {},
      pageHeader("遊戲配置", game.name),
      el("p", { class: "muted", text: "請先新增並選擇學生。" }),
    );
  }
  switch (game.code) {
    case MEMORY_MATCH:
      return memoryAssignPage(game);
    case PAIR_VACUUM:
      return vacuumAssignPage(game);
    case DECISION_PARKOUR:
      return parkourAssignPage(game);
    case SORT_ARENA:
      return sortAssignPage(game);
    case MARKET_SHOPPING:
    case MARKET_BUDGET:
      return marketAssignPage(game);
    default:
      return el(
        "section",
        {},
        pageHeader("遊戲配置", game.name),
        el("p", {
          class: "muted",
          text: "配置功能稍後提供",
        }),
      );
  }
}

export {
  assignPage,
  loadAssignLibrary,
  loadAssignment,
  loadStudentMaterialLists,
  materialConfigList,
  bindLibTabScroller,
  emptyAssignment,
  clearMaterialConfigState,
};
