import os
import sounddevice as sd
import wavio
from whisper.whisper_transcriber import WhisperTranscriber
from deepseek_client import DeepSeekClient
from excel_reader import ExcelReader
# ✅ 设置 ffmpeg 路径（你已正确安装）
os.environ["PATH"] += os.pathsep + r"D:\ffmpeg"

# ✅ 录音函数
def record_audio(filename="audio.wav", duration=5, samplerate=16000):
    print("🎤 开始录音...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    wavio.write(filename, recording, samplerate, sampwidth=2)
    print("🔚 录音结束，保存为", filename)
    return filename

def main():
    transcriber = WhisperTranscriber(model_size="base")
    client = DeepSeekClient(model="deepseek-r1:8b")

    print("请选择输入方式：")
    print("1. 🎙️ 录音识别并提问")
    print("2. 📁 导入音频文件识别并提问")
    print("3. 📊 读取 Excel 文件并提问")  # ✅ 新增
    choice = input("请输入 1、2 或 3：")

    if choice == "1":
        audio_path = record_audio("audio.wav", duration=5)
        print("🧠 正在语音识别...")
        text = transcriber.transcribe_audio(audio_path)
        print(f"\n📝 Whisper 识别结果：{text}")
        prompt = text

    elif choice == "2":
        audio_path = input("请输入音频文件路径（如 D:\\audio\\test.mp3）：").strip('"').strip()
        if not os.path.exists(audio_path):
            print("❌ 文件不存在，请检查路径")
            return
        print("🧠 正在语音识别...")
        text = transcriber.transcribe_audio(audio_path)
        print(f"\n📝 Whisper 识别结果：{text}")
        prompt = text

    elif choice == "3":
        excel_path = input("请输入 Excel 文件路径（如 D:\\data\\info.xlsx）：").strip('"').strip()
        if not os.path.exists(excel_path):
            print("❌ 文件不存在")
            return
        reader = ExcelReader(excel_path)
        headers, rows = reader.extract_data()
        if not headers:
            return

        print("\n✅ 表头字段：", headers)
        print("✅ 示例数据：")
        for row in rows:
            print(row)

        user_question = input("\n📝 请输入你希望提问的问题或说明（将结合上面的表进行分析）：\n> ")
        # 组织 prompt
        prompt = f"""以下是我提供的 Excel 表格信息：
        表头字段：{headers}
        示例数据（前 {len(rows)} 行）：{rows}

        我的问题是：{user_question}
        请结合表格内容和我的问题进行回答。"""

    else:
        print("❌ 无效输入")
        return

    # ✅ DeepSeek 回答
    print("\n🤖 正在调用 DeepSeek 回答中...")
    response = client.ask(prompt)
    print(f"\n📣 DeepSeek 回答：\n{response}")

if __name__ == "__main__":
    main()
