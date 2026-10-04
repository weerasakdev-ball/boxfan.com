@echo off
chcp 65001 >nul
cd /d %~dp0
echo ════════════════════════════════════════
echo   BOXFAN — สร้างหน้า Static นักมวย + SEO
echo ════════════════════════════════════════
echo.
echo [1/2] สร้างหน้าโปรไฟล์นักมวย (fighters\*.html)
python data\generate_profiles.py
if errorlevel 1 goto fail
echo.
echo [2/2] ฝังตารางอันดับ/ผลมวย/โปรแกรมชกลง HTML + หน้าแยกรุ่น + sitemap
python build_seo.py
if errorlevel 1 goto fail
echo.
echo ════════════════════════════════════════
echo   เสร็จแล้ว! ตรวจหน้าเว็บ แล้ว push ขึ้น GitHub ได้เลย
echo ════════════════════════════════════════
pause
exit /b 0
:fail
echo.
echo   ✗ มีข้อผิดพลาด — อ่านข้อความด้านบน (ไฟล์เดิมไม่ถูกแก้ในหน้าที่ล้มเหลว)
pause
exit /b 1
