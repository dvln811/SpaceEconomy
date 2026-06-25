"""Start local server for browser-based debugging.
Speed defaults to 1x - use the Dashboard speed dropdown to increase.
At high speeds (120x+), close extra browser tabs to reduce GIL contention."""
import sys, os
sys.path.insert(0, '.')
os.environ['PORT'] = '8000'
os.remove('data/game.db') if os.path.exists('data/game.db') else None

import server.main as m
print("Starting server at http://127.0.0.1:8000 (1x speed, use Dashboard to change)")
m.app.run(debug=False, host="0.0.0.0", port=8000, threaded=True)
