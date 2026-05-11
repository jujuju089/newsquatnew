import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Power Coach", layout="wide")

html_code = """
<div id="app-shell" style="background: #000; font-family: 'Arial Black', sans-serif; padding: 15px; border-radius: 25px; color: white; max-width: 900px; margin: auto; border: 2px solid #333; box-shadow: 0 0 30px rgba(255,255,255,0.1);">

    <!-- HEADER & MODE SWITCH -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h2 id="title-text" style="color: #00ff87; margin: 0; font-style: italic;">PUMP & GAINS</h2>
        <select id="mode-select" style="padding: 10px; border-radius: 10px; background: #222; color: white; border: 1px solid #444;">
            <option value="cyber">🤖 Cyber Modus</option>
            <option value="trainer">😘 Schätzelein Modus</option>
            <option value="mcfit">💪 McFit (Hardcore)</option>
        </select>
    </div>

    <!-- STATS -->
    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <div style="flex: 1; background: #111; padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #444;">
            <small style="color: #888;">KNIE</small><br><b id="deg-val" style="font-size: 1.4em;">--°</b>
        </div>
        <div style="flex: 1; background: #111; padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #444;">
            <small style="color: #888;">WDKH</small><br><b id="rep-val" style="font-size: 1.4em; color: #00ff87;">0</b>
        </div>
        <div style="flex: 1; background: #111; padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #444;">
            <small style="color: #888;">RÜCKEN</small><br><b id="back-val" style="font-size: 1.2em;">OK</b>
        </div>
    </div>

    <!-- VIEWPORT -->
    <div style="position: relative; border-radius: 20px; overflow: hidden; background: #050505;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    </div>

    <!-- AUDIO (HIDDEN) -->
    <audio id="fight-snd" src="https://www.zapsplat.com/wp-content/uploads/2015/sound-effects-one/human_grunt_effort_strong_001.mp3"></audio>
    <audio id="gym-snd" src="https://www.zapsplat.com/wp-content/uploads/2015/sound-effects-one/sport_gym_weight_plate_clank_drop_001.mp3"></audio>

    <!-- CONTROLS -->
    <div style="display: flex; gap: 10px; margin-top: 15px;">
        <button id="start-btn" style="flex: 2; padding: 18px; border-radius: 15px; border: none; background: #00ff87; font-weight: bold; cursor: pointer; font-size: 1.1em;">SESSION STARTEN</button>
        <button id="cam-btn" style="padding: 15px; border-radius: 15px; background: #333; color: white; border: none; width: 60px;">📷</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const modeSelect = document.getElementById('mode-select');
const fightSnd = document.getElementById('fight-snd');
const gymSnd = document.getElementById('gym-snd');

let detector, recording = false, currentFacingMode = 'environment';
let reps = 0, stage = 'up', lastSpeak = 0;

const phrases = {
    cyber: { start: "System aktiv.", depth: "Tiefe erreicht.", rep: (n) => n, back: "Haltung!" },
    trainer: { start: "Zeig mir die Muskeln, Schätzelein!", depth: "Oh ja, so tief!", rep: (n) => n + ". Super, Süßer!", back: "Nicht krumm werden, Schätzchen!" },
    mcfit: { start: "KEINE AUSREDEN! PUMP!", depth: "", rep: (n) => n + "! WEITER!", back: "RÜCKEN GERADE, DU LAUCH!" }
};

function speak(t) {
    if (Date.now() - lastSpeak > 2000) {
        const m = new SpeechSynthesisUtterance(t); m.lang = 'de-DE';
        m.pitch = modeSelect.value === 'mcfit' ? 0.8 : 1.2;
        window.speechSynthesis.speak(m); lastSpeak = Date.now();
    }
}

function playFight() {
    if (modeSelect.value === 'mcfit') {
        fightSnd.currentTime = 0; fightSnd.play();
        setTimeout(() => { gymSnd.currentTime = 0; gymSnd.play(); }, 300);
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
            const sR = kp[6], hR = kp[12], kR = kp[14], aR = kp[16];

            if (hR.score > 0.3 && kR.score > 0.3) {
                const ang = getAngle(hR, kR, aR);
                const back = getAngle(sR, hR, kR);
                const mode = modeSelect.value;

                document.getElementById('deg-val').innerText = Math.round(ang) + "°";

                if (recording) {
                    if (ang < 100 && stage === 'up') { 
                        stage = 'down'; 
                        if(mode !== 'mcfit') speak(phrases[mode].depth); 
                    }
                    if (ang > 150 && stage === 'down') { 
                        reps++; stage = 'up'; 
                        playFight(); // Kampfgeräusche im McFit Modus
                        speak(phrases[mode].rep(reps));
                        document.getElementById('rep-val').innerText = reps;
                    }
                    // TOLERANZ FIX: Rücken erst ab 130° als krumm werten
                    if (back < 130) { 
                        document.getElementById('back-val').innerText = "KRUMM";
                        document.getElementById('back-val').style.color = "red";
                        speak(phrases[mode].back);
                    } else {
                        document.getElementById('back-val').innerText = "OK";
                        document.getElementById('back-val').style.color = "#00ff87";
                    }
                }

                // SKELETT
                ctx.lineWidth = 6; ctx.strokeStyle = mode === 'mcfit' ? "#ff0000" : (mode === 'trainer' ? "#ff00ff" : "#00d4ff");
                ctx.shadowBlur = 10; ctx.shadowColor = ctx.strokeStyle;
                
                // Zeichne Punkte & Linien
                [sR, hR, kR, aR].forEach(p => {
                    if(p.score > 0.3) {
                        ctx.fillStyle = "white";
                        ctx.beginPath(); ctx.arc(p.x, p.y, 8, 0, 7); ctx.fill();
                    }
                });
                ctx.beginPath(); ctx.moveTo(sR.x, sR.y); ctx.lineTo(hR.x, hR.y); 
                ctx.lineTo(kR.x, kR.y); ctx.lineTo(aR.x, aR.y); ctx.stroke();
            }
        }
    }
    requestAnimationFrame(loop);
}

document.getElementById('start-btn').onclick = () => {
    recording = !recording;
    document.getElementById('start-btn').innerText = recording ? "STOP" : "SESSION STARTEN";
    document.getElementById('start-btn').style.background = recording ? "#ff4b4b" : "#00ff87";
    if (recording) { reps = 0; speak(phrases[modeSelect.value].start); }
};

document.getElementById('cam-btn').onclick = async () => {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    await setupCam();
};

init();
</script>
"""

components.html(html_code, height=1000)
