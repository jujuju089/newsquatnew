
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Winkel-App Fix", layout="wide")

st.title("📐 Winkel-KI (Tablet-Optimiert)")

html_code = """
<div id="ai-container" style="position: relative; font-family: sans-serif; background: #1a1a1a; color: white; border-radius: 20px; overflow: hidden; max-width: 900px; margin: auto;">
    
    <!-- DASHBOARD (Oben fixiert) -->
    <div style="position: relative; z-index: 10; background: rgba(45, 45, 45, 0.9); padding: 15px; display: flex; justify-content: space-around; align-items: center; border-bottom: 2px solid #ffaa00;">
        <div style="text-align: center;">
            <div id="angle-label" style="font-size: 1.8em; font-weight: bold; color: #ffaa00;">0°</div>
            <div id="status-text" style="font-size: 0.8em; color: #aaa;">Suche Mensch...</div>
        </div>
    </div>

    <!-- VIDEO BEREICH -->
    <div style="position: relative; width: 100%; line-height: 0; background: #000;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto; z-index: 1;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none;"></canvas>
        
        <!-- BUTTONS (Schweben ÜBER dem Video am unteren Rand) -->
        <div style="position: absolute; bottom: 20px; left: 0; width: 100%; display: flex; gap: 10px; justify-content: center; z-index: 100; padding: 0 10px; box-sizing: border-box;">
            <button id="switch-btn" style="padding: 12px 20px; background: #444; color: white; border: 2px solid white; border-radius: 10px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">📷 Kamera wechseln</button>
            <button id="stop-btn" style="padding: 12px 20px; background: #ff4b4b; color: white; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">⏹ Stopp</button>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const angleLabel = document.getElementById('angle-label');
const statusText = document.getElementById('status-text');

let detector;
let currentFacingMode = 'environment'; 
let active = true;

function calculateAngle(a, b, c) {
    let radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) angle = 360 - angle;
    return angle;
}

async function startStream() {
    try {
        if(video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); }
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode }
        });
        video.srcObject = stream;
        return new Promise(resolve => { video.onloadedmetadata = () => { video.play(); resolve(); }; });
    } catch (err) { console.error(err); }
}

async function init() {
    detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet,
        { modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
    );
    await startStream();
    detect();
}

async function detect() {
    if (!active) return;
    if (video.readyState >= 2) {
        const poses = await detector.estimatePoses(video);
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (poses.length > 0) {
            const kp = poses[0].keypoints;
            const hip = kp[12], knee = kp[14], ankle = kp[16];

            if (hip.score > 0.3 && knee.score > 0.3 && ankle.score > 0.3) {
                const angle = calculateAngle(hip, knee, ankle);
                angleLabel.innerText = Math.round(angle) + "°";
                statusText.innerText = angle < 100 ? "SQUAT!" : "Stehend";

                ctx.strokeStyle = "#ffaa00";
                ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.moveTo(hip.x, hip.y);
                ctx.lineTo(knee.x, knee.y);
                ctx.lineTo(ankle.x, ankle.y);
                ctx.stroke();
            }
            ctx.fillStyle = "white";
            kp.forEach(p => { if(p.score > 0.3) { ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, 2*Math.PI); ctx.fill(); } });
        }
    }
    requestAnimationFrame(detect);
}

document.getElementById('switch-btn').onclick = async (e) => {
    e.preventDefault(); // Verhindert ungewollte Browser-Aktionen
    currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
    await startStream();
};

document.getElementById('stop-btn').onclick = () => {
    active = false;
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=1000)
