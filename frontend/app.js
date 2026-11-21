const view = document.querySelector("#view");
const title = document.querySelector("#page-title");
const toast = document.querySelector("#toast");
let quiz = null;
let quizIndex = 0;
let quizScore = 0;
let quizSelected = -1;

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  let data;
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("visible"), 2600);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setTitle(text) {
  title.textContent = text;
}

function activateView(name) {
  document.querySelectorAll("[data-view]").forEach((element) => {
    element.classList.toggle("active", element.dataset.view === name);
  });
  document.querySelector(".sidebar").classList.remove("open");
}

async function renderDashboard() {
  activateView("dashboard");
  setTitle("Dashboard");
  const stats = await api("/api/dashboard");
  view.innerHTML = `
    <div class="grid-cards">
      ${[
        ["Notes", stats.notes],
        ["Tasks", stats.tasks],
        ["Completed", stats.completed],
        ["AI messages", stats.messages]
      ].map(([label, value]) => `
        <article class="card stat-card"><strong>${value}</strong><span>${label}</span></article>
      `).join("")}
    </div>
    <article class="card welcome-card">
      <h2>Welcome to SmartDesk</h2>
      <p>AI assistance, Python tools, notes, tasks, quiz practice, and local statistics in one workspace.</p>
    </article>`;
}

async function renderChat() {
  activateView("chat");
  setTitle("AI Assistant");
  let history = [];
  let settings = { ai_configured: false };
  try {
    [history, settings] = await Promise.all([
      api("/api/chat"),
      api("/api/settings")
    ]);
  } catch (error) {
    showToast(error.message);
  }
  const setupBanner = settings.ai_configured ? "" : `
    <div class="card" style="margin-bottom:10px;padding:12px 14px;border-color:#dc7b45">
      <strong>AI setup required</strong>
      <p style="margin:5px 0 9px;color:var(--muted)">Add an API key in Settings before sending messages.</p>
      <button class="button" id="open-chat-settings" type="button">Open Settings</button>
    </div>`;
  view.innerHTML = `
    ${setupBanner}
    <div class="chat-layout">
      <div>
        <div class="card chat-box" id="chat-box">
          ${history.length ? history.map(message => `
            <div class="message ${message.role === "user" ? "user" : ""}">
              <strong>${escapeHtml(message.role)}</strong>${escapeHtml(message.content)}
            </div>`).join("") : '<div class="empty">Start a new conversation.</div>'}
        </div>
        <form class="form-row" id="chat-form" style="margin-top:10px">
          <input class="field" id="chat-input" placeholder="Ask SmartDesk..." autocomplete="off">
          <button class="button" id="chat-send" type="submit">Send</button>
        </form>
      </div>
      <aside class="card chat-side">
        <strong>Conversation</strong>
        <p>Messages are stored locally through the Python backend.</p>
        <button class="button danger" id="clear-chat" type="button">Clear chat</button>
      </aside>
    </div>`;
  const openSettings = document.querySelector("#open-chat-settings");
  if (openSettings) {
    openSettings.addEventListener("click", () => {
      const rendering = renderSettings();
      if (rendering?.catch) rendering.catch((error) => showToast(error.message));
    });
  }
  const box = document.querySelector("#chat-box");
  box.scrollTop = box.scrollHeight;

  document.querySelector("#chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.querySelector("#chat-input");
    const send = document.querySelector("#chat-send");
    const prompt = input.value.trim();
    if (!prompt) return;
    send.disabled = true;
    input.disabled = true;
    box.insertAdjacentHTML("beforeend", `<div class="message user"><strong>User</strong>${escapeHtml(prompt)}</div>`);
    box.scrollTop = box.scrollHeight;
    try {
      const result = await api("/api/chat", {
        method: "POST",
        body: JSON.stringify({ prompt })
      });
      box.insertAdjacentHTML("beforeend", `<div class="message"><strong>AI</strong>${escapeHtml(result.answer)}</div>`);
    } catch (error) {
      box.insertAdjacentHTML("beforeend", `<div class="message error"><strong>Error</strong>${escapeHtml(error.message)}</div>`);
    } finally {
      input.value = "";
      input.disabled = false;
      send.disabled = false;
      input.focus();
      box.scrollTop = box.scrollHeight;
    }
  });

  document.querySelector("#clear-chat").addEventListener("click", async () => {
    try {
      await api("/api/chat/clear", { method: "POST", body: "{}" });
      await renderChat();
    } catch (error) {
      showToast(error.message);
    }
  });
}

