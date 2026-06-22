"""Faction Strategy worker: decision engine driven by faction state + agent personalities."""
import random
import sqlite3
import json
import os
from server.supervisor import WorkerThread
from server.intents import FactionOrder, EventLog

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "game_data.db")


class FactionStrategyWorker(WorkerThread):
    def __init__(self):
        super().__init__("faction_strategy", tick_interval=200)
        self._load_faction_data()

    def _load_faction_data(self):
        """Load faction state and agents from DB."""
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

        for fid, state in self.faction_states.items():
            assessment = self._assess(fid, universe)
            decision = self._decide(fid, state, assessment, tick)
            if decision:
                self._execute(fid, decision, assessment, tick)

    def _assess(self, fid, universe):
        """Assess faction's current situation."""
        systems = 0
        stations = 0
        producing = 0
        halted = 0
        border_systems = []  # systems adjacent to unclaimed space
        threat_systems = []  # enemy systems adjacent to ours

        for sid, sys in universe.items():
            if sys.faction == fid:
                systems += 1
                stations += len(sys.stations)
                for st in sys.stations:
                    for _ in st.produces:
                        producing += 1
                        if st.effective_rate < 0.01:
                            halted += 1
                # Check borders
                for neighbor_id in sys.connections:
                    nsys = universe.get(neighbor_id)
                    if nsys and not nsys.faction:
                        border_systems.append(neighbor_id)
                    elif nsys and nsys.faction and nsys.faction != fid:
                        # Check if enemy
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
        """Leader decides faction priority based on personality + situation."""
        leader = None
        for a in self.agents.get(fid, []):
            if a['role'] == 'leader':
                leader = a
                break
        if not leader:
            return None

        aggression = state['aggression'] * (0.7 + leader['aggression'] * 0.6)
        expansion = state['expansion_drive'] * (0.7 + (1 - leader['caution']) * 0.6)
        economic = state['economic_focus'] * (0.7 + leader['competence'] * 0.6)

        # Situation modifiers
        if assessment['health'] < 0.5:
            economic += 0.3  # economy struggling, focus inward
        if assessment['health'] > 0.8 and assessment['border_systems']:
            expansion += 0.2  # economy strong, can expand
        if len(assessment['threats']) > 3:
            aggression += 0.2  # surrounded by enemies

        # Pick highest priority
        options = [
            ('expand', expansion),
            ('reinforce', economic),
            ('attack', aggression),
            ('develop', economic * 0.8),
        ]

        # Add some noise so decisions aren't perfectly predictable
        options = [(o, v + random.gauss(0, 0.1)) for o, v in options]
        options.sort(key=lambda x: -x[1])
        return options[0][0]

    def _execute(self, fid, decision, assessment, tick):
        """Emit intents based on the decision, filtered through agent personalities."""
        fnames = {
            'terran_fed': 'Federation', 'science_collective': 'Nexus',
            'merchants_guild': 'Guild', 'free_states': 'Alliance',
            'iron_compact': 'Compact', 'corsairs': 'Corsairs'
        }
        fname = fnames.get(fid, fid)

        if decision == 'expand' and assessment['border_systems']:
            # Find the admiral to execute
            admiral = self._get_agent(fid, 'admiral')
            target = random.choice(assessment['border_systems'])
            # Admiral's caution affects whether they actually commit
            if admiral and random.random() > admiral['caution']:
                self.emit(FactionOrder(faction_id=fid, order_type='expand', target=target))
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} orders expansion into unclaimed territory"))
            else:
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} considers expansion but holds back"))

        elif decision == 'attack' and assessment['threats']:
            admiral = self._get_agent(fid, 'admiral') or self._get_agent(fid, 'general')
            target_sys, target_faction = random.choice(assessment['threats'])
            target_fname = fnames.get(target_faction, target_faction)
            if admiral and random.random() < admiral['aggression']:
                self.emit(FactionOrder(faction_id=fid, order_type='attack', target=target_sys))
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} launches offensive against {target_fname} territory"))
            else:
                self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} musters forces along {target_fname} border"))

        elif decision == 'reinforce':
            governor = self._get_agent(fid, 'governor')
            if governor:
                efficiency = governor['competence'] * (1 - governor['corruption'])
                if efficiency > 0.5:
                    self.emit(FactionOrder(faction_id=fid, order_type='reinforce', target=''))
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} focuses on economic reinforcement"))
                else:
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} economic programs stall due to mismanagement"))

        elif decision == 'develop':
            governor = self._get_agent(fid, 'governor')
            if governor:
                self.emit(FactionOrder(faction_id=fid, order_type='develop', target=''))
                if assessment['halted'] > 0:
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} prioritizes fixing {assessment['halted']} stalled production lines"))
                else:
                    self.emit(EventLog(tick=tick, msg=f"STRATEGY: {fname} invests in infrastructure development"))

    def _get_agent(self, fid, role):
        """Get an agent by role for a faction."""
        for a in self.agents.get(fid, []):
            if a['role'] == role:
                return a
        return None
