# Ship Fitting Specification

## Slot System

All ships have three module slot types plus hardpoint sub-limits:

| Slot | Color | Modules | Resource Bias |
|------|-------|---------|---------------|
| High | Red | Weapons, mining lasers, salvagers, tractor beams, remote repair, cloaks | PG-heavy |
| Mid | Yellow | Shield mods, propulsion (AB/MWD), EWAR, tackle, cap boosters, scanners | CPU-heavy |
| Low | Green | Armor plates/repairers, damage mods, engineering (CPU/PG upgrades), cargo expanders, navigation passives | Mixed |

### Hardpoints (sub-limit within High Slots)

- **Turret Hardpoints**: Max turrets (lasers, railguns, autocannons, blasters) that can be fitted
- **Launcher Hardpoints**: Max launchers (missile/rocket/torpedo) that can be fitted
- Remaining high slots can fit utility modules (mining lasers, salvagers, etc.)
- A ship with 6 High, 4 Turret, 3 Launcher can fit at most 4 turrets OR 3 launchers, or any mix not exceeding either limit (e.g., 3 turret + 3 launcher = all 6 highs used)

## Fitting Resources

| Resource | Description |
|----------|-------------|
| CPU (tf) | Processing capacity. Electronics, EWAR, and utility modules are CPU-intensive. |
| Power Grid (MW) | Energy output. Weapons, shields, and propulsion are PG-intensive. |
| Capacitor (GJ) | Energy pool drains on active module use, recharges over time. |

## Hull Class Base Stats

### Slot Layout by Class

| Class | High | Mid | Low | Turret HP | Launcher HP |
|-------|------|-----|-----|-----------|-------------|
| Fighter | 2 | 2 | 2 | 2 | 1 |
| Frigate | 3 | 3 | 2 | 2 | 2 |
| Destroyer | 5 | 3 | 3 | 4 | 3 |
| Cruiser | 5 | 4 | 4 | 4 | 3 |
| Battlecruiser | 6 | 5 | 5 | 5 | 4 |
| Battleship | 7 | 5 | 6 | 6 | 5 |
| Carrier | 4 | 6 | 5 | 2 | 2 |
| Dreadnought | 8 | 6 | 6 | 6 | 4 |
| Industrial | 2 | 3 | 4 | 1 | 1 |
| Mining Barge | 3 | 2 | 3 | 1 | 0 |

Note: Variants within a class may deviate by +/-1 slot to define sub-roles.

### Fitting Resources by Class

| Class | CPU (tf) | PG (MW) | Cap (GJ) | Cap Rech (GJ/s) |
|-------|----------|---------|-----------|-----------------|
| Fighter | 125 | 40 | 250 | 5.0 |
| Frigate | 200 | 60 | 400 | 7.5 |
| Destroyer | 275 | 100 | 550 | 10.0 |
| Cruiser | 350 | 150 | 800 | 15.0 |
| Battlecruiser | 450 | 250 | 1200 | 20.0 |
| Battleship | 550 | 400 | 1800 | 25.0 |
| Carrier | 600 | 350 | 2500 | 30.0 |
| Dreadnought | 700 | 600 | 3500 | 35.0 |
| Industrial | 250 | 80 | 500 | 8.0 |
| Mining Barge | 225 | 70 | 450 | 7.0 |

### Combat/Sensor Stats by Class

| Class | Signature (m) | Scan Res (mm) | Sensor Str | Target Range (km) | Max Targets |
|-------|---------------|---------------|------------|-------------------|-------------|
| Fighter | 25 | 900 | 8 | 30 | 2 |
| Frigate | 40 | 700 | 12 | 50 | 3 |
| Destroyer | 65 | 550 | 16 | 60 | 4 |
| Cruiser | 120 | 400 | 20 | 70 | 5 |
| Battlecruiser | 250 | 300 | 24 | 80 | 6 |
| Battleship | 400 | 200 | 28 | 90 | 7 |
| Carrier | 450 | 250 | 32 | 100 | 8 |
| Dreadnought | 550 | 150 | 36 | 100 | 8 |
| Industrial | 150 | 350 | 10 | 50 | 3 |
| Mining Barge | 100 | 400 | 10 | 40 | 2 |

## Stacking Penalties

When fitting multiple modules of the same effect type, diminishing returns apply:

```
effectiveness(n) = 0.5 ^ ((n-1) / 2.22)^2
```

| # Module | Effectiveness |
|----------|--------------|
| 1st | 100% |
| 2nd | 87% |
| 3rd | 57% |
| 4th | 28% |
| 5th | 10% |

Applies to: damage mods, hardeners, prop mods, sensor boosters, tracking enhancers.
Does NOT apply to: armor plates (flat HP), hull repairers (active), shield extenders (flat HP).

## Module Fitting Costs (CPU/PG by group)

### High Slot Modules

