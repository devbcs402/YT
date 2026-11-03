const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');

const FFMPEG_PATH = path.join(__dirname, 'node_modules', 'ffmpeg-static', 'ffmpeg.exe');
const AUDIO_PATH = path.join(__dirname, 'assets', 'master_audio.wav');
const OUTPUT_MP4 = path.join(__dirname, 'day1_what_is_nodejs_reel.mp4');

const FPS = 30;
const DURATION = 58.5; // exactly 58.5 seconds (in the 45-60s target range)
const TOTAL_FRAMES = Math.floor(DURATION * FPS); // 1755 frames
const WIDTH = 1080;
const HEIGHT = 1920;

console.log(`=======================================================`);
console.log(`🎬 100 DAYS OF BACKEND DEVELOPMENT — DAY 1: WHAT IS NODE.JS?`);
console.log(`   Format:     1080x1920 (9:16 Vertical Instagram Reel / YouTube Short)`);
console.log(`   Duration:   ${DURATION}s (${TOTAL_FRAMES} frames @ ${FPS} fps)`);
console.log(`   Voice:      Hindi/Hinglish (hi-IN-MadhurNeural, Clear Indian Tech Voice)`);
console.log(`   Subtitles:  Synchronized English Subtitles with active keyphrase highlight`);
console.log(`   Soundtrack: Light Futuristic Electronic Synth + SFX + Ducked Audio`);
console.log(`   Audio File: ${AUDIO_PATH}`);
console.log(`   Output MP4: ${OUTPUT_MP4}`);
console.log(`=======================================================\n`);

// Spawning FFmpeg child process reading MJPEG from stdin
const ffmpegArgs = [
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'mjpeg',
    '-r', String(FPS),
    '-i', '-',
    '-i', AUDIO_PATH,
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '256k',
    '-shortest',
    OUTPUT_MP4
];

console.log('Spawning FFmpeg encoder process...');
const ffmpeg = spawn(FFMPEG_PATH, ffmpegArgs, { stdio: ['pipe', 'inherit', 'inherit'] });

ffmpeg.on('error', (err) => {
    console.error('FFmpeg process error:', err);
});

let framesPiped = 0;
let renderStartTime = Date.now();

// Static file HTTP server
const server = http.createServer((req, res) => {
    let reqUrl = req.url.split('?')[0];
    if (reqUrl === '/nodejs_reel_engine.js') {
        res.writeHead(200, { 'Content-Type': 'application/javascript; charset=utf-8' });
        res.end(fs.readFileSync(path.join(__dirname, 'nodejs_reel_engine.js'), 'utf8'));
        return;
    }

    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(`
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@600;700;800;900&display=swap" rel="stylesheet">
        <style>
            body { margin: 0; background: #000; overflow: hidden; }
            #c { width: ${WIDTH}px; height: ${HEIGHT}px; }
        </style>
    </head>
    <body>
    <canvas id="c" width="${WIDTH}" height="${HEIGHT}"></canvas>
    <script src="nodejs_reel_engine.js"></script>
    <script>
        (async () => {
            const canvas = document.getElementById('c');
            const ctx = canvas.getContext('2d');
            const renderer = new NodeReelRenderer();

            await document.fonts.ready;
            await renderer.loadAssets();
            await new Promise(r => setTimeout(r, 600));

            const ws = new WebSocket('ws://' + location.host);
            ws.binaryType = 'arraybuffer';

            ws.onopen = async () => {
                const totalFrames = ${TOTAL_FRAMES};
                const fps = ${FPS};

                for (let f = 0; f < totalFrames; f++) {
                    const time = f / fps;
                    renderer.render(ctx, time, ${WIDTH}, ${HEIGHT});

                    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.92));
                    const arrayBuffer = await blob.arrayBuffer();

                    while (ws.bufferedAmount > 4 * 1024 * 1024) {
                        await new Promise(r => setTimeout(r, 15));
                    }

                    ws.send(arrayBuffer);
                }

                while (ws.bufferedAmount > 0) {
                    await new Promise(r => setTimeout(r, 50));
                }

                ws.send("DONE");
            };
        })();
    </script>
    </body>
    </html>
    `);
});

// WebSocket Server
const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
    console.log('Chromium browser connected to WebSocket. Beginning frame capture...');
    renderStartTime = Date.now();

    ws.on('message', (data, isBinary) => {
        if (!isBinary && data.toString() === 'DONE') {
            const elapsed = (Date.now() - renderStartTime) / 1000;
            console.log(`\n\n🎉 All ${framesPiped} frames streamed to FFmpeg in ${elapsed.toFixed(1)}s (${(framesPiped/elapsed).toFixed(1)} fps)!`);
            console.log('Finalizing MP4 container and encoding AAC audio...');
            ffmpeg.stdin.end();
            server.close();
            return;
        }

        ffmpeg.stdin.write(data);
        framesPiped++;
        if (framesPiped % 60 === 0 || framesPiped === TOTAL_FRAMES) {
            const pct = Math.min(100, Math.floor((framesPiped / TOTAL_FRAMES) * 100));
            const filled = Math.min(20, Math.max(0, Math.floor(pct / 5)));
            const bar = '█'.repeat(filled) + '░'.repeat(Math.max(0, 20 - filled));
            const sec = Math.min(DURATION, framesPiped / FPS).toFixed(1);
            process.stdout.write(`\r[${bar}] ${pct}% (${framesPiped}/${TOTAL_FRAMES} frames | ${sec}s / ${DURATION}s)`);
        }
    });
});

const PORT = 3899;
server.listen(PORT, () => {
    console.log(`Render server ready on port ${PORT}. Launching headless Chromium engine...`);

    const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--window-size=1080,1920',
        `http://localhost:${PORT}`
    ]);

    chrome.on('exit', () => {});

    ffmpeg.on('close', (code) => {
        if (code === 0) {
            const stats = fs.statSync(OUTPUT_MP4);
            const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
            console.log(`\n=======================================================`);
            console.log(`✅ EXPORT COMPLETE: ${OUTPUT_MP4}`);
            console.log(`   File Size: ${sizeMB} MB`);
            console.log(`   Format:    1080x1920 (9:16 Vertical Instagram Reel / YouTube Short)`);
            console.log(`   Duration:  ${DURATION}s`);
            console.log(`   Ready for upload to Instagram Reels / YouTube Shorts / TikTok!`);
            console.log(`=======================================================\n`);
            try { chrome.kill(); } catch(e) {}
            process.exit(0);
        } else {
            console.error(`FFmpeg exited with error code ${code}`);
            process.exit(1);
        }
    });
});
