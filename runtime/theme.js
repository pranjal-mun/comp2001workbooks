// Light / dark theme: dark until the student picks one with the toggle, then
// the choice is remembered for every page on the site.

const KEY = "comp2001-workbooks:theme";
const DEFAULT = "dark";

export function initTheme() {
  apply(saved() ?? DEFAULT);
  document.addEventListener("wb:toggle-theme", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });
}

export function currentTheme() {
  return document.documentElement.dataset.theme;
}

export function setTheme(theme) {
  try { localStorage.setItem(KEY, theme); } catch { /* ignore */ }
  apply(theme);
  document.dispatchEvent(new CustomEvent("wb:theme-changed", { detail: theme }));
}

function saved() {
  try { return localStorage.getItem(KEY); } catch { return null; }
}

function apply(theme) {
  document.documentElement.dataset.theme = theme;
}
