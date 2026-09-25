"""Kern gegen Handrechnung und Gegenproben: Kostenfunktionen, Alles-oder-nichts, Wardrop-Bedingung, Monotonie, Grenzwerte der Verfahren, Systemoptimum = Gleichgewicht auf Grenzkosten, Kontrollen."""

import pytest

import fw_algorithm as al
import fw_evaluation as ev
import fw_scenario as sc

NET = sc.generate(6, 5, 10, 100000)


def test_cost_functions_by_hand():
    """BPR-Kante mit a = 4, b = 0,6, c = 20, p = 4 bei x = 10: Fahrzeit 4 + 0,6 * 0,5^4 = 4,0375; Grenzkosten 4 + 0,6 * 5 * 0,0625 = 4,1875; Integral 4 * 10 + 0,6 * 20 / 5 * 0,5^5 = 40,075."""
    link = (0, 1, 4.0, 0.6, 20.0, 4)
    assert al.time(link, 10.0) == pytest.approx(4.0375) and al.marginal(link, 10.0) == pytest.approx(4.1875) and al.integral(link, 10.0) == pytest.approx(40.075)
    assert al.time_deriv(link, 10.0) == pytest.approx(0.6 * 4 * 0.5 ** 3 / 20)


def test_derivatives_match_finite_differences():
    link = (0, 1, 3.0, 0.45, 25.0, 4)
    h = 1e-6
    for x in (0.0, 5.0, 20.0, 40.0):
        assert al.time_deriv(link, x) == pytest.approx((al.time(link, x + h) - al.time(link, x - h)) / (2 * h), abs=1e-6)
        assert al.integral(link, x + h) - al.integral(link, x - h) == pytest.approx(2 * h * al.time(link, x), abs=1e-6)
        assert al.marginal_deriv(link, x) == pytest.approx((al.marginal(link, x + h) - al.marginal(link, x - h)) / (2 * h), abs=1e-4)


def test_fast_coefficients_equal_the_generic_functions():
    co = al.Coefs(NET)
    x = [float(k % 9) * 2.5 for k in range(NET.m)]
    for mode in al.MODES:
        f = al.cost_fn(mode)[0]
        fast = co.costs(mode, x)
        assert all(fast[k] == pytest.approx(f(NET.links[k], x[k]), rel=1e-12) for k in range(NET.m))


def test_pigou_by_hand():
    """Nutzergleichgewicht: alles auf die zweite Straße, Fahrzeit 1, sofort (0 Iterationen); Systemoptimum: halb und halb, 0,75; Preis der Anarchie 4/3."""
    p = sc.pigou()
    ue = al.assign(p, "ue")
    assert ue.iterations == 0 and ue.x == (0.0, 1.0) and al.tstt(p, ue.x) == 1.0
    so = al.assign(p, "so", "fw", 100, 1e-9)
    assert so.x[0] == pytest.approx(0.5, abs=1e-6) and al.tstt(p, so.x) == pytest.approx(0.75, abs=1e-9)
    assert al.price_of_anarchy(p)[0] == pytest.approx(4 / 3, abs=1e-6)


def test_two_stages_by_hand():
    """Zwei Stufen, Nachfrage 10, gleiche parallele Straßen: jede Straße trägt 5 (die Kantenflüsse sind eindeutig)."""
    z = sc.two_stages()
    r = al.assign(z, "ue")
    assert all(v == pytest.approx(5.0) for v in r.x)


def test_two_stages_path_flows_are_not_unique():
    """Drei verschiedene Wegeaufteilungen (Straße 1 oder 2, dann Straße 3 oder 4), alle mit den Kantenflüssen 5 / 5 / 5 / 5."""
    def link_flows(paths):
        out = [0.0] * 4
        for (first, second), q in paths.items():
            out[first] += q
            out[second] += q
        return out
    a = {(0, 2): 5.0, (1, 3): 5.0}
    b = {(0, 3): 5.0, (1, 2): 5.0}
    c = {(0, 2): 2.5, (0, 3): 2.5, (1, 2): 2.5, (1, 3): 2.5}
    assert link_flows(a) == link_flows(b) == link_flows(c) == [5.0, 5.0, 5.0, 5.0] and a != b != c


