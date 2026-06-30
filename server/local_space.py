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
                 'speed', 'max_speed', 'heading_x', 'heading_y', 'heading_z',
                 'state', 'target_obj', 'dock_station', 'is_player')

    def __init__(self, id, name='', ship_class='', role='', faction='',
                 x=0, y=0, z=0, speed=0, max_speed=100, state='idle', is_player=False):
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
        self.heading_x = 1
        self.heading_y = 0
        self.heading_z = 0
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
            'heading': [round(self.heading_x, 3), round(self.heading_y, 3), round(self.heading_z, 3)],
            'state': self.state, 'target_obj': self.target_obj,
            'is_player': self.is_player,
        }


class SystemObject:
    """A fixed object in the system (station, gate, planet) with 3D position."""
    __slots__ = ('id', 'name', 'obj_type', 'x', 'y', 'z', 'station_id')

    def __init__(self, id, name, obj_type, x, y, z, station_id=''):
        self.id = id
        self.name = name
        self.obj_type = obj_type
        self.x = x
        self.y = y
        self.z = z
        self.station_id = station_id


# Scale: 1 AU = 1000 local space units. Ship speeds in m/s mapped to units/tick.
AU_SCALE = 1000.0
WARP_SPEED_MULT = 0.0015  # AU/s per m/s of ship speed -> units/tick


class LocalSpaceWorker:
    """Maintains the 3D state of the player's current system."""

    def __init__(self):
        self.system_id = ''
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
        for ship in self.ships.values():
            if ship.state == 'flying':
                self._move_flying(ship)
            elif ship.state == 'warping':
                self._move_warping(ship)
            elif ship.state == 'arriving':
                self._move_arriving(ship)
            elif ship.state == 'departing':
                self._move_departing(ship)

    def _move_flying(self, ship):
        """Move ship along its heading at current speed (local flight, m/s scale)."""
        # Accelerate toward max_speed
        if ship.speed < ship.max_speed:
            accel = ship.max_speed * 0.05  # 5% of max per tick
            ship.speed = min(ship.max_speed, ship.speed + accel)
        # Convert m/s to local units/tick (1 AU = 1000 units, 1 AU = 150M km)
        # At these scales, m/s is tiny. 100 m/s = 0.000000667 AU/s = 0.000667 units/tick
        # That's too small to see. For local flight (not warp), scale up for gameplay.
        move_rate = ship.speed * 0.01  # gameplay scale: 100 m/s = 1 unit/tick
        ship.vx = ship.heading_x * move_rate
        ship.vy = ship.heading_y * move_rate
        ship.vz = ship.heading_z * move_rate
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
        warp_speed = ship.max_speed * WARP_SPEED_MULT * AU_SCALE
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
        ship.speed = move / (WARP_SPEED_MULT * AU_SCALE) if WARP_SPEED_MULT * AU_SCALE > 0 else 0

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
        warp_speed = ship.max_speed * WARP_SPEED_MULT * AU_SCALE
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
        warp_speed = ship.max_speed * WARP_SPEED_MULT * AU_SCALE
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

    def load_system(self, system_id, system_objects, npc_ships_in_system):
        """Initialize local space for a system. Called when player enters."""
        with self._lock:
            self.system_id = system_id
            # Convert system objects to 3D positions
            self.objects = []
            for obj in system_objects:
                # obj has distance (AU) and angle (radians)
                x = obj.distance * math.cos(obj.angle) * AU_SCALE
                z = obj.distance * math.sin(obj.angle) * AU_SCALE
                y = hash(obj.name) % 50 - 25  # slight vertical spread
                self.objects.append(SystemObject(obj.id, obj.name, obj.obj_type, x, y, z,
                                                getattr(obj, 'station_id', '')))

            # Place NPC ships at their current positions
            self.ships = {}
            for npc in npc_ships_in_system:
                # Place at their intra_position object
                pos_obj = self._get_object(npc.intra_position) if npc.intra_position else None
                if pos_obj:
                    x, y, z = pos_obj.x + random.uniform(-20, 20), pos_obj.y + random.uniform(-5, 5), pos_obj.z + random.uniform(-20, 20)
                else:
                    x, y, z = random.uniform(-500, 500), random.uniform(-20, 20), random.uniform(-500, 500)
                ls = LocalShip(
                    id=npc.id, name=npc.name, ship_class=npc.ship_class,
                    role=npc.role, faction=npc.faction,
                    x=x, y=y, z=z, max_speed=npc.speed,
                    state='docked' if npc.state in ('idle', 'loading', 'unloading') else 'arriving'
                )
                if npc.state == 'intra_traveling' and npc.intra_destination:
                    ls.state = 'arriving'
                    ls.target_obj = npc.intra_destination
                self.ships[npc.id] = ls

    def set_player_ship(self, ship_id, ship_class, speed, position_obj_id):
        """Place or update the player ship in local space."""
        with self._lock:
            pos_obj = self._get_object(position_obj_id)
            x = pos_obj.x if pos_obj else 0
            y = pos_obj.y + 10 if pos_obj else 10
            z = pos_obj.z if pos_obj else 0
            if ship_id in self.ships:
                ps = self.ships[ship_id]
                ps.max_speed = speed
            else:
                ps = LocalShip(id=ship_id, name='Player Ship', ship_class=ship_class,
                               x=x, y=y, z=z, max_speed=speed, state='idle', is_player=True)
                self.ships[ship_id] = ps
            self.player_ship = ps

    def player_fly(self, dx, dy, dz):
        """Set player heading to fly in a direction."""
        with self._lock:
            if not self.player_ship:
                return
            d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1
            self.player_ship.heading_x = dx / d
            self.player_ship.heading_y = dy / d
            self.player_ship.heading_z = dz / d
            self.player_ship.state = 'flying'

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

    def get_state(self):
        """Return full local space state for the client."""
        with self._lock:
            return {
                'system_id': self.system_id,
                'objects': [{'id': o.id, 'name': o.name, 'type': o.obj_type,
                             'x': round(o.x, 1), 'y': round(o.y, 1), 'z': round(o.z, 1),
                             'station_id': o.station_id} for o in self.objects],
                'ships': [s.to_dict() for s in self.ships.values()],
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
