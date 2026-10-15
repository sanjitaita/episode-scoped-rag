import { code, el, episodeCount, loadSetting, progressBar, saveSetting, watchOrder } from "./util.js";

const SUGGESTIONS = [
  "Catch me up on the last episode I watched.",
  "Who are the main characters so far?",
  "What's the biggest conflict right now?",
];

const MODES = {
  quick: {
    label: "Quick",
    hint: "Fast and sticks to what happened. It can miss or misstate details, so use Deep for “why” questions.",
  },
  deep: {
    label: "Deep",
    hint: "Lists the key facts first, then explains. Slower, but better for motives and analysis.",
  },
};

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatInline(text) {
  return escapeHtml(text).replace(/\[S(\d+)E(\d+)\]/g, '<span class="cite">S$1·E$2</span>');
}

function formatParagraphs(text) {
  return text
    .trim()
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${formatInline(paragraph).replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function splitDeep(text) {
  const match = text.match(/key facts:?\s*([\s\S]*?)\n\s*\**answer:?\**\s*([\s\S]*)/i);
  if (!match) {
    return null;
  }
  const facts = match[1]
    .split("\n")
    .map((line) => line.replace(/^\s*(?:[-*•]|\d+[.)])\s*/, "").trim())
    .filter((line) => line.length > 0);
  return { facts, answer: match[2].trim() };
}

function renderReply(container, text) {
  const deep = splitDeep(text);
  if (!deep || !deep.answer) {
    container.innerHTML = formatParagraphs(text);
    return;
  }

  container.innerHTML = formatParagraphs(deep.answer);
  if (deep.facts.length) {
    const list = el("ul", { class: "facts-list" });
    list.innerHTML = deep.facts.map((fact) => `<li>${formatInline(fact)}</li>`).join("");
    container.append(
      el(
        "details",
        { class: "facts" },
        el("summary", { class: "facts-summary mono" }, `Key facts (${deep.facts.length})`),
        list
      )
    );
  }
}

function sourceList(sources) {
  if (!sources.length) {
    return null;
  }
  return el(
    "div",
    { class: "sources" },
    el("span", { class: "sources-label mono" }, "From"),
    ...sources.map((source) =>
      el("span", { class: "source mono" }, `${code(source.season, source.episode)} ${source.title}`)
    )
  );
}

export function renderChat(root, watch, { onChange, ask }) {
  const { show, season, episode, seasons } = watch;
  const order = watchOrder(seasons, season, episode);
  const total = episodeCount(seasons);
  const range = order === 1 ? "episode 1" : `episodes 1–${order}`;
  let mode = loadSetting("answer-mode", "quick") === "deep" ? "deep" : "quick";

  const log = el("div", { class: "log", "aria-live": "polite" });
  const input = el("textarea", {
    class: "composer-input",
    rows: 1,
    placeholder: `Ask anything up to ${code(season, episode)}`,
    "aria-label": "Your question",
  });
  const send = el("button", { class: "btn btn-primary", type: "submit" }, "Ask");
  const hint = el("p", { class: "mode-hint" });
  const switcher = el("div", { class: "mode-switch", role: "radiogroup", "aria-label": "Answer style" });

  function setMode(next) {
    mode = next;
    saveSetting("answer-mode", mode);
    for (const option of switcher.children) {
      option.setAttribute("aria-checked", String(option.dataset.mode === mode));
    }
    hint.textContent = MODES[mode].hint;
  }

  for (const [key, value] of Object.entries(MODES)) {
    switcher.append(
      el(
        "button",
        { class: "mode-option", type: "button", role: "radio", "data-mode": key, onClick: () => setMode(key) },
        value.label
      )
    );
  }
  setMode(mode);

  const empty = el(
    "div",
    { class: "empty" },
    el("h2", { class: "empty-title" }, `You're caught up through Season ${season}, Episode ${episode}.`),
    el("p", { class: "empty-sub" }, "Ask about characters, plot, or what you think it all means."),
    el(
      "div",
      { class: "suggestions" },
      ...SUGGESTIONS.map((text) =>
        el("button", { class: "suggestion", type: "button", onClick: () => submit(text) }, text)
      )
    )
  );
  log.append(empty);

  function resize() {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  }

  function setBusy(busy) {
    input.disabled = busy;
    send.disabled = busy;
    for (const option of switcher.children) {
      option.disabled = busy;
    }
  }

  async function submit(question) {
    const text = question.trim();
    if (!text || send.disabled) {
      return;
    }

    const askedMode = mode;
    empty.remove();
    input.value = "";
    resize();
    setBusy(true);

    const status = askedMode === "deep" ? `Thinking it through · ${range}` : `Reading ${range}`;
    const reply = el("div", { class: "entry-a entry-pending" }, status);
    const entry = el(
      "article",
      { class: "entry" },
      askedMode === "deep" ? el("span", { class: "entry-mode mono" }, "Deep") : null,
      el("p", { class: "entry-q" }, text),
      reply
    );
    log.append(entry);
    entry.scrollIntoView({ behavior: "smooth", block: "start" });

    const started = Date.now();
    const timer = setInterval(() => {
      const seconds = Math.round((Date.now() - started) / 1000);
      if (seconds >= 5) {
        reply.textContent = `${status} · ${seconds}s`;
      }
    }, 1000);

    try {
      const result = await ask(show, season, episode, text, askedMode);
      if (!result.answer || !result.answer.trim()) {
        throw new Error("The model didn't finish an answer. Try asking again.");
      }
      reply.className = "entry-a";
      renderReply(reply, result.answer);
      const sources = sourceList(result.sources);
      if (sources) {
        entry.append(sources);
      }
    } catch (error) {
      reply.className = "entry-a entry-error";
      reply.textContent = error.message || "Something went wrong. Try again.";
    } finally {
      clearInterval(timer);
      setBusy(false);
      input.focus();
    }
  }

  input.addEventListener("input", resize);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit(input.value);
    }
  });

  const composer = el(
    "form",
    {
      class: "composer",
      onSubmit: (event) => {
        event.preventDefault();
        submit(input.value);
      },
    },
    el("div", { class: "composer-bar" }, switcher, hint),
    el("div", { class: "composer-box" }, input, send),
    el(
      "p",
      { class: "composer-note" },
      `Answers use ${range} only. Each question is answered on its own.`
    )
  );

  const head = el(
    "div",
    { class: "chat-head" },
    el("a", { class: "chat-back mono", href: "#/" }, "← All shows"),
    el(
      "div",
      { class: "chat-title-row" },
      el("h1", { class: "chat-title" }, show),
      el(
        "button",
        { class: "watch-chip mono", type: "button", onClick: onChange, title: "Change where you are" },
        `Through ${code(season, episode)}`,
        el("span", { class: "watch-chip-edit" }, "Change")
      )
    ),
    el("div", { class: "chat-progress" }, progressBar(order / total))
  );

  root.replaceChildren(el("section", { class: "chat" }, head, log, composer));
  input.focus();
}
