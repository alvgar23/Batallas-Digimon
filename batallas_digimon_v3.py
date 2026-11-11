"""
DIGIMON CARD DUEL – V3
-----------------------------------
Player vs COM (AI with 3 difficulty levels)

This script creates an interactive card duel system using the same
combat logic from Tournament Simulator V2. The duel mechanics remain
identical, but now the structure is a turn-based card game.

GAME FLOW
---------
1. Load Digimon from CSV.
2. Player chooses level (rookie, champion, etc).
3. Player and AI each receive 3 cards from that level.
4. 3-turn normal round:
    - Player selects a card (menu 1-3).
    - AI selects a card using selected difficulty mode.
    - Duel is resolved using V2 rules.
    - Win = +1 point, Tie = 0.
5. After 3 turns:
    - Higher score wins.
    - If tied → SUDDEN DEATH.
6. Sudden Death:
    - Both get new 3 cards.
    - First duel win decides the whole match.
    - If tie → use next card.
    - If they run out → new 3 cards and repeat.

AI DIFFICULTIES
---------------
NORMAL:
    - Mild intelligence.
    - Picks between mid/high cards with light randomness.

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
All duels are logged in detail into:
    duel_logs_v3.txt

Combat mechanics are EXACTLY the same as V2.

Author: Avtomat Agentics
"""


import csv
import random
from collections import defaultdict


# ======================================================
# ===============   LOAD DIGIMON (same as V2) ===========
# ======================================================

def load_digimon(csv_file):
    """
    Load Digimon from CSV into dictionaries.
    Numeric fields converted to int.
    Text fields normalized.
    """
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
# ===============   COMBAT LOGIC (copied from V2) ======
# ======================================================

def type_beats(a, b):
    """Circular type advantage."""
    ta = a["tipo"]
    tb = b["tipo"]
    if ta == tb:
        return False
    return (
        (ta == "vaccine" and tb == "virus") or
        (ta == "virus"   and tb == "data")  or
        (ta == "data"    and tb == "vaccine")
    )


def score_base_stats(a, b):
    """Compare the 5 core stats."""
    fields = ["defensa", "ataque1", "ataque2", "fuerza", "velocidad"]
    pa = pb = 0
    for s in fields:
        if a[s] > b[s]: pa += 1
        elif a[s] < b[s]: pb += 1
    return pa, pb


def diff_atq2_def(a, b):
    return a["ataque2"] - b["defensa"]


def diff_atq1_def(a, b):
    return a["ataque1"] - b["defensa"]


def duel(a, b, final_round=False, verbose=True):
    """
    Full duel logic from V2.
    Returns: winner ('a', 'b', 'tie'), log_text
    """
    log = []
    pa, pb = score_base_stats(a, b)
    log.append(f"Base stats: {pa}-{pb}")

    if pa != pb:
        log.append(f"Winner by base stats: {a['nombre'] if pa>pb else b['nombre']}")
        return ("a" if pa > pb else "b"), "\n".join(log)

    # media
    if a["media"] > b["media"]:
        log.append(f"Media: {a['media']} > {b['media']} → winner {a['nombre']}")
        return "a", "\n".join(log)
    elif a["media"] < b["media"]:
        log.append(f"Media: {b['media']} > {a['media']} → winner {b['nombre']}")
        return "b", "\n".join(log)
    else:
        log.append("Media: tie")

    # atq2-def
    d1 = diff_atq2_def(a, b)
    d2 = diff_atq2_def(b, a)
    if d1 > d2:
        log.append(f"Atq2-Def: {a['nombre']} wins")
        return "a", "\n".join(log)
    elif d1 < d2:
        log.append(f"Atq2-Def: {b['nombre']} wins")
        return "b", "\n".join(log)
    else:
        log.append("Atq2-Def: tie")

    # atq1-def
    d1 = diff_atq1_def(a, b)
    d2 = diff_atq1_def(b, a)
    if d1 > d2:
        log.append(f"Atq1-Def: {a['nombre']} wins")
        return "a", "\n".join(log)
    elif d1 < d2:
        log.append(f"Atq1-Def: {b['nombre']} wins")
        return "b", "\n".join(log)
    else:
        log.append("Atq1-Def: tie")

    # type
    if type_beats(a, b):
        log.append(f"Type advantage: {a['tipo']} > {b['tipo']} → {a['nombre']}")
        return "a", "\n".join(log)
    elif type_beats(b, a):
        log.append(f"Type advantage: {b['tipo']} > {a['tipo']} → {b['nombre']}")
        return "b", "\n".join(log)
    else:
        log.append("Type: tie")

    # ultra-tie
    if final_round:
        log.append("Ultra tie (FINAL) → tie")
    else:
        log.append("Ultra tie → tie")
    return "tie", "\n".join(log)


