"""Frank-Wolfe - wohin fährt der Verkehr, und warum dauert der Endspurt so lang? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo EIN Verfahren - Frank-Wolfe für die Verkehrsumlegung - und lässt stattdessen das Beispiel wachsen.
Vierte Erweiterung (Stück 16, E4) der Netzwerkfluss-Linie der "Konzepte"-Reihe: Kind des Mehrgüterflusses; jede Iteration ruft das Kürzeste-Wege-Orakel der Hauptlinie auf. Siehe README für die Einordnung.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import fw_algorithm as al
import fw_constants as C
import fw_evaluation as ev
from fw_presets import (
    KEPT,
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    seed_widget,
    sync_query_params,
)
from fw_visualization import build_accuracy, build_difference, build_dist, build_gap, build_load_series, build_map

st.set_page_config(page_title="Frank-Wolfe – Sebastian Hanisch", layout="wide")


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _int(x):
    return f"{int(round(x)):,}".replace(",", " ")


def _pct(x, digits=1):
    return f"{100 * x:.{digits}f} %".replace(".", ",")


def _sci(x):
    return f"{x:.1e}".replace(".", ",")


@st.cache_resource(show_spinner=False, max_entries=32)
def _analysis(params):
    return ev.analyse(ev.Params(*params))


@st.cache_resource(show_spinner=False, max_entries=32)
def _compare(params):
    return ev.compare(ev.Params(*params))


@st.cache_resource(show_spinner=False, max_entries=32)
def _poa(params):
    return ev.poa(ev.Params(*params))


st.title("🚦 Frank-Wolfe – wohin fährt der Verkehr?")
st.markdown(
    """
In einem Stadtnetz wählt jeder Fahrer den schnellsten Weg - aber wie schnell ein Weg ist, hängt davon ab, wie viele andere ihn wählen. Im **Nutzergleichgewicht** (Wardrop 1952) ist kein Weg, den jemand benutzt, länger als ein anderer: eine konvexe Optimierungsaufgabe, das **Beckmann-Programm**.
**Frank-Wolfe** löst sie mit dem, was die Netzwerkfluss-Linie schon kann: in jedem Schritt die Fahrzeiten am aktuellen Verkehr berechnen, jedes Zonenpaar **alles auf den schnellsten Weg** legen (ein Kürzeste-Wege-Lauf je Ursprung) und den Verkehr ein Stück in diese Richtung schieben.
Das Verfahren ist einfach und robust - und hat einen **langsamen Endspurt**: die ersten Prozent Genauigkeit kommen schnell, jede weitere Dezimalstelle kostet ein Vielfaches. Diese Demo zeigt den Verlauf, drei Schrittweiten (exakte Suche, 1/(k+1), konjugiert), wie genau man überhaupt rechnen muss - und was das **Systemoptimum** gegenüber dem Gleichgewicht kostet.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren vergleichen, zeigt diese Demo - vierte Erweiterung (E4) der Netzwerkfluss-Linie der \"Konzepte\"-Reihe, Kind des Mehrgüterflusses - **ein** Verfahren an einem wachsenden Beispiel. "
    "Anders als in den Demos \"Preis der Anarchie & Braess-Paradox\" und \"Maut & Grenzkosten-Preise\" (einzelne Lkw auf einem festen Vier-Knoten-Netz, Gleichgewichte durch Aufzählen) ist der Verkehr hier **stetig teilbar** und das Netz ein Stadtgitter: es geht nicht um das Paradox, sondern um **Rechenverfahren und ihre Genauigkeit**."
)

