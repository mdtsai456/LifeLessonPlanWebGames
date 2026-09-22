/** 故事線、選線前開場、每步閉場。 */
import { api } from "./api.js";
import { materialConfigList } from "./assign.js";
import { el, pageHeader } from "./dom.js";
import { MARKET_SHOPPING, clearWorkflowState, render, s, view } from "./state.js";

function orderOf(item) {
  const order = Number(item?.order);
  return Number.isFinite(order) ? order : 0;
}

function indexOfOrderOne(items) {
  const index = items.findIndex((item) => orderOf(item) === 1);
  return index >= 0 ? index : 0;
}

function clampIndex(index, length) {
  if (length <= 0) {
    return 0;
  }
  if (index < 0) {
    return 0;
  }
  if (index >= length) {
    return length - 1;
  }
  return index;
}

function dialogueLines(raw) {
  const lines = Array.isArray(raw)
    ? raw
        .map((line) => (typeof line === "string" ? line : ""))
        .filter((line) => line.trim().length > 0)
    : [];
  return lines.length > 0 ? lines : [""];
}

function materialIdFromApi(value) {
  if (value == null || value === "") {
    return null;
  }
  const id = Number(value);
  return Number.isInteger(id) ? id : null;
}

/** 把 API 步驟轉成畫面資料，缺欄位當空白。 */
function stepFromApi(item, materialId) {
  return {
    game: item.game,
    gameMaterialCustomizationId: materialId,
    order: orderOf(item),
    endNpcName: typeof item.endNpcName === "string" ? item.endNpcName : "",
    endDialogues: dialogueLines(item.endDialogues),
  };
}

function storylineFromApi(item) {
  const steps = Array.isArray(item.steps) ? item.steps.slice() : [];
  steps.sort((a, b) => orderOf(a) - orderOf(b));
  return {
    name: typeof item.name === "string" ? item.name : "",
    order: orderOf(item),
    steps: steps.map((step) => stepFromApi(step, materialIdFromApi(step.gameMaterialCustomizationId))),
  };
}

function parseStorylines(payload) {
  const lines = Array.isArray(payload?.storylines) ? payload.storylines : [];
  const storylines = lines.map(storylineFromApi).sort((a, b) => a.order - b.order);
  return {
    startNpcName: typeof payload?.startNpcName === "string" ? payload.startNpcName : "",
    startDialogues: dialogueLines(payload?.startDialogues),
    storylines,
  };
}

/** 還沒有 storylines、仍是 games 陣列時，當成舊檔。 */
function isLegacyGames(payload) {
  return Array.isArray(payload?.games) && !Array.isArray(payload?.storylines);
}

async function fetchMaterialConfigs(studentId, gameCode) {
  const payload = await api(`/api/students/${studentId}/games/${gameCode}/materials`);
  return materialConfigList(payload);
}

async function materialListsFor(studentId, gameCodes) {
  const lists = {};
  await Promise.all(
    gameCodes.map(async (code) => {
      lists[code] = await fetchMaterialConfigs(studentId, code);
    }),
  );
  return lists;
}

function gameCodesIn(storylines) {
  const codes = [];
  storylines.forEach((line) => {
    line.steps.forEach((step) => {
      if (step.game && !codes.includes(step.game)) {
        codes.push(step.game);
      }
    });
  });
  return codes;
}

/** 只有恰好一筆 json_path 以 /遊戲代號.json 結尾時才綁定。 */
function flatMaterialId(configs, gameCode) {
  const suffix = `/${gameCode}.json`;
  const matches = configs.filter((item) => {
    if (typeof item.json_path !== "string") {
      return false;
    }
    const normalized = item.json_path.replaceAll("\\", "/").replace(/\/+$/, "");
    return normalized.endsWith(suffix);
  });
  if (matches.length !== 1) {
    return null;
  }
  return matches[0].id;
}

function blankStep(order) {
  return {
    game: MARKET_SHOPPING,
    gameMaterialCustomizationId: null,
    order,
    endNpcName: "",
    endDialogues: [""],
  };
}

