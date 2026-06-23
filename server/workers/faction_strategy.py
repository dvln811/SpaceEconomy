"""Faction Strategy worker: decision engine driven by faction state + agent personalities."""
import random
import sqlite3
import json
import os
from server.supervisor import WorkerThread
from server.intents import FactionOrder, EventLog

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "game_data.db")

SPECIALTY_TASKS = {
    'mining': ['mining_ops'],
    'refining': ['production_boost'],
    'weapons_manufacturing': ['weapons_supply', 'ship_construction'],
    'ship_construction': ['ship_construction'],
    'logistics': ['supply_hauling'],
    'defense_contracting': ['patrol', 'defense_supply'],
    'electronics': ['production_boost'],
    'pharmaceuticals': ['trade_routes'],
    'energy_systems': ['production_boost'],
    'trade_brokerage': ['trade_routes'],
    'salvage_operations': ['mining_ops'],
    'research': ['production_boost'],
}

DECISION_TASKS = {
    'expand': ['supply_hauling', 'mining_ops'],
    'attack': ['ship_construction', 'weapons_supply'],
    'reinforce': ['patrol', 'defense_supply'],
    'develop': ['trade_routes', 'production_boost'],
}

FNAME = {
    'terran_fed': 'Terran Federation', 'science_collective': 'Nexus Collective',
    'merchants_guild': 'Merchants Guild', 'free_states': 'Frontier Alliance',
    'iron_compact': 'Iron Compact', 'corsairs': 'The Corsairs'
}


