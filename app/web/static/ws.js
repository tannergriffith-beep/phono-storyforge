// app/web/static/ws.js
//
// The WebSocket layer + a tiny type-keyed pub/sub. The server speaks one socket
// (see app/web/server.py); every inbound message has a `type`, so components
// subscribe with on("outcome", fn) instead of one big if/else. This is what lets
// the LoopRail and the legacy renderers both react to the same payload without
// knowing about each other.

"use strict";

import { $ } from "./dom.js";

let ws = null;
const handlers = new Map(); // type -> [fn]

/** Register a handler for an inbound message type. Multiple per type allowed. */
export function on(type, fn) {
  if (!handlers.has(type)) handlers.set(type, []);
  handlers.get(type).push(fn);
}

export function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => setStatus("connected", "ok");
  ws.onclose = () => setStatus("disconnected — refresh to reconnect", "err");
  ws.onerror = () => setStatus("connection error", "err");
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    const list = handlers.get(msg.type);
    if (list) list.forEach((fn) => fn(msg));
  };
}

/** Send a JSON action. No-ops if the socket isn't open (never throws mid-demo). */
export function send(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

/** Send a raw binary frame (mic PCM). No-ops if the socket isn't open. */
export function sendBinary(buf) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(buf);
}

export const isOpen = () => !!ws && ws.readyState === WebSocket.OPEN;

export function setStatus(text, cls) {
  const el = $("conn-status");
  if (!el) return;
  el.textContent = text;
  el.className = "status" + (cls ? " " + cls : "");
}