function renderCode() {
  activateView("code");
  setTitle("Python Code Lab");
  view.innerHTML = `
    <div class="editor-grid">
      <div>
        <textarea id="code-editor" class="code-area" spellcheck="false">print("Hello from SmartDesk!")</textarea>
      </div>
      <div>
        <pre id="code-output" class="output-area">Output appears here.</pre>
      </div>
    </div>
    <button class="button" id="run-code" style="margin-top:12px">Run Python</button>`;
  document.querySelector("#run-code").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    const output = document.querySelector("#code-output");
    try {
      const result = await api("/api/code", {
        method: "POST",
        body: JSON.stringify({ code: document.querySelector("#code-editor").value })
      });
      output.textContent = result.output;
    } catch (error) {
      output.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

function renderCalculator() {
  activateView("calculator");
  setTitle("Safe Calculator");
  view.innerHTML = `
    <article class="card panel">
      <form id="calculator-form" class="stack">
        <input class="field" id="expression" placeholder="Example: (10 - 2) / 4" autocomplete="off">
        <button class="button" type="submit">Calculate</button>
      </form>
      <div class="card result" id="calculation-result">Result:</div>
    </article>`;
  document.querySelector("#calculator-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const result = document.querySelector("#calculation-result");
    try {
      const data = await api("/api/calculate", {
        method: "POST",
        body: JSON.stringify({ expression: document.querySelector("#expression").value })
      });
      result.classList.remove("error");
      result.textContent = `Result: ${data.result}`;
    } catch (error) {
      result.classList.add("error");
      result.textContent = `Error: ${error.message}`;
    }
  });
}

async function renderNotes() {
  activateView("notes");
  setTitle("Notes");
  const notes = await api("/api/notes");
  view.innerHTML = `
    <article class="card panel">
      <form id="note-form" class="stack">
        <input class="field" id="note-title" maxlength="200" placeholder="Note title">
        <textarea class="textarea" id="note-content" maxlength="50000" placeholder="Write a note..."></textarea>
        <button class="button" type="submit" style="width:max-content">Add note</button>
      </form>
      <div class="item-list" id="note-list" style="margin-top:16px"></div>
    </article>`;

  const list = document.querySelector("#note-list");
  function paint() {
    list.innerHTML = notes.length ? notes.map(note => `
      <div class="list-item">
        <div class="item-main">
          <div class="item-title">${escapeHtml(note.title)}</div>
          <div class="item-content">${escapeHtml(note.content)}</div>
        </div>
        <button class="icon-button delete" data-delete-note="${note.id}" title="Delete note">×</button>
      </div>`).join("") : '<div class="empty">No notes yet.</div>';
  }
  paint();

  document.querySelector("#note-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const titleValue = document.querySelector("#note-title").value.trim();
    const contentValue = document.querySelector("#note-content").value.trim();
    if (!titleValue || !contentValue) {
      showToast("Enter both a title and note content.");
      return;
    }
    try {
      await api("/api/notes", {
        method: "POST",
        body: JSON.stringify({ title: titleValue, content: contentValue })
      });
      await renderNotes();
    } catch (error) {
      showToast(error.message);
    }
  });

  list.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-delete-note]");
    if (!button) return;
    try {
      await api(`/api/notes/${button.dataset.deleteNote}`, { method: "DELETE" });
      await renderNotes();
    } catch (error) {
      showToast(error.message);
    }
  });
}

async function renderTasks() {
  activateView("tasks");
  setTitle("Tasks");
  const tasks = await api("/api/tasks");
  view.innerHTML = `
    <article class="card panel">
      <form class="form-row" id="task-form">
        <input class="field" id="task-title" maxlength="500" placeholder="Add a task">
        <button class="button" type="submit">Add</button>
      </form>
      <div class="item-list" id="task-list" style="margin-top:16px"></div>
    </article>`;
  const list = document.querySelector("#task-list");
  function paint() {
    list.innerHTML = tasks.length ? tasks.map(task => `
      <div class="list-item ${task.done ? "done" : ""}">
        <button class="icon-button" data-toggle-task="${task.id}" title="Toggle task">${task.done ? "✓" : "○"}</button>
        <div class="item-main"><div class="item-title">${escapeHtml(task.title)}</div></div>
        <button class="icon-button delete" data-delete-task="${task.id}" title="Delete task">×</button>
      </div>`).join("") : '<div class="empty">No tasks yet.</div>';
  }
  paint();

  document.querySelector("#task-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.querySelector("#task-title");
    const titleValue = input.value.trim();
    if (!titleValue) return;
    try {
      await api("/api/tasks", {
        method: "POST",
        body: JSON.stringify({ title: titleValue })
      });
      await renderTasks();
    } catch (error) {
      showToast(error.message);
    }
  });

  list.addEventListener("click", async (event) => {
    const toggle = event.target.closest("[data-toggle-task]");
    if (toggle) {
      try {
        await api(`/api/tasks/${toggle.dataset.toggleTask}`, { method: "PUT" });
        await renderTasks();
      } catch (error) {
        showToast(error.message);
      }
      return;
    }
    const remove = event.target.closest("[data-delete-task]");
    if (remove) {
      try {
        await api(`/api/tasks/${remove.dataset.deleteTask}`, { method: "DELETE" });
        await renderTasks();
      } catch (error) {
        showToast(error.message);
      }
    }
  });
}

async function renderQuiz() {
  activateView("quiz");
  setTitle("Python Quiz");
  quiz = await api("/api/quiz");
  quizIndex = 0;
  quizScore = 0;
  quizSelected = -1;
  paintQuiz();
}

