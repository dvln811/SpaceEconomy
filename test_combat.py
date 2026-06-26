"""Test harness for combat engine: run battles, print event logs, benchmark at scale."""
import time, json, sys
sys.path.insert(0, '.')
from server.combat_engine import CombatEngine, make_ship, make_weapon, DmgType

def create_test_fleet(faction, size, prefix="ship"):
    """Generate a fleet of mixed composition."""
    fleet = []
    for i in range(size):
        # Mix of ship types
        if i % 5 == 0:  # 20% tanky shield ships
            weapons = [
                make_weapon("Beam Laser", "EM", 80, rof=0.8, tracking=50, size="M"),
                make_weapon("Beam Laser", "EM", 80, rof=0.8, tracking=50, size="M"),
                make_weapon("Missile", "Explosive", 100, rof=0.5, tracking=90, size="M"),
            ]
            ship = make_ship(f"{prefix}_{i}", f"{faction} Cruiser {i}", faction, "Cruiser",
                           shield=2000, armor=800, hull=600, weapons=weapons, speed=80, signature=80)
        elif i % 5 == 1:  # 20% armor brawlers
            weapons = [
                make_weapon("Autocannon", "Kinetic", 60, rof=1.5, tracking=80, size="S"),
                make_weapon("Autocannon", "Kinetic", 60, rof=1.5, tracking=80, size="S"),
                make_weapon("Autocannon", "Kinetic", 60, rof=1.5, tracking=80, size="S"),
                make_weapon("Rocket", "Explosive", 90, rof=0.6, tracking=70, size="S"),
            ]
            ship = make_ship(f"{prefix}_{i}", f"{faction} Brawler {i}", faction, "Frigate",
                           shield=400, armor=1200, hull=500, weapons=weapons, speed=150, signature=35)
        elif i % 5 == 2:  # 20% fast tacklers
            weapons = [
                make_weapon("Pulse Laser", "Thermal", 50, rof=1.2, tracking=90, size="S"),
                make_weapon("Pulse Laser", "Thermal", 50, rof=1.2, tracking=90, size="S"),
            ]
            ship = make_ship(f"{prefix}_{i}", f"{faction} Interceptor {i}", faction, "Fighter",
                           shield=300, armor=200, hull=300, weapons=weapons, speed=250, signature=25)
        elif i % 5 == 3:  # 20% missile boats
            weapons = [
                make_weapon("Torpedo", "Kinetic", 150, rof=0.33, tracking=100, size="L"),
                make_weapon("Torpedo", "Kinetic", 150, rof=0.33, tracking=100, size="L"),
                make_weapon("Flak", "Explosive", 40, rof=2.0, tracking=95, size="S"),
            ]
            ship = make_ship(f"{prefix}_{i}", f"{faction} Destroyer {i}", faction, "Destroyer",
                           shield=1000, armor=1200, hull=800, weapons=weapons, speed=100, signature=60)
        else:  # 20% railgun snipers
            weapons = [
                make_weapon("Railgun", "Kinetic", 120, rof=0.5, tracking=30, size="L"),
                make_weapon("Railgun", "Kinetic", 120, rof=0.5, tracking=30, size="L"),
            ]
            ship = make_ship(f"{prefix}_{i}", f"{faction} Sniper {i}", faction, "Frigate",
                           shield=600, armor=400, hull=400, weapons=weapons, speed=90, signature=45)
    
        fleet.append(ship)
    return fleet


def run_demo_battle():
    """Run a small battle with full event log."""
    print("=== DEMO BATTLE: 5v5 ===")
    print()

    fleet_a = create_test_fleet("Terran Federation", 5, "tf")
    fleet_b = create_test_fleet("Iron Compact", 5, "ic")

    engine = CombatEngine(fleet_a, fleet_b)
    result = engine.run(max_ticks=100)

    # Print event log (condensed)
    destroys = [e for e in engine.events if e.event == "destroyed"]
    hits = [e for e in engine.events if e.event == "hit"]
    misses = [e for e in engine.events if e.event == "miss"]
    
    print(f"Battle duration: {result['ticks']} ticks")
    print(f"Total events: {len(engine.events)} ({len(hits)} hits, {len(misses)} misses, {len(destroys)} kills)")
    print(f"Winner: {result['winner']}")
    print(f"  {result['fleet_a']['faction']}: {result['fleet_a']['survived']}/{result['fleet_a']['started']} survived")
    print(f"  {result['fleet_b']['faction']}: {result['fleet_b']['survived']}/{result['fleet_b']['started']} survived")
    print()

    # Show kill feed
    print("Kill feed:")
    for e in destroys:
        src_ship = next((s for s in fleet_a + fleet_b if s.id == e.source_id), None)
        tgt_ship = next((s for s in fleet_a + fleet_b if s.id == e.target_id), None)
        print(f"  T{e.tick:3d}: {src_ship.name if src_ship else '?'} destroyed {tgt_ship.name if tgt_ship else '?'}")
    print()

    # Show first 10 events as sample
    print("First 10 events:")
    for e in engine.events[:10]:
        if e.event == "hit":
            print(f"  T{e.tick}: {e.source_id} -> {e.target_id} [{e.weapon} {e.damage_type}] {e.damage:.0f} dmg | {e.remaining_hp}")
        elif e.event == "miss":
            print(f"  T{e.tick}: {e.source_id} -> {e.target_id} [{e.weapon}] MISS")
        else:
            print(f"  T{e.tick}: {e.event} {e.target_id}")
    print()


def run_benchmark():
    """Benchmark at various scales."""
    print("=== PERFORMANCE BENCHMARK ===")
    print()

    scenarios = [
        ("10v10", 10),
        ("50v50", 50),
        ("200v200", 200),
        ("500v500", 500),
        ("2000v2000", 2000),
    ]

    for name, size in scenarios:
        fleet_a = create_test_fleet("Alpha", size, "a")
        fleet_b = create_test_fleet("Beta", size, "b")
        
        engine = CombatEngine(fleet_a, fleet_b)
        start = time.perf_counter()
        # Run 5 ticks (not to completion - just measuring per-tick cost)
        for _ in range(5):
            engine.step()
        elapsed = (time.perf_counter() - start) / 5 * 1000
        
        print(f"  {name}: {elapsed:.2f}ms/tick | {size*2} ships | ~{size*2*3} shots/tick")

    print()
    
    # Full battle to completion
    print("=== FULL BATTLES TO COMPLETION ===")
    print()
    for name, size in [("20v20", 20), ("50v50", 50), ("100v100", 100)]:
        fleet_a = create_test_fleet("Alpha", size, "a")
        fleet_b = create_test_fleet("Beta", size, "b")
        engine = CombatEngine(fleet_a, fleet_b)
        start = time.perf_counter()
        result = engine.run(max_ticks=300)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  {name}: {elapsed:.1f}ms total | {result['ticks']} ticks | {len(engine.events)} events | winner: {result['winner']}")


if __name__ == "__main__":
    run_demo_battle()
    run_benchmark()
