@echo off
chcp 65001 >nul
cd /d %~dp0
echo ════════════════════════════════════════
echo   BOXFAN — อัปเดตเว็บหลังแก้ข้อมูล
echo ════════════════════════════════════════
echo.
echo [1/3] สร้างสารบัญนักมวย (data\fighters_index.js) ให้หน้าเว็บโหลดเร็ว
python build_index.py
if errorlevel 1 goto fail
echo.
echo [2/3] สร้างหน้าโปรไฟล์นักมวย (fighters\*.html)
python data\generate_profiles.py
if errorlevel 1 goto fail
echo.
echo [3/3] ฝังตารางอันดับ/ผลมวย/โปรแกรมชกลง HTML + หน้าแยกรุ่น + sitemap
python build_seo.py
if errorlevel 1 goto fail
echo.
echo ════════════════════════════════════════
echo   เสร็จแล้ว! ตรวจหน้าเว็บ แล้ว Commit + Push ขึ้น GitHub ได้เลย
echo ════════════════════════════════════════
pause
exit /b 0
:fail
echo.
echo   ✗ มีข้อผิดพลาด — อ่านข้อความด้านบน (ไฟล์เดิมไม่ถูกแก้ในขั้นที่ล้มเหลว)
echo     ยังไม่ต้อง Push ขึ้นเว็บ
pause
exit /b 1
