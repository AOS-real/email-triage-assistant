// Display only: every decision, check and rule is made on the server (triage/).
// All text is inserted with textContent, so nothing from an email can run as code.

const state = { inbox: null, selected: null, outcome: null, rulesNote: null };

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

async function post(path, data = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await response.json();
  if (result.inbox) state.inbox = result.inbox;
  return result;
}

const SECTION_NAME = { needs_you: "Needs you", can_wait: "Can wait", not_sure: "Needs you" };

function render() {
  const inbox = state.inbox;
  document.getElementById("summary").textContent = inbox.summary.text;
  const needs = inbox.messages.filter(m => m.section !== "can_wait");
  needs.sort((a, b) => (b.section === "not_sure") - (a.section === "not_sure"));
  const wait = inbox.messages.filter(m => m.section === "can_wait");
  fillList("needs", needs);
  fillList("wait", wait);
  document.getElementById("needs-count").textContent = `(${needs.length})`;
  document.getElementById("wait-count").textContent = `(${wait.length})`;
  renderDetail();
  renderRules();
}

function fillList(id, messages) {
  const list = document.getElementById(id);
  list.replaceChildren(...messages.map(messageRow));
}

function messageRow(m) {
  const unsure = m.section === "not_sure";
  const classes = ["message", unsure ? "unsure" : "", state.selected === m.id ? "selected" : ""];
  const chips = [
    unsure ? el("span", { class: "chip unsure" }, "Not sure") : null,
    m.label.warnings.length ? el("span", { class: "chip warn" }, "Warning") : null,
    m.moved_by_you ? el("span", { class: "chip you" }, "Moved by you") : null,
  ];
  const row = el("li", { class: classes.join(" ").trim(), onclick: () => select(m.id) },
    el("div", { class: "subject" }, chips, m.subject),
    el("div", { class: "from" }, m.from),
    el("div", { class: "headline" }, m.moved_by_you ? `You: ${m.moved_by_you}` : m.label.headline));
  if (unsure && !m.moved_by_you) {
    row.append(el("div", { class: "choice" },
      el("span", {}, m.label.ask),
      el("button", { onclick: e => { e.stopPropagation(); move(m.id, "needs_you", "once"); } },
         "Keep in Needs you"),
      el("button", { class: "quiet",
                     onclick: e => { e.stopPropagation(); move(m.id, "can_wait", "once"); } },
         "Move to Can wait")));
  }
  return row;
}

function select(id) {
  if (state.selected !== id) state.outcome = null;
  state.selected = id;
  render();
}

function renderDetail() {
  const panel = document.getElementById("detail");
  const m = state.inbox.messages.find(x => x.id === state.selected);
  if (!m) {
    panel.replaceChildren(el("p", { class: "empty" },
      "Select a message to see why it was placed there."));
    return;
  }
  const unsure = m.section === "not_sure";
  const label = m.label;
  const attachments = m.attachments.map(a =>
    `${a.name}${a.readable ? "" : " (could not be read)"}`).join(", ");
  const target = m.section === "can_wait" ? "needs_you" : "can_wait";

  panel.replaceChildren(...[
    el("h2", {}, m.subject),
    el("p", { class: "from" }, `From ${m.from}${m.sender_known ? "" : " (new sender)"}`),
    attachments ? el("p", {}, `Attachments: ${attachments}`) : null,
    el("div", { class: "body" }, m.body),
    el("div", { class: `label-box${unsure ? " unsure" : ""}` },
      m.moved_by_you
        ? el("h3", {}, `${SECTION_NAME[m.section]}: moved by you (${m.moved_by_you})`)
        : el("h3", {}, `${SECTION_NAME[m.section]}: ${label.headline}`),
      m.moved_by_you ? el("p", {}, `The assistant's own reading: ${label.headline}.`) : null,
      el("p", { class: "part" }, "What the assistant used"),
      el("ul", {}, label.used.length ? label.used.map(u => el("li", {}, u))
                                     : el("li", {}, "No request or deadline in the email")),
      el("p", { class: "part" }, "What it did not use"),
      el("ul", {}, label.not_used.map(u => el("li", {}, u))),
      label.rule_id ? el("p", {}, `Rule ${label.rule_id} is in What I've learned, where you can change or forget it.`) : null),
    label.warnings.length ? el("div", { class: "warnings" },
      el("p", { class: "part" }, "Warnings"),
      el("ul", {}, label.warnings.map(w => el("li", {}, w)))) : null,
    moveControls(m, target),
    state.outcome,
    el("p", { class: "status" },
      `Model output for this message: ${m.source === "simulated" ? "simulated (recorded by hand)" : m.source}.`),
  ].filter(Boolean));
}

