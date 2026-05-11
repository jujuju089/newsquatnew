import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NEON AI FINAL", layout="wide")

html_code = """
<div id="app-shell" style="background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); font-family: 'Segoe UI', sans-serif; padding: 20px; border-radius: 30px; color: white; max-width: 1000px; margin: auto; box-shadow: 0 20px 50px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);">

    <!-- HEADER -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0; background: linear-gradient(to right, #00d4ff, #00ff87); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.8em;">NEON COACH PRO</h1>
        <div id="pulse" style="width: 15px; height: 15px; background: #00ff87; border-radius: 50%; box-shadow: 0 0 15px #00ff87;"></div>
    </div>

    <!-- DASHBOARD -->
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 15px;">
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #00d4ff;">
            <small style="color: #00d4ff;">KNIE L/R</small><br><b id="angle-val">-- / --</b>
        </div>
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #00ff87;">
            <small style="color: #00ff87;">RÜCKEN</small><br><b id="back-val">WAIT</b>
        </div>
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 15px; text-align: center; border: 1px solid #ffaa00;">
            <small style="color: #ffaa00;">REPS | BEST</small><br><b id="rep-val">0 | --</b>
        </div>
    </div>

    <!-- VIEWPORT -->
    <div style="position: relative; border-radius: 20px; overflow: hidden; background: #000; line-height: 0;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto; transition: opacity 0.4s;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none;"></canvas>
    </div>

    <!-- CONTROLS -->
    <div style="display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap;">
        <button id="start-btn" style="flex: 2; padding: 15px; background: #00ff87; color: #000; border: none; border-radius: 12px; font-weight: bold; cursor: pointer;">START</button>
        <button id="ghost-btn" style="flex: 1; padding: 15px; background: #444; color: #fff; border: none; border-radius: 12px; cursor: pointer;">GHOST MODE</button>
        <button id="switch-btn" style="padding: 15px; background: #222; color: #fff; border: 1px solid #444; border-radius: 12px; cursor: pointer;">📷</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let detector, recording = false, ghost = false, currentFacingMode = 'environment';
let reps = 0, stage = 'up', best = 180, lastSpeak = 0;

function speak(text) {
    if (Date.now() - lastSpeak > 3000) {
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'de-DE';
        window.speechSynthesis.speak(msg);
        lastSpeak = Date.now();
    }
}

function getAngle(a, b, c) {
    let r = Math.atan2(c.y-b.y, c.x-b.x) - Math.atan2(a.y-b.y, a.x-b.x);
    let d = Math.abs(r * 180 / Math.PI); return d > 180 ? 360 - d : d;
}

async function setupCam() {
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode } });
    video.srcObject = stream;
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

            if (hL.score > 0.3 && hR.score > 0.3) {
                const angL = getAngle(hL, kL, aL);
                const angR = getAngle(hR, kR, aR);
                const backAng = getAngle(sR, hR, kR);
                const avg = (angL + angR) / 2;

                document.getElementById('angle-val').innerText = Math.round(angL) + " / " + Math.round(angR);

                if (recording) {
                    if (avg < 105) { stage = 'down'; speak("Gute Tiefe"); }
                    if (avg > 150 && stage === 'down') { reps++; stage = 'up'; speak(reps); }
                    if (avg < best) best = Math.round(avg);
                    
                    document.getElementById('rep-val').innerText = reps + " | " + best + "°";
                    document.getElementById('back-val').innerText = backAng < 145 ? "KRUMM" : "GERADE";
                    if (backAng < 145) speak("Rücken gerade");
                }

                // ZEICHNEN
                ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.shadowBlur = 10; ctx.shadowColor = "#00d4ff";
                
                // Beine & Rücken
                ctx.strokeStyle = "#00d4ff";
                ctx.beginPath(); ctx.moveTo(hL.x, hL.y); ctx.lineTo(kL.x, kL.y); ctx.lineTo(aL.x, aL.y); ctx.stroke();
                ctx.strokeStyle = "#00ff87";
                ctx.beginPath(); ctx.moveTo(hR.x, hR.y); ctx.lineTo(kR.x, kR.y); ctx.lineTo(aR.x, aR.y); ctx.stroke();
                
                // Schultern & Rücken (NEU: Sichtbare Schulterpunkte)
                ctx.strokeStyle = "#ffffff";
                ctx.beginPath(); ctx.moveTo(sL.x, sL.y); ctx.lineTo(sR.x, sR.y); ctx.stroke(); // Schulterlinie
                ctx.beginPath(); ctx.moveTo(sR.x, sR.y); ctx.lineTo(hR.x, hR.y); ctx.stroke(); // Rückenzug
                
                // Gelenkpunkte
                ctx.fillStyle = "white";
                [sL, sR, hL, hR, kL, kR, aL, aR].forEach(p => {
                    if(p.score > 0.3) { ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, 7); ctx.fill(); }
                });
            }
        }
    }
    requestAnimationFrame(loop);
}

document.getElementById('start-btn').onclick = () => {
    recording = !recording;
    document.getElementById('start-btn').innerText = recording ? "STOP" : "START";
    document.getElementById('start-btn').style.background = recording ? "#ff4b4b" : "#00ff87";
    if (recording) { reps = 0; best = 180; speak("Training gestartet"); }
};

document.getElementById('ghost-btn').onclick = () => {
    ghost = !ghost;
    video.style.opacity = ghost ? "0" : "1";
    document.getElementById('ghost-btn').style.background = ghost ? "#00d4ff" : "#444";
};

document.getElementById('switch-btn').onclick = async () => {
    currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
    await setupCam();
};

init();
</script>
"""

components.html(html_code, height=1000)
