@echo off
chcp 65001 >nul
cd /d %~dp0
title เขียนบทความ Boxfan
echo ════════════════════════════════════════
echo   เครื่องมือเขียนบทความ Boxfan
echo   เบราว์เซอร์จะเปิดหน้าเขียนบทความให้เอง
echo   ใช้เสร็จแล้ว ปิดหน้าต่างนี้ได้เลย
echo ════════════════════════════════════════
python article_editor.py
if errorlevel 1 (
  echo.
  echo   ✗ เปิดไม่สำเร็จ — ถ้าขึ้นว่าไม่มี markdown ให้พิมพ์:  pip install markdown pillow
  pause
)