function selectOpening(storylines) {
  view.storylineIndex = indexOfOrderOne(storylines);
  const steps = storylines[view.storylineIndex]?.steps ?? [];
  view.workflowIndex = indexOfOrderOne(steps);
}

/** 舊的 games 陣列只在畫面編成一條名稱為預設的故事線。 */
async function loadWorkflow() {
  if (!view.studentId) {
    clearWorkflowState();
    return;
  }
  const studentId = view.studentId;
  const payload = await api(`/api/students/${studentId}/workflow`);
  if (view.studentId !== studentId) {
    return;
  }
  if (isLegacyGames(payload)) {
    await loadLegacyGames(payload, studentId);
    return;
  }
  const parsed = parseStorylines(payload);
  await ensureListedGames(studentId, gameCodesIn(parsed.storylines));
  if (view.studentId !== studentId) {
    return;
  }
  s.workflowStartNpcName = parsed.startNpcName;
  s.workflowStartDialogues = parsed.startDialogues;
  s.storylines = parsed.storylines;
  view.editingStart = false;
  selectOpening(parsed.storylines);
}

/** 側欄已讀取的遊戲不再重新讀取。 */
async function ensureListedGames(studentId, gameCodes) {
  const missing = gameCodes.filter((code) => code && !Object.hasOwn(s.materialLists, code));
  if (missing.length === 0) {
    return;
  }
  const lists = await materialListsFor(studentId, missing);
  if (view.studentId !== studentId) {
    return;
  }
  Object.assign(s.materialLists, lists);
}

async function loadLegacyGames(payload, studentId) {
  const games = (payload.games || []).slice().sort((a, b) => orderOf(a) - orderOf(b));
  const codes = [];
  games.forEach((item) => {
    if (item.game && !codes.includes(item.game)) {
      codes.push(item.game);
    }
  });
  await ensureListedGames(studentId, codes);
  if (view.studentId !== studentId) {
    return;
  }
  const steps = games.map((item) =>
    stepFromApi(item, flatMaterialId(s.materialLists[item.game] ?? [], item.game)),
  );
  s.workflowStartNpcName = "";
  s.workflowStartDialogues = [""];
  s.storylines = [{ name: "預設", order: 1, steps }];
  view.editingStart = false;
  selectOpening(s.storylines);
}

function workflowPayload() {
  return {
    startNpcName: s.workflowStartNpcName,
    startDialogues: s.workflowStartDialogues,
    storylines: s.storylines.map((line, lineIndex) => ({
      name: line.name,
      order: lineIndex + 1,
      steps: line.steps.map((step, stepIndex) => ({
        game: step.game,
        gameMaterialCustomizationId: step.gameMaterialCustomizationId,
        order: stepIndex + 1,
        endNpcName: step.endNpcName,
        endDialogues: step.endDialogues,
      })),
    })),
  };
}

/** 把故事線、選線前開場與每步閉場整份寫入。 */
async function saveWorkflow() {
  if (!view.studentId) {
    return;
  }
  const studentId = view.studentId;
  const lineIndex = view.storylineIndex;
  const stepIndex = view.workflowIndex;
  try {
    const payload = await api(`/api/students/${studentId}/workflow`, {
      method: "PUT",
      body: JSON.stringify(workflowPayload()),
    });
    if (view.studentId !== studentId) {
      return;
    }
    const parsed = parseStorylines(payload);
    s.workflowStartNpcName = parsed.startNpcName;
    s.workflowStartDialogues = parsed.startDialogues;
    s.storylines = parsed.storylines;
    view.storylineIndex = clampIndex(lineIndex, s.storylines.length);
    const steps = s.storylines[view.storylineIndex]?.steps ?? [];
    view.workflowIndex = clampIndex(stepIndex, steps.length);
    s.error = "";
  } catch (err) {
    if (view.studentId !== studentId) {
      return;
    }
    s.error = err.message;
  }
  render();
}

function gameNameOf(code) {
  return s.games.find((game) => game.code === code)?.name ?? code;
}

