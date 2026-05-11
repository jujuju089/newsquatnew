import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Multi-Coach", layout="wide")

html_code = """
<div id="app-shell" style="background: #000; font-family: 'Arial', sans-serif; padding: 15px; border-radius: 25px; color: white; max-width: 900px; margin: auto; border: 2px solid #333;">

    <!-- HEADER & MODE SWITCH -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h2 id="title-text" style="color: #00d4ff; margin: 0;">NEON CYBER MODE</h2>
        <select id="mode-select" style="padding: 8px; border-radius: 10px; background: #222; color: white; border: 1px solid #00d4ff;">
            <option value="cyber">Cyber Modus (Seriös)</option>
            <option value="trainer">Schätzelein Modus (Anzüglich)</option>
        </select>
    </div>

    <!-- STATS BARS -->
    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <div style="flex: 1; background: #111; padding: 10px; border-radius: 15px; text-align: center; border-bottom: 3px solid #00d4ff;">
            <small>WINKEL</small><br><b id="deg-val">--°</b>
        </div>
        <div style="flex: 1; background: #111; padding: 10px; border-radius: 15px; text-align: center; border-bottom: 3px solid #00ff87;">
            <small>REPS</small><br><b id="rep-val">0</b>
        </div>
        <div style="flex: 1; background: #111; padding: 10px; border-radius: 15px; text-align: center; border-bottom: 3px solid #ff4b4b;">
            <small>RÜCKEN</small><br><b id="back-val">OK</b>
        </div>
    </div>

    <!-- CAMERA VIEW -->
    <div style="position: relative; border-radius: 20px; overflow: hidden; background: #050505;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    </div>

    <!-- CONTROLS -->
    <div style="display: flex; gap: 10px; margin-top: 15px;">
        <button id="start-btn" style="flex: 2; padding: 15px; border-radius: 15px; border: none; background: #00ff87; font-weight: bold; cursor: pointer;">TRAINING STARTEN</button>
        <button id="ghost-btn" style="flex: 1; padding: 15px; border-radius: 15px; border: 1px solid #444; background: #222; color: white;">GHOST</button>
        <button id="cam-btn" style="padding: 15px; border-radius: 15px; background: #333; color: white; border: none;">📷</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const modeSelect = document.getElementById('mode-select');

let detector, recording = false, ghost = false, currentFacingMode = 'environment';
let reps = 0, stage = 'up', lastSpeak = 0;

const phrases = {
    cyber: { start: "System bereit. Beginne Training.", depth: "Optimale Tiefe.", rep: (n) => n, back: "Haltung korrigieren!" },
    trainer: { start: "Na, dann zeig mal was du hast, Schätzelein!", depth: "Oh ja, so tief gefällt mir das!", rep: (n) => n + ". Das machst du super, Süßer!", back: "Nicht so krumm werden, Schätzchen!" }
};

function speak(t) {
    if (Date.now() - lastSpeak > 2500) {
        const m = new SpeechSynthesisUtterance(t); m.lang = 'de-DE';
        window.speechSynthesis.speak(m); lastSpeak = Date.now();
    }
}

function getAngle(a, b, c) {
    let r = Math.atan2(c.y-b.y, c.x-b.x) - Math.atan2(a.y-b.y, a.x-b.x);
    let d = Math.abs(r * 180 / Math.PI); return d > 180 ? 360 - d : d;
}

async function setupCam() {
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode } });
    video.srcObject = s;
}

async function init() {
    detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet);
    await setupCam();
    loop();
}

async function loop() {
    if (video.readyState >= 2) {
        const poses = await detector.estimatePoses(video);
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (poses.length > 0) {
            const kp = poses[0].keypoints;
            const sL = kp[5], sR = kp[6], hL = kp[11], hR = kp[12], kL = kp[13], kR = kp[14], aL = kp[15], aR = kp[16];

            if (hR.score > 0.3 && kR.score > 0.3) {
                const ang = getAngle(hR, kR, aR);
                const back = getAngle(sR, hR, kR);
                const mode = modeSelect.value;

                document.getElementById('deg-val').innerText = Math.round(ang) + "°";

                if (recording) {
                    if (ang < 100 && stage === 'up') { 
                        stage = 'down'; speak(phrases[mode].depth); 
                    }
                    if (ang > 150 && stage === 'down') { 
                        reps++; stage = 'up'; 
                        speak(phrases[mode].rep(reps));
                        document.getElementById('rep-val').innerText = reps;
                    }
                    if (back < 140) {
                        document.getElementById('back-val').innerText = "KRUMM";
                        speak(phrases[mode].back);
                    } else {
                        document.getElementById('back-val').innerText = "OK";
                    }
                }

                // SKELETT ZEICHNEN
                ctx.lineWidth = 5; ctx.shadowBlur = 15;
                const color = mode === 'cyber' ? "#00d4ff" : "#ff00ff";
                ctx.strokeStyle = color; ctx.shadowColor = color;

                // Linien
                const drawLine = (p1, p2) => {
                    if(p1.score > 0.3 && p2.score > 0.3) {
                        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
                    }
                };
                drawLine(sL, sR); drawLine(sL, hL); drawLine(sR, hR);
                drawLine(hL, kL); drawLine(kL, aL); drawLine(hR, kR); drawLine(kR, aR);

                // GELENKPUNKTE (WEISS & GLOW)
                ctx.fillStyle = "white"; ctx.shadowColor = "white";
                [sL, sR, hL, hR, kL, kR, aL, aR].forEach(p => {
                    if(p.score > 0.3) { ctx.beginPath(); ctx.arc(p.x, p.y, 6, 0, 7); ctx.fill(); }
                });
            }
        }
    }
    requestAnimationFrame(loop);
}

document.getElementById('start-btn').onclick = () => {
    recording = !recording;
    const btn = document.getElementById('start-btn');
    btn.innerText = recording ? "STOP" : "TRAINING STARTEN";
    btn.style.background = recording ? "#ff4b4b" : "#00ff87";
    if (recording) {
        reps = 0; document.getElementById('rep-val').innerText = "0";
        speak(phrases[modeSelect.value].start);
    }
};

document.getElementById('ghost-btn').onclick = () => {
    ghost = !ghost; video.style.opacity = ghost ? "0" : "1";
};

document.getElementById('cam-btn').onclick = async () => {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    await setupCam();
};

modeSelect.onchange = () => {
    const isCyber = modeSelect.value === 'cyber';
    document.getElementById('title-text').innerText = isCyber ? "NEON CYBER MODE" : "SCHÄTZELEIN TRAINER";
    document.getElementById('title-text').style.color = isCyber ? "#00d4ff" : "#ff00ff";
};

init();
</script>
"""

components.html(html_code, height=1000)
