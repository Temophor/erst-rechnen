"""E006 — Vermietete Eigentumswohnung vs. ETF: 30 Jahre, faires Cashflow-Matching.

Fairness-Prinzip (der methodische Kern der Folge): Beide Anleger schiessen in jedem
Jahr EXAKT gleich viel externes Geld zu. Der Immo-Kaeufer muss negative Cashflows
decken; der ETF-Anleger investiert denselben Betrag in den ETF. Positive Immo-
Cashflows fliessen in einen ETF-Nebentopf des Kaeufers. Am Ende zaehlt Endvermoegen.

Annahmen (Tafel): Preis 300.000 € (B-Stadt, 75 m2), Nebenkosten 10 % (30.000),
EK 60.000 -> Darlehen 270.000 zu 3,6 % (verifiziert 07/2026), 2 % Anfangstilgung.
Miete 875 €/Mo kalt (3,5 % brutto), Mietsteigerung 2 %/J. Nicht umlegbare Kosten
20 % der Miete + Instandhaltung 1 % des Gebaeudewerts. AfA 2 % auf 70 % Gebaeudeanteil.
Grenzsteuersatz 42 %. Verkauf nach 30 J steuerfrei (§ 23 EStG, >10 J).
Mietausfall: 2 % der Miete. ETF 6,5 %, Endbesteuerung effektiv 18,46 % auf Gewinne
(Vorabpauschale vernachlaessigt — Tafel-Hinweis).
NICHT bepreist (ehrlich benennen!): Eigenarbeit des Vermieters (~20-40 h/Jahr),
Klumpenrisiko, Sanierungs-Sonderschocks — dafuer Sensitivitaets-Szenario."""

from __future__ import annotations
import json
from pathlib import Path

PREIS, NEBENKOSTEN, EK = 300_000.0, 30_000.0, 60_000.0
ZINS, TILGUNG = 0.036, 0.02
MIETE_JAHR = 10_500.0
MIETSTEIGERUNG = 0.02
KOSTENQUOTE, INSTAND = 0.20, 2_100.0
MIETAUSFALL = 0.02
AFA = 0.02 * (PREIS * 0.70)
STEUERSATZ = 0.42
JAHRE = 30
ETF_RENDITE, ETF_ENDSTEUER = 0.065, 0.1846


def _etf_abgelten(wert: float, eingezahlt: float) -> float:
    return round(wert - max(0.0, wert - eingezahlt) * ETF_ENDSTEUER, 2)


def simulation(wertsteigerung: float, instand_faktor: float = 1.0) -> dict:
    darlehen = PREIS + NEBENKOSTEN - EK
    rate = darlehen * (ZINS + TILGUNG)
    restschuld = darlehen
    miete = MIETE_JAHR
    instand = INSTAND * instand_faktor
    nebentopf, nebentopf_einzahlungen = 0.0, 0.0
    etf, etf_einzahlungen = EK, EK
    zuschuesse = 0.0
    afa_jahre = 0
    for _ in range(JAHRE):
        zins_anteil = restschuld * ZINS
        einnahmen = miete * (1 - MIETAUSFALL)
        kosten = miete * KOSTENQUOTE + instand
        afa = AFA if afa_jahre < 50 else 0.0
        steuer_ergebnis = einnahmen - kosten - zins_anteil - afa
        steuer = steuer_ergebnis * STEUERSATZ          # negativ = Erstattung
        kredit_zahlung = min(rate, restschuld * (1 + ZINS))
        cashflow = einnahmen - kosten - kredit_zahlung - steuer
        if cashflow < 0:
            zuschuesse += -cashflow
            etf = etf * (1 + ETF_RENDITE) + (-cashflow)
            etf_einzahlungen += -cashflow
            nebentopf *= (1 + ETF_RENDITE)
        else:
            etf *= (1 + ETF_RENDITE)
            nebentopf = nebentopf * (1 + ETF_RENDITE) + cashflow
            nebentopf_einzahlungen += cashflow
        restschuld = max(0.0, restschuld + zins_anteil - kredit_zahlung)
        miete *= (1 + MIETSTEIGERUNG)
        instand *= (1 + MIETSTEIGERUNG)
        afa_jahre += 1
    immo_wert = PREIS * (1 + wertsteigerung) ** JAHRE
    immo_vermoegen = immo_wert - restschuld + _etf_abgelten(nebentopf, nebentopf_einzahlungen)
    etf_vermoegen = _etf_abgelten(etf, etf_einzahlungen)
    return {"wertsteigerung": wertsteigerung,
            "zuschuesse_gesamt": round(zuschuesse, 2),
            "restschuld_ende": round(restschuld, 2),
            "immo_endvermoegen": round(immo_vermoegen, 2),
            "etf_endvermoegen": round(etf_vermoegen, 2),
            "vorteil_immo": round(immo_vermoegen - etf_vermoegen, 2)}


