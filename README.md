# 📝 **ScrumSense: Slack-Triggered OBS Recording and Audio Transcription**

**ScrumSense** automates the process of controlling **OBS (Open Broadcaster Software)** based on **Slack** events, recording meetings, and transcribing the audio for **Scrum meeting summaries**. This project uses a combination of **Flask**, **ngrok**, **Vosk**, and **OpenAI's GPT-4** to transcribe audio recordings and summarize the key points from the meeting.

# Note:
  You will need to set up permissions within Slack API if you are working within an organizations Slack you will have to request authorizations to install the app, when you make changes you will have to re-install the app. It is seemless, yet tedious. Bear with the pain. 
---

## 🚀 **Features**

- **Slack Event Listener**: Listens to Slack events and triggers OBS recording when a user joins or leaves a huddle.
- **OBS Control**: Starts and stops OBS recording based on the user's status in Slack.
- **Audio Processing**: Converts and processes recorded audio using **FFmpeg** and **Vosk** for transcription.
- **Transcription and Summary**: Sends transcriptions to **OpenAI’s GPT-4** to generate a concise Scrum meeting summary.
- **Easy Setup**: Quickly integrate with Slack and OBS on your local machine.

---

## 🧰 **Technologies Used**

- **Flask**: Web framework for creating the Slack event listener.
- **Vosk**: Speech recognition tool for transcribing audio.
- **OpenAI GPT-4**: Summarizes transcriptions into Scrum meeting summaries.
- **FFmpeg**: Audio conversion and noise reduction.
- **ngrok**: Exposes the local Flask server to the internet for Slack integration.
- **pyautogui**: Automates keyboard actions for controlling OBS.

---

## 📋 **Prerequisites**

Before running the application, ensure you have the following installed:

1. **Python 3.8+** – Make sure Python is installed on your machine.
2. **ngrok** – Used to expose the local Flask server to the internet for Slack event subscriptions.
3. **OBS Studio** – Install OBS on your machine and configure it to be controlled by hotkeys.
4. **FFmpeg** – Used for audio processing and conversion.
5. **Vosk Model** – A speech recognition model for transcription.

---

## ⚡ **Installation Instructions**

### Step 1: Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/bgromala555/ScrumSense

cd ScrumSense

``` 

### Step 2: Install Python Dependencies
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

### Step 3: Set Up Config File
```bash
{
  "slack_signing_secret": "your_slack_signing_secret",
  "openai_api_key": "your_openai_api_key",
  "ffmpeg_path": "/path/to/ffmpeg",
  "obs_path": "/path/to/obs",
  "vosk_model_path": "/path/to/vosk-model",
  "transcripts_dir": "/path/to/transcripts",
  "recordings_dir": "/path/to/recordings",
  "real_name": "Full name from Slack Profile
}

```

### Step 4: Set Up Environment Variables
```bash
# On macOS/Linux:
brew install ngrok

On Windows, download ngrok from https://ngrok.com/download
After downloading, unzip the file and add ngrok to your PATH or use it directly from the unzipped folder.
```
### Step 5: Set Up Environment Variables
Start ngrok to expose your Flask server to the internet.

```bash
# Run ngrok to forward traffic to port 3000 (or whichever port your Flask app is running on)
ngrok http 3000
```

### Step 6: Configure Slack
```bash
1. Go to your [Slack App Configuration](https://api.slack.com/apps) and enable **Event Subscriptions**.
2. Set the **Request URL** to the ngrok URL you received (e.g., `https://abc123.ngrok.io/slack/events`).

---

### Subscribe to bot events:

- **Event Name**: `user_huddle_changed`
  - **Description**: A user's huddle status has changed
  - **Required Scope**: `users:read`

---

### OAuth Scopes:

- `calls:read`: View information about ongoing and past calls
- `channels:join`: Join public channels in a workspace
- `channels:read`: View basic information about public channels in a workspace
- `chat:write`: Send messages as @ScrumSense
- `users:read`: View people in a workspace
```

