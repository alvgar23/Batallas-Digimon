"""
author: Avtomat Agentics

DIGIMON TOURNAMENT SIMULATOR – FULL DESCRIPTION
-----------------------------------------------

This program simulates multiple Digimon tournaments using detailed
battle rules, multi-level filtering, random matchmaking, and complete
round-by-round logs.

CSV INPUT
---------
The CSV file contains one Digimon per row with the following fields:

    abreviatura, nombre, defensa, ataque1, ataque2,
    fuerza, velocidad, media, nivel, tipo

All numeric fields are integers. "nivel" and "tipo" are strings.

The program loads all Digimon from the CSV and then asks the user to
choose which levels to include (rookie, champion, etc.). If only one
level exists, it is selected automatically.

TOURNAMENT STRUCTURE
--------------------
The tournament runs in rounds until only one Digimon remains
(or multiple champions in case of a final ultra-tie).

Each round:
    - Participants are shuffled randomly.
    - If the number of participants is odd:
         The first match is a 3-way triple battle.
    - Remaining Digimon fight in standard 1-vs-1 duels.

TRIPLE BATTLES
--------------
A triple battle is a round-robin:
    Digimon A vs B
    Digimon A vs C
    Digimon B vs C

Each duel grants:
    +1 point to the winner
    +0 for a tie

Winners:
    - If one Digimon has the highest points → only that one advances.
    - If 2 or 3 tie → all tied Digimon advance.
    - If this happens in the FINAL → all tied Digimon are champions.

1-VS-1 DUEL RULES (VERY IMPORTANT)
---------------------------------
The duel has a strict hierarchy of decision criteria.

1. BASE STATS (primary battle)
   Compare the 5 fundamental stats:
       defensa, ataque1, ataque2, fuerza, velocidad
   Each stat won gives +1 point.
   If pa != pb → winner decided.

2. TIEBREAKER 1 – MEDIA
   Higher "media" wins.
   If still tied → next criterion.

3. TIEBREAKER 2 – ataque2 - enemy_defensa
   Compare:
       (A_atq2 - B_def) vs (B_atq2 - A_def)
   Higher value wins.
   If still tied → next criterion.

4. TIEBREAKER 3 – ataque1 - enemy_defensa
   Same logic as above.
   If still tied → next criterion.

5. TIEBREAKER 4 – TYPE ADVANTAGE
   Circular system:
       vaccine > virus
       virus > data
       data > vaccine
   If types decide → winner chosen.
   If same type or tie → proceed to ultra-tie.

6. ULTRA-TIE
   All criteria exhausted and still tied.

   - If NOT final round → both Digimon advance.
   - If FINAL ROUND → both Digimon are champions.

MULTIPLE TOURNAMENTS
--------------------
The simulator runs N tournaments (default = 10).
Each tournament has independent random shuffling.

Each winner (single or multiple) increments their count
in the "palmares" dictionary.

LOGGING
-------
The program prints a detailed log containing:

    - All rounds
    - All participants per round
    - All triple battles
    - All duels
    - Which criteria were used
    - When and why ties occur
    - When type advantage decides
    - When ultra-ties cause multiple advancement
    - Tournament champions

This produces a full, human-readable trace of the entire process.

SUMMARY
-------
This code:
    - Reads Digimon from CSV
    - Filters by level
    - Runs multi-round elimination tournaments
    - Uses deterministic, hierarchical duel rules
    - Supports triple battles
    - Supports ultra-tie logic
    - Supports multiple champions in finals
    - Supports multiple repeated tournaments
    - Maintains global victory statistics
    - Prints a full readable log of every decision

It is a complete Digimon battle and tournament engine with
fully explainable combat resolution.
"""


import csv
import random
from collections import defaultdict

# ======================================================
# ===============   DATA LOADING   =====================
# ======================================================

def load_digimon(csv_file):
    """
    Loads Digimon from a CSV file into a list of dictionaries.
    Converts numerical fields to int.
    Leaves 'nivel' and 'tipo' as strings.
    """
    digimon = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:

            # Convert numeric stats
            row["defensa"]   = int(row["defensa"])
            row["ataque1"]   = int(row["ataque1"])
            row["ataque2"]   = int(row["ataque2"])
            row["fuerza"]    = int(row["fuerza"])
            row["velocidad"] = int(row["velocidad"])
            row["media"]     = int(row["media"])

            # Normalize text fields
            row["nivel"] = row["nivel"].lower().strip()
            row["tipo"]  = row["tipo"].lower().strip()

            digimon.append(row)
    return digimon


