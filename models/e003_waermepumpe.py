"""E003 — Waermepumpe vs. neue Gasheizung, 20-Jahres-Vollkosten (Barwert).

Quellen (07/2026): KfW-458-Foerderung 30-70 %, foerderfaehig max. 30.000 € (max. 21.000 €
Zuschuss), Konditionen laut Koalition "auskoemmlich" bis mind. 2029 (energie-fachberater/KfW).
Gas-Arbeitspreis Mittel 9,31 ct/kWh (TGA-Barometer 03/2026), WP-Stromtarif ~20-27 ct
(Ansatz 22 ct, § 14a-Module), CO2-Preis 2026: 55-65 €/t, ETS2 ab 2027 marktbasiert.
Gas-Emissionsfaktor 0,201 kg CO2/kWh.

Persona: Bestandshaus 140 m2, 18.000 kWh Gasverbrauch, Heizung von 2003 stirbt.
Annahmen (Tafel): WP-Vollinstallation 28.000 € (Bestand, inkl. Puffer/Anpassung),
Gastherme neu 11.000 €. JAZ 3,5. Kesselwirkungsgrad alt->neu 95 %. Diskontsatz 3 %.
Energiepreissteigerung real: Strom +1 %/J, Gas +1 %/J ZUZUEGLICH CO2-Pfad."""

from __future__ import annotations
import json
from pathlib import Path

JAHRE = 20
DISKONT = 0.03
GAS_KWH = 18_000.0
WAERMEBEDARF = GAS_KWH * 0.95          # nutzbare Waerme der neuen Gastherme
JAZ = 3.5
WP_INVEST, GAS_INVEST = 28_000.0, 11_000.0
FOERDERSATZ = 0.55                      # 30 % Basis + 20 % Klimabonus + 5 % Effizienz
FOERDER_DECKEL = 30_000.0
GAS_ARBEITSPREIS = 0.0931               # €/kWh inkl. heutigem CO2-Anteil
WP_STROMPREIS = 0.22
CO2_HEUTE = 60.0                        # €/t (Mitte der 55-65-Spanne)
CO2_FAKTOR = 0.000201                   # t CO2 pro kWh Gas
PREISSTEIGERUNG = 0.01
WARTUNG_GAS = 180.0                     # inkl. Schornsteinfeger
WARTUNG_WP = 100.0


def co2_pfad(jahr: int, ziel_2045: float) -> float:
    """Linearer CO2-Preispfad von heute bis zum Zielwert 2045."""
    return CO2_HEUTE + (ziel_2045 - CO2_HEUTE) * min(1.0, jahr / 19)


def barwert_kosten(invest: float, jahreskosten_fn) -> float:
    bw = invest
    for j in range(JAHRE):
        bw += jahreskosten_fn(j) / (1 + DISKONT) ** (j + 1)
    return round(bw, 2)


def gas_jahreskosten(jahr: int, co2_ziel: float) -> float:
    basis = GAS_KWH * (GAS_ARBEITSPREIS - CO2_HEUTE * CO2_FAKTOR)  # Energie ohne CO2
    basis *= (1 + PREISSTEIGERUNG) ** jahr
    co2 = GAS_KWH * CO2_FAKTOR * co2_pfad(jahr, co2_ziel)
    return basis + co2 + WARTUNG_GAS


def wp_jahreskosten(jahr: int) -> float:
    strom = (WAERMEBEDARF / JAZ) * WP_STROMPREIS * (1 + PREISSTEIGERUNG) ** jahr
    return strom + WARTUNG_WP


def vergleich(co2_ziel: float, foerdersatz: float = FOERDERSATZ) -> dict:
    zuschuss = min(WP_INVEST, FOERDER_DECKEL) * foerdersatz
    wp = barwert_kosten(WP_INVEST - zuschuss, wp_jahreskosten)
    gas = barwert_kosten(GAS_INVEST, lambda j: gas_jahreskosten(j, co2_ziel))
    return {"co2_ziel_2045": co2_ziel, "foerdersatz": foerdersatz,
            "zuschuss": round(zuschuss, 2), "barwert_wp": wp, "barwert_gas": gas,
            "vorteil_wp": round(gas - wp, 2)}


