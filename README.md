# lernenMP3

## 소개 (Korean)

**lernenMP3**는 MP3 오디오 파일을 텍스트로 변환하고, 변환된 자막(SRT) 파일을 활용하여 독일어-한글 학습을 지원하는 데스크탑 프로그램입니다.

### 주요 기능
- MP3 파일에서 음성을 텍스트로 변환 (Whisper 기반)
- 변환된 텍스트를 문장 단위로 SRT(자막) 파일로 저장
- 독일어 → 한글 자동 번역 및 한글 SRT 파일 동시 생성
- 변환된 SRT 파일을 불러와서 문장별로 학습(듣기/읽기/복습) 지원
- 변환 결과 및 실행 경과를 실시간으로 확인 가능

### 사용 방법
1. **프로그램 실행**  
   ```
   python main.py
   ```
2. **변환하기 탭에서 MP3 파일 선택 후 변환 실행**
3. **변환이 완료되면 SRT 파일이 자동 저장됨**
4. **공부하기(기추출) 탭에서 변환된 MP3/SRT 파일이 자동으로 불러와짐**
5. **문장별로 자막을 보며 학습 진행**

### 요구 사항
- Python 3.8 이상
- 필수 패키지: tkinter, pydub, pygame, googletrans, requests 등  
  (requirements.txt 참고)

### 설치 및 실행 방법

1. Python 3.12.10 설치 (pyenv 권장)
2. 가상환경 생성 및 활성화
    ```bash
    pyenv install 3.12.10
    pyenv local 3.12.10
    python -m venv .venv
    source .venv/bin/activate
    ```
3. 패키지 설치
    ```bash
    pip install -r requirements.txt
    ```
4. 실행
    ```bash
    python main.py
    ```

### 참고
- Whisper 모델은 CPU에서 FP16 미지원 경고가 뜰 수 있으나, 정상 동작합니다.
- 네이버 Papago 번역을 사용하려면 별도 API 키가 필요합니다.

---

## Introduction (English)

**lernenMP3** is a desktop tool for converting MP3 audio files to text and supporting German-Korean language study using generated subtitle (SRT) files.

### Main Features
- Convert MP3 audio to text using Whisper
- Save converted text as sentence-level SRT (subtitle) files
- Automatic German → Korean translation and Korean SRT file generation
- Load SRT files for sentence-by-sentence study (listening/reading/review)
- Real-time display of conversion progress and results

### How to Use
1. **Run the program**
   ```
   python main.py
   ```
2. **In the Convert tab, select an MP3 file and start conversion**
3. **After conversion, SRT files are saved automatically**
4. **In the Study (Extracted/Pre-extracted) tab, converted MP3/SRT files are loaded automatically**
5. **Study each sentence with subtitles**

### Requirements
- Python 3.8 or higher
- Required packages: tkinter, pydub, pygame, googletrans, requests, etc.  
  (See requirements.txt)

### 설치 및 실행 방법

1. Python 3.12.10 설치 (pyenv 권장)
2. 가상환경 생성 및 활성화
    ```bash
    pyenv install 3.12.10
    pyenv local 3.12.10
    python -m venv .venv
    source .venv/bin/activate
    ```
3. 패키지 설치
    ```bash
    pip install -r requirements.txt
    ```
4. 실행
    ```bash
    python main.py
    ```

### Notes
- You may see a warning about FP16 not being supported on CPU for Whisper; this is normal.
- To use Naver Papago translation, you need your own API key.

---