# ======================================================
# ===============   LEVEL MENU   =======================
# ======================================================

def choose_levels(all_digimon):
    """
    Shows a level selection menu.
    If only one level exists in the file, selects it directly.
    Otherwise prints menu and asks the user to choose.
    """
    levels_found = sorted(list({d["nivel"] for d in all_digimon}))

    if len(levels_found) == 1:
        # Only one level exists → select it automatically
        print("Only one level found:", levels_found[0])
        return {levels_found[0]}

    print("Available levels in CSV:")
    for i, lvl in enumerate(levels_found, 1):
        print(f"{i}. {lvl}")
    print(f"{len(levels_found)+1}. All levels")

    while True:
        choice = input("Choose a level option: ").strip()

        # Number of one level
        if choice.isdigit():
            c = int(choice)
            if 1 <= c <= len(levels_found):
                return {levels_found[c-1]}
            elif c == len(levels_found)+1:
                return set(levels_found)

        print("Invalid option. Try again.")


# ======================================================
# ===============   TOURNAMENT MENU   ==================
# ======================================================

def choose_tournament_mode():
    print("\nChoose tournament mode:")
    print("1. Single Tournament (10 repetitions)")
    print("2. Full Ranking Tournament (Champion Removal Mode)")

    while True:
        choice = input("Option: ").strip()
        if choice == "1":
            return 1
        if choice == "2":
            return 2
        print("Invalid option.")



# ======================================================
# ===============   TYPE ADVANTAGE   ===================
# ======================================================

def type_beats(a, b):
    """
    Circular type advantage:
    vaccine > virus
    virus > data
    data > vaccine
    Returns True if a's type beats b's.
    """
    ta = a["tipo"]
    tb = b["tipo"]

    if ta == tb:
        return False

    return (
        (ta == "vaccine" and tb == "virus") or
        (ta == "virus"   and tb == "data")  or
        (ta == "data"    and tb == "vaccine")
    )


# ======================================================
# ===============   SCORING HELPERS   ==================
# ======================================================

def score_base_stats(a, b):
    """
    Compares the 5 fundamental stats.
    Returns pa, pb (points for each).
    """
    fields = ["defensa", "ataque1", "ataque2", "fuerza", "velocidad"]
    pa = pb = 0

    for s in fields:
        if a[s] > b[s]:
            pa += 1
        elif a[s] < b[s]:
            pb += 1

    return pa, pb


def diff_atq2_def(a, b):
    return a["ataque2"] - b["defensa"]


def diff_atq1_def(a, b):
    return a["ataque1"] - b["defensa"]


# ======================================================
# ===============   DUEL (1 VS 1)   ====================
# ======================================================

def duel(a, b, final_round=False, verbose=False):
    """
    Performs a full duel with all tiebreakers.
    verbose=True → returns string with printable explanation.
    Returns:
        winner ('a', 'b' or 'tie'),
        log (string explanation)
    """
    log = []
    # --- Base stats ---
    pa, pb = score_base_stats(a, b)
    log.append(f"Base stats: {pa}-{pb}")

    # If decided here, done
    if pa != pb:
        log.append(f"Result decided by base stats → winner: {a['nombre'] if pa>pb else b['nombre']}")
        return ("a" if pa > pb else "b"), "\n".join(log)

    # --- Tiebreaker: media ---
    if a["media"] > b["media"]:
        pa += 1
        log.append(f"Media: {a['media']} vs {b['media']} → +1 for {a['nombre']}")
        return "a", "\n".join(log)
    elif a["media"] < b["media"]:
        pb += 1
        log.append(f"Media: {a['media']} vs {b['media']} → +1 for {b['nombre']}")
        return "b", "\n".join(log)
    else:
        log.append("Media: tie")

    # --- Tiebreaker: atq2-def ---
    d1 = diff_atq2_def(a, b)
    d2 = diff_atq2_def(b, a)
    if d1 > d2:
        log.append(f"Atq2-Def: {a['nombre']} wins ({d1}>{d2})")
        return "a", "\n".join(log)
    elif d1 < d2:
        log.append(f"Atq2-Def: {b['nombre']} wins ({d2}>{d1})")
        return "b", "\n".join(log)
    else:
        log.append("Atq2-Def: tie")

    # --- Tiebreaker: atq1-def ---
    d1 = diff_atq1_def(a, b)
    d2 = diff_atq1_def(b, a)
    if d1 > d2:
        log.append(f"Atq1-Def: {a['nombre']} wins ({d1}>{d2})")
        return "a", "\n".join(log)
    elif d1 < d2:
        log.append(f"Atq1-Def: {b['nombre']} wins ({d2}>{d1})")
        return "b", "\n".join(log)
    else:
        log.append("Atq1-Def: tie")

    # --- Tiebreaker: type ---
    if type_beats(a, b):
        log.append(f"Type advantage: {a['tipo']} > {b['tipo']} → winner: {a['nombre']}")
        return "a", "\n".join(log)
    elif type_beats(b, a):
        log.append(f"Type advantage: {b['tipo']} > {a['tipo']} → winner: {b['nombre']}")
        return "b", "\n".join(log)
    else:
        log.append("Type: tie")

    # --- Ultra tie ---
    if final_round:
        log.append("Ultra tie in FINAL → both are champions")
    else:
        log.append("Ultra tie → both advance")

    return "tie", "\n".join(log)