| Module Group | Size S CPU/PG | Size M CPU/PG | Size L CPU/PG | Size C CPU/PG |
|-------------|---------------|---------------|---------------|---------------|
| Autocannon | 8/5 | 18/12 | 30/25 | 50/45 |
| Railgun | 20/8 | 35/18 | 55/35 | 80/60 |
| Beam Laser | 12/12 | 25/25 | 40/45 | 65/75 |
| Pulse Laser | 10/8 | 20/18 | 35/32 | 55/55 |
| Missile Launcher | 25/5 | 40/12 | 60/22 | 90/40 |
| Mining Laser | 10/5 | 20/12 | 35/22 | - |
| Salvager | 15/3 | 25/5 | - | - |
| Tractor Beam | 15/5 | 25/10 | - | - |
| Cloaking Device | 50/1 | 75/1 | - | - |
| Remote Armor Repairer | 20/15 | 35/30 | 55/50 | - |
| Remote Shield Booster | 25/12 | 40/25 | 60/45 | - |
| Energy Neutralizer | 20/10 | 35/20 | 55/35 | - |
| Energy Nosferatu | 15/8 | 28/16 | 45/28 | - |

### Mid Slot Modules

| Module Group | Size S CPU/PG | Size M CPU/PG | Size L CPU/PG |
|-------------|---------------|---------------|---------------|
| Shield Booster | 20/15 | 35/30 | 55/55 |
| Shield Extender | 25/20 | 40/35 | 60/55 |
| Shield Hardener | 20/1 | 30/1 | 45/1 |
| Shield Recharger | 15/1 | 25/1 | 40/1 |
| Afterburner | 10/15 | 18/30 | 28/55 |
| Microwarpdrive | 15/25 | 25/50 | 40/90 |
| ECM | 30/1 | 50/1 | 75/1 |
| Sensor Dampener | 25/1 | 40/1 | 60/1 |
| Target Painter | 20/1 | 35/1 | 50/1 |
| Tracking Disruptor | 25/1 | 40/1 | 60/1 |
| Stasis Webifier | 20/1 | 35/1 | 55/1 |
| Warp Disruptor | 20/1 | 30/1 | 45/1 |
| Warp Scrambler | 25/1 | 40/1 | 60/1 |
| Capacitor Booster | 10/5 | 18/10 | 28/18 |
| Scanner | 20/3 | 35/5 | - |

### Low Slot Modules

| Module Group | Size S CPU/PG | Size M CPU/PG | Size L CPU/PG |
|-------------|---------------|---------------|---------------|
| Armor Plate | 5/15 | 8/30 | 12/55 |
| Armor Repairer | 10/12 | 18/25 | 28/45 |
| Armor Hardener | 15/1 | 25/1 | 40/1 |
| Damage Control | 10/5 | 15/8 | 22/12 |
| Cargo Expander | 15/1 | 25/1 | 40/1 |
| Co-Processor | 1/5 | 1/10 | 1/18 |
| Reactor Control | 5/1 | 8/1 | 12/1 |
| Power Diagnostics | 8/1 | 12/1 | 18/1 |
| Inertial Stabilizer | 12/1 | 20/1 | 30/1 |
| Nanofiber Structure | 10/1 | 18/1 | 28/1 |
| Overdrive Injector | 8/5 | 15/10 | 22/18 |
| Warp Stabilizer | 15/1 | 25/1 | 40/1 |
| Drone Control Unit | 25/5 | 40/10 | 60/18 |
| Mining Upgrade | 15/3 | 25/5 | 40/8 |

## Quality Tier Modifiers

Fitting costs scale with quality:

| Quality | CPU/PG Modifier | Stat Modifier |
|---------|-----------------|---------------|
| Standard | 1.00x | 1.00x |
| Named (Compact) | 0.85x | 1.15x |
| T2 | 1.20x | 1.35x |
| Faction | 0.90x | 1.25x |

Named = lower fitting cost, moderate stats. T2 = highest stats but costs more to fit. Faction = best balance (low cost, high stats, expensive to buy).

## Damage Model

4 damage types: EM, Thermal, Kinetic, Explosive

### Base Resistances (before modules)

| Layer | EM | Thermal | Kinetic | Explosive |
|-------|-----|---------|---------|-----------|
| Shield | 0% | 20% | 40% | 50% |
| Armor | 60% | 35% | 25% | 0% |
| Hull | 0% | 0% | 0% | 0% |

### Damage Order
Shield (first) -> Armor -> Hull (destruction at 0)

## Design Philosophy

- CPU constrains electronics/utility (EWAR, scanners, tackle). A ship wanting to run heavy EWAR needs CPU upgrades (sacrificing lows).
- PG constrains weapons/tank. Big guns and big shields compete for powergrid.
- Hardpoints define maximum offensive capability. Can't brute-force more weapons with CPU/PG alone.
- Stacking penalties prevent one-dimensional min/max builds from being optimal.
- Every ship class has at least 2 highs (always able to fight back or mine).
- Industrial/Mining hulls trade combat capability for cargo/yield utility.
