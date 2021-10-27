@echo off
setlocal EnableDelayedExpansion EnableExtensions

REM Check Java

REM JAVA_HOME not defined
IF NOT DEFINED JAVA_HOME ( 

  java -version > nul 2>&1 
  IF NOT %errorlevel% == 0 (
    @echo Java 1.8 or later is required to run Registry Manager.
    endlocal
    exit /b 0
  )

  set "JAVA=java"
  goto :get-rm-home
)

REM JAVA_HOME defined
IF "%JAVA_HOME:~-1%" == "\" set JAVA_HOME=%JAVA_HOME:~0,-1%
IF NOT EXIST "%JAVA_HOME%\bin\java.exe" (
  @echo java.exe not found in %JAVA_HOME%\bin. Please set JAVA_HOME to a valid directory.
  endlocal
  exit /b 0
)

set "JAVA=%JAVA_HOME%\bin\java"

:get-rm-home

REM Get top-level Registry Manager directory

set SDIR=%~dp0
IF "%SDIR:~-1%" == "\" set SDIR=%SDIR:~0,-1%
set SDIR=%SDIR%\..
pushd %SDIR%
set REGISTRY_MANAGER_HOME=%CD%
popd

REM Get executable jar. 
REM NOTE. We can hardcode the version, but have to change the script every release.

FOR /f %%f IN ('dir /b /s "%REGISTRY_MANAGER_HOME%\dist\registry-manager-*.jar"') DO (
  set "TOOL_JAR=%%~f"
)

REM Run Registry Manager

"%JAVA%" -jar "%TOOL_JAR%" %*

endlocal
