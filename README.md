# overlay-gpt-flask

#가상환경 폴더 만들기
python3 -m venv venv

#가상환경 진입(windows)
.\venv\Scripts\activate
#가상환경 진입 안될 시
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

#가상환경 진입(mac)
source venv/bin/activate

#필요한 라이브러리 설치
pip install -r requirements.txt

#앱 실행
python3 app.py
