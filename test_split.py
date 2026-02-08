import whisper
import re

def split_segments_into_sentences(segments):
    import re
    new_segments = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        # 문장 분리 (구두점 후 공백 기준)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            continue
        # 시간 분배 (문자 수 비례)
        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0:
            continue
        start_time = seg["start"]
        duration = seg["end"] - seg["start"]
        current_time = start_time
        for sentence in sentences:
            char_ratio = len(sentence) / total_chars
            end_time = current_time + duration * char_ratio
            new_segments.append({
                "start": current_time,
                "end": end_time,
                "text": sentence
            })
            current_time = end_time
    return new_segments

# Load model and transcribe
model = whisper.load_model("base")
result = model.transcribe("samples/podcast_43021_pocha_talk_186_bist_du_open_minded_part_2.mp3")

segments = result["segments"]
print("Original segments:")
for seg in segments:
    print(f"{seg['start']:.2f}-{seg['end']:.2f}: {seg['text']}")

print("\nSplit sentences:")
split_sentences = split_segments_into_sentences(segments)
for sent in split_sentences:
    print(f"{sent['start']:.2f}-{sent['end']:.2f}: {sent['text']}")