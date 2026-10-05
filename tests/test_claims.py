"""Jede Zahl, die README, Hilfetexte und Beispieltexte nennen, ist hier belegt (Stadtgitter 8 x 8, 6 Zonen, Last 1,0, Seed 5, feste Netze ab Seed 100000).
Die Rechnung nutzt nur + - * / auf Python-Zahlen: Iterationszahlen sind auf allen Plattformen dieselben (Bänder von wenigen Iterationen trotzdem gegen Rundungsunterschiede);
Mittel über Netze werden mit Bändern geprüft."""

import pytest

import fw_algorithm as al
import fw_constants as C
import fw_evaluation as ev

P = ev.DEFAULT_PARAMS


def _run(name):
    p = C.PRESETS[name]
    params = ev.Params(p["net"], p["side"], p["zones"], p["load"], p["mode"], p["method"], p["iterations"], p["seed"])
    a = ev.analyse(params)
    return params, a["net"], a["result"]


def _its(r, tols=(1e-2, 1e-3, 1e-4, 1e-5)):
    return [r.first_below(t) for t in tols]


def _close(got, want, band=2):
    assert len(got) == len(want) and all((g is None and w is None) or (g is not None and w is not None and abs(g - w) <= (0 if w <= 5 else band)) for g, w in zip(got, want)), (got, want)


def test_the_default_grid_and_the_endspurt():
    """8 x 8 Kreuzungen, 224 Kanten, 6 Zonen, 30 Zonenpaare, 6 Kürzeste-Wege-Läufe je Iteration. Frank-Wolfe mit exakter Schrittweite: Lücke unter 1e-2 nach 4, 1e-3 nach 21, 1e-4 nach 102 Iterationen, 1e-5 in 200 nicht;
    Preis der Anarchie 1,040 (Gesamtfahrzeit 6 897 gegen 6 632)."""
    params, net, r = _run("🏙️ Stadtgitter")
    assert (net.m, len(net.zones), len(net.demand), len(net.origins())) == (224, 6, 30, 6)
    _close(_its(r), [4, 21, 102, None])
    assert r.iterations == 200 and r.gaps[-1] == pytest.approx(5.8e-5, rel=0.1) and r.runs == 202 * 6          # Start + 200 Iterationen + Schlusslücke, je 6 Läufe
    pa = ev.poa(params)
    assert pa["poa"] == pytest.approx(1.040, abs=0.001) and pa["ue"].tstt[-1] == pytest.approx(6897, abs=1) and pa["so"].tstt[-1] == pytest.approx(6632, abs=1)


def test_the_three_step_sizes():
    """Iterationen bis 1e-2 / 1e-3 / 1e-4 / 1e-5: exakte Schrittweite 4 / 21 / 102 / -, MSA 7 / 57 / - / -, konjugiert 4 / 15 / 24 / 69 (fertig, Lücke unter 1e-6, nach 145 Iterationen).
    Lücke am Ende: MSA 2,9e-4, exakte Suche 5,8e-5; feste Schrittweite 0,5: 4,2e-2, Gesamtfahrzeit 7 275."""
    _, _, fw = _run("🏙️ Stadtgitter")
    _, _, msa = _run("🐢 Nur MSA")
    _, _, cfw = _run("🔗 Konjugiert")
    _, _, fixed = _run("🧪 Fester Schritt")
    _close(_its(msa), [7, 57, None, None])
    _close(_its(cfw), [4, 15, 24, 69])
    assert abs(cfw.iterations - 145) <= 3 and cfw.gaps[-1] < 1e-6
    assert msa.gaps[-1] == pytest.approx(2.9e-4, rel=0.1) and fw.gaps[-1] == pytest.approx(5.8e-5, rel=0.1)
    assert fixed.gaps[-1] == pytest.approx(4.2e-2, rel=0.1) and fixed.tstt[-1] == pytest.approx(7275, abs=5) and fixed.first_below(1e-2) is None
    assert fw.tstt[-1] == pytest.approx(6898, abs=1) and msa.tstt[-1] == pytest.approx(6898, abs=1)


