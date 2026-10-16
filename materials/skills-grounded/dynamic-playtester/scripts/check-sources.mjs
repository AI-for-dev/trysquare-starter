// check-sources.mjs <session dir> <catalogue>: removes from the catalogue every entry whose
// source is not a page the collection returned.
//
// The pages are the `Source:` lines of the `codemode` results in the session of catalogue.sh,
// where the collection script prints one per page it kept. An entry the model wrote from memory
// cites a URL that is not among them, even when that URL exists.
//
// Exits 1, and removes the file, when no entry is left: the skill then stops instead of
// writing tests from an empty or invented catalogue.

import { existsSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const [sessionDir, catalogue] = process.argv.slice(2);
if (!sessionDir || !catalogue) {
  console.error("usage: check-sources.mjs <session dir> <catalogue>");
  process.exit(2);
}

// A URL as the two sides write it: no angle brackets, no trailing punctuation or slash.
const normalized = (url) => url.replace(/^</, "").replace(/[>.,;/]+$/, "");

function fetchedPages(dir) {
  const pages = new Set();
  const files = existsSync(dir) ? readdirSync(dir, { recursive: true }) : [];
  for (const file of files.filter((f) => String(f).endsWith(".jsonl"))) {
    for (const line of readFileSync(join(dir, String(file)), "utf8").split("\n")) {
      let entry;
      try {
        entry = JSON.parse(line);
      } catch {
        continue;
      }
      const message = entry.message ?? {};
      if (message.role !== "toolResult" || message.toolName !== "codemode") continue;
      for (const part of message.content ?? []) {
        for (const found of String(part.text ?? "").matchAll(/^Source: (\S+)/gm)) {
          pages.add(normalized(found[1]));
        }
      }
    }
  }
  return pages;
}

const pages = fetchedPages(sessionDir);
if (!existsSync(catalogue)) {
  console.log(`no catalogue written; the search returned ${pages.size} pages`);
  process.exit(1);
}

// Each entry runs from its `#### ` heading to the next heading of any level.
const kept = [];
const removed = [];
let entry = null;
const flush = () => {
  if (!entry) return;
  const source = entry.lines.map((l) => l.match(/^- Source:\s*(\S+)/)).find(Boolean);
  (source && pages.has(normalized(source[1])) ? kept : removed).push(entry);
  entry = null;
};
const out = [];
for (const line of readFileSync(catalogue, "utf8").split("\n")) {
  if (/^#{1,4} /.test(line)) flush();
  if (/^#### /.test(line)) {
    entry = { name: line.slice(5).trim(), lines: [line] };
    out.push(entry);
  } else if (entry) {
    entry.lines.push(line);
  } else {
    out.push(line);
  }
}
flush();

if (removed.length) {
  console.log(`removed, no fetched page behind them: ${removed.map((e) => e.name).join("; ")}`);
}
if (!kept.length) {
  rmSync(catalogue);
  console.log(`no entry backed by a fetched page (${pages.size} pages): the catalogue was not kept`);
  process.exit(1);
}
const dropped = new Set(removed);
const text = out
  .filter((part) => !dropped.has(part))
  .flatMap((part) => (typeof part === "string" ? [part] : part.lines))
  .join("\n");
writeFileSync(catalogue, text);
console.log(`${kept.length} entries in the catalogue, from ${pages.size} pages`);