with st.expander("So funktioniert Frank-Wolfe", expanded=True):
    st.markdown(
        r"""
1. **Fahrzeiten:** jede Straße hat eine Fahrzeit $t_e(x_e)=a_e+b_e\,(x_e/c_e)^p$, die mit dem Verkehr $x_e$ steigt (BPR-Form: $a_e$ Freifahrtzeit, Kapazität $c_e$, $b_e=0{,}15\,a_e$, $p=4$).
2. **Nutzergleichgewicht:** der Verkehr $x$ löst $\min\sum_e\int_0^{x_e}t_e(s)\,ds$ unter der Flusserhaltung je Zonenpaar (Beckmann). Die Kantenflüsse sind eindeutig, die Wegeflüsse im Allgemeinen nicht.
3. **Alles-oder-nichts:** mit den Fahrzeiten $t_e(x_e)$ als Kantenlängen legt man jedes Zonenpaar komplett auf einen kürzesten Weg (Dijkstra je Ursprung): das ergibt den Verkehr $y$. Das ist die beste Richtung für die *linearisierte* Aufgabe.
4. **Schritt:** $x\leftarrow x+a\,(y-x)$. Die Schrittweite $a$: **exakte Suche** (Bisektion auf der Richtungsableitung), **MSA** ($a=1/(k+1)$, keine Suche) oder **fest** 0,5 (Negativkontrolle: es zickzackt). Das **konjugierte Frank-Wolfe** ersetzt $y$ durch einen Zielpunkt, der zur vorigen Richtung konjugiert ist, und zickzackt weniger.
5. **Lücke:** $\big(\sum x_e t_e-\sum y_e t_e\big)/\sum x_e t_e$ ist 0 genau im Gleichgewicht und misst, wie viel Fahrzeit ein Wechsel auf die kürzesten Wege noch sparen würde. Das **Systemoptimum** (kleinste Gesamtfahrzeit) ist dieselbe Aufgabe mit den **Grenzkosten** $t_e+x_e t_e'$ statt der Fahrzeit.
        """
    )

st.caption("🎯 Schnellstart – ein Beispiel laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    net_key = st.selectbox("Netz", list(C.NETS), key="net_select", format_func=lambda k: C.NETS[k],
                           help="Ein Stadtgitter mit Zonen oder ein festes Lehrnetz: das Pigou-Netz (zwei parallele Straßen, Preis der Anarchie genau 4/3) und zwei Stufen paralleler Straßen (Kantenflüsse eindeutig, Wegeflüsse nicht).")
    mode = st.radio("Ziel", list(C.MODES), key="mode_radio", format_func=lambda k: C.MODES[k],
                    help="Nutzergleichgewicht: jeder wählt für sich den schnellsten Weg (Fahrzeit als Kosten). Systemoptimum: kleinste Gesamtfahrzeit (Grenzkosten als Kosten); derselbe Löser, andere Kosten.")
    method = st.radio("Verfahren", list(C.METHODS), key="method_radio", format_func=lambda k: C.METHODS[k],
                      help="Frank-Wolfe mit exakter Schrittweitensuche, mit fester Schrittfolge 1/(k+1) (MSA), konjugiert - oder mit festem Schritt 0,5, der nicht konvergiert (Negativkontrolle).")
    iterations = st.radio("Iterationsgrenze", list(C.ITERATIONS), key="iterations_radio", horizontal=True, help="Höchstzahl der Iterationen; die Rechnung stoppt früher, wenn die relative Lücke unter 1e-6 fällt.")
    if net_key == "grid":
        seed_widget("side_slider")
        side = st.slider("Kreuzungen je Kante", *bounds("side_slider"), key="side_slider", help="Das Stadtgitter hat side × side Kreuzungen und Straßen in beide Richtungen (bei 8 × 8: 224 Kanten).")
        st.session_state[KEPT["side_slider"]] = side
        seed_widget("zones_slider")
        zones = st.slider("Zonen", *bounds("zones_slider"), key="zones_slider", help="Zonen mit Nachfrage; jede Zone schickt Verkehr zu jeder anderen (Zonen × (Zonen − 1) Zonenpaare, ein Kürzeste-Wege-Lauf je Zone und Iteration).")
        st.session_state[KEPT["zones_slider"]] = zones
        seed_widget("load_slider")
        load = st.slider("Last [Zehntel des Standards]", *bounds("load_slider"), key="load_slider", step=5, help="Nachfrage in Zehnteln des Standards (10 = 1,0). Je höher die Last, desto länger der Endspurt: bis zur Lücke 1e-3 braucht Frank-Wolfe bei 0,5 im Mittel 2, bei 1,0 etwa 24 und bei 2,0 etwa 249 Iterationen.")
        st.session_state[KEPT["load_slider"]] = load
        seed_widget("seed_input")
        seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
        st.session_state[KEPT["seed_input"]] = seed
        st.button("🎲 Neues Netz generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Zufalls-Seed (neue Straßen, Zonen und Nachfrage). Die Verteilungen über 40 feste Netze weiter unten ändern sich dabei nicht.")
    else:
        side = int(st.session_state.get(KEPT["side_slider"], C.DEFAULT_SIDE))
        zones = int(st.session_state.get(KEPT["zones_slider"], C.DEFAULT_ZONES))
        load = int(st.session_state.get(KEPT["load_slider"], C.DEFAULT_LOAD))
        seed = int(st.session_state.get(KEPT["seed_input"], C.DEFAULT_SEED))
        st.caption("Dieses Netz ist fest - es gibt nichts zu erzeugen. Kreuzungen, Zonen, Last und Seed gehören zum Stadtgitter.")

