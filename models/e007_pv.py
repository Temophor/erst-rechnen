"""E007 — PV 2026: mit Speicher, ohne Speicher, gar nicht? (Grenzbetrachtung!)

⚠️ FRISCHE-CHECK vor Produktion: PV-Systempreis (Ansatz 14.000 € fuer 10 kWp inkl.
Montage, 0 % MwSt), Speicherpreis (Ansatz 5.500 € fuer 8 kWh nutzbar),
Einspeiseverguetung Teileinspeisung <=10 kWp (Ansatz 7,8 ct — EEG-Degression pruefen!),
Strompreis 37 ct ist verifiziert (BDEW 2026).

Methodischer Kern der Folge: Anlage und Speicher werden GETRENNT bewertet
(Grenzbetrachtung) — der klassische Fehler ist, beides zusammen zu rechnen und
die gute Anlagen-Rendite den schwachen Speicher subventionieren zu lassen."""

from __future__ import annotations
import json
from pathlib import Path

KWP = 10.0
PV_INVEST = 14_000.0
SPEICHER_INVEST = 5_500.0
ERTRAG_PRO_KWP = 950.0
VERBRAUCH = 4_500.0
EIGENVERBRAUCH_OHNE = 0.30      # Anteil des VERBRAUCHS aus PV gedeckt: konservative Quote
EIGENVERBRAUCH_MIT = 0.60
STROMPREIS = 0.37
EINSPEISUNG = 0.078
DEGRADATION = 0.005
BETRIEB_QUOTE = 0.01            # j. Betriebskosten (Versicherung, Wartung) auf Invest
JAHRE = 20
SPEICHER_LEBENSDAUER = 13


def jahresertrag(mit_speicher: bool, jahr: int) -> float:
    erzeugung = KWP * ERTRAG_PRO_KWP * (1 - DEGRADATION) ** jahr
    ev_quote = EIGENVERBRAUCH_MIT if mit_speicher else EIGENVERBRAUCH_OHNE
    eigen = min(VERBRAUCH * ev_quote, erzeugung)
    einspeisung = max(0.0, erzeugung - eigen)
    invest = PV_INVEST + (SPEICHER_INVEST if mit_speicher else 0.0)
    return eigen * STROMPREIS + einspeisung * EINSPEISUNG - invest * BETRIEB_QUOTE


def amortisation(mit_speicher: bool) -> float:
    invest = PV_INVEST + (SPEICHER_INVEST if mit_speicher else 0.0)
    kum, jahr = 0.0, 0
    while kum < invest and jahr < 40:
        kum += jahresertrag(mit_speicher, jahr)
        jahr += 1
    return jahr if kum >= invest else float("inf")


def gesamt(mit_speicher: bool) -> dict:
    invest = PV_INVEST + (SPEICHER_INVEST if mit_speicher else 0.0)
    summe = sum(jahresertrag(mit_speicher, j) for j in range(JAHRE))
    if mit_speicher:   # Speicher-Ersatz nach Lebensdauer einpreisen (anteilig)
        summe -= SPEICHER_INVEST * (JAHRE - SPEICHER_LEBENSDAUER) / SPEICHER_LEBENSDAUER
    return {"invest": invest, "ertrag_jahr_1": round(jahresertrag(mit_speicher, 0), 2),
            "gewinn_20j": round(summe - invest, 2),
            "amortisation_jahre": amortisation(mit_speicher)}


def speicher_grenzrechnung() -> dict:
    """Der Speicher isoliert: Mehrertrag vs. Mehrkosten."""
    mehrertrag = jahresertrag(True, 0) - jahresertrag(False, 0) \
        + SPEICHER_INVEST * BETRIEB_QUOTE  # Betriebskosten nicht doppelt anlasten
    amort = SPEICHER_INVEST / mehrertrag
    kipp_preis = mehrertrag * SPEICHER_LEBENSDAUER
    return {"mehrertrag_jahr": round(mehrertrag, 2),
            "amortisation_speicher_jahre": round(amort, 1),
            "speicher_lebensdauer": SPEICHER_LEBENSDAUER,
            "kipppunkt_speicherpreis": round(kipp_preis, 2),
            "aktueller_speicherpreis": SPEICHER_INVEST}


def zahlen() -> dict:
    return {"annahmen": {"kwp": KWP, "pv_invest": PV_INVEST,
                         "speicher_invest": SPEICHER_INVEST, "strompreis": STROMPREIS,
                         "einspeisung": EINSPEISUNG, "verbrauch": VERBRAUCH,
                         "ev_ohne": EIGENVERBRAUCH_OHNE, "ev_mit": EIGENVERBRAUCH_MIT},
            "ohne_speicher": gesamt(False),
            "mit_speicher": gesamt(True),
            "speicher_isoliert": speicher_grenzrechnung()}


def _selbsttest():
    assert jahresertrag(True, 0) > jahresertrag(False, 0)
    assert amortisation(False) <= amortisation(True)
    g = speicher_grenzrechnung()
    assert g["amortisation_speicher_jahre"] > 8      # Speicher traegt sich schwer
    o = gesamt(False)
    assert o["gewinn_20j"] > 0                        # Anlage selbst rechnet sich


if __name__ == "__main__":
    _selbsttest()
    z = zahlen()
    Path(__file__).with_name("e007_zahlen.json").write_text(
        json.dumps(z, indent=2, ensure_ascii=False))

    print(f"""
{'=' * 64}
E007 -- PV-Anlage: mit Speicher, ohne, oder gar nicht?
{'=' * 64}

Deine Annahmen (Konstanten oben in der Datei aendern fuer deine Situation):
  Anlagengroesse:      {KWP:.0f} kWp
  PV-Invest:           {PV_INVEST:,.0f} EUR
  Speicher-Invest:     {SPEICHER_INVEST:,.0f} EUR
  Strompreis:          {STROMPREIS * 100:.0f} ct/kWh
  Einspeiseverguetung: {EINSPEISUNG * 100:.1f} ct/kWh

Ergebnis ueber {JAHRE} Jahre:
  Anlage allein:     {z['ohne_speicher']['gewinn_20j']:,.0f} EUR Gewinn ({z['ohne_speicher']['amortisation_jahre']} Jahre Amortisation)
  Anlage + Speicher: {z['mit_speicher']['gewinn_20j']:,.0f} EUR Gewinn ({z['mit_speicher']['amortisation_jahre']} Jahre Amortisation)

  -> Der Speicher isoliert betrachtet: {z['speicher_isoliert']['amortisation_speicher_jahre']} Jahre
     Amortisation bei nur {z['speicher_isoliert']['speicher_lebensdauer']} Jahren Lebensdauer.
  -> Kipppunkt-Speicherpreis: {z['speicher_isoliert']['kipppunkt_speicherpreis']:,.0f} EUR
     (aktuell: {z['speicher_isoliert']['aktueller_speicherpreis']:,.0f} EUR)

Vollstaendige Rohdaten (auch in e007_zahlen.json):
{json.dumps(z, indent=2, ensure_ascii=False)}
""")
