"""Szenario (Gitter, Zonen, Nachfrage, Zufallsstrom) und Auswertung (Vergleich, Genauigkeit, Verteilungen)."""

import pytest

import fw_algorithm as al
import fw_constants as C
import fw_evaluation as ev
import fw_scenario as sc

P = ev.DEFAULT_PARAMS


def test_generation_is_deterministic_and_seed_dependent():
    a, b, c = sc.generate(6, 5, 10, 5), sc.generate(6, 5, 10, 5), sc.generate(6, 5, 10, 6)
    assert a == b and a != c


def test_grid_structure():
    """8 x 8 Kreuzungen: 2 * (7 * 8 + 8 * 7) = 224 Kanten, beide Richtungen einer Straße gleich; 6 Zonen, 30 geordnete Zonenpaare, 6 Ursprünge."""
    n = sc.generate(8, 6, 10, 5)
    assert n.n == 64 and n.m == 224 and len(n.zones) == 6 == len(set(n.zones)) and len(n.demand) == 30 and len(n.origins()) == 6
    pairs = {}
    for u, v, a, b, c, p in n.links:
        pairs.setdefault((min(u, v), max(u, v)), []).append((a, b, c, p))
    assert all(len(v) == 2 and v[0] == v[1] for v in pairs.values())
    assert all(2 <= l[2] <= 6 and 20 <= l[4] <= 45 and l[5] == 4 and l[3] == pytest.approx(0.15 * l[2]) for l in n.links)


def test_load_changes_only_the_demand():
    a, b = sc.generate(6, 5, 10, 5), sc.generate(6, 5, 20, 5)
    assert a.links == b.links and a.zones == b.zones and [(o, d) for o, d, _ in a.demand] == [(o, d) for o, d, _ in b.demand]
    assert all(q2 == pytest.approx(2 * q1) for (_, _, q1), (_, _, q2) in zip(a.demand, b.demand))


def test_demand_between_all_zone_pairs():
    n = sc.generate(6, 4, 10, 5)
    assert len(n.demand) == 4 * 3 and all(5 <= q <= 15 for _, _, q in n.demand)


def test_lessons_and_build_dispatch():
    assert set(sc.LESSONS) == set(C.FIXED_NETS) and sc.build("pigou", 9, 9, 9, 9).m == 2
    assert sc.build("grid", 6, 5, 10, 5) == sc.generate(6, 5, 10, 5)


def test_strongly_connected_so_every_pair_has_a_path():
    n = sc.generate(6, 5, 10, 5)
    y, _, _ = al.all_or_nothing(n, [1.0] * n.m)
    assert sum(y) > 0 and all(v >= 0 for v in y)


def test_analyse_and_compare_shapes():
    a = ev.analyse(P._replace(iterations=30))
    assert a["result"].iterations <= 30 and a["net"].m == 224
    c = ev.compare(P._replace(iterations=40))
    assert set(c["results"]) == {"fw", "msa", "cfw"} and set(c["table"]) == {"fw", "msa", "cfw"} and all(len(v) == 4 for v in c["table"].values())


def test_accuracy_rows_shrink_with_the_gap():
    rows = ev.accuracy(P._replace(side=5, zones=4))
    reached = [r for r in rows if r["iteration"] is not None]
    assert len(reached) >= 2 and reached[0]["tstt_error"] >= reached[-1]["tstt_error"] and reached[0]["iteration"] <= reached[-1]["iteration"]


def test_poa_is_at_least_one_and_pigou_is_four_thirds():
    assert ev.poa(P._replace(side=5, zones=4))["poa"] >= 1.0
    assert ev.poa(P._replace(net="pigou"))["poa"] == pytest.approx(4 / 3, abs=1e-4)


def test_distribution_shapes():
    d = ev.distribution(P._replace(side=5, zones=4), seeds=C.SWEEP_SEEDS[:3], max_iter=60)
    assert d["n"] == 3 and d["fw_its3"] > 0 and 0 <= d["fw_missed"] <= 3


def test_load_series_rows():
    rows = ev.load_series(P._replace(side=5, zones=4), loads=(5, 15), seeds=C.LOAD_SEEDS[:2], max_iter=60)
    assert [r["load"] for r in rows] == [5, 15] and rows[0]["its"][1e-2] <= rows[1]["its"][1e-2] and all(r["poa_mean"] >= 1.0 for r in rows)
