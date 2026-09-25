# Frank-Wolfe – wohin fährt der Verkehr, und warum dauert der Endspurt so lang? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-frank-wolfe-demo.streamlit.app/)**

Vierte Erweiterung (Stück 16, **E4 Verkehrsumlegung**) der **Netzwerkfluss-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind von [multicommodity-demo](https://github.com/sebastian-hanisch/multicommodity-demo) und [mcf-column-generation-demo](https://github.com/sebastian-hanisch/mcf-column-generation-demo):
anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Verfahren – **Frank-Wolfe für die Verkehrsumlegung** – an einem wachsenden Beispiel.
In einem Stadtnetz wählt jeder Fahrer den schnellsten Weg, aber wie schnell ein Weg ist, hängt davon ab, wie viele andere ihn wählen. Im **Nutzergleichgewicht** (Wardrop 1952) ist kein benutzter Weg länger als ein anderer: die Lösung eines konvexen Programms (**Beckmann 1956**). Frank-Wolfe löst es mit dem, was die Netzwerkfluss-Linie schon kann:
mit den Fahrzeiten am aktuellen Verkehr legt es jedes Zonenpaar **alles auf einen schnellsten Weg** (ein Dijkstra-Lauf je Ursprungszone, das Kürzeste-Wege-Orakel der Hauptlinie) und schiebt den Verkehr ein Stück in diese Richtung. Es ist einfach und robust – und hat einen **langsamen Endspurt**.
Das **Systemoptimum** (kleinste Gesamtfahrzeit) ist dasselbe Programm mit den Grenzkosten statt der Fahrzeit. Vehikel: ein Stadtgitter mit Straßen in beide Richtungen, BPR-Fahrzeiten und Zonen mit Nachfrage; dazu zwei Lehrnetze (Pigou, zwei Stufen).
Anders als in `poa-braess-demo` und `maut-demo` (einzelne Lkw auf einem festen Vier-Knoten-Netz, Gleichgewichte durch Aufzählen) ist der Verkehr hier **stetig teilbar**: es geht nicht um das Paradox, sondern um Rechenverfahren und ihre Genauigkeit.

**Einordnung in die Reihe (die Kanten des Graphen):** Kind des Mehrgüterflusses (Zonenpaare als Güter, konvexe statt lineare Kosten); jede Iteration ist ein Ein-Gut-Fluss mit Kosten wie das Pricing der Column Generation; das Systemoptimum als Gleichgewicht auf Grenzkosten verbindet zu `maut-demo`. Ein pfadbasiertes Folgestück (Gradient Projection, Algorithm B, TAPAS) ist nur erwähnt und wird gebaut, falls die Messung es trägt. Bisher gebaut: die zwölf Stücke der Hauptlinie, alle drei der Erweiterung E1 und dieses Stück.
```
multicommodity-demo (mehrere Güter teilen Kapazität)                                    [gebaut]
  ├─ mcf-column-generation-demo, garg-koenemann-demo, fixkosten-netzdesign-demo …        [gebaut]
  └─ frank-wolfe-demo (konvexe Kosten: Nutzergleichgewicht, Alles-oder-nichts-Orakel)    [dieses Stück]
       └─ gradient-projection-demo (pfadbasiert, Endspurt)                               [nur erwähnt]
```

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` belegt: Lehrnetze von Hand, Beispielnetze über ihre Seeds, Verteilungen über 40 feste Netze (Seeds ab 100000; die Lastreihe über 5 Netze). Standard: 8 × 8 Kreuzungen (224 Kanten), 6 Zonen, 30 Zonenpaare, Last 1,0, Seed 5, Frank-Wolfe mit exakter Schrittweite, höchstens 200 Iterationen.
Die Rechnung nutzt nur + − × ÷ auf Python-Zahlen (keine Bibliotheksfunktionen): Iterationszahlen sind auf allen Plattformen dieselben. Aufwand zählt in Kürzeste-Wege-Läufen (6 je Iteration, einer je Ursprungszone), nie in Sekunden.

**Der Endspurt ist lang.** Die relative Lücke (Anteil der Fahrzeit, den ein Wechsel aller auf die kürzesten Wege noch sparen würde) fällt schnell und dann immer langsamer: 1e-2 nach **4**, 1e-3 nach **21**, 1e-4 nach **102** Iterationen, 1e-5 in 200 nicht (Lücke am Ende 5,8e-5) – jede weitere Dezimalstelle kostet ein Mehrfaches.
Je mehr Verkehr, desto länger (Mittel über 5 Netze, Frank-Wolfe; „nicht erreicht“ zählt als 301): bis 1e-3 braucht es bei Last 0,5 im Mittel **2,0**, bei 1,0 **23,6**, bei 1,5 **117**, bei 2,0 **249** Iterationen; bis 1e-4 bei 0,5 nur 4,2, bei 1,0 schon 218, ab 1,5 nicht mehr innerhalb von 300. Doppelte Last im Standardnetz: 1e-2 nach 35, 1e-3 in 200 nicht mehr.

**Wie genau muss man rechnen?** Gegen eine sehr genaue Lösung: bei Lücke 1e-2 (Iteration 4) liegt die Gesamtfahrzeit 1,6 % daneben, der größte Kantenfluss 2,0 % der Nachfrage; bei 1e-3 (Iteration 21) 0,07 % bzw. 0,45 %; bei 1e-4 (Iteration 102) 0,015 % bzw. 0,074 %. **Die Gesamtfahrzeit stimmt früh, die Kantenflüsse brauchen länger** – wer Flüsse für eine Maut oder eine Straßenplanung braucht, rechnet weiter.

**Drei Schrittweiten.** Iterationen bis 1e-2 / 1e-3 / 1e-4 / 1e-5 im Standardnetz: Frank-Wolfe mit exakter Suche **4 / 21 / 102 / –**, MSA (Schritt 1/(k+1), keine Suche) **7 / 57 / – / –**, **konjugiertes Frank-Wolfe 4 / 15 / 24 / 69** (fertig, Lücke unter 1e-6, nach 145 Iterationen). Über 40 Netze (200 Iterationen, „nicht erreicht“ = 201): bis 1e-3 im Mittel 35,3 / 55,3 / **22,6**, bis 1e-4 159 / 183 / **70**; 1e-4 nicht erreicht in 22 / 31 / **8** von 40 Netzen.
Das konjugierte Verfahren ist im Mittel schneller, aber **nicht in jedem Netz besser**: in einzelnen Netzen bleibt seine Lücke lange stehen. Mit **festem Schritt 0,5** konvergiert Frank-Wolfe nicht: die Lücke bleibt bei 4,2e-2, die Gesamtfahrzeit bei 7 275 (5,5 % über dem Gleichgewicht).

**Preis der Anarchie auf einem Stadtgitter.** Gesamtfahrzeit im Gleichgewicht geteilt durch die im Systemoptimum: im Standardnetz **1,040** (6 897 gegen 6 632; die höchste Auslastung einer Kante sinkt von 169 % auf 127 %), im Mittel über 5 Netze bei Last 0,5 / 1,0 / 1,5 / 2,0 / 3,0: **1,005 / 1,026 / 1,056 / 1,066 / 1,065**, größter Wert 1,115. Der Extremfall 4/3 des Braess- und Pigou-Netzes kommt hier nicht vor.
Pigou (von Hand): Gleichgewicht alle auf die zweite Straße, Fahrzeit 1, Systemoptimum halb und halb, 0,75, Preis der Anarchie **4/3**.

**Kantenflüsse eindeutig, Wegeflüsse nicht.** Frank-Wolfe (1 500 Iterationen) und konjugiertes Frank-Wolfe (bis Lücke 1e-9) enden bei denselben Kantenflüssen (größte Abweichung 0,004 % der Nachfrage). Im Lehrnetz „Zwei Stufen“ trägt jede der vier Straßen 5; dazu passen drei verschiedene Wegeaufteilungen (von Hand im Test).

## Was nicht funktioniert hat / Vorab-Hypothesen

Vor dem Bau standen sieben Vermutungen im Plan. Gemessen:

- **„Der Schwanz ist sublinear, etwa ×10 je Dezimalstelle“ – bestätigt**, auf hohe Last verstärkt (Iterationen bis 1e-3: 2 → 24 → 117 → 249 bei Last 0,5 → 2,0).
- **„Die Schrittweitensuche schlägt MSA“ – nur mäßig.** MSA braucht bis 1e-3 etwa 57 statt 21 Iterationen und erreicht 1e-4 in 200 nicht; dafür kostet sie keine Suche. Am Ende gleiche Gesamtfahrzeit (6 898); die Suche erreicht die Lücke 5,8e-5, MSA 2,9e-4.
- **„Konjugiertes Frank-Wolfe ist deutlich schneller“ – im Mittel ja (70 statt 159 Iterationen bis 1e-4), aber nicht überall.** Es brauchte zudem eine Absicherung: liegt der Verkehr schon auf dem alten Zielpunkt oder ist die Richtung keine Abstiegsrichtung, beginnt es mit der Frank-Wolfe-Richtung neu; ohne sie blieb die Lücke stehen.
- **„Der Preis der Anarchie ist klein“ – bestätigt, aber nicht null:** im Mittel 0,5 bis 6,6 %, im größten Netz 11,5 %. Die Werte gelten für diese erzeugten Gitter.
- **„Kantenflüsse eindeutig, Wegeflüsse nicht“ – bestätigt** (Kantenflüsse übereinstimmend bis 0,004 %, Lehrnetz mit drei Aufteilungen).
- **Kontrollen:** fester Schritt 0,5 konvergiert nie; ohne Kapazitätsabhängigkeit (b = 0) genügt ein Alles-oder-nichts (Test).
- **Abweichung vom Plan:** die Iterationsgrenze beträgt 200 (Standardansicht unter einer Sekunde je Verfahren), die Lastreihe rechnet nur 5 Netze und bis 300 Iterationen (etwa 30 Sekunden); Gegenprobe gegen eine Bisektionslösung entfällt im Nutzerinterface (Pigou und Kantenflüsse sind im Test gegen Handrechnung und Verfahrenswechsel geprüft).

## Was die Demo zeigt

- **Verkehr zuordnen:** Regler durch die Iterationen, Stadtplan (Kantenbreite = Verkehr, Farbe = Auslastung) und die Lückenkurve mit Marke.
- **Drei Schrittweiten im Vergleich:** Lückenkurven und Iterationen bis 1e-2 … 1e-4 (plus fester Schritt als Kontrolle).
- **Gleichgewicht gegen Optimum:** Gesamtfahrzeiten, Preis der Anarchie, Karte der Verschiebung.
- **Experimente (auf Abruf):** Genauigkeit, Lastreihe, 40 Netze, Eindeutigkeit der Kantenflüsse.
- **Wo die Annahmen enden:** Frank-Wolfe-Endspurt, perfekte Information, eine Fahrzeugklasse, statisch, BPR-Fahrzeiten, ein generiertes Netz.

## Modell und Verfahren

- **Fahrzeit:** $t_e(x)=a_e+b_e(x/c_e)^p$ (BPR: $a_e$ Freifahrtzeit 2 bis 6, $b_e=0{,}15\,a_e$, Kapazität 20 bis 45, $p=4$); Lehrnetze mit $p=1$.
- **Nutzergleichgewicht:** $\min\sum_e\int_0^{x_e}t_e$ unter Flusserhaltung je Zonenpaar. **Systemoptimum:** $\min\sum_e x_e t_e$, dasselbe Programm mit den Grenzkosten $t_e+x_e t_e'$.
- **Frank-Wolfe:** Alles-oder-nichts $y$ mit den Kosten am aktuellen Verkehr, $x\leftarrow x+a(y-x)$; $a$ per Bisektion auf der Richtungsableitung (exakt), $1/(k+1)$ (MSA) oder 0,5 (fest, Kontrolle). **Konjugiert** (Mitradjieva und Lindberg 2013): Zielpunkt $s^k=\alpha s^{k-1}+(1-\alpha)y^k$ mit diagonaler Hesse-Matrix.
- **Relative Lücke:** $(\sum x t-\sum y t)/\sum x t$; 0 genau im Gleichgewicht. Aufwand: Kürzeste-Wege-Läufe und durchsuchte Kanten.

## Ehrliche Grenzen

- **Frank-Wolfe ist langsam am Ende.** Pfadbasierte Verfahren (Gradient Projection, Algorithm B, TAPAS) erreichen hohe Genauigkeit viel schneller; sie sind nur erwähnt.
- **Perfekte Information, unendlich viele kleine Fahrer** (Wardrop); Lernen aus Erfahrung ist ein anderes Modell.
- **Eine Fahrzeugklasse, statische Zuordnung, BPR-Fahrzeiten.**
- **Synthetische Daten:** ein Gitter mit erzeugten Kapazitäten und Zonen, kein reales Netz, keine Fremddaten (etwa Sioux Falls).

## Bewusst nicht umgesetzt

- Bi-konjugiertes Frank-Wolfe, pfadbasierte Verfahren (Gradient Projection, Algorithm B, TAPAS), Mehrklassen- und dynamische Umlegung, Maut und Kapazitätserweiterung als eigene Themen.

## Dateien

```
app.py                  Oberfläche (Streamlit)
fw_scenario.py          Stadtgitter, Zonen, Lehrnetze, Zufallsgenerator
fw_algorithm.py         Kosten, Alles-oder-nichts, Frank-Wolfe, MSA, konjugiert, Preis der Anarchie
fw_evaluation.py        Vergleiche, Genauigkeit, Lastreihe, Verteilungen
fw_visualization.py     Plotly-Abbildungen
fw_presets.py           Permalink, Presets, Zufalls-Seed
fw_constants.py         Konstanten, Regler-Grenzen, feste Seed-Mengen, Preset-Texte
tests/                  Kern, Auswertung, Presets, Behauptungen, App, Regler-Zustand
```

## Lokal starten

```bash
python -m venv venv
venv/Scripts/pip install -r requirements.txt
venv/Scripts/streamlit run app.py
```

## Tests ausführen

```bash
venv/Scripts/pip install -r requirements-dev.txt
venv/Scripts/python -m pytest tests/ -v
```

Gebaut mit Streamlit und Plotly; der Kern ist reines Python.