function currentStoryline() {
  if (s.storylines.length === 0) {
    return null;
  }
  if (view.storylineIndex < 0 || view.storylineIndex >= s.storylines.length) {
    view.storylineIndex = 0;
  }
  return s.storylines[view.storylineIndex];
}

/** 回傳目前選取的步驟。正在編輯選線前開場時回傳 null。沒有學生或沒有步驟時回傳 null。 */
function selectedWorkflowStep() {
  if (view.editingStart) {
    return null;
  }
  const line = currentStoryline();
  if (!view.studentId || !line || line.steps.length === 0) {
    return null;
  }
  if (view.workflowIndex < 0 || view.workflowIndex >= line.steps.length) {
    view.workflowIndex = 0;
  }
  return line.steps[view.workflowIndex];
}

function renumberOrders(items) {
  items.forEach((item, index) => {
    item.order = index + 1;
  });
}

/** 拖曳只改目前這條故事線的步驟順序。 */
function reorderWorkflow(fromIndex, toIndex) {
  const line = currentStoryline();
  if (!line || fromIndex === toIndex || fromIndex < 0 || toIndex < 0) {
    return;
  }
  if (fromIndex >= line.steps.length || toIndex >= line.steps.length) {
    return;
  }
  const next = line.steps.slice();
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  renumberOrders(next);
  line.steps = next;
  view.workflowIndex = next.indexOf(moved);
  view.editingStart = false;
}

async function ensureGameMaterials(gameCode) {
  if (Object.hasOwn(s.materialLists, gameCode)) {
    return true;
  }
  const studentId = view.studentId;
  try {
    const list = await fetchMaterialConfigs(studentId, gameCode);
    if (view.studentId !== studentId) {
      return false;
    }
    s.materialLists[gameCode] = list;
    return true;
  } catch (err) {
    if (view.studentId !== studentId) {
      return false;
    }
    s.error = err.message;
    return false;
  }
}

async function changeStepGame(step, gameCode) {
  if (step.game === gameCode) {
    return;
  }
  const studentId = view.studentId;
  const hadList = Object.hasOwn(s.materialLists, gameCode);
  step.game = gameCode;
  step.gameMaterialCustomizationId = null;
  render();
  if (hadList) {
    return;
  }
  await ensureGameMaterials(gameCode);
  if (view.studentId !== studentId) {
    return;
  }
  render();
}

async function addStoryline() {
  if (!view.studentId) {
    return;
  }
  const studentId = view.studentId;
  const order = s.storylines.length + 1;
  s.storylines.push({
    name: `故事線${order}`,
    order,
    steps: [blankStep(1)],
  });
  view.storylineIndex = s.storylines.length - 1;
  view.workflowIndex = 0;
  view.editingStart = false;
  render();
  if (Object.hasOwn(s.materialLists, MARKET_SHOPPING)) {
    return;
  }
  await ensureGameMaterials(MARKET_SHOPPING);
  if (view.studentId !== studentId) {
    return;
  }
  render();
}

function deleteStoryline(lineIndex = view.storylineIndex) {
  if (s.storylines.length <= 1) {
    return;
  }
  if (lineIndex < 0 || lineIndex >= s.storylines.length) {
    return;
  }
  s.storylines.splice(lineIndex, 1);
  renumberOrders(s.storylines);
  if (view.storylineIndex > lineIndex) {
    view.storylineIndex -= 1;
  }
  view.storylineIndex = clampIndex(view.storylineIndex, s.storylines.length);
  view.workflowIndex = clampIndex(
    view.workflowIndex,
    s.storylines[view.storylineIndex]?.steps.length ?? 0,
  );
  render();
}

async function addStep() {
  const line = currentStoryline();
  if (!line || !view.studentId) {
    return;
  }
  const studentId = view.studentId;
  const order = line.steps.length + 1;
  line.steps.push(blankStep(order));
  view.workflowIndex = line.steps.length - 1;
  render();
  if (Object.hasOwn(s.materialLists, MARKET_SHOPPING)) {
    return;
  }
  await ensureGameMaterials(MARKET_SHOPPING);
  if (view.studentId !== studentId) {
    return;
  }
  render();
}

