"""E004 — Rente mit 63: Break-even der Abschlaege.

Quellen (07/2026): aktueller Rentenwert 42,52 € ab 01.07.2026 (DRV/Bundesregierung),
Standardrente 45 EP = 1.913,40 €. Abschlag 0,3 %/Monat vorgezogen (max 14,4 %).
Regelaltersgrenze Jahrgang 1964+: 67. Fruehrente ab 63 fuer langjaehrig Versicherte (35 J.).
Reform-Lage: Renten-Kommission diskutiert Aenderungen erst fuer die Zeit NACH 2031.

Vereinfachungen (Tafel): Brutto-Vergleich (Steuer + KVdR wirken auf beide Pfade
aehnlich proportional und verschieben den Break-even nur um Monate);
Rentenanpassungen wirken proportional auf beide Pfade -> kuerzen sich im Break-even;
weitergearbeitete Jahre bringen ~1 Entgeltpunkt pro Jahr (Durchschnittsverdiener)."""

from __future__ import annotations
import json
from pathlib import Path

RENTENWERT = 42.52
EP_MIT_63 = 45.0
EP_PRO_JAHR_WEITER = 1.0
MONATE_VORGEZOGEN = 48          # 63 statt 67
ABSCHLAG_PRO_MONAT = 0.003


def rente_63() -> float:
    faktor = 1 - ABSCHLAG_PRO_MONAT * MONATE_VORGEZOGEN   # 0,856
    return round(EP_MIT_63 * RENTENWERT * faktor, 2)


def rente_67() -> float:
    ep = EP_MIT_63 + EP_PRO_JAHR_WEITER * (MONATE_VORGEZOGEN / 12)
    return round(ep * RENTENWERT, 2)


def break_even_alter() -> dict:
    """Ab welchem Alter hat der 67er-Pfad kumuliert mehr Rente erhalten?"""
    r63, r67 = rente_63(), rente_67()
    kum63 = r63 * MONATE_VORGEZOGEN     # Vorsprung bei Start des 67er-Pfads
    monate = 0
    while kum63 > 0 and monate < 12 * 40:
        kum63 -= (r67 - r63)
        monate += 1
    alter = 67 + monate / 12
    return {"rente_63": r63, "rente_67": r67,
            "vorsprung_mit_67_aufzuholen": round(rente_63() * MONATE_VORGEZOGEN, 2),
            "monatsluecke": round(r67 - r63, 2),
            "break_even_alter": round(alter, 1)}


def zahlen() -> dict:
    be = break_even_alter()
    abschlag_euro = round(EP_MIT_63 * RENTENWERT * ABSCHLAG_PRO_MONAT * MONATE_VORGEZOGEN, 2)
    return {
        "annahmen": {"rentenwert": RENTENWERT, "ep_mit_63": EP_MIT_63,
                     "monate_vorgezogen": MONATE_VORGEZOGEN,
                     "abschlag_gesamt": ABSCHLAG_PRO_MONAT * MONATE_VORGEZOGEN,
                     "ep_pro_jahr_weiterarbeit": EP_PRO_JAHR_WEITER},
        **be,
        "abschlag_euro_monat": abschlag_euro,
        "abschlag_euro_lebenslang_pro_jahr": round(abschlag_euro * 12, 2),
        # Lebenserwartung Mann 63 (Sterbetafel 2023/25): ~82; Frau: ~85 (Tafel-Range)
        "lebenserwartung_hinweis": "Mann ~82, Frau ~85 (im Video als Spanne)",
    }


def _selbsttest():
    assert abs(rente_63() - 45 * 42.52 * 0.856) < 0.01           # 1.638 €
    assert abs(rente_67() - 49 * 42.52) < 0.01                    # 2.083 €
    be = break_even_alter()
    assert 78 < be["break_even_alter"] < 86                       # Plausibilitaet
    # Ohne Abschlag und ohne Zusatz-EP: Break-even nie (fruener ist immer besser)
    global ABSCHLAG_PRO_MONAT, EP_PRO_JAHR_WEITER
    a, e = ABSCHLAG_PRO_MONAT, EP_PRO_JAHR_WEITER
    ABSCHLAG_PRO_MONAT, EP_PRO_JAHR_WEITER = 0.0, 0.0
    assert break_even_alter()["break_even_alter"] > 100
    ABSCHLAG_PRO_MONAT, EP_PRO_JAHR_WEITER = a, e


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
        RENTENWERT = _frage("Aktueller Rentenwert", RENTENWERT, " EUR")
        EP_MIT_63 = _frage("Deine Entgeltpunkte bei Rentenbeginn mit 63", EP_MIT_63)
        MONATE_VORGEZOGEN = int(_frage("Monate vorgezogen (z.B. 48 fuer 63 statt 67)", MONATE_VORGEZOGEN, " Monate"))
        EP_PRO_JAHR_WEITER = _frage("Zusaetzliche Entgeltpunkte pro Jahr Weiterarbeit", EP_PRO_JAHR_WEITER)
        print()

    z = zahlen()
    Path(__file__).with_name("e004_zahlen.json").write_text(
        json.dumps(z, indent=2, ensure_ascii=False))

    print(f"""
{'=' * 64}
E004 -- Rente mit 63: Wo liegt der Break-even?
{'=' * 64}

Deine Annahmen (Konstanten oben in der Datei aendern fuer deine Situation):
  Aktueller Rentenwert:            {RENTENWERT:.2f} EUR
  Entgeltpunkte mit 63:            {EP_MIT_63}
  Monate vorgezogen (63 statt 67): {MONATE_VORGEZOGEN}
  Abschlag pro Monat:              {ABSCHLAG_PRO_MONAT:.1%}

Ergebnis:
  Rente ab 63 (mit Abschlag):  {z['rente_63']:,.2f} EUR/Monat
  Rente ab 67 (ohne Abschlag): {z['rente_67']:,.2f} EUR/Monat
  Monatliche Luecke:           {z['monatsluecke']:,.2f} EUR

  -> Break-even-Alter: {z['break_even_alter']:.1f} Jahre -- erst danach hat der
     67er-Pfad kumuliert mehr Rente ausgezahlt bekommen als der 63er-Pfad.

Vollstaendige Rohdaten (auch in e004_zahlen.json):
{json.dumps(z, indent=2, ensure_ascii=False)}
""")
