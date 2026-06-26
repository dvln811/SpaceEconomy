"""
Combat simulation engine with full fitting model.
- CPU/Powergrid fitting constraints
- Capacitor (drains per shot, recharges per tick, empty = weapons offline)
- Module HP (bleedthrough damage, disabled at 0)
- Ammo consumption (projectiles/missiles burn ammo from cargo)
- 4 damage types with shield/armor/hull resistance profiles
"""
from dataclasses import dataclass, field
from enum import Enum
import random
import math


class DmgType(Enum):
    EM = "EM"
    THERMAL = "Thermal"
    KINETIC = "Kinetic"
    EXPLOSIVE = "Explosive"


BASE_RESIST = {
    "shield": {DmgType.EM: 0.0, DmgType.THERMAL: 0.20, DmgType.KINETIC: 0.40, DmgType.EXPLOSIVE: 0.50},
    "armor":  {DmgType.EM: 0.60, DmgType.THERMAL: 0.35, DmgType.KINETIC: 0.25, DmgType.EXPLOSIVE: 0.0},
    "hull":   {DmgType.EM: 0.0, DmgType.THERMAL: 0.0, DmgType.KINETIC: 0.0, DmgType.EXPLOSIVE: 0.0},
}

# Chance a module takes damage when armor or hull is hit
MODULE_DAMAGE_CHANCE_ARMOR = 0.05  # 5% per hit that penetrates to armor
MODULE_DAMAGE_CHANCE_HULL = 0.15   # 15% per hit that penetrates to hull
MODULE_DAMAGE_AMOUNT = 15.0        # flat HP lost per bleedthrough hit


@dataclass
class Weapon:
    name: str
    damage_type: DmgType
    base_damage: float         # damage per shot
    cycle_time: float          # ticks between shots
    tracking: float            # tracking speed (0-100)
    optimal_range: float       # meters
    size: str = "S"            # S, M, L, C
    # Fitting
    cpu_cost: float = 0.0
    pg_cost: float = 0.0
    cap_use: float = 0.0       # capacitor per shot (lasers high, projectiles 0)
    # Ammo
    ammo_id: str = ""          # commodity ID of ammo consumed (empty = no ammo needed)
    ammo_per_shot: int = 1     # units consumed per firing
    # State
    cooldown: float = 0.0
    hp: float = 40.0           # module durability
    hp_max: float = 40.0
    disabled: bool = False


@dataclass
class Module:
    """Non-weapon fitted module (shield booster, armor repairer, prop mod, etc.)"""
    name: str
    slot: str                  # "utility" or "core"
    # Fitting
    cpu_cost: float = 0.0
    pg_cost: float = 0.0
    cap_use: float = 0.0       # cap per activation cycle
    cycle_time: float = 10.0   # ticks between activations
    # Effects
    shield_boost: float = 0.0
    armor_repair: float = 0.0
    speed_bonus: float = 0.0
    # State
    hp: float = 30.0
    hp_max: float = 30.0
    disabled: bool = False
    cooldown: float = 0.0
    active: bool = True        # whether pilot has it turned on


@dataclass
class CombatShip:
    id: str
    name: str
    faction: str
    hull_class: str
    # HP layers
    shield_hp: float
    shield_max: float
    armor_hp: float
    armor_max: float
    hull_hp: float
    hull_max: float
    # Fitting resources
    cpu: float = 100.0
    cpu_max: float = 100.0
    powergrid: float = 80.0
    pg_max: float = 80.0
    # Capacitor
    cap: float = 500.0
    cap_max: float = 500.0
    cap_recharge: float = 5.0  # per tick
    # Resistances (can be modified by hardeners)
    resist_shield: dict = field(default_factory=dict)
    resist_armor: dict = field(default_factory=dict)
    # Fittings
    weapons: list = field(default_factory=list)
    modules: list = field(default_factory=list)
    # Cargo (ammo)
    ammo: dict = field(default_factory=dict)  # {ammo_id: quantity}
    # Combat stats
    speed: float = 100.0       # max speed m/s
    signature: float = 50.0
    # 3D Spatial
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    accel: float = 20.0        # m/s^2 acceleration
    orbit_range: float = 0.0   # desired orbit distance (set by role AI)
    role_ai: str = "brawl"     # brawl, orbit, kite, snipe
    # State
    alive: bool = True
    target_id: str = ""


