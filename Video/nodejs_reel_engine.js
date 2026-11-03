/**
 * 100 DAYS OF BACKEND DEVELOPMENT — DAY 1: WHAT IS NODE.JS?
 * High-End Motion Graphics Reel / Shorts Engine (1080x1920 @ 30fps)
 * Visual Style: Dark Navy (#070B14) + Emerald Green (#22C55E) + Electric Cyan (#06B6D4)
 */

class NodeReelRenderer {
    constructor() {
        this.duration = 58.5; // exactly 58.5 seconds
        this.sceneBoundaries = [0.0, 10.6, 21.6, 31.4, 43.5, 58.5];
        
        // Subtitles database with exact start/end timecodes
        this.subtitles = [
            { start: 0.50, end: 4.17, en: "Can you only build websites with JavaScript?", hi: "JavaScript se sirf websites banti hain?", key: "websites with JavaScript" },
            { start: 4.17, end: 5.82, en: "Absolutely not!", hi: "Bilkul nahi!", key: "not" },
            { start: 5.82, end: 10.48, en: "You can build powerful backend servers too!", hi: "Aap powerful backend servers bhi bana sakte ho!", key: "backend servers" },
            { start: 10.70, end: 13.64, en: "The secret is Node.js!", hi: "Iska secret hai Node.js!", key: "Node.js" },
            { start: 13.64, end: 21.45, en: "A JavaScript runtime to run JS outside the browser!", hi: "Browser ke bahar JavaScript run karne deta hai!", key: "outside the browser" },
            { start: 21.70, end: 26.20, en: "Build APIs and connect directly to databases...", hi: "Node.js se APIs banao aur databases connect karo...", key: "APIs & databases" },
            { start: 26.20, end: 31.20, en: "...and handle real-time client requests seamlessly!", hi: "...aur client requests efficiently handle karo!", key: "client requests" },
            { start: 31.50, end: 33.30, en: "Take a look at this code example!", hi: "Example dekho!", key: "code example" },
            { start: 33.30, end: 40.08, en: "In just a few lines, build an HTTP web server.", hi: "Sirf kuch lines mein pehla HTTP server!", key: "HTTP web server" },
            { start: 40.10, end: 43.40, en: "Server running on port 3000 • Status 200 OK", hi: "Server running on port 3000!", key: "port 3000 • 200 OK" },
            { start: 43.60, end: 48.03, en: "So JavaScript is no longer limited to the frontend!", hi: "JavaScript sirf frontend tak limited nahi hai!", key: "not limited" },
            { start: 48.03, end: 52.14, en: "It is a superpower for modern backend development.", hi: "Backend development ka powerful tool hai!", key: "superpower" },
            { start: 52.14, end: 58.20, en: "Follow along and conquer the 100-Day Challenge together!", hi: "Follow karo aur saath mein challenge complete karo!", key: "100-Day Challenge" }
        ];

        // Seeded particles for floating cyber background
        this.particles = [];
        for (let i = 0; i < 45; i++) {
            this.particles.push({
                x: (i * 137.5) % 1080,
                y: (i * 219.7) % 1920,
                radius: 1.5 + (i % 3) * 1.2,
                speedY: 20 + (i % 4) * 15,
                speedX: ((i % 5) - 2) * 8,
                alpha: 0.15 + (i % 4) * 0.15,
                color: i % 2 === 0 ? '#22c55e' : '#06b6d4'
            });
        }
    }

    async loadAssets() {
        return true;
    }

