"""
부동산 매물 데이터 모델
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class PropertyType(str, Enum):
    """매물 유형 - 총 18개"""
    # 주거용 (1행)
    APT = "아파트"
    OFFICETEL = "오피스텔"
    VILLA = "빌라"
    APT_PRESALE = "아파트분양권"
    OFFICETEL_PRESALE = "오피스텔분양권"
    REDEVELOPMENT = "재건축"
    
    # 주택 (2행)
    TOWNHOUSE = "전원주택"
    DETACHED = "단독/다가구"
    RETAIL_HOUSE = "상가주택"
    HANOK = "한옥주택"
    RECONSTRUCTION = "재개발"
    ONEROOM = "원룸"
    
    # 상업/기타 (3행)
    RETAIL = "상가"
    OFFICE = "사무실"
    WAREHOUSE = "공장/창고"
    LAND = "토지"
    KNOWLEDGE_CENTER = "지식산업센터"
    ACCOMMODATION = "숙박/펜션"


class TradeType(str, Enum):
    """거래 유형"""
    SALE = "매매"
    RENT = "전세"
    MONTHLY = "월세"
    SHORT = "단기"


class Platform(str, Enum):
    """플랫폼"""
    NAVER = "naver"
    ZIGBANG = "zigbang"
    DABANG = "dabang"
    KB = "kb"
    HOGANG = "hogang"


class PropertyBase(BaseModel):
    """매물 기본 정보"""
    
    # 식별 정보
    platform: Platform = Field(..., description="플랫폼")
    property_id: str = Field(..., description="매물 고유 ID")
    property_type: PropertyType = Field(..., description="매물 유형")
    trade_type: TradeType = Field(..., description="거래 유형")
    
    # 기본 정보
    title: str = Field(..., description="매물 제목")
    address: str = Field(..., description="주소")
    address_detail: Optional[str] = Field(None, description="상세 주소")
    
    # 가격 정보
    price: int = Field(..., description="가격 (만원)")
    deposit: Optional[int] = Field(None, description="보증금 (월세의 경우)")
    monthly_fee: Optional[int] = Field(None, description="월세")
    maintenance_fee: Optional[int] = Field(None, description="관리비")
    
    # 면적 정보
    area_exclusive: Optional[float] = Field(None, description="전용면적 (㎡)")
    area_supply: Optional[float] = Field(None, description="공급면적 (㎡)")
    area_land: Optional[float] = Field(None, description="대지면적 (㎡)")
    
    # 위치 정보
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    
    # 건물 정보
    floor: Optional[str] = Field(None, description="층수")
    total_floors: Optional[int] = Field(None, description="전체 층수")
    direction: Optional[str] = Field(None, description="방향")
    room_count: Optional[int] = Field(None, description="방 개수")
    bathroom_count: Optional[int] = Field(None, description="욕실 개수")
    
    # 기타 정보
    parking: Optional[bool] = Field(None, description="주차 가능 여부")
    elevator: Optional[bool] = Field(None, description="엘리베이터 유무")
    move_in_date: Optional[str] = Field(None, description="입주 가능일")
    
    # 부동산 정보
    realtor_name: Optional[str] = Field(None, description="부동산 이름")
    realtor_phone: Optional[str] = Field(None, description="부동산 전화번호")
    
    # 메타 정보
    collected_at: datetime = Field(default_factory=datetime.now, description="수집 시간")
    updated_at: Optional[datetime] = Field(None, description="업데이트 시간")
    is_active: bool = Field(True, description="활성 상태")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ApartmentProperty(PropertyBase):
    """아파트 매물"""
    
    complex_name: str = Field(..., description="단지명")
    complex_id: Optional[str] = Field(None, description="단지 ID")
    household_count: Optional[int] = Field(None, description="세대수")
    built_year: Optional[int] = Field(None, description="건축년도")
    constructor: Optional[str] = Field(None, description="건설사")
    heating_type: Optional[str] = Field(None, description="난방 방식")
    
    @validator('property_type', pre=True, always=True)
    def set_property_type(cls, v):
        return PropertyType.APT


class OfficetelProperty(PropertyBase):
    """오피스텔 매물"""
    
    building_name: str = Field(..., description="건물명")
    business_possible: Optional[bool] = Field(None, description="사업자 등록 가능")
    residential_ratio: Optional[float] = Field(None, description="주거 비율")
    
    @validator('property_type', pre=True, always=True)
    def set_property_type(cls, v):
        return PropertyType.OFFICETEL


class VillaProperty(PropertyBase):
    """빌라/연립 매물"""
    
    building_name: Optional[str] = Field(None, description="건물명")
    built_year: Optional[int] = Field(None, description="건축년도")
    
    @validator('property_type', pre=True, always=True)
    def set_property_type(cls, v):
        return PropertyType.VILLA


class PropertyCollection(BaseModel):
    """매물 컬렉션"""
    
    area: str = Field(..., description="검색 지역")
    platform: Platform = Field(..., description="플랫폼")
    trade_type: TradeType = Field(..., description="거래 유형")
    property_types: List[PropertyType] = Field(..., description="매물 유형 리스트")
    total_count: int = Field(..., description="전체 매물 수")
    properties: List[PropertyBase] = Field(..., description="매물 리스트")
    collected_at: datetime = Field(default_factory=datetime.now, description="수집 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchFilter(BaseModel):
    """검색 필터"""
    
    area: Optional[str] = Field(None, description="지역")
    property_types: Optional[List[PropertyType]] = Field(None, description="매물 유형")
    trade_type: Optional[TradeType] = Field(None, description="거래 유형")
    
    # 가격 범위
    price_min: Optional[int] = Field(None, description="최소 가격")
    price_max: Optional[int] = Field(None, description="최대 가격")
    
    # 면적 범위
    area_min: Optional[float] = Field(None, description="최소 면적")
    area_max: Optional[float] = Field(None, description="최대 면적")
    
    # 층수
    floor_min: Optional[int] = Field(None, description="최소 층수")
    floor_max: Optional[int] = Field(None, description="최대 층수")
    
    # 방 개수
    room_count_min: Optional[int] = Field(None, description="최소 방 개수")
    room_count_max: Optional[int] = Field(None, description="최대 방 개수")
    
    # 기타 옵션
    parking: Optional[bool] = Field(None, description="주차 가능")
    elevator: Optional[bool] = Field(None, description="엘리베이터")
    
    # 플랫폼
    platforms: Optional[List[Platform]] = Field(None, description="플랫폼 리스트")


class TaskRequest(BaseModel):
    """작업 요청"""
    
    task_type: str = Field(..., description="작업 유형")
    area: str = Field(..., description="지역")
    property_types: Optional[List[PropertyType]] = Field(None, description="매물 유형")
    trade_type: Optional[TradeType] = Field(TradeType.SALE, description="거래 유형")
    platforms: Optional[List[Platform]] = Field(None, description="플랫폼")
    filters: Optional[SearchFilter] = Field(None, description="검색 필터")
    priority: int = Field(1, description="우선순위 (1-10)")
    
    class Config:
        schema_extra = {
            "example": {
                "task_type": "collect",
                "area": "강남구",
                "property_types": ["아파트", "오피스텔"],
                "trade_type": "매매",
                "platforms": ["naver"],
                "priority": 5
            }
        }


class TaskResponse(BaseModel):
    """작업 응답"""
    
    task_id: str = Field(..., description="작업 ID")
    status: str = Field(..., description="상태")
    message: Optional[str] = Field(None, description="메시지")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }