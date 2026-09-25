"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "Frank-Wolfe: wohin fährt der Verkehr - und warum dauert der Endspurt so lang?"."""

# --- Regler ---------------------------------------------------------------------------------------------------------------------
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 4, 10, 8            # Kantenlänge des Stadtgitters (Kreuzungen)
ZONES_MIN, ZONES_MAX, DEFAULT_ZONES = 3, 10, 6         # Zonen mit Nachfrage
LOAD_MIN, LOAD_MAX, DEFAULT_LOAD = 5, 30, 10           # Lastfaktor in Zehnteln (1,0 = Standard), Schritt 5
DEFAULT_SEED = 5
SEED_MAX = 2_000_000_000

NETS = {
    "grid": "Stadtgitter mit Zonen",
    "pigou": "Pigou-Netz (zwei parallele Straßen)",
    "zweistufen": "Zwei Stufen (Wege nicht eindeutig)",
}
DEFAULT_NET = "grid"
FIXED_NETS = ("pigou", "zweistufen")
MODES = {"ue": "Nutzergleichgewicht (jeder wählt den schnellsten Weg)", "so": "Systemoptimum (kleinste Gesamtfahrzeit)"}
DEFAULT_MODE = "ue"
METHODS = {"fw": "Frank-Wolfe (exakte Schrittweite)", "msa": "Frank-Wolfe mit Schritt 1/(k+1) (MSA)", "cfw": "Konjugiertes Frank-Wolfe", "fixed": "Fester Schritt 0,5 (Negativkontrolle)"}
DEFAULT_METHOD = "fw"
ITERATIONS = (100, 200, 400)
DEFAULT_ITERATIONS = 200
TOLS = (1e-2, 1e-3, 1e-4, 1e-5)

# --- feste Seed-Mengen (dieselben wie in den Flussdemos; unabhängig vom Nutzer-Seed) ---------------------------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
LOAD_SEEDS = DIST_SEEDS[:5]
LOADS = (5, 10, 15, 20, 30)

COLORS = {"fw": "#1f77b4", "msa": "#2ca02c", "cfw": "#d62728", "fixed": "#8c8c8c", "ue": "#1f77b4", "so": "#d62728", "zone": "#ff7f0e", "node": "#111111"}

# --- Presets -----------------------------------------------------------------------------------------------------------------
_BASE = dict(net=DEFAULT_NET, side=DEFAULT_SIDE, zones=DEFAULT_ZONES, load=DEFAULT_LOAD, mode=DEFAULT_MODE, method=DEFAULT_METHOD, iterations=DEFAULT_ITERATIONS, seed=DEFAULT_SEED)
PRESETS = {
    "🏙️ Stadtgitter": {**_BASE},
    "🚗 Hohe Last": {**_BASE, "load": 20},
    "🌙 Niedrige Last": {**_BASE, "load": 5},
    "🐢 Nur MSA": {**_BASE, "method": "msa"},
    "🔗 Konjugiert": {**_BASE, "method": "cfw"},
    "🌐 Systemoptimum": {**_BASE, "mode": "so"},
    "🛣️ Pigou-Netz": {**_BASE, "net": "pigou"},
    "🧪 Fester Schritt": {**_BASE, "method": "fixed"},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py belegt (Lehrnetze von Hand, Stadtgitter über die Seeds der Presets)
PRESET_HELP = {
    "🏙️ Stadtgitter": "8 × 8 Kreuzungen (224 Kanten), 6 Zonen, 30 Zonenpaare: Frank-Wolfe mit exakter Schrittweite unterschreitet die relative Lücke 1e-2 nach 4, 1e-3 nach 21 und 1e-4 nach 102 Iterationen; 1e-5 wird in 200 nicht erreicht. Preis der Anarchie 1,040 (Gesamtfahrzeit 6 897 gegen 6 632 im Systemoptimum).",
    "🚗 Hohe Last": "Doppelte Nachfrage: schon 1e-2 braucht 35 Iterationen, 1e-3 wird in 200 nicht erreicht (Lücke am Ende 1,3e-3); die höchste Auslastung einer Kante liegt bei 224 %. Preis der Anarchie 1,100.",
    "🌙 Niedrige Last": "Halbe Nachfrage: 1e-3 nach 1 und 1e-4 nach 5 Iterationen, 1e-5 nach 43 - der Verkehr staut sich kaum, der Endspurt ist kurz. Preis der Anarchie 1,013.",
    "🐢 Nur MSA": "Schrittweite 1/(k+1) statt Suche: 1e-2 nach 7, 1e-3 nach 57 Iterationen, 1e-4 in 200 nicht (Lücke am Ende 2,9e-4, die Suche erreicht 5,8e-5). Dieselbe Gesamtfahrzeit wie die Suche (6 898), aber mehr Iterationen bis zur gleichen Genauigkeit.",
    "🔗 Konjugiert": "Konjugiertes Frank-Wolfe: 1e-2 nach 4, 1e-3 nach 15, 1e-4 nach 24 und 1e-5 nach 69 Iterationen, fertig (Lücke unter 1e-6) nach 145 - mit der Suche braucht 1e-4 dagegen 102 Iterationen.",
    "🌐 Systemoptimum": "Dieselben Zonen, aber die Grenzkosten als Kosten: die Gesamtfahrzeit fällt nach 200 Iterationen auf 6 634 (Nutzergleichgewicht 6 897), die höchste Auslastung sinkt von 169 % auf 127 %. Der Löser ist derselbe, nur die Kosten sind andere.",
    "🛣️ Pigou-Netz": "Zwei parallele Straßen, eine mit fester Fahrzeit 1, eine mit Fahrzeit gleich der Verkehrsmenge; Nachfrage 1. Nutzergleichgewicht: alle fahren die zweite Straße, Fahrzeit 1 (Alles-oder-nichts trifft es sofort, 0 Iterationen). Systemoptimum: halb und halb, 0,75. Preis der Anarchie 4/3.",
    "🧪 Fester Schritt": "Schritt 0,5 in jeder Iteration: die relative Lücke bleibt bei 4,2e-2 hängen und die Gesamtfahrzeit bei 7 275 (5,5 % über dem Gleichgewicht) - der Verkehr springt zwischen zwei Zuständen hin und her. Frank-Wolfe braucht eine fallende oder gesuchte Schrittweite.",
}
