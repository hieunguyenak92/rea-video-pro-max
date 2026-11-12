"use strict";

// The page presents recorded files only. Missing records never become demo data.
const $ = (id) => document.getElementById(id);
const videoA = $("reference");
const videoB = $("adapted");
const sources = {
  analysis: {path: "evidence/reference-analysis.json", label: "Reference analysis"},
  template: {path: "evidence/style-template.json", label: "Reusable style template"},
  project: {path: "evidence/project.json", label: "New-content project"},
  verification: {path: "evidence/verification.json", label: "Verification record"}
};
const records = {};
const issues = [];
let selectedButton = null;
let updating = false;

function duration(player) {
  return Number.isFinite(player.duration) && player.duration > 0 ? player.duration : 0;
}

function setProgress(fraction, seekA = true) {
  fraction = Math.min(1, Math.max(0, Number(fraction) || 0));
  if (seekA && duration(videoA)) videoA.currentTime = fraction * duration(videoA);
  if ($("linked").checked && duration(videoB)) {
    const wanted = fraction * duration(videoB);
    if (Math.abs(videoB.currentTime - wanted) > (seekA ? 0.01 : 0.2)) videoB.currentTime = wanted;
  }
  $("scrub").value = String(Math.round(fraction * 1000));
  $("scrub").setAttribute("aria-valuetext", `${Math.round(fraction * 100)} percent`);
  $("time").value = `${Math.round(fraction * 100)}%`;
}

$("scrub").addEventListener("input", (event) => setProgress(Number(event.target.value) / 1000));
videoA.addEventListener("timeupdate", () => {
  if (!updating && duration(videoA)) setProgress(videoA.currentTime / duration(videoA), false);
});
videoA.addEventListener("play", () => {
  $("play").replaceChildren(document.createTextNode("Ⅱ  Pause"));
  $("play").setAttribute("aria-label", "Pause reference and linked new video");
  if ($("linked").checked && duration(videoA) && duration(videoB)) {
    const rate = duration(videoB) / duration(videoA);
    videoB.playbackRate = Math.max(0.25, Math.min(4, rate));
    videoB.muted = true; // A's native audio remains available; B can be heard independently.
    videoB.play().catch(() => { $("media-status").textContent = "Linked playback was blocked by the browser. Use each player's native controls."; });
  }
});
videoA.addEventListener("pause", () => {
  $("play").replaceChildren(document.createTextNode("▶  Play"));
  $("play").setAttribute("aria-label", "Play reference and linked new video");
  if ($("linked").checked) videoB.pause();
});
videoA.addEventListener("ended", () => { if ($("linked").checked) videoB.pause(); });
$("play").addEventListener("click", async () => {
  if (!videoA.paused) { videoA.pause(); return; }
  if (videoA.ended) setProgress(0);
  try { await videoA.play(); }
  catch { $("media-status").textContent = "Reference playback is unavailable. Check the media file or use the MP4 link."; }
});
$("linked").addEventListener("change", () => {
  videoB.pause();
  videoB.playbackRate = 1;
  videoB.muted = false;
  if ($("linked").checked && duration(videoA)) setProgress(videoA.currentTime / duration(videoA), false);
});
for (const [player, label] of [[videoA, "Reference A"], [videoB, "New video B"]]) {
  player.addEventListener("error", () => { $("media-status").textContent = `${label} is unavailable or unsupported by this browser. See the MP4 link and validation record.`; });
}

function inspect(value, title, caption, path, button = null) {
  if (selectedButton) selectedButton.setAttribute("aria-pressed", "false");
  selectedButton = button;
  if (button) button.setAttribute("aria-pressed", "true");
  $("detail-title").textContent = title;
  $("detail-caption").textContent = caption;
  $("detail").textContent = JSON.stringify(value, null, 2);
  $("record-link").href = path;
}