function moveControls(m, target) {
  const box = el("div", { class: "choice" });
  if (m.can_undo) {
    box.append(el("button", { class: "quiet", onclick: () => undo(m.id) }, "Undo last move"));
  }
  const open = el("button", {}, target === "needs_you" ? "Move back to Needs you" : "Move to Can wait");
  open.addEventListener("click", () => {
    box.replaceChildren(el("span", {}, "Why?"),
      ...m.reasons.map(([key, text]) =>
        el("button", { class: "quiet", onclick: () => move(m.id, target, key) }, text)));
  });
  box.append(open);
  return box;
}

async function move(id, section, reason) {
  state.selected = id;
  const result = await post("/api/move", { id, section, reason });
  if (result.error) {
    state.outcome = el("p", { class: "error" }, result.error);
  } else {
    state.outcome = outcomeBox(result);
  }
  render();
}

function outcomeBox(result) {
  const box = el("div", { class: "outcome" }, el("p", {}, `Moved to ${result.to}.`));
  if (result.message) box.append(el("p", {}, result.message));
  if (result.rule) {
    const affected = result.affected.length
      ? `This would also move: ${result.affected.join("; ")}.`
      : "No other message would move now.";
    box.append(
      el("p", {}, el("strong", {}, "Learn this rule? "), result.rule.text + "."),
      el("p", {}, affected),
      el("p", {}, "It would expire on " + result.rule.expires + " unless you renew it."),
      el("div", { class: "choice" },
        el("button", { onclick: () => saveRule(result.rule.id) }, "Save rule"),
        el("button", { class: "quiet", onclick: () => discardRule() }, "Not now")));
  }
  return box;
}

async function saveRule(ruleId) {
  const result = await post("/api/rules/save", { rule_id: ruleId });
  state.outcome = result.error
    ? el("p", { class: "error" }, result.error)
    : el("div", { class: "outcome" }, el("p", {}, `Saved: ${result.rule.text}.`));
  render();
}

async function discardRule() {
  await post("/api/rules/discard");
  state.outcome = el("div", { class: "outcome" }, el("p", {}, "Moved. No rule was saved."));
  render();
}

async function undo(id) {
  const result = await post("/api/undo", { id });
  state.outcome = result.error ? el("p", { class: "error" }, result.error)
                               : el("div", { class: "outcome" }, el("p", {}, "Move undone."));
  render();
}

function renderRules() {
  const list = document.getElementById("rules");
  const rules = state.inbox.rules;
  const note = state.rulesNote ? el("li", { class: "outcome" }, state.rulesNote) : null;
  if (!rules.length) {
    list.replaceChildren(...[note, el("li", { class: "empty" },
      "Nothing learned yet. A rule appears here only when you move a message and confirm it.")]
      .filter(Boolean));
    return;
  }
  list.replaceChildren(...[note].filter(Boolean), ...rules.map(rule => {
    const other = rule.section === "needs_you" ? "can_wait" : "needs_you";
    const feedback = el("p", { class: "error" });
    return el("li", { class: `rule${rule.expired ? " expired" : ""}` },
      el("div", { class: "text" }, rule.text),
      el("div", { class: "meta" }, `Because: ${rule.evidence}`),
      el("div", { class: "meta" }, rule.expired
        ? `Expired on ${rule.expires}; no longer applied.`
        : `Learned ${rule.created}; expires ${rule.expires}.`),
      el("div", { class: "choice" },
        el("button", { class: "quiet", onclick: () => ruleAction("edit", { rule_id: rule.id, section: other }, feedback) },
           `Send to ${SECTION_NAME[other]} instead`),
        rule.expired ? el("button", { class: "quiet", onclick: () => ruleAction("renew", { rule_id: rule.id }, feedback) }, "Renew") : null,
        el("button", { class: "quiet", onclick: () => ruleAction("forget", { rule_id: rule.id }, feedback) }, "Forget")),
      feedback);
  }));
}

async function ruleAction(kind, data, feedback) {
  const result = await post(`/api/rules/${kind}`, data);
  if (result.error) { feedback.textContent = result.error; return; }
  state.rulesNote = kind === "forget"
    ? (result.resorted.length ? `Forgotten. Re-sorted: "${result.resorted.join('", "')}"`
                              : "Forgotten. No message changed section.")
    : kind === "edit" ? `Changed: ${result.rule.text}.` : "Renewed for another 90 days.";
  render();
}

document.getElementById("ask").addEventListener("submit", async event => {
  event.preventDefault();
  const input = document.getElementById("ask-text");
  const reply = document.getElementById("ask-reply");
  if (!input.value.trim()) return;
  reply.hidden = false;
  reply.textContent = "Reading your request...";
  const result = await post("/api/request", { text: input.value });
  reply.className = `reply ${result.kind}`;
  reply.textContent = result.text;
});

document.getElementById("reset").addEventListener("click", async () => {
  state.selected = null;
  state.outcome = null;
  state.rulesNote = null;
  await post("/api/reset");
  render();
});

async function load() {
  // A13: the inbox is acknowledged at once ("Sorting..."), then filled when placed.
  const response = await fetch("/api/inbox");
  state.inbox = await response.json();
  render();
}

load();
