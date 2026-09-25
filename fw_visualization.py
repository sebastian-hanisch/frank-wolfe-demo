"""Plotly-Abbildungen: Stadtplan mit Verkehr und Auslastung, Flussdifferenz zwischen Systemoptimum und Nutzergleichgewicht, Lückenkurven der Verfahren, Genauigkeit, Lastreihe, Verteilung.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen. Karten haben gleichen Maßstab (scaleanchor) mit automatischem Bereich; der Rand kommt über zwei unsichtbare Punkte
(ein fest vorgegebener Bereich wird beim ersten Zeichnen in schmaler Breite eingefroren). Beschriftungen von Kanten sind Annotationen mit heller Hinterlegung."""

from math import hypot

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import fw_constants as C

UTIL_BINS = ((0.0, 0.5, "Auslastung unter 50 %", "#2ca02c"), (0.5, 0.8, "50 bis 80 %", "#bcbd22"), (0.8, 1.0, "80 bis 100 %", "#ff7f0e"), (1.0, 1.3, "100 bis 130 %", "#d62728"), (1.3, 1e9, "über 130 %", "#7f0000"))


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.18), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _frame(fig, points, height, pad=8):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    return _base(fig, height)


def _offsets(net):
    """Seitlicher Versatz je Kante: gegenläufige Kanten liegen nebeneinander, parallele Kanten zwischen denselben Knoten fächern auf."""
    groups = {}
    for k, l in enumerate(net.links):
        groups.setdefault((l[0], l[1]), []).append(k)
    off = {}
    for (u, v), ks in groups.items():
        base = 1.4 if net.kind == "grid" else 0.0
        for i, k in enumerate(ks):
            off[k] = base + (i - (len(ks) - 1) / 2) * 6.0
    return off


def _segment(net, k, off):
    u, v = net.links[k][0], net.links[k][1]
    (x0, y0), (x1, y1) = net.pos[u], net.pos[v]
    length = hypot(x1 - x0, y1 - y0) or 1.0
    nx, ny = (y1 - y0) / length, -(x1 - x0) / length
    o = off[k]
    return x0 + nx * o, y0 + ny * o, x1 + nx * o, y1 + ny * o


def _width(flow, top, lo=1.0, hi=7.0):
    return round(lo + (hi - lo) * flow / top) if top > 0 else lo


def build_map(net, x, height=460, label_flows=False):
    """Stadtplan: Kantenbreite ~ Verkehr, Farbe = Auslastung x / Kapazität; Zonen orange umrandet. `label_flows`: Verkehr an den Kanten beschriften (kleine Lehrnetze)."""
    fig = go.Figure()
    off = _offsets(net)
    top = max(x) if x else 1.0
    used = [k for k in range(net.m) if x[k] > 1e-9]
    unused = [k for k in range(net.m) if x[k] <= 1e-9]
    if unused:
        xs, ys = [], []
        for k in unused:
            x0, y0, x1, y1 = _segment(net, k, off)
            xs += [x0, x1, None]
            ys += [y0, y1, None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(150,150,150,0.35)", width=1), hoverinfo="skip", name="unbenutzt"))
    for lo, hi, name, color in UTIL_BINS:
        ks = [k for k in used if lo <= x[k] / net.links[k][4] < hi]
        by_width = {}
        for k in ks:
            by_width.setdefault(_width(x[k], top), []).append(k)
        first = True
        for w, group in sorted(by_width.items()):
            xs, ys = [], []
            for k in group:
                x0, y0, x1, y1 = _segment(net, k, off)
                xs += [x0, x1, None]
                ys += [y0, y1, None]
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=w), hoverinfo="skip", name=name, showlegend=first))
            first = False
    hx, hy, ht = [], [], []
    for k in range(net.m):
        x0, y0, x1, y1 = _segment(net, k, off)
        hx.append((x0 + x1) / 2)
        hy.append((y0 + y1) / 2)
        u, v = net.links[k][0], net.links[k][1]
        ht.append(f"{net.names[u]} → {net.names[v]}: Verkehr {x[k]:.1f}, Kapazität {net.links[k][4]:.0f}, Fahrzeit {net.links[k][2] + net.links[k][3] * (x[k] / net.links[k][4]) ** net.links[k][5]:.2f}")
    fig.add_trace(go.Scatter(x=hx, y=hy, mode="markers", marker=dict(size=9, opacity=0), hovertext=ht, hoverinfo="text", showlegend=False))
    if label_flows:
        for k in range(net.m):
            x0, y0, x1, y1 = _segment(net, k, off)
            fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=f"{x[k]:.2f}", showarrow=False, font=dict(size=10), bgcolor="rgba(255,255,255,0.85)", borderpad=1)
    zone_set = set(net.zones)
    dots = [v for v in range(net.n) if v not in zone_set]
    fig.add_trace(go.Scatter(x=[net.pos[v][0] for v in dots], y=[net.pos[v][1] for v in dots], mode="markers", marker=dict(size=4, color=C.COLORS["node"]), hovertext=[net.names[v] for v in dots], hoverinfo="text", showlegend=False))
    z = list(net.zones)
    fig.add_trace(go.Scatter(x=[net.pos[v][0] for v in z], y=[net.pos[v][1] for v in z], mode="markers+text", text=[f"Z{i + 1}" if net.kind == "grid" else net.names[v] for i, v in enumerate(z)], textposition="top center", textfont=dict(size=9),
                             marker=dict(size=13, symbol="square", color=C.COLORS["zone"], line=dict(width=1.5, color="#333")), hovertext=[net.names[v] for v in z], hoverinfo="text", name="Zone"))
    return _frame(fig, net.pos, height)