sync_query_params({"net_select": net_key, "mode_radio": mode, "method_radio": method, "iterations_radio": int(iterations), "side_slider": int(side), "zones_slider": int(zones),
                   "load_slider": int(load), "seed_input": int(seed)})

# feste Lehrnetze ignorieren die Zufallsregler: sonst würden gleiche Netze unter verschiedenen Schlüsseln mehrfach berechnet
params = (net_key, int(side), int(zones), int(load), mode, method, int(iterations), int(seed))
if net_key != "grid":
    params = (net_key, C.DEFAULT_SIDE, C.DEFAULT_ZONES, C.DEFAULT_LOAD, mode, method, int(iterations), C.DEFAULT_SEED)
with st.spinner("Rechne..."):
    a = _analysis(params)
net, res = a["net"], a["result"]
N_IT = res.iterations
label = net.kind != "grid"

# --- Verkehr zuordnen -------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Verkehr zuordnen, Iteration für Iteration")
if st.session_state.get("fw_step_owner") != params:
    st.session_state["fw_step"] = N_IT
    st.session_state["fw_step_owner"] = params
step_col, play_col = st.columns([5, 2])
with step_col:
    if N_IT > 0:
        step = st.slider("Iteration", 0, N_IT, key="fw_step", help="Iteration 0: alle fahren die schnellsten Wege bei leerem Netz (Alles-oder-nichts auf den Freifahrtzeiten); danach schiebt jede Iteration den Verkehr ein Stück Richtung Alles-oder-nichts.")
    else:
        step = 0
        st.caption("Das Netz ist schon nach dem ersten Alles-oder-nichts im Gleichgewicht - es gibt nichts zu iterieren.")
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch", disabled=N_IT == 0)
view_slot = st.empty()


def _render(k):
    with view_slot.container():
        c1, c2 = st.columns([3, 2])
        c1.plotly_chart(build_map(net, res.flows[k], label_flows=label), width="stretch", key=f"map_{k}")
        c2.plotly_chart(build_gap({method: res}, current=k, height=460), width="stretch", key=f"gap_{k}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Relative Lücke", _sci(res.gaps[k]), help="Anteil der Fahrzeit, den ein Wechsel aller auf die kürzesten Wege noch sparen würde; 0 im Gleichgewicht.")
        m2.metric("Gesamtfahrzeit", _f(res.tstt[k], 1), delta=None if k == 0 else _f(res.tstt[k] - res.tstt[k - 1], 1) + " gegen vorher", delta_color="off", help="Summe der Verkehrsmenge mal Fahrzeit über alle Kanten.")
        m3.metric("Schrittweite", "–" if k == 0 else _f(res.steps[k - 1], 3), help="Anteil, um den der Verkehr in Richtung Alles-oder-nichts geschoben wurde (Iteration k − 1 → k).")
        m4.metric("Höchste Auslastung", _pct(max(al.utilization(net, res.flows[k])), 0), help="Größtes Verhältnis Verkehr / Kapazität einer Kante.")


if auto_play:
    for k in range(N_IT + 1):
        _render(k)
        time.sleep(min(0.4, 6.0 / max(N_IT, 1)))
    step = N_IT
else:
    _render(step)
