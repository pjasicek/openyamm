"use strict";

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const faces = ["fondamento", "almendra", "endgame"];
const query = new URLSearchParams(location.search);
let face = faces.includes(query.get("font")) ? query.get("font") : "fondamento";
const states = [
  ["normal", "Normal", "Pale gold · raised edge"],
  ["hover", "Hover", "Warm light on the letters"],
  ["pressed", "Held down", "1px lower · inset bevel"],
  ["selected", "Selected tab", "Persistent inset gold rim"],
  ["disabled", "Unavailable", "Muted ink · no response"],
  ["focus", "Keyboard focus", "A fine outer edge"],
];

function updateReference() {
  const source = $("#original-label");
  const name = source.selectedOptions[0].textContent;
  $("#original-states").innerHTML = ["u", "h", "d"].map((state, index) => `<figure>
    <figcaption>${["Normal / U", "Highlight / H", "Pressed / D"][index]}</figcaption>
    <img src="assets/legacy-buttons/but${source.value}${state}.png" alt="Original ${name} button, ${state}"
      width="150" height="52"></figure>`).join("");
  $("#current-states").innerHTML = ["Normal", "Hover", "Held down"].map((state, index) => `<figure>
    <figcaption>${state}</figcaption><div class="current-button ${index ? "is-hover" : ""}">${name}</div></figure>`).join("");
}
$("#original-label").addEventListener("change", updateReference);
updateReference();
$("#live-tabs").innerHTML = ["Stats", "Skills", "Inventory", "Awards", "Exit"].map(name => `<button
  class="obs-button" data-tab="${name}" ${name === "Exit" ? "" : `aria-pressed="${name === "Inventory"}"`}>
  <span class="obs-label">${name}</span></button>`).join("");
$("#state-board").innerHTML = states.map(([state, name, note]) => `<figure><figcaption>${name}</figcaption>
  <button class="obs-button" tabindex="-1" data-demo-state="${state}" ${state === "disabled" ? "disabled" : ""}>
    <span class="obs-label">Inventory</span></button><small>${note}</small></figure>`).join("");

function updateContext() {
  const params = new URLSearchParams({ screen: $("#context-screen").value, treatment: "carved", export: "1" });
  if (!$("#current-toggle").checked) params.set("buttons", face);
  $("#context-frame").src = `index.html?${params}`;
}

function updateFont() {
  $("#specimen").className = `button-theme font-${face}`;
  $$("[data-face]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.face === face)));
  const params = new URLSearchParams(location.search);
  params.set("font", face);
  history.replaceState(null, "", `${location.pathname}?${params}`);
  updateContext();
}

$$("[data-face]").forEach(button => button.addEventListener("click", () => { face = button.dataset.face; updateFont(); }));
$$("[data-tab]").forEach(button => button.addEventListener("click", () => {
  if (button.dataset.tab === "Exit") {
    $("#feedback").textContent = "Exit is a momentary action; it does not stay selected.";
    return;
  }
  $$("[data-tab][aria-pressed]").forEach(other => other.setAttribute("aria-pressed", String(other === button)));
  $("#feedback").textContent = `${button.dataset.tab} selected. The rim stays after the pointer leaves.`;
}));
$("#label-input").addEventListener("input", event => {
  $("#label-example .obs-label").textContent = event.target.value || "Button";
});
$("#label-example").addEventListener("click", () => {
  $("#feedback").textContent = `“${$("#label-example").textContent}” uses the same font and state treatment.`;
});
$("#topic-example").addEventListener("click", () => {
  $("#feedback").textContent = "Learn Skills uses the same lettering and input response on an open dialogue row.";
});
$("#context-screen").addEventListener("change", updateContext);
$("#current-toggle").addEventListener("change", updateContext);
$("#context-fullscreen").addEventListener("click", () => $("#context-frame").requestFullscreen());
updateFont();
