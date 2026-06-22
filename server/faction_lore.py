"""Add faction histories and agent bios to the database."""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")

FACTION_HISTORIES = {
    'terran_fed': """The Terran Federation was born from the ashes of the Colonial Compact, a loose alliance of human settlements that collapsed during the Isolation Wars 200 years ago. When the jump gate network destabilized, cutting off dozens of systems for decades, the core worlds banded together under martial law to prevent total collapse. Admiral Kenji Sato unified the remaining navy into a peacekeeping force, establishing the Federation Senate to govern through law rather than warlord rule. Today, the Federation is the largest organized power, controlling the most developed core systems. Their navy is the best equipped and trained, but their bureaucracy is slow and their reach into the frontier is limited. They believe in order through institutions, regulated trade, and collective defense. Critics call them authoritarian; supporters call them civilization's last line.""",

    'science_collective': """The Nexus Collective emerged from the Arcturus Research Initiative, a pre-war consortium of universities and research stations that pooled resources to survive the Isolation. While other factions fought over territory, the scientists on Arcturus Station focused on understanding the jump gate network, developing new propulsion technologies, and preserving humanity's knowledge base. When gates stabilized, they emerged with technological advantages decades ahead of their neighbors. Led by a council of senior researchers, the Collective values knowledge above territory. They expand not through conquest but through establishing research outposts and offering technological partnerships. Their military is small but advanced, their ships faster and harder to detect. They are allied with the Federation by necessity but trust no one fully.""",

    'merchants_guild': """The Merchants Guild predates the Isolation Wars, originally a mutual insurance cooperative among independent traders. When the gates fell, the Guild's distributed network of trade posts became lifelines for cut-off colonies. Captains who maintained routes through dangerous space became legends, and the Guild's influence grew proportionally. After reconnection, the Guild reorganized as a trade oligarchy, with the wealthiest merchant families forming the Trade Council. They control the most profitable trade routes, the largest fleet of haulers, and maintain neutrality in most conflicts to preserve commerce. The Guild believes money is power, and access to markets is the ultimate leverage. They will trade with anyone, including the Corsairs, earning them distrust from the Federation.""",

    'free_states': """The Frontier Alliance is the youngest faction, formed only 40 years ago when rim colonies rejected both Federation taxation and Guild monopoly pricing. Led by charismatic miners and frontier captains, the Alliance is a loose confederation of self-governing systems that share mutual defense pacts but jealously guard their independence. They have no standing navy, instead relying on militia fleets that muster when threatened. Their economy is resource-rich but underdeveloped, exporting raw materials and importing finished goods. The Alliance's strength is their people: fiercely loyal, self-reliant, and willing to fight for their freedom. Their weakness is coordination. Getting five Alliance governors to agree on anything takes longer than the problem takes to solve itself.""",

    'iron_compact': """The Iron Compact began as the Krovost Mining Consortium, a corporate military operation that seized control of mineral-rich frontier systems during the chaos of reconnection. Marshal Yuri Krov, a former Federation officer turned mercenary, welded together a coalition of private military companies, mining corporations, and displaced colonists into a single militarized state. The Compact believes in strength through industry: every citizen serves, every factory produces for the war machine, every resource feeds the fleet. They are the most aggressive faction, openly expansionist, and view the unclaimed systems between them and the Alliance as their birthright. Their military doctrine emphasizes overwhelming force and rapid conquest. Internal politics are brutal: promotion comes through competence or removal of rivals.""",

    'corsairs': """The Corsairs are not a faction in the traditional sense but a loose confederation of pirate fleets, smuggling rings, and outlaw stations that operate in the spaces between civilized powers. They have no unified government, no territory they openly claim, and no standing treaties. The current "Pirate King" holds power only as long as they remain the most dangerous and profitable leader available. Corsair culture glorifies cunning, boldness, and plunder. They raid trade routes, sell stolen goods through black markets, and offer "protection" to frontier settlements. Some Corsairs are desperate refugees; others are ideological anarchists who view the major factions as oppressive regimes. The Federation and Guild consider them terrorists. The Alliance considers them a nuisance but occasionally useful.""",
}

