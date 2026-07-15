"""Gemeinsames Steuer-Modul 2026 — § 32a EStG Tarif + Lohnsteuerklassen-Naeherung.

Quellen (Stand 07/2026):
  * § 32a EStG 2026 (WOERTLICH von gesetze-im-internet.de abgerufen 2026-07-06,
    gilt ab VZ 2026): Grundfreibetrag 12.348 €, Zonen 17.799 / 69.878 / 277.825 €,
    Zone2 (914,51·y+1400)·y; Zone3 (173,10·z+2397)·z+1034,87;
    Zone4 0,42·x−11.135,63; Zone5 0,45·x−19.470,38
  * Lohnsteuer-Naeherungen nach § 39b Abs. 2 EStG:
    Klasse III: Splittingverfahren aufs eigene Einkommen (2·T(x/2))
    Klasse V/VI: 2·(T(1,25·x) − T(0,75·x)), mindestens 14 % (vereinfachte Wiedergabe)
    Klasse IV: Grundtarif T(x)
  Vereinfachung (Annahmen-Tafel!): Wir rechnen auf Ebene des "zu versteuernden
  Jahresbetrags" — Vorsorgepauschale & Co. sind pauschal beruecksichtigt, indem
  Nettoberechnungen SV-Abzuege separat mit ~21 % ansetzen (Elterngeld-Logik)."""

from __future__ import annotations

GRUNDFREIBETRAG = 12_348
SOLI_SATZ = 0.055  # greift erst ab hoher ESt (Freigrenze ~ hier ignoriert, Tafel-Hinweis)
SV_PAUSCHAL = 0.21  # Sozialversicherungs-Pauschale fuer Netto-Naeherung (Elterngeld-Stil)


def est_tarif(zvE: float) -> float:
    """Einkommensteuer 2026 nach § 32a EStG (Grundtarif), zvE abgerundet auf volle €."""
    x = int(zvE)
    if x <= GRUNDFREIBETRAG:
        return 0.0
    if x <= 17_799:
        y = (x - GRUNDFREIBETRAG) / 10_000
        return round((914.51 * y + 1_400) * y, 2)
    if x <= 69_878:
        z = (x - 17_799) / 10_000
        return round((173.10 * z + 2_397) * z + 1_034.87, 2)
    if x <= 277_825:
        return round(0.42 * x - 11_135.63, 2)
    return round(0.45 * x - 19_470.38, 2)


def est_splitting(zvE_gemeinsam: float) -> float:
    """Splittingtarif fuer Verheiratete (Veranlagung)."""
    return round(2 * est_tarif(zvE_gemeinsam / 2), 2)


def lst_klasse(jahresbetrag: float, klasse: int) -> float:
    """Jahres-Lohnsteuer-Naeherung je Steuerklasse (§ 39b Abs. 2)."""
    if klasse in (1, 4):
        return est_tarif(jahresbetrag)
    if klasse == 3:
        return est_splitting(jahresbetrag)
    if klasse in (5, 6):
        st = 2 * (est_tarif(1.25 * jahresbetrag) - est_tarif(0.75 * jahresbetrag))
        return round(max(st, 0.14 * max(0, jahresbetrag - GRUNDFREIBETRAG * 0)), 2) \
            if jahresbetrag > GRUNDFREIBETRAG else round(max(st, 0.0), 2)
    raise ValueError(klasse)


def netto_monat(brutto_jahr: float, klasse: int) -> float:
    """Netto-Naeherung im Elterngeld-Stil: Brutto − LSt(Klasse) − 21 % SV, /12.
    (Elterngeldstellen rechnen mit pauschalierten Abzuegen — genau dieser Logik folgen wir.)"""
    lst = lst_klasse(brutto_jahr * (1 - 0.0), klasse)  # LSt auf Jahresbetrag ~ Brutto (Tafel!)
    return round((brutto_jahr - lst - brutto_jahr * SV_PAUSCHAL) / 12, 2)


def _selbsttest():
    assert est_tarif(12_348) == 0.0
    assert est_tarif(12_349) > 0.0
    # Zonen-Uebergaenge stetig (keine Spruenge > 1 €)
    for grenze in (17_799, 69_878, 277_825):
        assert abs(est_tarif(grenze + 1) - est_tarif(grenze)) < 1.0
    # Splitting: fuer gleiches Einkommen beider = Grundtarif x2
    assert abs(est_splitting(80_000) - 2 * est_tarif(40_000)) < 0.02
    # Klasse 5 zahlt mehr als Klasse 4, Klasse 3 weniger
    assert lst_klasse(30_000, 5) > lst_klasse(30_000, 4) > lst_klasse(30_000, 3)
    # Spitzensteuersatz-Zone: Grenzsteuersatz ~42 %
    d = est_tarif(100_001) - est_tarif(100_000)
    assert 0.41 < d < 0.43


if __name__ == "__main__":
    _selbsttest()
    for z in (20_000, 40_000, 58_000, 80_000):
        print(z, "ESt:", est_tarif(z), "| LSt III:", lst_klasse(z, 3),
              "IV:", lst_klasse(z, 4), "V:", lst_klasse(z, 5))
    print("Selbsttest OK")
