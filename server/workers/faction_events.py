"""Faction Event Worker: wraps FactionEventGenerator into a simulation worker.

Replaces the old EventGeneratorWorker. Fires every 200 ticks, generates
structured events referencing real agents, applies effects, logs history.
"""
import sqlite3
import os
from server.supervisor import WorkerThread
from server.intents import EventLog
from server.event_framework import FactionEventGenerator
from server.agent_lifecycle import process_event_effects, record_structured_event

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "game_data.db")


class FactionEventWorker(WorkerThread):
    def __init__(self):
        super().__init__("faction_events", tick_interval=200)
        self._generator = FactionEventGenerator()
        self._agents_by_faction = {}
        self._systems_by_faction = {}
        self._stations_by_faction = {}
        self._load_data()

    def _load_data(self):
        """Load agents and systems from DB."""
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row

        self._agents_by_faction = {}
        for row in conn.execute("SELECT * FROM faction_agents WHERE alive=1").fetchall():
            fid = row['faction_id']
            if fid not in self._agents_by_faction:
                self._agents_by_faction[fid] = []
            self._agents_by_faction[fid].append(dict(row))

        self._systems_by_faction = {}
        for row in conn.execute("SELECT id, name, faction_id FROM systems WHERE faction_id != ''").fetchall():
            fid = row['faction_id']
            if fid not in self._systems_by_faction:
                self._systems_by_faction[fid] = []
            self._systems_by_faction[fid].append((row['id'], row['name']))

        self._stations_by_faction = {}
        for row in conn.execute("""SELECT s.id, s.name, s.station_type, s.system_id, sys.faction_id
                                   FROM stations s JOIN systems sys ON s.system_id = sys.id
                                   WHERE sys.faction_id != ''""").fetchall():
            fid = row['faction_id']
            if fid not in self._stations_by_faction:
                self._stations_by_faction[fid] = []
            self._stations_by_faction[fid].append((row['id'], row['name'], row['station_type'], row['system_id']))

        conn.close()

    def _agent_name(self, agent_id):
        if not agent_id:
            return ''
        for agents in self._agents_by_faction.values():
            for a in agents:
                if a.get('id') == agent_id:
                    return a.get('name', '')
        return ''

    def process(self, tick: int, snapshot):
        # Reload agents every 1000 ticks to pick up deaths/spawns
        if tick % 1000 == 0:
            self._load_data()

        events = self._generator.generate_tick_events(
            tick, self._agents_by_faction, self._systems_by_faction, self._stations_by_faction)

        for event in events:
            # Record to DB
            record_structured_event(event)
            # Apply effects (kill agents, transfer wealth, etc)
            process_event_effects(event)
            # Emit to news ticker via existing EventLog system
            self.emit(EventLog(tick=tick, msg=event.news_msg,
                               agent_id=event.agent_id, agent_name=self._agent_name(event.agent_id),
                               category=event.category))
