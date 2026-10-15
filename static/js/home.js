import { el, episodeCount, poster } from "./util.js";

function tile(show, seasons, onPick) {
  const meta = seasons
    ? `${seasons.length} season${seasons.length === 1 ? "" : "s"} · ${episodeCount(seasons)} episodes`
    : "";

  return el(
    "button",
    { class: "tile", type: "button", onClick: () => onPick(show) },
    poster(show, "tile-poster"),
    el("span", { class: "tile-name" }, show),
    el("span", { class: "tile-meta mono" }, meta)
  );
}

function comingSoon() {
  return el(
    "div",
    { class: "tile tile-soon", "aria-hidden": "true" },
    el("div", { class: "tile-poster mono" }, "More shows on the way")
  );
}

export function renderHome(root, shows, seasonsByShow, onPick) {
  const intro = el(
    "section",
    { class: "home-intro" },
    el(
      "h1",
      { class: "home-title" },
      "Ask about the show you're watching, ",
      el("em", {}, "without the spoilers.")
    ),
    el(
      "p",
      { class: "home-lede" },
      "Pick a show and tell us how far you've gotten. ",
      el("strong", {}, "Answers only draw on episodes you've already seen,"),
      " so nothing ahead of you can slip through."
    )
  );

  const tiles = el("div", { class: "tiles" });
  for (const show of shows) {
    tiles.append(tile(show, seasonsByShow[show], onPick));
  }
  tiles.append(comingSoon());

  const shelf = el(
    "section",
    { class: "shelf" },
    el(
      "div",
      { class: "shelf-head" },
      el("h2", { class: "shelf-title" }, "Shows"),
      el("span", { class: "shelf-count mono" }, `${shows.length} available`)
    ),
    tiles
  );

  root.replaceChildren(intro, shelf);
}
