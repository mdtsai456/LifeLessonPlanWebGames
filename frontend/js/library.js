/** 素材庫頁。修改 GameTag 與 GameMaterial。 */
import { api } from "./api.js";
import {
  closeModal,
  confirmDanger,
  el,
  isModel,
  materialPreview,
  pageHeader,
  placeholderColor,
  placeholderImage,
  showAddPanel,
} from "./dom.js";
import { currentGame, currentTag, render, s, view } from "./state.js";
async function loadCatalog(tagCode) {
  s.tags = await api(`/api/games/${view.gameCode}/tags`);
  const nextTag = tagCode && s.tags.some((tag) => tag.code === tagCode) ? tagCode : s.tags[0]?.code ?? null;
  view.tagCode = nextTag;
  await loadMaterials();
}

async function loadTags() {
  if (!view.gameCode) {
    s.tags = [];
    s.materials = [];
    view.tagCode = null;
    return;
  }
  s.loading = true;
  try {
    await loadCatalog(view.tagCode);
  } finally {
    s.loading = false;
  }
}

async function loadMaterials() {
  if (!view.tagCode) {
    s.materials = [];
    return;
  }
  const payload = await api(`/api/tags/${view.tagCode}/materials`);
  s.materials = payload.materials;
}

function themeTabs(active) {
  const tabs = s.tags.map((tag) =>
    el("button", {
      class: tag.code === active?.code ? "tab active" : "tab",
      type: "button",
      text: tag.name,
      onclick: async () => {
        view.tagCode = tag.code;
        s.error = "";
        try {
          await loadMaterials();
        } catch (err) {
          s.error = err.message;
          s.materials = [];
        }
        render();
      },
    }),
  );

  if (s.addingTheme) {
    const input = el("input", { class: "tab-input", placeholder: "分類名稱" });
    let cancelled = false;
    const submit = () => {
      if (!cancelled) {
        addTag(input.value);
      }
    };
    input.addEventListener("blur", submit);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        cancelled = true;
        s.addingTheme = false;
        render();
      }
    });
    const form = el(
      "form",
      {
        class: "tab-add-form",
        onsubmit: (event) => {
          event.preventDefault();
          submit();
        },
      },
      input,
    );
    tabs.push(form);
    queueMicrotask(() => input.focus());
  } else {
    tabs.push(
      el("button", {
        class: "tab add-tab",
        type: "button",
        "aria-label": "新增分類",
        text: "+",
        onclick: () => {
          s.addingTheme = true;
          render();
        },
      }),
    );
  }

  if (active) {
    tabs.push(
      el("button", {
        class: "tab-delete",
        type: "button",
        text: "刪除分類",
        onclick: () => openDeleteTagModal(active),
      }),
    );
  }

  return el("div", { class: "tabs" }, tabs);
}

