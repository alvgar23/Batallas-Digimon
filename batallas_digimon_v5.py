"""
DIGIMON CARD DUEL V3
-----------------------------------
Player vs COM (AI with 3 difficulty levels)

This script creates an interactive card duel system using the same
combat logic from Tournament Simulator V2. The duel mechanics remain
identical, but now the structure is a turn-based card game.

UPDATED GAME FLOW
-----------------
1. Load Digimon from CSV.
2. Player chooses level (rookie, champion, etc).
3. Initial DRAFT phase:
    - For each of the 5 hand slots:
        * Player sees 3 random cards -> chooses 1.
        * AI sees 3 random cards (logged) -> chooses best of those 3.
4. 5-turn normal round:
    - Player selects a card from their 5-card hand.
    - AI selects a card using selected difficulty mode.
    - Duel is resolved using V2 rules.
    - Win = +1 point, Tie = 0.
5. After 5 turns:
    - Higher score wins.
    - If tied -> SUDDEN DEATH.
6. Sudden Death (DRAFT-based):
    - Each SD round:
        * Player gets 3-card draft -> chooses 1.
        * AI gets 3-card draft (logged) -> chooses best of those 3.
        * One duel is resolved.
    - First non-tie duel decides the whole match.
    - If tie -> repeat with a new 3-card draft.
    - If pool too small -> reset to original level pool.

AI DIFFICULTIES
---------------
NORMAL:
    - Mild intelligence.
    - Picks between top card and random card (50/50).

HARD:
    - Classifies hand into strong/mid/weak.
    - Analyzes player's previous plays.
    - Adjusts strategy.
    - 20% randomness.

IMPOSSIBLE (HYBRID ADAPTIVE):
    - Full card classification.
    - Tracks player tendencies.
    - Predicts openings.
    - Tracks type usage.
    - Mixes logic + 10% chaotic moves.
    - Hard to predict, hard to beat.

LOGGING
-------
All duels and AI draft decisions are logged in detail into:
    duel_logs_v3.txt

Combat mechanics are EXACTLY the same as V2.

Author: Avtomat Agentics
"""


import csv
import random
from collections import defaultdict

# ======================================================
# ===============   LOAD DIGIMON DATA   ================
# ======================================================

def load_digimon(csv_file):
    digimon = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in ["defensa","ataque1","ataque2","fuerza","velocidad","media"]:
                row[k] = int(row[k])
            row["nivel"] = row["nivel"].lower().strip()
            row["tipo"]  = row["tipo"].lower().strip()
            digimon.append(row)
    return digimon


# ======================================================
# =============   LOAD EVOLUTION PATHS   ===============
# ======================================================

def load_evolution_paths(csv_file):
    routes = defaultdict(list)
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rookie = r["rookie"].strip()
            routes[rookie].append({
                "champion": r["champion"].strip() if r["champion"] else None,
                "ultimate": r["ultimate"].strip() if r["ultimate"] else None,
                "mega":     r["mega"].strip()     if r["mega"]     else None
            })
    return routes


# ======================================================
# ==================   HELPERS   =======================
# ======================================================

def find_card_by_name(name, pool):
    for d in pool:
        if d["nombre"].lower() == name.lower():
            return d.copy()
    return None


TYPE_ORDER = {"vaccine": "virus", "virus": "data", "data": "vaccine"}

def apply_type_bonus(a, b):
    a = a.copy()
    b = b.copy()
    if TYPE_ORDER[a["tipo"]] == b["tipo"]:
        for k in ["defensa","ataque1","ataque2","fuerza","velocidad","media"]:
            a[k] += 10
    elif TYPE_ORDER[b["tipo"]] == a["tipo"]:
        for k in ["defensa","ataque1","ataque2","fuerza","velocidad","media"]:
            b[k] += 10
    return a, b


def type_beats(a, b):
    if a["tipo"] == b["tipo"]:
        return False
    return (
        (a["tipo"] == "vaccine" and b["tipo"] == "virus") or
        (a["tipo"] == "virus"   and b["tipo"] == "data")  or
        (a["tipo"] == "data"    and b["tipo"] == "vaccine")
    )


