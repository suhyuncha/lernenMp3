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
- Python 3.8 이상 (3.12.10에서 테스트됨)
- 필수 패키지: pydub, pygame, googletrans, requests, openai-whisper, torch, numpy  
  (requirements.txt 참고, tkinter는 내장)

### 설치 및 실행 방법

#### pyenv 사용 (권장)

1. pyenv 설치 및 초기화
    ```bash
    brew install pyenv
    # ~/.zshrc 또는 ~/.bash_profile에 다음 추가:
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    # 터미널 재시작
    ```

2. Python 3.12.10 설치
    ```bash
    pyenv install 3.12.10
    pyenv local 3.12.10
    ```

3. 패키지 설치
    ```bash
    pip install -r requirements.txt
    ```

4. 프로그램 실행
    ```bash
    python main.py
    ```

#### 매번 프로그램 실행 시

pyenv로 설정된 Python 버전에서 직접 실행하세요:
```bash
python main.py
```

또는 pyenv 경로를 직접 사용하여 실행할 수 있습니다:
```bash
~/.pyenv/versions/3.12.10/bin/python main.py
```

### 시스템 의존성 (macOS 기준)

아래 패키지는 Homebrew로 미리 설치해야 합니다.

```bash
# ffmpeg (오디오 변환/재생 필수)
brew install ffmpeg

# (필요시) 최신 tcl-tk (tkinter GUI 오류 발생 시)
brew install tcl-tk
```

- ffmpeg가 설치되어 있지 않으면 변환/재생 기능이 동작하지 않습니다.
- tcl-tk는 tkinter 관련 오류가 있을 때만 설치하면 됩니다.

### 참고
- Whisper 모델은 CPU에서 FP16 미지원 경고가 뜰 수 있으나, 정상 동작합니다.
- 네이버 Papago 번역은 현재 미구현 상태입니다. (Google Translate만 사용 가능)

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
- Python 3.8 or higher (tested with 3.12.10)
- Required packages: pydub, pygame, googletrans, requests, openai-whisper, torch, numpy  
  (See requirements.txt, tkinter is built-in)

### Installation and Setup

#### Using pyenv (Recommended)

1. Install and initialize pyenv
    ```bash
    brew install pyenv
    # Add to ~/.zshrc or ~/.bash_profile:
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    # Restart terminal
    ```

2. Install Python 3.12.10
    ```bash
    pyenv install 3.12.10
    pyenv local 3.12.10
    ```

3. Install packages
    ```bash
    pip install -r requirements.txt
    ```

4. Run the program
    ```bash
    python main.py
    ```

#### Running the Program Each Time

Run the program using pyenv-configured Python:
```bash
python main.py
```

Or directly using the pyenv Python path:
```bash
~/.pyenv/versions/3.12.10/bin/python main.py
```

### System Dependencies (macOS)

아래 패키지는 Homebrew로 미리 설치해야 합니다.

```bash
# ffmpeg (오디오 변환/재생 필수)
brew install ffmpeg

# (필요시) 최신 tcl-tk (tkinter GUI 오류 발생 시)
brew install tcl-tk
```

- ffmpeg가 설치되어 있지 않으면 변환/재생 기능이 동작하지 않습니다.
- tcl-tk는 tkinter 관련 오류가 있을 때만 설치하면 됩니다.

### Notes
- You may see a warning about FP16 not being supported on CPU for Whisper; this is normal.
- Naver Papago translation is not yet implemented. (Only Google Translate is available)

---
