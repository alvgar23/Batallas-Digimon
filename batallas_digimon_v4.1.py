"""
DIGIMON CARD DUEL V4.1
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
# ===============   LOAD DIGIMON   =====================
# ======================================================

def load_digimon(csv_file):
    digimon = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["defensa"]   = int(row["defensa"])
            row["ataque1"]   = int(row["ataque1"])
            row["ataque2"]   = int(row["ataque2"])
            row["fuerza"]    = int(row["fuerza"])
            row["velocidad"] = int(row["velocidad"])
            row["media"]     = int(row["media"])
            row["nivel"] = row["nivel"].lower().strip()
            row["tipo"]  = row["tipo"].lower().strip()
            digimon.append(row)
    return digimon


# ======================================================
# =============== TYPE BONUS +10 =======================
# ======================================================

TYPE_ORDER = {
    "vaccine": "virus",
    "virus":   "data",
    "data":    "vaccine"
}

def apply_type_bonus(a, b):
    a2 = a.copy()
    b2 = b.copy()

    if TYPE_ORDER[a2["tipo"]] == b2["tipo"]:
        for k in ["defensa","ataque1","ataque2","fuerza","velocidad","media"]:
            a2[k] += 10
    elif TYPE_ORDER[b2["tipo"]] == a2["tipo"]:
        for k in ["defensa","ataque1","ataque2","fuerza","velocidad","media"]:
            b2[k] += 10

    return a2, b2


# ======================================================
# ==================    DUEL LOGIC   ===================
# ======================================================

def type_beats(a, b):
    ta = a["tipo"]
    tb = b["tipo"]
    if ta == tb:
        return False
    return (
        (ta=="vaccine" and tb=="virus") or
        (ta=="virus"   and tb=="data")  or
        (ta=="data"    and tb=="vaccine")
    )

def score_base_stats(a, b):
    fields = ["defensa","ataque1","ataque2","fuerza","velocidad"]
    pa = pb = 0
    for s in fields:
        if a[s] > b[s]: pa += 1
        elif a[s] < b[s]: pb += 1
    return pa, pb

def diff_atq2_def(a, b): return a["ataque2"] - b["defensa"]
def diff_atq1_def(a, b): return a["ataque1"] - b["defensa"]

def duel(a, b, final_round=False):
    a, b = apply_type_bonus(a, b)

    log = []

    pa, pb = score_base_stats(a, b)
    log.append(f"Base stats: {pa}-{pb}")
    if pa != pb:
        log.append(f"Winner by base stats: {a['nombre'] if pa>pb else b['nombre']}")
        return ("a" if pa>pb else "b"), "\n".join(log)

    if a["media"] > b["media"]:
        log.append(f"Media win: {a['nombre']}")
        return "a", "\n".join(log)
    elif a["media"] < b["media"]:
        log.append(f"Media win: {b['nombre']}")
        return "b", "\n".join(log)
    log.append("Media tie")

    d1 = diff_atq2_def(a,b)
    d2 = diff_atq2_def(b,a)
    if d1!=d2:
        log.append(f"ATQ2-DEF win: {a['nombre'] if d1>d2 else b['nombre']}")
        return ("a" if d1>d2 else "b"), "\n".join(log)
    log.append("ATQ2-DEF tie")

    d1 = diff_atq1_def(a,b)
    d2 = diff_atq1_def(b,a)
    if d1!=d2:
        log.append(f"ATQ1-DEF win: {a['nombre'] if d1>d2 else b['nombre']}")
        return ("a" if d1>d2 else "b"), "\n".join(log)
    log.append("ATQ1-DEF tie")

    if type_beats(a,b):
        log.append(f"Type win: {a['nombre']}")
        return "a", "\n".join(log)
    if type_beats(b,a):
        log.append(f"Type win: {b['nombre']}")
        return "b", "\n".join(log)

    log.append("Ultra tie")
    return "tie", "\n".join(log)


# ======================================================
# ==================  AI SCORING   =====================
# ======================================================

def weighted_score(d):
    return (
        1.5*d["ataque2"] +
        1.3*d["ataque1"] +
        d["velocidad"] +
        d["fuerza"] +
        0.8*d["defensa"] +
        0.6*d["media"]
    )

def classify_by_strength(hand):
    scored = [(weighted_score(x), x) for x in hand]
    scored.sort(reverse=True, key=lambda t:t[0])
    n = len(scored)
    c1 = n//3
    c2 = (2*n)//3
    strong = [x for _,x in scored[:c1]]
    mid    = [x for _,x in scored[c1:c2]]
    weak   = [x for _,x in scored[c2:]]
    return {"strong":strong, "mid":mid, "weak":weak}, scored

# ======================================================
# ================== DRAFT STYLES  =====================
# ======================================================

DRAFT_STYLES = ["attack","speed","physical","general","type","random"]

def pick_draft_style():
    print("\nChoose DRAFT style:")
    for i,s in enumerate(DRAFT_STYLES,1):
        print(f"{i}. {s}")
    c = int(input("Style: "))
    style = DRAFT_STYLES[c-1]
    if style=="random":
        style = random.choice(DRAFT_STYLES[:-1])
    return style

def ai_pick_draft_style():
    return random.choice(DRAFT_STYLES[:-1])


# ======================================================
# ===== AI TYPE SUB-BEHAVIORS (ONLY IF STYLE=type) =====
# ======================================================

def ai_pick_type_behavior():
    return random.choice(["balanced","specialized","cyclic","natural"])


def ai_pick_by_type_behavior(options, behavior, ai_memory):
    types = ["vaccine","virus","data"]

    # ---------- 1. BALANCED ----------
    if behavior == "balanced":
        count = ai_memory["type_count"]
        target = min(count, key=lambda t: count[t])
        cands = [c for c in options if c["tipo"] == target]
        return random.choice(cands) if cands else random.choice(options)

    # ---------- 2. SPECIALIZED ----------
    if behavior == "specialized":
        if ai_memory["spec_type"] is None:
            ai_memory["spec_type"] = options[0]["tipo"]
        target = ai_memory["spec_type"]
        cands = [c for c in options if c["tipo"] == target]
        return random.choice(cands) if cands else random.choice(options)

    # ---------- 3. CYCLIC ----------
    if behavior == "cyclic":
        seq = ["vaccine","virus","data"]
        t = seq[ai_memory["cycle_pos"]]
        ai_memory["cycle_pos"] = (ai_memory["cycle_pos"] + 1) % 3
        for c in options:
            if c["tipo"] == t:
                return c
        return random.choice(options)

    # ---------- 4. NATURAL ----------
    if behavior == "natural":
        counts = defaultdict(int)
        for c in options:
            counts[c["tipo"]] += 1
        common = max(counts, key=lambda t: counts[t])
        target = TYPE_ORDER[common]
        cands = [c for c in options if c["tipo"] == target]
        return random.choice(cands) if cands else random.choice(options)

    return random.choice(options)


# ======================================================
# ==========  DISPLAY & SCORE BY STYLE  =================
# ======================================================

def display_card_by_style(card, style):
    if style=="attack":
        return f"{card['nombre']} | ATQ1 {card['ataque1']} | ATQ2 {card['ataque2']}"
    if style=="speed":
        return f"{card['nombre']} | SPD {card['velocidad']}"
    if style=="physical":
        return f"{card['nombre']} | DEF {card['defensa']} | STR {card['fuerza']}"
    if style=="general":
        return f"{card['nombre']} | MEDIA {card['media']}"
    if style=="type":
        return f"{card['nombre']} | TYPE {card['tipo']}"
    return card["nombre"]

def score_by_style(card, style):
    if style=="attack":   return card["ataque1"] + card["ataque2"]
    if style=="speed":    return card["velocidad"]
    if style=="physical": return card["defensa"] + card["fuerza"]
    if style=="general":  return card["media"]
    if style=="type":
        order={"vaccine":3,"virus":2,"data":1}
        return order.get(card["tipo"],0)
    return 0


# ======================================================
# ==================  DRAFT SYSTEM  ====================
# ======================================================

def draft_one_card(pool, style):
    options = random.sample(pool, 3)
    print("\n=== DRAFT FOR CARD ===")
    for i,c in enumerate(options,1):
        print(f"{i}. {display_card_by_style(c, style)}")
    pick = int(input("Choose (1-3): "))
    chosen = options[pick-1]
    pool.remove(chosen)
    return chosen, pool


def ai_draft_card(pool, style, log, slot_num, ai_type_behavior, ai_memory):
    options = random.sample(pool, 3)
    shown = [display_card_by_style(c, style) for c in options]

    if style == "type":
        choice = ai_pick_by_type_behavior(options, ai_type_behavior, ai_memory)
    else:
        scored = [(score_by_style(c, style), c) for c in options]
        scored.sort(reverse=True, key=lambda t:t[0])
        choice = scored[0][1]

    pool.remove(choice)

    log.append(
        f"[DRAFT AI] Slot {slot_num}: style={style}, behavior={ai_type_behavior} | options={shown} -> {choice['nombre']}"
    )

    ai_memory["type_count"][choice["tipo"]] += 1
    return choice


def draft_initial_hands(pool, log, picks, player_style, ai_style):
    player = []
    ai = []

    ai_type_behavior = ai_pick_type_behavior() if ai_style == "type" else None

    ai_memory = {
        "type_count": {"vaccine":0, "virus":0, "data":0},
        "spec_type": None,
        "cycle_pos": 0
    }

    for slot in range(1, picks+1):

        chosen, pool = draft_one_card(pool, player_style)
        player.append(chosen)
        log.append(f"[DRAFT PLAYER] Slot {slot}: {chosen['nombre']} (style={player_style})")

        ai_card = ai_draft_card(pool, ai_style, log, slot, ai_type_behavior, ai_memory)
        ai.append(ai_card)

    return player, ai, pool

# ======================================================
# =================  PLAYER TURN PICK  =================
# ======================================================

def show_hand(hand):
    print("\nYour hand:")
    for i,d in enumerate(hand,1):
        print(
            f"{i}. {d['nombre']} | DEF {d['defensa']} | ATQ1 {d['ataque1']} | "
            f"ATQ2 {d['ataque2']} | STR {d['fuerza']} | SPD {d['velocidad']} | "
            f"MEDIA {d['media']} | TYPE {d['tipo']}"
        )

def player_choose_card(hand):
    while True:
        show_hand(hand)
        c = input("Choose your card: ")
        if c.isdigit():
            c = int(c)
            if 1 <= c <= len(hand):
                return hand.pop(c-1)
        print("Invalid.")


# ======================================================
# ================== AI TURN PICK  =====================
# ======================================================

def ai_choose_card(hand, difficulty, player_history, ai_log, turn, mode):

    classified, scored = classify_by_strength(hand)
    ai_log.append(f"[AI] Hand classified: {[(d['nombre'], s) for s, d in scored]}")

    scored_sorted = sorted(scored, key=lambda t: t[0], reverse=True)
    top = scored_sorted[0][1]
    mid = scored_sorted[len(scored_sorted)//2][1]
    low = scored_sorted[-1][1]

    if difficulty != 3:
        choice = top
    else:
        if mode == "aggressive":
            choice = (
                top if random.random() < 0.75
                else mid if random.random() < 0.7
                else low
            )

        elif mode == "conservative":
            choice = (
                low if turn < 4 and random.random() < 0.7
                else mid if turn < 4
                else top
            )

        elif mode == "human":
            r = random.random()
            if turn == 1:
                choice = mid
            elif r < 0.2:
                choice = low
            elif r < 0.6:
                choice = mid
            else:
                choice = top
            if random.random() < 0.12:
                choice = random.choice([x for _, x in scored])

        elif mode == "opportunistic":
            if len(player_history) >= 1:
                p = player_history[-1]
                pwr = p["ataque2"] + p["fuerza"] + p["velocidad"]
            else:
                pwr = 0
            choice = mid if pwr > weighted_score(top)*0.9 else top
            if random.random() < 0.15:
                cand = [x for s, x in scored if s >= scored_sorted[0][0]*0.9]
                if cand:
                    choice = random.choice(cand)

        elif mode == "chaotic":
            choice = (
                random.choice(hand) if random.random() < 0.4
                else mid if random.random() < 0.5
                else top
            )

        else:
            choice = mid

    hand.remove(choice)
    ai_log.append(f"[AI] Personality='{mode}' chose: {choice['nombre']}")
    return choice


# ======================================================
# ==================== ROUND LOGIC =====================
# ======================================================

def play_round(player_hand, ai_hand, difficulty, log):
    score_p = 0
    score_ai = 0
    hist = []

    ai_mode = None

    for turn in range(1, 6):
        log.append(f"\n===== TURN {turn} =====")

        p_card = player_choose_card(player_hand)
        log.append(f"Player chose: {p_card['nombre']}")
        hist.append(p_card)

        if ai_mode is None and difficulty == 3:
            ai_mode = random.choice(
                ["aggressive", "opportunistic", "human", "conservative", "chaotic"]
            )
            log.append(f"[AI MODE SELECTED]: {ai_mode}")

        ai_log = []
        a_card = ai_choose_card(ai_hand, difficulty, hist, ai_log, turn, ai_mode)
        for l in ai_log:
            log.append(l)
        log.append(f"AI chose: {a_card['nombre']}")

        res, txt = duel(p_card, a_card)
        log.append(txt)

        if res == "a":
            score_p += 1
            log.append("-> Player wins")
        elif res == "b":
            score_ai += 1
            log.append("-> AI wins")
        else:
            log.append("-> Tie")

    return score_p, score_ai, hist


# ======================================================
# ================== SUDDEN DEATH ======================
# ======================================================

def sudden_death(pool, difficulty, log):
    log.append("\n===== SUDDEN DEATH =====")
    original = pool[:]
    r = 1

    while True:
        if len(pool) < 6:
            pool = original[:]
            log.append("[SD] Pool reset.")

        print(f"\n=== SUDDEN DEATH {r} ===")
        opts = random.sample(pool, 3)
        for i, c in enumerate(opts, 1):
            print(f"{i}. {c['nombre']}")
        pick = int(input("Choose: "))
        p_card = opts[pick-1]
        pool.remove(p_card)
        log.append(f"[SD] Player picked {p_card['nombre']}")

        ai_opts = random.sample(pool, 3)
        scored = [(weighted_score(c), c) for c in ai_opts]
        scored.sort(reverse=True, key=lambda t: t[0])
        a_card = scored[0][1]
        pool.remove(a_card)
        log.append(f"[SD] AI picked {a_card['nombre']}")

        res, txt = duel(p_card, a_card, final_round=True)
        log.append(txt)

        if res == "a":
            log.append("Player wins Sudden Death!")
            return "player"
        if res == "b":
            log.append("AI wins Sudden Death!")
            return "ai"

        log.append("[SD] Tie. Repeat.")
        r += 1


# ======================================================
# ======================== MAIN ========================
# ======================================================

def choose_level(all_digimon):
    levels = sorted({d["nivel"] for d in all_digimon})
    print("Available levels:")
    for i, l in enumerate(levels, 1):
        print(f"{i}. {l}")
    print(f"{len(levels)+1}. All")

    while True:
        c = input("Choose: ")
        if c.isdigit():
            c = int(c)
            if 1 <= c <= len(levels):
                return levels[c-1]
            if c == len(levels)+1:
                return "All"
        print("Invalid.")

def run_game():
    all_digimon = load_digimon("datos_digimon_todos.csv")
    level = choose_level(all_digimon)

    if level == "All":
        pool = all_digimon[:]
    else:
        pool = [d for d in all_digimon if d["nivel"] == level]

    print("\nChoose difficulty:")
    print("1. Normal\n2. Hard\n3. Impossible")
    while True:
        c = input("Difficulty: ")
        if c in ["1", "2", "3"]:
            diff = int(c)
            break

    log = []
    log.append(f"=== DIGIMON CARD DUEL V4.1 ===")
    log.append(f"Level: {level}")
    log.append(f"Difficulty: {diff}")

    player_style = pick_draft_style()
    ai_style     = ai_pick_draft_style()
    log.append(f"[DRAFT STYLES] Player={player_style} | AI={ai_style}")

    player_hand, ai_hand, pool = draft_initial_hands(
        pool, log, picks=5,
        player_style=player_style,
        ai_style=ai_style
    )

    sp, sa, hist = play_round(player_hand, ai_hand, diff, log)
    log.append(f"\nFinal Score: {sp}-{sa}")

    if sp > sa:
        winner = "player"
        log.append("PLAYER WINS MATCH!")
    elif sa > sp:
        winner = "ai"
        log.append("AI WINS MATCH!")
    else:
        winner = sudden_death(pool, diff, log)

    print(f"\nWinner: {winner.upper()}")

    with open("duel_logs_v4.1.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))

    print("Log saved.")


if __name__ == "__main__":
    run_game()