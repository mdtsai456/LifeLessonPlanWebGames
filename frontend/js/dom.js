/** 建立 DOM 節點與 modal。 */
import { THEME_COLORS } from "./state.js";
function el(tag, props, ...children) {
  const node = document.createElement(tag);
  Object.entries(props || {}).forEach(([key, value]) => {
    if (value == null || value === false) {
      return;
    }
    if (key === "class") {
      node.className = value;
    } else if (key === "text") {
      node.textContent = value;
    } else if (key.startsWith("on")) {
      node.addEventListener(key.slice(2), value);
    } else if (value === true) {
      node.setAttribute(key, "");
    } else {
      node.setAttribute(key, value);
    }
  });
  children.flat().forEach((child) => {
    if (child == null || child === false) {
      return;
    }
    node.append(typeof child === "string" ? document.createTextNode(child) : child);
  });
  return node;
}

function pageHeader(eyebrow, title, extra) {
  return el(
    "header",
    { class: "page-header" },
    el("div", {}, el("p", { class: "eyebrow", text: eyebrow }), el("h2", { text: title })),
    extra ?? null,
  );
}

function openModal(panel) {
  panel.addEventListener("click", (event) => event.stopPropagation());
  const backdrop = el("div", { class: "modal-backdrop", role: "presentation", onclick: closeModal }, panel);
  document.getElementById("modal-root").replaceChildren(backdrop);
}

function closeModal() {
  const root = document.getElementById("modal-root");
  if (root) {
    root.replaceChildren();
  }
}

function confirmDanger(label, title, message, onConfirm) {
  openModal(
    el(
      "div",
      { class: "card modal-panel", role: "dialog", "aria-modal": "true", "aria-label": label },
      el("h3", { text: title }),
      el("p", { text: message }),
      el(
        "div",
        { class: "modal-actions" },
        el("button", {
          class: "danger",
          type: "button",
          text: "刪除",
          onclick: async () => {
            closeModal();
            await onConfirm();
          },
        }),
        el("button", { class: "ghost", type: "button", text: "取消", onclick: closeModal }),
      ),
    ),
  );
}

function showAddPanel(label, ...children) {
  openModal(
    el(
      "div",
      { class: "card modal-panel", role: "dialog", "aria-modal": "true", "aria-label": label },
      ...children,
    ),
  );
}

function placeholderColor(seed) {
  return THEME_COLORS[[...seed].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % THEME_COLORS.length];
}

/** 產生色塊與名稱首字。卡片載入失敗時作為後備圖。Placeholder 表單輸入時也用此預覽。 */
function placeholderImage(name, color) {
  const raw = name.trim().charAt(0) || "?";
  const label = raw
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="36" fill="${color}"/>
  <text x="128" y="150" text-anchor="middle" font-size="72" fill="#ffffff" font-family="Segoe UI, sans-serif">${label}</text>
</svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function materialImage(material, tag) {
  if (material.image_url) {
    return material.image_url;
  }
  return placeholderImage(material.name, placeholderColor(tag?.code ?? ""));
}

function materialImg(material, tag) {
  const img = el("img", { src: materialImage(material, tag), alt: material.name });
  img.addEventListener("error", () => {
    img.src = placeholderImage(material.name, placeholderColor(tag?.code ?? ""));
  });
  return img;
}

function isModel(material) {
  return Boolean(material.model_url);
}

function materialPreview(material, tag) {
  if (isModel(material)) {
    return el("model-viewer", {
      class: "model-thumb",
      src: material.model_url,
      "camera-controls": true,
      "auto-rotate": true,
      "interaction-prompt": "none",
      "shadow-intensity": "1",
      alt: material.name,
    });
  }
  return materialImg(material, tag);
}

export {
  el,
  pageHeader,
  openModal,
  closeModal,
  confirmDanger,
  showAddPanel,
  placeholderColor,
  placeholderImage,
  materialImage,
  materialImg,
  isModel,
  materialPreview,
};
