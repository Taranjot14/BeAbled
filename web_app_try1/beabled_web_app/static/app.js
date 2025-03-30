let aslEnabled = false;
let callActive = false;
const mainVideo = document.getElementById("mainVideo");
const selfVideo = document.getElementById("selfVideo");
const joinBtn = document.getElementById("joinBtn");
const aslPanel = document.getElementById("aslPanel");
const aslBtn = document.getElementById("aslBtn");

let canvas = document.createElement("canvas");
let ctx = canvas.getContext("2d");

document.getElementById("micBtn").onclick = () => {};
document.getElementById("camBtn").onclick = () => {};

aslBtn.onclick = () => {
    aslEnabled = !aslEnabled;
    aslPanel.classList.toggle("d-none", !aslEnabled);
    aslPanel.textContent = aslEnabled ? "ASL detection on" : "ASL detection off";
};

joinBtn.onclick = () => {
    if (!callActive) {
        navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then(stream => {
            selfVideo.srcObject = stream;
            mainVideo.srcObject = stream;
            setInterval(() => {
                if (!aslEnabled) return;
                canvas.width = selfVideo.videoWidth;
                canvas.height = selfVideo.videoHeight;
                ctx.drawImage(selfVideo, 0, 0);
                let imgData = canvas.toDataURL("image/jpeg");

                fetch("/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ image: imgData })
                })
                .then(res => res.json())
                .then(data => {
                    aslPanel.textContent = `✋ ${data.prediction} (${data.confidence})`;
                });
            }, 1000);
        });
        callActive = true;
        joinBtn.textContent = "Leave";
    } else {
        location.reload();
    }
};