st.caption("Kantenbreite = Verkehr, Farbe = Auslastung (Verkehr / Kapazität); orange Quadrate sind Zonen. Rechts die relative Lücke gegen die Iteration (logarithmisch): sie fällt schnell und dann immer langsamer - das ist der Endspurt.")

if res.gaps[-1] < 1e-6:
    st.success(f"✅ Nach {res.iterations} Iterationen ist die relative Lücke unter 1e-6 ({_sci(res.gaps[-1])}); {_int(res.runs)} Kürzeste-Wege-Läufe insgesamt.")
elif method == "fixed":
    st.warning(f"⚠️ Mit festem Schritt 0,5 fällt die Lücke nicht unter {_sci(min(res.gaps))}: der Verkehr springt zwischen zwei Zuständen hin und her. Ohne fallende oder gesuchte Schrittweite konvergiert Frank-Wolfe nicht.")
else:
    st.info(f"ℹ️ Nach {res.iterations} Iterationen (Grenze) liegt die relative Lücke bei {_sci(res.gaps[-1])}; die Gesamtfahrzeit ist auf {_f(res.tstt[-1], 1)} gefallen. Mehr Iterationen oder ein anderes Verfahren im Vergleich unten helfen.")
if net_key == "zweistufen":
    st.markdown("**Kantenflüsse eindeutig, Wegeflüsse nicht:** jede der vier Straßen trägt genau 5. Dazu passen mehrere Wegeaufteilungen, etwa (1,3) = 5 und (2,4) = 5, oder (1,4) = 5 und (2,3) = 5, oder alle vier Wege je 2,5 - Straße 1 oder 2, dann Straße 3 oder 4. Das Nutzergleichgewicht legt nur die Kantenflüsse fest.")

st.markdown("---")

# --- Verfahren im Vergleich -------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Drei Schrittweiten im Vergleich")
methods = ("fw", "msa", "cfw") + (("fixed",) if method == "fixed" else ())
with st.spinner("Rechne die Verfahren..."):
    cmp = _compare(params) if method != "fixed" else ev.compare(ev.Params(*params), methods=methods)
st.plotly_chart(build_gap(cmp["results"], height=340), width="stretch", key="compare_chart")
st.table({"Verfahren": [C.METHODS[m] for m in methods],
          **{f"Iterationen bis Lücke {t:.0e}": [("–" if cmp["table"][m][i] is None else str(cmp["table"][m][i])) for m in methods] for i, t in enumerate(C.TOLS[:3])}})
st.caption(f"Iterationen, bis die relative Lücke erstmals unter die Schwelle fällt; „–“ heißt: nicht innerhalb von {iterations} Iterationen. Jede Iteration braucht {len(net.origins())} Kürzeste-Wege-Läufe (einen je Ursprungszone); die Schrittweitensuche kostet dazu nur Auswertungen der Fahrzeitfunktion, keine Wegesuche.")

st.markdown("---")

# --- Nutzergleichgewicht gegen Systemoptimum ---------------------------------------------------------------------------------------------

st.markdown("## 🎯 Was kostet das Gleichgewicht gegenüber dem Optimum?")
with st.spinner("Rechne Nutzergleichgewicht und Systemoptimum..."):
    pa = _poa(params)
ue, so = pa["ue"], pa["so"]
q1, q2, q3 = st.columns(3)
q1.metric("Gesamtfahrzeit im Gleichgewicht", _f(ue.tstt[-1], 1))
q2.metric("Gesamtfahrzeit im Systemoptimum", _f(so.tstt[-1], 1))
q3.metric("Preis der Anarchie", _f(pa["poa"], 3), delta=f"{_pct(pa['poa'] - 1)} mehr Fahrzeit", delta_color="off", help="Gesamtfahrzeit im Nutzergleichgewicht geteilt durch die im Systemoptimum (beide mit konjugiertem Frank-Wolfe, höchstens 300 Iterationen).")
if net_key == "pigou":
    st.success("✅ Pigou-Netz: im Gleichgewicht fahren alle die zweite Straße (Fahrzeit 1), im Optimum halb und halb (mittlere Fahrzeit 0,75): Preis der Anarchie genau 4/3.")
