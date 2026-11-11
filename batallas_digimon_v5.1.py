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

"""
DIGIMON CARD DUEL V5
Estructura limpia, logs estilo V4.1, draft corregido,
evoluciones correctas y manos completas en todos los niveles.
"""

###############################################################
# DIGIMON CARD DUEL V5.1  — PART 1/3
# Core System: CSV loading, evolution loading, helpers,
# type system, and V4.1 duel logic EXACTLY preserved.
# Comments written in clean English like original scripts.
###############################################################

import csv
import random
from collections import defaultdict


# ============================================================
# ===============   LOAD DIGIMON FROM CSV   ==================
# ============================================================

def load_digimon(csv_file):
    """
    Loads Digimon data from CSV.
    Expected columns:
    abreviatura, nombre, defensa, ataque1, ataque2,
    velocidad, fuerza, media, nivel, tipo
    """
    digimon = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["defensa"]   = int(row["defensa"])
            row["ataque1"]   = int(row["ataque1"])
            row["ataque2"]   = int(row["ataque2"])
            row["velocidad"] = int(row["velocidad"])
            row["fuerza"]    = int(row["fuerza"])
            row["media"]     = int(row["media"])
            row["nivel"] = row["nivel"].lower().strip()
            row["tipo"]  = row["tipo"].lower().strip()
            digimon.append(row)
    return digimon


# ============================================================
# ===============   LOAD EVOLUTION PATHS   ==================
# ============================================================

