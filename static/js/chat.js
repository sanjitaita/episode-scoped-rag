import { code, el, episodeCount, progressBar, watchOrder } from "./util.js";

const SUGGESTIONS = [
  "Catch me up on the last episode I watched.",
  "Who are the main characters so far?",
  "What's the biggest conflict right now?",
];

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatAnswer(text) {
  return escapeHtml(text.trim())
    .split(/\n{2,}/)
    .map((paragraph) =>
      paragraph
        .replace(/\[S(\d+)E(\d+)\]/g, '<span class="cite">S$1·E$2</span>')
        .replace(/\n/g, "<br>")
    )
    .map((paragraph) => `<p>${paragraph}</p>`)
    .join("");
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

  const log = el("div", { class: "log", "aria-live": "polite" });
  const input = el("textarea", {
    class: "composer-input",
    rows: 1,
    placeholder: `Ask anything up to ${code(season, episode)}`,
    "aria-label": "Your question",
  });
  const send = el("button", { class: "btn btn-primary", type: "submit" }, "Ask");

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
  }

  async function submit(question) {
    const text = question.trim();
    if (!text || send.disabled) {
      return;
    }

    empty.remove();
    input.value = "";
    resize();
    setBusy(true);

    const reply = el("div", { class: "entry-a entry-pending" }, `Reading ${range}`);
    const entry = el("article", { class: "entry" }, el("p", { class: "entry-q" }, text), reply);
    log.append(entry);
    entry.scrollIntoView({ behavior: "smooth", block: "start" });

    try {
      const result = await ask(show, season, episode, text);
      reply.className = "entry-a";
      reply.innerHTML = formatAnswer(result.answer);
      const sources = sourceList(result.sources);
      if (sources) {
        entry.append(sources);
      }
    } catch (error) {
      reply.className = "entry-a entry-error";
      reply.textContent = error.message || "Something went wrong. Try again.";
    } finally {
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
