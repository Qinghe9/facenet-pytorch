@REM ----------------------------------------------------------------------------
@REM Maven Wrapper startup batch script
@REM ----------------------------------------------------------------------------

@echo off
setlocal

set MAVEN_PROJECTBASEDIR=%~dp0
set WRAPPER_JAR="%MAVEN_PROJECTBASEDIR%.mvn\wrapper\maven-wrapper.jar"
set WRAPPER_URL="https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.2.0/maven-wrapper-3.2.0.jar"

if exist %WRAPPER_JAR% (
    echo Found Maven Wrapper JAR
) else (
    echo Maven Wrapper JAR not found, downloading...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('%WRAPPER_URL%', '%WRAPPER_JAR%')"
)

if not exist %WRAPPER_JAR% (
    echo ERROR: Failed to download Maven Wrapper JAR
    exit /b 1
)

@REM Build the classpath
set CLASSPATH=%WRAPPER_JAR%

@REM Execute Maven
java -classpath %CLASSPATH% org.apache.maven.wrapper.MavenWrapperMain %*

endlocal