def test_load_presets():
    """Doppelte Last: 1e-2 nach 35 Iterationen, 1e-3 in 200 nicht (Lücke am Ende 1,3e-3), höchste Auslastung 224 %, Preis der Anarchie 1,100; halbe Last: 1e-3 nach 1, 1e-4 nach 5, 1e-5 nach 43, Preis der Anarchie 1,013."""
    params, net, r = _run("🚗 Hohe Last")
    _close(_its(r), [35, None, None, None])
    assert r.gaps[-1] == pytest.approx(1.3e-3, rel=0.15) and max(al.utilization(net, r.x)) == pytest.approx(2.24, abs=0.02) and ev.poa(params)["poa"] == pytest.approx(1.100, abs=0.002)
    lparams, _, lr = _run("🌙 Niedrige Last")
    _close(_its(lr), [0, 1, 5, 43])
    assert ev.poa(lparams)["poa"] == pytest.approx(1.013, abs=0.001)


def test_system_optimum_preset():
    """Systemoptimum: nach 200 Iterationen Gesamtfahrzeit 6 634 (Gleichgewicht 6 897), höchste Auslastung 127 % (Gleichgewicht 169 %)."""
    _, net, so = _run("🌐 Systemoptimum")
    _, _, ue = _run("🏙️ Stadtgitter")
    assert so.tstt[-1] == pytest.approx(6634, abs=2) and ue.tstt[-1] == pytest.approx(6898, abs=1)
    assert max(al.utilization(net, so.x)) == pytest.approx(1.27, abs=0.01) and max(al.utilization(net, ue.x)) == pytest.approx(1.69, abs=0.01)


def test_pigou_preset_numbers():
    """Pigou: Gleichgewicht 0 Iterationen, Fahrzeit 1; Systemoptimum 0,75; Preis der Anarchie 4/3."""
    params, net, r = _run("🛣️ Pigou-Netz")
    assert r.iterations == 0 and al.tstt(net, r.x) == 1.0
    pa = ev.poa(params)
    assert pa["so"].tstt[-1] == pytest.approx(0.75, abs=1e-6) and pa["poa"] == pytest.approx(4 / 3, abs=1e-4)


def test_accuracy_needed():
    """Fehler der Gesamtfahrzeit / größter Kantenflussfehler (Anteil der Nachfrage), wenn Frank-Wolfe erstmals unter die Lücke fällt: 1e-2 (Iteration 4): 1,6 % / 2,0 %; 1e-3 (21): 0,07 % / 0,45 %; 1e-4 (102): 0,015 % / 0,07 %."""
    rows = ev.accuracy(P)
    assert [r["iteration"] for r in rows][0] == 4 and abs(rows[1]["iteration"] - 21) <= 2 and abs(rows[2]["iteration"] - 102) <= 3
    assert rows[0]["tstt_error"] == pytest.approx(0.0158, abs=0.001) and rows[0]["flow_error"] == pytest.approx(0.0200, abs=0.001)
    assert rows[1]["tstt_error"] == pytest.approx(0.0007, abs=0.0002) and rows[1]["flow_error"] == pytest.approx(0.0045, abs=0.0007)
    assert rows[2]["tstt_error"] == pytest.approx(0.00015, abs=0.00005) and rows[2]["flow_error"] == pytest.approx(0.00074, abs=0.0002)
    assert all(a["flow_error"] >= b["flow_error"] for a, b in zip(rows, rows[1:]))


def test_link_flows_are_unique():
    """Frank-Wolfe (1 500 Iterationen) und konjugiertes Frank-Wolfe (bis Lücke 1e-9) enden bei denselben Kantenflüssen: größte Abweichung 0,004 % der Nachfrage."""
    u = ev.uniqueness(P)
    assert u["max_diff"] < 1e-4 and u["gap_a"] < 1e-8


