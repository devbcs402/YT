const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const FFMPEG_PATH = path.join(__dirname, 'node_modules', 'ffmpeg-static', 'ffmpeg.exe');

const SAMPLE_RATE = 44100;
const DURATION = 58.5; // exactly 58.5 seconds
const TOTAL_SAMPLES = Math.floor(SAMPLE_RATE * DURATION);

const left = new Float32Array(TOTAL_SAMPLES);
const right = new Float32Array(TOTAL_SAMPLES);

const BPM = 120; // 120 BPM futuristic electronic tech beat
const BEAT_SEC = 60 / BPM; // 0.5s per beat
const SIXTEENTH = BEAT_SEC / 4; // 0.125s

console.log(`Synthesizing Day 1 Node.js Soundtrack: ${DURATION}s @ ${BPM} BPM stereo 44.1kHz...`);

// Helper audio synthesis functions
function addKick(time, velocity = 0.6) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(0.25 * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const pitchDrop = 110 * Math.exp(-t * 35);
        const freq = 45 + pitchDrop;
        const phase = 2 * Math.PI * freq * t;
        const amp = Math.exp(-t * 10) * velocity;
        const sub = Math.sin(2 * Math.PI * 40 * t) * Math.exp(-t * 6.0) * 0.4;
        const val = (Math.sin(phase) + sub) * amp * 0.8;
        left[startSample + i] += val;
        right[startSample + i] += val;
    }
}

function addSnare(time, velocity = 0.45) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(0.2 * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const noise = (Math.random() - 0.5) * 1.2 * Math.exp(-t * 22);
        const tone = Math.sin(2 * Math.PI * 220 * t) * Math.exp(-t * 25) * 0.3;
        const amp = velocity * Math.exp(-t * 14);
        const val = (noise + tone) * amp;
        left[startSample + i] += val * 0.9;
        right[startSample + i] += val * 1.1;
    }
}

function addHiHat(time, velocity = 0.25, open = false) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const dur = open ? 0.12 : 0.035;
    const durSamples = Math.floor(dur * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const decay = open ? 35 : 95;
        const noise = (Math.random() - 0.5) * 1.0 * Math.exp(-t * decay);
        const metallic = Math.sin(2 * Math.PI * 8500 * t) * 0.2 * Math.exp(-t * decay);
        const val = (noise + metallic) * velocity;
        left[startSample + i] += val * 0.85;
        right[startSample + i] += val * 1.15;
    }
}

function addSynthArp(time, freq, duration = 0.14, velocity = 0.22, pan = 0.5) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(duration * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const env = Math.exp(-t * 18) * velocity;
        const sine = Math.sin(2 * Math.PI * freq * t);
        const sine2 = Math.sin(2 * Math.PI * (freq * 2) * t) * 0.25;
        const val = (sine * 0.75 + sine2) * env;
        left[startSample + i] += val * (1 - pan * 0.5);
        right[startSample + i] += val * (0.5 + pan * 0.5);
    }
}

function addPadChord(time, freqs, duration = 2.5, velocity = 0.25) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(duration * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const env = (1 - Math.exp(-t * 3)) * Math.exp(-t * (1.8 / duration)) * velocity;
        let sumL = 0;
        let sumR = 0;
        freqs.forEach((f, idx) => {
            const pan = idx % 2 === 0 ? 0.7 : 1.3;
            const detune = 1.0 + (idx % 2 === 0 ? 0.003 : -0.003);
            const w1 = Math.sin(2 * Math.PI * f * t);
            const w2 = Math.sin(2 * Math.PI * f * detune * t) * 0.5;
            const shimmer = Math.sin(2 * Math.PI * (f * 2) * t) * 0.15;
            const tone = (w1 + w2 + shimmer);
            sumL += tone * (2 - pan);
            sumR += tone * pan;
        });
        left[startSample + i] += sumL * env * 0.18;
        right[startSample + i] += sumR * env * 0.18;
    }
}