# Bio template components for agent generation
BIO_TEMPLATES = {
    'leader': {
        'terran_fed': [
            "Rose through the Senate ranks during the Outer Rim Crisis. Known for measured responses and political acumen. Carries the weight of maintaining order across hundreds of systems.",
            "Former navy flag officer turned politician. Believes the Federation's survival depends on strong institutions, not strong men. Has made enemies in the military establishment by cutting budgets.",
            "A compromise candidate who united the Senate's hawkish and dovish wings. Privately fears the Federation is overextended but publicly projects confidence.",
        ],
        'science_collective': [
            "The youngest Archon in Collective history, elected after publishing breakthrough research on jump gate harmonics. Sees the galaxy as a puzzle to be solved, not conquered.",
            "A former xenoarchaeologist who discovered Precursor artifacts in the Deep Void. Believes humanity's future lies in understanding the galaxy's deeper mysteries, not in territorial squabbles.",
            "Third-generation Collective citizen. Raised on Arcturus Station, educated in quantum mechanics and game theory. Applies mathematical models to governance with unsettling precision.",
        ],
        'merchants_guild': [
            "Built a shipping empire from a single freighter inherited at age 19. Ruthless in business but famously generous to loyal employees. Owns stakes in 200+ stations.",
            "Former pirate turned legitimate. Bought their way into the Trade Council with wealth accumulated through 'creative logistics' during the border conflicts. No one asks where the money came from.",
            "Born into Guild aristocracy. Has never touched a cargo manifest personally but can recite profit margins for every trade route from memory. Views the galaxy purely in terms of supply and demand.",
        ],
        'iron_compact': [
            "Seized power in a bloodless coup after the previous Marshal's failed offensive against the Alliance. Promises victory through industrial superiority rather than reckless attacks.",
            "A veteran of 30 campaigns. Every scar tells a story, every story ends with their enemy dead. Believes the Compact's destiny is to unite humanity under one iron banner.",
            "Rose from factory floor to supreme command in 15 years. Understands that armies march on logistics, not slogans. Currently rebuilding the Compact's depleted fleet at unprecedented speed.",
        ],
        'free_states': [
            "A former miner who led the Rockfall Uprising, where three Alliance systems expelled Guild-backed governors. Elected on a platform of 'no taxes, no masters, no compromise.'",
            "Reluctant leader who keeps getting re-elected because no one else is trusted. Would rather be running their farm but recognizes that without unity, the Alliance will be devoured.",
            "A charismatic orator who can convince five feuding governors to cooperate. For about a week. Then everything falls apart and they have to do it again.",
        ],
        'corsairs': [
            "Killed the previous Pirate King in single combat over a disputed cargo haul. Rules through fear, charisma, and the simple fact that they're the best pilot in the fleet.",
            "A former Federation intelligence operative gone rogue. Uses their training to run the most efficient raiding operation in the sector. The Federation wants them dead more than anyone.",
            "Nobody knows their real name or origin. Appeared five years ago with a stolen dreadnought and a crew of fanatics. Conquered the previous leadership through sheer audacity.",
        ],
    },
    'admiral': [
        "A decorated fleet commander with {battles} engagements under their belt. Known for {style} tactics that {outcome}.",
        "Former merchant captain who switched to military service after pirates destroyed their convoy. Brings unconventional thinking to fleet doctrine.",
        "Academy graduate, top of their class. Textbook brilliant but sometimes rigid. The crew respects competence; allies wonder if they can improvise under pressure.",
        "Self-taught tactician from the frontier. Learned warfare by surviving it. No formal training but an instinct for positioning that formal officers envy.",
    ],
    'governor': [
        "Administers their territory with {style}. The citizens are {outcome}, and the economy {econ}.",
        "A former logistics officer who sees governance as a supply chain problem. Infrastructure projects always on time. Social programs underfunded.",
        "Populist governor who maintains power through public approval. Spends heavily on services. The budget is a constant crisis.",
        "Efficient bureaucrat who maximizes output from every system under their control. Not beloved, but respected. The stations run on time.",
    ],
    'general': [
        "Ground forces commander who believes wars are won in the dirt, not in orbit. Advocates for marine boarding actions and station assaults.",
        "Defensive specialist. Their fortifications are legendary. Enemies have learned that attacking a system they've prepared is extremely costly.",
        "Former special operations officer. Prefers precision strikes and unconventional warfare over fleet engagements.",
    ],
    'director': [
        "Manages the faction's economic machinery with ruthless efficiency. Every credit is tracked, every waste is eliminated.",
        "A pragmatist who maintains trade relationships even with nominal enemies. Believes commerce prevents wars. Or at least profitable ones.",
        "Logistics genius who can supply a fleet across 50 systems without a single shipment going missing. Boring at parties but indispensable in war.",
    ],
    'spymaster': [
        "Operates a network of informants across every major faction. Knows secrets that would topple governments. Uses them sparingly, for maximum leverage.",
        "Former counter-intelligence specialist. Paranoid by training, effective by nature. Trusts no one, which is why everyone trusts them with secrets.",
        "A ghost. Even faction leadership doesn't know their real face. Communications arrive through dead drops and encrypted channels.",
    ],
}


def generate_bio(faction_id, role):
    """Generate a contextual bio for an agent."""
    import random
    if role == 'leader' and faction_id in BIO_TEMPLATES.get('leader', {}):
        return random.choice(BIO_TEMPLATES['leader'][faction_id])
    elif role in BIO_TEMPLATES:
        templates = BIO_TEMPLATES[role]
        bio = random.choice(templates)
        # Fill in template variables
        styles = ['aggressive', 'cautious', 'methodical', 'unpredictable', 'patient']
        outcomes = ['feared', 'respected', 'tolerated', 'beloved', 'effective']
        econs = ['grows steadily', 'booms but is volatile', 'is stable but stagnant', 'thrives under good management']
        bio = bio.replace('{battles}', str(random.randint(5, 40)))
        bio = bio.replace('{style}', random.choice(styles))
        bio = bio.replace('{outcome}', random.choice(outcomes))
        bio = bio.replace('{econ}', random.choice(econs))
        return bio
    return ""


def apply():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Add backstory columns
    for table, col in [('factions', 'history'), ('faction_agents', 'bio')]:
        cols = [r[1] for r in conn.execute(f'PRAGMA table_info({table})')]
        if col not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT ''")

    # Set faction histories
    for fid, history in FACTION_HISTORIES.items():
        conn.execute("UPDATE factions SET history=? WHERE id=?", (history, fid))

    # Generate bios for current agents
    agents = conn.execute("SELECT id, faction_id, role FROM faction_agents").fetchall()
    import random
    for a in agents:
        bio = generate_bio(a['faction_id'], a['role'])
        conn.execute("UPDATE faction_agents SET bio=? WHERE id=?", (bio, a['id']))

    conn.commit()

    # Report
    print("Faction histories set:")
    for r in conn.execute("SELECT id, LENGTH(history) as len FROM factions"):
        print(f"  {r['id']}: {r['len']} chars")
    print("\nAgent bios set:")
    for r in conn.execute("SELECT name, role, LENGTH(bio) as len FROM faction_agents ORDER BY faction_id LIMIT 10"):
        print(f"  {r['name']} ({r['role']}): {r['len']} chars")

    conn.close()


if __name__ == '__main__':
    apply()
