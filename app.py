import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NEON AI COACH FIX", layout="wide")

html_code = """
<div id="app-shell" style="background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); font-family: 'Segoe UI', sans-serif; padding: 20px; border-radius: 30px; color: white; max-width: 1000px; margin: auto; border: 1px solid rgba(255,255,255,0.1);">

    <!-- HEADER -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 0 10px;">
        <div>
            <h1 style="margin: 0; background: linear-gradient(to right, #00d4ff, #00ff87); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2em; letter-spacing: 2px;">NEON AI COACH</h1>
            <p style="margin: 0; color: #888; font-size: 0.8em;">CAMERA FIX VERSION</p>
        </div>
        <div id="status-pulse" style="width: 20px; height: 20px; background: #00ff87; border-radius: 50%; box-shadow: 0 0 15px #00ff87;"></div>
    </div>

    <!-- METRIKEN BOARD -->
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); padding: 15px; border-radius: 20px; border: 1px solid rgba(0,212,255,0.3); text-align: center;">
            <div style="font-size: 0.7em; color: #00d4ff;">WINKEL L / R</div>
            <div id="angle-display" style="font-size: 1.5em; font-weight: bold;">--° / --°</div>
        </div>
        <div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); padding: 15px; border-radius: 20px; border: 1px solid rgba(0,255,135,0.3); text-align: center;">
            <div style="font-size: 0.7em; color: #00ff87;">RÜCKEN</div>
            <div id="back-display" style="font-size: 1.2em; font-weight: bold; color: #00ff87;">--</div>
        </div>
        <div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); padding: 15px; border-radius: 20px; border: 1px solid rgba(255,170,0,0.3); text-align: center;">
            <div style="font-size: 0.7em; color: #ffaa00;">REPS | BEST</div>
            <div id="rep-display" style="font-size: 1.5em; font-weight: bold;">0 | --°</div>
        </div>
    </div>

    <!-- VIDEO -->
    <div style="position: relative; border-radius: 25px; overflow: hidden; background: #000;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto; transition: opacity 0.5s;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none;"></canvas>
    </div>

    <!-- STEUERUNG -->
    <div style="display: flex; gap: 15px; margin-top: 25px;">
        <button id="main-btn" style="flex: 2; padding: 18px; background: linear-gradient(to right, #00d4ff, #0080ff); color: white; border: none; border-radius: 15px; cursor: pointer; font-weight: bold; font-size: 1.1em;">START TRAINING</button>
        <button id="switch-btn" style="flex: 1; padding: 18px; background: #444; color: white; border: none; border-radius: 15px; cursor: pointer; font-weight: bold;">📷 KAMERA WECHSELN</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const angleDisplay = document.getElementById('angle-display');
const backDisplay = document.getElementById('back-display');
const repDisplay = document.getElementById('rep-display');
const mainBtn = document.getElementById('main-btn');
const switchBtn = document.getElementById('switch-btn');

let detector, currentFacingMode = 'environment', recording = false;
let repCount = 0, stage = 'up', minAngle = 180;
let smoothL = 180, smoothR = 180;

function getAngle(a, b, c) {
    let r = Math.atan2(c.y-b.y, c.x-b.x) - Math.atan2(a.y-b.y, a.x-b.x);
    let d = Math.abs(r * 180 / Math.PI); return d > 180 ? 360 - d : d;
}

async function startStream() {
    // CRITICAL FIX: Alle alten Tracks stoppen, bevor neue Kamera angefordert wird
    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }

    try {
        const constraints = {
            video: { 
                facingMode: { exact: currentFacingMode } 
            }
        };
        // Fallback: Wenn 'exact' fehlschlägt (manche Browser), normales facingMode nutzen
        const stream = await navigator.mediaDevices.getUserMedia(constraints)
            .catch(() => navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode } }));
        
        video.srcObject = stream;
        return new Promise(resolve => { video.onloadedmetadata = () => resolve(); });
    } catch (err) {
        console.error("Kamerafehler:", err);
        alert("Kamera konnte nicht gewechselt werden. Prüfe die Berechtigungen im Browser!");
    }
}

async function init() {
    detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet);
    await startStream();
    detect();
}

async function detect() {
    if (video.readyState >= 2) {
        const poses = await detector.estimatePoses(video);
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (poses.length > 0) {
            const kp = poses[0].keypoints;
            const sR = kp[6], hL = kp[11], hR = kp[12], kL = kp[13], kR = kp[14], aL = kp[15], aR = kp[16];

            if (hL.score > 0.3 && hR.score > 0.3) {
                const angL = getAngle(hL, kL, aL);
                const angR = getAngle(hR, kR, aR);
                const backAng = getAngle(sR, hR, kR);

                smoothL = smoothL * 0.6 + angL * 0.4;
                smoothR = smoothR * 0.6 + angR * 0.4;
                const avgKnee = (smoothL + smoothR) / 2;

                angleDisplay.innerText = `${Math.round(smoothL)}° / ${Math.round(smoothR)}°`;

                if (recording) {
                    if (avgKnee < 105) stage = 'down';
                    if (avgKnee > 150 && stage === 'down') { repCount++; stage = 'up'; }
                    if (avgKnee < minAngle) minAngle = Math.round(avgKnee);
                    repDisplay.innerText = `${repCount} | ${minAngle}°`;
                    backDisplay.innerText = backAng < 145 ? "KRUMM" : "OK";
                    backDisplay.style.color = backAng < 145 ? "#ff4b4b" : "#00ff87";
                }

                ctx.lineWidth = 6; ctx.strokeStyle = '#00d4ff';
                ctx.beginPath(); ctx.moveTo(hL.x, hL.y); ctx.lineTo(kL.x, kL.y); ctx.lineTo(aL.x, aL.y); ctx.stroke();
                ctx.strokeStyle = '#00ff87';
                ctx.beginPath(); ctx.moveTo(hR.x, hR.y); ctx.lineTo(kR.x, kR.y); ctx.lineTo(aR.x, aR.y); ctx.stroke();
            }
        }
    }
    requestAnimationFrame(detect);
}

mainBtn.onclick = () => {
    recording = !recording;
    mainBtn.innerText = recording ? "STOP & ANALYSE" : "START TRAINING";
    mainBtn.style.background = recording ? "#ff4b4b" : "linear-gradient(to right, #00d4ff, #0080ff)";
    if (!recording) alert("Training beendet! Reps: " + repCount + " | Tiefe: " + minAngle + "°");
};

switchBtn.onclick = async () => {
    currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
    await startStream();
};

init();
</script>
"""

components.html(html_code, height=1000)
