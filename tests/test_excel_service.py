import unittest
import pandas as pd
import base64
from io import BytesIO
from services.excel_service import ExcelService

class TestExcelService(unittest.TestCase):
    def setUp(self):
        # 테스트용 엑셀 데이터 생성
        self.test_data = pd.DataFrame({
            '이름': ['홍길동', '김철수', '이영희'],
            '나이': [25, 30, 28],
            '직업': ['개발자', '디자이너', '마케터']
        })
        
        # DataFrame을 엑셀 파일로 변환
        output = BytesIO()
        self.test_data.to_excel(output, index=False)
        output.seek(0)
        
        # 엑셀 파일을 base64로 인코딩
        self.base64_data = base64.b64encode(output.getvalue()).decode('utf-8')
    
    def test_read_excel_data(self):
        # 엑셀 데이터 읽기 테스트
        df = ExcelService.read_excel_data(self.base64_data)
        
        # 결과 검증
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ['이름', '나이', '직업'])
        self.assertEqual(df.iloc[0]['이름'], '홍길동')
    
    def test_get_excel_summary(self):
        # 데이터 요약 정보 테스트
        df = ExcelService.read_excel_data(self.base64_data)
        summary = ExcelService.get_excel_summary(df)
        
        # 결과 검증
        self.assertIsNotNone(summary)
        self.assertEqual(summary['row_count'], 3)
        self.assertEqual(summary['column_count'], 3)
        self.assertEqual(summary['columns'], ['이름', '나이', '직업'])
        self.assertEqual(len(summary['sample_data']), 3)

if __name__ == '__main__':
    unittest.main() 