# ======================================================
# ================  GAME SYSTEM V3  =====================
# ======================================================

def choose_level(all_digimon):
    """Let the user pick a level OR all levels mixed."""
    levels = sorted(list({d["nivel"] for d in all_digimon}))

    print("Available levels:")
    for i, lvl in enumerate(levels, 1):
        print(f"{i}. {lvl}")
    print(f"{len(levels)+1}. All levels mixed")

    while True:
        c = input("Choose level: ").strip()

        if c.isdigit():
            c = int(c)
            if 1 <= c <= len(levels):
                return levels[c-1]                # One specific level
            elif c == len(levels) + 1:
                return "All"                     # Mixed pool

        print("Invalid option.")


def deal_hand(pool, n=5):
    """Randomly pick n digimon from a level pool."""
    return random.sample(pool, n)


def show_hand(hand):
    """Display hand with stats so user can pick intelligently."""
    print("\nYour hand:")
    for i, d in enumerate(hand, 1):
        print(f"{i}. {d['nombre']} | DEF {d['defensa']} | ATQ1 {d['ataque1']} | "
              f"ATQ2 {d['ataque2']} | STR {d['fuerza']} | SPD {d['velocidad']} | "
              f"MEDIA {d['media']} | TYPE {d['tipo']}")


def player_choose_card(hand):
    """Player selects card using menu 1-2-3-4-5."""
    while True:
        show_hand(hand)
        c = input("Choose your card (1-5): ").strip()
        if c.isdigit() and 1 <= int(c) <= len(hand):
            return hand.pop(int(c)-1)
        print("Invalid option.")


# ======================================================
# ===============  AI SYSTEM  ==========================
# ======================================================

def classify_hand(hand):
    """
    Classify cards by relative strength.
    Simple score = sum of key stats.
    Sorted ONLY by score to avoid dict comparison errors.
    """
    scored = []
    for d in hand:
        score = d["defensa"] + d["ataque1"] + d["ataque2"] + d["fuerza"] + d["velocidad"] + d["media"]
        scored.append((score, d))

    # Sort ONLY by the score, ignoring the dict to avoid TypeError
    scored.sort(key=lambda x: x[0], reverse=True)

    return scored


def ai_choose_card(hand, difficulty, player_history, ai_log):
    """
    AI decision maker.
    Difficulty modes:
        1 = Normal
        2 = Hard
        3 = Impossible
    """
    # Log classification
    classified = classify_hand(hand)
    ai_log.append(f"[AI] Hand classified: {[(c['nombre'], s) for s, c in classified]}")

    if difficulty == 1:
        # NORMAL: soft intelligence
        # Prefers top 2 cards but with randomness
        if random.random() < 0.5:
            choice = classified[0][1]
        else:
            idx = random.choice(range(len(hand)))
            choice = hand[idx]

    elif difficulty == 2:
        # HARD: looks at player's previous pattern
        if len(player_history) == 0:
            # Unknown behavior → save best card
            choice = classified[1][1]
        else:
            # If player opened strong, AI counters later
            last_player = player_history[-1]
            last_score = last_player["defensa"] + last_player["ataque1"] + last_player["ataque2"] + last_player["fuerza"] + last_player["velocidad"] + last_player["media"]

            if last_score > classified[0][0] * 0.8:
                # Player used a strong card → AI saves strongest
                choice = classified[-1][1]
            else:
                choice = classified[0][1]

        # 20% chaos
        if random.random() < 0.2:
            choice = random.choice(hand)

    else:
        # IMPOSSIBLE: hybrid adaptive
        # Analyze player tendencies:
        strong_usage = sum(
            p["ataque2"] + p["fuerza"] + p["velocidad"] for p in player_history
        )

        # Guess player behavior
        if len(player_history) == 0:
            guess_aggressive = True
        else:
            guess_aggressive = strong_usage / len(player_history) > 180

        if guess_aggressive:
            # Player tends to open strong → AI keeps its bomb for counter
            choice = classified[-1][1]
        else:
            choice = classified[0][1]

        # AI type reaction (if many player's cards share same type)
        if len(player_history) >= 2:
            types = [p["tipo"] for p in player_history]
            common = max(set(types), key=types.count)
            # Try counter type if available
            for _, d in classified:
                if type_beats(d, {"tipo": common}):
                    choice = d
                    break

        # 10% chaos to break predictability
        if random.random() < 0.1:
            choice = random.choice(hand)

    hand.remove(choice)
    ai_log.append(f"[AI] Chose card: {choice['nombre']}")
    return choice


