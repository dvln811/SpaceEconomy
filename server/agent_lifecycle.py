"""Agent lifecycle: processes event effects on agents, logs history."""
import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "game_data.db")


def process_event_effects(event):
    """Apply an event's effects to agents/DB. Call after event is generated.
    
    Supported effect types:
    - agent_killed: marks agent as dead, spawns replacement
    - agent_lost: marks agent as dead (defection/mutiny), spawns replacement
    - leader_change: updates faction leader
    - wealth_transfer: moves wealth between agents
    """
    if not event.effects:
        return

    conn = sqlite3.connect(DB, timeout=10)
    for effect in event.effects:
        etype = effect.get('type', '')
        target = effect.get('target', '')

        if etype in ('agent_killed', 'agent_lost') and target:
            # Get dead agent's info before killing
            row = conn.execute("SELECT faction_id, role, system_id, station_id FROM faction_agents WHERE id=?",
                               (target,)).fetchone()
            conn.execute("UPDATE faction_agents SET alive=0, died_tick=?, cause_of_death=? WHERE id=?",
                         (event.tick, event.title[:100], target))
            log_history(conn, event.tick, target, 'death', event.title, system_id=event.system_id)
            # Spawn replacement
            if row:
                _spawn_replacement(conn, row[0], row[1], row[2], row[3], event.tick)

        elif etype == 'leader_change' and target:
            # Demote old leader if still alive
            conn.execute("UPDATE faction_agents SET role='admiral' WHERE faction_id=? AND role='leader' AND id!=? AND alive=1",
                         (event.faction_id, target))
            # Promote new leader
            conn.execute("UPDATE faction_agents SET role='leader' WHERE id=?", (target,))
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
    conn = sqlite3.connect(DB, timeout=10)
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



def _spawn_replacement(conn, faction_id, role, system_id, station_id, tick):
    """Spawn a new agent to fill a vacated role."""
    import random
    from server.agent_population import generate_name, generate_trait, POP_TITLES, FACTION_BIAS

    bias = FACTION_BIAS.get(faction_id, {})
    gender = random.choice(['male', 'female'])
    used = set(r[0] for r in conn.execute("SELECT name FROM faction_agents WHERE faction_id=?", (faction_id,)).fetchall())
    name = generate_name(faction_id, gender, used)
    titles = POP_TITLES.get(role, ['Officer'])
    title = random.choice(titles)
    agent_id = f"{faction_id}_{role}_{random.randint(10000,99999)}"
    # Avoid ID collision with existing/dead agents
    existing = set(r[0] for r in conn.execute("SELECT id FROM faction_agents WHERE id LIKE ?", (f"{faction_id}_{role}_%",)).fetchall())
    while agent_id in existing:
        agent_id = f"{faction_id}_{role}_{random.randint(100000,999999)}"

    conn.execute("""INSERT INTO faction_agents
        (id, name, title, faction_id, role, aggression, caution, competence,
         loyalty, ambition, corruption, system_id, station_id, rank, wealth, gender, alive)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
        (agent_id, name, title, faction_id, role,
         generate_trait(0.5, bias.get('aggression', 0)),
         generate_trait(0.5, bias.get('caution', 0)),
         generate_trait(0.5, bias.get('competence', 0)),
         generate_trait(0.6, bias.get('loyalty', 0)),
         generate_trait(0.4, bias.get('ambition', 0)),
         generate_trait(0.1, bias.get('corruption', 0)),
         system_id or '', station_id or '', 1,
         round(random.uniform(50, 200), 1), gender))

    log_history(conn, tick, agent_id, 'spawned', f"Replaces fallen predecessor as {title}", system_id=system_id or '')
