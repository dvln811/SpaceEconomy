"""Benchmark: estimate per-shot combat simulation cost at scale."""
import time, random

class Ship:
    __slots__ = ['hp_shield','hp_armor','hp_hull','weapons','alive','resist_s','resist_a']
    def __init__(self, weapons=4):
        self.hp_shield = 1000.0
        self.hp_armor = 800.0
        self.hp_hull = 500.0
        self.weapons = weapons
        self.alive = True
        self.resist_s = 0.3
        self.resist_a = 0.5

def simulate_tick(fleet_a, fleet_b):
    """One combat tick: all alive ships fire all weapons at a random enemy."""
    events = 0
    for fleet, enemy in [(fleet_a, fleet_b), (fleet_b, fleet_a)]:
        alive_enemies = [s for s in enemy if s.alive]
        if not alive_enemies:
            break
        for ship in fleet:
            if not ship.alive:
                continue
            target = random.choice(alive_enemies)
            for w in range(ship.weapons):
                if random.random() > 0.85:
                    events += 1
                    continue
                raw_dmg = random.uniform(80, 120)
                if target.hp_shield > 0:
                    actual = raw_dmg * (1 - target.resist_s)
                    target.hp_shield -= actual
                    if target.hp_shield < 0:
                        target.hp_armor += target.hp_shield * (1 - target.resist_a)
                        target.hp_shield = 0
                elif target.hp_armor > 0:
                    actual = raw_dmg * (1 - target.resist_a)
                    target.hp_armor -= actual
                    if target.hp_armor < 0:
                        target.hp_hull += target.hp_armor
                        target.hp_armor = 0
                else:
                    target.hp_hull -= raw_dmg
                if target.hp_hull <= 0:
                    target.alive = False
                    alive_enemies = [s for s in enemy if s.alive]
                    if not alive_enemies:
                        break
                events += 1
    return events

print("=== COMBAT SIMULATION PERFORMANCE BENCHMARK ===")
print()
print("Per-shot model: each ship fires N weapons per tick, full damage calc")
print("Game budget: battle_sim runs every 20 ticks at 23t/s = 870ms window")
print()

scenarios = [
    ("Current game (20v20, 4 wpn)", 20, 20, 4),
    ("Large battle (50v50, 4 wpn)", 50, 50, 4),
    ("Grand battle (200v200, 4 wpn)", 200, 200, 4),
    ("100x scale (2000v2000, 4 wpn)", 2000, 2000, 4),
    ("500x scale (10000v10000, 4 wpn)", 10000, 10000, 4),
]

for name, size_a, size_b, wpns in scenarios:
    iters = 3 if size_a >= 2000 else 10
    times = []
    for _ in range(iters):
        fleet_a = [Ship(wpns) for _ in range(size_a)]
        fleet_b = [Ship(wpns) for _ in range(size_b)]
        start = time.perf_counter()
        simulate_tick(fleet_a, fleet_b)
        times.append(time.perf_counter() - start)
    avg_ms = sum(times) / len(times) * 1000
    shots = (size_a + size_b) * wpns
    budget_pct = avg_ms / 870 * 100
    print(f"  {name}:")
    print(f"    Ships: {size_a+size_b} | Shots/tick: {shots} | Time: {avg_ms:.2f}ms | Budget: {budget_pct:.1f}%")
    print()

print("=== MULTIPLE SIMULTANEOUS BATTLES (realistic scenario) ===")
print()

# 15 mixed battles
start = time.perf_counter()
for _ in range(5):
    simulate_tick([Ship(4) for _ in range(10)], [Ship(4) for _ in range(10)])
for _ in range(5):
    simulate_tick([Ship(4) for _ in range(30)], [Ship(4) for _ in range(30)])
for _ in range(3):
    simulate_tick([Ship(4) for _ in range(50)], [Ship(4) for _ in range(50)])
for _ in range(2):
    simulate_tick([Ship(4) for _ in range(100)], [Ship(4) for _ in range(100)])
elapsed_ms = (time.perf_counter() - start) * 1000
print(f"  15 mixed battles (5x10v10 + 5x30v30 + 3x50v50 + 2x100v100):")
print(f"    Total: {elapsed_ms:.2f}ms | Budget: {elapsed_ms/870*100:.1f}%")
print()

# Absolute worst case: one massive 500v500
start = time.perf_counter()
simulate_tick([Ship(4) for _ in range(500)], [Ship(4) for _ in range(500)])
elapsed_ms = (time.perf_counter() - start) * 1000
print(f"  Worst case (single 500v500):")
print(f"    Total: {elapsed_ms:.2f}ms | Budget: {elapsed_ms/870*100:.1f}%")