function deleteStepAt(lineIndex, stepIndex) {
  const line = s.storylines[lineIndex];
  if (!line || line.steps.length <= 1) {
    return;
  }
  if (stepIndex < 0 || stepIndex >= line.steps.length) {
    return;
  }
  line.steps.splice(stepIndex, 1);
  renumberOrders(line.steps);
  if (view.storylineIndex === lineIndex) {
    if (view.workflowIndex > stepIndex) {
      view.workflowIndex -= 1;
    }
    view.workflowIndex = clampIndex(view.workflowIndex, line.steps.length);
  }
  render();
}

function deleteStep() {
  deleteStepAt(view.storylineIndex, view.workflowIndex);
}

function addStartDialogueLine() {
  s.workflowStartDialogues.push("");
  render();
}

function deleteStartDialogueLine(lineIndex) {
  s.workflowStartDialogues.splice(lineIndex, 1);
  if (s.workflowStartDialogues.length === 0) {
    s.workflowStartDialogues.push("");
  }
  render();
}

function addEndDialogueLine() {
  const step = selectedWorkflowStep();
  if (!step) {
    return;
  }
  step.endDialogues.push("");
  render();
}

function deleteEndDialogueLine(lineIndex) {
  const step = selectedWorkflowStep();
  if (!step) {
    return;
  }
  step.endDialogues.splice(lineIndex, 1);
  if (step.endDialogues.length === 0) {
    step.endDialogues.push("");
  }
  render();
}

/** 從側欄放下時新增一步。原來的步驟留在原位。 */
function addConfigStep(lineIndex, gameCode, configId, atIndex) {
  const line = s.storylines[lineIndex];
  if (!line || !Number.isInteger(configId)) {
    return;
  }
  const step = {
    game: gameCode,
    gameMaterialCustomizationId: configId,
    order: 1,
    endNpcName: "",
    endDialogues: [""],
  };
  const next = line.steps.slice();
  let index = atIndex;
  if (!Number.isInteger(index) || index < 0 || index > next.length) {
    index = next.length;
  }
  next.splice(index, 0, step);
  renumberOrders(next);
  line.steps = next;
  view.storylineIndex = lineIndex;
  view.workflowIndex = index;
  view.editingStart = false;
}

/** 在同一條故事線上更改順序。拖到末端時，該步排在最後。 */
function placeStepOnSameLine(fromIndex, toIndex) {
  const line = currentStoryline();
  if (!line || fromIndex < 0 || fromIndex >= line.steps.length) {
    return;
  }
  if (toIndex >= line.steps.length) {
    if (fromIndex === line.steps.length - 1) {
      return;
    }
    const next = line.steps.slice();
    const [moved] = next.splice(fromIndex, 1);
    next.push(moved);
    renumberOrders(next);
    line.steps = next;
    view.workflowIndex = next.length - 1;
    view.editingStart = false;
    return;
  }
  reorderWorkflow(fromIndex, toIndex);
}

/** 從其他故事線放下時移走該步。來源只剩一步時，不移走該步。 */
function moveStepToLine(fromLine, fromIndex, toLine, toIndex) {
  if (fromLine === toLine) {
    view.storylineIndex = fromLine;
    placeStepOnSameLine(fromIndex, toIndex);
    return;
  }
  const source = s.storylines[fromLine];
  const target = s.storylines[toLine];
  if (!source || !target || source.steps.length <= 1) {
    return;
  }
  if (fromIndex < 0 || fromIndex >= source.steps.length) {
    return;
  }
  const [step] = source.steps.splice(fromIndex, 1);
  renumberOrders(source.steps);
  let index = toIndex;
  if (!Number.isInteger(index) || index < 0 || index > target.steps.length) {
    index = target.steps.length;
  }
  target.steps.splice(index, 0, step);
  renumberOrders(target.steps);
  view.storylineIndex = toLine;
  view.workflowIndex = index;
  view.editingStart = false;
}