def score_base_stats(a, b):
    pa = pb = 0
    for s in ["defensa","ataque1","ataque2","fuerza","velocidad"]:
        if a[s] > b[s]:
            pa += 1
        elif a[s] < b[s]:
            pb += 1
    return pa, pb


# ======================================================
# ==================   DUEL LOGIC   ====================
# ======================================================

def duel(a, b):
    a, b = apply_type_bonus(a, b)

    # base stats
    pa, pb = score_base_stats(a, b)
    if pa != pb:
        return ("a" if pa > pb else "b"), "Base stats decide"

    # media
    if a["media"] > b["media"]:
        return "a", "Media decides"
    if a["media"] < b["media"]:
        return "b", "Media decides"

    # atq2-def
    d1 = a["ataque2"] - b["defensa"]
    d2 = b["ataque2"] - a["defensa"]
    if d1 != d2:
        return ("a" if d1 > d2 else "b"), "ATQ2-DEF decides"

    # atq1-def
    d1 = a["ataque1"] - b["defensa"]
    d2 = b["ataque1"] - a["defensa"]
    if d1 != d2:
        return ("a" if d1 > d2 else "b"), "ATQ1-DEF decides"

    # type
    if type_beats(a, b): return "a", "Type advantage"
    if type_beats(b, a): return "b", "Type advantage"

    return "tie", "Perfect tie"


# ======================================================
# ================== EVOLUTION ENGINE ==================
# ======================================================

EVOLUTION_BONUS = 5

def apply_evolution_bonus(card, origin_name):
    new = card.copy()
    for k in ["defensa","ataque1","ataque2","fuerza","velocidad","media"]:
        new[k] += EVOLUTION_BONUS
    new["evo_from"] = origin_name
    new["evo_bonus"] = EVOLUTION_BONUS
    return new


def get_available_evolutions(card_name, level, evo_routes):
    if level == "rookie":
        key = "champion"
    elif level == "champion":
        key = "ultimate"
    elif level == "ultimate":
        key = "mega"
    else:
        return []

    res = []
    for r in evo_routes.get(card_name, []):
        nxt = r.get(key)
        if nxt:
            res.append(nxt)
    return res


def evolve_single_card(card, current_level, evo_routes, full_pool):
    name = card["nombre"]
    options = get_available_evolutions(name, current_level, evo_routes)
    if not options:
        return None
    chosen = random.choice(options)
    base = find_card_by_name(chosen, full_pool)
    if not base:
        return None
    return apply_evolution_bonus(base, name)


def evolve_team_after_battle(used, sp, sa, evo_routes, full_pool, level):
    """
    Evolves cards based on match win margin.
    """
    diff = sp - sa
    evo_p = 1 if diff == 1 else 2 if diff == 2 else 3 if diff == 5 else 0
    diff = sa - sp
    evo_ai = 1 if diff == 1 else 2 if diff == 2 else 3 if diff == 5 else 0

    evolved_p = []
    evolved_ai = []

    if evo_p:
        pool = used["player"][:]
        random.shuffle(pool)
        for _ in range(evo_p):
            if not pool: break
            c = pool.pop()
            e = evolve_single_card(c, level, evo_routes, full_pool)
            if e: evolved_p.append(e)

    if evo_ai:
        pool = used["ai"][:]
        random.shuffle(pool)
        for _ in range(evo_ai):
            if not pool: break
            c = pool.pop()
            e = evolve_single_card(c, level, evo_routes, full_pool)
            if e: evolved_ai.append(e)

    return evolved_p, evolved_ai


# ======================================================
# ================== DISPLAY HELPERS ===================
# ======================================================

def card_text(c):
    base = (
        f"{c['nombre']} | DEF {c['defensa']} | ATQ1 {c['ataque1']} | "
        f"ATQ2 {c['ataque2']} | STR {c['fuerza']} | SPD {c['velocidad']} | "
        f"MEDIA {c['media']} | TYPE {c['tipo']}"
    )
    if "evo_from" in c:
        base += f"  [EVO+{c['evo_bonus']} from {c['evo_from']}]"
    return base


def show_hand(hand):
    print("\nYour hand:")
    for i, c in enumerate(hand, 1):
        print(f"{i}. {card_text(c)}")


