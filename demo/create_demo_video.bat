@echo off
echo PropertyYards Demo Video Creator
echo ============================
echo.
echo Creating demo video...
echo.

REM Create sample frame
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $bitmap = New-Object System.Drawing.Bitmap(1920, 1080); $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.FillRectangle([System.Drawing.Brushes]::DarkBlue, 0, 0, 1920, 1080); $font = New-Object System.Drawing.Font('Arial', 72); $graphics.DrawString('PropertyYards', $font, [System.Drawing.Brushes]::White, 600, 400); $font2 = New-Object System.Drawing.Font('Arial', 36); $graphics.DrawString('Demo Video - 4 Minutes', $font2, [System.Drawing.Brushes]::White, 550, 500); $bitmap.Save('propertyyards_demo.jpg', [System.Drawing.Imaging.ImageFormat]::Jpeg); $graphics.Dispose(); $bitmap.Dispose();"

echo Demo video preparation completed!
echo.
echo Files created:
if exist propertyyards_demo.jpg echo - propertyyards_demo.jpg (Sample frame)
if exist VIDEO_READY.md echo - VIDEO_READY.md (Video information)
echo.
echo Next Steps:
echo 1. Use professional video editing software
echo 2. Record voice narration
echo 3. Add screen recordings
echo 4. Export as MP4
echo.
pause
