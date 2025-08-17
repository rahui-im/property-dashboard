# 🚀 GitHub & Vercel 배포 가이드

## 📝 Step 1: GitHub에 업로드

### 1.1 GitHub 리포지토리 생성
1. GitHub.com에 로그인
2. 우측 상단 **"+"** 클릭 → **"New repository"**
3. Repository name: `property-dashboard` (또는 원하는 이름)
4. Public 선택
5. **"Create repository"** 클릭

### 1.2 로컬 프로젝트와 GitHub 연결

```bash
# GitHub 리포지토리 URL 추가 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/property-dashboard.git

# 코드 푸시
git branch -M main
git push -u origin main
```

**만약 에러가 나면:**
```bash
# 토큰 생성이 필요한 경우
# GitHub → Settings → Developer settings → Personal access tokens → Generate new token
# repo 권한 체크 후 생성

# 푸시 재시도
git push -u origin main
# Username: YOUR_GITHUB_USERNAME
# Password: YOUR_PERSONAL_ACCESS_TOKEN
```

## 🎨 Step 2: Vercel 배포

### 2.1 Vercel 계정 설정
1. [vercel.com](https://vercel.com) 접속
2. **"Sign Up"** → GitHub으로 로그인
3. 권한 승인

### 2.2 프로젝트 Import
1. Vercel 대시보드에서 **"Add New..."** → **"Project"**
2. **"Import Git Repository"**
3. 방금 만든 `property-dashboard` 리포지토리 선택
4. **"Import"** 클릭

### 2.3 배포 설정
1. **Framework Preset**: Next.js (자동 감지됨)
2. **Build Command**: `npm run build` (기본값)
3. **Output Directory**: `out` (기본값)
4. **Install Command**: `npm install` (기본값)
5. **"Deploy"** 클릭

### 2.4 배포 완료
- 2-3분 후 배포 완료
- URL 형태: `https://property-dashboard-YOUR_USERNAME.vercel.app`

## 📱 Step 3: 모바일 확인

1. 배포된 URL을 모바일에서 접속
2. 반응형 디자인 확인
3. 차트와 테이블이 모바일에서도 잘 보이는지 확인

## 🔧 Step 4: 업데이트 방법

### 코드 수정 후 자동 배포
```bash
# 파일 수정 후
git add -A
git commit -m "Update: 설명"
git push

# Vercel이 자동으로 감지하고 재배포 (2-3분)
```

## 🎯 Step 5: 커스텀 도메인 (선택사항)

1. Vercel 프로젝트 → Settings → Domains
2. 도메인 추가 (예: `samsung-property.com`)
3. DNS 설정 안내 따라하기

## ⚠️ 주의사항

### 데이터 크기
- `public/data.js` 파일이 너무 크면 (10MB 이상) 배포 실패 가능
- 현재는 상위 100개 매물만 포함

### 환경 변수
- API 키가 필요한 경우 Vercel → Settings → Environment Variables에서 설정

### 빌드 에러 해결
```bash
# 로컬에서 먼저 테스트
npm install
npm run build

# 에러가 있으면 수정 후 다시 푸시
```

## 🔗 유용한 링크

- GitHub 리포지토리: `https://github.com/YOUR_USERNAME/property-dashboard`
- Vercel 대시보드: `https://vercel.com/dashboard`
- 배포된 사이트: `https://property-dashboard-YOUR_USERNAME.vercel.app`

## 📞 도움이 필요하면

1. Vercel 로그 확인: 프로젝트 → Functions 탭 → Logs
2. GitHub Issues에 문제 작성
3. Vercel Support: https://vercel.com/support

---

**성공적인 배포를 축하합니다! 🎉**