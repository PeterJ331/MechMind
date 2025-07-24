from flask import Flask, request, render_template, send_from_directory, redirect, url_for, session
import os
import base64
import shutil
import time
from utils.extractor import extract_text
from deepseek_client import DeepSeekClient
from whisper_utils.whisper_transcriber import WhisperTranscriber
from utils.excel_reader import ExcelReader
from rag_retriever import retrieve_top_k
from datetime import datetime
from flask import Response

from openai import OpenAI

# ✅ Flask 设置
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 用于 session 管理
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ 初始化本地模型和语音转录器
model = DeepSeekClient()
transcriber = WhisperTranscriber()
TOP_K = 10


# ✅ 创建目录树字典
def get_folder_files():
    folder_files = {}
    for folder in os.listdir(UPLOAD_FOLDER):
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if os.path.isdir(folder_path):
            files = os.listdir(folder_path)
            folder_files[folder] = files
    return folder_files


# ✅ 调用 OpenAI 接口（DeepSeek-R1 免费版）
def ask_openai(prompt, api_key):
    try:
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            # 其它可选模型
            # "deepseek/deepseek-r1:free"  支持 163840 token 长上下文，很强的推理水平
            # "meta-llama/llama-3.2-11b-vision-instruct:free"  支持图文输入，适合需要图片理解任务
            # "google/gemma-3-27b-it:free"  大上下文（96000 token），多模态支持，最新状态免费
            # "mistralai/mistral-small-3.1-24b-instruct:free"  强劲的文本处理模型，24B 参数规模
            # "google/gemma-3n-e2b-it:free"  小参数、免费，是 Gemma 家族轻巧版
            messages=[
                {"role": "system", "content": "你是一位专业的AI助手，擅长解答各类问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 调用 OpenAI API 出错：{e}"


# ✅ 首页
@app.route('/')
def index():
    folder_files = get_folder_files()
    folders = list(folder_files.keys())
    selected_model = session.get('selected_model', 'local')
    api_key = session.get('api_key', '')
    return render_template('index.html',
                           folder_files=folder_files,
                           folders=folders,
                           selected_model=selected_model,
                           api_key=api_key)


# ✅ 设置模型 & API Key
@app.route('/set_model', methods=['POST'])
def set_model():
    selected_model = request.form.get('global_model', 'local')
    api_key = request.form.get('api_key', '')

    session['selected_model'] = selected_model
    session['api_key'] = api_key

    return redirect(url_for('index'))

# ✅ 通用问答接口（表单提问）
@app.route('/ask', methods=['POST'])
def ask():
    question = request.form.get('question')
    selected_model = session.get('selected_model', 'local')
    api_key = session.get('api_key', '')

    top_chunks = retrieve_top_k(question, k=TOP_K)
    context = "\n".join(top_chunks)
    prompt = f"根据以下资料回答问题：\n\n{context}\n\n问题：{question}"

    if selected_model == 'openai':
        answer = ask_openai(prompt, api_key)
    else:
        answer = model.ask(prompt)
    # ✅ 保存为 Markdown 文件
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"qa_{timestamp}.md"
    # markdown_path = os.path.join(UPLOAD_FOLDER, filename)
    # with open(markdown_path, 'w', encoding='utf-8') as f:
    #     f.write(f"# 用户问题\n\n{question}\n\n")
    #     f.write(f"# AI 回答\n\n{answer}\n")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session['markdown_content'] = f"# 用户问题\n\n{question}\n\n# AI 回答\n\n{answer}"
    session['markdown_filename'] = f"qa_{timestamp}.md"

    # 如果需要开启实时记录对话内容保存为.md文件则启用下方代码
    # markdown_content = f"# 用户问题\n\n{question}\n\n# AI 回答\n\n{answer}"
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"qa_{timestamp}.md"
    # markdown_path = os.path.join(UPLOAD_FOLDER, filename)
    #
    # with open(markdown_path, 'w', encoding='utf-8') as f:
    #     f.write(markdown_content)
    #
    # session['markdown_filename'] = filename  # 仅保存文件名，不存内容

    folder_files = get_folder_files()
    folders = list(folder_files.keys())

    return render_template("index.html",
                           answer=answer,
                           source_chunks=top_chunks,
                           folder_files=folder_files,
                           folders=folders,
                           selected_model=selected_model,
                           api_key=api_key)


# ✅ 语音提问接口
@app.route('/ask_from_voice', methods=['POST'])
def ask_from_voice():
    base64_audio = request.form['audio_blob']
    audio_data = base64.b64decode(base64_audio)
    audio_path = os.path.join(UPLOAD_FOLDER, 'audio', 'recorded.wav')
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    with open(audio_path, 'wb') as f:
        f.write(audio_data)

    question = transcriber.transcribe_audio(audio_path)
    top_chunks = retrieve_top_k(question, k=TOP_K)
    context = "\n".join(top_chunks)
    prompt = f"根据以下资料回答问题：\n\n{context}\n\n用户语音提问是：{question}"

    selected_model = session.get('selected_model', 'local')
    api_key = session.get('api_key', '')

    if selected_model == 'openai':
        answer = ask_openai(prompt, api_key)
    else:
        answer = model.ask(prompt)
    # ✅ 保存为 Markdown 文件
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"voice_qa_{timestamp}.md"
    # markdown_path = os.path.join(UPLOAD_FOLDER, filename)
    # with open(markdown_path, 'w', encoding='utf-8') as f:
    #     f.write(f"# 用户语音问题\n\n{question}\n\n")
    #     f.write(f"# AI 回答\n\n{answer}\n")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session['markdown_content'] = f"# 用户语音问题\n\n{question}\n\n# AI 回答\n\n{answer}"
    session['markdown_filename'] = f"qa_{timestamp}.md"

    folder_files = get_folder_files()
    folders = list(folder_files.keys())
    return render_template("index.html",
                           answer=answer,
                           voice_text=question,
                           source_chunks=top_chunks,
                           folder_files=folder_files,
                           folders=folders,
                           selected_model=selected_model,
                           api_key=api_key)


# ✅ 文件上传 / 文件操作
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    folder = request.form['folder']
    target_folder = os.path.join(UPLOAD_FOLDER, folder)
    os.makedirs(target_folder, exist_ok=True)
    filepath = os.path.join(target_folder, file.filename)
    file.save(filepath)
    return redirect(url_for('index'))


@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form['folder_name']
    path = os.path.join(UPLOAD_FOLDER, folder_name)
    if not os.path.exists(path):
        os.makedirs(path)
    return redirect(url_for('index'))


@app.route('/delete/<folder>/<filename>')
def delete_file(folder, filename):
    file_path = os.path.join(UPLOAD_FOLDER, folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))


@app.route('/view/<folder>/<filename>')
def view_file(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, folder), filename)


