@echo off
chcp 65001 >nul
cd /d %~dp0
echo BOXFAN — build_seo.py (ฝังเนื้อหาลง HTML ให้ Google อ่านได้ + sitemap)
python build_seo.py
pause
