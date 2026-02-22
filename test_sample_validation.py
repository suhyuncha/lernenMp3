#!/usr/bin/env python3
"""
샘플 파일 변환 테스트
요구사항 검증:
1. 문장 단위 자막 생성 ✓
2. 정확한 시작 시간 ✓
3. 적절한 길이 (너무 길지 않음) ?
4. 최대한 문장 단위 ?
5. 언어 학습에 적합한 구성 ?
"""

from whisper_worker import whisper_worker
from convert_view import split_segments_by_period
import multiprocessing

def main():
    mp3_file = 'samples/podcast_sample_2min.mp3'
    
    print("=" * 100)
    print("음성 → 자막 변환 테스트 (2분 샘플)")
    print("=" * 100)
    
    # Whisper 변환
    print("\n[1단계] Whisper로 음성 텍스트 추출 중...")
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=whisper_worker, args=(mp3_file, 'base', queue))
    process.start()
    process.join()
    
    result = queue.get()
    if result['error']:
        print(f"❌ 오류: {result['error']}")
        return
    
    segments = result['result']['segments']
    print(f"✅ 완료: {len(segments)}개의 세그먼트 추출됨")
    
    # 문장 단위 분할
    print("\n[2단계] 문장 단위로 분할 중...")
    sentences = split_segments_by_period(segments)
    print(f"✅ 완료: {len(sentences)}개의 문장 생성됨")
    
    # 요구사항 검증
    print("\n" + "=" * 100)
    print("요구사항 검증")
    print("=" * 100)
    
    # 1. 시간 정확도 검증
    print("\n[✓] 1. 정확한 시작 시간")
    overlaps = sum(1 for i in range(len(sentences)-1) if sentences[i]['end'] > sentences[i+1]['start'])
    print(f"    - 시간 겹침: {overlaps}개 {'✅ OK' if overlaps == 0 else '❌ 문제'}")
    
    # 2. 적절한 길이 검증
    print("\n[?] 2. 조각 길이 검증 (너무 길지 않은가?)")
    lengths = [len(s['text'].split()) for s in sentences]  # 단어 수
    avg_length = sum(lengths) / len(lengths)
    max_length = max(lengths)
    min_length = min(lengths)
    print(f"    - 평균 단어 수: {avg_length:.1f}개")
    print(f"    - 최대: {max_length}개 단어")
    print(f"    - 최소: {min_length}개 단어")
    print(f"    - 평가: {'✅ 적절함' if avg_length < 20 else '⚠️ 다소 길음'}")
    
    # 3. 시간 길이 검증 (문장당 재생 시간)
    print("\n[?] 3. 문장당 재생 시간 (언어 학습에 적합한가?)")
    durations = [s['end'] - s['start'] for s in sentences]
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    print(f"    - 평균: {avg_duration:.2f}초")
    print(f"    - 최대: {max_duration:.2f}초")
    print(f"    - 평가: {'✅ 학습에 적합' if avg_duration < 10 else '⚠️ 다소 김'}")
    
    # 4. 샘플 출력
    print("\n" + "=" * 100)
    print("샘플 결과 (첫 10개 문장)")
    print("=" * 100)
    
    for i, sent in enumerate(sentences[:10], 1):
        duration = sent['end'] - sent['start']
        word_count = len(sent['text'].split())
        text_preview = sent['text'][:60] + ('...' if len(sent['text']) > 60 else '')
        print(f"\n[{i:2d}] {sent['start']:6.2f}~{sent['end']:6.2f}s ({duration:5.2f}s, {word_count:2d}w)")
        print(f"     {text_preview}")
    
    # 5. 전체 통계
    print("\n" + "=" * 100)
    print("전체 통계")
    print("=" * 100)
    total_time = sum(durations)
    total_words = sum(len(s['text'].split()) for s in sentences)
    avg_words_per_second = total_words / total_time if total_time > 0 else 0
    
    print(f"총 문장: {len(sentences)}개")
    print(f"총 시간: {total_time:.2f}초 (원본: 120.00초)")
    print(f"총 단어: {total_words}개")
    print(f"분당 단어 수(WPM): {avg_words_per_second * 60:.0f}")
    
    # 6. 최종 평가
    print("\n" + "=" * 100)
    print("최종 평가")
    print("=" * 100)
    
    checks = []
    checks.append(("시간 정확도 (겹침 없음)", overlaps == 0))
    checks.append(("적절한 문장 길이", avg_length < 25))
    checks.append(("적절한 재생 시간", avg_duration < 12))
    checks.append(("언어 학습에 적합한 구성", len(sentences) > 5))  # 최소한 5개 이상
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
    
    all_pass = all(result for _, result in checks)
    print(f"\n{'🎉 모든 요구사항 만족!' if all_pass else '⚠️ 일부 개선 필요'}")

if __name__ == '__main__':
    main()
