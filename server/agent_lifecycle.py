"""Agent lifecycle: processes event effects on agents, logs history."""
import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "game_data.db")


def process_event_effects(event):
    """Apply an event's effects to agents/DB. Call after event is generated.
    
    Supported effect types:
    - agent_killed: marks agent as dead
    - agent_lost: marks agent as dead (defection/mutiny)
    - leader_change: updates faction leader
    - wealth_transfer: moves wealth between agents
    """
    if not event.effects:
        return

    conn = sqlite3.connect(DB)
    for effect in event.effects:
        etype = effect.get('type', '')
        target = effect.get('target', '')

        if etype in ('agent_killed', 'agent_lost') and target:
            conn.execute("UPDATE faction_agents SET alive=0, died_tick=?, cause_of_death=? WHERE id=?",
                         (event.tick, event.title[:100], target))
            log_history(conn, event.tick, target, 'death', event.title, system_id=event.system_id)

        elif etype == 'leader_change' and target:
            conn.execute("UPDATE faction_state SET leader_id=? WHERE faction_id=?",
                         (target, event.faction_id))
            log_history(conn, event.tick, target, 'promoted_leader', event.title)

        elif etype == 'wealth_transfer':
            amount = effect.get('value', 0)
            from_id = effect.get('from', '')
            to_id = effect.get('to', '')
            if from_id:
                conn.execute("UPDATE faction_agents SET wealth = max(0, wealth - ?) WHERE id=?", (amount, from_id))
            if to_id:
                conn.execute("UPDATE faction_agents SET wealth = wealth + ? WHERE id=?", (amount, to_id))

    conn.commit()
    conn.close()


def log_history(conn, tick, agent_id, event_type, detail, related_agent_id='', system_id=''):
    """Log an entry to agent_history."""
    conn.execute("""INSERT INTO agent_history (tick, agent_id, event_type, detail, related_agent_id, system_id)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                 (tick, agent_id, event_type, detail[:200], related_agent_id, system_id))


def log_event_for_agents(conn, event):
    """Log this event in history for all involved agents."""
    if event.agent_id:
        log_history(conn, event.tick, event.agent_id, event.category,
                    event.title[:200], system_id=event.system_id)


def record_structured_event(event):
    """Persist a StructuredEvent to the sim_events table."""
    conn = sqlite3.connect(DB)
    d = event.to_dict()
    conn.execute("""INSERT INTO sim_events (tick, category, severity, faction_id, system_id,
                    agent_id, title, detail, effects, chain_id, chain_step)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                 (d['tick'], d['category'], d['severity'], d['faction_id'], d['system_id'],
                  d['agent_id'], d['title'], d['detail'], d['effects'], d['chain_id'], d['chain_step']))
    # Log to agent history
    if event.agent_id:
        log_history(conn, event.tick, event.agent_id, event.category, event.title[:200],
                    system_id=event.system_id)
    conn.commit()
    conn.close()
