"""Orakel: Verkehrsumlegung gegen unabhängige Rechenwege. (1) Die relative Lücke jeder Iteration wird mit networkx-Dijkstra (nicht mit dem Alles-oder-nichts der Demo)
nachgerechnet, die Zielfunktion mit numerischer Quadratur, Flusserhaltung je Knoten. (2) Das Optimum (Nutzergleichgewicht und Systemoptimum) wird pfadbasiert mit scipy
(SLSQP über alle einfachen Wege, Zielfunktion per Quadratur) gelöst und mit Frank-Wolfe und konjugiertem Frank-Wolfe verglichen: Zielfunktion und Kantenflüsse.
(3) Regression: das konjugierte Verfahren darf nicht stehen bleiben (Netze, auf denen der Deckel alpha <= 1 - delta die Lücke für immer bei 3e-3 bis 6e-3 hielt). Schnell (< 10 s)."""

import networkx as nx
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.optimize import minimize

import fw_algorithm as al
import fw_scenario as sc


def _cost(link, x, mode):
    _, _, a, b, c, p = link
    return a + b * (x / c) ** p if mode == "ue" else a + b * (p + 1) * (x / c) ** p


def _objective(net, x, mode):
    if mode == "so":
        return sum(x[k] * _cost(l, x[k], "ue") for k, l in enumerate(net.links))
    return sum(quad(lambda s, l=l: _cost(l, s, "ue"), 0, x[k])[0] for k, l in enumerate(net.links))


def _gap(net, x, mode):
    graph = nx.DiGraph()
    for k, l in enumerate(net.links):
        w = _cost(l, x[k], mode)
        if not graph.has_edge(l[0], l[1]) or graph[l[0]][l[1]]["w"] > w:
            graph.add_edge(l[0], l[1], w=w)
    sx = sum(x[k] * _cost(l, x[k], mode) for k, l in enumerate(net.links))
    sy = sum(q * nx.single_source_dijkstra_path_length(graph, o, weight="w")[d] for o, d, q in net.demand)
    return (sx - sy) / sx


def _path_solution(net, mode):
    """Optimale Kantenflüsse pfadbasiert: Wegeflüsse h >= 0 über alle einfachen Wege je Zonenpaar, SLSQP."""
    graph = nx.DiGraph()
    for k, l in enumerate(net.links):
        graph.add_edge(l[0], l[1], k=k)
    cols, owner = [], []
    for i, (o, d, _) in enumerate(net.demand):
        for path in nx.all_simple_paths(graph, o, d):
            v = np.zeros(net.m)
            for u, w in zip(path, path[1:]):
                v[graph[u][w]["k"]] = 1
            cols.append(v)
            owner.append(i)
    mat, scale = np.array(cols).T, np.mean([q for *_, q in net.demand])
    eq = np.zeros((len(net.demand), len(owner)))
    for j, i in enumerate(owner):
        eq[i, j] = 1
    q = np.array([t[2] for t in net.demand]) / scale
    f = lambda h: _objective(net, mat @ h * scale, mode) / scale ** 2
    g = lambda h: mat.T @ np.array([_cost(l, (mat @ h * scale)[k], mode) for k, l in enumerate(net.links)]) / scale
    h0 = np.array([q[i] / owner.count(i) for i in owner])
    res = minimize(f, h0, jac=g, method="SLSQP", bounds=[(0, None)] * len(owner), constraints=[{"type": "eq", "fun": lambda h: eq @ h - q, "jac": lambda h: eq}], options={"maxiter": 1000, "ftol": 1e-15})
    return mat @ res.x * scale


def test_iteration_by_iteration_gap_objective_and_balance_against_independent_computation():
    for side, zones, load, seed in ((2, 3, 10, 11), (3, 3, 15, 5), (3, 4, 20, 77)):
        net = sc.generate(side, zones, load, seed)
        supply = np.zeros(net.n)
        for o, d, q in net.demand:
            supply[o] += q
            supply[d] -= q
        for mode in al.MODES:
            for method in al.METHODS:
                res = al.assign(net, mode, method, 40, 1e-9)
                for k in range(0, len(res.flows), 5):
                    x = res.flows[k]
                    if k < len(res.gaps):
                        assert res.gaps[k] == pytest.approx(_gap(net, x, mode), abs=1e-9)
                    assert res.objective[k] == pytest.approx(_objective(net, x, mode), rel=1e-8)
                    balance = np.zeros(net.n)
                    for j, l in enumerate(net.links):
                        balance[l[0]] += x[j]
                        balance[l[1]] -= x[j]
                    assert np.abs(balance - supply).max() < 1e-8


def test_equilibrium_and_system_optimum_against_path_based_scipy():
    for side, zones, load, seed in ((2, 3, 15, 6), (3, 3, 10, 5), (3, 3, 20, 7)):
        net = sc.generate(side, zones, load, seed)
        for mode in al.MODES:
            ref = _path_solution(net, mode)
            for method in ("fw", "cfw"):
                res = al.assign(net, mode, method, 500, 1e-8)
                assert res.gaps[-1] < 1e-6 and _gap(net, res.x, mode) < 1e-6
                assert _objective(net, res.x, mode) == pytest.approx(_objective(net, ref, mode), rel=1e-5)
                assert np.abs(np.array(res.x) - ref).max() / net.total_demand() < 5e-3


@pytest.mark.parametrize("side,zones,load,seed,mode", [(3, 4, 20, 719603, "so"), (3, 4, 30, 455006, "so"), (3, 4, 20, 89472, "so"), (3, 4, 30, 97373, "ue"), (3, 4, 30, 455006, "ue")])
def test_conjugate_frank_wolfe_does_not_get_stuck(side, zones, load, seed, mode):
    net = sc.generate(side, zones, load, seed)
    res = al.assign(net, mode, "cfw", 400, 1e-6)
    assert res.gaps[-1] < 1e-4 and _gap(net, res.x, mode) < 1e-4