function addSubBass(time, freq, duration = 1.8, velocity = 0.35) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(duration * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const env = Math.min(1.0, t * 20) * Math.exp(-t * (1.5 / duration)) * velocity;
        const val = Math.sin(2 * Math.PI * freq * t) * env;
        left[startSample + i] += val * 0.7;
        right[startSample + i] += val * 0.7;
    }
}

function addWhoosh(time, duration = 0.5, up = true, velocity = 0.45) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(duration * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const p = t / duration;
        const env = Math.sin(p * Math.PI) * velocity;
        const noise = (Math.random() - 0.5) * 1.4;
        const sweepFreq = up ? 200 + p * 3200 : 3200 - p * 3000;
        const tone = Math.sin(2 * Math.PI * sweepFreq * t) * 0.3;
        const val = (noise + tone) * env;
        left[startSample + i] += val * (0.6 + p * 0.6);
        right[startSample + i] += val * (1.2 - p * 0.6);
    }
}

function addDigitalChime(time, freq = 880, duration = 1.2, velocity = 0.4) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(duration * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const env = Math.exp(-t * 5.0) * velocity;
        const h1 = Math.sin(2 * Math.PI * freq * t);
        const h2 = Math.sin(2 * Math.PI * freq * 2.0 * t) * 0.4;
        const h3 = Math.sin(2 * Math.PI * freq * 3.5 * t) * 0.15;
        const val = (h1 + h2 + h3) * env;
        left[startSample + i] += val * 0.8;
        right[startSample + i] += val * 1.1;
    }
}

function addKeyClick(time, velocity = 0.18) {
    const startSample = Math.floor(time * SAMPLE_RATE);
    const durSamples = Math.floor(0.015 * SAMPLE_RATE);
    for (let i = 0; i < durSamples && startSample + i < TOTAL_SAMPLES; i++) {
        const t = i / SAMPLE_RATE;
        const noise = (Math.random() - 0.5) * Math.exp(-t * 350) * velocity;
        left[startSample + i] += noise;
        right[startSample + i] += noise;
    }
}

// -------------------------------------------------------------------
// COMPOSE BACKGROUND MUSIC & SFX ACROSS THE 58.5s TIMELINE
// Progression: Am -> F -> C -> G (Classic uplifting tech progression)
// -------------------------------------------------------------------
const chords = [
    { name: 'Am', root: 55.0, freqs: [220.00, 261.63, 329.63, 440.00] },
    { name: 'F',  root: 43.65, freqs: [174.61, 220.00, 261.63, 349.23] },
    { name: 'C',  root: 65.41, freqs: [130.81, 196.00, 261.63, 329.63] },
    { name: 'G',  root: 48.99, freqs: [196.00, 246.94, 293.66, 392.00] }
];

// Play chords every 4 seconds (8 beats)
for (let t = 0.0; t < DURATION; t += 4.0) {
    const chordIdx = Math.floor(t / 4.0) % chords.length;
    const chord = chords[chordIdx];
    addPadChord(t, chord.freqs, 4.2, 0.22);
    addSubBass(t, chord.root, 3.8, 0.28);
}

// Play light electronic beat (subdued kicks, hi-hats, arps)
for (let t = 0.5; t < DURATION - 1.0; t += BEAT_SEC) {
    const beatIdx = Math.round(t / BEAT_SEC);
    
    // Light kick on beats 1 and 3 (subdued so voice shines)
    if (beatIdx % 2 === 0) {
        addKick(t, 0.45);
    } else {
        addSnare(t, 0.25);
    }
    
    // Subtle hi-hat on offbeats
    addHiHat(t + SIXTEENTH * 2, 0.16, false);
    
    // Melodic futuristic synth arp
    const noteFreq = [440, 523.25, 659.25, 587.33, 523.25, 659.25, 783.99, 659.25][beatIdx % 8];
    addSynthArp(t, noteFreq, 0.12, 0.18, (beatIdx % 2 === 0 ? 0.3 : 0.7));
    addSynthArp(t + SIXTEENTH * 2, noteFreq * 1.5, 0.09, 0.12, 0.5);
}

