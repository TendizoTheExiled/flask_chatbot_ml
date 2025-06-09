from flask import Flask, request, jsonify
import pandas as pd
from transformers import pipeline
import os # <-- We'll use this to check file paths

app = Flask(__name__)

# --- Global Variables for Model and Data ---
# Initialize them to None. They'll be loaded once when the app starts.
qa_df = None
qa_pipeline = None

# --- Configuration Paths ---
# Use relative paths for files that will be in your project directory
QA_DATA_FILE = 'maize_qa.csv'
# The 'model' directory will be in the same folder as app.py on Railway
MODEL_DIR = './model' # <-- Changed from an absolute path

# --- Function to Load Resources (called once at startup) ---
def load_resources():
    global qa_df, qa_pipeline

    print("Attempting to load chatbot resources...")

    # Load your CSV with questions, intents, and responses
    if os.path.exists(QA_DATA_FILE):
        try:
            qa_df = pd.read_csv(QA_DATA_FILE)
            if all(col in qa_df.columns for col in ['question', 'intent', 'response']):
                print(f"Successfully loaded Q&A data from {QA_DATA_FILE}.")
            else:
                print(f"ERROR: '{QA_DATA_FILE}' must contain 'question', 'intent', and 'response' columns.")
                qa_df = None # Mark as failed
        except Exception as e:
            print(f"ERROR: Failed to load Q&A data from {QA_DATA_FILE}: {e}")
            qa_df = None
    else:
        print(f"ERROR: Q&A data file '{QA_DATA_FILE}' not found. Please ensure it is in the same directory.")
        qa_df = None

    # Load your trained DistilBERT model
    if os.path.exists(MODEL_DIR) and os.path.isdir(MODEL_DIR):
        try:
            qa_pipeline = pipeline("text-classification", model=MODEL_DIR)
            print(f"Successfully loaded DistilBERT model from {MODEL_DIR}.")
        except Exception as e:
            print(f"ERROR: Failed to load DistilBERT model from {MODEL_DIR}: {e}")
            qa_pipeline = None
    else:
        print(f"ERROR: Model directory '{MODEL_DIR}' not found or is not a directory.")
        qa_pipeline = None

# --- Call load_resources when the app starts ---
# This ensures model and data are ready before requests come in.
with app.app_context():
    load_resources()

# --- Helper function to get response ---
def get_response(user_question):
    # Check if resources are actually loaded before proceeding
    if qa_pipeline is None or qa_df is None:
        return "Sorry, the chatbot's resources are not fully loaded. Please inform the administrator."

    try:
        # Predict intent using your model
        # The pipeline outputs a list of dictionaries, e.g., [{'label': 'greeting', 'score': 0.99}]
        intent_pred_result = qa_pipeline(user_question)
        intent_pred = intent_pred_result[0]['label']

        print(f"User question: '{user_question}' -> Predicted Intent: '{intent_pred}'")

        # Find the response for the predicted intent
        # Ensure 'intent' is the correct column name in your CSV (it matches your example)
        match = qa_df[qa_df['intent'] == intent_pred]

        if not match.empty:
            return match.iloc[0]['response']
        else:
            # If an intent is predicted but no matching response is found in CSV
            return "I understood your intent, but I don't have a specific answer for that. Could you rephrase?"
    except Exception as e:
        print(f"Error during intent prediction or response retrieval: {e}")
        return "Oops! Something went wrong while trying to understand your question."

# --- API Endpoints ---

# Health check / Home route
@app.route('/', methods=['GET'])
def home():
    if qa_pipeline is None or qa_df is None:
        return "Chatbot API is still starting up or encountered an error loading resources. Please wait.", 503
    return "Chatbot API is running and ready to receive questions!"

# Main chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    # Ensure resources are loaded before handling the request
    if qa_pipeline is None or qa_df is None:
        return jsonify({"error": "Chatbot resources are not loaded. Please try again later."}), 503

    data = request.get_json(silent=True) # silent=True returns None if parsing fails
    if not data:
        return jsonify({'error': 'Invalid JSON request.'}), 400

    user_question = data.get('question', '').strip() # .strip() removes whitespace

    if not user_question:
        return jsonify({'response': 'Please provide a question in your request.'}), 400

    response = get_response(user_question)
    return jsonify({'response': response})

# --- Run the Flask App ---
if __name__ == '__main__':
    # This is for local development ONLY.
    # On Railway (and other production environments), Gunicorn will run your app.
    app.run(host='0.0.0.0', port=5000, debug=True)