def player_choose_card(hand):
    while True:
        show_hand(hand)
        x = input("Choose card: ").strip()
        if x.isdigit():
            x = int(x)
            if 1 <= x <= len(hand):
                return hand.pop(x-1)
        print("Invalid choice.")


# ======================================================
# ====================== AI LOGIC ======================
# ======================================================

def weighted_score(c):
    return (
        1.5 * c["ataque2"] +
        1.3 * c["ataque1"] +
        c["velocidad"] +
        c["fuerza"] +
        0.8 * c["defensa"] +
        0.6 * c["media"]
    )


def classify_strength(hand):
    scored = [(weighted_score(c), c) for c in hand]
    scored.sort(reverse=True)
    return scored


def ai_choose_card(hand, difficulty, hist, ai_log, turn, mode):
    scored = classify_strength(hand)
    top = scored[0][1]
    mid = scored[len(scored)//2][1]
    low = scored[-1][1]

    if difficulty != 3:
        choice = top
    else:
        # modes
        if mode == "aggressive":
            choice = top if random.random() < 0.75 else mid
        elif mode == "conservative":
            choice = low if turn < 4 else top
        elif mode == "human":
            r = random.random()
            if r < 0.2: choice = low
            elif r < 0.6: choice = mid
            else: choice = top
        elif mode == "opportunistic":
            if hist:
                p = hist[-1]
                pwr = p["ataque2"] + p["fuerza"] + p["velocidad"]
            else:
                pwr = 0
            choice = mid if pwr > weighted_score(top)*0.9 else top
        elif mode == "chaotic":
            choice = random.choice(hand)
        else:
            choice = mid

    hand.remove(choice)
    ai_log.append(f"AI -> {choice['nombre']}")
    return choice


# ======================================================
# ===================== PLAY ROUND =====================
# ======================================================

def play_round(player_hand, ai_hand, difficulty, log):
    score_p = 0
    score_ai = 0
    hist = []
    ai_mode = None

    for turn in range(1, 6):
        log.append(f"Turn {turn}")

        p = player_choose_card(player_hand)
        hist.append(p)
        log.append(f"Player plays {p['nombre']}")

        if ai_mode is None and difficulty == 3:
            ai_mode = random.choice(["aggressive","conservative","human","opportunistic","chaotic"])
            log.append(f"[AI MODE] {ai_mode}")

        ai_log = []
        a = ai_choose_card(ai_hand, difficulty, hist, ai_log, turn, ai_mode)
        for L in ai_log:
            log.append(L)

        log.append(f"AI plays {a['nombre']}")

        res, reason = duel(p, a)
        log.append(reason)

        if res == "a": score_p += 1
        elif res == "b": score_ai += 1

    return score_p, score_ai, hist

# ======================================================
# ===================== DRAFT SYSTEM ===================
# ======================================================

DRAFT_STYLES = ["attack","speed","physical","general","type"]

def pick_draft_style():
    print("\nChoose DRAFT style:")
    for i, s in enumerate(DRAFT_STYLES, 1):
        print(f"{i}. {s}")
    while True:
        x = input("Style: ").strip()
        if x.isdigit() and 1 <= int(x) <= len(DRAFT_STYLES):
            return DRAFT_STYLES[int(x)-1]
        print("Invalid.")

def display_card_by_style(c, style):
    if style == "attack":
        return f"{c['nombre']} | ATQ1 {c['ataque1']} | ATQ2 {c['ataque2']}"
    if style == "speed":
        return f"{c['nombre']} | SPD {c['velocidad']}"
    if style == "physical":
        return f"{c['nombre']} | DEF {c['defensa']} | STR {c['fuerza']}"
    if style == "general":
        return f"{c['nombre']} | MEDIA {c['media']}"
    if style == "type":
        return f"{c['nombre']} | TYPE {c['tipo']}"
    return c["nombre"]

def score_card_for_style(c, style):
    if style == "attack":   return c["ataque1"] + c["ataque2"]
    if style == "speed":    return c["velocidad"]
    if style == "physical": return c["defensa"] + c["fuerza"]
    if style == "general":  return c["media"]
    if style == "type":
        order = {"vaccine":3, "virus":2, "data":1}
        return order.get(c["tipo"], 0)
    return 0

def draft_pick_player(pool, style):
    """Player selects 1 of 3."""
    if len(pool) < 3:
        opts = pool[:]
    else:
        opts = random.sample(pool, 3)

    print("\n=== PLAYER DRAFT ===")
    for i, c in enumerate(opts, 1):
        print(f"{i}. {display_card_by_style(c, style)}")

    while True:
        x = input("Choose (1-3): ").strip()
        if x.isdigit() and 1 <= int(x) <= len(opts):
            chosen = opts[int(x)-1]
            break
        print("Invalid.")

    pool.remove(chosen)
    return chosen

# ---------------- AI draft ----------------

def ai_pick_type_behavior():
    return random.choice(["balanced","specialized","cyclic","natural"])

def ai_type_decision(options, behavior, mem):
    if behavior == "balanced":
        count = mem["count"]
        least = min(count, key=lambda t: count[t])
        candidates = [c for c in options if c["tipo"] == least]
        return random.choice(candidates) if candidates else random.choice(options)

    if behavior == "specialized":
        if mem["spec"] is None:
            mem["spec"] = options[0]["tipo"]
        t = mem["spec"]
        candidates = [c for c in options if c["tipo"] == t]
        return random.choice(candidates) if candidates else random.choice(options)

    if behavior == "cyclic":
        seq = ["vaccine","virus","data"]
        t = seq[mem["pos"]]
        mem["pos"] = (mem["pos"] + 1) % 3
        for c in options:
            if c["tipo"] == t:
                return c
        return random.choice(options)

    if behavior == "natural":
        freq = defaultdict(int)
        for c in options:
            freq[c["tipo"]] += 1
        most = max(freq, key=lambda x: freq[x])
        counter = TYPE_ORDER[most]
        candidates = [c for c in options if c["tipo"] == counter]
        return random.choice(candidates) if candidates else random.choice(options)

    return random.choice(options)

def draft_pick_ai(pool, style, log, slot, behavior, mem):
    """AI picks 1 of 3."""
    if len(pool) < 3:
        opts = pool[:]
    else:
        opts = random.sample(pool, 3)

    shown = [display_card_by_style(c, style) for c in opts]

    if style == "type":
        choice = ai_type_decision(opts, behavior, mem)
    else:
        scored = sorted(opts, key=lambda c: score_card_for_style(c, style), reverse=True)
        choice = scored[0]

    pool.remove(choice)
    mem["count"][choice["tipo"]] += 1

    log.append(f"[AI DRAFT] Slot {slot} | {shown} → {choice['nombre']}")
    return choice

# ------------- Build draft hands -------------

def draft_build_hands(pool, log, p_style, ai_style):
    behavior = ai_pick_type_behavior()
    mem = {"count": defaultdict(int), "spec": None, "pos": 0}

    hand_p = []
    hand_ai = []

    for slot in range(1, 6):
        chosen_p = draft_pick_player(pool, p_style)
        hand_p.append(chosen_p)

        chosen_ai = draft_pick_ai(pool, ai_style, log, slot, behavior, mem)
        hand_ai.append(chosen_ai)

    return hand_p, hand_ai, pool


# ======================================================
# ===================== MATCH SYSTEM ===================
# ======================================================

def ai_select_final_five(pool):
    pool_copy = pool[:]
    return random.sample(pool_copy, 5)

def play_match_no_draft(p_hand, ai_hand, difficulty, log):
    log.append("\n=== MATCH (NO DRAFT) ===")
    p = [c.copy() for c in p_hand]
    a = [c.copy() for c in ai_hand]

    sp, sa, hist = play_round(p, a, difficulty, log)
    ai_used = [c for c in ai_hand if c not in a]

    return sp, sa, {"player": hist, "ai": ai_used}


def play_match_with_draft(pool, difficulty, log):
    log.append("\n=== MATCH (WITH DRAFT) ===")

    p_style = pick_draft_style()
    ai_style = random.choice(DRAFT_STYLES)
    log.append(f"[DRAFT STYLES] Player={p_style} | AI={ai_style}")

    pool_copy = pool[:]
    hand_p, hand_ai, _ = draft_build_hands(pool_copy, log, p_style, ai_style)

    p = [c.copy() for c in hand_p]
    a = [c.copy() for c in hand_ai]

    sp, sa, hist = play_round(p, a, difficulty, log)
    ai_used = [c for c in hand_ai if c not in a]

    return sp, sa, {"player": hist, "ai": ai_used}


# ======================================================
# ================== TOURNAMENT LOGIC ==================
# ======================================================

TOURNAMENT_LEVELS = ["rookie","champion","ultimate","mega"]

def tournament_run(all_digimon, evo_routes, difficulty, log):
    total_p = 0
    total_ai = 0

    carry = {
        "champion": {"p":[], "ai":[]},
        "ultimate": {"p":[], "ai":[]},
        "mega":     {"p":[], "ai":[]}
    }

    for level in TOURNAMENT_LEVELS:
        log.append(f"\n\n==== LEVEL {level.upper()} ====")

        base_pool = [d.copy() for d in all_digimon if d["nivel"] == level]
        extra_p = carry[level]["p"] if level in carry else []
        extra_ai = carry[level]["ai"] if level in carry else []

        seed_p = base_pool[:] + [c.copy() for c in extra_p]
        seed_ai = base_pool[:] + [c.copy() for c in extra_ai]

        for battle in range(1, 3):
            log.append(f"\n--- {level.upper()} BATTLE {battle} ---")
            use_draft = (battle == 2)

            if not use_draft:
                final_p = random.sample(seed_p, 5)
                final_ai = ai_select_final_five(seed_ai)
                sp, sa, used = play_match_no_draft(final_p, final_ai, difficulty, log)
            else:
                pool = seed_p + seed_ai
                sp, sa, used = play_match_with_draft(pool, difficulty, log)

            total_p += sp
            total_ai += sa

            log.append(f"[RESULT] Player {sp} – AI {sa}")

            # Evolutions except mega
            if level != "mega":
                evo_p, evo_ai = evolve_team_after_battle(
                    used, sp, sa, evo_routes, all_digimon, level
                )

                for c in evo_p:
                    c["nombre"] = f"{c['nombre']} (EVO+{c['evo_bonus']} from {c['evo_from']})"
                for c in evo_ai:
                    c["nombre"] = f"{c['nombre']} (EVO+{c['evo_bonus']} from {c['evo_from']})"

                if evo_p:
                    log.append("Player evolves: " + ", ".join([c["nombre"] for c in evo_p]))
                if evo_ai:
                    log.append("AI evolves: " + ", ".join([c["nombre"] for c in evo_ai]))

                if level == "rookie":
                    carry["champion"]["p"].extend(evo_p)
                    carry["champion"]["ai"].extend(evo_ai)
                elif level == "champion":
                    carry["ultimate"]["p"].extend(evo_p)
                    carry["ultimate"]["ai"].extend(evo_ai)
                elif level == "ultimate":
                    carry["mega"]["p"].extend(evo_p)
                    carry["mega"]["ai"].extend(evo_ai)

    # END
    print("\n===== FINAL SCORE =====")
    print(f"PLAYER {total_p} | AI {total_ai}")
    log.append("\n===== FINAL SCORE =====")
    log.append(f"PLAYER {total_p} | AI {total_ai}")

    if total_p > total_ai:
        print("PLAYER WINS")
    elif total_ai > total_p:
        print("AI WINS")
    else:
        print("DRAW")


# ======================================================
# ========================= MAIN =======================
# ======================================================

def run_game_v5():
    print("Loading Digimon data...")
    all_digimon = load_digimon("datos_digimon_todos.csv")

    print("Loading evolution paths...")
    evo_routes = load_evolution_paths("linea_evolutiva.csv")

    print("\nDifficulty:")
    print("1. Normal")
    print("2. Hard")
    print("3. Impossible")

    while True:
        x = input("Difficulty: ").strip()
        if x in ["1","2","3"]:
            difficulty = int(x)
            break
        print("Invalid.")

    log = []
    log.append("=== DIGIMON CARD DUEL V5 ===")
    log.append(f"Difficulty={difficulty}")

    tournament_run(all_digimon, evo_routes, difficulty, log)

    with open("duel_logs_v5.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))

    print("Log saved to duel_logs_v5.txt")


if __name__ == "__main__":
    run_game_v5()