// -------------------------------------------------------------------
// TIMED SOUND EFFECTS FOR EACH SCENE TRANSITION AND ACTION
// -------------------------------------------------------------------
// Scene 1: Hook (0 - 10.6s)
addWhoosh(0.1, 0.6, true, 0.6); // Fast zoom-in hook
addDigitalChime(1.5, 587.33, 0.8, 0.35); // "JavaScript = Backend?" question popup
addWhoosh(5.4, 0.4, false, 0.4); // Transform to backend server

// Scene 2: Meet Node.js (10.6s - 21.6s)
addWhoosh(10.5, 0.5, true, 0.5); // Scene transition
addDigitalChime(11.2, 880, 1.2, 0.45); // Node.js logo 3D entrance chime
addWhoosh(13.5, 0.5, false, 0.35); // JS code gliding out of browser

// Scene 3: How it works (21.6s - 31.4s)
addWhoosh(21.5, 0.5, true, 0.45); // Architecture diagram transition
addDigitalChime(23.2, 783.99, 0.6, 0.35); // Client request packet pulse
addDigitalChime(25.5, 987.77, 0.6, 0.35); // MongoDB query
addDigitalChime(27.8, 1174.66, 0.8, 0.45); // 200 OK Response returned

// Scene 4: Code Demo (31.4s - 43.5s)
addWhoosh(31.3, 0.45, true, 0.45); // Code editor pop-in
// Code typing clicks (32.0s to 37.0s)
for (let tc = 32.2; tc < 37.2; tc += 0.18) {
    addKeyClick(tc, 0.12 + Math.random() * 0.08);
}
// Terminal execution enter (39.5s)
addKeyClick(39.5, 0.35);
addDigitalChime(40.2, 880, 1.0, 0.4); // Server running on port 3000 chime
addDigitalChime(41.8, 1318.5, 1.4, 0.5); // Browser response Hello from Node.js!

// Scene 5: Outro & Call To Action (43.5s - 58.5s)
addWhoosh(43.4, 0.6, true, 0.6); // Outro transition whoosh
addKick(43.5, 0.7); // Impact hit on Day 1 Challenge title
addDigitalChime(44.2, 659.25, 1.5, 0.45); // Day 01/100 fanfare
addDigitalChime(50.8, 880.00, 1.2, 0.45); // Follow button pop
addWhoosh(56.5, 0.8, false, 0.4); // Final fade whoosh

// Fade out gracefully to silence in last 1.5s
for (let i = Math.floor(57.0 * SAMPLE_RATE); i < TOTAL_SAMPLES; i++) {
    const t = (i - 57.0 * SAMPLE_RATE) / (1.5 * SAMPLE_RATE);
    const fade = Math.cos(t * Math.PI * 0.5);
    left[i] *= fade;
    right[i] *= fade;
}

// Limiter & Master Normalize BGM
let peak = 0;
for (let i = 0; i < TOTAL_SAMPLES; i++) {
    if (Math.abs(left[i]) > peak) peak = Math.abs(left[i]);
    if (Math.abs(right[i]) > peak) peak = Math.abs(right[i]);
}
const bgmGain = peak > 0.85 ? 0.85 / peak : 1.0;
for (let i = 0; i < TOTAL_SAMPLES; i++) {
    left[i] = Math.tanh(left[i] * bgmGain);
    right[i] = Math.tanh(right[i] * bgmGain);
}

// Write BGM WAV buffer
const numChannels = 2;
const bitsPerSample = 16;
const bytesPerSample = bitsPerSample / 8;
const blockAlign = numChannels * bytesPerSample;
const dataByteLength = TOTAL_SAMPLES * blockAlign;
const headerByteLength = 44;
const wavBuffer = Buffer.alloc(headerByteLength + dataByteLength);

