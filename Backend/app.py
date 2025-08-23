from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, send
from flask_cors import CORS # Import CORS
from openai import OpenAI
import os
from ai import get_ai_response
import datetime # For status timestamps
import random   # For simulating process
import time     # For simulating process
import threading # For running simulation in background thread

app = Flask(__name__)

CORS(app) 

socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

# Serve the React frontend (if needed)
@app.route('/')
def index():
    return "Backend is Running"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY not found in environment variables. Please check your .env file.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# --- Existing SocketIO handlers ---
@socketio.on('chatMessage')
def handle_message(message):
    user_text = message.get('text')
    sender = message.get('sender')

    print(f"Received message from {sender}: {user_text}")

    # First, echo the user's message back to all clients so they see their own message
    emit('message', {'text': user_text, 'sender': 'user'}, broadcast=True)

    if user_text:
        try:
            # --- MODIFIED: Call the get_ai_response function from ai.py ---
            ai_response_content = get_ai_response(user_text)
            print(f"AI Response: {ai_response_content}")

            # Send the AI's response back to all clients
            emit('message', {'text': ai_response_content, 'sender': 'ai'}, broadcast=True)

        except Exception as e:
            print(f"An unexpected error occurred in app.py handle_message: {e}")
            emit('message', {'text': "An internal server error occurred.", 'sender': 'ai'}, broadcast=True)
    else:
        print("Received empty message from user.")

@socketio.on('ai_reaction')
def handle_ai_reaction(data):
    message_index = data.get('messageIndex')
    reaction_type = data.get('reaction')
    
    print(f"Received AI reaction: Message Index {message_index}, Reaction: {reaction_type}")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