@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, folder), filename, as_attachment=True)


# ✅ Excel 问答
@app.route('/ask_from_excel', methods=['POST'])
def ask_from_excel():
    excel_file = request.files['excel_file']
    excel_path = os.path.join(UPLOAD_FOLDER, 'excel', excel_file.filename)
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    if os.path.exists(excel_path):
        os.remove(excel_path)
    excel_file.save(excel_path)
    print(f"新上传 Excel 文件路径：{excel_path}")
    print("修改时间：", time.ctime(os.path.getmtime(excel_path)))

    user_question = request.form['excel_question']
    reader = ExcelReader(excel_path)
    headers, rows = reader.extract_data()

    if not headers:
        return "❌ 无法读取 Excel，请检查文件格式"

    structured_info = f"表头字段：{headers}\n前几行数据：{rows}"
    prompt_question = f"以下是用户上传的 Excel 表格信息：\n{structured_info}\n\n问题：{user_question}"

    top_chunks = retrieve_top_k(user_question, k=TOP_K)
    context = "\n".join(top_chunks)
    final_prompt = f"{context}\n\n{prompt_question}"

    selected_model = session.get('selected_model', 'local')
    api_key = session.get('api_key', '')

    if selected_model == 'openai':
        answer = ask_openai(final_prompt, api_key)
    else:
        answer = model.ask(final_prompt)
    # ✅ 保存为 Markdown 文件
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"excel_qa_{timestamp}.md"
    # markdown_path = os.path.join(UPLOAD_FOLDER, filename)
    # with open(markdown_path, 'w', encoding='utf-8') as f:
    #     f.write(f"# 用户问题（基于 Excel 表格）\n\n{user_question}\n\n")
    #     f.write(f"# 表格摘要\n\n{structured_info}\n\n")
    #     f.write(f"# AI 回答\n\n{answer}\n")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session['markdown_content'] = (f"# 用户问题（基于 Excel 表格）\n\n{user_question}\n\n"
                                   f"# 表格摘要\n\n{structured_info}\n\n# AI 回答\n\n{answer}")
    session['markdown_filename'] = f"qa_{timestamp}.md"

    folder_files = get_folder_files()
    folders = list(folder_files.keys())
    return render_template("index.html",
                           answer=answer,
                           source_chunks=top_chunks,
                           folder_files=folder_files,
                           folders=folders,
                           selected_model=selected_model,
                           api_key=api_key)

@app.route('/download_md/<filename>')
def download_markdown(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete_folder/<folder_name>', methods=['POST'])
def delete_folder(folder_name):
    folder_path = os.path.join(UPLOAD_FOLDER, folder_name)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)  # 删除整个目录
    return redirect(url_for('index'))

@app.route('/download_md_live')
def download_markdown_live():
    content = session.get('markdown_content', '')
    filename = session.get('markdown_filename', 'qa.md')

    if not content:
        return "❌ 没有 Markdown 内容可下载。"

    # 构建下载响应
    response = Response(content, mimetype='text/markdown')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    # ✅ 下载完成后清理 session 中的数据
    session.pop('markdown_content', None)
    session.pop('markdown_filename', None)

    return response

if __name__ == '__main__':
    app.run(debug=True)
