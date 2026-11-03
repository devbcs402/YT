const fs = require('fs');
const path = require('path');

const scenes = [
  {
    id: 1,
    name: 'scene1_hook',
    enMap: [
      { hi: "JavaScript se sirf websites banti hain?", en: "JavaScript only makes websites?" },
      { hi: "Bilkul nahi!", en: "Not at all!" },
      { hi: "Aap JavaScript se powerful backend servers bhi bana sakte ho!", en: "You can build powerful backend servers with JavaScript too!" }
    ]
  },
  {
    id: 2,
    name: 'scene2_intro',
    enMap: [
      { hi: "Iska secret hai Node.js!", en: "The secret is Node.js!" },
      { hi: "Ye ek JavaScript runtime environment hai, jo aapko browser ke bahar JavaScript run karne deta hai.", en: "It's a JavaScript runtime environment that lets you run JavaScript outside the browser!" }
    ]
  },
  {
    id: 3,
    name: 'scene3_how_it_works',
    enMap: [
      { hi: "Ab Node.js ki help se aap APIs bana sakte ho, database se connect kar sakte ho, aur client ki requests handle kar sakte ho.", en: "With Node.js, you can build APIs, connect to databases, and handle client requests!" }
    ]
  },
  {
    id: 4,
    name: 'scene4_code_demo',
    enMap: [
      { hi: "Example dekho!", en: "Check this example!" },
      { hi: "Sirf kuch lines mein hum apna pehla Node.js HTTP server bana sakte hain.", en: "In just a few lines, we can build our first Node.js HTTP server." }
    ]
  },
  {
    id: 5,
    name: 'scene5_outro',
    enMap: [
      { hi: "Toh ab JavaScript sirf frontend tak limited nahi hai!", en: "So JavaScript is no longer limited to frontend!" },
      { hi: "Ye backend development ka bhi powerful tool hai.", en: "It's a powerful tool for backend development too!" },
      { hi: "Follow karo aur chalo saath mein complete 100-day challenge karte hain!", en: "Follow along and let's complete the 100-day challenge together!" }
    ]
  }
];

const timings = [];
let accumulatedTime = 0.0;

for (const s of scenes) {
  const p = path.join(__dirname, 'assets', 'voice', s.name, 'metadata.json');
  const d = JSON.parse(fs.readFileSync(p, 'utf8'));
  const sents = d.Metadata.filter(m => m.Type === 'SentenceBoundary');
  const words = d.Metadata.filter(m => m.Type === 'WordBoundary');
  
  // Calculate scene duration based on words or sentences
  const lastWord = words[words.length - 1];
  const sceneDur = lastWord ? (lastWord.Data.Offset + lastWord.Data.Duration) / 10000000 + 0.3 : 10.0;
  
  console.log(`\n=== ${s.name} (Start: ${accumulatedTime.toFixed(2)}s, Duration: ${sceneDur.toFixed(2)}s) ===`);
  
  const mappedSents = sents.map((sent, idx) => {
    const startSec = sent.Data.Offset / 10000000;
    const durSec = sent.Data.Duration / 10000000;
    const globalStart = accumulatedTime + startSec;
    const globalEnd = accumulatedTime + startSec + durSec;
    const enText = (s.enMap[idx] && s.enMap[idx].en) || sent.Data.text.Text;
    console.log(`  [${globalStart.toFixed(2)}s -> ${globalEnd.toFixed(2)}s] "${sent.Data.text.Text}" => "${enText}"`);
    return {
      textHi: sent.Data.text.Text,
      textEn: enText,
      localStart: startSec,
      localEnd: startSec + durSec,
      globalStart,
      globalEnd
    };
  });

  timings.push({
    sceneId: s.id,
    sceneName: s.name,
    sceneStart: accumulatedTime,
    sceneEnd: accumulatedTime + sceneDur,
    sceneDuration: sceneDur,
    sentences: mappedSents
  });

  accumulatedTime += sceneDur;
}

console.log(`\nTotal Timeline Duration: ${accumulatedTime.toFixed(2)}s`);
fs.writeFileSync(path.join(__dirname, 'timeline_data.json'), JSON.stringify(timings, null, 2));
