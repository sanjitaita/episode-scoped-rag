import { code, el, episodeCount, poster, progressBar, watchOrder } from "./util.js";

function options(values, label, selected) {
  return values.map((value) =>
    el("option", { value, selected: value === selected }, `${label} ${value}`)
  );
}

export function openPicker(dialog, show, seasons, initial, onConfirm) {
  const total = episodeCount(seasons);
  let season = initial?.season ?? seasons[0].season;
  let episode = initial?.episode ?? seasons[0].episodes[0];

  const seasonSelect = el("select", { class: "select", id: "picker-season" });
  const episodeSelect = el("select", { class: "select", id: "picker-episode" });
  const progress = el("div", { class: "progress" });
  const note = el("p", { class: "picker-note" });

  function episodesOf(number) {
    return seasons.find((entry) => entry.season === number).episodes;
  }

  function refresh() {
    seasonSelect.replaceChildren(...options(seasons.map((entry) => entry.season), "Season", season));
    episodeSelect.replaceChildren(...options(episodesOf(season), "Episode", episode));

    const order = watchOrder(seasons, season, episode);
    progress.replaceChildren(
      progressBar(order / total),
      el(
        "div",
        { class: "progress-label mono" },
        el("span", {}, `${order} of ${total} episodes`),
        el("span", {}, `${Math.round((order / total) * 100)}%`)
      )
    );
    note.textContent = `Anything after ${code(season, episode)} stays out of the conversation.`;
  }

  seasonSelect.addEventListener("change", () => {
    season = Number(seasonSelect.value);
    episode = episodesOf(season)[0];
    refresh();
  });

  episodeSelect.addEventListener("change", () => {
    episode = Number(episodeSelect.value);
    refresh();
  });

  const body = el(
    "div",
    { class: "picker-body" },
    el(
      "div",
      { class: "picker-show" },
      poster(show, "picker-thumb", false),
      el("h2", { class: "picker-title" }, show)
    ),
    el("p", { class: "picker-question" }, "Where are you in the show?"),
    el(
      "div",
      { class: "picker-fields" },
      el("label", { class: "field" }, el("span", { class: "field-label mono" }, "Season"), seasonSelect),
      el("label", { class: "field" }, el("span", { class: "field-label mono" }, "Last episode watched"), episodeSelect)
    ),
    progress,
    note
  );

  const actions = el(
    "div",
    { class: "picker-actions" },
    el("button", { class: "btn", type: "button", onClick: () => dialog.close() }, "Cancel"),
    el(
      "button",
      {
        class: "btn btn-primary",
        type: "button",
        onClick: () => {
          dialog.close();
          onConfirm({ season, episode });
        },
      },
      "Start asking"
    )
  );

  refresh();
  dialog.replaceChildren(body, actions);
  dialog.onclick = (event) => {
    if (event.target === dialog) {
      dialog.close();
    }
  };
  dialog.showModal();
  seasonSelect.focus();
}
