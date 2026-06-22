# Ship Hull Classes

## Philosophy

There is no "military" vs "civilian" distinction on hulls. A hull defines physical characteristics (size, slot layout, bonuses). What you fit determines the role. An Industrial can mount weapons. A Frigate can fit mining lasers.

Faction military ships (in `military_ships` table) are faction-specific variants of standard hull classes with unique bonuses and pre-fitted loadouts.

## Hull Classes

| Class | Size | Typical Use | Examples |
|-------|------|-------------|----------|
| Frigate | Small | Fast attack, scouting, tackle | Viper Interceptor, Warden Frigate |
| Destroyer | Small | Anti-frigate, patrol, escort | Sentinel Corvette |
| Cruiser | Medium | Line combat, exploration | (faction ships) |
| Battlecruiser | Medium | Fleet command, heavy combat | (faction ships) |
| Battleship | Large | Sustained combat, fleet anchor | (faction ships) |
| Carrier | Capital | Fighter deployment, fleet support | (faction ships) |
| Dreadnought | Capital | Siege, station assault | (faction ships) |
| Industrial | Varies | Hauling, cargo transport | Pinto Runner through Clydesdale |
| Mining Barge | Varies | Ore extraction | Prospect Skiff through Deep Core Borer |

## Slot System

All ships use three slot types:

- **Weapon Mounts (W)** - Weapons, mining lasers, salvagers, tractor beams
- **Utility Bays (U)** - Shields, EWAR, propulsion, capacitor modules, scanners
- **Core Slots (C)** - Armor, engineering, damage mods, cargo expanders

## Design Principles

- Every ship has at least 2 Weapon Mounts (can always fight back and mine)
- Industrials favor Utility + Core (tank and cargo) over Weapon Mounts
- Mining Barges favor Weapon Mounts (for mining lasers) but have modest Utility/Core
- Combat hulls (Frigate through Dreadnought) favor Weapon Mounts
- The Clydesdale (T4 Industrial) is a fortress: 4W/6U/5C, slower but nearly as tough as a battlecruiser
- Fitting determines role, hull determines potential
