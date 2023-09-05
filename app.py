from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, flash
import os
from dotenv import load_dotenv
from connectors import dbconnectionString
import openai
import requests
import time
import pyodbc
from werkzeug.utils import secure_filename


# Load environment variables from .env.local file
load_dotenv(".env.local")

# openai.organization="ORG_ID"
openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.Model.list()

app = Flask(__name__)

# File uploading
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ.get("SECRET_KEY")  # for flashing messages

latest_response = None
full_response = None  # Initialize latest_response at the top

logs = []

@app.route('/')
def index():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', logs=logs, files=files)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

@app.route('/send_chat_message', methods=['POST'])
def send_chat_message():
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": request.json.get('user_message')
                }
            ],
            "stream": True
        }

        print("Sending request to OpenAI...")
        response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers, stream=True)

        global latest_response
        latest_response = response

        print("Message sent to OpenAI.")
        return jsonify({"message": "Chat message received and sent to OpenAI."})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_chat_stream')
def get_chat_stream():
    if not latest_response:
        return "No content available for streaming yet.", 204  # 204 No Content

    def generate():
        for chunk in latest_response.iter_content(chunk_size=None):
            print(f"Received chunk: {chunk}")
            yield f"data: {chunk.decode('utf-8')}\\n\\n"
            time.sleep(0.5)

    print("Streaming response back to client...")
    return Response(generate(), mimetype="text/event-stream")


@app.route('/send_bulk_chat_message', methods=['POST'])
def send_bulk_chat_message():
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": request.json.get('user_message')
                }
            ],
            "stream": False
        }

        print("Sending bulk request to OpenAI...")
        logs.append("Sending bulk request to OpenAI...")
        response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)

        global full_response
        full_response = response.json()

        print("Bulk message sent to OpenAI.")
        logs.append("Bulk message sent to OpenAI.")
        return jsonify({"message": "Bulk chat message received and sent to OpenAI."})

    except Exception as e:
        print(f"Error: {e}")
        logs.append(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_bulk_response')
def get_bulk_response():
    if not full_response:
        return jsonify({"error": "No content available yet."}), 204  # 204 No Content

    print("Sending full response back to client...")
    return jsonify(full_response)


# Check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File successfully uploaded')
        return redirect(url_for('index'))
    else:
        flash('Allowed file types are txt')
        return redirect(url_for('index'))

@app.route('/run_query', methods=['GET'])
def run_query():
    try:
        connection = pyodbc.connect(dbconnectionString)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM chat_history")
        data = cursor.fetchall()
        connection.close()
        return str(data)
    except Exception as e:
        return str(e)




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8082, threaded=True)