from flask import Flask, render_template, send_from_directory, request, jsonify
import time
from dotenv import load_dotenv
import os
import PyPDF2
from groq import Groq
import json

# Load environment variables from a .env file if present
load_dotenv()  

# Initialize the Flask application
# The 'static_folder' tells Flask where to find files like CSS, JS (if we had them in separate files)
# The 'template_folder' tells Flask where to find our HTML files. We'll place index.html in a 'templates' folder.
app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize Groq client
try:
    groq_api_key = os.getenv('groq_api_key')
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")
    client = Groq(api_key=groq_api_key)
except ValueError as e:
    print(f"Error initializing Groq client: {e}")
    client = None

# Create a function to extract text from PDF
def extractTextFromPDF(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    try:
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def getFeedbackFromGroq(prompt, resumeData):
    with open ('system_prompt.txt', 'r') as file:
        systemPrompt = file.read()
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": f"{systemPrompt}"
                },
                {
                    "role": "user",
                    "content": f"{prompt}. \n \n Here is the resume data: {resumeData}"
                }
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting feedback from Groq: {e}")
        return {"error": "Failed to get feedback from Groq."}



# Define a route for the root URL ('/')
@app.route('/')
def index():
    """
    This is the main route of our application.
    When a user visits the root URL ('/'), this function will be called.
    It tells Flask to find 'index.html' in our 'templates' folder and send it to the browser.
    """
    return render_template('index.html')


@app.route('/resumeBuilder/createResume', methods=['POST'])
def create_resume():
    """
    This route will handle the creation of a new resume.
    """
    
    responseData = request.get_json()
    prompt = responseData.get('prompt', '') #Here '' is the default value if 'prompt' is not found
    mock_response = {
        "status": "success",
        "message": "Resume created successfully.",
        "data": {
            "prompt": prompt
        }
    }
    time.sleep(5)
    return jsonify(mock_response), 201


@app.route('/resumeBuilder/rateResume', methods=['POST'])
def rate_resume():
    """
    This route will handle the rating of an existing resume.
    """

    # request is a global object of flask which captures every information in the incoming request
    # .files is the attribute that contains all the uploaded files
    # 'resume' will be the key in whose value we expect the uploaded file to be from frontend JavaScript

    if 'resume' not in request.files:
        return jsonify({'error':'No file found'}), 400

    file = request.files['resume']
    userPrompt = request.form.get('userPrompt', '')

    # Check if the user selected a file
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # If we reached this point, it means a file was uploaded
    # You can now process the file (e.g., save it, analyze it, etc.)

    pdfData = extractTextFromPDF(file)
    llm_response = getFeedbackFromGroq(userPrompt, pdfData)
    return jsonify({"review": [llm_response]}), 200


# This is a standard Python construct. 
# The code inside this 'if' block will only run when you execute 'python server.py' directly.
# This always need to be at the end of the code of flask app
if __name__ == '__main__':
    # app.run() starts the development server.
    # debug=True is very useful during development. It automatically reloads the server when you save changes
    # and provides helpful error messages if something goes wrong.
    app.run(debug=True, port=5000)