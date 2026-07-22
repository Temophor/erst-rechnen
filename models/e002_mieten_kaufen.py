"""E022 — Mieten vs. Kaufen (Selbstnutzer): Die Antwort haengt am Kauffaktor.

Faires Duell (wie E006, aber Selbstnutzer): Beide wohnen identisch. Der Kaeufer
zahlt Kaufnebenkosten, Kreditrate, Instandhaltung; der Mieter zahlt Miete und
investiert ALLES, was er gegenueber dem Kaeufer uebrig hat (Anfangskapital +
monatliche Differenz), in den ETF. Nach 30 J: Immobilienwert vs. Depot (netto).

Der Dreh der Folge: Preis = KAUFFAKTOR x Jahreskaltmiete — der Kipppunkt-Faktor
ist DIE eine Zahl, mit der jeder seine Stadt einordnen kann.

Annahmen (Tafel): Kredit 3,6 % (✓), Tilgung 2 %, NK 10 %, EK = 20 % + NK,
Instandhaltung 1,5 % des Gebaeudewerts (steigend 2 %), Miet- und Wertsteigerung
2 %/J (Sweep!), ETF 6,5 % (Endsteuer eff. 18,46 %), 30 Jahre.
NICHT bepreist: Umzugsflexibilitaet vs. Eigentums-Sicherheit (beides real, beide
Richtungen — im Urteil wuerdigen)."""

from __future__ import annotations
import json
from pathlib import Path

KALTMIETE_JAHR = 14_400.0     # 1.200 €/Monat Referenzwohnung
JAHRE = 30
ZINS, TILGUNG = 0.036, 0.02
NEBENKOSTEN = 0.10
EK_QUOTE = 0.20
INSTAND_QUOTE = 0.015 * 0.7   # auf Gebaeudeanteil (70 % vom Preis)
STEIGERUNG = 0.02             # Miete UND Immobilienwert (Basisfall)
ETF_R, ETF_ENDSTEUER = 0.065, 0.1846


def duell(faktor: float, wertsteigerung: float = STEIGERUNG,
          zins: float = ZINS, etf_r: float = ETF_R) -> dict:
    preis = KALTMIETE_JAHR * faktor
    ek = preis * EK_QUOTE + preis * NEBENKOSTEN
    kredit = preis * (1 - EK_QUOTE)
    rate = kredit * (zins + TILGUNG)
    restschuld = kredit
    miete = KALTMIETE_JAHR
    instand = preis * INSTAND_QUOTE
    depot, eingezahlt = ek, ek               # Mieter startet mit dem EK des Kaeufers
    for _ in range(JAHRE):
        zins_jahr = restschuld * zins
        zahlung = min(rate, restschuld + zins_jahr)
        kaeufer_kosten = zahlung + instand
        differenz = kaeufer_kosten - miete    # was der Mieter uebrig hat (kann <0 sein!)
        depot = depot * (1 + etf_r) + differenz
        eingezahlt += max(0.0, differenz)
        restschuld = max(0.0, restschuld + zins_jahr - zahlung)
        miete *= 1 + STEIGERUNG
        instand *= 1 + STEIGERUNG
    immo = preis * (1 + wertsteigerung) ** JAHRE - restschuld
    depot_netto = depot - max(0.0, depot - eingezahlt) * ETF_ENDSTEUER
    return {"faktor": faktor, "preis": round(preis, -3),
            "kaeufer_endvermoegen": round(immo, -2),
            "mieter_endvermoegen": round(depot_netto, -2),
            "vorteil_kaufen": round(immo - depot_netto, -2)}


def kipp_faktor(wertsteigerung: float = STEIGERUNG,
                zins: float = ZINS, etf_r: float = ETF_R) -> float:
    lo, hi = 8.0, 50.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if duell(mid, wertsteigerung, zins, etf_r)["vorteil_kaufen"] > 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 1)


def zahlen() -> dict:
    return {"annahmen": {"kaltmiete_jahr": KALTMIETE_JAHR, "zins": ZINS,
                         "tilgung": TILGUNG, "nk": NEBENKOSTEN, "ek_quote": EK_QUOTE,
                         "steigerung": STEIGERUNG, "etf": ETF_R, "jahre": JAHRE},
            "duell_faktor_20": duell(20.0),
            "duell_faktor_25": duell(25.0),
            "duell_faktor_30": duell(30.0),
            "duell_faktor_35": duell(35.0),
            "kipp_faktor_basis": kipp_faktor(),
            "kipp_faktor_bei_1pz_wert": kipp_faktor(0.01),
            "kipp_faktor_bei_3pz_wert": kipp_faktor(0.03),
            # Unsicherheits-Spanne ueber die drei grossen Stellschrauben (Marken-
            # kern: Modell statt Meinung). Alle jeweils "ceteris paribus".
            "kipp_faktor_bei_zins_2pz": kipp_faktor(zins=0.02),
            "kipp_faktor_bei_zins_5pz": kipp_faktor(zins=0.05),
            "kipp_faktor_bei_etf_5pz": kipp_faktor(etf_r=0.05),
            "kipp_faktor_bei_etf_8pz": kipp_faktor(etf_r=0.08)}


def _selbsttest():
    assert duell(18.0)["vorteil_kaufen"] > 0            # billig kaufen gewinnt
    assert duell(38.0)["vorteil_kaufen"] < 0            # teuer kaufen verliert
    k = kipp_faktor()
    assert 20.0 < k < 33.0                              # plausible Groessenordnung
    assert abs(duell(k)["vorteil_kaufen"]) < 25_000     # am Kipp ~neutral (von Mio.)
    assert kipp_faktor(0.03) > k > kipp_faktor(0.01)    # mehr Wertsteigerung vertraegt mehr Preis
    # Richtungs-Checks der neuen Stellschrauben (fuer die Unsicherheits-Aussage):
    assert kipp_faktor(zins=0.02) > k > kipp_faktor(zins=0.05)   # billiger Kredit -> Kaufen vertraegt mehr Preis
    assert kipp_faktor(etf_r=0.05) > k > kipp_faktor(etf_r=0.08)  # hoehere ETF-Rendite -> Mieten gewinnt frueher
    # Gesamtspanne der drei grossen Treiber bleibt im nennbaren Korridor ~18-28:
    spanne = [kipp_faktor(0.01), kipp_faktor(0.03), kipp_faktor(zins=0.02),
              kipp_faktor(zins=0.05), kipp_faktor(etf_r=0.05), kipp_faktor(etf_r=0.08)]
    assert 17.0 < min(spanne) and max(spanne) < 28.0


if __name__ == "__main__":
    _selbsttest()
    z = zahlen()
    Path(__file__).with_name("e002_zahlen.json").write_text(
        json.dumps(z, indent=2, ensure_ascii=False))
    print(json.dumps(z, indent=2, ensure_ascii=False))
