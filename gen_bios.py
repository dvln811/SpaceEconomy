"""Generate short bios for all agents that don't have one."""
import sqlite3, random

conn = sqlite3.connect('data/game_data.db')
conn.row_factory = sqlite3.Row

# Bio templates by role
TEMPLATES = {
    'station_commander': [
        "Runs a tight operation. Known for {trait} and {habit}.",
        "Former {background} who earned command through {achievement}.",
        "Keeps the station profitable despite {challenge}. {quirk}.",
    ],
    'fleet_captain': [
        "Veteran of {count} engagements. Favors {style} tactics.",
        "Rose through the ranks after {achievement}. Crew is fiercely loyal.",
        "Former {background}. Commands from the bridge with {trait}.",
    ],
    'merchant_lord': [
        "Built a fortune trading {goods}. {quirk}.",
        "Controls {count} trade contracts across the region. Known for {trait}.",
        "Started with a single cargo hold. Now owns {count} vessels.",
    ],
    'mining_foreman': [
        "Spent {count} years in the belts. Knows every rock by name.",
        "Runs extraction ops with ruthless efficiency. {quirk}.",
        "Former {background} who found better pay underground.",
    ],
    'factory_overseer': [
        "Keeps production lines running {hours} hours a day. {trait}.",
        "Promoted after streamlining output by {count}%. {quirk}.",
        "Known for demanding perfection. Workers respect but fear them.",
    ],
    'mercenary_leader': [
        "Sells their skills to the highest bidder. {count} confirmed kills.",
        "Former {background} gone freelance. No job too dirty if the pay is right.",
        "Runs a small but effective crew. Reputation for {trait}.",
    ],
    'smuggler': [
        "Moves contraband through routes nobody else dares. {quirk}.",
        "Has contacts in {count} systems. Never caught -- so far.",
        "Former {background}. Found crime more profitable than honest work.",
    ],
    'diplomat': [
        "Negotiated {count} treaties. Speaks {count2} languages fluently.",
        "Prefers words to weapons. Has defused {count} potential conflicts.",
        "Known for {trait}. Trusted even by rivals.",
    ],
    'bounty_hunter': [
        "Tracks targets across sectors. {count} bounties collected.",
        "Works alone. Methodical, patient, and absolutely relentless.",
        "Former {background}. Now hunts those who break the law.",
    ],
    'spy': [
        "Identity classified. Operates deep behind enemy lines.",
        "Has {count} known aliases. True loyalties are uncertain.",
        "Recruited young. {quirk}. Nobody suspects them.",
    ],
}

TRAITS = ['iron discipline', 'sharp cunning', 'quiet intensity', 'relentless ambition',
          'cold pragmatism', 'easy charm', 'brutal honesty', 'patient calculation',
          'fierce loyalty', 'casual ruthlessness', 'quiet competence', 'natural authority']
HABITS = ['never sleeping more than four hours', 'personally inspecting every shipment',
          'keeping a detailed journal', 'drinking too much Arcturus brandy',
          'maintaining old friendships', 'trusting no one completely']
BACKGROUNDS = ['navy enlistee', 'mining crew grunt', 'corporate accountant', 'dock rat',
               'academy dropout', 'cargo hauler', 'security guard', 'street vendor',
               'refugee', 'farmer', 'mechanic', 'salvage diver']
ACHIEVEMENTS = ['a daring rescue operation', 'uncovering a smuggling ring',
                'surviving a corsair ambush alone', 'turning a failing post profitable',
                'a brilliant flanking maneuver', 'saving an entire crew from void exposure']
CHALLENGES = ['constant pirate harassment', 'chronic supply shortages',
              'aging infrastructure', 'a hostile workforce', 'corporate interference']
QUIRKS = ['Collects ancient star charts', 'Never removes their sidearm',
          'Speaks with a distinctive rim accent', 'Has a cybernetic left eye',
          'Keeps a small garden aboard ship', 'Always pays debts immediately',
          'Refuses to use autopilot', 'Known by a nickname nobody explains']
GOODS = ['rare minerals', 'weapons components', 'luxury goods', 'fuel cells',
         'medical supplies', 'ship parts', 'information']
STYLES = ['aggressive close-range', 'patient long-range', 'hit-and-run',
          'overwhelming force', 'deceptive maneuvering', 'defensive attrition']

def gen_bio(role):
    templates = TEMPLATES.get(role, ["A capable individual with a reputation for {trait}. {quirk}."])
    t = random.choice(templates)
    return t.format(
        trait=random.choice(TRAITS),
        habit=random.choice(HABITS),
        background=random.choice(BACKGROUNDS),
        achievement=random.choice(ACHIEVEMENTS),
        challenge=random.choice(CHALLENGES),
        quirk=random.choice(QUIRKS),
        goods=random.choice(GOODS),
        style=random.choice(STYLES),
        count=random.randint(3, 30),
        count2=random.randint(3, 6),
        hours=random.choice(['18', '20', '22']),
    )

agents = conn.execute("SELECT id, role FROM faction_agents WHERE bio = '' OR bio IS NULL").fetchall()
for a in agents:
    bio = gen_bio(a['role'])
    conn.execute("UPDATE faction_agents SET bio=? WHERE id=?", (bio, a['id']))

conn.commit()
conn.close()
print(f"Generated bios for {len(agents)} agents.")
