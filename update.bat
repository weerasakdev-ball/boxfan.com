@echo off
cd /d %~dp0
echo ════════════════════════════════════════
echo   BOXFAN — อัปเดตข้อมูลทั้งหมด
echo ════════════════════════════════════════
echo.
echo [1/2] Export ข้อมูลจาก DB...
python data\export_db.py
echo.
echo [2/2] สร้างหน้า Static นักมวย...
python data\generate_profiles.py
echo.
echo ════════════════════════════════════════
echo   เสร็จแล้ว! รีเฟรชหน้าเว็บได้เลย
echo ════════════════════════════════════════
pause