def kipppunkt_foerderung(co2_ziel: float) -> float:
    """Foerdersatz, ab dem die WP gewinnt (Bisektion)."""
    lo, hi = 0.0, 0.70
    if vergleich(co2_ziel, hi)["vorteil_wp"] < 0:
        return float("nan")
    if vergleich(co2_ziel, lo)["vorteil_wp"] > 0:
        return 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if vergleich(co2_ziel, mid)["vorteil_wp"] < 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def zahlen() -> dict:
    szenarien = {f"co2_{z:.0f}": vergleich(z) for z in (60.0, 150.0, 250.0)}
    jahr1 = {"gas_jahr_1": round(gas_jahreskosten(0, 150), 2),
             "wp_jahr_1": round(wp_jahreskosten(0), 2)}
    return {
        "annahmen": {"wp_invest": WP_INVEST, "gas_invest": GAS_INVEST,
                     "foerdersatz": FOERDERSATZ, "jaz": JAZ,
                     "gas_arbeitspreis": GAS_ARBEITSPREIS, "wp_strompreis": WP_STROMPREIS,
                     "co2_heute": CO2_HEUTE, "diskont": DISKONT, "jahre": JAHRE},
        "jahr_1": jahr1,
        "szenarien": szenarien,
        "ohne_foerderung_bei_co2_150": vergleich(150.0, 0.0)["vorteil_wp"],
        "kipppunkt_foerdersatz_bei_co2_konstant": kipppunkt_foerderung(60.0),
        "kipppunkt_foerdersatz_bei_co2_150": kipppunkt_foerderung(150.0),
    }


def _selbsttest():
    v = vergleich(150.0)
    assert abs(v["zuschuss"] - 28_000 * 0.55) < 0.01
    # Monotonie: hoeherer CO2-Pfad -> WP-Vorteil groesser
    assert vergleich(250.0)["vorteil_wp"] > vergleich(60.0)["vorteil_wp"]
    # Mehr Foerderung -> WP besser
    assert vergleich(150.0, 0.7)["vorteil_wp"] > vergleich(150.0, 0.3)["vorteil_wp"]
    # Jahr-1-Betriebskosten: WP muss guenstiger sein (JAZ-Effekt)
    assert wp_jahreskosten(0) < gas_jahreskosten(0, 60.0)


if __name__ == "__main__":
    _selbsttest()
    z = zahlen()
    Path(__file__).with_name("e003_zahlen.json").write_text(
        json.dumps(z, indent=2, ensure_ascii=False))

    s150 = z["szenarien"]["co2_150"]
    print(f"""
{'=' * 64}
E003 -- Waermepumpe oder neue Gasheizung? (20-Jahres-Vollkosten, Barwert)
{'=' * 64}

Deine Annahmen (Konstanten oben in der Datei aendern fuer deine Situation):
  Waermepumpe-Invest:   {WP_INVEST:,.0f} EUR (vor Foerderung)
  Gastherme-Invest:     {GAS_INVEST:,.0f} EUR
  Foerdersatz:          {FOERDERSATZ:.0%}
  Jahresarbeitszahl:    {JAZ}
  Gaspreis:             {GAS_ARBEITSPREIS * 100:.2f} ct/kWh
  Stromtarif (WP):      {WP_STROMPREIS * 100:.0f} ct/kWh
  CO2-Preis heute:      {CO2_HEUTE:.0f} EUR/t

Ergebnis (CO2-Pfad Richtung 150 EUR/t bis 2045):
  Waermepumpe (20 Jahre, Barwert): {s150['barwert_wp']:,.0f} EUR
  Gasheizung  (20 Jahre, Barwert): {s150['barwert_gas']:,.0f} EUR
  Vorteil Waermepumpe:             {s150['vorteil_wp']:+,.0f} EUR

  -> Ohne Foerderung kippt das Ergebnis: {z['ohne_foerderung_bei_co2_150']:+,.0f} EUR Vorteil WP.
  -> Kipppunkt-Foerdersatz (damit die WP gewinnt): {z['kipppunkt_foerdersatz_bei_co2_150']:.0%}

Vollstaendige Rohdaten (auch in e003_zahlen.json):
{json.dumps(z, indent=2, ensure_ascii=False)}
""")