function parseDragPayload(raw) {
  if (raw.startsWith("config:")) {
    const parts = raw.split(":");
    return { type: "config", gameCode: parts[1], configId: Number(parts[2]) };
  }
  if (raw.startsWith("belt:")) {
    const parts = raw.split(":");
    return { type: "belt", line: Number(parts[1]), index: Number(parts[2]) };
  }
  return { type: "unknown" };
}

function applyConveyorDrop(event, lineIndex, atIndex) {
  event.preventDefault();
  event.stopPropagation();
  event.currentTarget.classList.remove("over");
  if (!view.studentId || !event.dataTransfer) {
    return;
  }
  const raw = event.dataTransfer.getData("text/plain") || event.dataTransfer.getData("text") || "";
  const payload = parseDragPayload(raw);
  if (payload.type === "config" && Number.isInteger(payload.configId)) {
    addConfigStep(lineIndex, payload.gameCode, payload.configId, atIndex);
    render();
    return;
  }
  if (payload.type === "belt" && Number.isInteger(payload.line) && Number.isInteger(payload.index)) {
    moveStepToLine(payload.line, payload.index, lineIndex, atIndex);
    render();
  }
}

function markDropTarget(event) {
  event.preventDefault();
  event.stopPropagation();
  event.currentTarget.classList.add("over");
}

function unmarkDropTarget(event) {
  event.currentTarget.classList.remove("over");
}

function stepTitle(step) {
  if (step.gameMaterialCustomizationId != null) {
    return `${step.game} ${step.gameMaterialCustomizationId}`;
  }
  return "預設";
}

/** 步驟卡片。點選後編輯該步。拖到其他故事線時移走該步。來源只剩一步時，該步留在原位。 */
function conveyorItem(lineIndex, step, index) {
  const selected =
    !view.editingStart && lineIndex === view.storylineIndex && index === view.workflowIndex;
  return el(
    "article",
    {
      class: selected ? "conveyor-item is-selected" : "conveyor-item",
      draggable: "true",
      onclick: () => {
        view.storylineIndex = lineIndex;
        view.workflowIndex = index;
        view.editingStart = false;
        render();
      },
      ondragstart: (event) => {
        event.stopPropagation();
        const payload = `belt:${lineIndex}:${index}`;
        event.dataTransfer.setData("text/plain", payload);
        event.dataTransfer.setData("text", payload);
        event.dataTransfer.effectAllowed = "move";
      },
      ondragover: markDropTarget,
      ondragleave: unmarkDropTarget,
      ondrop: (event) => applyConveyorDrop(event, lineIndex, index),
    },
    el("span", { class: "conveyor-game", text: gameNameOf(step.game) }),
    el("strong", { text: stepTitle(step) }),
    el("button", {
      class: "ghost conveyor-remove",
      type: "button",
      text: "×",
      "aria-label": "刪除步驟",
      disabled: s.storylines[lineIndex]?.steps.length <= 1,
      onclick: (event) => {
        event.stopPropagation();
        deleteStepAt(lineIndex, index);
      },
    }),
  );
}

function dialogueControls(lines, onInput, onDelete, onAdd, placeholder) {
  return [
    el(
      "div",
      { class: "npc-lines" },
      ...lines.map((text, lineIndex) =>
        el(
          "div",
          { class: "npc-line" },
          el("textarea", {
            rows: "2",
            placeholder,
            text,
            oninput: (event) => {
              onInput(lineIndex, event.target.value);
            },
          }),
          el("button", {
            class: "ghost",
            type: "button",
            text: "刪除",
            onclick: () => onDelete(lineIndex),
          }),
        ),
      ),
    ),
    el("button", {
      class: "ghost npc-add",
      type: "button",
      text: "新增對白",
      onclick: onAdd,
    }),
  ];
}

