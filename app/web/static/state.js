// app/web/static/state.js
//
// The single shared client state. Kept deliberately small: per-connection UI
// state only — the authoritative tutoring state lives in the backend store and
// arrives over the WebSocket (see ws.js).

"use strict";

export const state = {
  words: [],                  // expected token stream (positions index into this)
  targetPositions: [],        // positions of words exercising the target grapheme
  mic: { ctx: null, stream: null, node: null, recording: false },
  illustratedEnabled: false,  // creds-gated take-home book feature
  learnerName: "",            // for the "Generate <name>'s book" label
};

export const OUT_RATE = 16000; // app/voice expects 16-bit/16 kHz mono PCM
