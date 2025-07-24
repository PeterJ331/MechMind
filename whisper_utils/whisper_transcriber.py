# whisper_transcriber.py
import whisper
# print("🔍 whisper_utils 模块位置：", whisper.__file__)

class WhisperTranscriber:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)

    def transcribe_audio(self, audio_path):
        result = self.model.transcribe(audio_path, language="zh")
        return result['text']