function startDialoguePanel() {
  if (!view.studentId) {
    return el(
      "div",
      { class: "card npc-panel" },
      el("p", { class: "eyebrow", text: "選線前開場" }),
      el("p", { class: "muted", text: "請先新增並選擇學生。" }),
    );
  }
  return el(
    "div",
    { class: "card npc-panel" },
    el("p", { class: "eyebrow", text: "選線前開場" }),
    el(
      "label",
      {},
      "NPC 名字",
      el("input", {
        value: s.workflowStartNpcName,
        placeholder: "例如：阿姨",
        oninput: (event) => {
          s.workflowStartNpcName = event.target.value;
        },
      }),
    ),
    ...dialogueControls(
      s.workflowStartDialogues,
      (lineIndex, value) => {
        s.workflowStartDialogues[lineIndex] = value;
      },
      deleteStartDialogueLine,
      addStartDialogueLine,
      "例如：今天想玩哪一條故事？",
    ),
  );
}

function storylineNameField(line) {
  return el(
    "label",
    {},
    "故事線名稱",
    el("input", {
      value: line?.name ?? "",
      "aria-label": "故事線名稱",
      disabled: !line,
      oninput: (event) => {
        if (!line) {
          return;
        }
        line.name = event.target.value;
        const labels = document.querySelectorAll(".conveyor-branches .storyline-label");
        const label = labels[view.storylineIndex];
        if (label) {
          label.textContent = event.target.value;
        }
      },
    }),
  );
}

function selectStoryline(lineIndex) {
  const line = s.storylines[lineIndex];
  if (!line) {
    return;
  }
  view.storylineIndex = lineIndex;
  view.workflowIndex = clampIndex(view.workflowIndex, line.steps.length);
  view.editingStart = false;
  render();
}

function selectStartDialogue() {
  view.editingStart = true;
  render();
}

function gameField(step) {
  const select = el("select", {
    class: "config-select",
    "aria-label": "遊戲",
    onchange: (event) => {
      changeStepGame(step, event.target.value);
    },
  });
  const codes = s.games.map((game) => game.code);
  if (step.game && !codes.includes(step.game)) {
    codes.unshift(step.game);
  }
  codes.forEach((code) => {
    select.append(el("option", { value: code, text: gameNameOf(code) }));
  });
  select.value = step.game;
  return el("label", {}, "遊戲", select);
}

function materialField(step) {
  const lists = s.materialLists[step.game] ?? [];
  const select = el("select", {
    class: "config-select",
    "aria-label": "素材配置",
    onchange: (event) => {
      const raw = event.target.value;
      step.gameMaterialCustomizationId = raw ? Number(raw) : null;
    },
  });
  select.append(el("option", { value: "", text: "預設" }));
  lists.forEach((config) => {
    select.append(
      el("option", {
        value: String(config.id),
        text: `${step.game} ${config.id}`,
      }),
    );
  });
  const current = step.gameMaterialCustomizationId;
  if (current != null && !lists.some((config) => config.id === current)) {
    select.append(
      el("option", {
        value: String(current),
        text: `${step.game} ${current}`,
      }),
    );
  }
  select.value = current == null ? "" : String(current);
  return el("label", {}, "素材配置", select);
}

function stepCard() {
  const line = currentStoryline();
  const step = selectedWorkflowStep();
  const actions = el(
    "div",
    { class: "toolbar" },
    el("button", {
      type: "button",
      text: "新增步驟",
      disabled: !view.studentId || !line,
      onclick: addStep,
    }),
    el("button", {
      class: "ghost",
      type: "button",
      text: "刪除步驟",
      disabled: !line || line.steps.length <= 1,
      onclick: deleteStep,
    }),
  );
  if (!step) {
    return el(
      "div",
      { class: "card npc-panel" },
      el("p", { class: "eyebrow", text: "步驟" }),
      storylineNameField(line),
      actions,
      el("p", {
        class: "muted",
        text: view.studentId ? "這條故事線還沒有步驟。" : "請先新增並選擇學生。",
      }),
    );
  }
  return el(
    "div",
    { class: "card npc-panel" },
    el("p", { class: "eyebrow", text: "步驟" }),
    storylineNameField(line),
    el("p", { class: "muted", text: `正在編輯：${gameNameOf(step.game)} · ${stepTitle(step)}` }),
    actions,
    gameField(step),
    materialField(step),
    el("p", { class: "eyebrow", text: "閉場" }),
    el(
      "label",
      {},
      "NPC 名字",
      el("input", {
        value: step.endNpcName,
        placeholder: "例如：店員",
        oninput: (event) => {
          step.endNpcName = event.target.value;
        },
      }),
    ),
    ...dialogueControls(
      step.endDialogues,
      (lineIndex, value) => {
        step.endDialogues[lineIndex] = value;
      },
      deleteEndDialogueLine,
      addEndDialogueLine,
      "例如：這一關完成了，我們繼續往前走吧！",
    ),
  );
}

