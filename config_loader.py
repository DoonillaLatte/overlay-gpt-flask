import json
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """설정 파일들을 우선순위에 따라 로드"""
        
        # 1. 실행파일과 같은 디렉토리의 config.json 확인 (설치 버전)
        exe_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        config_paths = [
            exe_dir / "config.json",
            exe_dir.parent / "config.json",  # 상위 디렉토리
            Path("config.json"),  # 현재 디렉토리
        ]
        
        config_loaded = False
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                    logger.info(f"설정 파일 로드됨: {config_path}")
                    config_loaded = True
                    break
                except Exception as e:
                    logger.warning(f"설정 파일 로드 실패 {config_path}: {e}")
        
        # 2. .env 파일 로드 (개발 환경 또는 추가 설정)
        env_paths = [
            exe_dir / ".env",
            exe_dir.parent / ".env",
            Path(".env"),
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                try:
                    load_dotenv(env_path)
                    logger.info(f".env 파일 로드됨: {env_path}")
                    break
                except Exception as e:
                    logger.warning(f".env 파일 로드 실패 {env_path}: {e}")
        
        # 3. 환경 변수에서 API 키 확인
        env_api_key = os.getenv('OPENAI_API_KEY')
        if env_api_key:
            self.config['openai_api_key'] = env_api_key
            logger.info("환경 변수에서 OPENAI_API_KEY 로드됨")
        
        # 4. 설정 검증
        if not self.get_openai_api_key():
            logger.error("OpenAI API 키를 찾을 수 없습니다!")
            logger.error("다음 중 하나의 방법으로 API 키를 설정해주세요:")
            logger.error("1. config.json 파일에 설정")
            logger.error("2. .env 파일에 OPENAI_API_KEY 설정")
            logger.error("3. 환경 변수 OPENAI_API_KEY 설정")
    
    def get_openai_api_key(self):
        """OpenAI API 키 반환"""
        return self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
    
    def get_flask_port(self):
        """Flask 포트 반환"""
        return int(os.getenv('FLASK_PORT', self.config.get('flask_port', 5001)))
    
    def get_flask_env(self):
        """Flask 환경 반환"""
        return os.getenv('FLASK_ENV', self.config.get('flask_env', 'production'))
    
    def get_app_version(self):
        """앱 버전 반환"""
        return self.config.get('app_version', '1.0.0')
    
    def is_api_key_valid(self):
        """API 키 유효성 간단 검사"""
        api_key = self.get_openai_api_key()
        return api_key and len(api_key) > 20 and api_key.startswith('sk-')
    
    def create_sample_config(self, file_path="config.json"):
        """샘플 설정 파일 생성"""
        sample_config = {
            "openai_api_key": "your-api-key-here",
            "flask_port": 5001,
            "flask_env": "production",
            "app_version": "1.0.0"
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            logger.info(f"샘플 설정 파일 생성됨: {file_path}")
            return True
        except Exception as e:
            logger.error(f"샘플 설정 파일 생성 실패: {e}")
            return False

# 글로벌 설정 인스턴스
config = ConfigLoader() 