def kipppunkt_wertsteigerung() -> float:
    lo, hi = -0.02, 0.08
    for _ in range(60):
        mid = (lo + hi) / 2
        if simulation(mid)["vorteil_immo"] < 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def zahlen() -> dict:
    szen = {f"g_{g:.0%}": simulation(g) for g in (0.0, 0.01, 0.02, 0.03)}
    return {"annahmen": {"preis": PREIS, "nebenkosten": NEBENKOSTEN, "ek": EK,
                         "zins": ZINS, "tilgung": TILGUNG, "miete_jahr": MIETE_JAHR,
                         "steuersatz": STEUERSATZ, "etf_rendite": ETF_RENDITE},
            "szenarien": szen,
            "kipppunkt_wertsteigerung": kipppunkt_wertsteigerung(),
            "sanierungsschock_bei_2pz": simulation(0.02, instand_faktor=2.0)["vorteil_immo"]}


def _selbsttest():
    assert simulation(0.03)["vorteil_immo"] > simulation(0.0)["vorteil_immo"]
    s = simulation(0.02)
    assert s["restschuld_ende"] < 40_000                 # nach 30 J fast getilgt
    k = kipppunkt_wertsteigerung()
    assert 0.0 < k < 0.06
    assert abs(simulation(k)["vorteil_immo"]) < 3_000    # am Kipppunkt ~ neutral
    assert simulation(0.02, 2.0)["vorteil_immo"] < s["vorteil_immo"]


def _frage(text: str, standard: float, einheit: str = "", skaliert: bool = False) -> float:
    """skaliert=True: Eingabe wird durch 100 geteilt (fuer %-Werte)."""
    anzeige = standard * 100 if skaliert else standard
    raw = input(f"{text} [{anzeige:g}{einheit}]: ").strip().replace(",", ".")
    if not raw:
        return standard
    wert = float(raw)
    return wert / 100 if skaliert else wert


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--interaktiv", "-i", action="store_true",
                    help="Fragt nach deinen eigenen Zahlen, statt die Standardwerte zu benutzen.")
    args = ap.parse_args()

    _selbsttest()  # validiert die Rechenlogik mit den eingebauten Standardwerten

    if args.interaktiv:
        print("Trag deine eigenen Zahlen ein (Enter = Standardwert uebernehmen).\n")
        PREIS = _frage("Kaufpreis", PREIS, " EUR")
        NEBENKOSTEN = _frage("Kaufnebenkosten", NEBENKOSTEN, " EUR")
        EK = _frage("Eigenkapital", EK, " EUR")
        ZINS = _frage("Kreditzins", ZINS, "%", skaliert=True)
        TILGUNG = _frage("Anfangstilgung", TILGUNG, "%", skaliert=True)
        MIETE_JAHR = _frage("Kaltmiete pro Jahr", MIETE_JAHR, " EUR")
        ETF_RENDITE = _frage("Erwartete ETF-Rendite", ETF_RENDITE, "%", skaliert=True)
        AFA = 0.02 * (PREIS * 0.70)
        print()

    z = zahlen()
    Path(__file__).with_name("e006_zahlen.json").write_text(
        json.dumps(z, indent=2, ensure_ascii=False))

    s2 = z["szenarien"]["g_2%"]
    print(f"""
{'=' * 64}
E006 -- Vermietete Wohnung oder ETF? (30 Jahre, faires Cashflow-Matching)
{'=' * 64}

Deine Annahmen (Konstanten oben in der Datei aendern fuer deine Situation):
  Kaufpreis:      {PREIS:,.0f} EUR
  Eigenkapital:   {EK:,.0f} EUR
  Zins / Tilgung: {ZINS:.1%} / {TILGUNG:.1%}
  Kaltmiete p.a.: {MIETE_JAHR:,.0f} EUR
  ETF-Rendite:    {ETF_RENDITE:.1%}

Ergebnis bei 2 % jaehrlicher Wertsteigerung:
  Zuschuesse noetig (Cashflow-Deckung): {s2['zuschuesse_gesamt']:,.0f} EUR ueber 30 Jahre
  Endvermoegen Wohnung: {s2['immo_endvermoegen']:,.0f} EUR
  Endvermoegen ETF:     {s2['etf_endvermoegen']:,.0f} EUR
  Vorteil Wohnung:      {s2['vorteil_immo']:+,.0f} EUR

  -> Kipppunkt: Ab {z['kipppunkt_wertsteigerung']:.1%} Wertsteigerung pro Jahr schlaegt
     die Wohnung den ETF.

Vollstaendige Rohdaten (auch in e006_zahlen.json):
{json.dumps(z, indent=2, ensure_ascii=False)}
""")