function conveyorStations(line, lineIndex) {
  const stations = [];
  line.steps.forEach((step, index) => {
    if (index === 0) {
      return;
    }
    stations.push(el("span", { class: "conveyor-link", "aria-hidden": "true" }));
    stations.push(
      el(
        "div",
        {
          class: "conveyor-drop",
          ondragover: markDropTarget,
          ondragleave: unmarkDropTarget,
          ondrop: (event) => applyConveyorDrop(event, lineIndex, index),
        },
        conveyorItem(lineIndex, step, index),
      ),
    );
  });
  return stations;
}

function emptySlot(lineIndex, index = 0) {
  return el("div", {
    class: "conveyor-empty",
    text: "拖入配置",
    ondragover: markDropTarget,
    ondragleave: unmarkDropTarget,
    ondrop: (event) => applyConveyorDrop(event, lineIndex, index),
  });
}

function firstSlot(line, lineIndex) {
  const first = line.steps[0];
  return el(
    "div",
    { class: "conveyor-lead" },
    el("p", {
      class: "eyebrow storyline-label",
      text: line.name,
      role: "button",
      tabindex: "0",
      onclick: () => selectStoryline(lineIndex),
      onkeydown: (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectStoryline(lineIndex);
        }
      },
    }),
    first
      ? el(
          "div",
          {
            class: "conveyor-drop",
            ondragover: markDropTarget,
            ondragleave: unmarkDropTarget,
            ondrop: (event) => applyConveyorDrop(event, lineIndex, 0),
          },
          conveyorItem(lineIndex, first, 0),
        )
      : emptySlot(lineIndex),
  );
}

function svgNode(name, attrs) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attrs).forEach(([key, value]) => {
    node.setAttribute(key, value);
  });
  return node;
}

function storylineTreeSvg() {
  return svgNode("svg", { class: "conveyor-tree", "aria-hidden": "true" });
}

function layoutStorylineTree(hub) {
  const origin = hub.querySelector(".conveyor-origin");
  const fork = hub.querySelector(".conveyor-intro") || hub.querySelector(".conveyor-start");
  const tree = hub.querySelector(".conveyor-tree");
  const rows = [...hub.querySelectorAll(":scope .conveyor-branches .conveyor")];
  if (!fork || !tree || rows.length === 0) {
    return;
  }
  const single = rows.length === 1;
  hub.classList.toggle("is-single", single);
  if (origin) {
    origin.style.transform = "";
  }
  const hubBox = hub.getBoundingClientRect();
  const originX = hubBox.left + hub.clientLeft;
  const originY = hubBox.top + hub.clientTop;
  const pointOf = (node) => {
    const box = node.getBoundingClientRect();
    return {
      x: box.left - originX,
      y: box.top + box.height / 2 - originY,
    };
  };
  const ends = rows.map((row) => {
    const target = row.querySelector(".conveyor-item, .conveyor-empty") || row;
    return pointOf(target);
  });
  let startPoint = pointOf(fork);
  startPoint = { x: fork.getBoundingClientRect().right - originX, y: startPoint.y };
  const ys = ends.map((point) => point.y);
  const midY = (Math.min(...ys) + Math.max(...ys)) / 2;
  const dy = midY - startPoint.y;
  if (origin && Math.abs(dy) >= 1) {
    origin.style.transform = `translateY(${dy}px)`;
    startPoint = {
      x: fork.getBoundingClientRect().right - originX,
      y: fork.getBoundingClientRect().top + fork.getBoundingClientRect().height / 2 - originY,
    };
  }
  const parts = [];
  if (single) {
    parts.push(`M ${startPoint.x} ${startPoint.y} H ${ends[0].x}`);
  } else {
    const spineX = startPoint.x + 22;
    parts.push(`M ${startPoint.x} ${startPoint.y} H ${spineX}`);
    parts.push(`M ${spineX} ${Math.min(...ys)} V ${Math.max(...ys)}`);
    ends.forEach((end) => {
      parts.push(`M ${spineX} ${end.y} H ${end.x}`);
    });
  }
  const width = Math.max(1, hub.clientWidth);
  const height = Math.max(1, hub.clientHeight);
  tree.setAttribute("viewBox", `0 0 ${width} ${height}`);
  tree.removeAttribute("width");
  tree.removeAttribute("height");
  tree.replaceChildren(
    svgNode("path", {
      d: parts.join(" "),
      fill: "none",
      stroke: "#c8b89a",
      "stroke-width": "4",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    }),
  );
}