class FactionStrategyWorker(WorkerThread):
    def __init__(self):
        super().__init__("faction_strategy", tick_interval=100)
        self._load_faction_data()

    def _load_faction_data(self):
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        self.faction_states = {}
        for r in conn.execute("SELECT * FROM faction_state"):
            self.faction_states[r['faction_id']] = dict(r)
        self.agents = {}
        for r in conn.execute("SELECT * FROM faction_agents WHERE alive=1"):
            fid = r['faction_id']
            if fid not in self.agents:
                self.agents[fid] = []
            self.agents[fid].append(dict(r))
        conn.close()

    def process(self, tick: int, snapshot):
        universe = snapshot['universe']
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row

        for fid, state in self.faction_states.items():
            assessment = self._assess(fid, universe)
            decision, reasoning = self._decide(fid, state, assessment, tick)
            if decision:
                self._log_decision(conn, fid, tick, decision, reasoning)
                self._assign_corps(conn, fid, decision, tick)
                self._update_phases(conn, fid, tick)
                if decision == 'attack':
                    self._maybe_create_fleet_build(conn, fid, tick)
                self._execute(fid, decision, assessment, tick)

        conn.commit()
        conn.close()

    def _assess(self, fid, universe):
        systems = 0
        stations = 0
        producing = 0
        halted = 0
        border_systems = []
        threat_systems = []

        for sid, sys in universe.items():
            if sys.faction == fid:
                systems += 1
                stations += len(sys.stations)
                for st in sys.stations:
                    for _ in st.produces:
                        producing += 1
                        if st.effective_rate < 0.01:
                            halted += 1
                for neighbor_id in sys.connections:
                    nsys = universe.get(neighbor_id)
                    if nsys and not nsys.faction:
                        border_systems.append(neighbor_id)
                    elif nsys and nsys.faction and nsys.faction != fid:
                        threat_systems.append((neighbor_id, nsys.faction))

        return {
            'systems': systems,
            'stations': stations,
            'producing': producing,
            'halted': halted,
            'health': producing / max(producing + halted, 1),
            'border_systems': list(set(border_systems))[:10],
            'threats': threat_systems[:10],
        }

    def _decide(self, fid, state, assessment, tick):
        leader = None
        for a in self.agents.get(fid, []):
            if a['role'] == 'leader':
                leader = a
                break
        if not leader:
            return None, ''

        aggression = state['aggression'] * (0.7 + leader['aggression'] * 0.6)
        expansion = state['expansion_drive'] * (0.7 + (1 - leader['caution']) * 0.6)
        economic = state['economic_focus'] * (0.7 + leader['competence'] * 0.6)

        reasons = []
        if assessment['health'] < 0.5:
            economic += 0.3
            reasons.append(f"Economy struggling ({int(assessment['health']*100)}% health)")
        if assessment['health'] > 0.8 and assessment['border_systems']:
            expansion += 0.2
            reasons.append(f"Economy strong ({int(assessment['health']*100)}% health), {len(assessment['border_systems'])} border systems available")
        if len(assessment['threats']) > 3:
            aggression += 0.2
            reasons.append(f"{len(assessment['threats'])} threat contacts on borders")

        options = [
            ('expand', expansion),
            ('reinforce', economic),
            ('attack', aggression),
            ('develop', economic * 0.8),
        ]
        options = [(o, v + random.gauss(0, 0.1)) for o, v in options]
        options.sort(key=lambda x: -x[1])
        decision = options[0][0]

        if not reasons:
            reasons.append(f"{assessment['systems']} systems, {assessment['stations']} stations")
        reasoning = '; '.join(reasons)
        return decision, reasoning

    def _log_decision(self, conn, fid, tick, decision, reasoning):
        conn.execute(
            "INSERT INTO faction_decisions (faction_id, tick, decision, reasoning, details) VALUES (?,?,?,?,?)",
            (fid, tick, decision, reasoning, '')
        )
        # Prune to last 20 per faction
        conn.execute(
            "DELETE FROM faction_decisions WHERE faction_id=? AND id NOT IN (SELECT id FROM faction_decisions WHERE faction_id=? ORDER BY id DESC LIMIT 20)",
            (fid, fid)
        )

    def _assign_corps(self, conn, fid, decision, tick):
        needed_tasks = DECISION_TASKS.get(decision, [])
        corps = conn.execute(
            "SELECT id, specialty FROM corporations WHERE faction_id=? AND status='active'", (fid,)
        ).fetchall()

        for corp in corps:
            spec = corp['specialty'] or ''
            possible_tasks = SPECIALTY_TASKS.get(spec, [])
            # Find overlap between what's needed and what this corp can do
            matching = [t for t in possible_tasks if t in needed_tasks]
            if matching:
                task = matching[0]
            elif possible_tasks:
                task = possible_tasks[0]
            else:
                task = needed_tasks[0] if needed_tasks else 'idle'

            activity = json.dumps({"task": task, "target": decision, "progress": 0, "assigned_tick": tick})
            conn.execute("UPDATE corporations SET activity=? WHERE id=?", (activity, corp['id']))

    def _update_phases(self, conn, fid, tick):
        projects = conn.execute(
            "SELECT id, project_type, created_tick, phase, status FROM build_projects WHERE faction_id=? AND status='active'",
            (fid,)
        ).fetchall()

        for p in projects:
            age = tick - p['created_tick']
            new_phase = p['phase']

            if p['project_type'] == 'station_expansion':
                if age < 200:
                    new_phase = 'scouting'
                elif age < 600:
                    new_phase = 'staging'
                else:
                    new_phase = 'constructing'
            elif p['project_type'] in ('fleet_build', 'dreadnought'):
                if age < 200:
                    new_phase = 'requisitioning'
                elif age < 600:
                    new_phase = 'assembling'
                else:
                    new_phase = 'constructing'

            if new_phase != p['phase']:
                conn.execute("UPDATE build_projects SET phase=? WHERE id=?", (new_phase, p['id']))

    def _maybe_create_fleet_build(self, conn, fid, tick):
        # Only create if fewer than 3 active fleet builds
        count = conn.execute(
            "SELECT COUNT(*) FROM build_projects WHERE faction_id=? AND project_type='fleet_build' AND status='active'",
            (fid,)
        ).fetchone()[0]
        if count >= 3:
            return
        target = conn.execute("SELECT id FROM systems WHERE faction_id=? LIMIT 1", (fid,)).fetchone()
        target_sys = target[0] if target else ''
        ship_opts = [
            ('Build 3 Frigates', {"steel_plate": 300, "electronics": 120, "fuel_cells": 60}),
            ('Build 2 Corvettes', {"steel_plate": 600, "electronics": 250, "weapons_array": 150}),
        ]
        name, reqs = random.choice(ship_opts)
        conn.execute(
            "INSERT INTO build_projects (faction_id, project_type, project_name, target_system, requirements, accumulated, status, created_tick, phase) VALUES (?,?,?,?,?,?,?,?,?)",
            (fid, 'fleet_build', name, target_sys, json.dumps(reqs), '{}', 'active', tick, 'requisitioning')
        )

    def _execute(self, fid, decision, assessment, tick):
        fname = FNAME.get(fid, fid)

        if decision == 'expand' and assessment['border_systems']:
            admiral = self._get_agent(fid, 'admiral')
            target = random.choice(assessment['border_systems'])
            if admiral and random.random() > admiral['caution']:
                self.emit(FactionOrder(faction_id=fid, order_type='expand', target=target))
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} orders expansion into unclaimed territory"))
            else:
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} considers expansion but holds back"))

        elif decision == 'attack' and assessment['threats']:
            admiral = self._get_agent(fid, 'admiral') or self._get_agent(fid, 'general')
            target_sys, target_faction = random.choice(assessment['threats'])
            target_fname = FNAME.get(target_faction, target_faction)
            if admiral and random.random() < admiral['aggression']:
                self.emit(FactionOrder(faction_id=fid, order_type='attack', target=target_sys))
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} launches offensive against {target_fname}"))
            else:
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} musters forces along {target_fname} border"))

        elif decision == 'reinforce':
            governor = self._get_agent(fid, 'governor')
            if governor:
                efficiency = governor['competence'] * (1 - governor['corruption'])
                if efficiency > 0.5:
                    self.emit(FactionOrder(faction_id=fid, order_type='reinforce', target=''))
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} focuses on defensive reinforcement"))
                else:
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} defense programs stall due to mismanagement"))

        elif decision == 'develop':
            governor = self._get_agent(fid, 'governor')
            if governor:
                self.emit(FactionOrder(faction_id=fid, order_type='develop', target=''))
                if assessment['halted'] > 0:
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} prioritizes fixing {assessment['halted']} stalled production lines"))
                else:
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} invests in infrastructure development"))

    def _get_agent(self, fid, role):
        for a in self.agents.get(fid, []):
            if a['role'] == role:
                return a
        return None
