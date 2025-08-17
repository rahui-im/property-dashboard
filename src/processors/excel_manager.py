"""
Excel 파일 관리자 - 매물 데이터를 Excel로 저장/관리
"""
import pandas as pd
from datetime import datetime
import os
from typing import List, Dict

class ExcelManager:
    """Excel 파일 관리 클래스"""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def save_properties(self, properties: List[Dict], area: str) -> str:
        """매물 데이터를 Excel 파일로 저장"""
        if not properties:
            return None
        
        # DataFrame 생성
        df = pd.DataFrame(properties)
        
        # 가격 포맷팅 (억/만원 단위로 표시)
        df['가격_표시'] = df['price'].apply(self._format_price)
        
        # 평수 계산 (제곱미터 → 평)
        df['평수'] = (df['area'] * 0.3025).round(1)
        
        # 컬럼 순서 정리
        columns = ['id', 'platform', 'title', 'price', '가격_표시', 
                  'area', '평수', 'floor', 'address', 'description', 
                  'collected_at', 'url']
        
        df = df[columns]
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{area}_매물_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        # Excel 파일로 저장 (스타일 적용)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='매물목록', index=False)
            
            # 워크시트 가져오기
            worksheet = writer.sheets['매물목록']
            
            # 컬럼 너비 자동 조정
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        return filename
    
    def _format_price(self, price: int) -> str:
        """가격을 억/만원 단위로 포맷팅"""
        if price >= 100000000:  # 1억 이상
            eok = price // 100000000
            man = (price % 100000000) // 10000
            if man > 0:
                return f"{eok}억 {man:,}만원"
            else:
                return f"{eok}억원"
        else:
            man = price // 10000
            return f"{man:,}만원"
    
    def load_properties(self, filename: str) -> pd.DataFrame:
        """Excel 파일에서 매물 데이터 로드"""
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            return pd.read_excel(filepath)
        else:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
    
    def merge_files(self, pattern: str = "*.xlsx") -> pd.DataFrame:
        """여러 Excel 파일을 하나로 병합"""
        import glob
        
        all_files = glob.glob(os.path.join(self.output_dir, pattern))
        df_list = []
        
        for file in all_files:
            df = pd.read_excel(file)
            df_list.append(df)
        
        if df_list:
            merged_df = pd.concat(df_list, ignore_index=True)
            
            # 중복 제거
            merged_df = merged_df.drop_duplicates(subset=['id'], keep='last')
            
            return merged_df
        else:
            return pd.DataFrame()