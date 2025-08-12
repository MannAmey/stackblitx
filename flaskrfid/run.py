#!/usr/bin/env python3
"""
RFID Server - Flask Application Entry Point
"""
import os
from app import create_app

if __name__ == '__main__':
    app, socketio = create_app()
    
    port = int(os.getenv('PORT', 3003))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )