// Reading settings under the ⚙ button: theme, text size, text width and smooth scrolling.

import { currentTheme, setTheme } from "./theme.js";
// Remembered for every page on the site, like the theme.

const KEY = "comp2001-workbooks:settings";
export const SIZES = [
  { label: "Small", scale: 0.9 },
  { label: "Normal", scale: 1 },
  { label: "Large", scale: 1.125 },
  { label: "Larger", scale: 1.25 },
];
export const WIDTHS = [
  { label: "Narrow", value: "narrow", max: "52rem" },
  { label: "Medium", value: "medium", max: "68rem" },
  { label: "Full", value: "full", max: "none" },
];

function load() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY) ?? "{}") ?? {}; } catch { /* ignore */ }
  const width = WIDTHS.some((w) => w.value === saved.width) ? saved.width : "full";
  return { scale: typeof saved.scale === "number" ? saved.scale : 1, width, smooth: saved.smooth === true };
}

let settings = load();

function apply() {
  const root = document.documentElement;
  root.style.fontSize = settings.scale === 1 ? "" : `${settings.scale * 100}%`;
  root.classList.toggle("wb-smooth", settings.smooth);
  root.style.setProperty("--wb-main-width", WIDTHS.find((w) => w.value === settings.width).max);
}

function save(change) {
  settings = { ...settings, ...change };
  try { localStorage.setItem(KEY, JSON.stringify(settings)); } catch { /* ignore */ }
  apply();
}

export function initSettings() { apply(); }

/** "smooth" or "auto", for scrollIntoView calls. */
export function scrollBehavior() { return settings.smooth ? "smooth" : "auto"; }

function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  node.append(...children);
  return node;
}

export function settingsMenu() {
  const sizeButtons = SIZES.map(({ label, scale }) => {
    const b = h("button", { type: "button", class: "wb-seg", onclick: () => { save({ scale }); refresh(); } }, label);
    b.dataset.scale = String(scale);
    return b;
  });
  const widthButtons = WIDTHS.map(({ label, value }) => {
    const b = h("button", { type: "button", class: "wb-seg", onclick: () => { save({ width: value }); refresh(); } }, label);
    b.dataset.width = value;
    return b;
  });
  const themeButtons = [["Light", "light"], ["Dark", "dark"]].map(([label, value]) => {
    const b = h("button", { type: "button", class: "wb-seg", onclick: () => { setTheme(value); refresh(); } }, label);
    b.dataset.theme = value;
    return b;
  });
  const smooth = h("input", { type: "checkbox", id: "wb-set-smooth", onchange: () => save({ smooth: smooth.checked }) });
  const refresh = () => {
    for (const b of sizeButtons) b.setAttribute("aria-pressed", String(Number(b.dataset.scale) === settings.scale));
    for (const b of themeButtons) b.setAttribute("aria-pressed", String(b.dataset.theme === currentTheme()));
    for (const b of widthButtons) b.setAttribute("aria-pressed", String(b.dataset.width === settings.width));
    smooth.checked = settings.smooth;
  };
  refresh();
  const menu = h("details", { class: "wb-menu wb-settings" },
    h("summary", { class: "wb-btn wb-btn-quiet wb-settings-button", title: "Settings: theme, text size, width, scrolling", "aria-label": "Settings" }, "⚙"),
    h("div", { class: "wb-menu-items wb-settings-panel" },
      h("div", { class: "wb-settings-label" }, "Theme"),
      h("div", { class: "wb-segs", role: "group", "aria-label": "Theme" }, ...themeButtons),
      h("div", { class: "wb-settings-label" }, "Text size"),
      h("div", { class: "wb-segs", role: "group", "aria-label": "Text size" }, ...sizeButtons),
      h("div", { class: "wb-settings-label" }, "Text width"),
      h("div", { class: "wb-segs", role: "group", "aria-label": "Text width" }, ...widthButtons),
      h("label", { class: "wb-settings-check", for: "wb-set-smooth" }, smooth, "Smooth scrolling to a section"),
    ));
  document.addEventListener("click", (e) => { if (!menu.contains(e.target)) menu.open = false; });
  document.addEventListener("wb:theme-changed", refresh);
  return menu;
}
