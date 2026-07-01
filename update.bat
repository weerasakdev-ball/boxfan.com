@echo off
cd /d %~dp0
echo กำลังอัปเดตข้อมูล...
python data\export_db.py
echo.
echo เสร็จแล้ว! รีเฟรชหน้าเว็บได้เลยครับ
pause