wavBuffer.write('RIFF', 0);
wavBuffer.writeUInt32LE(36 + dataByteLength, 4);
wavBuffer.write('WAVE', 8);
wavBuffer.write('fmt ', 12);
wavBuffer.writeUInt32LE(16, 16);
wavBuffer.writeUInt16LE(1, 20); // PCM
wavBuffer.writeUInt16LE(2, 22); // Stereo
wavBuffer.writeUInt32LE(SAMPLE_RATE, 24);
wavBuffer.writeUInt32LE(SAMPLE_RATE * blockAlign, 28);
wavBuffer.writeUInt16LE(blockAlign, 32);
wavBuffer.writeUInt16LE(16, 34);
wavBuffer.write('data', 36);
wavBuffer.writeUInt32LE(dataByteLength, 40);

let offset = 44;
for (let i = 0; i < TOTAL_SAMPLES; i++) {
    const sL = Math.max(-1, Math.min(1, left[i]));
    const sR = Math.max(-1, Math.min(1, right[i]));
    const intL = sL < 0 ? Math.floor(sL * 32768) : Math.min(32767, Math.floor(sL * 32767));
    const intR = sR < 0 ? Math.floor(sR * 32768) : Math.min(32767, Math.floor(sR * 32767));
    wavBuffer.writeInt16LE(intL, offset);
    wavBuffer.writeInt16LE(intR, offset + 2);
    offset += 4;
}

const bgmPath = path.join(__dirname, 'assets', 'bgm_sfx.wav');
fs.writeFileSync(bgmPath, wavBuffer);
console.log(`✅ Synthesized BGM & SFX: ${bgmPath}`);

// -------------------------------------------------------------------
// MIX BGM + 5 VOICE CLIPS USING FFMPEG
// Scene voice delays:
// Scene 1: 0.4s (400ms)
// Scene 2: 10.6s (10600ms)
// Scene 3: 21.6s (21600ms)
// Scene 4: 31.4s (31400ms)
// Scene 5: 43.5s (43500ms)
// -------------------------------------------------------------------
const v1 = path.join(__dirname, 'assets', 'voice', 'scene1_hook', 'audio.mp3');
const v2 = path.join(__dirname, 'assets', 'voice', 'scene2_intro', 'audio.mp3');
const v3 = path.join(__dirname, 'assets', 'voice', 'scene3_how_it_works', 'audio.mp3');
const v4 = path.join(__dirname, 'assets', 'voice', 'scene4_code_demo', 'audio.mp3');
const v5 = path.join(__dirname, 'assets', 'voice', 'scene5_outro', 'audio.mp3');
const masterOut = path.join(__dirname, 'assets', 'master_audio.wav');

console.log('Mixing Voice-Over narration with BGM and SFX using FFmpeg...');

// Delays in ms:
// Voice clips leveled with high clarity, BGM sidechained/ducked underneath
const filterComplex = [
    `[0:a]volume=0.35[bgm]`,
    `[1:a]adelay=400|400,volume=1.35[v1]`,
    `[2:a]adelay=10600|10600,volume=1.35[v2]`,
    `[3:a]adelay=21600|21600,volume=1.35[v3]`,
    `[4:a]adelay=31400|31400,volume=1.35[v4]`,
    `[5:a]adelay=43500|43500,volume=1.35[v5]`,
    `[bgm][v1][v2][v3][v4][v5]amix=inputs=6:duration=first:dropout_transition=2[mixed]`,
    `[mixed]alimiter=limit=0.95[out]`
].join(';');

const ffmpegArgs = [
    '-y',
    '-i', bgmPath,
    '-i', v1,
    '-i', v2,
    '-i', v3,
    '-i', v4,
    '-i', v5,
    '-filter_complex', filterComplex,
    '-map', '[out]',
    '-ac', '2',
    '-ar', '44100',
    '-t', String(DURATION),
    masterOut
];

const res = spawnSync(FFMPEG_PATH, ffmpegArgs, { stdio: 'inherit' });
if (res.status === 0) {
    console.log(`🎉 Master Audio Track Created Successfully: ${masterOut}`);
} else {
    console.error('Error mixing audio in FFmpeg, exit code:', res.status);
    process.exit(1);
}
