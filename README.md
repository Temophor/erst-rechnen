# erst-rechnen

Alle Rechenmodelle zum Kanal **[Erstrechnen](https://www.youtube.com/@erstrechnen)** — offen, zum Selbernachvollziehen und mit deinen eigenen Zahlen neu Ausrechnen.

„Erst rechnen, dann entscheiden."

## Wie du es benutzt

Jedes Modell ist eine einzelne, abhängigkeitsfreie Python-Datei (nur Standardbibliothek). Konstanten stehen oben in der Datei — ändere sie auf deine eigene Situation und lass das Skript neu laufen:

```bash
python models/e001_sondertilgung_vs_etf.py
```

Jede Datei enthält einen Selbsttest (`_selbsttest()`), der beim Ausführen automatisch mitläuft, sowie den kompletten Rechenweg. Die Ergebnisse werden zusätzlich als `eXXX_zahlen.json` neben der Datei abgelegt.

## Die Folgen

| Folge | Modell | Kipppunkt |
|---|---|---|
| E001 — Sondertilgung oder ETF? | `models/e001_sondertilgung_vs_etf.py` | 4,33 % erwartete ETF-Rendite |
| E002 — Steuerklasse 3/5 | `models/e002_steuerklassen.py` | 7 Monate vor dem Mutterschutz |
| E003 — Wärmepumpe oder Gas? | `models/e003_waermepumpe.py` | ~15–23 % Förderquote |
| E004 — Rente mit 63 | `models/e004_rente63.py` | Break-even 81,8 Jahre |
| E005 — Leasing, Neuwagen oder Gebraucht? | `models/e005_auto_dreieck.py` | dein Neuwagen-Bedürfnis |
| E006 — Wohnung oder ETF? | `models/e006_immo_vs_etf.py` | 3,2 % Wertsteigerung/Jahr |
| E007 — PV-Anlage: mit Speicher, ohne, oder gar nicht? | `models/e007_pv.py` | 5.100 € Speicherpreis (Grenzbetrachtung) |

`models/steuer_2026.py` ist ein gemeinsames Hilfsmodul (Einkommensteuertarif 2026 nach § 32a EStG, Lohnsteuerklassen-Näherung nach § 39b), das von E002 verwendet wird.

Weitere Modelle kommen mit jeder neuen Folge dazu.

## Wichtiger Hinweis

Jedes Modell ist eine **Beispielrechnung** mit klar benannten Annahmen — keine Steuer-, Rechts-, Anlage- oder sonstige Beratung. Prüfe insbesondere gesetzliche Werte (Steuersätze, Freibeträge, Rentenwert, Förderquoten) vor eigenen Entscheidungen auf ihre Aktualität — die Quellen mit Abrufdatum stehen jeweils im Kopf der Datei bzw. in der Videobeschreibung der zugehörigen Folge.

Dein Ergebnis hängt von deinen Zahlen ab. Deshalb liegt hier der ganze Rechenweg offen — nicht nur das Ergebnis.
