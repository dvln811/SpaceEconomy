import os

TICK_RATE = float(os.getenv("TICK_RATE", "1.0"))  # seconds between economy ticks
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "0"))  # 0 = random port for local dev
