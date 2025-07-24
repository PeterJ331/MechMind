let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function startRecording() {
    if (isRecording) return;

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            isRecording = true;
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = e => {
                audioChunks.push(e.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    document.getElementById("audio_blob_input").value = base64data;
                    document.getElementById("voice-status").innerText = "🎧 音频已捕获，点击提交开始识别";
                };
            };

            mediaRecorder.start();
            document.getElementById("voice-status").innerText = "🎙️ 正在录音...";
        })
        .catch(error => {
            console.error("录音失败:", error);
            document.getElementById("voice-status").innerText = "❌ 无法访问麦克风";
        });
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById("voice-status").innerText = "⏹️ 已停止录音，准备上传...";
    }
}