st.plotly_chart(build_difference(net, ue.x, so.x), width="stretch", key="diff_chart")
st.caption("Systemoptimum minus Nutzergleichgewicht je Kante: rot = im Optimum mehr Verkehr, blau = weniger. Auf einem Stadtgitter liegt der Preis der Anarchie meist nur wenige Prozent über 1 - der Extremfall 4/3 des Braess-Netzes ist selten.")

st.markdown("---")

# --- Experimente -------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie genau muss man rechnen?")
st.caption("Fehler der Gesamtfahrzeit und größter Kantenflussfehler (in Prozent der gesamten Nachfrage) gegen eine sehr genaue Lösung, wenn Frank-Wolfe die Lücke 1e-2, 1e-3 und 1e-4 erstmals unterschreitet. Die Fahrzeit stimmt früh, die Kantenflüsse brauchen länger.")
if net_key != "grid":
    st.info("Für dieses Experiment das Stadtgitter wählen.")
else:
    if st.button("Genauigkeit messen (dauert einige Sekunden)", key="accuracy_start"):
        st.session_state["accuracy_on"] = True
    if st.session_state.get("accuracy_on"):
        with st.spinner("Rechne die Referenzlösung..."):
            acc = ev.accuracy(ev.Params(*params))
        st.plotly_chart(build_accuracy(acc), width="stretch", key="accuracy_chart")
        st.table({"Lücke": [f"{r['gap']:.0e}" for r in acc], "Iteration": [str(r["iteration"]) if r["iteration"] is not None else "–" for r in acc],
                  "Fehler Gesamtfahrzeit": [_pct(r["tstt_error"], 2) if r["iteration"] is not None else "–" for r in acc], "größter Kantenflussfehler": [_pct(r["flow_error"], 2) if r["iteration"] is not None else "–" for r in acc]})
        st.caption("Wer nur die Gesamtfahrzeit braucht, ist mit einer Lücke von 1e-3 fertig; wer Kantenflüsse (etwa für eine Maut oder eine Straßenplanung) braucht, rechnet weiter.")

st.subheader("🔬 Wie hängt der Endspurt von der Last ab?")
st.caption("Iterationen bis zur Lücke 1e-2, 1e-3 und 1e-4 (Frank-Wolfe mit exakter Schrittweite, Mittel über 5 feste Netze; „nicht erreicht“ zählt als Grenze + 1 = 301) und Preis der Anarchie je Lastfaktor.")
if net_key != "grid":
    st.info("Für dieses Experiment das Stadtgitter wählen.")
else:
    if st.button("Lastreihe durchrechnen (dauert etwa eine Minute)", key="load_start"):
        st.session_state["load_on"] = True
    if st.session_state.get("load_on"):
        with st.spinner("Rechne 5 Lastfaktoren × 5 Netze..."):
            rows = ev.load_series(ev.Params(*params))
        st.plotly_chart(build_load_series(rows), width="stretch", key="load_chart")
        st.table({"Lastfaktor": [_f(r["load"] / 10, 1) for r in rows], "bis 1e-2": [_f(r["its"][1e-2], 1) for r in rows], "bis 1e-3": [_f(r["its"][1e-3], 1) for r in rows], "bis 1e-4": [_f(r["its"][1e-4], 1) for r in rows],
                  "Preis der Anarchie (Mittel)": [_f(r["poa_mean"], 3) for r in rows], "Preis der Anarchie (größter)": [_f(r["poa_max"], 3) for r in rows]})
        st.caption("Je mehr Verkehr, desto mehr Kanten sind überlastet und desto länger dauert der Endspurt; bei kleiner Last ist das Nutzergleichgewicht nach einer Handvoll Iterationen erreicht. Der Preis der Anarchie wächst mit der Last, bleibt aber weit unter 4/3.")

st.subheader("🔬 Ist das konjugierte Verfahren wirklich schneller?")
st.caption("Iterationen bis zur Lücke 1e-3 und 1e-4 auf 40 festen Netzen mit den Einstellungen (Mittel; „nicht erreicht“ zählt als Grenze + 1 = 201).")
if net_key != "grid":
    st.info("Für dieses Experiment das Stadtgitter wählen.")
