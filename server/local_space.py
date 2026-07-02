"""Local Space Worker: persistent real-time 3D simulation of the player's current system.

This worker maintains actual 3D positions (x, y, z) for:
- Player ship (position, velocity, heading, speed)
- All NPC ships in the same system (arrivals, departures, docking, mining, warping)
- System objects (stations, gates, planets) as fixed reference points

Runs every tick (1/sec). The player's ship page READS from this state.
Player commands (fly, stop, warp) WRITE to this state.
When player is on another page, this keeps running.
"""
import math
import random
import threading
import time


class LocalShip:
    """A ship in local space with full 3D state."""
    __slots__ = ('id', 'name', 'ship_class', 'role', 'faction',
                 'x', 'y', 'z', 'vx', 'vy', 'vz',
                 'speed', 'max_speed', 'align_time', 'heading_x', 'heading_y', 'heading_z',
                 '_target_hx', '_target_hy', '_target_hz', '_flight_timer',
                 'state', 'target_obj', 'dock_station', 'is_player')

    def __init__(self, id, name='', ship_class='', role='', faction='',
                 x=0, y=0, z=0, speed=0, max_speed=100, align_time=5, state='idle', is_player=False):
        self.id = id
        self.name = name
        self.ship_class = ship_class
        self.role = role
        self.faction = faction
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.speed = speed
        self.max_speed = max_speed
        self.align_time = align_time
        self.heading_x = 1
        self.heading_y = 0
        self.heading_z = 0
        self._target_hx = 1
        self._target_hy = 0
        self._target_hz = 0
        self._flight_timer = 0
        self.state = state  # idle, flying, warping, docking, docked, mining, arriving, departing
        self.target_obj = None  # target object id for warp
        self.dock_station = ''
        self.is_player = is_player

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'ship_class': self.ship_class,
            'role': self.role, 'faction': self.faction,
            'x': round(self.x, 1), 'y': round(self.y, 1), 'z': round(self.z, 1),
            'vx': round(self.vx, 2), 'vy': round(self.vy, 2), 'vz': round(self.vz, 2),
            'speed': round(self.speed, 1), 'max_speed': self.max_speed,
            'align_time': self.align_time,
            'heading': [round(self.heading_x, 3), round(self.heading_y, 3), round(self.heading_z, 3)],
            'state': self.state, 'target_obj': self.target_obj,
            'is_player': self.is_player,
        }


class SystemObject:
    """A fixed object in the system (station, gate, planet) with 3D position."""
    __slots__ = ('id', 'name', 'obj_type', 'x', 'y', 'z', 'station_id', 'au_distance', 'connects_to', 'parent', 'ss_x', 'ss_z')

    def __init__(self, id, name, obj_type, x, y, z, station_id='', au_distance=0.0, connects_to='', parent='', ss_x=0.0, ss_z=0.0):
        self.id = id
        self.name = name
        self.obj_type = obj_type
        self.x = x
        self.y = y
        self.z = z
        self.station_id = station_id
        self.au_distance = au_distance
        self.connects_to = connects_to
        self.parent = parent
        self.ss_x = ss_x
        self.ss_z = ss_z


# Scale: 1 unit = 1 km. Local grid is ~500km radius.
# Ship speeds in m/s -> km/s = speed/1000. At 95 m/s base = 0.095 km/s.
# With afterburner: ~0.5 km/s. MWD: ~3 km/s.
# Warp between grids uses AU scale separately (not in local space).
LOCAL_GRID_RADIUS = 500  # km
WARP_SPEED_MULT = 0.0015  # AU/s per m/s -- used for intra-system warp only