def load_evolution_paths(csv_file):
    """
    Loads evolution routes from linea_evolutiva.csv.
    Format:
        rookie, champion, ultimate, mega
    Gracefully handles empty or missing fields.
    """
    evo_map = {}

    import csv
    with open(csv_file, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:

            # Convert None → "" to avoid .strip() errors
            rook   = (row.get("rookie")   or "").strip()
            champ  = (row.get("champion") or "").strip()
            ult    = (row.get("ultimate") or "").strip()
            mega   = (row.get("mega")     or "").strip()

            # Rookie -> Champion
            if rook and champ:
                evo_map[rook] = champ

            # Champion -> Ultimate
            if champ and ult:
                evo_map[champ] = ult

            # Ultimate -> Mega
            if ult and mega:
                evo_map[ult] = mega

    return evo_map


# ============================================================
# ======================== HELPERS ============================
# ============================================================

def find_card_by_name(name, pool):
    """Returns a copy of a card from pool by name."""
    name = name.lower().strip()
    for d in pool:
        if d["nombre"].lower() == name:
            return d.copy()
    return None


# ============================================================
# ==================== TYPE ADVANTAGE ========================
# ============================================================

# vaccine > virus > data > vaccine
TYPE_ORDER = {
    "vaccine": "virus",
    "virus":   "data",
    "data":    "vaccine"
}

def apply_type_bonus(a, b):
    """
    +10 bonus to ALL stats if type A beats type B,
    or vice versa. Same exact logic as V4.1.
    """
    a2 = a.copy()
    b2 = b.copy()

    if TYPE_ORDER[a2["tipo"]] == b2["tipo"]:
        for k in ["defensa","ataque1","ataque2","velocidad","fuerza","media"]:
            a2[k] += 10
    elif TYPE_ORDER[b2["tipo"]] == a2["tipo"]:
        for k in ["defensa","ataque1","ataque2","velocidad","fuerza","media"]:
            b2[k] += 10

    return a2, b2


def type_beats(a, b):
    """Pure type win condition used at final tiebreaker."""
    ta = a["tipo"]
    tb = b["tipo"]
    if ta == tb:
        return False
    return (
        (ta=="vaccine" and tb=="virus") or
        (ta=="virus"   and tb=="data")  or
        (ta=="data"    and tb=="vaccine")
    )


# ============================================================
# ==================== DUEL LOGIC (V4.1) =====================
# ============================================================

def score_base_stats(a, b):
    """
    Compares DEF, ATQ1, ATQ2, STR, SPD
    Returns (pa, pb) = points for A and B.
    """
    fields = ["defensa","ataque1","ataque2","fuerza","velocidad"]
    pa = pb = 0
    for s in fields:
        if a[s] > b[s]: pa += 1
        elif a[s] < b[s]: pb += 1
    return pa, pb


def duel(a, b):
    """
    FULL V4.1 DUEL LOGIC — Untouched, sacred.
    Order:
        1. Type bonus (+10 all stats)
        2. Base stats (5-point comparison)
        3. Media
        4. ATQ2 - DEF
        5. ATQ1 - DEF
        6. Type final comparison
        7. Tie
    Returns:
        "a"/"b"/"tie", reason-string
    """

    # 1. Apply type bonus
    a2, b2 = apply_type_bonus(a, b)

    # 2. Base stats
    pa, pb = score_base_stats(a2, b2)
    if pa != pb:
        return ("a" if pa>pb else "b"), "Base stats decide"

    # 3. Media
    if a2["media"] > b2["media"]:
        return "a", "Media decides"
    if a2["media"] < b2["media"]:
        return "b", "Media decides"

    # 4. ATQ2 - DEF
    d1 = a2["ataque2"] - b2["defensa"]
    d2 = b2["ataque2"] - a2["defensa"]
    if d1 != d2:
        return ("a" if d1>d2 else "b"), "ATQ2-DEF decides"

    # 5. ATQ1 - DEF
    d1 = a2["ataque1"] - b2["defensa"]
    d2 = b2["ataque1"] - a2["defensa"]
    if d1 != d2:
        return ("a" if d1>d2 else "b"), "ATQ1-DEF decides"

    # 6. Final type check (no bonus)
    if type_beats(a2, b2): return "a", "Type advantage"
    if type_beats(b2, a2): return "b", "Type advantage"

    # 7. Perfect tie
    return "tie", "Perfect tie"

###############################################################
# DIGIMON CARD DUEL V5.1  — PART 2/3
# AI system (simple & adaptive), personalities, draft system,
# player personality detection, counter-personality logic.
###############################################################

# ============================================================
# ===================== AI BASIC SCORING =====================
# ============================================================

def ai_simple_score(card, mode):
    """
    V4.1 behaviour — simple evaluators.
    Modes:
        aggressive   -> highest ATQ2
        physical     -> highest STR
        balanced     -> highest MEDIA
        type         -> choose by type ranking
        chaotic       -> random
        human         -> ATQ1 + ATQ2
    """
    if mode == "aggressive":
        return card["ataque2"]

    if mode == "physical":
        return card["fuerza"]

    if mode == "balanced":
        return card["media"]

    if mode == "type":
        order = {"vaccine": 3, "virus": 2, "data": 1}
        return order.get(card["tipo"], 0)

    if mode == "human":
        return card["media"]


    # chaotic → random
    return random.randint(0, 999)


# ============================================================
# =============  AI PERSONALITY CARD PICKER  =================
# ============================================================

def ai_choose_card(hand, mode, player_history):
    """
    IA NO ve la carta actual del jugador.
    Modos ajustados: opportunistic y human.
    """

    # CHAOTIC: random total
    if mode == "chaotic":
        choice = random.choice(hand)
        hand.remove(choice)
        return choice

    # OPPORTUNISTIC mejorado
    if mode == "opportunistic":
        # Si hay historial, analizar ritmo
        if player_history:
            last = player_history[-1]
            pwr_last = last["ataque2"] + last["velocidad"] + last["fuerza"]
        else:
            pwr_last = 0

        # Detectar si el jugador lleva turno fuerte (ritmo ofensivo)
        # Usamos un umbral comparado contra las cartas propias
        strongest_ai = max(hand, key=lambda c: c["ataque2"])
        strongest_val = strongest_ai["ataque2"]

        # Si el jugador viene de un golpe fuerte → IA se guarda lo bueno
        if pwr_last > strongest_val * 0.85:
            # Escoger carta "media"
            choice = max(hand, key=lambda c: c["media"])
            hand.remove(choice)
            return choice

        # Si el jugador viene flojo → IA aprovecha y tira fuerte
        choice = strongest_ai
        hand.remove(choice)
        return choice

    # HUMAN mejorado
    if mode == "human":
        # Comportamiento mezclado:
        roll = random.random()

        # 60% → carta "razonable"
        if roll < 0.60:
            choice = max(hand, key=lambda c: (c["defensa"] + c["fuerza"] + c["ataque2"]) / 3)
            hand.remove(choice)
            return choice

        # 20% → se comporta agresivo
        if roll < 0.80:
            choice = max(hand, key=lambda c: c["ataque2"])
            hand.remove(choice)
            return choice

        # 20% → se comporta conservador (tirando carta floja ahora)
        choice = min(hand, key=lambda c: c["ataque2"])
        hand.remove(choice)
        return choice

    # Resto de modos estándar
    scored = [(ai_simple_score(c, mode), c) for c in hand]
    scored.sort(key=lambda t: t[0], reverse=True)
    choice = scored[0][1]
    hand.remove(choice)
    return choice


# ============================================================
# ================= PLAYER PERSONALITY SCAN ==================
# ============================================================

def detect_player_personality(played_cards_stats):
    """
    played_cards_stats: lista en orden de juego con el valor (media) o fuerza de cada carta jugada.
    """

    n = len(played_cards_stats)
    if n < 2:
        return "aggressive"  # por defecto

    half = n // 2
    first_half = sum(played_cards_stats[:half]) / half
    second_half = sum(played_cards_stats[half:]) / (n - half)

    # Si las cartas fuertes están al principio → aggressive
    if first_half > second_half:
        return "aggressive"

    # Si las fuertes están al final → conservative
    return "conservative"



# ============================================================
# ================= COUNTER PERSONALITY MAP ==================
# ============================================================

COUNTER = {
    "aggressive":   "conservative",
    "conservative": "aggressive",
    "human":        "opportunistic",
    "opportunistic":"chaotic",
    "chaotic":      "aggressive",
}


# ============================================================
# ===== AI PERSONALITY SELECTION BETWEEN ROUNDS (5 DUELS) ====
# ============================================================

def choose_ai_personality_after_round(prev_mode, result_diff, player_style):

    # 1. AI gana de paliza → NO CAMBIA JAMÁS
    if result_diff >= 3:
        return prev_mode

    # Helper: generar mezcla 40/20/20/20
    def mixed_distribution(core_mode):
        r = random.random()
        if r < 0.40:
            return core_mode
        elif r < 0.60:
            return "chaotic"
        elif r < 0.80:
            return "opportunistic"
        else:
            return "human"

    # 2. AI gana por poco (1–2)
    if result_diff > 0:
        # core_mode = lo que antes iba a devolver: 70% prev_mode, 30% counter
        if random.random() < 0.70:
            core = prev_mode
        else:
            core = COUNTER.get(player_style, prev_mode)
        return mixed_distribution(core)

    # 3. Empate → antes random entre 3 modos; ahora mezclado con nuestro sistema
    if result_diff == 0:
        # core_mode = aleatorio entre los tres que antes usabas
        core = random.choice(["chaotic", "opportunistic", "human"])
        return mixed_distribution(core)

    # 4. AI pierde por poco (−1 o −2)
    if result_diff >= -2:
        # core_mode = lo que antes iba a devolver: 60% counter, 40% prev_mode
        if random.random() < 0.60:
            core = COUNTER.get(player_style, prev_mode)
        else:
            core = prev_mode
        return mixed_distribution(core)

    # 5. AI pierde por paliza (−3 o peor) → core = counter 100%
    core = COUNTER.get(player_style, prev_mode)
    return mixed_distribution(core)



# ============================================================
# ======================== DRAFT SYSTEM =======================
# ============================================================

def show_card_draft(card):
    return (f"{card['nombre']} | DEF {card['defensa']} | ATQ1 {card['ataque1']} | "
            f"ATQ2 {card['ataque2']} | STR {card['fuerza']} | SPD {card['velocidad']} "
            f"| MEDIA {card['media']} | TYPE {card['tipo']}")


def player_draft(pool):
    """Player chooses 1 of 3 cards."""
    options = random.sample(pool, 3)
    print("\n=== DRAFT (Pick 1 of 3) ===")
    for i, c in enumerate(options, 1):
        print(f"{i}. {show_card_draft(c)}")
    while True:
        x = input("Choose: ")
        if x.isdigit() and 1 <= int(x) <= 3:
            chosen = options[int(x) - 1]
            pool.remove(chosen)
            return chosen, pool


def ai_draft(pool, ai_mode):
    """AI also picks 1 of 3 based on its personality."""
    options = random.sample(pool, 3)
    best = None
    best_score = -99999

    # Evaluate each with simple V4.1 scoring
    for c in options:
        sc = ai_simple_score(c, ai_mode)
        if sc > best_score:
            best_score = sc
            best = c

    pool.remove(best)
    return best, pool


# ============================================================
# ====================== ROUND (5 DUELS) ======================
# ============================================================

def play_5_duels(player_hand, ai_hand, ai_mode):
    """
    Returns:
        score_player, score_ai, player_history
    """
    score_p = 0
    score_ai = 0
    history = []

    for turn in range(5):
        # PLAYER CHOICE
        print("\nYour hand:")
        for i, d in enumerate(player_hand, 1):
            print(f"{i}. {show_card_draft(d)}")
        while True:
            x = input("Play card: ")
            if x.isdigit() and 1 <= int(x) <= len(player_hand):
                p_card = player_hand.pop(int(x) - 1)
                break
        history.append(p_card)

        # AI CHOICE (no cheating)
        a_card = ai_choose_card(ai_hand, ai_mode, history)

        # Duel
        result, why = duel(p_card, a_card)
        print(f"PLAYER played {p_card['nombre']} — AI played {a_card['nombre']}")
        print("Result:", result.upper(), "| Reason:", why)

        if result == "a":
            score_p += 1
        elif result == "b":
            score_ai += 1

    return score_p, score_ai, history


###############################################################
# DIGIMON CARD DUEL V5.1 — PART 3/3
# Full tournament engine (8 battles × 5 duels),
# evolution system, level progression, AI personality adaptation,
# final main() runner.
###############################################################

# ============================================================
# ======================= EVOLUTION ==========================
# ============================================================

def evolve_card(card, evo_map):
    """
    Given a rookie->champion->ultimate->mega map,
    returns the EVO+5 version of the card.
    If the card is already final (mega), return None.
    """
    name = card["nombre"]
    if name not in evo_map:
        return None  # cannot evolve

    evo_name = evo_map[name]
    new_card = card.copy()
    new_card["nombre"] = evo_name

    # +5 to all stats (your rule)
    for k in ["defensa","ataque1","ataque2","fuerza","velocidad","media"]:
        new_card[k] += 5

    # Level upgrade
    order = ["rookie","champion","ultimate","mega"]
    lvl = card["nivel"]
    idx = order.index(lvl)
    new_card["nivel"] = order[min(idx+1,3)]

    return new_card


# ============================================================
# ====================== BATTLE TYPES ========================
# ============================================================

def battle_without_draft(pool, ai_mode):
    """
    Takes 5 random for player and AI. No draft.
    Evolutions returned.
    """
    full = pool[:]  # safety copy
    p_hand = random.sample(full, 5)
    for x in p_hand:
        full.remove(x)

    ai_hand = random.sample(full, 5)

    print("\n=== BATTLE (NO DRAFT) ===")
    score_p, score_ai, hist = play_5_duels(p_hand, ai_hand, ai_mode)

    return score_p, score_ai, hist


def battle_with_draft(pool, ai_mode):
    """
    Draft 5 cards each.
    Evolutions returned.
    """
    print("\n=== BATTLE (DRAFT) ===")
    p_hand = []
    ai_hand = []
    for _ in range(5):
        pl, pool = player_draft(pool)
        ai, pool = ai_draft(pool, ai_mode)
        p_hand.append(pl)
        ai_hand.append(ai)

    score_p, score_ai, hist = play_5_duels(p_hand, ai_hand, ai_mode)
    return score_p, score_ai, hist


# ============================================================
# =============== PERSONALITY CYCLING PER ROUND =============
# ============================================================

def run_battle(pool, ai_mode, evo_map, is_draft):
    """
    Runs one battle (5 duels).
    Returns:
        score_p, score_ai, player_history, evolutions
    """
    # Run battle
    if is_draft:
        scp, sca, hist = battle_with_draft(pool, ai_mode)
    else:
        scp, sca, hist = battle_without_draft(pool, ai_mode)

    # Compute evolutions (except mega)
    evolutions = []
    for card in hist:
        evo = evolve_card(card, evo_map)
        if evo:
            evolutions.append(evo)

    return scp, sca, hist, evolutions


# ============================================================
# ======================= MASTER ENGINE ======================
# ============================================================

def run_tournament_v5_1(all_cards, evo_map):
    """
    FULL 8-BATTLE TOURNAMENT
    Rookie B1 (no draft)
    Rookie B2 (draft)
    Champion B3 (no draft)
    Champion B4 (draft)
    Ultimate B5 (no draft)
    Ultimate B6 (draft)
    Mega B7 (no draft)
    Mega B8 (draft)
    """

    # -----------------------------
    # Prepare pools per level
    # -----------------------------
    rookies   = [c for c in all_cards if c["nivel"]=="rookie"]
    champions = [c for c in all_cards if c["nivel"]=="champion"]
    ultimates = [c for c in all_cards if c["nivel"]=="ultimate"]
    megas     = [c for c in all_cards if c["nivel"]=="mega"]

    # IA FIRST PERSONALITY = random
    ai_mode = random.choice(["aggressive","conservative","human",
                             "opportunistic","chaotic"])

    print("\n===================================================")
    print("               DIGIMON CARD DUEL V5.1             ")
    print("===================================================")
    print("Initial AI personality:", ai_mode)
    print("===================================================\n")

    # -------------------------------------------------------
    # ============== ROOKIE LEVEL ===========================
    # -------------------------------------------------------

    print("\n######## LEVEL: ROOKIE ########")

    # ---------- Battle 1 (no draft) ----------
    scp, sca, h1, evo1 = run_battle(rookies[:], ai_mode, evo_map, False)
    print(f"Battle 1 Score: PLAYER {scp} - AI {sca}")

    result_diff = sca - scp
    p_style = detect_player_personality([c["media"] for c in h1]) 
    print("Player detected as:", p_style)
    ai_mode = choose_ai_personality_after_round(ai_mode, result_diff, p_style)
    print("New AI personality after Battle 1:", ai_mode)

    # ---------- Battle 2 (draft) ----------
    scp2, sca2, h2, evo2 = run_battle(rookies[:], ai_mode, evo_map, True)
    print(f"Battle 2 Score: PLAYER {scp2} - AI {sca2}")

    result_diff = sca2 - scp2
    p_style = detect_player_personality([c["media"] for c in h2]) 
    print("Player detected as:", p_style)
    ai_mode = choose_ai_personality_after_round(ai_mode, result_diff, p_style)
    print("New AI personality after Battle 2:", ai_mode)


    # -------------------------------------------------------
    # ============== CHAMPION LEVEL =========================
    # -------------------------------------------------------

    print("\n######## LEVEL: CHAMPION ########")

    champ_b3_pool = champions[:] + evo1
    champ_b4_pool = champions[:] + evo2

    # ---------- Battle 3 (no draft) ----------
    scp3, sca3, h3, evo3 = run_battle(champ_b3_pool, ai_mode, evo_map, False)
    print(f"Battle 3 Score: PLAYER {scp3} - AI {sca3}")

    result_diff = sca3 - scp3
    p_style = detect_player_personality([c["media"] for c in h3]) 
    print("Player detected as:", p_style)
    ai_mode = choose_ai_personality_after_round(ai_mode, result_diff, p_style)
    print("New AI personality after Battle 3:", ai_mode)

    # ---------- Battle 4 (draft) ----------
    scp4, sca4, h4, evo4 = run_battle(champ_b4_pool, ai_mode, evo_map, True)
    print(f"Battle 4 Score: PLAYER {scp4} - AI {sca4}")

    result_diff = sca4 - scp4
    p_style = detect_player_personality([c["media"] for c in h4])
    print("Player detected as:", p_style)
    ai_mode = choose_ai_personality_after_round(ai_mode, result_diff, p_style)
    print("New AI personality after Battle 4:", ai_mode)


    # -------------------------------------------------------
    # ============== ULTIMATE LEVEL =========================
    # -------------------------------------------------------

    print("\n######## LEVEL: ULTIMATE ########")

    ult_b5_pool = ultimates[:] + evo3
    ult_b6_pool = ultimates[:] + evo4

    # Battle 5 (no draft)
    scp5, sca5, h5, evo5 = run_battle(ult_b5_pool, ai_mode, evo_map, False)
    print(f"Battle 5 Score: PLAYER {scp5} - AI {sca5}")

    result_diff = sca5 - scp5
    p_style = detect_player_personality([c["media"] for c in h5]) 
    print("Player detected as:", p_style)
    ai_mode = choose_ai_personality_after_round(ai_mode, result_diff, p_style)
    print("New AI personality after Battle 5:", ai_mode)

    # Battle 6 (draft)
    scp6, sca6, h6, evo6 = run_battle(ult_b6_pool, ai_mode, evo_map, True)
    print(f"Battle 6 Score: PLAYER {scp6} - AI {sca6}")

    result_diff = sca6 - scp6
    p_style = detect_player_personality([c["media"] for c in h6]) 
    print("Player detected as:", p_style)
    ai_mode = choose_ai_personality_after_round(ai_mode, result_diff, p_style)
    print("New AI personality after Battle 6:", ai_mode)


    # -------------------------------------------------------
    # ============== MEGA LEVEL =============================
    # -------------------------------------------------------

    print("\n######## LEVEL: MEGA ########")

    mega_b7_pool = megas[:] + evo5
    mega_b8_pool = megas[:] + evo6

    # Battle 7 (no draft, mega cannot evolve further)
    scp7, sca7, h7, _ = run_battle(mega_b7_pool, ai_mode, evo_map, False)
    print(f"Battle 7 Score: PLAYER {scp7} - AI {sca7}")

    result_diff = sca7 - scp7
    p_style = detect_player_personality([c["media"] for c in h7]) 
    print("Player detected as:", p_style)
    ai_mode = choose_ai_personality_after_round(ai_mode, result_diff, p_style)
    print("New AI personality after Battle 7:", ai_mode)

    # Battle 8 (draft, last one)
    scp8, sca8, h8, _ = run_battle(mega_b8_pool, ai_mode, evo_map, True)
    print(f"Battle 8 Score: PLAYER {scp8} - AI {sca8}")
    print("\n=============== FINAL RESULT ===============")
    total_p = scp + scp2 + scp3 + scp4 + scp5 + scp6 + scp7 + scp8
    total_a = sca + sca2 + sca3 + sca4 + sca5 + sca6 + sca7 + sca8
    print(f"TOTAL SCORE: PLAYER {total_p} — AI {total_a}")

    if total_p > total_a:
        print("PLAYER WINS THE TOURNAMENT.")
    elif total_a > total_p:
        print("AI WINS THE TOURNAMENT.")
    else:
        print("DRAW — EXTREMELY RARE.")


# ============================================================
# ============================ MAIN ==========================
# ============================================================

def run_game_v5_1():
    # Load digimon
    all_cards = load_digimon("datos_digimon_todos.csv")

    # Load evo map (you must define a CSV or dict before running)
    # For now we assume you already have a variable evo_map ready.
    # Example:
    # evo_map = {"Agumon": "Greymon", "Greymon": "MetalGreymon", ...}

    evo_map = load_evolution_paths("linea_evolutiva.csv")

    run_tournament_v5_1(all_cards, evo_map)


# If you want direct execution:
run_game_v5_1()