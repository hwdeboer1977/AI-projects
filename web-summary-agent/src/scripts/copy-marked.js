import fs from "fs";
import path from "path";

const candidates = [
  // Newer marked versions commonly provide a UMD build here:
  "node_modules/marked/lib/marked.umd.js",
  "node_modules/marked/lib/marked.umd.min.js",

  // Some versions provide these:
  "node_modules/marked/marked.min.js",
  "node_modules/marked/marked.js",

  // Fallbacks seen in other builds:
  "node_modules/marked/dist/marked.umd.js",
  "node_modules/marked/dist/marked.umd.min.js",
  "node_modules/marked/dist/marked.min.js",
];

const dst = path.resolve("src/extension/marked.min.js");

function firstExisting(paths) {
  for (const p of paths) {
    const abs = path.resolve(p);
    if (fs.existsSync(abs)) return abs;
  }
  return null;
}

const src = firstExisting(candidates);

if (!src) {
  console.error(
    "❌ Could not find a browser build of 'marked' in node_modules."
  );
  console.error("Searched:\n" + candidates.map((p) => " - " + p).join("\n"));
  process.exit(1);
}

fs.mkdirSync(path.dirname(dst), { recursive: true });
fs.copyFileSync(src, dst);

console.log(`✓ Copied marked from: ${src}`);
console.log(`✓ To: ${dst}`);
