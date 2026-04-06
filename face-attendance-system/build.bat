@echo off
chcp 65001 >nul
setlocal

set JAVA_HOME=E:\jdk\dk-26
set PATH=%JAVA_HOME%\bin;%PATH%

cd /d D:\Qinghe\opencv-face\facenet-pytorch\face-attendance-system

echo ====== Compiling Project ======
call apache-maven\apache-maven-3.9.6\bin\mvn.cmd clean compile -DskipTests

if %ERRORLEVEL% NEQ 0 (
    echo ====== Compilation Failed ======
    exit /b 1
)

echo ====== Compilation Successful ======
exit /b 0