def build_difference(net, ue, so, height=460):
    """Systemoptimum minus Nutzergleichgewicht je Kante: Breite ~ Betrag der Verschiebung, Rot = im Systemoptimum mehr Verkehr, Blau = weniger."""
    fig = go.Figure()
    off = _offsets(net)
    diff = [so[k] - ue[k] for k in range(net.m)]
    top = max((abs(d) for d in diff), default=1.0) or 1.0
    for sign, color, name in ((1, "#d62728", "Systemoptimum: mehr Verkehr"), (-1, "#1f77b4", "Systemoptimum: weniger Verkehr")):
        by_width = {}
        for k in range(net.m):
            if sign * diff[k] > 1e-6 * top + 1e-9:
                by_width.setdefault(_width(abs(diff[k]), top), []).append(k)
        first = True
        for w, group in sorted(by_width.items()):
            xs, ys = [], []
            for k in group:
                x0, y0, x1, y1 = _segment(net, k, off)
                xs += [x0, x1, None]
                ys += [y0, y1, None]
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=w), hoverinfo="skip", name=name, showlegend=first))
            first = False
    z = list(net.zones)
    fig.add_trace(go.Scatter(x=[net.pos[v][0] for v in z], y=[net.pos[v][1] for v in z], mode="markers", marker=dict(size=11, symbol="square", color=C.COLORS["zone"], line=dict(width=1.5, color="#333")), hoverinfo="skip", name="Zone"))
    return _frame(fig, net.pos, height)


def build_gap(results, current=None, height=340):
    """Relative Lücke gegen die Iteration (logarithmisch) je Verfahren; gepunktet 1e-2 ... 1e-5; `current`: Iteration der Karte."""
    fig = go.Figure()
    for m, res in results.items():
        gaps = [max(g, 1e-12) for g in res.gaps]
        fig.add_trace(go.Scatter(x=list(range(len(gaps))), y=gaps, mode="lines", name=C.METHODS[m], line=dict(color=C.COLORS[m], width=2)))
    for tol in C.TOLS:
        fig.add_hline(y=tol, line=dict(color="rgba(80,80,80,0.35)", dash="dot", width=1))
    if current is not None:
        fig.add_vline(x=current, line=dict(color="#111", dash="dash"), annotation_text="Bild", annotation_position="top")
    fig.update_xaxes(title="Iteration")
    fig.update_yaxes(title="relative Lücke", type="log", exponentformat="power")
    return _base(fig, height)


def build_accuracy(rows, height=300):
    """Fehler der Gesamtfahrzeit und größter Kantenflussfehler, wenn Frank-Wolfe eine Lücke erstmals unterschreitet (logarithmisch)."""
    rows = [r for r in rows if r.get("iteration") is not None]
    x = [f"Lücke {r['gap']:.0e}<br>Iteration {r['iteration']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=[r["tstt_error"] for r in rows], name="Fehler der Gesamtfahrzeit", marker_color="#1f77b4"))
    fig.add_trace(go.Bar(x=x, y=[r["flow_error"] for r in rows], name="größter Kantenflussfehler (Anteil der Nachfrage)", marker_color="#d62728"))
    fig.update_yaxes(title="Fehler", type="log", tickformat=".1%")
    fig.update_layout(barmode="group")
    return _base(fig, height)


def build_load_series(rows, height=340):
    """Iterationen bis zur Lücke 1e-2, 1e-3 und 1e-4 je Lastfaktor (linke Achse, logarithmisch) und Preis der Anarchie (rechte Achse)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    loads = [r["load"] / 10 for r in rows]
    for tol, color in zip(C.TOLS[:3], ("#2ca02c", "#1f77b4", "#d62728")):
        fig.add_trace(go.Scatter(x=loads, y=[max(r["its"][tol], 0.5) for r in rows], mode="lines+markers", name=f"bis Lücke {tol:.0e}", line=dict(color=color)), secondary_y=False)
    fig.add_trace(go.Scatter(x=loads, y=[r["poa_mean"] for r in rows], mode="lines+markers", name="Preis der Anarchie (Mittel)", line=dict(color="#555", dash="dot")), secondary_y=True)
    fig.update_xaxes(title="Lastfaktor")
    fig.update_yaxes(title="Iterationen (Frank-Wolfe)", type="log", secondary_y=False)
    fig.update_yaxes(title="Preis der Anarchie", secondary_y=True, showgrid=False, tickformat=".2f")
    return _base(fig, height)


def build_dist(dist, height=320):
    """Mittlere Iterationen bis zur Lücke 1e-3 und 1e-4 je Verfahren über die festen Netze (nicht erreicht = Grenze + 1)."""
    ms = ("fw", "msa", "cfw")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[C.METHODS[m] for m in ms], y=[dist[f"{m}_its3"] for m in ms], name="bis Lücke 1e-3", marker_color="#1f77b4"))
    fig.add_trace(go.Bar(x=[C.METHODS[m] for m in ms], y=[dist[f"{m}_its4"] for m in ms], name="bis Lücke 1e-4", marker_color="#d62728"))
    fig.update_yaxes(title="Iterationen (Mittel)")
    fig.update_layout(barmode="group")
    return _base(fig, height)
