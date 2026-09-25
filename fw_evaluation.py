"""Auswertung: Verfahren im Vergleich, Iterationen bis zur Lücke, Genauigkeit, Preis der Anarchie, Lastreihe, Verteilungen, Eindeutigkeit der Kantenflüsse.
Alle Zufallsnetze kommen aus festen Seeds (fw_constants), unabhängig vom Nutzer-Seed."""

import statistics
from collections import namedtuple

import fw_algorithm as al
import fw_constants as C
import fw_scenario as sc

Params = namedtuple("Params", "net side zones load mode method iterations seed")
DEFAULT_PARAMS = Params(C.DEFAULT_NET, C.DEFAULT_SIDE, C.DEFAULT_ZONES, C.DEFAULT_LOAD, C.DEFAULT_MODE, C.DEFAULT_METHOD, C.DEFAULT_ITERATIONS, C.DEFAULT_SEED)


def network(params):
    return sc.build(params.net, params.side, params.zones, params.load, params.seed)


def analyse(params):
    """Verkehrsumlegung mit dem gewählten Verfahren und dem gewählten Modus."""
    net = network(params)
    res = al.assign(net, params.mode, params.method, params.iterations, 1e-6)
    return dict(net=net, result=res)


def compare(params, methods=("fw", "msa", "cfw")):
    """Alle Verfahren auf demselben Netz und im selben Modus; Iterationen bis zur Lücke 1e-2 ... 1e-5."""
    net = network(params)
    out = {m: al.assign(net, params.mode, m, params.iterations, 1e-6) for m in methods}
    table = {m: [r.first_below(t) for t in C.TOLS] for m, r in out.items()}
    return dict(net=net, results=out, table=table)


def reference(net, mode="ue"):
    """Sehr genaue Lösung (konjugiertes Frank-Wolfe bis Lücke 1e-9) als Vergleichswert."""
    return al.assign(net, mode, "cfw", 800, 1e-9)


def accuracy(params, gaps=(1e-2, 1e-3, 1e-4), max_iter=600):
    """Wie genau muss man rechnen? Fehler der Gesamtfahrzeit und größter Kantenflussfehler (in Prozent der gesamten Nachfrage) gegen die Referenzlösung, wenn Frank-Wolfe die Lücke erstmals unterschreitet."""
    net = network(params)
    ref = reference(net, params.mode)
    res = al.assign(net, params.mode, "fw", max_iter, gaps[-1] / 10)
    total = net.total_demand()
    rows = []
    for g in gaps:
        k = res.first_below(g)
        if k is None:
            rows.append(dict(gap=g, iteration=None))
            continue
        x = res.flows[k]
        rows.append(dict(gap=g, iteration=k, tstt_error=abs(res.tstt[k] - ref.tstt[-1]) / ref.tstt[-1],
                         flow_error=max(abs(x[j] - ref.x[j]) for j in range(net.m)) / total))
    return rows


def poa_of(net, max_iter=300, tol=1e-6):
    """Preis der Anarchie: Gesamtfahrzeit im Nutzergleichgewicht geteilt durch die im Systemoptimum (beide mit konjugiertem Frank-Wolfe). Rückgabe (PoA, UE-Ergebnis, SO-Ergebnis)."""
    ue = al.assign(net, "ue", "cfw", max_iter, tol)
    so = al.assign(net, "so", "cfw", max_iter, tol)
    return ue.tstt[-1] / so.tstt[-1], ue, so


def poa(params, max_iter=300):
    net = network(params)
    value, ue, so = poa_of(net, max_iter)
    return dict(poa=value, ue=ue, so=so, net=net)


def load_series(params, loads=C.LOADS, seeds=C.LOAD_SEEDS, max_iter=300):
    """Iterationen bis Lücke 1e-2 ... 1e-4 (Frank-Wolfe mit exakter Schrittweite, Mittel über feste Netze; nicht erreicht = Iterationsgrenze + 1) und Preis der Anarchie je Lastfaktor."""
    rows = []
    for load in loads:
        its = {t: [] for t in C.TOLS[:3]}
        poas = []
        for seed in seeds:
            p = params._replace(load=load, seed=seed)
            net = network(p)
            res = al.assign(net, "ue", "fw", max_iter, 1e-4 / 10)
            for t in its:
                k = res.first_below(t)
                its[t].append(max_iter + 1 if k is None else k)
            poas.append(poa_of(net)[0])
        rows.append(dict(load=load, its={t: statistics.fmean(v) for t, v in its.items()}, poa_mean=statistics.fmean(poas), poa_max=max(poas)))
    return rows


def distribution(params, seeds=C.SWEEP_SEEDS, max_iter=200):
    """Über feste Netze mit den Einstellungen: Iterationen bis 1e-3 und 1e-4 je Verfahren (nicht erreicht = Grenze + 1), Lücke nach 100 Iterationen, Zahl der Kürzeste-Wege-Läufe bis 1e-4."""
    rows = []
    for seed in seeds:
        net = network(params._replace(seed=seed))
        row = {}
        for m in ("fw", "msa", "cfw"):
            res = al.assign(net, params.mode, m, max_iter, 1e-4 / 10)
            row[m] = dict(its3=res.first_below(1e-3), its4=res.first_below(1e-4), gap100=res.gaps[min(100, len(res.gaps) - 1)], origins=len(net.origins()))
        rows.append(row)

    def mean_its(m, key):
        vals = [(max_iter + 1 if r[m][key] is None else r[m][key]) for r in rows]
        return statistics.fmean(vals)

    return dict(n=len(rows), max_iter=max_iter, rows=rows,
                **{f"{m}_{k}": mean_its(m, k) for m in ("fw", "msa", "cfw") for k in ("its3", "its4")},
                **{f"{m}_missed": sum(1 for r in rows if r[m]["its4"] is None) for m in ("fw", "msa", "cfw")},
                **{f"{m}_gap100": statistics.fmean(r[m]["gap100"] for r in rows) for m in ("fw", "msa", "cfw")})


def uniqueness(params):
    """Kantenflüsse sind eindeutig: Frank-Wolfe und konjugiertes Frank-Wolfe enden bei denselben Flüssen (größte Abweichung in Prozent der gesamten Nachfrage), auch wenn sie ganz andere Wege benutzen."""
    net = network(params)
    a = al.assign(net, params.mode, "cfw", 800, 1e-9)
    b = al.assign(net, params.mode, "fw", 1500, 1e-7)
    total = net.total_demand()
    return dict(max_diff=max(abs(a.x[k] - b.x[k]) for k in range(net.m)) / total, gap_a=a.gaps[-1], gap_b=b.gaps[-1], iterations=(a.iterations, b.iterations))


def wardrop_check(net, x, mode="ue"):
    """Wardrop-Bedingung: für jedes Zonenpaar ist der kürzeste Weg höchstens so lang wie jeder benutzte; hier über die relative Lücke und die Restlücke einer Alles-oder-nichts-Zuordnung ausgedrückt."""
    cost = al.link_costs(net, mode, x)
    y, _, _ = al.all_or_nothing(net, cost)
    return al.relative_gap(net, mode, x, y)