function paintQuiz() {
  if (quizIndex >= quiz.length) {
    view.innerHTML = `
      <article class="card panel" style="text-align:center">
        <h2>Quiz complete</h2>
        <p style="font-size:32px;margin:12px 0">${quizScore}/${quiz.length}</p>
        <button class="button" id="restart-quiz">Try again</button>
      </article>`;
    document.querySelector("#restart-quiz").addEventListener("click", () => {
      renderQuiz().catch((error) => showToast(error.message));
    });
    return;
  }
  const item = quiz[quizIndex];
  view.innerHTML = `
    <article class="card panel">
      <div class="panel-header">
        <h2>Question ${quizIndex + 1} of ${quiz.length}</h2>
        <span style="color:var(--muted)">Score: ${quizScore}</span>
      </div>
      <p style="font-size:18px;font-weight:700">${escapeHtml(item.question)}</p>
      <div class="quiz-options">
        ${item.options.map((option, index) => `
          <button class="quiz-option ${quizSelected === index ? "selected" : ""}" data-answer="${index}">
            ${escapeHtml(option)}
          </button>`).join("")}
      </div>
      <button class="button" id="next-question">Next</button>
    </article>`;

  view.querySelectorAll("[data-answer]").forEach((button) => {
    button.addEventListener("click", () => {
      quizSelected = Number(button.dataset.answer);
      paintQuiz();
    });
  });
  document.querySelector("#next-question").addEventListener("click", () => {
    if (quizSelected < 0) {
      showToast("Select an answer before continuing.");
      return;
    }
    if (quizSelected === quiz[quizIndex].answer) quizScore++;
    quizIndex++;
    quizSelected = -1;
    paintQuiz();
  });
}

async function renderStatistics() {
  activateView("statistics");
  setTitle("Statistics");
  const stats = await api("/api/dashboard");
  view.innerHTML = `
    <article class="card panel">
      <div class="item-list">
        ${Object.entries(stats).map(([key, value]) => `
          <div class="list-item">
            <div class="item-main"><div class="item-title">${escapeHtml(key.replaceAll("_", " ").replace(/^\w/, char => char.toUpperCase()))}</div></div>
            <strong>${value}</strong>
          </div>`).join("")}
      </div>
    </article>`;
}

async function renderSettings() {
  activateView("settings");
  setTitle("Settings");
  const config = await api("/api/settings");
  view.innerHTML = `
    <article class="card panel">
      <form id="settings-form" class="settings-grid">
        <label>API key
          <input class="field" id="api-key" type="password" value="${escapeHtml(config.api_key)}">
        </label>
        <label>API endpoint
          <input class="field" id="api-endpoint" value="${escapeHtml(config.api_endpoint)}">
        </label>
        <label>Model
          <input class="field" id="api-model" value="${escapeHtml(config.model)}">
        </label>
        <label>Theme
          <select class="select" id="theme">
            <option value="dark" ${config.theme === "dark" ? "selected" : ""}>Dark</option>
            <option value="light" ${config.theme !== "dark" ? "selected" : ""}>Light</option>
          </select>
        </label>
        <div style="grid-column:1/-1"><button class="button" type="submit">Save settings</button></div>
      </form>
    </article>`;
  document.querySelector("#theme").value = config.theme === "dark" ? "dark" : "light";
  applyTheme(config.theme);
  document.querySelector("#settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const theme = document.querySelector("#theme").value;
    try {
      await api("/api/settings", {
        method: "POST",
        body: JSON.stringify({
          api_key: document.querySelector("#api-key").value,
          api_endpoint: document.querySelector("#api-endpoint").value,
          model: document.querySelector("#api-model").value,
          theme
        })
      });
      applyTheme(theme);
      showToast("Settings saved.");
    } catch (error) {
      showToast(error.message);
    }
  });
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme === "dark" ? "dark" : "light";
}

async function initialTheme() {
  try {
    applyTheme((await api("/api/settings")).theme);
  } catch {
    applyTheme("dark");
  }
}

const renderers = {
  dashboard: renderDashboard,
  chat: renderChat,
  code: renderCode,
  calculator: renderCalculator,
  notes: renderNotes,
  tasks: renderTasks,
  quiz: renderQuiz,
  statistics: renderStatistics,
  settings: renderSettings
};

document.querySelectorAll("[data-view]").forEach((element) => {
  element.addEventListener("click", (event) => {
    event.preventDefault();
    const name = element.dataset.view;
    const rendering = renderers[name]();
    if (rendering?.catch) rendering.catch((error) => showToast(error.message));
  });
});

document.querySelector("#menu-button").addEventListener("click", () => {
  document.querySelector(".sidebar").classList.toggle("open");
});

window.addEventListener("error", (event) => {
  showToast(event.message || "An unexpected page error occurred.");
});

window.addEventListener("unhandledrejection", (event) => {
  showToast(event.reason?.message || "An unexpected request error occurred.");
});

initialTheme();
renderDashboard().catch((error) => showToast(error.message));