    // Easing helpers
    easeOutCubic(x) { return 1 - Math.pow(1 - x, 3); }
    easeInOutCubic(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
    easeOutBack(x) {
        const c1 = 1.70158;
        const c3 = c1 + 1;
        return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
    }
    clamp(v, min = 0, max = 1) { return Math.max(min, Math.min(max, v)); }

    render(ctx, time, width = 1080, height = 1920) {
        ctx.save();
        ctx.clearRect(0, 0, width, height);

        // 1. Dark Futuristic Cyber Tech Background
        this.renderCyberBackground(ctx, time, width, height);

        // Determine scene
        let sceneIndex = 0;
        for (let i = 0; i < this.sceneBoundaries.length - 1; i++) {
            if (time >= this.sceneBoundaries[i] && time < this.sceneBoundaries[i + 1]) {
                sceneIndex = i;
                break;
            }
        }
        if (time >= 43.5) sceneIndex = 4;

        // Render appropriate scene
        switch (sceneIndex) {
            case 0:
                this.renderScene1(ctx, time, width, height); // 0.0 - 10.6s: The Hook & Transformation
                break;
            case 1:
                this.renderScene2(ctx, time - 10.6, width, height); // 10.6 - 21.6s: Meet Node.js
                break;
            case 2:
                this.renderScene3(ctx, time - 21.6, width, height); // 21.6 - 31.4s: How It Works Diagram
                break;
            case 3:
                this.renderScene4(ctx, time - 31.4, width, height); // 31.4 - 43.5s: Real Code Demo & Terminal
                break;
            case 4:
            default:
                this.renderScene5(ctx, time - 43.5, width, height); // 43.5 - 58.5s: Strong Ending & CTA
                break;
        }

        // 2. Global Persistent Top Header
        this.renderTopHeader(ctx, time, width, height);

        // 3. Global Synchronized Subtitle Caption Bar
        this.renderSubtitleBar(ctx, time, width, height);

        // 4. Global Timeline Progress Bar (bottom indicator)
        this.renderGlobalProgressBar(ctx, time, width, height);

        ctx.restore();
    }

    // =========================================================================
    // BACKGROUND & AMBIENCE
    // =========================================================================
    renderCyberBackground(ctx, time, w, h) {
        // Deep tech radial gradient
        const bgGrad = ctx.createRadialGradient(w / 2, 700, 100, w / 2, 960, 1200);
        bgGrad.addColorStop(0, '#0c1a2e');
        bgGrad.addColorStop(0.5, '#080e1c');
        bgGrad.addColorStop(1, '#05070e');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, w, h);

        // Subtle glowing cyan and green atmospheric orbs
        const p1x = w * 0.25 + Math.sin(time * 0.4) * 80;
        const p1y = 450 + Math.cos(time * 0.3) * 60;
        const orb1 = ctx.createRadialGradient(p1x, p1y, 10, p1x, p1y, 400);
        orb1.addColorStop(0, 'rgba(6, 182, 212, 0.08)');
        orb1.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
        ctx.fillStyle = orb1;
        ctx.fillRect(0, 0, w, h);

        const p2x = w * 0.75 + Math.cos(time * 0.5) * 80;
        const p2y = 1100 + Math.sin(time * 0.4) * 70;
        const orb2 = ctx.createRadialGradient(p2x, p2y, 10, p2x, p2y, 450);
        orb2.addColorStop(0, 'rgba(34, 197, 94, 0.08)');
        orb2.addColorStop(1, 'rgba(34, 197, 94, 0.0)');
        ctx.fillStyle = orb2;
        ctx.fillRect(0, 0, w, h);

        // Subtle perspective tech grid
        ctx.save();
        ctx.strokeStyle = 'rgba(30, 41, 59, 0.35)';
        ctx.lineWidth = 1;
        const gridSpacing = 80;
        for (let x = 0; x <= w; x += gridSpacing) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.stroke();
        }
        for (let y = 0; y <= h; y += gridSpacing) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }
        ctx.restore();

        // Floating tech particles
        ctx.save();
        for (const p of this.particles) {
            const curY = (p.y - time * p.speedY + h * 10) % h;
            const curX = (p.x + Math.sin(time + p.radius) * p.speedX + w * 10) % w;
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.alpha;
            ctx.beginPath();
            ctx.arc(curX, curY, p.radius, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    }

    // =========================================================================
    // PERSISTENT TOP HEADER & PROGRESS
    // =========================================================================
    renderTopHeader(ctx, time, w, h) {
        ctx.save();
        const headerY = 135;

        // Pill badge background
        const pillW = 540;
        const pillH = 58;
        const pillX = (w - pillW) / 2;

        this.drawRoundedRect(ctx, pillX, headerY, pillW, pillH, 29);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(51, 65, 85, 0.8)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Pulsing green live indicator
        const pulseAlpha = 0.6 + Math.sin(time * 6) * 0.4;
        ctx.fillStyle = `rgba(34, 197, 94, ${pulseAlpha})`;
        ctx.beginPath();
        ctx.arc(pillX + 32, headerY + pillH / 2, 7, 0, Math.PI * 2);
        ctx.fill();

        // Badge text
        ctx.fillStyle = '#ffffff';
        ctx.font = '700 22px "Space Grotesk", sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText('100 DAYS OF BACKEND', pillX + 54, headerY + pillH / 2);

        // Day counter accent
        ctx.fillStyle = '#22c55e';
        ctx.font = '800 22px "Space Grotesk", sans-serif';
        ctx.fillText('• DAY 01', pillX + 375, headerY + pillH / 2);

        ctx.restore();
    }

    renderGlobalProgressBar(ctx, time, w, h) {
        ctx.save();
        const pct = this.clamp(time / this.duration);
        const barH = 6;
        const barY = h - barH;

        // Background line
        ctx.fillStyle = 'rgba(30, 41, 59, 0.6)';
        ctx.fillRect(0, barY, w, barH);

        // Progress line with emerald neon glow
        const grad = ctx.createLinearGradient(0, barY, w, barY);
        grad.addColorStop(0, '#06b6d4');
        grad.addColorStop(1, '#22c55e');
        ctx.fillStyle = grad;
        ctx.shadowColor = '#22c55e';
        ctx.shadowBlur = 12;
        ctx.fillRect(0, barY, w * pct, barH);
        ctx.restore();
    }

    // =========================================================================
    // SYNCHRONIZED ENGLISH SUBTITLE CAPTION BAR
    // =========================================================================
    renderSubtitleBar(ctx, time, w, h) {
        // Find active subtitle cue
        const cue = this.subtitles.find(s => time >= s.start && time < s.end);
        if (!cue) return;

        ctx.save();
        const cueProgress = (time - cue.start) / (cue.end - cue.start);
        const subY = 1610; // Clean mobile safe area (above IG UI)
        const subW = 940;
        const subH = 120;
        const subX = (w - subW) / 2;

        // Container card with glassmorphism
        this.drawRoundedRect(ctx, subX, subY, subW, subH, 24);
        ctx.fillStyle = 'rgba(8, 14, 26, 0.92)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(34, 197, 94, 0.4)';
        ctx.lineWidth = 1.5;
        ctx.shadowColor = 'rgba(0, 0, 0, 0.6)';
        ctx.shadowBlur = 20;
        ctx.stroke();

        // Top mini caption label
        ctx.fillStyle = 'rgba(148, 163, 184, 0.8)';
        ctx.font = '600 16px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText('DAY 1 — ENGLISH SUBTITLES', w / 2, subY + 16);

        // Main English subtitle with highlighted keyphrase
        const text = cue.en;
        ctx.font = '700 27px "Plus Jakarta Sans", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // Split text to highlight keywords
        if (cue.key && text.toLowerCase().includes(cue.key.toLowerCase())) {
            const parts = text.split(new RegExp(`(${cue.key})`, 'i'));
            let totalW = 0;
            const textMetrics = parts.map(p => {
                const width = ctx.measureText(p).width;
                totalW += width;
                return { text: p, width, isKey: p.toLowerCase() === cue.key.toLowerCase() };
            });

            let curX = w / 2 - totalW / 2;
            const midY = subY + 68;

            for (const item of textMetrics) {
                if (item.isKey) {
                    ctx.fillStyle = '#22c55e'; // Vibrant Emerald Green
                    ctx.shadowColor = 'rgba(34, 197, 94, 0.8)';
                    ctx.shadowBlur = 10;
                } else {
                    ctx.fillStyle = '#f8fafc'; // Crisp pure white
                    ctx.shadowBlur = 0;
                }
                ctx.textAlign = 'left';
                ctx.fillText(item.text, curX, midY);
                curX += item.width;
            }
        } else {
            ctx.fillStyle = '#f8fafc';
            ctx.fillText(text, w / 2, subY + 68);
        }

        // Subtitle sentence progress bar at card bottom
        const subBarW = subW - 48;
        const subBarX = subX + 24;
        const subBarY = subY + subH - 8;
        ctx.fillStyle = 'rgba(30, 41, 59, 0.7)';
        ctx.fillRect(subBarX, subBarY, subBarW, 3);
        ctx.fillStyle = '#22c55e';
        ctx.fillRect(subBarX, subBarY, subBarW * this.clamp(cueProgress), 3);

        ctx.restore();
    }

    // =========================================================================
    // SCENE 1: THE HOOK & TRANSFORMATION (0.0s – 10.6s)
    // "JavaScript se sirf websites banti hain? Bilkul nahi! Powerful backend servers!"
    // =========================================================================
    renderScene1(ctx, time, w, h) {
        ctx.save();

        // Camera zoom-in transition in first 1.2s
        const zoom = time < 1.2 ? 1.0 + (1.2 - time) * 0.15 : 1.0;
        ctx.translate(w / 2, h / 2);
        ctx.scale(zoom, zoom);
        ctx.translate(-w / 2, -h / 2);

        // Top Hook Kinetic Title
        const titleOpacity = this.clamp(time / 0.5);
        ctx.save();
        ctx.globalAlpha = titleOpacity;
        ctx.textAlign = 'center';

        ctx.font = '800 48px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.fillText('JavaScript Beyond', w / 2, 270);
        ctx.fillStyle = '#06b6d4';
        ctx.shadowColor = 'rgba(6, 182, 212, 0.8)';
        ctx.shadowBlur = 15;
        ctx.fillText('The Browser!', w / 2, 335);
        ctx.shadowBlur = 0;
        ctx.restore();

        // Timing phases within Scene 1:
        // 0.0s – 5.0s: Browser mockup with "Frontend Only?" question
        // 5.0s – 5.8s: "BILKUL NAHI!" (Impact flash & NO stamp)
        // 5.8s – 10.6s: Browser morphs/scales into glowing 3D Rack Server!

        const isBackendPhase = time >= 5.5;
        const morphProgress = this.clamp((time - 5.0) / 1.0);

        if (!isBackendPhase) {
            // FRONTEND BROWSER WINDOW PHASE
            const browserY = 430 + Math.sin(time * 2) * 6;
            const bW = 860;
            const bH = 680;
            const bX = (w - bW) / 2;

            this.drawBrowserMockup(ctx, bX, browserY, bW, bH, time);

            // Floating question badge: "JavaScript = Only Frontend?"
            const badgePop = this.easeOutBack(this.clamp(time / 0.8));
            ctx.save();
            ctx.translate(w / 2, 1220);
            ctx.scale(badgePop, badgePop);

            const qW = 660;
            const qH = 100;
            this.drawRoundedRect(ctx, -qW / 2, -qH / 2, qW, qH, 22);
            ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
            ctx.fill();
            ctx.strokeStyle = '#f59e0b';
            ctx.lineWidth = 2.5;
            ctx.shadowColor = 'rgba(245, 158, 11, 0.6)';
            ctx.shadowBlur = 20;
            ctx.stroke();

            ctx.font = '800 32px "Space Grotesk", sans-serif';
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('JavaScript = Only Websites? 🤔', 0, 0);
            ctx.restore();

            // At 4.2s - 5.5s: "BILKUL NAHI! (NO!)" impact stamp
            if (time >= 4.0) {
                const stampProgress = this.easeOutBack(this.clamp((time - 4.0) / 0.35));
                ctx.save();
                ctx.translate(w / 2, 770);
                ctx.rotate(-0.12);
                ctx.scale(stampProgress, stampProgress);

                const stampW = 560;
                const stampH = 120;
                this.drawRoundedRect(ctx, -stampW / 2, -stampH / 2, stampW, stampH, 20);
                ctx.fillStyle = 'rgba(239, 68, 68, 0.95)';
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 4;
                ctx.shadowColor = 'rgba(239, 68, 68, 0.9)';
                ctx.shadowBlur = 30;
                ctx.stroke();

                ctx.font = '900 48px "Space Grotesk", sans-serif';
                ctx.fillStyle = '#ffffff';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('BILKUL NAHI! ❌', 0, 0);
                ctx.restore();
            }
        } else {
            // BACKEND SERVER TOWER VISUALIZATION PHASE
            const serverY = 440;
            const sW = 860;
            const sH = 720;
            const sX = (w - sW) / 2;

            const enterProgress = this.easeOutBack(this.clamp((time - 5.5) / 0.8));
            ctx.save();
            ctx.translate(w / 2, serverY + sH / 2);
            ctx.scale(enterProgress, enterProgress);
            ctx.translate(-w / 2, -(serverY + sH / 2));

            this.drawServerRackVisualization(ctx, sX, serverY, sW, sH, time);
            ctx.restore();

            // Large Animated Banner: "JavaScript = Powerful Backend Servers!"
            const banProgress = this.easeOutBack(this.clamp((time - 6.0) / 0.6));
            ctx.save();
            ctx.translate(w / 2, 1260);
            ctx.scale(banProgress, banProgress);

            const banW = 800;
            const banH = 120;
            this.drawRoundedRect(ctx, -banW / 2, -banH / 2, banW, banH, 26);
            ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
            ctx.fill();
            ctx.strokeStyle = '#22c55e';
            ctx.lineWidth = 3;
            ctx.shadowColor = 'rgba(34, 197, 94, 0.8)';
            ctx.shadowBlur = 25;
            ctx.stroke();

            ctx.font = '800 32px "Space Grotesk", sans-serif';
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('JavaScript = Backend Servers! ⚡', 0, -14);

            ctx.font = '700 22px "Plus Jakarta Sans", sans-serif';
            ctx.fillStyle = '#4ade80';
            ctx.fillText('Fast • Scalable • Event-Driven', 0, 24);
            ctx.restore();
        }

        ctx.restore();
    }

    drawBrowserMockup(ctx, x, y, w, h, time) {
        // Outer window frame
        this.drawRoundedRect(ctx, x, y, w, h, 24);
        ctx.fillStyle = '#0d1527';
        ctx.fill();
        ctx.strokeStyle = 'rgba(51, 65, 85, 0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Browser top header bar
        const headerH = 64;
        this.drawRoundedRect(ctx, x, y, w, headerH, 24, true, false);
        ctx.fillStyle = '#162238';
        ctx.fill();

        // Mac traffic lights
        ctx.fillStyle = '#ef4444';
        ctx.beginPath(); ctx.arc(x + 36, y + 32, 8, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath(); ctx.arc(x + 64, y + 32, 8, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#10b981';
        ctx.beginPath(); ctx.arc(x + 92, y + 32, 8, 0, Math.PI * 2); ctx.fill();

        // Address bar
        this.drawRoundedRect(ctx, x + 130, y + 14, w - 160, 36, 12);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.7)';
        ctx.fill();
        ctx.font = '500 16px "Space Grotesk", monospace';
        ctx.fillStyle = '#94a3b8';
        ctx.textAlign = 'left';
        ctx.fillText('🔒 https://my-portfolio-site.com', x + 155, y + 38);

        // Webpage content inside browser
        const bodyY = y + headerH + 20;

        // Hero card
        this.drawRoundedRect(ctx, x + 40, bodyY, w - 80, 180, 16);
        ctx.fillStyle = 'rgba(30, 41, 59, 0.6)';
        ctx.fill();
        ctx.font = '800 28px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.fillText('Interactive Frontend UI', x + 70, bodyY + 60);

        ctx.font = '500 18px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('Buttons, Animations, Styles & DOM Manipulation', x + 70, bodyY + 100);

        // Animated CTA button in website
        this.drawRoundedRect(ctx, x + 70, bodyY + 120, 180, 40, 10);
        ctx.fillStyle = '#06b6d4';
        ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.font = '700 16px "Space Grotesk", sans-serif';
        ctx.fillText('Click Me 👆', x + 120, bodyY + 145);

        // Three grid cards below
        const cardW = (w - 120) / 3;
        for (let i = 0; i < 3; i++) {
            const cx = x + 40 + i * (cardW + 20);
            const cy = bodyY + 210;
            this.drawRoundedRect(ctx, cx, cy, cardW, 280, 14);
            ctx.fillStyle = 'rgba(15, 23, 42, 0.7)';
            ctx.fill();
            ctx.strokeStyle = 'rgba(51, 65, 85, 0.5)';
            ctx.stroke();

            // Card icon
            ctx.fillStyle = i === 0 ? '#38bdf8' : i === 1 ? '#f43f5e' : '#a855f7';
            ctx.beginPath();
            ctx.arc(cx + 35, cy + 45, 16, 0, Math.PI * 2);
            ctx.fill();

            // Card title
            ctx.fillStyle = '#e2e8f0';
            ctx.font = '700 18px "Space Grotesk", sans-serif';
            ctx.fillText(['HTML5', 'CSS3', 'React'][i], cx + 65, cy + 50);

            // Mock lines
            ctx.fillStyle = 'rgba(100, 116, 139, 0.4)';
            ctx.fillRect(cx + 20, cy + 90, cardW - 40, 10);
            ctx.fillRect(cx + 20, cy + 120, cardW - 60, 10);
            ctx.fillRect(cx + 20, cy + 150, cardW - 50, 10);
        }
    }

    drawServerRackVisualization(ctx, x, y, w, h, time) {
        // Outer Rack frame
        this.drawRoundedRect(ctx, x, y, w, h, 24);
        ctx.fillStyle = '#090e1a';
        ctx.fill();
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = 'rgba(34, 197, 94, 0.4)';
        ctx.shadowBlur = 20;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Top rack header
        this.drawRoundedRect(ctx, x, y, w, 70, 24, true, false);
        ctx.fillStyle = '#111c33';
        ctx.fill();

        ctx.fillStyle = '#22c55e';
        ctx.font = '800 24px "Space Grotesk", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('⚡ BACKEND PRODUCTION SERVER TOWER', x + 40, y + 42);

        // 3 Server Units in Rack
        const unitH = 180;
        for (let i = 0; i < 3; i++) {
            const uy = y + 90 + i * (unitH + 20);
            this.drawRoundedRect(ctx, x + 30, uy, w - 60, unitH, 16);
            ctx.fillStyle = '#0d1629';
            ctx.fill();
            ctx.strokeStyle = 'rgba(34, 197, 94, 0.3)';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Server Unit label
            ctx.fillStyle = '#f8fafc';
            ctx.font = '700 20px "Space Grotesk", sans-serif';
            ctx.fillText([
                'NODE.JS APPLICATION CLUSTER #01',
                'API GATEWAY & LOAD BALANCER #02',
                'DATABASE & CACHE ENGINE #03'
            ][i], x + 60, uy + 45);

            // Blinking activity LEDs
            for (let led = 0; led < 8; led++) {
                const ledX = x + w - 280 + led * 26;
                const ledY = uy + 40;
                const isBlink = Math.sin(time * 12 + led * 1.5 + i * 2) > 0;
                ctx.fillStyle = isBlink ? '#22c55e' : 'rgba(34, 197, 94, 0.2)';
                ctx.shadowColor = '#22c55e';
                ctx.shadowBlur = isBlink ? 8 : 0;
                ctx.beginPath();
                ctx.arc(ledX, ledY, 5, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.shadowBlur = 0;

            // CPU & Memory activity graph bars
            const barW = (w - 140) / 12;
            for (let b = 0; b < 12; b++) {
                const barH = 30 + Math.sin(time * 4 + b * 0.8 + i) * 20;
                const bx = x + 60 + b * (barW + 6);
                const by = uy + unitH - 30 - barH;
                ctx.fillStyle = b < 8 ? '#06b6d4' : '#22c55e';
                ctx.fillRect(bx, by, barW, barH);
            }
        }
    }

    // =========================================================================
    // SCENE 2: INTRODUCE NODE.JS (10.6s – 21.6s)
    // "Iska secret hai Node.js! Ye ek JavaScript runtime environment hai..."
    // =========================================================================
    renderScene2(ctx, time, w, h) {
        ctx.save();

        // Title kinetic typography
        ctx.textAlign = 'center';
        ctx.font = '800 48px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('Meet Node.js', w / 2, 260);

        ctx.font = '700 24px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#22c55e';
        ctx.shadowColor = 'rgba(34, 197, 94, 0.8)';
        ctx.shadowBlur = 12;
        ctx.fillText('JavaScript Runtime Environment', w / 2, 310);
        ctx.shadowBlur = 0;

        // Big 3D Stylized Node.js Hexagon Entrance
        const hexEnter = this.easeOutBack(this.clamp(time / 0.8));
        const floatY = Math.sin(time * 2.5) * 12;

        ctx.save();
        ctx.translate(w / 2, 570 + floatY);
        ctx.scale(hexEnter, hexEnter);

        this.drawNodeHexagonLogo(ctx, 0, 0, 160, time);
        ctx.restore();

        // Concept Comparison: Browser vs Outside the Browser
        const compY = 870;
        const compW = 900;
        const compH = 580;
        const compX = (w - compW) / 2;

        this.drawRoundedRect(ctx, compX, compY, compW, compH, 24);
        ctx.fillStyle = 'rgba(13, 21, 39, 0.9)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(51, 65, 85, 0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Header inside comparison card
        ctx.font = '800 24px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.fillText('WHAT DOES NODE.JS DO?', w / 2, compY + 45);

        // Left Column: Traditional Browser
        const colW = (compW - 80) / 2;
        const col1X = compX + 30;
        const col2X = compX + compW / 2 + 10;
        const colY = compY + 80;
        const colH = compH - 110;

        // Browser Column
        this.drawRoundedRect(ctx, col1X, colY, colW, colH, 16);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.7)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
        ctx.stroke();

        ctx.fillStyle = '#ef4444';
        ctx.font = '800 20px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('IN THE BROWSER', col1X + colW / 2, colY + 38);

        ctx.font = '500 17px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#cbd5e1';
        ctx.textAlign = 'left';
        const browserPoints = [
            '❌ No Direct File System Access',
            '❌ Cannot Run as Web Server',
            '❌ No Direct Database Connection',
            '✅ Trapped inside browser tab',
            '✅ Limited to UI / DOM actions'
        ];
        browserPoints.forEach((pt, idx) => {
            ctx.fillText(pt, col1X + 22, colY + 95 + idx * 60);
        });

        // Node.js Column
        this.drawRoundedRect(ctx, col2X, colY, colW, colH, 16);
        ctx.fillStyle = 'rgba(6, 40, 25, 0.7)';
        ctx.fill();
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = '#22c55e';
        ctx.font = '800 20px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('WITH NODE.JS 🚀', col2X + colW / 2, colY + 38);

        ctx.font = '600 17px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'left';
        const nodePoints = [
            '⚡ Full File System (fs) Access',
            '⚡ Native HTTP Web Servers',
            '⚡ Connect MongoDB, SQL & Redis',
            '⚡ Runs Anywhere (Cloud, Linux, Mac)',
            '⚡ High Concurrency & Fast APIs'
        ];
        nodePoints.forEach((pt, idx) => {
            ctx.fillText(pt, col2X + 22, colY + 95 + idx * 60);
        });

        // Bottom Highlight Pill: "Built on Chrome V8 Engine + C++"
        const engineProgress = this.easeOutBack(this.clamp((time - 3.5) / 0.6));
        ctx.save();
        ctx.translate(w / 2, 1500);
        ctx.scale(engineProgress, engineProgress);

        const pillW = 740;
        const pillH = 70;
        this.drawRoundedRect(ctx, -pillW / 2, -pillH / 2, pillW, pillH, 18);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
        ctx.fill();
        ctx.strokeStyle = '#06b6d4';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.font = '700 22px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Powered by Google Chrome V8 & Libuv ⚙️', 0, 0);
        ctx.restore();

        ctx.restore();
    }

    drawNodeHexagonLogo(ctx, cx, cy, radius, time) {
        ctx.save();
        ctx.translate(cx, cy);

        // Outer glow
        const glowRad = radius + 35 + Math.sin(time * 3) * 15;
        const glow = ctx.createRadialGradient(0, 0, radius * 0.5, 0, 0, glowRad);
        glow.addColorStop(0, 'rgba(34, 197, 94, 0.4)');
        glow.addColorStop(1, 'rgba(34, 197, 94, 0.0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(0, 0, glowRad, 0, Math.PI * 2);
        ctx.fill();

        // 3D Hexagon Shape
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const angle = (Math.PI / 3) * i - Math.PI / 6;
            const x = radius * Math.cos(angle);
            const y = radius * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();

        // Hexagon Gradient
        const hexGrad = ctx.createLinearGradient(-radius, -radius, radius, radius);
        hexGrad.addColorStop(0, '#3e863d');
        hexGrad.addColorStop(0.5, '#22c55e');
        hexGrad.addColorStop(1, '#15803d');
        ctx.fillStyle = hexGrad;
        ctx.fill();
        ctx.strokeStyle = '#86efac';
        ctx.lineWidth = 6;
        ctx.stroke();

        // Node.js Stylized Text inside
        ctx.font = '900 68px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.shadowColor = 'rgba(0, 0, 0, 0.6)';
        ctx.shadowBlur = 10;
        ctx.fillText('node', 0, -10);

        ctx.font = '800 32px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#dcfce7';
        ctx.fillText('.JS', 0, 48);

        ctx.restore();
    }

    // =========================================================================
    // SCENE 3: HOW IT WORKS ARCHITECTURE DIAGRAM (21.6s – 31.4s)
    // "Ab Node.js ki help se aap APIs bana sakte ho, database se connect..."
    // =========================================================================
    renderScene3(ctx, time, w, h) {
        ctx.save();

        // Top Kinetic Title
        ctx.textAlign = 'center';
        ctx.font = '800 46px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('How Node.js Works', w / 2, 260);

        ctx.font = '700 24px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#06b6d4';
        ctx.shadowColor = 'rgba(6, 182, 212, 0.8)';
        ctx.shadowBlur = 12;
        ctx.fillText('Full Request & Response Lifecycle', w / 2, 310);
        ctx.shadowBlur = 0;

        // Sequence badge flow at top of diagram
        const stepProgress = (time / 9.8) * 4; // 0 to 4 steps
        const currentStep = Math.min(3, Math.floor(stepProgress));

        const flowBarY = 370;
        const flowW = 940;
        const flowH = 64;
        const flowX = (w - flowW) / 2;
        this.drawRoundedRect(ctx, flowX, flowBarY, flowW, flowH, 18);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(51, 65, 85, 0.8)';
        ctx.stroke();

        const steps = ['Client', 'Node.js API', 'MongoDB', 'Response'];
        ctx.font = '700 20px "Space Grotesk", sans-serif';
        ctx.textBaseline = 'middle';
        const itemW = flowW / 4;

        steps.forEach((st, idx) => {
            const ix = flowX + idx * itemW + itemW / 2;
            const isAct = idx <= currentStep;
            ctx.fillStyle = isAct ? '#22c55e' : '#64748b';
            ctx.fillText(`${idx + 1}. ${st}`, ix - 10, flowBarY + flowH / 2);

            if (idx < 3) {
                ctx.fillStyle = '#475569';
                ctx.fillText('→', flowX + (idx + 1) * itemW, flowBarY + flowH / 2);
            }
        });

        // =========================================================
        // THREE CENTRAL ARCHITECTURE NODES:
        // 1. CLIENT (Left: x = 200, y = 800)
        // 2. NODE.JS SERVER (Center: x = 540, y = 800)
        // 3. MONGODB (Right: x = 880, y = 800)
        // =========================================================
        const nY = 780;
        const clientX = 200;
        const serverX = 540;
        const dbX = 880;

        // Connecting dynamic energy pipes
        this.drawConnectionPipe(ctx, clientX, nY, serverX, nY, time, currentStep >= 0);
        this.drawConnectionPipe(ctx, serverX, nY, dbX, nY, time, currentStep >= 1);

        // 1. Client Card
        this.drawArchitectureNode(ctx, clientX, nY, 'CLIENT', 'Mobile / Web', '#06b6d4', '📱', currentStep === 0);

        // 2. Node.js API Card
        this.drawArchitectureNode(ctx, serverX, nY, 'NODE.JS', 'REST API Engine', '#22c55e', '⚡', currentStep === 1 || currentStep === 3);

        // 3. Database Card
        this.drawArchitectureNode(ctx, dbX, nY, 'DATABASE', 'MongoDB / SQL', '#10b981', '🍃', currentStep === 2);

        // Data packet animation flowing between nodes
        if (currentStep === 0) {
            // Client -> Server packet
            const pktProgress = (stepProgress % 1);
            const px = clientX + (serverX - clientX) * pktProgress;
            this.drawDataPacket(ctx, px, nY - 40, 'GET /api/users', '#06b6d4');
        } else if (currentStep === 1) {
            // Server -> DB query packet
            const pktProgress = (stepProgress % 1);
            const px = serverX + (dbX - serverX) * pktProgress;
            this.drawDataPacket(ctx, px, nY - 40, 'db.users.find()', '#22c55e');
        } else if (currentStep === 2) {
            // DB -> Server data return packet
            const pktProgress = (stepProgress % 1);
            const px = dbX - (dbX - serverX) * pktProgress;
            this.drawDataPacket(ctx, px, nY + 40, 'Document Data', '#10b981');
        } else {
            // Server -> Client JSON Response packet
            const pktProgress = (stepProgress % 1);
            const px = serverX - (serverX - clientX) * pktProgress;
            this.drawDataPacket(ctx, px, nY + 40, '200 OK JSON', '#38bdf8');
        }

        // Live JSON Terminal Card below diagram
        const jsonY = 1080;
        const jsonW = 920;
        const jsonH = 380;
        const jsonX = (w - jsonW) / 2;

        this.drawRoundedRect(ctx, jsonX, jsonY, jsonW, jsonH, 20);
        ctx.fillStyle = '#0a101f';
        ctx.fill();
        ctx.strokeStyle = 'rgba(51, 65, 85, 0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Header of JSON viewer
        this.drawRoundedRect(ctx, jsonX, jsonY, jsonW, 50, 20, true, false);
        ctx.fillStyle = '#111b33';
        ctx.fill();

        ctx.fillStyle = '#94a3b8';
        ctx.font = '600 16px "Space Grotesk", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('📡 LIVE HTTP RESPONSE PAYLOAD (JSON)', jsonX + 30, jsonY + 32);

        // JSON Content with syntax highlighting
        const jsonLines = [
            { text: '{', color: '#f8fafc' },
            { text: '  "status": 200,', color: '#4ade80' },
            { text: '  "message": "Success from Node.js Server",', color: '#38bdf8' },
            { text: '  "timestamp": "' + new Date().toISOString().slice(0, 19) + 'Z",', color: '#fbbf24' },
            { text: '  "data": [', color: '#f8fafc' },
            { text: '    { "id": 101, "role": "Backend Engineer", "challenge": "Day 01" }', color: '#c084fc' },
            { text: '  ]', color: '#f8fafc' },
            { text: '}', color: '#f8fafc' }
        ];

        ctx.font = '500 20px "Fira Code", monospace';
        jsonLines.forEach((jl, idx) => {
            ctx.fillStyle = jl.color;
            ctx.fillText(jl.text, jsonX + 35, jsonY + 90 + idx * 34);
        });

        ctx.restore();
    }

    drawConnectionPipe(ctx, x1, y1, x2, y2, time, active) {
        ctx.save();
        ctx.strokeStyle = active ? 'rgba(34, 197, 94, 0.5)' : 'rgba(51, 65, 85, 0.4)';
        ctx.lineWidth = 4;
        ctx.setLineDash([12, 8]);
        ctx.lineDashOffset = -time * 30;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.restore();
    }

    drawArchitectureNode(ctx, cx, cy, title, sub, color, icon, isActive) {
        ctx.save();
        const nw = 220;
        const nh = 220;
        const nx = cx - nw / 2;
        const ny = cy - nh / 2;

        this.drawRoundedRect(ctx, nx, ny, nw, nh, 22);
        ctx.fillStyle = isActive ? 'rgba(16, 27, 48, 0.95)' : 'rgba(11, 18, 33, 0.85)';
        ctx.fill();
        ctx.strokeStyle = isActive ? color : 'rgba(51, 65, 85, 0.6)';
        ctx.lineWidth = isActive ? 3.5 : 2;
        if (isActive) {
            ctx.shadowColor = color;
            ctx.shadowBlur = 25;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Icon
        ctx.font = '54px "Apple Color Emoji", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(icon, cx, cy - 35);

        // Title
        ctx.font = '800 22px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText(title, cx, cy + 35);

        // Subtitle
        ctx.font = '600 15px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = color;
        ctx.fillText(sub, cx, cy + 65);

        ctx.restore();
    }

    drawDataPacket(ctx, x, y, label, color) {
        ctx.save();
        const pw = 180;
        const ph = 42;
        this.drawRoundedRect(ctx, x - pw / 2, y - ph / 2, pw, ph, 12);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.shadowColor = color;
        ctx.shadowBlur = 12;
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.font = '700 15px "Fira Code", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, x, y);
        ctx.restore();
    }

    // =========================================================================
    // SCENE 4: REAL CODE DEMO & TERMINAL (31.4s – 43.5s)
    // "Example dekho! Sirf kuch lines mein pehla HTTP server..."
    // =========================================================================
    renderScene4(ctx, time, w, h) {
        ctx.save();

        // Top Header
        ctx.textAlign = 'center';
        ctx.font = '800 46px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('Real Code Demo', w / 2, 260);

        ctx.font = '700 22px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#22c55e';
        ctx.fillText('Create an HTTP Web Server in 9 Lines', w / 2, 305);

        // VS Code Editor Mockup
        const edY = 360;
        const edW = 960;
        const edH = 700;
        const edX = (w - edW) / 2;

        this.drawCodeEditor(ctx, edX, edY, edW, edH, time);

        // Terminal window sliding in below editor
        const termY = 1100;
        const termW = 960;
        const termH = 220;
        const termX = (w - termW) / 2;
        this.drawTerminalWindow(ctx, termX, termY, termW, termH, time);

        // Browser preview card popping in at bottom (after 8.5s in scene)
        if (time >= 8.5) {
            const browserProgress = this.easeOutBack(this.clamp((time - 8.5) / 0.5));
            const bY = 1350;
            const bW = 960;
            const bH = 170;
            const bX = (w - bW) / 2;

            ctx.save();
            ctx.translate(w / 2, bY + bH / 2);
            ctx.scale(browserProgress, browserProgress);
            ctx.translate(-w / 2, -(bY + bH / 2));

            this.drawMiniBrowserResponse(ctx, bX, bY, bW, bH, time);
            ctx.restore();
        }

        ctx.restore();
    }

    drawCodeEditor(ctx, x, y, w, h, time) {
        // Outer editor frame
        this.drawRoundedRect(ctx, x, y, w, h, 20);
        ctx.fillStyle = '#0d1117'; // GitHub/VS Code Dark
        ctx.fill();
        ctx.strokeStyle = '#30363d';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Editor title bar
        const titleH = 56;
        this.drawRoundedRect(ctx, x, y, w, titleH, 20, true, false);
        ctx.fillStyle = '#161b22';
        ctx.fill();

        // Window controls
        ctx.fillStyle = '#ff5f56';
        ctx.beginPath(); ctx.arc(x + 32, y + 28, 7, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffbd2e';
        ctx.beginPath(); ctx.arc(x + 56, y + 28, 7, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#27c93f';
        ctx.beginPath(); ctx.arc(x + 80, y + 28, 7, 0, Math.PI * 2); ctx.fill();

        // Active File Tab
        const tabW = 220;
        this.drawRoundedRect(ctx, x + 120, y + 8, tabW, 40, 8);
        ctx.fillStyle = '#0d1117';
        ctx.fill();
        ctx.fillStyle = '#22c55e';
        ctx.font = '700 16px "Fira Code", monospace';
        ctx.textAlign = 'left';
        ctx.fillText('📄 server.js', x + 145, y + 33);

        // Progressive line typing reveal
        const lines = [
            { num: 1, tokens: [{ t: 'const', c: '#c084fc' }, { t: ' http = ', c: '#f8fafc' }, { t: 'require', c: '#38bdf8' }, { t: '("node:http");', c: '#86efac' }] },
            { num: 2, tokens: [] },
            { num: 3, tokens: [{ t: 'const', c: '#c084fc' }, { t: ' server = http.', c: '#f8fafc' }, { t: 'createServer', c: '#4ade80', highlight: true }, { t: '((req, res) => {', c: '#f8fafc' }] },
            { num: 4, tokens: [{ t: '  res.', c: '#f8fafc' }, { t: 'end', c: '#38bdf8' }, { t: '("Hello from Node.js!");', c: '#86efac' }] },
            { num: 5, tokens: [{ t: '});', c: '#f8fafc' }] },
            { num: 6, tokens: [] },
            { num: 7, tokens: [{ t: 'server.', c: '#f8fafc' }, { t: 'listen', c: '#4ade80', highlight: true }, { t: '(', c: '#f8fafc' }, { t: '3000', c: '#fbbf24', highlight: true }, { t: ', () => {', c: '#f8fafc' }] },
            { num: 8, tokens: [{ t: '  console.', c: '#f8fafc' }, { t: 'log', c: '#38bdf8' }, { t: '("Server running on port 3000");', c: '#86efac' }] },
            { num: 9, tokens: [{ t: '});', c: '#f8fafc' }] }
        ];

        // Reveal lines over first 3.5s
        const visibleLinesCount = Math.min(lines.length, Math.floor(time * 3.5) + 3);

        ctx.font = '500 24px "Fira Code", monospace';
        const startY = y + 105;
        const lineH = 58;

        for (let i = 0; i < visibleLinesCount; i++) {
            const line = lines[i];
            const ly = startY + i * lineH;

            // Line number
            ctx.fillStyle = '#484f58';
            ctx.textAlign = 'right';
            ctx.fillText(String(line.num), x + 55, ly);

            // Gutter divider
            ctx.fillStyle = '#21262d';
            ctx.fillRect(x + 75, ly - 28, 1, 40);

            // Code tokens
            let tokenX = x + 100;
            ctx.textAlign = 'left';

            // Highlighting boxes for createServer and listen
            const isHighlightPhase = time >= 3.0;
            if (isHighlightPhase && (i === 2 || i === 6)) {
                ctx.save();
                this.drawRoundedRect(ctx, x + 90, ly - 32, w - 140, 46, 8);
                ctx.fillStyle = 'rgba(34, 197, 94, 0.12)';
                ctx.fill();
                ctx.strokeStyle = 'rgba(34, 197, 94, 0.5)';
                ctx.lineWidth = 1.5;
                ctx.stroke();
                ctx.restore();
            }

            line.tokens.forEach(tk => {
                ctx.fillStyle = tk.c;
                ctx.fillText(tk.t, tokenX, ly);
                tokenX += ctx.measureText(tk.t).width;
            });
        }
    }

    drawTerminalWindow(ctx, x, y, w, h, time) {
        this.drawRoundedRect(ctx, x, y, w, h, 18);
        ctx.fillStyle = '#0a0d14';
        ctx.fill();
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Terminal header
        this.drawRoundedRect(ctx, x, y, w, 44, 18, true, false);
        ctx.fillStyle = '#141a29';
        ctx.fill();

        ctx.fillStyle = '#94a3b8';
        ctx.font = '600 16px "Space Grotesk", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('💻 TERMINAL — bash', x + 25, y + 28);

        // Terminal command typing & output
        const cmdY = y + 90;
        ctx.font = '600 24px "Fira Code", monospace';
        ctx.fillStyle = '#38bdf8';
        ctx.fillText('$ ', x + 30, cmdY);

        ctx.fillStyle = '#f8fafc';
        ctx.fillText('node server.js', x + 60, cmdY);

        // Output appears after 4.5s in scene
        if (time >= 4.5) {
            const outY = cmdY + 55;
            ctx.fillStyle = '#22c55e';
            ctx.shadowColor = 'rgba(34, 197, 94, 0.8)';
            ctx.shadowBlur = 10;
            ctx.fillText('> Server running on port 3000', x + 30, outY);
            ctx.shadowBlur = 0;

            // Green pulsing dot
            ctx.beginPath();
            ctx.arc(x + 520, outY - 7, 7, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    drawMiniBrowserResponse(ctx, x, y, w, h, time) {
        this.drawRoundedRect(ctx, x, y, w, h, 20);
        ctx.fillStyle = '#0f172a';
        ctx.fill();
        ctx.strokeStyle = '#06b6d4';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = 'rgba(6, 182, 212, 0.5)';
        ctx.shadowBlur = 20;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // URL bar
        this.drawRoundedRect(ctx, x + 25, y + 16, w - 50, 44, 12);
        ctx.fillStyle = '#1e293b';
        ctx.fill();

        ctx.fillStyle = '#38bdf8';
        ctx.font = '600 18px "Fira Code", monospace';
        ctx.textAlign = 'left';
        ctx.fillText('🔒 http://localhost:3000', x + 45, y + 44);

        // Status pill
        this.drawRoundedRect(ctx, x + w - 180, y + 20, 140, 36, 10);
        ctx.fillStyle = '#166534';
        ctx.fill();
        ctx.fillStyle = '#86efac';
        ctx.font = '700 16px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('200 OK ✅', x + w - 110, y + 43);

        // Body content from res.end()
        ctx.fillStyle = '#ffffff';
        ctx.font = '800 36px "Space Grotesk", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('"Hello from Node.js!"', x + 50, y + 125);
    }

    // =========================================================================
    // SCENE 5: STRONG ENDING & CHALLENGE CTA (43.5s – 58.5s)
    // "Toh ab JavaScript sirf frontend tak limited nahi hai! Follow karo..."
    // =========================================================================
    renderScene5(ctx, time, w, h) {
        ctx.save();

        // 3 Animated Floating Tech Cards (Node.js, Express.js, MongoDB)
        const logosY = 320;
        const logoSpacing = 280;
        const cardW = 250;
        const cardH = 220;

        const stack = [
            { name: 'Node.js', icon: '🟢', desc: 'Runtime Core', color: '#22c55e' },
            { name: 'Express.js', icon: '⚡', desc: 'Backend APIs', color: '#38bdf8' },
            { name: 'MongoDB', icon: '🍃', desc: 'NoSQL Database', color: '#10b981' }
        ];

        stack.forEach((st, idx) => {
            const cx = w / 2 + (idx - 1) * logoSpacing;
            const float = Math.sin(time * 3 + idx * 1.5) * 10;
            const cy = logosY + float;

            this.drawRoundedRect(ctx, cx - cardW / 2, cy - cardH / 2, cardW, cardH, 20);
            ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
            ctx.fill();
            ctx.strokeStyle = st.color;
            ctx.lineWidth = 2.5;
            ctx.shadowColor = st.color;
            ctx.shadowBlur = 15;
            ctx.stroke();
            ctx.shadowBlur = 0;

            ctx.font = '48px "Apple Color Emoji", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(st.icon, cx, cy - 30);

            ctx.font = '800 22px "Space Grotesk", sans-serif';
            ctx.fillStyle = '#ffffff';
            ctx.fillText(st.name, cx, cy + 30);

            ctx.font = '600 16px "Plus Jakarta Sans", sans-serif';
            ctx.fillStyle = st.color;
            ctx.fillText(st.desc, cx, cy + 60);
        });

        // Bold Giant Challenge Title
        const titleY = 620;
        ctx.textAlign = 'center';

        ctx.font = '800 36px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('100 DAYS OF', w / 2, titleY);

        ctx.font = '900 58px "Space Grotesk", sans-serif';
        const grad = ctx.createLinearGradient(w / 2 - 400, titleY + 60, w / 2 + 400, titleY + 60);
        grad.addColorStop(0, '#38bdf8');
        grad.addColorStop(0.5, '#22c55e');
        grad.addColorStop(1, '#a855f7');
        ctx.fillStyle = grad;
        ctx.shadowColor = 'rgba(34, 197, 94, 0.6)';
        ctx.shadowBlur = 25;
        ctx.fillText('BACKEND DEVELOPMENT', w / 2, titleY + 70);
        ctx.shadowBlur = 0;

        // Big Glowing Badge: DAY 01 / 100 COMPLETE
        const badgeY = 820;
        const badgeW = 820;
        const badgeH = 150;
        const badgeX = (w - badgeW) / 2;

        this.drawRoundedRect(ctx, badgeX, badgeY, badgeW, badgeH, 26);
        ctx.fillStyle = 'rgba(13, 21, 39, 0.95)';
        ctx.fill();
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 3.5;
        ctx.shadowColor = '#22c55e';
        ctx.shadowBlur = 30;
        ctx.stroke();
        ctx.shadowBlur = 0;

        ctx.font = '900 48px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('DAY 01 / 100 COMPLETE ✅', w / 2, badgeY + 62);

        // 100-Day Progress Bar (1% Filled)
        const pbarW = badgeW - 80;
        const pbarH = 14;
        const pbarX = badgeX + 40;
        const pbarY = badgeY + 95;

        this.drawRoundedRect(ctx, pbarX, pbarY, pbarW, pbarH, 7);
        ctx.fillStyle = 'rgba(30, 41, 59, 0.8)';
        ctx.fill();

        const animatedPct = this.clamp(time / 2.0) * 0.05 + 0.01;
        this.drawRoundedRect(ctx, pbarX, pbarY, pbarW * animatedPct, pbarH, 7);
        ctx.fillStyle = '#22c55e';
        ctx.shadowColor = '#22c55e';
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.font = '700 16px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('1% Mastery Unlocked • 99 Days Remaining', w / 2, badgeY + 132);

        // High-Conversion Call To Action Card
        const ctaY = 1050;
        const ctaW = 860;
        const ctaH = 460;
        const ctaX = (w - ctaW) / 2;

        this.drawRoundedRect(ctx, ctaX, ctaY, ctaW, ctaH, 26);
        ctx.fillStyle = 'rgba(11, 18, 33, 0.92)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.font = '800 36px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('Up Next: DAY 2 🚀', w / 2, ctaY + 65);

        ctx.font = '600 24px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#38bdf8';
        ctx.fillText('Building REST APIs with Express.js', w / 2, ctaY + 115);

        // Follow Button
        const btnW = 560;
        const btnH = 90;
        const btnY = ctaY + 175;
        const btnX = (w - btnW) / 2;

        const pulseScale = 1.0 + Math.sin(time * 5) * 0.03;
        ctx.save();
        ctx.translate(w / 2, btnY + btnH / 2);
        ctx.scale(pulseScale, pulseScale);

        this.drawRoundedRect(ctx, -btnW / 2, -btnH / 2, btnW, btnH, 24);
        const btnGrad = ctx.createLinearGradient(-btnW / 2, 0, btnW / 2, 0);
        btnGrad.addColorStop(0, '#22c55e');
        btnGrad.addColorStop(1, '#06b6d4');
        ctx.fillStyle = btnGrad;
        ctx.shadowColor = '#22c55e';
        ctx.shadowBlur = 25;
        ctx.fill();

        ctx.font = '900 34px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('FOLLOW FOR DAY 2! 🔔', 0, 0);
        ctx.restore();

        // Channel watermark & hashtag
        ctx.font = '700 22px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('#100DaysOfBackend • Share with Friends 💬', w / 2, ctaY + 335);

        ctx.font = '600 18px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#64748b';
        ctx.fillText('Comment "CODE" to get Day 1 GitHub Repo link!', w / 2, ctaY + 385);

        ctx.restore();
    }

    // =========================================================================
    // GENERAL DRAWING UTILITIES
    // =========================================================================
    drawRoundedRect(ctx, x, y, width, height, radius, topOnly = false, bottomOnly = false) {
        ctx.beginPath();
        if (topOnly) {
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + width - radius, y);
            ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            ctx.lineTo(x + width, y + height);
            ctx.lineTo(x, y + height);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
        } else {
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + width - radius, y);
            ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            ctx.lineTo(x + width, y + height - radius);
            ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
            ctx.lineTo(x + radius, y + height);
            ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
        }
        ctx.closePath();
    }
}

// Export for browser
if (typeof window !== 'undefined') {
    window.NodeReelRenderer = NodeReelRenderer;
    window.ReelRenderer = NodeReelRenderer;
}
if (typeof module !== 'undefined') {
    module.exports = NodeReelRenderer;
}
