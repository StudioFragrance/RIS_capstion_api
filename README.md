### 개발 환경 구축
- 소스코드 다운로드
    ```bash
    git clone https://github.com/MemoriaScent/pipeline.git
    ```
- 소스코드 폴더로 이동
    ```bash
    cd RIS_capstion_api
    ```
- VirtualEnv 구성
    ```bash
    python3 -m venv .venv
    ```
- VirtualEnv 활성화
    ```bash
    # Linux, macOS
    source .venv/bin/activate
    
    # Windows
    .venv/bin/activate.bat
    ```
- PIP 최신버전 업그레이드
    ```bash
    pip install -U pip
    ```
- 의존성 패키지 및 프로젝트 설치
    ```bash
    pip install -e .
    ```
- Kafka 구성 (Docker Compose 사용)
    ```bash
    docker compose up -d
    ```

### 개발 환경 종료
- Kafka 종료
    ```bash
    # 터미널의 Working Directory(pwd)가 프로젝트 최상단 폴더이어야 함 
    docker compose down
    ```
- VirtualEnv 해제
    ```bash
    # Linux, macOS, Windows
    deactivate
    ```
- Docker 임시 파일 삭제(선택사항)
    ```bash
    docker system prune -a
    ```
  
- 프로그램 실행
    ```bash
    cd recever
    python recever_main.py
    ```
    
    and
    
    ```bash
    cd sender
    python sender_main.py
```
