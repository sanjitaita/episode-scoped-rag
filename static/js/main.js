import { getSeasons, getShows } from "./api.js";
import { renderHome } from "./home.js";
import { openPicker } from "./picker.js";
import { el, recall, remember, slugify } from "./util.js";

const app = document.getElementById("app");
const dialog = document.getElementById("picker");
const cache = { shows: null, seasons: {} };

async function loadShows() {
  if (!cache.shows) {
    cache.shows = await getShows();
  }
  return cache.shows;
}

async function loadSeasons(show) {
  if (!cache.seasons[show]) {
    cache.seasons[show] = await getSeasons(show);
  }
  return cache.seasons[show];
}

function showStatus(message) {
  app.replaceChildren(el("p", { class: "status" }, message));
}

async function choose(show, current) {
  const seasons = await loadSeasons(show);
  openPicker(dialog, show, seasons, current ?? recall(show), ({ season, episode }) => {
    remember(show, { season, episode });
    location.hash = `#/ask/${slugify(show)}/${season}/${episode}`;
  });
}

async function showHome() {
  const shows = await loadShows();
  const seasons = await Promise.all(shows.map((show) => loadSeasons(show).catch(() => null)));
  const seasonsByShow = Object.fromEntries(shows.map((show, i) => [show, seasons[i]]));
  renderHome(app, shows, seasonsByShow, (show) => choose(show));
}

async function showChat(slug, season, episode) {
  showStatus(`Chat for ${slug} through S${season}·E${episode} is coming in the next commit.`);
}

async function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/");
  try {
    if (parts[0] === "ask" && parts.length === 4) {
      await showChat(parts[1], Number(parts[2]), Number(parts[3]));
    } else {
      await showHome();
    }
    window.scrollTo(0, 0);
  } catch (error) {
    showStatus(`Couldn't load shows. Is the server running? (${error.message})`);
  }
}

window.addEventListener("hashchange", route);
route();