# ======================================================
# ===============   TRIPLE BATTLE   ====================
# ======================================================

def triple_battle(d1, d2, d3, final_round=False):
    """
    Round-robin fight among 3 digimon.
    Returns winners list + explanation log.
    """
    log = []
    points = {"d1": 0, "d2": 0, "d3": 0}

    # Each pair duel
    r12, log12 = duel(d1, d2, verbose=True)
    r13, log13 = duel(d1, d3, verbose=True)
    r23, log23 = duel(d2, d3, verbose=True)

    log.append("Fight 1: " + d1["nombre"] + " vs " + d2["nombre"])
    log.append(log12)
    log.append("-------------------------")

    if r12 == "a": points["d1"] += 1
    elif r12 == "b": points["d2"] += 1

    log.append("Fight 2: " + d1["nombre"] + " vs " + d3["nombre"])
    log.append(log13)
    log.append("-------------------------")

    if r13 == "a": points["d1"] += 1
    elif r13 == "b": points["d3"] += 1

    log.append("Fight 3: " + d2["nombre"] + " vs " + d3["nombre"])
    log.append(log23)
    log.append("-------------------------")

    if r23 == "a": points["d2"] += 1
    elif r23 == "b": points["d3"] += 1

    # Determine winners
    maxp = max(points.values())
    winners = []
    mapping = {"d1": d1, "d2": d2, "d3": d3}

    for key, val in points.items():
        if val == maxp:
            winners.append(mapping[key])

    # Explanatory line
    log.append(f"Triple scores: {d1['nombre']}={points['d1']}, "
               f"{d2['nombre']}={points['d2']}, "
               f"{d3['nombre']}={points['d3']}")

    if len(winners) == 1:
        log.append("Winner: " + winners[0]["nombre"])
    else:
        if final_round:
            log.append("Final triple tie → all are champions")
        else:
            log.append("Tie → multiple digimon advance")

    return winners, "\n".join(log)


# ======================================================
# ===============   TOURNAMENT LOGIC   ================
# ======================================================

def run_tournament(digimon):
    """
    Runs a full tournament, returns champions and detailed log.
    """
    log = []
    participants = digimon[:]
    round_number = 1

    while len(participants) > 1:
        n = len(participants)
        log.append("\n" + "="*50)
        log.append(f"==============   ROUND {round_number}   ==============")
        log.append("="*50)

        random.shuffle(participants)
        log.append(f"Participants: {', '.join(d['nombre'] for d in participants)}")

        new_round = []
        idx = 0

        # Triple if odd
        if n % 2 == 1:
            log.append("\n--- Triple battle ---")
            w, ltxt = triple_battle(participants[0], participants[1], participants[2],
                                    final_round=(n == 3))
            log.append(ltxt)
            new_round.extend(w)
            idx = 3

        # Duels
        while idx < n:
            if idx == n-1:
                break

            a = participants[idx]
            b = participants[idx+1]

            log.append(f"\n--- Duel: {a['nombre']} vs {b['nombre']} ---")
            result, ltxt = duel(a, b, final_round=(n == 2), verbose=True)
            log.append(ltxt)

            if result == "a":
                new_round.append(a)
            elif result == "b":
                new_round.append(b)
            else:
                # Ultra tie
                if n == 2:
                    # Final → both champions
                    return [a, b], "\n".join(log)
                else:
                    new_round.extend([a, b])

            idx += 2

        participants = new_round
        round_number += 1

    # Single champion
    return [participants[0]], "\n".join(log)


