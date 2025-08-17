# 🚀 Vercel 실시간 검색 배포 가이드

## 📝 Vercel 배포 단계

### 1. Vercel 프로젝트 설정
1. [vercel.com](https://vercel.com) 접속
2. 프로젝트 Import (이미 있다면 Settings로 이동)

### 2. 중요 설정 변경

#### Root Directory 설정
- **Settings → General → Root Directory**
- 값: `frontend` 입력
- **Save** 클릭

#### Environment Variables 설정 (선택사항)
- **Settings → Environment Variables**
- 변수 추가:
  - Name: `NEXT_PUBLIC_API_URL`
  - Value: (비워두기 - 내장 API 사용)
  - Environment: Production

### 3. 재배포
- **Deployments** 탭
- 최신 배포 옆 점 3개 클릭
- **Redeploy** → **Redeploy** 클릭

## 🎯 배포 후 확인사항

### 실시간 검색 테스트
1. 배포된 URL 접속
2. **🔍 주소 검색** 모드 선택
3. **🟢 실시간 모드** 활성화
4. 주소 입력 (예: "삼성동 151")
5. 검색 결과 확인

### API 엔드포인트
```
https://your-app.vercel.app/api/realtime-search?address=삼성동&platforms=all
```

## 📊 기능 비교

| 기능 | 로컬 | Vercel |
|------|------|--------|
| 정적 데이터 검색 | ✅ | ✅ |
| 실시간 네이버 검색 | ✅ | ✅ |
| 실시간 직방 검색 | ✅ | ✅ |
| 다방/KB 검색 | ✅ | ❌ (API 제한) |
| 응답 속도 | 빠름 | 보통 |
| 데이터 최신성 | 실시간 | 실시간 |

## ⚠️ 제한사항

### Vercel 무료 플랜
- Serverless Function 실행시간: 10초
- 월 100GB 대역폭
- API 호출 제한 있음

### 외부 API 제한
- 일부 부동산 API는 CORS 정책으로 직접 호출 불가
- 네이버/직방은 공개 API 사용 가능
- 다방/KB는 별도 백엔드 서버 필요

## 🔧 문제 해결

### "실시간 검색이 안 돼요"
1. Vercel 콘솔에서 Functions 로그 확인
2. API 엔드포인트 직접 테스트
3. CORS 에러 확인

### "Root Directory 설정을 못 찾겠어요"
1. Settings → General 탭
2. "Root Directory" 섹션
3. `frontend` 입력 후 Save

### "배포가 실패해요"
1. Build 로그 확인
2. package.json이 frontend 폴더에 있는지 확인
3. node_modules 삭제 후 재시도

## 📱 사용 방법

### 1. 주소 검색 (캐시 모드)
- 빠른 검색
- 저장된 100개 데이터에서 검색
- 오프라인 가능

### 2. 실시간 검색
- 최신 매물 정보
- 네이버, 직방 실시간 데이터
- 5-10초 소요

## 🎉 완료!

이제 Vercel에서 실시간 부동산 검색이 가능합니다!

- **배포 URL**: `https://property-dashboard-[your-subdomain].vercel.app`
- **API 문서**: 배포 URL + `/api/realtime-search`

---

문제가 있으면 GitHub Issues에 문의해주세요.