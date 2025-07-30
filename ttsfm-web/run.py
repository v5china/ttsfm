#!/usr/bin/env python
"""
Run script for TTSFM web application with proper eventlet initialization
"""

# MUST be the first imports for eventlet to work properly
import eventlet
eventlet.monkey_patch()

# Now import the app
from app import app, socketio, HOST, PORT, DEBUG

if __name__ == '__main__':
    print(f"Starting TTSFM with WebSocket support on {HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)