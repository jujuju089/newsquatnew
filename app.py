import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NEON AI COACH", layout="wide")

html_code = """
<div id="app-shell" style="background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); font-family: 'Segoe UI', Roboto, sans-serif; padding: 20px; border-radius: 30px; color: white; max-width: 1000px; margin: auto; box-shadow: 0 20px 50px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);">

    <!-- HEADER -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 0 10px;">
        <div>
            <h1 style="margin: 0; background: linear-gradient(to right, #00d4ff, #00ff87); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2em; letter-spacing: 2px;">NEON AI COACH</h1>
            <p style="margin: 0; color: #888; font-size: 0.8em;">NEXT-GEN MOTION ANALYSIS</p>
        </div>
        <div id="status-pulse" style="width: 20px; height: 20px; background: #00ff87; border-radius: 50%; box-shadow: 0 0 15px #00ff87; animation: pulse 2s infinite;"></div>
    </div>

    <!-- METRIKEN BOARD -->
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); padding: 15px; border-radius: 20px; border: 1px solid rgba(0,212,255,0.3); text-align: center;">
            <div style="font-size: 0.7em; color: #00d4ff;">WINKEL L / R</div>
            <div id="angle-display" style="font-size: 1.5em; font-weight: bold;">--° / --°</div>
        </div>
        <div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); padding: 15px; border-radius: 20px; border: 1px solid rgba(0,255,135,0.3); text-align: center;">
            <div style="font-size: 0.7em; color: #00ff87;">RÜCKEN-LOG</div>
            <div id="back-display" style="font-size: 1.2em; font-weight: bold; color: #00ff87;">OPTIMAL</div>
        </div>
        <div style="background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); padding: 15px; border-radius: 20px; border: 1px solid rgba(255,170,0,0.3); text-align: center;">
            <div style="font-size: 0.7em; color: #ffaa00;">REPS & TIEFE</div>
            <div id="rep-display" style="font-size: 1.5em; font-weight: bold;">0 | --°</div>
        </div>
    </div>

    <!-- HAUPTFENSTER -->
    <div style="position: relative; border-radius: 25px; overflow: hidden; background: #000; border: 2px solid rgba(255,255,255,0.1); box-shadow: inset 0 0 50px rgba(0,212,255,0.2);">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto; transition: opacity 0.5s;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none;"></canvas>
        
        <!-- LIVE FEEDBACK OVERLAY -->
        <div id="hint-box" style="position: absolute; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); padding: 10px 20px; border-radius: 50px; border: 1px solid #00d4ff; font-weight: bold; color: #00d4ff; display: none; z-index: 10;">TIEFER GEHEN</div>
    </div>

    <!-- CONTROLS -->
    <div style="display: flex; gap: 15px; margin-top: 25px; padding-bottom: 10px;">
        <button id="main-btn" style="flex: 2; padding: 18px; background: linear-gradient(to right, #00d4ff, #0080ff); color: white; border: none; border-radius: 15px; cursor: pointer; font-weight: bold; font-size: 1.1em; box-shadow: 0 10px 20px rgba(0,128,255,0.3); transition: transform 0.2s;">START TRAINING</button>
        <button id="ghost-btn" style="flex: 1; padding: 18px; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); border-radius: 15px; cursor: pointer; font-weight: bold;">GHOST MODE</button>
        <button id="switch-btn" style="width: 60px; background: #444; border: none; border-radius: 15px; cursor: pointer; color: white;">📷</button>
    </div>

    <style>
        @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.7; } 70% { transform: scale(1); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.7; } }
        button:active { transform: scale(0.95); }
    </style>
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
const hintBox = document.getElementById('hint-box');
const mainBtn = document.getElementById('main-btn');

let detector, currentFacingMode = 'environment', recording = false, ghostMode = false;
let repCount = 0, stage = 'up', minAngle = 180, lastSpeak = 0;
let smoothL = 180, smoothR = 180;

function speak(t) {
    if (Date.now() - lastSpeak > 3000) {
        const m = new SpeechSynthesisUtterance(t); m.lang = 'de-DE';
        window.speechSynthesis.speak(m); lastSpeak = Date.now();
    }
}

function getAngle(a, b, c) {
    let r = Math.atan2(c.y-b.y, c.x-b.x) - Math.atan2(a.y-b.y, a.x-b.x);
    let d = Math.abs(r * 180 / Math.PI); return d > 180 ? 360 - d : d;
}

async function init() {
    detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet);
    const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode, width: 1280 } });
    video.srcObject = s; video.onloadedmetadata = () => detect();
}

async function detect() {
    if (video.readyState >= 2) {
        const poses = await detector.estimatePoses(video);
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (poses.length > 0) {
            const kp = poses[0].keypoints;
            // Keypoints Mapping
            const sL = kp[5], sR = kp[6], hL = kp[11], hR = kp[12], kL = kp[13], kR = kp[14], aL = kp[15], aR = kp[16];

            if (hL.score > 0.3 && hR.score > 0.3) {
                const angL = getAngle(hL, kL, aL);
                const angR = getAngle(hR, kR, aR);
                const backAng = getAngle(sR, hR, kR);

                smoothL = smoothL * 0.6 + angL * 0.4;
                smoothR = smoothR * 0.6 + angR * 0.4;
                const avgKnee = (smoothL + smoothR) / 2;

                angleDisplay.innerText = `${Math.round(smoothL)}° / ${Math.round(smoothR)}°`;

                if (recording) {
                    // Symmetrie Warnung
                    if (Math.abs(smoothL - smoothR) > 15) {
                        hintBox.innerText = "SKELETT SCHIEF!"; hintBox.style.display = "block";
                    } else if (avgKnee < 100) {
                        hintBox.innerText = "PERFEKTE TIEFE"; hintBox.style.display = "block";
                    } else { hintBox.style.display = "none"; }

                    // Rep Counter Logik
                    if (avgKnee < 105) stage = 'down';
                    if (avgKnee > 150 && stage === 'down') { 
                        repCount++; stage = 'up'; speak(repCount + " Wiederholungen");
                    }
                    if (avgKnee < minAngle) minAngle = Math.round(avgKnee);
                    
                    repDisplay.innerText = `${repCount} | ${minAngle}°`;

                    // Rücken Check
                    if (backAng < 145) {
                        backDisplay.innerText = "KRUMM"; backDisplay.style.color = "#ff4b4b";
                        speak("Rücken gerade");
                    } else {
                        backDisplay.innerText = "OPTIMAL"; backDisplay.style.color = "#00ff87";
                    }
                }

                // Zeichnen (Neon Styles)
                ctx.lineWidth = 8; ctx.lineCap = 'round';
                // Beine Links
                ctx.strokeStyle = '#00d4ff';
                ctx.beginPath(); ctx.moveTo(hL.x, hL.y); ctx.lineTo(kL.x, kL.y); ctx.lineTo(aL.x, aL.y); ctx.stroke();
                // Beine Rechts
                ctx.strokeStyle = '#00ff87';
                ctx.beginPath(); ctx.moveTo(hR.x, hR.y); ctx.lineTo(kR.x, kR.y); ctx.lineTo(aR.x, aR.y); ctx.stroke();
                // Rücken
                ctx.strokeStyle = (backAng < 145) ? '#ff4b4b' : '#ffffff';
                ctx.beginPath(); ctx.moveTo(sR.x, sR.y); ctx.lineTo(hR.x, hR.y); ctx.stroke();
                
                // Glow Effect
                ctx.shadowBlur = 15; ctx.shadowColor = "white";
                kp.forEach(p => { if(p.score > 0.4) { ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, 7); ctx.fill(); } });
                ctx.shadowBlur = 0;
            }
        }
    }
    requestAnimationFrame(detect);
}

mainBtn.onclick = () => {
    recording = !recording;
    if (recording) {
        repCount = 0; minAngle = 180;
        mainBtn.innerText = "STOP & ANALYSE"; mainBtn.style.background = "#ff4b4b";
        speak("Training gestartet. Achte auf deine Form.");
    } else {
        mainBtn.innerText = "START TRAINING"; mainBtn.style.background = "linear-gradient(to right, #00d4ff, #0080ff)";
        speak("Training beendet. Du hast " + repCount + " Wiederholungen geschafft.");
        alert("SESSION REPORT:\\n\\nReps: " + repCount + "\\nTiefster Winkel: " + minAngle + "°");
    }
};

document.getElementById('ghost-btn').onclick = () => {
    ghostMode = !ghostMode;
    video.style.opacity = ghostMode ? "0" : "1";
};

document.getElementById('switch-btn').onclick = async () => {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: currentFacingMode } });
    video.srcObject = s;
};

init();
</script>
"""

components.html(html_code, height=1000)
