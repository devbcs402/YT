const { execSync } = require('child_process');
const path = require('path');
const ffmpeg = path.join(__dirname, 'node_modules', 'ffmpeg-static', 'ffmpeg.exe');

const scenes = ['scene1_hook', 'scene2_intro', 'scene3_how_it_works', 'scene4_code_demo', 'scene5_outro'];
let totalVoiceSec = 0;
for (const s of scenes) {
  const p = path.join(__dirname, 'assets', 'voice', s, 'audio.mp3');
  try {
    execSync(`"${ffmpeg}" -i "${p}"`, { stdio: 'pipe' });
  } catch (err) {
    const out = err.stderr ? err.stderr.toString() : '';
    const m = out.match(/Duration:\s*(\d+):(\d+):([\d.]+)/);
    if (m) {
      const sec = parseFloat(m[1]) * 3600 + parseFloat(m[2]) * 60 + parseFloat(m[3]);
      console.log(`${s}: ${sec.toFixed(2)}s`);
      totalVoiceSec += sec;
    }
  }
}
console.log(`Total voice duration: ${totalVoiceSec.toFixed(2)}s`);
