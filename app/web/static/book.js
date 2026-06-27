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
  bookProgress("Making the book…");
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
  bookProgress("The book is ready!");

  // Doc link — present unless the export degraded to pages-only.
  const link = $("book-link");
  if (msg.shareable_url) {
    link.href = msg.shareable_url;
    link.textContent = msg.title ? `Open “${msg.title}” ↗` : "Open the book ↗";
    link.hidden = false;
  } else {
    link.hidden = true;
  }

  // Quiet reassurance, never a clinical "unverified" badge.
  $("book-decodable").textContent = msg.decodable ? "made from sounds they know ✓" : "";

  // Calm notes when something degraded — the book is still a gift, never broken.
  const notes = {
    illustrated_pages_only:
      "The pictures are ready — the shareable link wasn't available tonight, so here are the pages.",
    text_only: "We couldn't add pictures tonight, so this is a word-only book — still made just for them.",
    text_only_pages_only:
      "Just the words tonight — pictures and the link weren't available, but the story is all theirs.",
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
      // Decorative: the page text is shown adjacent, so the illustration is
      // marked decorative for screen readers (design-system §17).
      img.alt = "";
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