def test_all_or_nothing_puts_each_pair_on_a_shortest_path_and_conserves_demand():
    cost = al.link_costs(NET, "ue", [0.0] * NET.m)
    y, scanned, runs = al.all_or_nothing(NET, cost)
    assert runs == len(NET.origins()) and scanned > 0
    bal = [0.0] * NET.n
    for k, (u, v, *_r) in enumerate(NET.links):
        bal[u] -= y[k]
        bal[v] += y[k]
    for o, d, q in NET.demand:
        bal[o] += q
        bal[d] -= q
    assert all(abs(b) < 1e-9 for b in bal)


@pytest.mark.parametrize("method", ("fw", "msa", "cfw"))
def test_objective_never_increases_for_the_line_search_methods(method):
    r = al.assign(NET, "ue", method, 60, 1e-9)
    if method != "msa":
        assert all(b <= a + 1e-9 for a, b in zip(r.objective, r.objective[1:]))
    assert r.gaps[-1] < r.gaps[0]


def test_flows_stay_feasible_and_gaps_are_non_negative():
    r = al.assign(NET, "ue", "cfw", 80, 1e-9)
    assert all(g >= -1e-12 for g in r.gaps) and all(v >= -1e-9 for x in r.flows for v in x)
    assert all(abs(sum(x) - sum(r.flows[0])) < 1e6 for x in r.flows)


@pytest.mark.parametrize("mode", al.MODES)
def test_all_methods_reach_the_same_link_flows(mode):
    """Frank-Wolfe, MSA und konjugiertes Frank-Wolfe enden (bei hoher Genauigkeit) bei denselben Kantenflüssen; die Kantenflüsse sind eindeutig."""
    net = sc.generate(5, 4, 10, 100003)
    ref = al.assign(net, mode, "cfw", 800, 1e-10)
    total = net.total_demand()
    for method in ("fw", "msa"):
        r = al.assign(net, mode, method, 1500, 1e-7)
        assert max(abs(r.x[k] - ref.x[k]) for k in range(net.m)) / total < 5e-4


def test_wardrop_condition_at_the_solution():
    """Im Gleichgewicht ist die Lücke einer neuen Alles-oder-nichts-Zuordnung (fast) 0: kein Zonenpaar spart durch einen Wechsel."""
    net = sc.generate(5, 4, 10, 100003)
    r = al.assign(net, "ue", "cfw", 800, 1e-9)
    assert ev.wardrop_check(net, r.x, "ue") < 1e-6


def test_system_optimum_is_the_equilibrium_on_marginal_costs():
    """Das Systemoptimum hat höchstens die Gesamtfahrzeit des Gleichgewichts (Preis der Anarchie >= 1), und seine Zielfunktion ist die Gesamtfahrzeit."""
    net = sc.generate(5, 4, 10, 100003)
    value, ue, so = al.price_of_anarchy(net, "cfw", 600, 1e-8)
    assert value >= 1.0 and so.tstt[-1] <= ue.tstt[-1] + 1e-6
    assert al.objective(net, "so", so.x) == pytest.approx(so.tstt[-1])


def test_constant_costs_need_one_all_or_nothing():
    """Ohne Kapazitätsabhängigkeit (b = 0) ist die Fahrzeit konstant: schon Alles-oder-nichts auf den Freifahrtzeiten ist das Gleichgewicht."""
    links = tuple((u, v, a, 0.0, c, p) for u, v, a, b, c, p in NET.links)
    flat = sc.Network(NET.n, NET.names, NET.pos, links, NET.zones, NET.demand, "grid", NET.side)
    r = al.assign(flat, "ue")
    assert r.iterations == 0 and r.gaps[0] == pytest.approx(0.0, abs=1e-12)


def test_fixed_step_does_not_converge_and_jumps():
    r = al.assign(NET, "ue", "fixed", 100, 1e-6)
    assert min(r.gaps) > 1e-4 and all(s == 0.5 for s in r.steps)
    good = al.assign(NET, "ue", "fw", 100, 1e-6)
    assert good.gaps[-1] < min(r.gaps)


def test_conjugate_variant_resets_when_it_has_no_descent():
    r = al.assign(NET, "ue", "cfw", 200, 1e-9)
    assert all(0.0 < s <= 1.0 for s in r.steps) and r.gaps[-1] < 1e-4


def test_first_below_and_counts():
    r = al.assign(NET, "ue", "fw", 50, 1e-9)
    k = r.first_below(1e-2)
    assert k is not None and r.gaps[k] < 1e-2 and all(g >= 1e-2 for g in r.gaps[:k])
    assert r.runs >= (r.iterations + 1) * len(NET.origins())
