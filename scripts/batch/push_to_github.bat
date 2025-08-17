@echo off
echo GitHub Push Script for rahui-im
echo ================================

echo Setting remote origin...
git remote remove origin 2>nul
git remote add origin https://github.com/rahui-im/property-dashboard.git

echo Pushing to GitHub...
git push -u origin main

echo.
echo ✅ Complete! Check your repository at:
echo https://github.com/rahui-im/property-dashboard
echo.
echo 🚀 Next step: Deploy to Vercel
echo 1. Go to https://vercel.com
echo 2. Import this repository
echo 3. Deploy!
echo.
pause