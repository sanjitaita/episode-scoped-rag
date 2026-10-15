async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    if (typeof data.detail === "string") {
      message = data.detail;
    }
    throw new Error(message);
  }
  return data;
}
export async function getShows() {
  const data = await request("/api/shows");
  return data.shows;
}

export async function getSeasons(show) {
  const data = await request(`/api/shows/${encodeURIComponent(show)}/seasons`);
  return data.seasons;
}

export async function askQuestion(show, season, episode, question, mode) {
  return request("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ show, season, episode, question, mode }),
  });
}