def test_the_endspurt_grows_with_the_load():
    """Iterationen bis 1e-2 / 1e-3 / 1e-4 (Frank-Wolfe, Mittel über 5 Netze, nicht erreicht = 301): Last 0,5: 0,6 / 2,0 / 4,2; 1,0: 3,4 / 23,6 / 218; 1,5: 13,2 / 117 / 301; 2,0: 29,2 / 249 / 301;
    3,0: 78 / 301 / 301. Preis der Anarchie (Mittel): 1,005 / 1,026 / 1,056 / 1,066 / 1,065; größter 1,011 / 1,041 / 1,107 / 1,091 / 1,115."""
    rows = {r["load"]: r for r in ev.load_series(P)}
    assert rows[5]["its"][1e-3] == pytest.approx(2.0, abs=0.6) and rows[10]["its"][1e-2] == pytest.approx(3.4, abs=1.0) and rows[10]["its"][1e-3] == pytest.approx(23.6, abs=4)
    assert rows[15]["its"][1e-3] == pytest.approx(117, abs=20) and rows[20]["its"][1e-3] == pytest.approx(249, abs=30) and rows[30]["its"][1e-2] == pytest.approx(78, abs=12)
    assert rows[10]["its"][1e-4] == pytest.approx(218, abs=40) and rows[15]["its"][1e-4] == 301 and rows[30]["its"][1e-3] == 301
    assert [round(rows[l]["poa_mean"], 3) for l in (5, 10, 15, 20, 30)] == pytest.approx([1.005, 1.026, 1.056, 1.066, 1.065], abs=0.004)
    assert max(r["poa_max"] for r in rows.values()) == pytest.approx(1.115, abs=0.006) and all(r["poa_max"] < 4 / 3 for r in rows.values())
    its = [rows[l]["its"][1e-3] for l in (5, 10, 15, 20, 30)]
    assert its == sorted(its)


@pytest.fixture(scope="module")
def dist():
    return ev.distribution(P)


def test_conjugate_versus_the_others_over_forty_nets(dist):
    """40 feste Netze (200 Iterationen, nicht erreicht = 201): Iterationen bis 1e-3: Frank-Wolfe 35,3, MSA 55,3, konjugiert 13,3; bis 1e-4: 159, 183, 37; Lücke 1e-4 nicht erreicht in 22 / 31 / 0 von 40 Netzen;
    mittlere Lücke nach 100 Iterationen 4e-4 / 6e-4 / 5e-5. (Vor der Korrektur des Deckels alpha <= 1 - delta: 22,6 / 70 / 8 / 2e-4.)"""
    assert dist["n"] == 40
    assert dist["fw_its3"] == pytest.approx(35.3, abs=3) and dist["msa_its3"] == pytest.approx(55.3, abs=4) and dist["cfw_its3"] == pytest.approx(13.3, abs=2)
    assert dist["fw_its4"] == pytest.approx(159, abs=8) and dist["msa_its4"] == pytest.approx(183, abs=8) and dist["cfw_its4"] == pytest.approx(37, abs=6)
    assert (dist["fw_missed"], dist["msa_missed"], dist["cfw_missed"]) == pytest.approx((22, 31, 0), abs=2)
    assert dist["fw_gap100"] == pytest.approx(4e-4, rel=0.4) and dist["msa_gap100"] == pytest.approx(6e-4, rel=0.4) and dist["cfw_gap100"] == pytest.approx(5e-5, rel=0.5)
    assert dist["cfw_its4"] < dist["fw_its4"] < dist["msa_its4"]


def test_the_conjugate_variant_is_not_better_in_every_net(dist):
    """Nicht in jedem Netz: in 2 der 40 Netze erreicht das konjugierte Verfahren 1e-3 später als die Schrittweitensuche (7 statt 5, 11 statt 8), nie aber gar nicht."""
    worse = [r for r in dist["rows"] if r["fw"]["its3"] is not None and (r["cfw"]["its3"] is None or r["cfw"]["its3"] > r["fw"]["its3"])]
    assert 1 <= len(worse) <= 4 and all(r["cfw"]["its3"] is not None for r in dist["rows"])
