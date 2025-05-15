// Toggle model answer visibility
function toggleModelAnswer() {
    const modelAnswerSection = document.getElementById("model-answer");
    modelAnswerSection.style.display = (modelAnswerSection.style.display === "none") ? "block" : "none";
}

// Handle change in the selected question
const questionSelect = document.getElementById("question");
const toggleButton = document.querySelector("button[onclick='toggleModelAnswer()']");
questionSelect?.addEventListener("change", function () {
    if (toggleButton) toggleButton.style.display = "none";
    const modelAnswerSection = document.getElementById("model-answer");
    if (modelAnswerSection) modelAnswerSection.style.display = "none";
});

// Video recording logic
let mediaRecorder;
let recordedBlobs = [];

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const preview = document.getElementById("preview");
const recorded = document.getElementById("recorded");
const uploadBtn = document.getElementById("uploadBtn");
const videoDataInput = document.getElementById("videoData");
const recordingSection = document.getElementById("recording-section");

startBtn?.addEventListener('click', startRecording);
stopBtn?.addEventListener('click', stopRecording);

async function startRecording() {
    try {
        recordedBlobs = [];
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        preview.srcObject = stream;

        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) recordedBlobs.push(event.data);
        };

        mediaRecorder.onstop = handleRecordingStop;

        mediaRecorder.start();
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } catch (err) {
        alert("Error accessing webcam: " + err.message);
        console.error("getUserMedia failed:", err);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        preview.srcObject?.getTracks().forEach(track => track.stop());
    }
    stopBtn.disabled = true;
    startBtn.disabled = false;
}

function handleRecordingStop() {
    const blob = new Blob(recordedBlobs, { type: 'video/webm' });
    recorded.src = URL.createObjectURL(blob);
    recordingSection.style.display = "block";

    convertBlobToBase64(blob).then(base64Video => {
        videoDataInput.value = base64Video;  // This sets the hidden input's value to the base64 video data
        uploadBtn.disabled = false; // Enable the upload button
    }).catch(error => {
        console.error("Failed to convert Blob to Base64:", error);
    });
}

// Convert Blob to Base64
function convertBlobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// Upload Function
function uploadVideo(event) {
    event.preventDefault();

    const videoData = videoDataInput.value.trim();

    if (!videoData.startsWith('data:video/')) {
        alert('Invalid video format. Ensure it is a base64 video.');
        console.error("Video Data is not in Base64 format:", videoData);
        return;
    }

    fetch('/upload_video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video: videoData })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Server Error:', data.error);
            alert('Failed to upload video: ' + data.error);
        } else {
            console.log('Success:', data);
            alert('Video uploaded successfully!');
        }
    })
    .catch(error => {
        console.error('Fetch Error:', error);
        alert('Failed to upload video. Network error or invalid server response.');
    });
}

function displayScore(score, transcribedText) {
    document.getElementById("score-section").style.display = "block";
    document.getElementById("similarity-score").textContent = score + "%";

    document.getElementById("transcribed-answer").style.display = "block";
    document.getElementById("transcribed-text").textContent = transcribedText;
}
function displayScore(score, transcribedText) {
    document.getElementById("score-section").style.display = "block";
    document.getElementById("similarity-score").textContent = score + "%";

    document.getElementById("transcribed-answer").style.display = "block";
    document.getElementById("transcribed-text").textContent = transcribedText;
}