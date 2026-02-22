import whisper
from pydub import AudioSegment
import os

file_path = "/Users/suhyun/Documents/dev/mp3/"

# 1. 오디오를 텍스트로 변환 (타임스탬프 포함)
def get_transcript_with_timestamps(audio_path):
    model = whisper.load_model("base") # 또는 더 정확한 'medium'
    print("텍스트 추출 중...")
    result = model.transcribe(audio_path, verbose=False)
    return result['segments'] # [{start: 0.0, end: 5.2, text: "..."}, ...]

# 2. 문맥상 자를 지점 결정 (예: 7분 내외에서 가장 긴 침묵 혹은 문장 끝)
def find_split_points(segments, target_interval_sec=420): # 7분(420초) 기준
    split_points = [0]
    last_split = 0
    
    for i, segment in enumerate(segments):
        # 현재 문장의 끝 시간이 마지막 절단 지점으로부터 target_interval을 넘었을 때
        if segment['end'] - last_split >= target_interval_sec:
            # 여기서 바로 자르지 않고, 문장이 끝나는 지점을 선택
            split_points.append(segment['end'] * 1000) # 밀리초 단위
            last_split = segment['end']
            
    return split_points

# 3. 오디오 자르기 및 저장
def split_audio_by_context(audio_path, split_points):
    audio = AudioSegment.from_mp3(audio_path)

    intput_name = os.path.basename(audio_path).split('.')[0]

    for i in range(len(split_points)):
        start = split_points[i]
        end = split_points[i+1] if i+1 < len(split_points) else len(audio)
        
        chunk = audio[start:end]
        outfile = os.path.join(file_path, f"{intput_name}_part_{i+1}.mp3")
        chunk.export(outfile, format="mp3")
        print(f"Part {i+1} 저장 완료: {start/1000}s ~ {end/1000}s")

# 실행 예시
audio_file = "podcast_43021_pocha_talk_186_bist_du_open_minded.mp3"
segments = get_transcript_with_timestamps(os.path.join(file_path, audio_file))
points = find_split_points(segments)
split_audio_by_context(os.path.join(file_path, audio_file), points)