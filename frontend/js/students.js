/** 老師的學生名單。 */
import { api } from "./api.js";
import { clearMaterialConfigState, loadAssignment, loadStudentMaterialLists } from "./assign.js";
import { confirmDanger, el, pageHeader } from "./dom.js";
import { clearWorkflowState, parseRoute, render, s, view } from "./state.js";
import { loadWorkflow } from "./workflow.js";
async function addStudent(rawUsername) {
  const username = rawUsername.trim();
  if (!username) {
    s.error = "請輸入學生帳號";
    render();
    return;
  }
  try {
    const student = await api("/api/students", {
      method: "POST",
      body: JSON.stringify({ username }),
    });
    s.students.push({ ...student, id: Number(student.id) });
    s.students.sort((a, b) => a.username.localeCompare(b.username));
    s.error = "";
    if (view.studentId == null) {
      view.studentId = Number(student.id);
      try {
        await loadStudentMaterialLists();
      } catch (err) {
        s.error = err.message;
      }
    }
  } catch (err) {
    s.error = err.message;
  }
  render();
}

async function removeStudent(id) {
  try {
    await api(`/api/students/${id}`, { method: "DELETE" });
    s.students = s.students.filter((student) => student.id !== id);
    if (view.studentId === id) {
      view.studentId = s.students[0]?.id ?? null;
      clearWorkflowState();
      clearMaterialConfigState();
      s.materialLists = {};
      s.materialListsStudentId = null;
      if (view.studentId) {
        await loadStudentMaterialLists();
      }
      if (parseRoute().page === "workflow" && view.studentId) {
        await loadWorkflow();
      }
      if (parseRoute().page === "assign" && view.studentId) {
        await loadAssignment();
      }
    }
    s.error = "";
  } catch (err) {
    s.error = err.message;
  }
  render();
}

/** 學生名單頁。新增與刪除都呼叫後端。 */
function studentsPage() {
  const nameField = el("input", { placeholder: "學生帳號", "aria-label": "學生帳號" });
  const form = el(
    "form",
    {
      class: "inline-form",
      onsubmit: (event) => {
        event.preventDefault();
        addStudent(nameField.value);
      },
    },
    nameField,
    el("button", { type: "submit", text: "新增學生" }),
  );
  const rows = s.students.map((student) =>
    el(
      "li",
      { class: "card student-row" },
      el("span", { text: student.username }),
      el("button", {
        class: "ghost",
        type: "button",
        text: "刪除",
        onclick: () => openDeleteStudentModal(student),
      }),
    ),
  );
  return el(
    "section",
    {},
    pageHeader("學生", `${s.teacher?.username ?? ""} 的學生名單`),
    form,
    s.error ? el("p", { class: "error", text: s.error }) : null,
    s.students.length === 0
      ? el("p", { class: "muted", text: "還沒有學生，用上面的欄位新增一個。" })
      : el("ul", { class: "student-list" }, rows),
  );
}

function openDeleteStudentModal(student) {
  confirmDanger(
    "確認刪除學生",
    "刪除學生",
    `確定要刪除「${student.username}」嗎？這位學生的關卡配置紀錄也會一起刪除。`,
    () => removeStudent(student.id),
  );
}

export {
  studentsPage,
};