else:
    if st.button("40 Netze durchrechnen (dauert etwa eine halbe Minute)", key="dist_start"):
        st.session_state["dist_on"] = True
    if st.session_state.get("dist_on"):
        with st.spinner("Rechne 40 Netze × 3 Verfahren..."):
            dist = ev.distribution(ev.Params(*params))
        st.plotly_chart(build_dist(dist), width="stretch", key="dist_chart")
        st.table({"Verfahren": [C.METHODS[m] for m in ("fw", "msa", "cfw")], "Lücke 1e-4 nicht erreicht": [f"{dist[m + '_missed']} von {dist['n']}" for m in ("fw", "msa", "cfw")]})
        st.caption("Das konjugierte Verfahren braucht im Mittel weniger Iterationen (bis zur Lücke 1e-4 weniger als die Hälfte der exakten Suche), ist aber nicht in jedem Netz besser: in einzelnen Netzen bleibt seine Lücke lange stehen. MSA spart die Schrittweitensuche, liegt aber bei der Genauigkeit hinter der exakten Suche.")

st.subheader("🔬 Sind die Kantenflüsse eindeutig?")
st.caption("Frank-Wolfe und konjugiertes Frank-Wolfe nutzen ganz verschiedene Zwischenschritte; am Ende müssen sie bei denselben Kantenflüssen ankommen.")
if net_key != "grid":
    st.info("Für dieses Experiment das Stadtgitter wählen (das Lehrnetz „Zwei Stufen“ zeigt es oben von Hand).")
