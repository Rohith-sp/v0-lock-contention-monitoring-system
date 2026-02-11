"""
Flask Web Server with Thread Contention
Demonstrates real HTTP server contention for auto-split demo
"""

from flask import Flask, jsonify
import threading
import time
import sys
import random

app = Flask(__name__)

# Shared resource that creates contention
request_counter = 0
counter_lock = threading.Lock()

# Server configuration
PORT = 5000

@app.route('/')
def home():
    """Handle basic HTTP request"""
    global request_counter
    
    # Simulate some processing
    time.sleep(random.uniform(0.01, 0.05))
    
    # Update shared counter (creates lock contention)
    with counter_lock:
        request_counter += 1
        count = request_counter
    
    return jsonify({
        'message': 'Hello from Flask server',
        'port': PORT,
        'request_number': count,
        'thread': threading.current_thread().name
    })

@app.route('/heavy')
def heavy():
    """Simulate heavy computation"""
    # More processing = more thread time = more contention
    time.sleep(random.uniform(0.1, 0.3))
    
    with counter_lock:
        request_counter += 1
        count = request_counter
    
    return jsonify({
        'message': 'Heavy task completed',
        'port': PORT,
        'request_number': count
    })

@app.route('/stats')
def stats():
    """Show server statistics"""
    return jsonify({
        'port': PORT,
        'total_requests': request_counter,
        'active_threads': threading.active_count()
    })

def main():
    global PORT
    
    # Get port from command line
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            print("Usage: python web_server.py [port]")
            print("Example: python web_server.py 5000")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"  Flask Web Server")
    print(f"{'='*60}")
    print(f"  Port: {PORT}")
    print(f"  Endpoints:")
    print(f"    - http://localhost:{PORT}/")
    print(f"    - http://localhost:{PORT}/heavy")
    print(f"    - http://localhost:{PORT}/stats")
    print(f"{'='*60}\n")
    
    # Run with threading enabled (creates thread pool)
    app.run(
        host='0.0.0.0',
        port=PORT,
        threaded=True,
        debug=False,
        use_reloader=False  # Disable reloader for demo
    )

if __name__ == '__main__':
    main()
