import os
import pyaudio
import wave
import keyboard
import whisper
import time

# Set paths
output_dir = r"C:\Users\bgrom\Downloads\recordings"
audio_file = os.path.join(output_dir, "recorded_audio.wav")
transcription_file = os.path.join(output_dir, "transcription.txt")

# Set Whisper model path
model_path = r"C:\Users\bgrom\Downloads\small.pt"

# Function to record audio when hotkey is pressed
def record_audio(output_path):
    p = pyaudio.PyAudio()

    # Device index for "Microphone (1080P Pro Stream)"
    device_index = 21  # This is the device you want to use

    # Get the device info
    device_info = p.get_device_info_by_index(device_index)
    print(f"Using device: {device_info['name']}")

    # Set parameters for the recording
    channels = device_info['maxInputChannels']  # 2 channels (Stereo)
    rate = int(device_info['defaultSampleRate'])  # Default sample rate
    frames_per_buffer = 1024
    format = pyaudio.paInt16

    print("Press and hold 'Ctrl' to start recording...")

    frames = []
    recording = False  # Flag to track if we're recording
    stream = p.open(format=format, channels=channels, rate=rate,
                    input=True, input_device_index=device_index, frames_per_buffer=frames_per_buffer)

    while True:
        if keyboard.is_pressed('ctrl') and not recording:  # Start recording only if not already recording
            print("Recording started...")
            recording = True
            frames = []  # Clear frames to start a fresh recording

        if recording and keyboard.is_pressed('ctrl'):
            data = stream.read(frames_per_buffer)
            frames.append(data)  # Keep recording as long as 'Ctrl' is held down
        
        elif recording and not keyboard.is_pressed('ctrl'):  # Stop recording when 'Ctrl' is released
            print("Recording stopped.")
            break

    # Stop recording
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio to a file
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

# Function to transcribe the recorded audio using Whisper
def transcribe_audio(audio_file, model_path):
    # Load the model
    model = whisper.load_model(model_path)

    # Check if the audio file exists
    if not os.path.exists(audio_file):
        print(f"Error: The file {audio_file} does not exist.")
        return "", 0

    start_time = time.time()
    
    try:
        # Transcribe the audio
        result = model.transcribe(audio_file)
        elapsed_time = time.time() - start_time
        print(f"✅ Transcription completed in {elapsed_time:.2f} seconds.")
        return result["text"], elapsed_time
    except Exception as e:
        print(f"Error during transcription: {e}")
        return "", 0

# Main flow: Capture audio and then transcribe
record_audio(audio_file)
transcribed_text, transcription_time = transcribe_audio(audio_file, model_path)

# Save transcription to a file
with open(transcription_file, "w", encoding="utf-8") as f:
    f.write(transcribed_text)

# Output results
print(f"✅ Transcription saved to: {transcription_file}")
