@echo off
set COMMIT_MSG=%~1
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update backend

echo [1/4] Copying files to d:\hf_deploy...
xcopy "d:\ipoautomation\config" "d:\hf_deploy\config" /Y /E /I
xcopy "d:\ipoautomation\automation" "d:\hf_deploy\automation" /Y /E /I
copy "d:\ipoautomation\requirements.txt" "d:\hf_deploy\requirements.txt" /Y

echo.
echo [2/4] Switching to d:\hf_deploy...
cd /d d:\hf_deploy

echo.
echo [3/4] Committing changes...
git add .
git commit -m "%COMMIT_MSG%"

echo.
echo [4/4] Pushing to Hugging Face (hf)...
git push hf main

echo.
echo Deployment Complete!
pause