class LocalSpaceWorker:
    """Maintains the 3D state of the player's current system."""

    def __init__(self):
        self.system_id = ''
        self._anchor_id = ''
        self.objects = []  # SystemObject list
        self.ships = {}  # id -> LocalShip
        self.player_ship = None  # reference to player's LocalShip
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name='local_space')
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            time.sleep(1.0)  # 1 tick per second
            with self._lock:
                self._tick()

    def _tick(self):
        """Advance all ships one tick."""
        for ship in list(self.ships.values()):
            if ship.state == 'flying':
                self._move_flying(ship)
            elif ship.state == 'warping':
                self._move_warping(ship)
            elif ship.state == 'arriving':
                self._move_arriving(ship)
            elif ship.state == 'departing':
                self._move_departing(ship)
            elif ship.state == 'idle' and ship.speed > 0:
                self._decelerate(ship)
            elif ship.state == 'docked' and not ship.is_player:
                # Random chance to undock and fly around locally
                if random.random() < 0.05:  # 5% per tick = undock every ~20 sec
                    self._npc_undock_local(ship)

    def _npc_undock_local(self, ship):
        """NPC undocks and flies to a random nearby point."""
        ship.state = 'flying'
        ship._flight_timer = random.randint(40, 120)
        ship._target_hx = random.uniform(-1, 1)
        ship._target_hy = random.uniform(-0.3, 0.3)
        ship._target_hz = random.uniform(-1, 1)
        d = math.sqrt(ship._target_hx**2 + ship._target_hy**2 + ship._target_hz**2) or 1
        ship._target_hx /= d
        ship._target_hy /= d
        ship._target_hz /= d
        ship.heading_x = ship._target_hx
        ship.heading_y = ship._target_hy
        ship.heading_z = ship._target_hz
        ship.speed = 0

    def _decelerate(self, ship):
        """Gradually slow down a stopped ship."""
        ship.speed *= 0.85
        if ship.speed < 0.5:
            ship.speed = 0
            ship.vx = ship.vy = ship.vz = 0
            return
        ship.vx = ship.heading_x * ship.speed
        ship.vy = ship.heading_y * ship.speed
        ship.vz = ship.heading_z * ship.speed
        ship.x += ship.vx
        ship.y += ship.vy
        ship.z += ship.vz

    def _move_flying(self, ship):
        """Move ship along its heading at current speed (km scale)."""
        # NPC flight timer - stop after duration
        if not ship.is_player and ship._flight_timer > 0:
            ship._flight_timer -= 1
            if ship._flight_timer <= 0:
                ship.state = 'idle'
                ship.speed = 0
                ship.vx = ship.vy = ship.vz = 0
                return
        # Gradual turn toward target heading
        lerp_rate = 0.08
        ship.heading_x += (ship._target_hx - ship.heading_x) * lerp_rate
        ship.heading_y += (ship._target_hy - ship.heading_y) * lerp_rate
        ship.heading_z += (ship._target_hz - ship.heading_z) * lerp_rate
        d = math.sqrt(ship.heading_x**2 + ship.heading_y**2 + ship.heading_z**2) or 1
        ship.heading_x /= d
        ship.heading_y /= d
        ship.heading_z /= d
        # Accelerate toward max_speed
        if ship.speed < ship.max_speed:
            accel = ship.max_speed * 0.08
            ship.speed = min(ship.max_speed, ship.speed + accel)
        # Move: speed is m/s, 1 tick = 1 sec, 1 unit = 1 meter
        ship.vx = ship.heading_x * ship.speed
        ship.vy = ship.heading_y * ship.speed
        ship.vz = ship.heading_z * ship.speed
        ship.x += ship.vx
        ship.y += ship.vy
        ship.z += ship.vz

    def _move_warping(self, ship):
        """Warp: move ship toward target object at warp speed."""
        target = self._get_object(ship.target_obj)
        if not target:
            ship.state = 'idle'
            return
        dx = target.x - ship.x
        dy = target.y - ship.y
        dz = target.z - ship.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < 5:  # arrived (within 5 units = ~0.005 AU)
            ship.x = target.x
            ship.y = target.y
            ship.z = target.z
            ship.state = 'idle'
            ship.speed = 0
            ship.vx = ship.vy = ship.vz = 0
            ship.target_obj = None
            return
        # Warp speed in units/tick
        warp_speed = ship.max_speed * 0.05
        move = min(warp_speed, dist)
        nx, ny, nz = dx/dist, dy/dist, dz/dist
        ship.heading_x = nx
        ship.heading_y = ny
        ship.heading_z = nz
        ship.vx = nx * move
        ship.vy = ny * move
        ship.vz = nz * move
        ship.x += ship.vx
        ship.y += ship.vy
        ship.z += ship.vz
        ship.speed = move / 0.05 if True else 0

    def _move_arriving(self, ship):
        """NPC arriving from gate - fly toward a station."""
        # Pick random station if no target
        if not ship.target_obj:
            stations = [o for o in self.objects if o.obj_type == 'station']
            if stations:
                ship.target_obj = random.choice(stations).id
            else:
                ship.state = 'idle'
                return
        target = self._get_object(ship.target_obj)
        if not target:
            ship.state = 'idle'
            return
        dx = target.x - ship.x
        dy = target.y - ship.y
        dz = target.z - ship.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < 5:
            ship.state = 'docked'
            ship.speed = 0
            ship.vx = ship.vy = ship.vz = 0
            return
        # Warp to station
        warp_speed = ship.max_speed * 0.05
        move = min(warp_speed, dist)
        nx, ny, nz = dx/dist, dy/dist, dz/dist
        ship.heading_x, ship.heading_y, ship.heading_z = nx, ny, nz
        ship.vx = nx * move
        ship.vy = ny * move
        ship.vz = nz * move
        ship.x += ship.vx
        ship.y += ship.vy
        ship.z += ship.vz

    def _move_departing(self, ship):
        """NPC departing toward a gate to leave system."""
        target = self._get_object(ship.target_obj)
        if not target:
            # Remove ship from local space
            self.ships.pop(ship.id, None)
            return
        dx = target.x - ship.x
        dy = target.y - ship.y
        dz = target.z - ship.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < 5:
            # Ship leaves system
            self.ships.pop(ship.id, None)
            return
        warp_speed = ship.max_speed * 0.05
        move = min(warp_speed, dist)
        nx, ny, nz = dx/dist, dy/dist, dz/dist
        ship.heading_x, ship.heading_y, ship.heading_z = nx, ny, nz
        ship.x += nx * move
        ship.y += ny * move
        ship.z += nz * move

    def _get_object(self, obj_id):
        for o in self.objects:
            if o.id == obj_id:
                return o
        return None

    # ── Public API (called from Flask endpoints) ──

    def load_system(self, system_id, system_objects, npc_ships_in_system, ship_speed_map=None, anchor_station_id=''):
        """Initialize local space for a system. Called when player enters."""
        if ship_speed_map is None:
            ship_speed_map = {}
        with self._lock:
            self.system_id = system_id
            # ── NEW LSG SYSTEM ──
            # 1 unit = 1 centimeter. All models scaled 100x smaller.
            # Target object at (0,0,0). Player arrives at offset.
            # SS (Solar System) coordinates stored on objects for nav/label display.
            # Only nearby objects (moons of planet, etc.) get placed in LSG.
            # LSG usable range: ~10,000,000 units = 100,000m = 100km (plenty)
            #
            # Scale: ship 30m = 0.3 units. Station 8km = 80 units.
            # Speed: 111 m/s = 1.11 units/s. 
            # Camera orbit: 80m = 0.8 units.

            self.objects = []
            for obj in system_objects:
                # Store SS coordinates (AU-based polar -> cartesian) for nav display
                ss_x = obj.distance * math.cos(obj.angle)
                ss_z = obj.distance * math.sin(obj.angle)
                # LSG position: not placed in grid by default (0,0,0 means "not in local space")
                # Only the anchor target and nearby objects get real LSG positions
                self.objects.append(SystemObject(obj.id, obj.name, obj.obj_type, 0, 0, 0,
                                                getattr(obj, 'station_id', ''),
                                                au_distance=obj.distance,
                                                connects_to=getattr(obj, 'connects_to', ''),
                                                parent=getattr(obj, 'parent', ''),
                                                ss_x=ss_x, ss_z=ss_z))

            # Find anchor object and set it at origin
            anchor_obj = None
            if anchor_station_id:
                for o in self.objects:
                    if o.station_id == anchor_station_id:
                        anchor_obj = o
                        break
            if not anchor_obj:
                for o in self.objects:
                    if o.station_id:
                        anchor_obj = o
                        break

            # Place moons near their parent planet if anchor is a planet
            # (For now, just place anchor at origin - client handles the rest)
            if anchor_obj:
                anchor_obj.x = 0
                anchor_obj.y = 0
                anchor_obj.z = 0
            self._anchor_id = anchor_obj.id if anchor_obj else ''

            # Place NPC ships around the anchor (within 30 units = 3000cm = 30m scaled)
            self.ships = {}
            for npc in npc_ships_in_system:
                # Look up real speed from DB (m/s), scale to cm/s (/100)
                real_speed = ship_speed_map.get(npc.ship_class, 80) / 100.0
                if anchor_obj:
                    # Spread ships in a wider radius around anchor
                    r = random.uniform(2, 30)
                    angle = random.uniform(0, math.pi * 2)
                    x = anchor_obj.x + math.cos(angle) * r
                    y = random.uniform(-2, 2)
                    z = anchor_obj.z + math.sin(angle) * r
                else:
                    x = random.uniform(-20, 20)
                    y = random.uniform(-2, 2)
                    z = random.uniform(-20, 20)
                ls = LocalShip(
                    id=npc.id, name=npc.name, ship_class=npc.ship_class,
                    role=npc.role, faction=npc.faction,
                    x=x, y=y, z=z, max_speed=real_speed,
                    state='docked' if npc.state in ('idle', 'loading', 'unloading') else 'arriving'
                )
                if npc.state == 'intra_traveling' and npc.intra_destination:
                    ls.state = 'arriving'
                    ls.target_obj = npc.intra_destination
                # Start ~40% of ships already flying so local space feels alive
                elif ls.state == 'docked' and random.random() < 0.4:
                    ls.state = 'flying'
                    ls._flight_timer = random.randint(30, 80)
                    ls._target_hx = random.uniform(-1, 1)
                    ls._target_hy = random.uniform(-0.2, 0.2)
                    ls._target_hz = random.uniform(-1, 1)
                    d = math.sqrt(ls._target_hx**2 + ls._target_hy**2 + ls._target_hz**2) or 1
                    ls._target_hx /= d
                    ls._target_hy /= d
                    ls._target_hz /= d
                    ls.heading_x = ls._target_hx
                    ls.heading_y = ls._target_hy
                    ls.heading_z = ls._target_hz
                    ls.speed = real_speed * random.uniform(0.5, 1.0)
                self.ships[npc.id] = ls

    def set_player_ship(self, ship_id, ship_class, speed, align_time, position_obj_id):
        """Place or update the player ship in local space."""
        with self._lock:
            # Player starts at origin (0,0,0). Station is 2km away.
            x, y, z = 0, 0, 0
            if ship_id in self.ships:
                ps = self.ships[ship_id]
                ps.max_speed = speed
                ps.align_time = align_time
            else:
                ps = LocalShip(id=ship_id, name='Player Ship', ship_class=ship_class,
                               x=x, y=y, z=z, max_speed=speed, align_time=align_time,
                               state='idle', is_player=True)
                self.ships[ship_id] = ps
            self.player_ship = ps

    def player_fly(self, dx, dy, dz):
        """Set player target heading to fly in a direction (ship will gradually turn)."""
        with self._lock:
            if not self.player_ship:
                return
            d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1
            self.player_ship._target_hx = dx / d
            self.player_ship._target_hy = dy / d
            self.player_ship._target_hz = dz / d
            self.player_ship.state = 'flying'

    def player_undock(self):
        """Place player at dock boundary (20 units from station), heading away."""
        with self._lock:
            if not self.player_ship:
                return
            # Find the player's station
            station = None
            for o in self.objects:
                if o.station_id:
                    station = o
                    break
            if station:
                # Place player 20 units from station center (= 2000cm = 20m)
                import random as _rnd
                angle = _rnd.uniform(0, math.pi * 2)
                self.player_ship.x = station.x + math.cos(angle) * 20
                self.player_ship.y = station.y + _rnd.uniform(-1, 1)
                self.player_ship.z = station.z + math.sin(angle) * 20
                # Heading away from station
                dx = self.player_ship.x - station.x
                dy = self.player_ship.y - station.y
                dz = self.player_ship.z - station.z
                d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1
                self.player_ship.heading_x = dx / d
                self.player_ship.heading_y = dy / d
                self.player_ship.heading_z = dz / d
                self.player_ship._target_hx = self.player_ship.heading_x
                self.player_ship._target_hy = self.player_ship.heading_y
                self.player_ship._target_hz = self.player_ship.heading_z
            self.player_ship.state = 'idle'
            self.player_ship.speed = 0
            self.player_ship.state = 'idle'

    def player_stop(self):
        """Begin decelerating player ship."""
        with self._lock:
            if not self.player_ship:
                return
            self.player_ship.state = 'idle'
            # Deceleration handled in tick (gradual)

    def player_warp(self, target_obj_id):
        """Start player warp to an object."""
        with self._lock:
            if not self.player_ship:
                return
            self.player_ship.target_obj = target_obj_id
            self.player_ship.state = 'warping'

    def recenter_on_target(self, target_obj_id, from_x=0, from_z=0):
        """Re-anchor the LSG coordinate system around the warp target.
        
        Shifts all objects so the target is at (0, 0, 0).
        Places player 15-20km from target on the approach vector (from -> target).
        For planets, uses larger offset (2-3x radius equivalent).
        """
        with self._lock:
            target = None
            for o in self.objects:
                if o.id == target_obj_id:
                    target = o
                    break
            if not target:
                return

            # Update anchor to the new target
            self._anchor_id = target_obj_id

            # Shift all objects so target is at origin
            offset_x = target.x
            offset_y = target.y
            offset_z = target.z
            for o in self.objects:
                o.x -= offset_x
                o.y -= offset_y
                o.z -= offset_z

            # Determine arrival distance based on object type (in cm-scale units)
            # Planet: 800 units (= 800m real), Moon: 500, Gate: 100, Station: 500
            if target.obj_type == 'planet':
                arrival_dist = 800
            elif target.obj_type == 'moon':
                arrival_dist = 500
            elif target.obj_type == 'gate':
                arrival_dist = 100
            else:
                arrival_dist = 500

            # Approach vector: from the player's previous position toward target
            # (from_x, from_z are the player's position before warp in the OLD coordinate system)
            # In new coords, the "from" direction is (-offset_x, 0, -offset_z) normalized
            dx = -offset_x
            dz = -offset_z
            dist = math.sqrt(dx*dx + dz*dz)
            if dist > 0:
                dx /= dist
                dz /= dist
            else:
                dx, dz = 1, 0

            # Place player at arrival_dist from target, along approach vector
            if self.player_ship:
                self.player_ship.x = dx * arrival_dist
                self.player_ship.y = 0
                self.player_ship.z = dz * arrival_dist
                # Face toward target (heading points from player toward origin/target)
                self.player_ship.heading_x = -dx
                self.player_ship.heading_y = 0
                self.player_ship.heading_z = -dz
                self.player_ship._target_hx = -dx
                self.player_ship._target_hy = 0
                self.player_ship._target_hz = -dz
                self.player_ship.speed = 0
                self.player_ship.vx = 0
                self.player_ship.vy = 0
                self.player_ship.vz = 0
                self.player_ship.state = 'idle'
                self.player_ship.target_obj = None

    def get_state(self):
        """Return local space state for the client (NPCs + objects, not player ship)."""
        with self._lock:
            return {
                'system_id': self.system_id,
                'objects': [{'id': o.id, 'name': o.name, 'type': o.obj_type,
                             'x': round(o.x, 2), 'y': round(o.y, 2), 'z': round(o.z, 2),
                             'station_id': o.station_id,
                             'au_distance': round(o.au_distance, 4),
                             'connects_to': o.connects_to,
                             'parent': o.parent,
                             'ss_x': round(o.ss_x, 4), 'ss_z': round(o.ss_z, 4),
                             'is_anchor': (o.id == self._anchor_id)} for o in self.objects],
                'ships': [s.to_dict() for s in self.ships.values() if not s.is_player],
                'player': self.player_ship.to_dict() if self.player_ship else None,
            }

    def npc_arrive(self, ship_id, name, ship_class, role, faction, speed, gate_obj_id, dest_obj_id):
        """NPC ship arrives in system via gate."""
        with self._lock:
            gate = self._get_object(gate_obj_id)
            if not gate:
                return
            ls = LocalShip(id=ship_id, name=name, ship_class=ship_class, role=role,
                           faction=faction, x=gate.x, y=gate.y, z=gate.z, max_speed=speed,
                           state='arriving')
            ls.target_obj = dest_obj_id
            self.ships[ship_id] = ls

    def npc_depart(self, ship_id, gate_obj_id):
        """NPC ship begins departing toward gate."""
        with self._lock:
            ship = self.ships.get(ship_id)
            if ship:
                ship.state = 'departing'
                ship.target_obj = gate_obj_id
