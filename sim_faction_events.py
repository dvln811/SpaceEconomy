"""Run faction event system for N ticks and report results."""
import sys, sqlite3
sys.path.insert(0, '.')
from server.event_framework import FactionEventGenerator
from server.agent_lifecycle import process_event_effects, record_structured_event

TICKS = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
INTERVAL = 200  # same as worker

conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row

# Clear previous test data
conn.execute("DELETE FROM sim_events")
conn.execute("DELETE FROM agent_history")
conn.execute("UPDATE faction_agents SET alive=1, died_tick=0, cause_of_death=''")
conn.commit()

# Load data
agents_by_faction = {}
for row in conn.execute("SELECT * FROM faction_agents WHERE alive=1").fetchall():
    fid = row['faction_id']
    if fid not in agents_by_faction:
        agents_by_faction[fid] = []
    agents_by_faction[fid].append(dict(row))

systems_by_faction = {}
for row in conn.execute("SELECT id, name, faction_id FROM systems WHERE faction_id != ''").fetchall():
    fid = row['faction_id']
    if fid not in systems_by_faction:
        systems_by_faction[fid] = []
    systems_by_faction[fid].append((row['id'], row['name']))
conn.close()

gen = FactionEventGenerator()
total = 0
by_category = {}
by_severity = {1: 0, 2: 0, 3: 0, 4: 0}
deaths = 0

print(f"Running {TICKS} ticks ({TICKS // INTERVAL} event cycles)...\n")

for tick in range(0, TICKS, INTERVAL):
    events = gen.generate_tick_events(tick, agents_by_faction, systems_by_faction, {})
    for e in events:
        record_structured_event(e)
        process_event_effects(e)
        total += 1
        by_category[e.category] = by_category.get(e.category, 0) + 1
        by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
        if any(ef.get('type') in ('agent_killed', 'agent_lost') for ef in e.effects):
            deaths += 1
        # Print major+ events
        if e.severity >= 3:
            print(f"  T{tick:5d} [S{e.severity}] {e.title[:80]}")

# Report
conn = sqlite3.connect('data/game_data.db')
alive = conn.execute("SELECT count(*) FROM faction_agents WHERE alive=1").fetchone()[0]
dead = conn.execute("SELECT count(*) FROM faction_agents WHERE alive=0").fetchone()[0]
hist_count = conn.execute("SELECT count(*) FROM agent_history").fetchone()[0]
events_db = conn.execute("SELECT count(*) FROM sim_events").fetchone()[0]
chains = conn.execute("SELECT count(DISTINCT chain_id) FROM sim_events WHERE chain_id != ''").fetchone()[0]
conn.close()

print(f"\n{'='*60}")
print(f"Results after {TICKS} ticks ({TICKS*6/60:.0f} game-hours, {TICKS*6/1440:.1f} game-days):")
print(f"  Total events: {total}")
print(f"  By category: {dict(sorted(by_category.items()))}")
print(f"  By severity: Minor={by_severity[1]} Notable={by_severity[2]} Major={by_severity[3]} Critical={by_severity[4]}")
print(f"  Event chains: {chains}")
print(f"  Agent deaths: {deaths}")
print(f"  Agents alive: {alive} | dead: {dead}")
print(f"  History entries: {hist_count}")
print(f"  DB events stored: {events_db}")
