@echo off
echo Starting Email MCP Services...
echo.

echo Starting Auth Server...
start "Auth Server" cmd /k "uv run auth_server.py"


echo.
echo Services started! Check the opened windows for logs.
pause 