@dataclass
class Missile:
    """In-flight missile entity."""
    id: str
    source_id: str
    target_id: str
    weapon_name: str
    damage_type: DmgType
    damage: float
    speed: float = 300.0       # m/s
    flight_time: float = 30.0  # ticks before expiry
    tracking: float = 80.0     # ability to follow target
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class BattleEvent:
    tick: int
    event: str  # fire, hit, miss, destroyed, module_damaged, module_disabled, cap_empty, cap_restored
    source_id: str = ""
    target_id: str = ""
    weapon: str = ""
    damage: float = 0.0
    damage_type: str = ""
    remaining_hp: str = ""
    detail: str = ""


class CombatEngine:
    def __init__(self, fleet_a: list[CombatShip], fleet_b: list[CombatShip]):
        self.fleet_a = fleet_a
        self.fleet_b = fleet_b
        self.tick = 0
        self.events: list[BattleEvent] = []
        self.missiles: list[Missile] = []
        self._missile_id = 0
        self.finished = False
        self._assign_roles_and_positions()

    def _assign_roles_and_positions(self):
        """Spawn fleets facing each other, assign orbit ranges by role."""
        role_map = {"Fighter": "orbit", "Frigate": "brawl", "Destroyer": "snipe", "Cruiser": "kite"}
        orbit_ranges = {"orbit": 2000, "brawl": 500, "kite": 8000, "snipe": 12000}
        for i, s in enumerate(self.fleet_a):
            s.x = -15000.0 + random.uniform(-500, 500)
            s.y = (i - len(self.fleet_a)/2) * 600 + random.uniform(-200, 200)
            s.z = random.uniform(-300, 300)
            s.role_ai = role_map.get(s.hull_class, "brawl")
            s.orbit_range = orbit_ranges.get(s.role_ai, 3000)
        for i, s in enumerate(self.fleet_b):
            s.x = 15000.0 + random.uniform(-500, 500)
            s.y = (i - len(self.fleet_b)/2) * 600 + random.uniform(-200, 200)
            s.z = random.uniform(-300, 300)
            s.role_ai = role_map.get(s.hull_class, "brawl")
            s.orbit_range = orbit_ranges.get(s.role_ai, 3000)

    def get_alive(self, fleet):
        return [s for s in fleet if s.alive]

    def _dist(self, a, b):
        return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2)

    def _move_ships(self):
        """Move all alive ships according to their role AI."""
        all_ships = self.get_alive(self.fleet_a) + self.get_alive(self.fleet_b)
        ship_map = {s.id: s for s in all_ships}

        for ship in all_ships:
            target = ship_map.get(ship.target_id)
            if not target or not target.alive:
                continue

            dx = target.x - ship.x
            dy = target.y - ship.y
            dz = target.z - ship.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0

            if ship.role_ai == "brawl":
                # Close to 500m, then orbit
                if dist > ship.orbit_range + 200:
                    # Approach
                    ship.vx += (dx/dist) * ship.accel
                    ship.vy += (dy/dist) * ship.accel
                    ship.vz += (dz/dist) * ship.accel * 0.3
                else:
                    # Orbit perpendicular
                    ship.vx += (-dy/dist) * ship.accel * 0.8
                    ship.vy += (dx/dist) * ship.accel * 0.8
                    ship.vz += random.uniform(-1, 1) * ship.accel * 0.2

            elif ship.role_ai == "orbit":
                # Maintain orbit_range, fast perpendicular movement
                if dist > ship.orbit_range + 500:
                    ship.vx += (dx/dist) * ship.accel
                    ship.vy += (dy/dist) * ship.accel
                elif dist < ship.orbit_range - 500:
                    ship.vx -= (dx/dist) * ship.accel * 0.5
                    ship.vy -= (dy/dist) * ship.accel * 0.5
                # Always orbit
                ship.vx += (-dy/dist) * ship.accel * 1.2
                ship.vy += (dx/dist) * ship.accel * 1.2
                ship.vz += random.uniform(-2, 2)

            elif ship.role_ai == "kite":
                # Keep at orbit_range, back off if too close
                if dist < ship.orbit_range - 1000:
                    ship.vx -= (dx/dist) * ship.accel * 1.5
                    ship.vy -= (dy/dist) * ship.accel * 1.5
                elif dist > ship.orbit_range + 1000:
                    ship.vx += (dx/dist) * ship.accel * 0.5
                    ship.vy += (dy/dist) * ship.accel * 0.5
                ship.vx += (-dy/dist) * ship.accel * 0.5
                ship.vy += (dx/dist) * ship.accel * 0.5

            elif ship.role_ai == "snipe":
                # Stay far, minimal movement
                if dist < ship.orbit_range - 2000:
                    ship.vx -= (dx/dist) * ship.accel
                    ship.vy -= (dy/dist) * ship.accel
                elif dist > ship.orbit_range + 2000:
                    ship.vx += (dx/dist) * ship.accel * 0.3
                    ship.vy += (dy/dist) * ship.accel * 0.3

            # Clamp speed
            spd = math.sqrt(ship.vx**2 + ship.vy**2 + ship.vz**2)
            if spd > ship.speed:
                scale = ship.speed / spd
                ship.vx *= scale
                ship.vy *= scale
                ship.vz *= scale

            # Apply velocity
            ship.x += ship.vx
            ship.y += ship.vy
            ship.z += ship.vz

            # Drag (space friction for game feel)
            ship.vx *= 0.92
            ship.vy *= 0.92
            ship.vz *= 0.92

    def _move_missiles(self):
        """Update in-flight missiles, check for impacts."""
        tick_events = []
        surviving = []
        all_ships = {s.id: s for s in self.fleet_a + self.fleet_b if s.alive}

        for m in self.missiles:
            m.flight_time -= 1
            if m.flight_time <= 0:
                surviving.append(None)  # expired
                continue
            target = all_ships.get(m.target_id)
            if not target:
                continue  # target dead, missile lost

            # Save old position
            old_x, old_y, old_z = m.x, m.y, m.z

            # Lead prediction: aim where target will be
            dx = target.x - m.x
            dy = target.y - m.y
            dz = target.z - m.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
            # Estimate time to reach target, lead by target velocity
            eta = dist / max(m.speed, 1)
            lead_x = target.x + target.vx * eta * 0.5
            lead_y = target.y + target.vy * eta * 0.5
            lead_z = target.z + target.vz * eta * 0.5
            dx = lead_x - m.x
            dy = lead_y - m.y
            dz = lead_z - m.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0

            m.x += (dx/dist) * m.speed
            m.y += (dy/dist) * m.speed
            m.z += (dz/dist) * m.speed

            # Impact: trace from old to new, check if passes within target signature
            seg_dx, seg_dy, seg_dz = m.x - old_x, m.y - old_y, m.z - old_z
            to_tgt_x, to_tgt_y, to_tgt_z = target.x - old_x, target.y - old_y, target.z - old_z
            seg_len_sq = seg_dx**2 + seg_dy**2 + seg_dz**2
            t_closest = max(0, min(1, (to_tgt_x*seg_dx + to_tgt_y*seg_dy + to_tgt_z*seg_dz) / max(seg_len_sq, 1)))
            closest_x = old_x + seg_dx * t_closest
            closest_y = old_y + seg_dy * t_closest
            closest_z = old_z + seg_dz * t_closest
            closest_dist = math.sqrt((target.x-closest_x)**2 + (target.y-closest_y)**2 + (target.z-closest_z)**2)
            if closest_dist < target.signature:
                # Hit - apply damage directly (missiles always hit if they reach)
                actual, hit_layer = self._apply_damage(target, m.damage * random.uniform(0.9, 1.1), m.damage_type)
                hp_str = "S:%.0f/%.0f A:%.0f/%.0f H:%.0f/%.0f" % (
                    target.shield_hp, target.shield_max,
                    target.armor_hp, target.armor_max,
                    target.hull_hp, target.hull_max)
                tick_events.append(BattleEvent(
                    tick=self.tick, event="hit", source_id=m.source_id,
                    target_id=m.target_id, weapon=m.weapon_name,
                    damage=round(actual, 1), damage_type=m.damage_type.value,
                    remaining_hp=hp_str))
                if hit_layer in ("armor", "hull"):
                    tick_events.extend(self._module_bleedthrough(target, hit_layer))
                if target.hull_hp <= 0:
                    target.alive = False
                    tick_events.append(BattleEvent(
                        tick=self.tick, event="destroyed",
                        source_id=m.source_id, target_id=m.target_id))
                continue  # missile consumed

            surviving.append(m)

        self.missiles = [m for m in surviving if m is not None]
        return tick_events

    def step(self) -> list[BattleEvent]:
        if self.finished:
            return []
        self.tick += 1
        tick_events = []

        alive_a = self.get_alive(self.fleet_a)
        alive_b = self.get_alive(self.fleet_b)
        if not alive_a or not alive_b:
            self.finished = True
            return []

        # Movement
        self._move_ships()

        # Missile updates
        tick_events.extend(self._move_missiles())

        # Capacitor recharge
        for ship in alive_a + alive_b:
            was_empty = ship.cap <= 0
            ship.cap = min(ship.cap_max, ship.cap + ship.cap_recharge)
            if was_empty and ship.cap > 0:
                tick_events.append(BattleEvent(tick=self.tick, event="cap_restored", target_id=ship.id))

        # Active modules
        for ship in alive_a + alive_b:
            for mod in ship.modules:
                if mod.disabled or not mod.active:
                    continue
                mod.cooldown -= 1
                if mod.cooldown > 0:
                    continue
                if ship.cap < mod.cap_use:
                    continue
                mod.cooldown = mod.cycle_time
                ship.cap -= mod.cap_use
                if mod.shield_boost > 0:
                    ship.shield_hp = min(ship.shield_max, ship.shield_hp + mod.shield_boost)
                if mod.armor_repair > 0:
                    ship.armor_hp = min(ship.armor_max, ship.armor_hp + mod.armor_repair)

        # Recheck alive after missiles
        alive_a = self.get_alive(self.fleet_a)
        alive_b = self.get_alive(self.fleet_b)
        if not alive_a or not alive_b:
            self.finished = True
            self.events.extend(tick_events)
            return tick_events

        # Weapons fire
        for fleet, enemies in [(alive_a, alive_b), (alive_b, alive_a)]:
            if not enemies:
                break
            for ship in fleet:
                target = self._pick_target(ship, enemies)
                if not target:
                    continue
                dist = self._dist(ship, target)

                for wpn in ship.weapons:
                    if wpn.disabled:
                        continue
                    wpn.cooldown -= 1
                    if wpn.cooldown > 0:
                        continue
                    if wpn.cap_use > 0 and ship.cap < wpn.cap_use:
                        if ship.cap <= 0:
                            tick_events.append(BattleEvent(tick=self.tick, event="cap_empty", target_id=ship.id))
                        continue
                    if wpn.ammo_id and ship.ammo.get(wpn.ammo_id, 0) < wpn.ammo_per_shot:
                        continue

                    # Range check - can't fire beyond 2x optimal
                    if dist > wpn.optimal_range * 2.0:
                        continue

                    wpn.cooldown = wpn.cycle_time
                    ship.cap -= wpn.cap_use
                    if wpn.ammo_id:
                        ship.ammo[wpn.ammo_id] -= wpn.ammo_per_shot

                    # Missiles/rockets/torpedoes: launch as spatial entity
                    if "Missile" in wpn.name or "Rocket" in wpn.name or "Torpedo" in wpn.name:
                        self._missile_id += 1
                        flight = 20 + wpn.optimal_range / 200
                        # Use ammo name for display, fall back to weapon type
                        projectile_name = wpn.ammo_id if wpn.ammo_id else wpn.name.replace(" Launcher", "")
                        self.missiles.append(Missile(
                            id=f"msl_{self._missile_id}", source_id=ship.id,
                            target_id=target.id, weapon_name=projectile_name,
                            damage_type=wpn.damage_type, damage=wpn.base_damage,
                            speed=500 + wpn.optimal_range * 0.02,
                            flight_time=flight, tracking=wpn.tracking,
                            x=ship.x, y=ship.y, z=ship.z))
                        continue

                    # Turret weapons: instant hit with angular velocity tracking
                    hit_chance = self._calc_hit_chance(wpn, ship, target, dist)
                    if random.random() > hit_chance:
                        tick_events.append(BattleEvent(
                            tick=self.tick, event="miss", source_id=ship.id,
                            target_id=target.id, weapon=wpn.name, damage_type=wpn.damage_type.value))
                        continue

                    # Range falloff
                    falloff = 1.0 if dist <= wpn.optimal_range else max(0.2, 1.0 - (dist - wpn.optimal_range) / wpn.optimal_range)
                    raw = wpn.base_damage * random.uniform(0.9, 1.1) * falloff
                    actual, hit_layer = self._apply_damage(target, raw, wpn.damage_type)

                    hp_str = "S:%.0f/%.0f A:%.0f/%.0f H:%.0f/%.0f" % (
                        target.shield_hp, target.shield_max,
                        target.armor_hp, target.armor_max,
                        target.hull_hp, target.hull_max)
                    tick_events.append(BattleEvent(
                        tick=self.tick, event="hit", source_id=ship.id,
                        target_id=target.id, weapon=wpn.name,
                        damage=round(actual, 1), damage_type=wpn.damage_type.value,
                        remaining_hp=hp_str))

                    if hit_layer in ("armor", "hull"):
                        tick_events.extend(self._module_bleedthrough(target, hit_layer))
                    if target.hull_hp <= 0:
                        target.alive = False
                        tick_events.append(BattleEvent(
                            tick=self.tick, event="destroyed",
                            source_id=ship.id, target_id=target.id))
                        enemies = [e for e in enemies if e.alive]
                        ship.target_id = ""
                        if not enemies:
                            break

        self.events.extend(tick_events)
        if not self.get_alive(self.fleet_a) or not self.get_alive(self.fleet_b):
            self.finished = True
        return tick_events

    def run(self, max_ticks=600) -> dict:
        while not self.finished and self.tick < max_ticks:
            self.step()
        return self.summary()

    def summary(self) -> dict:
        a_alive = self.get_alive(self.fleet_a)
        b_alive = self.get_alive(self.fleet_b)
        winner = "draw"
        if a_alive and not b_alive:
            winner = self.fleet_a[0].faction
        elif b_alive and not a_alive:
            winner = self.fleet_b[0].faction
        return {
            "ticks": self.tick, "winner": winner,
            "fleet_a": {"faction": self.fleet_a[0].faction if self.fleet_a else "?",
                        "started": len(self.fleet_a), "survived": len(a_alive)},
            "fleet_b": {"faction": self.fleet_b[0].faction if self.fleet_b else "?",
                        "started": len(self.fleet_b), "survived": len(b_alive)},
            "total_events": len(self.events),
        }

    def _pick_target(self, ship, enemies):
        if ship.target_id:
            for e in enemies:
                if e.id == ship.target_id and e.alive:
                    return e
        best_score = -1
        target = None
        candidates = enemies if len(enemies) <= 5 else random.sample(enemies, 5)
        for e in candidates:
            dist = self._dist(ship, e)
            # Prefer targets in range and hittable
            in_range = any(dist < w.optimal_range * 2 for w in ship.weapons if not w.disabled)
            avg_hit = sum(self._calc_hit_chance(w, ship, e, dist) for w in ship.weapons if not w.disabled) / max(1, sum(1 for w in ship.weapons if not w.disabled))
            hp_pct = (e.shield_hp + e.armor_hp + e.hull_hp) / (e.shield_max + e.armor_max + e.hull_max)
            score = avg_hit * (2.0 - hp_pct) * (1.5 if in_range else 0.5) + random.uniform(0, 0.2)
            if score > best_score:
                best_score = score
                target = e
        if target:
            ship.target_id = target.id
        return target

    def _calc_hit_chance(self, wpn: Weapon, attacker: CombatShip, target: CombatShip, dist: float = None) -> float:
        """True angular velocity tracking: transversal_speed / distance vs tracking."""
        if dist is None:
            dist = self._dist(attacker, target)
        dist = max(dist, 100)  # prevent div by zero

        # Transversal velocity (perpendicular component of relative velocity)
        rel_vx = target.vx - attacker.vx
        rel_vy = target.vy - attacker.vy
        rel_vz = target.vz - attacker.vz
        # Direction to target
        dx = target.x - attacker.x
        dy = target.y - attacker.y
        dz = target.z - attacker.z
        d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
        # Radial component
        radial = (rel_vx * dx + rel_vy * dy + rel_vz * dz) / d
        # Transversal = total relative speed minus radial
        rel_speed_sq = rel_vx**2 + rel_vy**2 + rel_vz**2
        transversal = math.sqrt(max(0, rel_speed_sq - radial**2))

        # Angular velocity = transversal / distance
        angular_vel = transversal / dist

        # Weapon resolution (size penalty)
        weapon_res = {"S": 25, "M": 80, "L": 200, "C": 400}.get(wpn.size, 80)
        sig_factor = min(1.0, (target.signature / weapon_res) ** 1.5)

        # Tracking factor: weapon tracking vs angular velocity
        track_factor = wpn.tracking / (angular_vel * 500 + 10)

        combined = sig_factor * min(1.0, track_factor)
        hit = 0.1 + 0.85 * (combined ** 0.5)
        return max(0.05, min(0.95, hit))

    def _apply_damage(self, target: CombatShip, raw: float, dmg_type: DmgType) -> tuple[float, str]:
        """Returns (actual_damage, layer_hit). layer_hit = where final damage landed."""
        remaining = raw
        hit_layer = "shield"

        if target.shield_hp > 0:
            resist = target.resist_shield.get(dmg_type, BASE_RESIST["shield"][dmg_type])
            effective = remaining * (1.0 - resist)
            absorbed = min(target.shield_hp, effective)
            target.shield_hp -= absorbed
            remaining -= absorbed / (1.0 - resist) if resist < 1.0 else 0
            if target.shield_hp > 0:
                return absorbed, "shield"

        hit_layer = "armor"
        if target.armor_hp > 0:
            resist = target.resist_armor.get(dmg_type, BASE_RESIST["armor"][dmg_type])
            effective = remaining * (1.0 - resist)
            absorbed = min(target.armor_hp, effective)
            target.armor_hp -= absorbed
            remaining -= absorbed / (1.0 - resist) if resist < 1.0 else 0
            if target.armor_hp > 0:
                return raw - remaining, "armor"

        hit_layer = "hull"
        hull_resist = BASE_RESIST["hull"][dmg_type]
        effective = remaining * (1.0 - hull_resist)
        target.hull_hp -= effective
        return raw, "hull"

    def _module_bleedthrough(self, target: CombatShip, layer: str) -> list[BattleEvent]:
        """Chance to damage a random fitted module when armor/hull takes a hit."""
        events = []
        chance = MODULE_DAMAGE_CHANCE_ARMOR if layer == "armor" else MODULE_DAMAGE_CHANCE_HULL
        if random.random() > chance:
            return events

        # Pick a random non-destroyed module (weapon or utility)
        all_mods = [(i, "wpn", w) for i, w in enumerate(target.weapons) if not w.disabled]
        all_mods += [(i, "mod", m) for i, m in enumerate(target.modules) if not m.disabled]
        if not all_mods:
            return events

        idx, mod_type, mod = random.choice(all_mods)
        mod.hp -= MODULE_DAMAGE_AMOUNT
        if mod.hp <= 0:
            mod.hp = 0
            mod.disabled = True
            events.append(BattleEvent(
                tick=self.tick, event="module_disabled", target_id=target.id,
                detail=mod.name))
        else:
            events.append(BattleEvent(
                tick=self.tick, event="module_damaged", target_id=target.id,
                detail=f"{mod.name} ({mod.hp:.0f}/{mod.hp_max:.0f})"))
        return events


