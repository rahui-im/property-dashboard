# 🚀 GitHub 푸시 가이드

## 방법 1: GitHub Desktop 사용 (가장 쉬움)

1. [GitHub Desktop 다운로드](https://desktop.github.com/)
2. 설치 후 GitHub 계정으로 로그인
3. **File → Add Local Repository**
4. `D:\property-collector` 폴더 선택
5. **Publish repository** 클릭
6. Repository name: `property-dashboard`
7. **Publish** 클릭

## 방법 2: 명령어로 푸시 (Personal Access Token 필요)

### Token 생성
1. GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token (classic)
4. 권한 선택: `repo` 전체 체크
5. Generate token
6. 토큰 복사 (한 번만 보임!)

### 푸시 명령어
```bash
git remote set-url origin https://YOUR_TOKEN@github.com/rahui-im/property-dashboard.git
git push -u origin main
```

## 방법 3: Git Bash에서 직접 입력

```bash
git push https://github.com/rahui-im/property-dashboard.git main

# Username 입력: rahui-im
# Password 입력: YOUR_PERSONAL_ACCESS_TOKEN (비밀번호 아님!)
```

## 방법 4: SSH Key 사용

1. SSH 키 생성
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

2. 공개키 복사
```bash
cat ~/.ssh/id_ed25519.pub
```

3. GitHub → Settings → SSH and GPG keys → New SSH key
4. 키 붙여넣기

5. 푸시
```bash
git remote set-url origin git@github.com:rahui-im/property-dashboard.git
git push -u origin main
```

## 🎯 가장 빠른 방법

**GitHub Desktop을 추천합니다!**
- 로그인만 하면 자동으로 인증 처리
- GUI로 쉽게 관리 가능
- 충돌 해결도 쉬움

---

## ✅ 푸시 성공 후 Vercel 배포

1. [vercel.com](https://vercel.com) 접속
2. **Import Git Repository**
3. `rahui-im/property-dashboard` 선택
4. **Deploy** 클릭

배포 URL: `https://property-dashboard-rahui-im.vercel.app`