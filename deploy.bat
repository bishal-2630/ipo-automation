@echo off
set COMMIT_MSG=%~1
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update backend

echo [1/4] Copying files to d:\hf_deploy...
xcopy "d:\ipoautomation\config" "d:\hf_deploy\config" /Y /E /I
xcopy "d:\ipoautomation\automation" "d:\hf_deploy\automation" /Y /E /I
copy "d:\ipoautomation\requirements_api.txt" "d:\hf_deploy\requirements.txt" /Y
copy "d:\ipoautomation\manage.py" "d:\hf_deploy\manage.py" /Y
copy "d:\ipoautomation\main.py" "d:\hf_deploy\main.py" /Y
copy "d:\ipoautomation\notifications.py" "d:\hf_deploy\notifications.py" /Y
copy "d:\ipoautomation\expiry_handler.py" "d:\hf_deploy\expiry_handler.py" /Y
copy "d:\ipoautomation\Dockerfile" "d:\hf_deploy\Dockerfile" /Y
copy "d:\ipoautomation\.dockerignore" "d:\hf_deploy\.dockerignore" /Y
copy "d:\ipoautomation\run_github_automation.py" "d:\hf_deploy\run_github_automation.py" /Y
copy "d:\ipoautomation\start.sh" "d:\hf_deploy\start.sh" /Y

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
