@echo off
IF "%~1"=="" (
	echo Enter a version
	goto end_of_script
)
echo Version: %1
echo Preparing to build release...
set ver-num=%1
set base-dir=%CD%\..
set deploy-dir=%CD%
set output-dir=%CD%\..\Releases

echo INFO: Creating cmd zip file...
set "destination=%deploy-dir%\Multi-Drive Backup Tool-%ver-num%-cmd.zip"
del "%destination%" /Q /F >nul 2>&1
for %%a in ("%base-dir%\backup.py","%base-dir%\configuration.py","%base-dir%\entry.py","%base-dir%\exclusions.py","%base-dir%\LICENSE","%base-dir%\limitations.py","%base-dir%\log.py","%base-dir%\mdbt.py","%base-dir%\observer.py","%base-dir%\README.md","%base-dir%\USAGE_CLI.md","%base-dir%\USAGE_CMD.md","%base-dir%\USAGE_GUI.md","%base-dir%\util.py") do (
  echo Zipping %%~fa
  if not exist "%destination%" (
    call zipjs.bat zipItem -source "%%~fa" -destination "%destination%" -force no
  ) else (
    call zipjs.bat addToZip -source  "%%~fa" -destination "%destination%" -force no
  )
)

echo INFO: Compiling the executables for the cli and gui...
pyinstaller --onefile --icon="%base-dir%\Icon\icon.ico" "%base-dir%\mdbt_gui.pyw" -w
pyinstaller --onefile --icon="%base-dir%\Icon\icon.ico" "%base-dir%\mdbt_cli.py" -c

echo INFO: Updating version number in the iss files...
python "%deploy-dir%\iss_update_version.py" "%deploy-dir%\setup_cli.iss" "%ver-num%"
python "%deploy-dir%\iss_update_version.py" "%deploy-dir%\setup_gui.iss" "%ver-num%"

echo INFO: Building the installers...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "%deploy-dir%\setup_cli.iss"
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "%deploy-dir%\setup_gui.iss"

echo INFO: Cleaning up...
del "%deploy-dir%\dist\mdbt_cli.exe" /Q /F >nul 2>&1
del "%deploy-dir%\dist\mdbt_gui.exe" /Q /F >nul 2>&1
MOVE /Y "%deploy-dir%\Output\Multi-Drive Backup Tool-%ver-num%-cli.exe" "%output-dir%\Multi-Drive Backup Tool-%ver-num%-cli.exe"
MOVE /Y "%deploy-dir%\Output\Multi-Drive Backup Tool-%ver-num%-gui.exe" "%output-dir%\Multi-Drive Backup Tool-%ver-num%-gui.exe"
MOVE /Y "%deploy-dir%\Multi-Drive Backup Tool-%ver-num%-cmd.zip" "%output-dir%\Multi-Drive Backup Tool-%ver-num%-cmd.zip"
del /Q "%deploy-dir%\mdbt_cli.spec"
del /Q "%deploy-dir%\mdbt_gui.spec"
rmdir /S /Q "%deploy-dir%\Output"
rmdir /S /Q "%deploy-dir%\build"
rmdir /S /Q "%deploy-dir%\dist"

echo.
echo.
echo Release build successfully completed for version "%ver-num%".
echo All new files are in the Releases subdirectory.
echo REMEMBER TO CHANGE APP_VERSION IN UTIL.PY
echo IF ANY NEW FILES WERE ADDED, OPEN THIS SCRIPT AND MANUALLY ADD THEM TO CMD FILE LIST

:end_of_script
PAUSE