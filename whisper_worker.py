import whisper

def whisper_worker(mp3_file, model_name, queue):
    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(mp3_file)
        queue.put({"result": result, "error": None})
    except Exception as e:
        queue.put({"result": None, "error": str(e)})

def get_audio_duration(mp3_file):
    audio = whisper.load_audio(mp3_file)
    duration = audio.shape[0] / whisper.audio.SAMPLE_RATE
    return duration