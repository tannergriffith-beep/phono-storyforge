// app/web/static/book.js
//
// Illustrated take-home book (opt-in, creds-gated coda). Off the critical path:
// the reading loop is unaffected whether or not this feature is enabled.

"use strict";

import { $ } from "./dom.js";
import * as ws from "./ws.js";

export function generateBook() {
  const btn = $("gen-book-btn");
  btn.disabled = true;
  $("book-result").hidden = true;
  bookProgress("Starting…");
  ws.send({ action: "generate_book" });
}

export function bookProgress(text) {
  const e = $("book-progress");
  if (e) e.textContent = text || "";
}

export function endBookGen() {
  const btn = $("gen-book-btn");
  if (btn) btn.disabled = false;
}

export function renderBookReady(msg) {
  endBookGen();
  bookProgress("Done — the illustrated book is ready.");

  // Doc link — present unless the export degraded to pages-only.
  const link = $("book-link");
  if (msg.shareable_url) {
    link.href = msg.shareable_url;
    link.textContent = msg.title ? `Open “${msg.title}” ↗` : "Open the Google Doc ↗";
    link.hidden = false;
  } else {
    link.hidden = true;
  }

  $("book-decodable").textContent = msg.decodable ? "decodable ✓" : "decodability unverified";

  // A short note when something degraded, so the result is never misleading.
  const notes = {
    illustrated_pages_only:
      "Pages illustrated, but the Google Docs export was unavailable — showing the pages here.",
    text_only: "Illustrations were unavailable, so this is a text-only book.",
    text_only_pages_only:
      "Illustrations and the Docs export were unavailable — showing the page text only.",
  };
  $("book-note").textContent = notes[msg.source] || "";

  // Pages with inline thumbnails when illustrated.
  const pagesEl = $("book-pages");
  pagesEl.innerHTML = "";
  (msg.pages || []).forEach((p, i) => {
    const div = document.createElement("div");
    div.className = "book-page";
    if (p.image_ref) {
      const img = document.createElement("img");
      img.className = "book-thumb";
      img.src = p.image_ref;
      img.alt = `page ${i + 1} illustration`;
      div.appendChild(img);
    }
    const num = document.createElement("span");
    num.className = "book-page-n";
    num.textContent = i + 1;
    const txt = document.createElement("span");
    txt.className = "book-page-t";
    txt.textContent = p.text;
    div.appendChild(num);
    div.appendChild(txt);
    pagesEl.appendChild(div);
  });
  $("book-result").hidden = false;
}
