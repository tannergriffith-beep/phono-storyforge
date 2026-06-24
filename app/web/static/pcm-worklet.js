// app/web/static/pcm-worklet.js
//
// FLAGSHIP STAGE C (step 2): mic-capture AudioWorklet.
//
// Forwards the raw Float32 mono samples of each render quantum to the main
// thread, which downsamples to 16 kHz / 16-bit PCM and ships them over the
// WebSocket. The output is left silent (we never write to it) so the child's
// voice is NOT echoed back to the speakers.

class PCMCapture extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input[0]) {
      // Copy out of the shared buffer before it is recycled.
      this.port.postMessage(input[0].slice(0));
    }
    return true; // keep the processor alive for the whole read
  }
}

registerProcessor("pcm-capture", PCMCapture);
