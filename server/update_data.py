"""Live data update script. Pauses simulation, re-migrates game_data.db, resumes.
Usage: python -m server.update_data

This allows updating items, ships, systems, factions without nuking the simulation state.
The simulation state (inventories, ship positions, prices) is preserved.
"""
import time
import requests
import sys
import os

# Server URL
BASE_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8000")


def main():
    print("=== LIVE DATA UPDATE ===")
    print(f"Target: {BASE_URL}")
    print()

    # Step 1: Pause simulation
    print("1. Pausing simulation...")
    try:
        r = requests.post(f"{BASE_URL}/api/speed", json={"multiplier": 0})
        print(f"   Speed set to 0 (paused)")
    except Exception as e:
        print(f"   WARNING: Could not pause ({e}). Proceeding anyway...")

    # Step 2: Re-run migration to update game_data.db
    print("2. Re-migrating game_data.db from Python sources...")
    from server.migrate_to_db import migrate
    migrate()
    print("   Migration complete.")

    # Step 3: Signal server to reload data (if API exists)
    print("3. Signaling server to reload game data...")
    try:
        r = requests.post(f"{BASE_URL}/api/reload_data")
        if r.status_code == 200:
            print(f"   Server reloaded successfully.")
        else:
            print(f"   Reload endpoint not available. Server restart needed.")
    except:
        print("   Could not reach server. Data will load on next restart.")

    # Step 4: Resume simulation
    print("4. Resuming simulation...")
    try:
        r = requests.post(f"{BASE_URL}/api/speed", json={"multiplier": 1})
        print(f"   Speed set to 1 (resumed)")
    except:
        print("   Could not resume. Set speed manually via debug page.")

    print()
    print("=== UPDATE COMPLETE ===")
    print("Game data updated. Simulation state preserved.")
    print("No nuke required.")


if __name__ == "__main__":
    main()
