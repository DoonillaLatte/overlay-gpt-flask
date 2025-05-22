import base64
import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class ExcelService:
    @staticmethod
    def read_excel_data(base64_data):
        """
        base64로 인코딩된 엑셀 데이터를 읽어 pandas DataFrame으로 변환합니다.
        
        Args:
            base64_data (str): base64로 인코딩된 엑셀 파일 데이터
            
        Returns:
            pd.DataFrame: 엑셀 데이터를 담은 DataFrame
            None: 에러 발생 시
        """
        try:
            # base64 데이터를 디코딩
            excel_data = base64.b64decode(base64_data)
            
            # BytesIO 객체로 변환
            excel_file = BytesIO(excel_data)
            
            # pandas로 엑셀 파일 읽기
            df = pd.read_excel(excel_file)
            
            return df
        except Exception as e:
            logger.error(f"엑셀 파일 읽기 오류: {str(e)}")
            return None
    
    @staticmethod
    def get_excel_summary(df):
        """
        엑셀 데이터의 기본적인 요약 정보를 반환합니다.
        
        Args:
            df (pd.DataFrame): 엑셀 데이터
            
        Returns:
            dict: 데이터 요약 정보
        """
        if df is None:
            return None
            
        try:
            summary = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': df.columns.tolist(),
                'data_types': df.dtypes.to_dict(),
                'missing_values': df.isnull().sum().to_dict(),
                'sample_data': df.head().to_dict('records')
            }
            return summary
        except Exception as e:
            logger.error(f"데이터 요약 생성 중 오류 발생: {str(e)}")
            return None 