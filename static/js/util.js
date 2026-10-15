export function slugify(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key.startsWith("on")) {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value !== false && value != null) {
      node.setAttribute(key, value === true ? "" : value);
    }
  }
  node.append(...children.filter((child) => child != null));
  return node;
}

export function poster(show, className, withFallbackTitle = true) {
  const frame = el("div", { class: className });
  const img = el("img", { src: `/static/posters/${slugify(show)}.jpg`, alt: "", loading: "lazy" });
  img.addEventListener("error", () => {
    img.remove();
    if (withFallbackTitle) {
      frame.append(el("div", { class: "tile-fallback" }, show));
    }
  });
  frame.append(img);
  return frame;
}

export function episodeCount(seasons) {
  return seasons.reduce((total, season) => total + season.episodes.length, 0);
}

export function watchOrder(seasons, season, episode) {
  let order = 0;
  for (const entry of seasons) {
    if (entry.season < season) {
      order += entry.episodes.length;
    } else if (entry.season === season) {
      order += entry.episodes.filter((number) => number <= episode).length;
    }
  }
  return order;
}

export function progressBar(fraction) {
  const percent = `${Math.round(fraction * 1000) / 10}%`;
  return el(
    "div",
    { class: "progress-track" },
    el("div", { class: "progress-fill", style: `width: ${percent}` }),
    el("div", { class: "progress-head", style: `left: ${percent}` })
  );
}

export function code(season, episode) {
  return `S${season}·E${episode}`;
}

export function remember(show, value) {
  try {
    localStorage.setItem(`watch:${slugify(show)}`, JSON.stringify(value));
  } catch {}
}

export function recall(show) {
  try {
    return JSON.parse(localStorage.getItem(`watch:${slugify(show)}`));
  } catch {
    return null;
  }
}
