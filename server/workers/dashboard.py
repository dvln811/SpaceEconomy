"""Dashboard worker: updates the DashboardCache every 10 ticks."""
import json
import logging
from server.supervisor import WorkerThread
from server.dashboard_cache import DashboardCache

log = logging.getLogger("space_economy")


class DashboardWorker(WorkerThread):
    def __init__(self, commodities: dict, station_consumption: dict):
        super().__init__("dashboard", tick_interval=10)
        self.commodities = commodities
        self.station_consumption = station_consumption
        self.cache = DashboardCache()

    def process(self, tick: int, snapshot):
        # Build a minimal sim-like object from snapshot for the cache
        sim_proxy = _SimProxy(snapshot, tick)
        self.cache.update(sim_proxy, self.commodities, self.station_consumption)

        # Inject warfare status from battle_sim worker if available
        # (will be injected externally by main.py on read)

        # Inject faction data
        try:
            from server.game_data_db import get_data_db
            _name_map = {'corsairs': 'The Corsairs', 'free_states': 'Frontier Alliance', 'iron_compact': 'Iron Compact', 'merchants_guild': 'Merchants Guild', 'science_collective': 'Nexus Collective', 'terran_fed': 'Terran Federation'}
            _emblem_map = {'corsairs': 'the_corsairs.png', 'free_states': 'frontier_alliance.png', 'iron_compact': 'iron_compact.png', 'merchants_guild': 'merchants_guild.png', 'science_collective': 'nexus_collective.png', 'terran_fed': 'terran_federation.png'}
            fconn = get_data_db()
            faction_status = {}
            for fs in fconn.execute("SELECT faction_id, aggression, expansion_drive, economic_focus FROM faction_state").fetchall():
                fid = fs['faction_id']
                sys_count = sum(1 for s in snapshot['universe'].values() if s.faction == fid)
                faction_status[fid] = {"name": _name_map.get(fid, fid), "systems": sys_count, "emblem": _emblem_map.get(fid, ''), "aggression": fs['aggression'], "expansion": fs['expansion_drive'], "economic": fs['economic_focus'], "projects": [], "fleet_builds": [], "corporations": [], "decisions": []}
            for p in fconn.execute("SELECT faction_id, project_type, project_name, target_system, requirements, accumulated, status, phase FROM build_projects").fetchall():
                reqs = json.loads(p['requirements'])
                acc = json.loads(p['accumulated'])
                total_needed = sum(reqs.values())
                total_have = sum(min(acc.get(k, 0), v) for k, v in reqs.items())
                pct = round(100 * total_have / total_needed) if total_needed > 0 else 0
                if p['faction_id'] not in faction_status:
                    continue
                if p['project_type'] == 'fleet_build':
                    faction_status[p['faction_id']]["fleet_builds"].append({"name": p['project_name'], "phase": p['phase'] or 'requisitioning', "progress": pct, "status": p['status']})
                else:
                    faction_status[p['faction_id']]["projects"].append({"name": p['project_name'], "type": p['project_type'], "phase": p['phase'] or 'constructing', "target": p['target_system'], "progress": pct, "status": p['status']})
            for c in fconn.execute("SELECT name, faction_id, specialty, activity FROM corporations WHERE status='active'").fetchall():
                if c['faction_id'] not in faction_status:
                    continue
                act = json.loads(c['activity']) if c['activity'] else {}
                faction_status[c['faction_id']]["corporations"].append({"name": c['name'], "specialty": c['specialty'] or '', "activity": act.get('task', 'idle'), "target": act.get('target', '')})
            for d in fconn.execute("SELECT faction_id, tick, decision, reasoning FROM faction_decisions ORDER BY id DESC").fetchall():
                if d['faction_id'] in faction_status and len(faction_status[d['faction_id']]["decisions"]) < 5:
                    faction_status[d['faction_id']]["decisions"].append({"tick": d['tick'], "decision": d['decision'], "reasoning": d['reasoning'] or ''})
            fconn.close()
            self.cache.data['factions'] = faction_status
        except Exception as e:
            log.debug(f"Dashboard faction query failed: {e}")
            self.cache.data['factions'] = {}


class _SimProxy:
    """Lightweight proxy exposing sim attributes from a snapshot dict."""
    def __init__(self, snapshot, tick):
        self.universe = snapshot['universe']
        self.ships = snapshot['ships']
        self.tick_count = tick
        self.events = snapshot.get('events', [])
        self.trade_volume = snapshot.get('trade_volume', 0)
        self.start_time = snapshot.get('start_time', 0)