# --- Factory helpers ---

def make_weapon(name: str, damage_type: str, base_damage: float, cycle_time: float = 3.0,
                tracking: float = 60, optimal: float = 10000, size: str = "S",
                cap_use: float = 0.0, ammo_id: str = "", ammo_per_shot: int = 1,
                cpu: float = 0, pg: float = 0, hp: float = 40) -> Weapon:
    dt = DmgType(damage_type) if isinstance(damage_type, str) else damage_type
    return Weapon(name=name, damage_type=dt, base_damage=base_damage,
                  cycle_time=cycle_time, tracking=tracking, optimal_range=optimal, size=size,
                  cap_use=cap_use, ammo_id=ammo_id, ammo_per_shot=ammo_per_shot,
                  cpu_cost=cpu, pg_cost=pg, hp=hp, hp_max=hp)


def make_module(name: str, slot: str = "utility", cap_use: float = 0, cycle_time: float = 10,
                shield_boost: float = 0, armor_repair: float = 0, speed_bonus: float = 0,
                cpu: float = 0, pg: float = 0, hp: float = 30) -> Module:
    return Module(name=name, slot=slot, cap_use=cap_use, cycle_time=cycle_time,
                  shield_boost=shield_boost, armor_repair=armor_repair, speed_bonus=speed_bonus,
                  cpu_cost=cpu, pg_cost=pg, hp=hp, hp_max=hp)


def make_ship(id: str, name: str, faction: str, hull_class: str,
              shield: float, armor: float, hull: float,
              weapons: list[Weapon], speed: float = 100, signature: float = 50,
              cap: float = 500, cap_recharge: float = 5.0,
              modules: list[Module] = None, ammo: dict = None,
              accel: float = 0) -> CombatShip:
    if accel <= 0:
        accel = speed * 0.25  # default: reaches top speed in ~4 ticks
    return CombatShip(
        id=id, name=name, faction=faction, hull_class=hull_class,
        shield_hp=shield, shield_max=shield,
        armor_hp=armor, armor_max=armor,
        hull_hp=hull, hull_max=hull,
        cap=cap, cap_max=cap, cap_recharge=cap_recharge,
        weapons=weapons, modules=modules or [], ammo=ammo or {},
        speed=speed, signature=signature, accel=accel)
