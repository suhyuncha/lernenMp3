import whisper

def whisper_worker(mp3_file, model_name, queue):
    try:
        print(f"Loading model: {model_name}")
        model = whisper.load_model(model_name)
        print("Model loaded, starting transcription")
        result = model.transcribe(mp3_file)
        print("Transcription completed")
        queue.put({"result": result, "error": None})
    except Exception as e:
        print(f"Error: {str(e)}")
        queue.put({"result": None, "error": str(e)})

def get_audio_duration(mp3_file):
    audio = whisper.load_audio(mp3_file)
    duration = audio.shape[0] / whisper.audio.SAMPLE_RATE
    return duration