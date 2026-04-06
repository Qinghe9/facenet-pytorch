$env:JAVA_HOME = "E:\jdk\dk-26"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

$projectDir = "D:\Qinghe\opencv-face\facenet-pytorch\face-attendance-system"
Set-Location $projectDir

Write-Host "Java Version:"
java -version 2>&1

Write-Host ""
Write-Host "===== Compiling Project ====="
& "$projectDir\.apache-maven\apache-maven-3.9.6\bin\mvn.cmd" clean compile -DskipTests 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===== Compilation Successful ====="
} else {
    Write-Host ""
    Write-Host "===== Compilation Failed ====="
    exit 1
}
