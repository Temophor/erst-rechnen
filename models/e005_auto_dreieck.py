"""E005 — Leasing vs. Neukauf vs. Gebrauchtwagen: 10-Jahres-Gesamtkosten.

Beispiel-Deal + Wertverlust-Annahmen (Tafel; ⚠️ vor Produktion an einem echten
aktuellen Leasing-Angebot + DAT/ADAC-Restwerten spiegeln):
Kompaktklasse, Neupreis 32.000 €. Leasing 299 €/Mo, 990 € Anzahlung, 36 Monate,
Ueberfuehrung 890 €. Wertverlust Kauf: 3 Jahre -37 %, danach ~ -9 %/Jahr.
Gebrauchtkauf: 3 Jahre alt fuer 20.160 € (= 63 % Neupreis).
Wartung: Neuwagen J1-3 300 €/J, danach altersabhaengig steigend (400 + 60·(alter-3)).
Leasing: Vollkasko-Pflicht +300 €/J gegenueber Vergleichsfall.
Opportunitaetskosten: gebundenes Kapital zu 1,84 % (Tagesgeld netto) verzinst.
Versicherung/Steuer-Basis fuer alle gleich -> nur Differenzen modelliert."""

from __future__ import annotations
import json
from pathlib import Path

JAHRE = 10
NEUPREIS = 32_000.0
LEASING_RATE, LEASING_ANZAHLUNG, LEASING_UEBERF = 299.0, 990.0, 890.0
LEASING_ZYKLUS_JAHRE = 3
GEBRAUCHT_ALTER = 3
OPP_ZINS = 0.0184


def restwert(alter_jahre: float) -> float:
    if alter_jahre <= 3:
        return NEUPREIS * (1 - 0.37 * alter_jahre / 3)
    return NEUPREIS * 0.63 * (0.91 ** (alter_jahre - 3))


def wartung(alter: int) -> float:
    return 300.0 if alter <= 3 else 400.0 + 60.0 * (alter - 3)


def leasing_kosten() -> float:
    zyklen = JAHRE / LEASING_ZYKLUS_JAHRE
    raten = LEASING_RATE * 12 * JAHRE
    fixkosten = (LEASING_ANZAHLUNG + LEASING_UEBERF) * zyklen
    vollkasko_extra = 300.0 * JAHRE
    wartung_leasing = 300.0 * JAHRE          # immer Neuwagenalter
    return round(raten + fixkosten + vollkasko_extra + wartung_leasing, 2)


def kauf_kosten(kaufalter: int) -> float:
    kaufpreis = restwert(kaufalter)
    endalter = kaufalter + JAHRE
    rest = restwert(endalter)
    wart = sum(wartung(kaufalter + j) for j in range(1, JAHRE + 1))
    kapitalkosten = kaufpreis * ((1 + OPP_ZINS) ** JAHRE - 1)
    return round(kaufpreis - rest + wart + kapitalkosten, 2)


def zahlen() -> dict:
    lease = leasing_kosten()
    neu = kauf_kosten(0)
    gebraucht = kauf_kosten(GEBRAUCHT_ALTER)
    return {"annahmen": {"neupreis": NEUPREIS, "leasing_rate": LEASING_RATE,
                         "jahre": JAHRE, "wertverlust_3j": 0.37,
                         "gebraucht_kaufpreis": round(restwert(GEBRAUCHT_ALTER), 2),
                         "opp_zins": OPP_ZINS},
            "dauerleasing_10j": lease,
            "neukauf_10j": neu,
            "gebraucht_10j": gebraucht,
            "leasing_vs_gebraucht": round(lease - gebraucht, 2),
            "neukauf_vs_gebraucht": round(neu - gebraucht, 2),
            "monatskosten": {"leasing": round(lease / 120, 2),
                             "neukauf": round(neu / 120, 2),
                             "gebraucht": round(gebraucht / 120, 2)}}


def _selbsttest():
    assert abs(restwert(0) - NEUPREIS) < 0.01 and abs(restwert(3) - NEUPREIS * 0.63) < 0.01
    assert restwert(10) < restwert(5) < restwert(3)
    z = zahlen()
    assert z["dauerleasing_10j"] > z["neukauf_10j"] > z["gebraucht_10j"]
    assert wartung(10) > wartung(4) > 0


if __name__ == "__main__":
    _selbsttest()
    z = zahlen()
    Path(__file__).with_name("e005_zahlen.json").write_text(
        json.dumps(z, indent=2, ensure_ascii=False))
    print(json.dumps(z, indent=2, ensure_ascii=False))