# ======================================================
# ===============  ROUND AND GAME LOGIC  ===============
# ======================================================

def play_round(player_hand, ai_hand, difficulty, log):
    """
    Play the 3-turn normal round.
    Returns: score_player, score_ai, player_history(list)
    """
    score_p = 0
    score_ai = 0
    history = []

    for turn in range(1, 6):
        log.append(f"\n===== TURN {turn} =====")

        # Player
        p_card = player_choose_card(player_hand)
        log.append(f"Player chose: {p_card['nombre']}")
        history.append(p_card)

        # AI
        ai_log = []
        a_card = ai_choose_card(ai_hand, difficulty, history, ai_log)
        for line in ai_log:
            log.append(line)
        log.append(f"AI chose: {a_card['nombre']}")

        # Duel
        result, txt = duel(p_card, a_card)
        log.append(txt)

        if result == "a":
            score_p += 1
            log.append("→ Player wins this duel.")
        elif result == "b":
            score_ai += 1
            log.append("→ AI wins this duel.")
        else:
            log.append("→ Tie (0 points).")

    return score_p, score_ai, history


def sudden_death(pool, difficulty, log):
    """
    Sudden Death:
    - New hands of 3 each time if needed.
    - First duel win ends match.
    """
    log.append("\n===== SUDDEN DEATH =====")

    while True:
        player_hand = deal_hand(pool)
        ai_hand = deal_hand(pool)

        while player_hand and ai_hand:
            p_card = player_choose_card(player_hand)
            log.append(f"[SD] Player chose {p_card['nombre']}")

            ai_log = []
            # Show AI hand before choosing
            ai_log.append(f"[SD] AI hand: {[(d['nombre'], d['defensa'] + d['ataque1'] + d['ataque2'] + d['fuerza'] + d['velocidad'] + d['media']) for d in ai_hand]}")

            # In Sudden Death, AI must play its strongest card immediately
            classified = classify_hand(ai_hand)
            a_card = classified[0][1]   # strongest card
            ai_hand.remove(a_card)
            ai_log.append(f"[SD] [AI] Forced best card: {a_card['nombre']}")
            for line in ai_log:
                log.append(f"[SD] {line}")

            log.append(f"[SD] AI chose {a_card['nombre']}")

            result, txt = duel(p_card, a_card, final_round=True)
            log.append(txt)

            if result == "a":
                log.append("Player wins by Sudden Death!")
                return "player"
            elif result == "b":
                log.append("AI wins by Sudden Death!")
                return "ai"
            else:
                log.append("[SD] Tie → next card")

        log.append("[SD] Out of cards → new hands.")


def run_game():
    """Main game loop."""
    all_digimon = load_digimon("datos_digimon_todos.csv")

    # Choose level
    level = choose_level(all_digimon)
    if level == "All":
        pool = all_digimon[:]       # full deck
    else:
        pool = [d for d in all_digimon if d["nivel"] == level]


    # Difficulty
    print("\nChoose AI difficulty:")
    print("1. Normal")
    print("2. Hard")
    print("3. Impossible")
    while True:
        c = input("Difficulty: ").strip()
        if c in ["1", "2", "3"]:
            diff = int(c)
            break

    # Log
    log = []
    log.append(f"=== DIGIMON CARD DUEL V3 ===")
    log.append(f"Level chosen: {level}")
    log.append(f"AI Difficulty: {diff}")

    # Deal hands
    player_hand = deal_hand(pool)
    ai_hand = deal_hand(pool)

    # Play normal round
    score_p, score_ai, history = play_round(player_hand, ai_hand, diff, log)

    log.append(f"\nFinal score: Player {score_p} – AI {score_ai}")

    if score_p > score_ai:
        log.append("PLAYER WINS MATCH!")
        winner = "player"
    elif score_ai > score_p:
        log.append("AI WINS MATCH!")
        winner = "ai"
    else:
        # Sudden Death
        winner = sudden_death(pool, diff, log)

    print(f"\nWinner: {winner.upper()}")

    # Save log
    with open("duel_logs_v3.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))

    print("Full log saved as duel_logs_v3.txt")


# ======================================================
# =====================   MAIN   =======================
# ======================================================

if __name__ == "__main__":
    run_game()