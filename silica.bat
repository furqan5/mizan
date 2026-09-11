@echo off
SET PATH=;C:/Program Files/OpenModelica1.27.0-64bit/bin/;%PATH%;
SET ERRORLEVEL=
CALL "%CD%/silica.exe" %*
SET RESULT=%ERRORLEVEL%

EXIT /b %RESULT%