else:
    if st.button("Eindeutigkeit prüfen (dauert einige Sekunden)", key="unique_start"):
        st.session_state["unique_on"] = True
    if st.session_state.get("unique_on"):
        with st.spinner("Rechne beide Verfahren bis zur hohen Genauigkeit..."):
            un = ev.uniqueness(ev.Params(*params))
        u1, u2 = st.columns(2)
        u1.metric("Größte Abweichung der Kantenflüsse", _pct(un["max_diff"], 4), help="In Prozent der gesamten Nachfrage, nach 800 Iterationen konjugiertem Frank-Wolfe (Lücke unter 1e-9) gegen 1 500 Iterationen Frank-Wolfe.")
        u2.metric("Restlücke des einfachen Verfahrens", _sci(un["gap_b"]))
        st.caption("Die Kantenflüsse stimmen bis auf die Restlücke überein: bei strikt steigenden Fahrzeiten ist das Gleichgewicht auf den Kanten eindeutig. Die Wege, auf denen der Verkehr dorthin kommt, sind es nicht.")

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist - und wer ansetzt |
|---|---|
| **Frank-Wolfe ist schnell genug** | Der Endspurt ist sublinear: jede weitere Dezimalstelle kostet ein Mehrfaches. **Pfadbasierte Verfahren** (Gradient Projection, Algorithm B, TAPAS) halten Wege und verschieben Verkehr zwischen ihnen; sie erreichen hohe Genauigkeit viel schneller (Gradient Projection ist als eigenes Stück gebaut, Algorithm B und TAPAS sind nur erwähnt). |
| **Jeder kennt alle Fahrzeiten** | Wardrop setzt perfekte Information und rationale, unendlich viele kleine Fahrer voraus. Lernen aus Erfahrung ist ein anderes Modell (Demo „No-Regret-Lernen“). |
| **Eine Fahrzeugklasse, statische Zuordnung** | Lkw und Pkw belasten die Straßen verschieden, und Staus bauen sich im Zeitverlauf auf; beides ist hier nicht abgebildet (dynamische Umlegung, Mehrklassen-Umlegung). |
| **BPR-Fahrzeiten** | Eine glatte Potenzfunktion der Auslastung; echte Kreuzungen und Warteschlangen sind anders. Die Kantenflüsse sind für jede streng steigende Fahrzeit eindeutig, die Zahlen hier gelten für diese Funktion. |
| **Ein generiertes Netz** | Ein Gitter mit erzeugten Kapazitäten und Zonen, kein reales Stadtnetz und keine Fremddaten. |
"""
)
st.caption("Die Netzwerkfluss-Linie ist als Ganzes geplant: die zwölf Stücke der Hauptlinie (gebaut), die Erweiterung E1 (Projektauswahl, Graph Cuts, Gomory-Hu-Baum) und die Erweiterung E4: **Frank-Wolfe** (dieses Stück, gebaut) mit dem pfadbasierten Folgestück [gradient-projection-demo](https://github.com/sebastian-hanisch/gradient-projection-demo) (gebaut).")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Nutzergleichgewicht (Wardrop).** Für jedes Zonenpaar $w$ gilt: alle benutzten Wege sind gleich lang und nicht länger als jeder unbenutzte. Äquivalent (Beckmann 1956) löst der Kantenverkehr $x$ das konvexe Programm
$$\min_x\ Z(x)=\sum_e\int_0^{x_e}t_e(s)\,ds\quad\text{u.d.N. Flusserhaltung je Zonenpaar},\qquad t_e(x)=a_e+b_e\Big(\frac{x}{c_e}\Big)^p,\quad \int_0^{x}t_e=a_e x+\frac{b_e c_e}{p+1}\Big(\frac{x}{c_e}\Big)^{p+1}.$$
Die Zielfunktion ist streng konvex in $x$: die Kantenflüsse sind eindeutig.

**Systemoptimum.** $\min\sum_e x_e t_e(x_e)$: derselbe Löser mit den Grenzkosten $t_e(x_e)+x_e t_e'(x_e)=a_e+b_e(p+1)(x_e/c_e)^p$ (Pigou 1920, Beckmann/McGuire/Winsten 1956). Preis der Anarchie $=\text{Gesamtfahrzeit}_{UE}/\text{Gesamtfahrzeit}_{SO}$.

**Frank-Wolfe.** Mit den Kosten $t(x^k)$ ist $y^k$ (Alles-oder-nichts) die Lösung der linearisierten Aufgabe, $y^k-x^k$ eine Abstiegsrichtung; $x^{k+1}=x^k+a_k(y^k-x^k)$. Relative Lücke $g_k=\big(t(x^k)^\top(x^k-y^k)\big)/\big(t(x^k)^\top x^k\big)\ge0$; sie ist 0 genau im Gleichgewicht. Bekannt: die Konvergenz ist sublinear, die Iterationen wachsen etwa mit $1/\varepsilon$; der Grund ist das Zickzack, weil $y^k$ eine Ecke ist und die Lösung im Innern der Fläche liegt.

**MSA:** $a_k=1/(k+1)$ ohne Suche. **Konjugiertes Frank-Wolfe** (Mitradjieva und Lindberg 2013): $s^k=\alpha_k s^{k-1}+(1-\alpha_k)y^k$ mit $\alpha_k=\dfrac{(s^{k-1}-x^k)^\top H_k\,(y^k-x^k)}{(s^{k-1}-x^k)^\top H_k\,(y^k-s^{k-1})}\in[0,1-\delta]$ und der (diagonalen) Hesse-Matrix $H_k$ der Zielfunktion; Richtung $s^k-x^k$, sonst wie Frank-Wolfe. Ist $x^k$ schon auf $s^{k-1}$ angekommen oder die Richtung keine Abstiegsrichtung, beginnt das Verfahren mit der Frank-Wolfe-Richtung neu.

**Aufwand.** Eine Iteration kostet einen Dijkstra-Lauf je Ursprungszone (das Kürzeste-Wege-Orakel der Hauptlinie); die Schrittweitensuche rechnet nur Fahrzeitfunktionen aus.

Implementiert in `fw_scenario.py` (Netz, Zonen, Lehrnetze, eigener Zufallsgenerator), `fw_algorithm.py` (Kosten, Alles-oder-nichts, Frank-Wolfe, MSA, konjugiert, Lücke, Preis der Anarchie), `fw_evaluation.py` (Vergleiche, Genauigkeit, Lastreihe, Verteilungen).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Netzwerkfluss: vom Max-Flow zum Netzdesign](https://sebastianhanisch.net/konzepte-netzwerkfluss.html)."
)
