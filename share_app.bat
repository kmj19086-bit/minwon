@echo off
echo ====================================================
echo   민원 해결사 AI - 외부 접속 링크 생성기 (Tunnel)
echo ====================================================
echo.
echo * 이 창이 켜져 있는 동안에만 다른 사람이 들어올 수 있습니다.
echo * 종료하려면 창을 닫거나 Ctrl + C를 누르세요.
echo.
echo 터널을 연결하는 중입니다... 잠시만 기다려 주세요.
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:8501 nokey@localhost.run
pause