# ======================================================
# ===============   MULTI-TOURNAMENT   ================
# ======================================================

def run_multiple(csv_file, repeats=10):
    """
    Runs multiple tournaments and returns a palmares dict and full log.
    """
    all_digimon = load_digimon(csv_file)
    allowed_levels = choose_levels(all_digimon)
    digimon = [d for d in all_digimon if d["nivel"] in allowed_levels]

    palmares = defaultdict(int)
    full_log = []

    for i in range(1, repeats+1):
        full_log.append("\n" + "#"*60)
        full_log.append(f"################   TOURNAMENT {i}   ################")
        full_log.append("#"*60)

        winners, log = run_tournament(digimon)
        full_log.append(log)
        full_log.append("\nWinners of this tournament:")
        for w in winners:
            full_log.append(" - " + w["nombre"])
            palmares[w["nombre"]] += 1

    return palmares, "\n".join(full_log)


# ======================================================
# ===============   FULL RANKING MODE   ================
# ======================================================

def run_full_ranking(csv_file, repeats=10):
    """
    Runs full ranking mode:
    Each cycle:
        - Runs 10 tournaments with the current remaining Digimon
        - Determines the champion (highest wins)
        - Removes champion from the pool
        - Repeats until no digimon remain

    Returns:
        ranking (list of digimon names in order from strongest to weakest)
        full_logs (combined logs of all blocks)
    """
    all_digimon = load_digimon(csv_file)
    allowed_levels = choose_levels(all_digimon)
    remaining = [d for d in all_digimon if d["nivel"] in allowed_levels]

    ranking = []
    all_logs = []

    block_number = 1

    while len(remaining) > 0:
        all_logs.append("\n" + "#"*70)
        all_logs.append(f"##############   FULL RANKING BLOCK {block_number}   ##############")
        all_logs.append("#"*70)

        # Run tournaments only with the remaining Digimon
        palmares = defaultdict(int)
        block_logs = []

        for i in range(1, repeats+1):
            block_logs.append("\n" + "-"*60)
            block_logs.append(f"-------------   BLOCK {block_number} – TOURNAMENT {i}   -------------")
            block_logs.append("-"*60)

            winners, logs = run_tournament(remaining)
            block_logs.append(logs)
            block_logs.append("\nWinners:")
            for w in winners:
                block_logs.append(" - " + w["nombre"])
                palmares[w["nombre"]] += 1

        # Determine champion of the block
        champion_name = max(palmares.items(), key=lambda x: x[1])[0]
        ranking.append(champion_name)

        # Log the block winner
        all_logs.append("\nPalmarés for this block:")
        for name, wins in sorted(palmares.items(), key=lambda x: -x[1]):
            all_logs.append(f"{name}: {wins}")

        all_logs.append(f"\nChampion of block {block_number}: {champion_name}")
        all_logs.extend(block_logs)

        # Remove champion from remaining pool
        remaining = [d for d in remaining if d["nombre"] != champion_name]

        block_number += 1

    return ranking, "\n".join(all_logs)



# ======================================================
# ===============   MAIN   =============================
# ======================================================

if __name__ == "__main__":
    mode = choose_tournament_mode()

    if mode == 1:
        palmares, logs = run_multiple("datos_digimon_todos.csv", repeats=10)

        print("\nFINAL PALMARÉS:")
        for name, wins in sorted(palmares.items(), key=lambda x: -x[1]):
            print(name, wins)

        # print("\n===== FULL TOURNAMENT LOG =====\n")
        # print(logs)

    else:
        ranking, logs = run_full_ranking("datos_digimon_todos.csv", repeats=10)

        print("\n======== GLOBAL RANKING (STRONGEST → WEAKEST) ========")
        for i, name in enumerate(ranking, 1):
            print(f"{i}. {name}")

        # print("\n===== FULL RANKING MODE LOG =====\n")
        # print(logs)



    # If you want to save logs to a file:
    with open("logs.txt","w",encoding="utf-8") as f:
        f.write(logs)