function bindStorylineTree(hub) {
  const draw = () => layoutStorylineTree(hub);
  requestAnimationFrame(draw);
  if (typeof ResizeObserver === "undefined") {
    return;
  }
  const observer = new ResizeObserver(draw);
  observer.observe(hub);
}

function storylineBlock(line, lineIndex) {
  return el(
    "div",
    { class: "storyline-block" },
    el(
      "div",
      {
        class: "conveyor",
        ondragover: markDropTarget,
        ondragleave: unmarkDropTarget,
        ondrop: (event) => applyConveyorDrop(event, lineIndex, line.steps.length),
      },
      firstSlot(line, lineIndex),
      ...conveyorStations(line, lineIndex),
      ...(line.steps.length > 0
        ? [
            el("span", { class: "conveyor-link", "aria-hidden": "true" }),
            emptySlot(lineIndex, line.steps.length),
          ]
        : []),
      el("span", { class: "conveyor-link", "aria-hidden": "true" }),
      el("div", { class: "conveyor-end", text: "終" }),
      el("button", {
        class: "storyline-remove",
        type: "button",
        text: "刪除故事線",
        disabled: s.storylines.length <= 1,
        onclick: () => deleteStoryline(lineIndex),
      }),
    ),
  );
}

function startDialogueNode() {
  return el("button", {
    class: view.editingStart ? "conveyor-intro is-selected" : "conveyor-intro",
    type: "button",
    text: "起始",
    onclick: selectStartDialogue,
  });
}

function workflowPage() {
  const saveBtn = el("button", {
    type: "button",
    text: "儲存配置",
    disabled: !view.studentId,
    onclick: saveWorkflow,
  });
  const lines = view.studentId ? s.storylines : [];
  const hub = view.studentId
    ? el(
        "div",
        { class: "conveyor-hub" },
        el(
          "div",
          { class: "conveyor-origin" },
          el("div", { class: "conveyor-end conveyor-start", text: "起" }),
          el("span", { class: "conveyor-link", "aria-hidden": "true" }),
          startDialogueNode(),
        ),
        storylineTreeSvg(),
        el(
          "div",
          { class: "conveyor-branches" },
          ...lines.map((line, lineIndex) => storylineBlock(line, lineIndex)),
        ),
      )
    : null;
  if (hub) {
    bindStorylineTree(hub);
  }
  return el(
    "section",
    { class: "workflow-page" },
    pageHeader("關卡流程", "關卡配置", saveBtn),
    s.error ? el("p", { class: "error", text: s.error }) : null,
    view.studentId
      ? el("p", {
          class: "muted",
          text: "把左側的配置拖進其中一條故事線。由左到右是步驟。同一份配置可以出現在多步。",
        })
      : el("p", { class: "muted", text: "請先新增並選擇學生。" }),
    hub,
    view.studentId
      ? el("button", {
          class: "storyline-add",
          type: "button",
          text: "新增故事線",
          onclick: addStoryline,
        })
      : null,
    view.studentId ? (view.editingStart ? startDialoguePanel() : stepCard()) : null,
  );
}

export { workflowPage, loadWorkflow, selectedWorkflowStep };
