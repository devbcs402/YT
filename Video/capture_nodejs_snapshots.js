const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');

const PORT = 3788;
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACTS_DIR = 'C:\\Users\\ADMIN\\.gemini\\antigravity-ide\\brain\\72cd6dd6-190c-4340-82e0-bdeaa89fc14b';

const snapshots = [
    { time: 3.0, name: 'scene1_frontend_hook.jpg', title: 'Scene 1: Frontend Website Hook' },
    { time: 7.5, name: 'scene1_backend_server.jpg', title: 'Scene 1: Backend Server Transformation' },
    { time: 14.5, name: 'scene2_meet_nodejs.jpg', title: 'Scene 2: Meet Node.js & Capabilities' },
    { time: 26.5, name: 'scene3_architecture_flow.jpg', title: 'Scene 3: Request-Response Architecture Flow' },
    { time: 36.5, name: 'scene4_code_editor.jpg', title: 'Scene 4: Syntax-Highlighted Code Demo' },
    { time: 42.0, name: 'scene4_terminal_browser.jpg', title: 'Scene 4: Terminal Execution & 200 OK Response' },
    { time: 51.0, name: 'scene5_challenge_outro.jpg', title: 'Scene 5: 100 Days Challenge Outro & Follow CTA' }
];

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
            body { margin:0; background:#000; overflow:hidden; }
            #c { width: 1080px; height: 1920px; }
        </style>
    </head>
    <body>
    <canvas id="c" width="1080" height="1920"></canvas>
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

            const timestamps = ${JSON.stringify(snapshots.map(s => s.time))};

            ws.onopen = async () => {
                for (let i = 0; i < timestamps.length; i++) {
                    const t = timestamps[i];
                    renderer.render(ctx, t, 1080, 1920);
                    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.95));
                    const arrayBuffer = await blob.arrayBuffer();
                    ws.send(arrayBuffer);
                    await new Promise(r => setTimeout(r, 150));
                }
                ws.send("DONE");
            };
        })();
    </script>
    </body>
    </html>
    `);
});

const wss = new WebSocketServer({ server });
let frameIdx = 0;
const previewDir = path.join(__dirname, 'assets', 'previews');
if (!fs.existsSync(previewDir)) fs.mkdirSync(previewDir, { recursive: true });

wss.on('connection', (ws) => {
    console.log('Browser connected to snapshot WebSocket...');

    ws.on('message', (data, isBinary) => {
        if (!isBinary && data.toString() === 'DONE') {
            console.log('🎉 All snapshots captured and saved successfully!');
            server.close();
            process.exit(0);
            return;
        }

        const snapInfo = snapshots[frameIdx];
        if (snapInfo) {
            const buf = Buffer.from(data);
            const outPath = path.join(previewDir, snapInfo.name);
            fs.writeFileSync(outPath, buf);

            // Also copy to artifacts directory
            try {
                if (fs.existsSync(ARTIFACTS_DIR)) {
                    const artifactPath = path.join(ARTIFACTS_DIR, snapInfo.name);
                    fs.writeFileSync(artifactPath, buf);
                }
            } catch (e) {
                console.error('Error copying to artifact dir:', e.message);
            }

            const sizeKB = (buf.length / 1024).toFixed(1);
            console.log(`Saved snapshot [${snapInfo.time}s]: ${snapInfo.name} (${sizeKB} KB)`);
            frameIdx++;
        }
    });
});

server.listen(PORT, () => {
    console.log(`Snapshot server listening on port ${PORT}, launching headless Chrome...`);
    spawn(CHROME, [
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--window-size=1080,1920',
        `http://localhost:${PORT}`
    ]);
});