async function addTag(rawName) {
  const name = rawName.trim();
  s.addingTheme = false;
  if (!name) {
    render();
    return;
  }
  try {
    const tag = await api(`/api/games/${view.gameCode}/tags`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    s.tags.push({ code: tag.code, name: tag.name });
    view.tagCode = tag.code;
    s.error = "";
    await loadMaterials();
  } catch (err) {
    s.error = err.message;
  }
  render();
}

function nameInput(material) {
  const input = el("input", { value: material.name, "aria-label": "素材名稱" });
  input.addEventListener("blur", async () => {
    const name = input.value.trim();
    if (!name) {
      input.value = material.name;
      return;
    }
    if (name === material.name) {
      return;
    }
    try {
      const updated = await api(`/api/materials/${material.code}`, {
        method: "PATCH",
        body: JSON.stringify({ name }),
      });
      material.name = updated.name;
      s.error = "";
    } catch (err) {
      s.error = err.message;
      input.value = material.name;
    }
    render();
  });
  return input;
}

function uploadLabel(material) {
  const file = el("input", { type: "file", accept: "image/*", hidden: true });
  file.addEventListener("change", async () => {
    const chosen = file.files?.[0];
    file.value = "";
    if (!chosen) {
      return;
    }
    const body = new FormData();
    body.append("image", chosen);
    try {
      const updated = await api(`/api/materials/${material.code}/image`, { method: "PUT", body });
      material.image_url = updated.image_url;
      s.error = "";
    } catch (err) {
      s.error = err.message;
    }
    render();
  });
  return el("label", { class: "upload-btn" }, "更換圖片", file);
}

function materialCard(tag, material) {
  return el(
    "article",
    { class: "card material-card" },
    el("button", {
      class: "material-delete",
      type: "button",
      "aria-label": `刪除 ${material.name}`,
      text: "×",
      onclick: () => openDeleteModal(tag, material),
    }),
    materialPreview(material, tag),
    nameInput(material),
    isModel(material)
      ? el("p", { class: "muted material-kind-label", text: "Model" })
      : uploadLabel(material),
  );
}

function libraryGrid(tag) {
  return el(
    "div",
    { class: "material-grid" },
    s.materials.map((material) => materialCard(tag, material)),
    el("button", {
      class: "card add-card",
      type: "button",
      "aria-label": "新增素材",
      text: "+",
      onclick: () => openAddModal(tag),
    }),
  );
}

/** 素材庫頁。修改 GameTag 與 GameMaterial。 */
function libraryPage() {
  const game = currentGame();
  const tag = currentTag();
  if (!game) {
    return el(
      "section",
      {},
      pageHeader("素材庫", "找不到遊戲"),
      el("p", { class: "muted", text: "請確認資料庫有 Game 資料。" }),
    );
  }
  return el(
    "section",
    {},
    pageHeader("素材庫", `${game.name}：可新增、刪除分類與素材`),
    s.error ? el("p", { class: "error", text: s.error }) : null,
    s.loading ? el("p", { class: "muted", text: "載入中…" }) : null,
    themeTabs(tag),
    tag
      ? libraryGrid(tag)
      : el("p", { class: "muted", text: "這個遊戲還沒有分類，先按上面的 + 新增一個。" }),
  );
}

function openDeleteModal(tag, material) {
  confirmDanger(
    "確認刪除素材",
    "刪除素材",
    `確定要從「${tag.name}」刪除「${material.name}」嗎？若沒有其他分類再用它，素材本身也會刪掉。`,
    async () => {
      try {
        await api(`/api/tags/${tag.code}/materials/${material.code}`, { method: "DELETE" });
        s.materials = s.materials.filter((item) => item.code !== material.code);
        s.error = "";
      } catch (err) {
        s.error = err.message;
      }
      render();
    },
  );
}

function openDeleteTagModal(tag) {
  confirmDanger(
    "確認刪除分類",
    "刪除分類",
    `確定要從這個遊戲移除「${tag.name}」嗎？其他遊戲若也用這個分類，不會被刪掉。`,
    async () => {
      try {
        await api(`/api/games/${view.gameCode}/tags/${tag.code}`, { method: "DELETE" });
        s.error = "";
        view.tagCode = null;
        await loadTags();
      } catch (err) {
        s.error = err.message;
      }
      render();
    },
  );
}

function generatingActions() {
  return [
    el("button", { type: "button", text: "生成中…", disabled: true }),
    el("button", { class: "ghost", type: "button", text: "返回", disabled: true }),
  ];
}

/** 把 FormData 傳送到這個分類。成功後關閉視窗並重新載入卡片。 */
async function postNewMaterial(tag, body, message) {
  try {
    const created = await api(`/api/tags/${tag.code}/materials`, { method: "POST", body });
    s.materials.push(created);
    s.error = "";
    closeModal();
    render();
  } catch (err) {
    message.textContent = err.message;
  }
}

/** Image / Model：附帶暫存檔 id。後端把 png 或 glb 移到 Shared。 */
async function addMaterialFromTemp(tag, name, tempId, message) {
  const body = new FormData();
  body.append("name", name);
  body.append("temp_id", tempId);
  await postNewMaterial(tag, body, message);
}

/** Placeholder：只傳送名稱。後端寫入色塊 SVG。 */
async function addMaterialByName(tag, name, message) {
  const body = new FormData();
  body.append("name", name);
  await postNewMaterial(tag, body, message);
}

/** Placeholder 表單。不呼叫 2D 或 3D 生成。輸入名稱後顯示色塊與首字。 */
function openAddPlaceholderForm(tag) {
  const nameField = el("input", { placeholder: "例如：木製寶箱" });
  const preview = el("img", { class: "preview-img", alt: "預覽" });
  const message = el("p", { class: "error" });
  const saveBtn = el("button", {
    type: "button",
    text: "加入素材庫",
    onclick: () => {
      const name = nameField.value.trim();
      if (!name) {
        return;
      }
      addMaterialByName(tag, name, message);
    },
  });

  // 名稱為空時顯示「?」。名稱為空時停用加入按鈕。
  function refreshPreview() {
    const name = nameField.value.trim();
    preview.src = placeholderImage(name, placeholderColor(tag.code));
    saveBtn.disabled = !name;
  }

  nameField.addEventListener("input", refreshPreview);
  refreshPreview();

  showAddPanel(
    "新增 Placeholder",
    el("h3", { text: "新增 Placeholder" }),
    el("label", {}, "素材名稱", nameField),
    preview,
    message,
    el(
      "div",
      { class: "modal-actions" },
      saveBtn,
      el("button", { class: "ghost", type: "button", text: "返回", onclick: () => openAddModal(tag) }),
    ),
  );
  queueMicrotask(() => nameField.focus());
}

function openAddModal(tag) {
  showAddPanel(
    "選擇素材類型",
    el("h3", { text: "選擇素材類型" }),
    el(
      "div",
      { class: "type-choice" },
      el("button", { type: "button", text: "Image", onclick: () => openAdd2dForm(tag) }),
      el("button", { type: "button", text: "Model", onclick: () => openAdd3dForm(tag) }),
      el("button", { type: "button", text: "Placeholder", onclick: () => openAddPlaceholderForm(tag) }),
    ),
    el("button", { class: "ghost", type: "button", text: "取消", onclick: closeModal }),
  );
}

function openGenerateForm(tag, spec) {
  const waitNote = el("p", {
    class: "muted hint",
    hidden: true,
    text: "生成可能需要幾分鐘，請稍候，不要重整。",
  });
  const message = el("p", { class: "error" });
  const actions = el("div", { class: "modal-actions" });

  function showIdleActions() {
    actions.replaceChildren(
      el("button", { type: "button", text: "生成預覽", onclick: generatePreview }),
      el("button", { class: "ghost", type: "button", text: "返回", onclick: () => openAddModal(tag) }),
    );
  }

  async function generatePreview() {
    const invalid = spec.validate();
    if (invalid) {
      message.textContent = invalid;
      return;
    }
    message.textContent = "";
    spec.setBusy(true);
    waitNote.hidden = false;
    actions.replaceChildren(...generatingActions());
    try {
      const result = await spec.generate();
      spec.showResult(result);
      spec.preview.hidden = false;
      waitNote.hidden = true;
      spec.setBusy(false);
      actions.replaceChildren(
        el("button", {
          type: "button",
          text: "加入素材庫",
          onclick: () => addMaterialFromTemp(tag, spec.name(), result.tempId, message),
        }),
        el("button", { class: "ghost", type: "button", text: "返回", onclick: () => openAddModal(tag) }),
      );
    } catch (err) {
      waitNote.hidden = true;
      spec.setBusy(false);
      message.textContent = err.message;
      showIdleActions();
    }
  }

  showIdleActions();
  showAddPanel(spec.title, ...spec.body, waitNote, spec.preview, message, actions);
  queueMicrotask(() => spec.focus());
}

function openAdd2dForm(tag) {
  const nameField = el("input", { placeholder: "例如：木製寶箱" });
  const preview = el("img", { class: "preview-img", alt: "預覽", hidden: true });
  openGenerateForm(tag, {
    title: "新增 Image",
    body: [el("h3", { text: "新增 Image" }), el("label", {}, "物件名稱", nameField)],
    preview,
    name: () => nameField.value.trim(),
    focus: () => nameField.focus(),
    setBusy: (busy) => {
      nameField.disabled = busy;
    },
    validate: () => (nameField.value.trim() ? "" : "請填寫物件名稱"),
    generate: () =>
      api(`/api/tags/${tag.code}/generate-2d`, {
        method: "POST",
        body: JSON.stringify({ objectName: nameField.value.trim() }),
      }),
    showResult: (result) => {
      preview.src = result.imageUrl;
    },
  });
}

function openAdd3dForm(tag) {
  const nameField = el("input", { placeholder: "例如：紅椅子" });
  const promptField = el("textarea", { placeholder: "英文描述給 Trellis，例如 a red chair" });
  const preview = el("div", { class: "model-preview", hidden: true });
  openGenerateForm(tag, {
    title: "新增 Model",
    body: [
      el("h3", { text: "新增 Model" }),
      el("label", {}, "素材標題", nameField),
      el("label", {}, "生成描述", promptField),
      el("p", { class: "muted hint", text: "送出時會自動加上 (low poly, with smooth curve)" }),
    ],
    preview,
    name: () => nameField.value.trim(),
    focus: () => nameField.focus(),
    setBusy: (busy) => {
      nameField.disabled = busy;
      promptField.disabled = busy;
    },
    validate: () => {
      if (!nameField.value.trim()) {
        return "請填寫素材標題";
      }
      if (!promptField.value.trim()) {
        return "請填寫生成描述";
      }
      return "";
    },
    generate: () =>
      api(`/api/tags/${tag.code}/generate-3d`, {
        method: "POST",
        body: JSON.stringify({ prompt: promptField.value.trim() }),
      }),
    showResult: (result) => {
      preview.replaceChildren(
        el("model-viewer", {
          src: result.modelUrl,
          "camera-controls": true,
          "auto-rotate": true,
          "interaction-prompt": "none",
          "shadow-intensity": "1",
          alt: nameField.value.trim(),
        }),
      );
    },
  });
}

export {
  libraryPage,
  loadTags,
};
