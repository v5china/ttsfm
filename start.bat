@echo off
title TTSFM Server

REM Start Redis (assuming Redis is installed and in PATH)
echo Starting Redis Server...
start /B redis-server

REM Wait for Redis to start
timeout /t 2 /nobreak

REM Start Celery Worker
echo Starting Celery Worker...
start /B celery -A celery_worker.celery worker --pool=solo -l info

REM Wait for Celery to initialize
timeout /t 2 /nobreak

REM Start Flask Application
echo Starting Flask Application...
python app.py 