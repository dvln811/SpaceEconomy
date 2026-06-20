"""Add category and subcategory columns to commodities table."""
import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "game_data.db")


def categorize(row):
    """Derive category/subcategory from tier and stats."""
    tier = row["tier"]
    stats = json.loads(row["stats"]) if row["stats"] else {}
    name = row["name"]

    if tier == 0:
        return "Trade Goods", ""
    if tier == 1:
        return "Raw Materials", ""
    if tier == 2:
        return "Refined Materials", ""
    if tier == 3:
        return "Manufactured", ""
    if tier == 4:
        return "Components", ""

    # Tier 5: determine from stats
    slot = stats.get("slot", "")
    if slot == "ammo":
        dt = stats.get("damage_type", "")
        if "Plasma" in name:
            return "Ammunition", "Energy Charges"
        elif "Missile" in name or "Torpedo" in name:
            return "Ammunition", "Missiles & Torpedoes"
        else:
            return "Ammunition", "Projectile"
    if slot == "drone":
        return "Drones", ""
    if slot == "engine":
        return "Propulsion", "Engines" if "Engine" in name else "Jump Drives"
    if "mining_yield" in stats or "cycle_time" in stats:
        return "Mining", ""
    if slot == "high" and stats.get("damage_type"):
        # Weapons
        if "Pulse Laser" in name:
            return "Weapons", "Pulse Lasers"
        elif "Beam Laser" in name:
            return "Weapons", "Beam Lasers"
        elif "Railgun" in name:
            return "Weapons", "Railguns"
        elif "Plasma Cannon" in name:
            return "Weapons", "Plasma Cannons"
        elif "Missile" in name:
            return "Weapons", "Missile Launchers"
        elif "Autocannon" in name:
            return "Weapons", "Autocannons"
        return "Weapons", ""
    if slot == "high" and stats.get("mining_yield"):
        return "Mining", ""
    if slot == "high":
        return "Utility", ""
    if slot == "mid":
        if stats.get("shield_hp") or stats.get("regen"):
            return "Defense", "Shields"
        if stats.get("intercept_rate") or stats.get("jam_strength"):
            return "Defense", "Electronic Warfare"
        if stats.get("speed_bonus"):
            if "Afterburner" in name:
                return "Propulsion", "Afterburners"
            return "Propulsion", "Maneuvering"
        if stats.get("scan_range"):
            return "Utility", ""
        return "Defense", ""
    if slot == "low":
        if stats.get("armor_hp") or stats.get("repair_rate"):
            return "Defense", "Armor"
        if stats.get("cargo_bonus"):
            return "Utility", ""
        return "Utility", ""
    if stats.get("mining_yield") is not None:
        return "Mining", ""
    return "Utility", ""


def migrate():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Add columns if they don't exist
    cols = [r[1] for r in conn.execute("PRAGMA table_info(commodities)")]
    if "category" not in cols:
        conn.execute("ALTER TABLE commodities ADD COLUMN category TEXT DEFAULT ''")
    if "subcategory" not in cols:
        conn.execute("ALTER TABLE commodities ADD COLUMN subcategory TEXT DEFAULT ''")

    rows = conn.execute("SELECT * FROM commodities").fetchall()
    for row in rows:
        cat, sub = categorize(row)
        conn.execute("UPDATE commodities SET category=?, subcategory=? WHERE id=?", (cat, sub, row["id"]))

    conn.commit()
    print(f"Updated {len(rows)} commodities with categories")
    # Verify
    for cat in conn.execute("SELECT category, COUNT(*) as c FROM commodities GROUP BY category ORDER BY category"):
        print(f"  {cat[0]}: {cat[1]}")
    conn.close()


if __name__ == "__main__":
    migrate()
