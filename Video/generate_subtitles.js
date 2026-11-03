const fs = require('fs');
const path = require('path');

const cues = [
  {
    start: 0.50,
    end: 4.17,
    hi: "JavaScript se sirf websites banti hain?",
    en: "Can you only build websites with JavaScript?",
    highlight: "JavaScript"
  },
  {
    start: 4.17,
    end: 5.82,
    hi: "Bilkul nahi!",
    en: "Absolutely not!",
    highlight: "not"
  },
  {
    start: 5.82,
    end: 10.48,
    hi: "Aap JavaScript se powerful backend servers bhi bana sakte ho!",
    en: "You can build powerful backend servers with JavaScript too!",
    highlight: "backend servers"
  },
  {
    start: 10.70,
    end: 13.64,
    hi: "Iska secret hai Node.js!",
    en: "The secret is Node.js!",
    highlight: "Node.js"
  },
  {
    start: 13.64,
    end: 21.45,
    hi: "Ye ek JavaScript runtime environment hai, jo aapko browser ke bahar JavaScript run karne deta hai.",
    en: "It's a JavaScript runtime environment to run JavaScript outside the browser!",
    highlight: "runtime environment"
  },
  {
    start: 21.70,
    end: 26.20,
    hi: "Ab Node.js ki help se aap APIs bana sakte ho, database se connect kar sakte ho...",
    en: "With Node.js, you can build APIs and connect to databases...",
    highlight: "APIs & databases"
  },
  {
    start: 26.20,
    end: 31.20,
    hi: "...aur client ki requests handle kar sakte ho.",
    en: "...and handle real-time client requests!",
    highlight: "client requests"
  },
  {
    start: 31.50,
    end: 33.30,
    hi: "Example dekho!",
    en: "Take a look at this example!",
    highlight: "example"
  },
  {
    start: 33.30,
    end: 40.08,
    hi: "Sirf kuch lines mein hum apna pehla Node.js HTTP server bana sakte hain.",
    en: "In just a few lines, we can build our first Node.js HTTP server.",
    highlight: "HTTP server"
  },
  {
    start: 40.10,
    end: 43.40,
    hi: "Server running on port 3000!",
    en: "Server running on port 3000 • Response 200 OK",
    highlight: "port 3000"
  },
  {
    start: 43.60,
    end: 48.03,
    hi: "Toh ab JavaScript sirf frontend tak limited nahi hai!",
    en: "So JavaScript is no longer limited to the frontend!",
    highlight: "not limited"
  },
  {
    start: 48.03,
    end: 52.14,
    hi: "Ye backend development ka bhi powerful tool hai.",
    en: "It's a powerful tool for modern backend development!",
    highlight: "backend development"
  },
  {
    start: 52.14,
    end: 57.65,
    hi: "Follow karo aur chalo saath mein complete 100-day challenge karte hain!",
    en: "Follow along and let's master the 100-Day Challenge together!",
    highlight: "100-Day Challenge"
  }
];

function toSRTTime(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}

function toVTTTime(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
}

let srtContent = '';
let vttContent = 'WEBVTT\n\n';

cues.forEach((c, idx) => {
  srtContent += `${idx + 1}\n${toSRTTime(c.start)} --> ${toSRTTime(c.end)}\n${c.en}\n\n`;
  vttContent += `${idx + 1}\n${toVTTTime(c.start)} --> ${toVTTTime(c.end)}\n${c.en}\n\n`;
});

fs.writeFileSync(path.join(__dirname, 'assets', 'subtitles.srt'), srtContent);
fs.writeFileSync(path.join(__dirname, 'assets', 'subtitles.vtt'), vttContent);
fs.writeFileSync(path.join(__dirname, 'assets', 'subtitles.json'), JSON.stringify(cues, null, 2));

console.log('✅ Generated subtitles.srt, subtitles.vtt, and subtitles.json successfully!');
