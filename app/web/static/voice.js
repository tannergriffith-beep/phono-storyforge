// app/web/static/voice.js
//
// Step-2 browser mic -> WebSocket -> app/voice Transcriber.
//
// Additive enhancement: stream 16 kHz/16-bit PCM frames over the same socket
// between read_start/read_end. The server feeds them to the injectable
// LiveTranscriber audio_source. If anything fails (no mic, no Live quota), the
// typed presets still work — voice is never load-bearing.

"use strict";

import { $ } from "./dom.js";
import { state, OUT_RATE } from "./state.js";
import * as ws from "./ws.js";

export function voiceStatus(text) {
  const e = $("voice-status");
  if (e) e.textContent = text || "";
}

export async function toggleMic() {
  if (state.mic.recording) { stopMic(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    await ctx.audioWorklet.addModule("/static/pcm-worklet.js");
    const src = ctx.createMediaStreamSource(stream);
    const node = new AudioWorkletNode(ctx, "pcm-capture");
    const inRate = ctx.sampleRate;
    node.port.onmessage = (e) => {
      const pcm16 = downsampleTo16k(e.data, inRate);
      if (pcm16.length) ws.sendBinary(pcm16.buffer);
    };
    src.connect(node);
    node.connect(ctx.destination); // pulls the graph; worklet output is silent (no echo)
    state.mic = { ctx, stream, node, recording: true };
    ws.send({ action: "read_start" });
    setMicUI(true);
    voiceStatus("Listening… tap Stop when they finish the page.");
  } catch (err) {
    voiceStatus("mic unavailable: " + err.message + " — use the typed presets instead");
  }
}

export function stopMic() {
  ws.send({ action: "read_end" });
  const m = state.mic;
  if (m.node) m.node.disconnect();
  if (m.stream) m.stream.getTracks().forEach((t) => t.stop());
  if (m.ctx) m.ctx.close();
  state.mic = { ctx: null, stream: null, node: null, recording: false };
  setMicUI(false);
  voiceStatus("transcribing…");
}

// Nearest-sample downsample from the mic's native rate to 16 kHz, then to Int16.
function downsampleTo16k(f32, inRate) {
  const ratio = inRate / OUT_RATE;
  const outLen = Math.floor(f32.length / ratio);
  const out = new Int16Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const s = Math.max(-1, Math.min(1, f32[Math.floor(i * ratio)]));
    out[i] = s * 0x7fff;
  }
  return out;
}

function setMicUI(recording) {
  const btn = $("mic-btn");
  if (!btn) return;
  // Keep the line icon across states (PR11); only the label changes.
  const icon = '<svg class="icon" aria-hidden="true"><use href="#i-mic"/></svg> ';
  btn.innerHTML = icon + (recording ? "Stop" : "Read aloud");
  btn.classList.toggle("recording", recording);
  btn.setAttribute("aria-pressed", recording ? "true" : "false");
}
