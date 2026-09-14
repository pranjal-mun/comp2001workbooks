// Static server for local testing. Python's http.server is not enough here:
// CheerpJ fetches its runtime and the jars with byte-range requests.
//   node tools/serve.mjs [port] [basePath]      e.g. node tools/serve.mjs 9000
// Then open http://127.0.0.1:9000/ (or /basePath/ to emulate GitHub Pages).
import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("../", import.meta.url)));
const port = Number.parseInt(process.argv[2] || process.env.PORT || "9000", 10);
const basePath = normalizeBasePath(process.argv[3] || "");
const types = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".jar": "application/java-archive",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".txt": "text/plain; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
};

createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url || "/", "http://localhost").pathname);
    if (basePath && pathname !== basePath && !pathname.startsWith(`${basePath}/`)) throw new Error("Outside base path");
    const relativePath = basePath ? pathname.slice(basePath.length) || "/" : pathname;
    const requested = relativePath.endsWith("/") ? `${relativePath}index.html` : relativePath;
    const file = resolve(root, `.${requested}`);
    if (file !== root && !file.startsWith(`${root}${sep}`)) throw new Error("Invalid path");
    const info = await stat(file);
    if (!info.isFile()) throw new Error("Not a file");

    const headers = {
      "Accept-Ranges": "bytes",
      "Cache-Control": "no-store",
      "Content-Type": types[extname(file)] || "application/octet-stream",
    };
    const range = request.headers.range?.match(/^bytes=(\d*)-(\d*)$/);
    if (range) {
      const start = range[1] ? Number.parseInt(range[1], 10) : 0;
      const end = range[2] ? Math.min(Number.parseInt(range[2], 10), info.size - 1) : info.size - 1;
      if (start > end || start >= info.size) {
        response.writeHead(416, { "Content-Range": `bytes */${info.size}` });
        response.end();
        return;
      }
      response.writeHead(206, { ...headers, "Content-Length": end - start + 1, "Content-Range": `bytes ${start}-${end}/${info.size}` });
      createReadStream(file, { start, end }).pipe(response);
      return;
    }

    response.writeHead(200, { ...headers, "Content-Length": info.size });
    createReadStream(file).pipe(response);
  } catch {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
}).listen(port, "127.0.0.1", () => {
  console.log(`Serving ${root} at http://127.0.0.1:${port}${basePath}/`);
});

function normalizeBasePath(value) {
  if (!value || value === "/") return "";
  return `/${value.replace(/^\/+|\/+$/g, "")}`;
}
