import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Multi-Coach Pro", layout="wide")

html_code = """
<div id="app-shell" style="transition: all 0.5s; padding: 15px; border-radius: 25px; color: white; max-width: 900px; margin: auto; border: 3px solid rgba(255,255,255,0.1); min-height: 800px; position: relative; overflow: hidden;">

    <!-- BACKGROUND LAYER -->
    <div id="bg-overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; z-index: -1; transition: all 0.8s; background-size: cover; background-position: center;"></div>

    <!-- HEADER & MODE SELECT -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 15px;">
        <h2 id="title-text" style="margin: 0; font-style: italic; text-transform: uppercase;">TRAINING SYSTEM</h2>
        <select id="mode-select" style="padding: 10px; border-radius: 8px; background: #222; color: white; border: 1px solid #fff;">
            <option value="forest">🌲 Wald-Ruhe (Zen)</option>
            <option value="mcfit">🏋️ McFit (Pumping Iron)</option>
            <option value="hardcore">💀 Hammer Hardcore (Brutal)</option>
            <option value="cyber">🤖 Cyber (Technisch)</option>
        </select>
    </div>

    <!-- STATS -->
    <div style="display: flex; gap: 8px; margin-bottom: 10px;">
        <div style="flex: 1; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.2);">
            <small>WINKEL</small><br><b id="deg-val" style="font-size: 1.5em;">--°</b>
        </div>
        <div style="flex: 1; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 10px; text-align: center; border: 2px solid #fff;" id="rep-box">
            <small>REPS</small><br><b id="rep-val" style="font-size: 2em;">0</b>
        </div>
        <div style="flex: 1; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 10px; text-align: center; border: 1px solid rgba(255,255,255,0.2);">
            <small>HALTUNG</small><br><b id="back-val">OK</b>
        </div>
    </div>

    <!-- VIDEO VIEW -->
    <div style="position: relative; border-radius: 15px; overflow: hidden; background: #000; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto; transition: opacity 0.5s;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    </div>

    <!-- AUDIO ELEMENTS -->
    <audio id="metal-snd" src="https://www.zapsplat.com/wp-content/uploads/2015/sound-effects-one/sport_gym_weight_plate_clank_drop_001.mp3"></audio>
    <audio id="bird-snd" loop src="https://www.zapsplat.com/wp-content/uploads/2015/sound-effects-three/animals_birds_woodland_loop_001.mp3"></audio>

    <!-- UI BUTTONS -->
    <div style="display: flex; gap: 10px; margin-top: 15px;">
        <button id="start-btn" style="flex: 3; padding: 20px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; font-size: 1.2em; transition: all 0.3s;">TRAINING STARTEN</button>
        <button id="cam-btn" style="flex: 1; padding: 15px; border-radius: 12px; background: rgba(0,0,0,0.7); color: white; border: 1px solid #fff;">📷</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const modeSelect = document.getElementById('mode-select');
const bgOverlay = document.getElementById('bg-overlay');
const birdSnd = document.getElementById('bird-snd');
const metalSnd = document.getElementById('metal-snd');

let detector, recording = false, currentFacingMode = 'environment';
let reps = 0, stage = 'up', lastSpeak = 0;

const configs = {
    forest: { 
        color: "#2ecc71", 
        title: "WALD-RUHE",
        bg: "linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url('https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1000&q=80')",
        start: "Atme tief ein. Wir beginnen die Wald-Session.",
        rep: (n) => n + ". Sehr harmonisch.",
        back: "Bleib aufrecht wie eine Tanne.",
        rate: 0.8, pitch: 1.0
    },
    mcfit: { 
        color: "#fbff00", 
        title: "MCFIT PUMP",
        bg: "linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1000&q=80')",
        start: "McFit Modus aktiv. Pump das Eisen!",
        rep: (n) => n + "! WEITER!",
        back: "Rücken gerade, keine Ausreden!",
        rate: 1.0, pitch: 0.8
    },
    hardcore: { 
        color: "#ff0000", 
        title: "HAMMER HARDCORE",
        bg: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?auto=format&fit=crop&w=1000&q=80')",
        start: "LEIDEN ZEIT! BEWEG DICH!",
        rep: (n) => n + "! NOCH EINE DU VERSAGER!",
        back: "GERADE BLEIBEN ODER ABHAUEN!",
        rate: 1.4, pitch: 0.6
    },
    cyber: { 
        color: "#00d4ff", 
        title: "CYBER CORE",
        bg: "linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url('https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80')",
        start: "System initialisiert.",
        rep: (n) => n,
        back: "Haltungskorrektur erforderlich.",
        rate: 1.0, pitch: 1.2
    }
};

function updateUI() {
    const c = configs[modeSelect.value];
    bgOverlay.style.backgroundImage = c.bg;
    document.getElementById('title-text').innerText = c.title;
    document.getElementById('title-text').style.color = c.color;
    document.getElementById('start-btn').style.backgroundColor = c.color;
    document.getElementById('rep-box').style.borderColor = c.color;
    
    if (modeSelect.value === 'forest') { birdSnd.play(); } else { birdSnd.pause(); }
}

function speak(t) {
    if (Date.now() - lastSpeak > 2000) {
        const m = new SpeechSynthesisUtterance(t);
        const c = configs[modeSelect.value];
        m.lang = 'de-DE'; m.rate = c.rate; m.pitch = c.pitch;
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
    updateUI();
    loop();
}

async function loop() {
    if (video.readyState >= 2) {
        const poses = await detector.estimatePoses(video);
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (poses.length > 0) {
            const kp = poses[0].keypoints;
            const sR = kp[6], hR = kp[12], kR = kp[14], aR = kp[16];

            if (hR.score > 0.3 && kR.score > 0.3) {
                const ang = getAngle(hR, kR, aR);
                const back = getAngle(sR, hR, kR);
                const config = configs[modeSelect.value];

                document.getElementById('deg-val').innerText = Math.round(ang) + "°";

                if (recording) {
                    if (ang < 95 && stage === 'up') { stage = 'down'; }
                    if (ang > 155 && stage === 'down') { 
                        reps++; stage = 'up'; 
                        if (modeSelect.value === 'mcfit' || modeSelect.value === 'hardcore') metalSnd.play();
                        speak(config.rep(reps));
                        document.getElementById('rep-val').innerText = reps;
                    }
                    
                    if (back < 115) { 
                        document.getElementById('back-val').innerText = "❌ KORREKTUR";
                        speak(config.back);
                    } else {
                        document.getElementById('back-val').innerText = "✅ OK";
                    }
                }

                ctx.lineWidth = 8; ctx.strokeStyle = config.color;
                ctx.shadowBlur = 15; ctx.shadowColor = "black";
                
                const points = [sR, hR, kR, aR];
                ctx.beginPath(); ctx.moveTo(points[0].x, points[0].y);
                for(let i=1; i<points.length; i++) ctx.lineTo(points[i].x, points[i].y);
                ctx.stroke();

                points.forEach(p => {
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(p.x, p.y, 10, 0, 7); ctx.fill();
                });
            }
        }
    }
    requestAnimationFrame(loop);
}

document.getElementById('start-btn').onclick = () => {
    recording = !recording;
    document.getElementById('start-btn').innerText = recording ? "STOP" : "STARTEN";
    if (recording) { reps = 0; speak(configs[modeSelect.value].start); }
};

document.getElementById('cam-btn').onclick = async () => {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    await setupCam();
};

modeSelect.onchange = updateUI;

init();
</script>
"""

components.html(html_code, height=1000)
