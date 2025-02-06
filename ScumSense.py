import hashlib
import hmac
import time
import os
import json
import subprocess
import wave
from flask import Flask, request, jsonify
from vosk import Model, KaldiRecognizer
from openai import OpenAI
import pyautogui

# Load configuration from config.json
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()

# Initialize Flask app
app = Flask(__name__)

# Slack Signing Secret
SIGNING_SECRET = config.get("slack_signing_secret")

# Paths
OBS_PATH = config.get("obs_path") #looking for .exe file
RECORDINGS_DIR = config.get("recordings_dir") #this is the path where all video files will be saved with obs (You have to set that up manually 
VOSK_MODEL_PATH = config.get("vosk_model_path") # model used was vosk-model-en-us-0.22
FFMPEG_PATH = config.get("ffmpeg_path") # this part i downloaded the actual model and used the .exe file for it. 
API_KEY_FILE = config.get("api_key_file") # Get this from you OPEN AI API information
TRANSCRIPTS_DIR = config.get("transcripts_dir") #Output for the transcripts

# File paths
CONVERTED_AUDIO_PATH = os.path.join(RECORDINGS_DIR, "converted_audio.wav")
TEXT_FILE_PATH = os.path.join(RECORDINGS_DIR, "transcribed_text.txt")

# Huddle tracking
huddle_active = False

# Load OpenAI API Key
def load_api_key():
    try:
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"API key file not found at {API_KEY_FILE}.")
        exit(1)

# Initialize OpenAI client
api_key = load_api_key()
client = OpenAI(api_key=api_key)

# Debug print helper
def debug_print(message):
    print(f"[DEBUG] {message}")

# Verify Slack request signature
@app.before_request
def verify_slack_signature():
    slack_signature = request.headers.get("X-Slack-Signature")
    slack_timestamp = request.headers.get("X-Slack-Request-Timestamp")
    request_body = request.get_data(as_text=True)

    if not slack_signature or not slack_timestamp:
        debug_print("Missing Slack signature or timestamp.")
        return "Missing headers", 403

    # Reject requests older than 5 minutes
    if abs(time.time() - int(slack_timestamp)) > 60 * 5:
        debug_print("Request timestamp is too old.")
        return "Request timeout", 403

    # Create the basestring
    basestring = f"v0:{slack_timestamp}:{request_body}"
    # Hash the basestring using the Signing Secret
    computed_signature = "v0=" + hmac.new(
        bytes(SIGNING_SECRET, "utf-8"),
        bytes(basestring, "utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # Compare the computed signature with the Slack signature
    if not hmac.compare_digest(computed_signature, slack_signature):
        debug_print("Invalid Slack signature.")
        return "Invalid signature", 403

# Process Slack Event
@app.route("/slack/events", methods=["POST"])
def slack_events():
    global huddle_active
    data = request.json

    # Log incoming JSON payload
    debug_print(f"[DEBUG] Incoming Slack event: {json.dumps(data, indent=2)}")

    if "event" in data:
        event = data["event"]
        event_type = event.get("type")
        user_data = event.get("user", {})
        real_name = user_data.get("real_name", "Unknown User")
        huddle_state = user_data.get("profile", {}).get("huddle_state", "default_unset")

        if real_name == config["real_name"]:  # Using the value from config.json You find htis in your slack channel on your profile
            debug_print(f"Detected huddle state change for {real_name}: {huddle_state}")

            if huddle_state == "in_a_huddle" and not huddle_active:
                # User joins huddle
                huddle_active = True
                debug_print("Starting 15-second countdown before OBS recording...")
                time.sleep(15)
                start_obs_recording()

            elif huddle_state == "default_unset" and huddle_active:
                # User leaves huddle
                huddle_active = False
                debug_print("Stopping OBS recording and processing audio...")
                stop_obs_recording()

                # Process the latest recording
                latest_recording = find_latest_recording()
                if latest_recording:
                    convert_mkv_to_wav(latest_recording, CONVERTED_AUDIO_PATH)
                    transcription = transcribe_audio(CONVERTED_AUDIO_PATH)
                    if transcription:
                        process_transcription_with_openai(transcription)

    return jsonify({"status": "OK"})

# Audio Processing Functions
def find_latest_recording():
    try:
        files = [os.path.join(RECORDINGS_DIR, f) for f in os.listdir(RECORDINGS_DIR) if f.endswith(".mkv")]
        if not files:
            raise FileNotFoundError("No MKV recordings found.")
        latest_file = max(files, key=os.path.getctime)
        debug_print(f"Latest recording found: {latest_file}")
        return latest_file
    except Exception as e:
        debug_print(f"Error finding the latest recording: {e}")
        return None

def convert_mkv_to_wav(mkv_path, wav_path):
    try:
        debug_print(f"Applying noise reduction and converting {mkv_path} to WAV...")

        # FFmpeg command to reduce noise using an audio filter
        command = [
            FFMPEG_PATH, "-y", "-i", mkv_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # Convert to WAV
            "-ar", "16000",  # Sample rate 16kHz
            "-ac", "1",  # Mono audio
            "-af", "highpass=f=200, lowpass=f=3000",  # Filters: Remove frequencies below 200Hz and above 3kHz
            wav_path
        ]
        
        subprocess.run(command, check=True)
        debug_print(f"Noise-reduced audio saved to {wav_path}")

    except subprocess.CalledProcessError as e:
        debug_print(f"Error applying noise reduction: {e}")


def transcribe_audio(audio_path):
    if not os.path.exists(VOSK_MODEL_PATH):
        debug_print(f"Vosk model not found at {VOSK_MODEL_PATH}.")
        return None

    model = Model(VOSK_MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)

    try:
        with wave.open(audio_path, "rb") as wf:
            debug_print("Transcribing audio...")
            transcription = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    transcription.append(result.get("text", ""))  # Extract the text field

            final_result = json.loads(recognizer.FinalResult())
            transcription.append(final_result.get("text", ""))  # Extract final text

        transcribed_text = " ".join(transcription)

        # Save transcription to file
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        with open(TEXT_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(transcribed_text)

        debug_print(f"Transcription saved to {TEXT_FILE_PATH}")
        return transcribed_text
    except Exception as e:
        debug_print(f"Error during transcription: {e}")
        return None

def process_transcription_with_openai(transcription):
    try:
        debug_print("Sending transcription to OpenAI...")
        messages = [
            {"role": "system", "content": (
                "You are an assistant skilled at summarizing Scrum meetings. "
                "Focus on identifying key details, such as tasks discussed, blockers, resolutions, and action items. "
                "Ignore small talk and irrelevant information."
            )},
            {"role": "user", "content": f"Here is the transcription: {transcription}. Provide a structured Scrum summary."}
        ]
        completion = client.chat.completions.create(
            model="gpt-4o",  # Fixed model name here
            messages=messages,
            max_tokens=1000
        )
        response = completion.choices[0].message.content.strip()
        debug_print(f"Summary from OpenAI: {response}")
        return response
    except Exception as e:
        debug_print(f"Error during OpenAI processing: {e}")
        return None

# Run Flask App
if __name__ == "__main__":
    debug_print("Starting Flask server...")
    app.run(port=3000)