function addLane(label, items, total, css, sourceKey, videoSide) {
  const row = document.createElement("div"); row.className = "lane-row";
  const name = document.createElement("span"); name.className = "lane-label"; name.textContent = label;
  const lane = document.createElement("div"); lane.className = "lane";
  lane.setAttribute("role", "group"); lane.setAttribute("aria-label", label);
  const valid = Array.isArray(items) ? items.filter((item) => Number.isFinite(item.start) && Number.isFinite(item.end) && item.end > item.start) : [];
  if (!valid.length || !total) {
    const empty = document.createElement("span"); empty.className = "empty-lane"; empty.textContent = "No recorded events"; lane.append(empty);
  }
  for (const item of valid) {
    const start = Math.max(0, Math.min(1, item.start / total));
    const end = Math.max(start, Math.min(1, item.end / total));
    const button = document.createElement("button"); button.type = "button"; button.className = `clip ${css}`;
    button.style.left = `${start * 100}%`; button.style.width = `${Math.max(0.4, (end - start) * 100)}%`;
    const text = item.text || item.id || "Event";
    button.textContent = text;
    button.title = `${text} · ${item.start.toFixed(3)}–${item.end.toFixed(3)} s`;
    button.setAttribute("aria-label", `${label}: ${button.title}`);
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      inspect(item, item.id || label, `${videoSide} · ${item.start.toFixed(3)}–${item.end.toFixed(3)} seconds. Preserve the method/status fields when interpreting this event.`, sources[sourceKey].path, button);
      videoA.pause(); videoB.pause();
      updating = true;
      if ($("linked").checked || videoSide === "Reference A") setProgress(start);
      else if (duration(videoB)) videoB.currentTime = start * duration(videoB);
      updating = false;
    });
    lane.append(button);
  }
  row.append(name, lane); $("timeline").append(row);
}

function verificationSummary(value) {
  if (value.passed === true || value.ok === true || value.status === "passed") return "Passed";
  if (value.passed === false || value.ok === false || value.status === "failed") return "Needs review";
  // Schemas may evolve. Show a record, not an invented success state.
  return typeof value.status === "string" ? value.status.replaceAll("_", " ") : "Recorded";
}

async function loadRecord(key, source) {
  try {
    const response = await fetch(source.path, {cache: "no-cache"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const value = await response.json();
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("expected a JSON object");
    records[key] = value;
  } catch (error) {
    issues.push(`${source.label}: unavailable (${error.message})`);
  }
}

async function initialize() {
  await Promise.all(Object.entries(sources).map(([key, source]) => loadRecord(key, source)));
  $("timeline").replaceChildren();
  if (records.analysis) {
    const analysis = records.analysis;
    $("shot-count").textContent = String(Array.isArray(analysis.shots) ? analysis.shots.length : 0);
    const captions = Array.isArray(analysis.captions) ? analysis.captions : [];
    const regions = Array.isArray(analysis.text_regions) ? analysis.text_regions : captions;
    const suspect = regions.filter((item) => !captions.some((caption) => caption.id === item.id));
    $("caption-count").textContent = String(captions.length);
    const total = Number(analysis.source?.duration) || 0;
    addLane("A / SHOTS", analysis.shots, total, "", "analysis", "Reference A");
    addLane("A / CAPTIONS", captions, total, "caption-clip", "analysis", "Reference A");
    if (suspect.length) addLane("A / SUSPECT TEXT", suspect, total, "suspect-clip", "analysis", "Reference A");
    inspect({source: analysis.source, coverage: analysis.coverage, unknowns: analysis.unknowns}, "Coverage and unknowns", "Reference facts and unresolved properties, from the recorded analysis. Select an event to see its evidence and method.", sources.analysis.path);
  }
  if (records.project) {
    const project = records.project;
    const total = Number(project.render?.duration) || 0;
    $("b-duration").textContent = total ? `${total.toFixed(2)}s` : "Unknown";
    addLane("B / SCENES", project.scenes, total, "b-clip", "project", "New video B");
    addLane("B / TEXT", project.captions, total, "caption-clip", "project", "New video B");
  }
  if (records.verification) {
    $("verification-status").textContent = verificationSummary(records.verification);
    $("verification-subtitle").textContent = "bounded checks · open full record";
  }
  if (!records.analysis && !records.project) {
    const message = document.createElement("p"); message.className = "loading"; message.textContent = "Recorded timeline unavailable. Open the JSON links to inspect the files directly."; $("timeline").append(message);
    $("detail").textContent = "No recorded artifact was loaded. No analysis has been substituted.";
  }
  for (const button of document.querySelectorAll("[data-artifact]")) {
    const key = button.dataset.artifact;
    button.disabled = !records[key];
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => inspect(records[key], sources[key].label, "Recorded local output. Consult method, provenance, coverage, implementation choices and individual checks before treating a property as established.", sources[key].path, button));
  }
  $("data-status").textContent = issues.length ? `${issues.join(" · ")}. If opened as a file, serve the repository with python -m http.server and open /docs/.` : "All four recorded artifacts loaded. Nothing on this page runs live inference.";
}

initialize().catch((error) => { $("data-status").textContent = `Recorded inspector unavailable: ${error.message}. The artifact links remain usable.`; });
