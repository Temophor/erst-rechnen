"""E001 — Sondertilgung vs. ETF, das Finanzmodell hinter der Folge.

Vergleich (geschlossener Topf, 12 Jahre = restliche Zinsbindung):
  A) 10.000 EUR Sondertilgung heute. Annuitaet bleibt unveraendert, der Kredit tilgt
     schneller; der Vermoegensvorteil am Ende der Zinsbindung entspricht exakt
     10.000 * (1 + sollzins/12)^(12*jahre)  (solange der Kredit nicht vorher auslaeuft).
     Steuerfrei und garantiert.
  B) 10.000 EUR in einen thesaurierenden Aktien-ETF. Jaehrlich Vorabpauschale
     (Basiszins-Regel, Teilfreistellung 30 %), am Ende Verkauf mit Abgeltungsteuer;
     bereits versteuerte Vorabpauschalen mindern den steuerpflichtigen Gewinn.

Bewusste Vereinfachungen (stehen auf der Annahmen-Tafel der Folge):
  * Basiszins ueber die Laufzeit konstant (tatsaechlich jaehrlich neu vom BMF).
  * Sparerpauschbetrag anderweitig ausgeschoepft (konservativ fuer den ETF-Pfad).
  * Vorabpauschale-Steuer wird aus dem Topf bezahlt (Anteilsverkauf); der dabei
    realisierte Mini-Gewinn wird vernachlaessigt (Effekt zweiter Ordnung).
  * ETF-Rendite als konstante Jahresrate; Schwankung zeigt die Folge separat
    als Percentile-Faecher (Monte Carlo, lognormal).

Quellen (Stand Juli 2026, vor Produktion erneut pruefen):
  * Basiszins 2026: 3,20 % — BMF-Schreiben vom 13.01.2026 (§ 18 Abs. 4 InvStG)
  * Abgeltungsteuer inkl. Soli: 26,375 % (25 % * 1,055), ohne Kirchensteuer
  * Teilfreistellung Aktienfonds: 30 % (§ 20 InvStG)
  * Bauzins-Niveau 10J Mitte 2026: ~3,5-4,0 % (baufivergleich.de 06/2026: Top ~3,60 %)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Params:
    einmalbetrag: float = 10_000.0
    jahre: int = 12
    sollzins: float = 0.036          # Kredit-Sollzins p.a., monatliche Verrechnung
    etf_rendite: float = 0.065       # nominal p.a., vor Steuern
    basiszins: float = 0.032         # BMF 2026
    teilfreistellung: float = 0.30   # Aktienfonds
    abgeltungsteuer: float = 0.26375 # inkl. Soli, ohne Kirchensteuer


def sondertilgung_endwert(p: Params) -> float:
    """Garantierter Vermoegensvorteil der Sondertilgung am Ende der Zinsbindung."""
    return p.einmalbetrag * (1 + p.sollzins / 12) ** (12 * p.jahre)


def etf_endwert_netto(p: Params, rendite: float | None = None) -> dict:
    """ETF-Endwert nach Vorabpauschalen und Verkaufssteuer (geschlossener Topf)."""
    r = p.etf_rendite if rendite is None else rendite
    steuersatz_effektiv = (1 - p.teilfreistellung) * p.abgeltungsteuer
    wert = p.einmalbetrag
    vap_summe = 0.0          # bereits versteuerte Vorabpauschalen (mindern Verkaufsgewinn)
    vap_steuern = 0.0
    for _ in range(p.jahre):
        wert_anfang = wert
        wert_ende = wert_anfang * (1 + r)
        jahresgewinn = wert_ende - wert_anfang
        basisertrag = wert_anfang * p.basiszins * 0.7
        vap = max(0.0, min(basisertrag, jahresgewinn))
        steuer = vap * steuersatz_effektiv
        wert = wert_ende - steuer
        vap_summe += vap
        vap_steuern += steuer
    brutto_gewinn = wert - p.einmalbetrag
    steuerpflichtig = max(0.0, brutto_gewinn - vap_summe)
    verkaufssteuer = steuerpflichtig * steuersatz_effektiv
    netto = wert - verkaufssteuer
    return {
        "wert_vor_verkaufssteuer": wert,
        "vap_summe": vap_summe,
        "vap_steuern": vap_steuern,
        "verkaufssteuer": verkaufssteuer,
        "endwert_netto": netto,
        "steuern_gesamt": vap_steuern + verkaufssteuer,
    }


def kipppunkt_rendite(p: Params, lo: float = 0.0, hi: float = 0.20) -> float:
    """ETF-Rendite (vor Steuern), bei der beide Wege exakt gleich enden. Bisektion."""
    ziel = sondertilgung_endwert(p)
    f = lambda r: etf_endwert_netto(p, r)["endwert_netto"] - ziel
    if f(lo) > 0 or f(hi) < 0:
        raise ValueError("Kipppunkt liegt ausserhalb des Suchintervalls")
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def sensitivitaet(p: Params, zinsen: list[float], renditen: list[float]) -> list[dict]:
    """Grid: fuer jeden Kreditzins der Kipppunkt + Gewinner bei gegebener ETF-Erwartung."""
    zeilen = []
    for z in zinsen:
        q = Params(**{**asdict(p), "sollzins": z})
        kp = kipppunkt_rendite(q)
        zeilen.append({
            "sollzins": z,
            "kipppunkt": kp,
            "gewinner_bei_erwartung": "ETF" if p.etf_rendite > kp else "Sondertilgung",
        })
    return zeilen


def monte_carlo_faecher(p: Params, mu: float = 0.065, sigma: float = 0.15,
                        n: int = 20_000, seed: int = 1) -> dict:
    """Percentile des ETF-Netto-Endwerts bei lognormalen Jahresrenditen.

    mu/sigma beziehen sich auf die arithmetische Jahresrendite; simuliert wird
    jahresweise, Steuern wie im deterministischen Modell.
    """
    import random
    rng = random.Random(seed)
    m = math.log(1 + mu) - 0.5 * (sigma / (1 + mu)) ** 2
    s = sigma / (1 + mu)
    ergebnisse = []
    steuersatz_effektiv = (1 - p.teilfreistellung) * p.abgeltungsteuer
    for _ in range(n):
        wert, vap_summe = p.einmalbetrag, 0.0
        for _ in range(p.jahre):
            r = math.exp(rng.gauss(m, s)) - 1
            wert_anfang = wert
            wert_ende = wert_anfang * (1 + r)
            vap = max(0.0, min(wert_anfang * p.basiszins * 0.7, wert_ende - wert_anfang))
            wert = wert_ende - vap * steuersatz_effektiv
            vap_summe += vap
        steuerpflichtig = max(0.0, wert - p.einmalbetrag - vap_summe)
        ergebnisse.append(wert - steuerpflichtig * steuersatz_effektiv)
    ergebnisse.sort()
    pct = lambda q: ergebnisse[int(q * (n - 1))]
    unter_ziel = sum(1 for e in ergebnisse if e < sondertilgung_endwert(p)) / n
    return {"p10": pct(0.10), "p25": pct(0.25), "p50": pct(0.50),
            "p75": pct(0.75), "p90": pct(0.90),
            "verlust_wahrscheinlichkeit_vs_sondertilgung": unter_ziel}


def episode_zahlen(p: Params | None = None) -> dict:
    p = p or Params()
    st = sondertilgung_endwert(p)
    etf = etf_endwert_netto(p)
    kp = kipppunkt_rendite(p)
    altkredit = Params(**{**asdict(p), "sollzins": 0.012})
    zahlen = {
        "params": asdict(p),
        "sondertilgung_endwert": round(st, 2),
        "etf": {k: round(v, 2) for k, v in etf.items()},
        "etf_vorsprung_netto": round(etf["endwert_netto"] - st, 2),
        "kipppunkt_rendite_vor_steuern": round(kp, 5),
        "kipppunkt_altkredit_1_2_prozent": round(kipppunkt_rendite(altkredit), 5),
        "sensitivitaet": [
            {**z, "kipppunkt": round(z["kipppunkt"], 5)}
            for z in sensitivitaet(p, [0.012, 0.02, 0.028, 0.036, 0.044], [])
        ],
        "monte_carlo": {k: round(v, 4) for k, v in monte_carlo_faecher(p).items()},
    }
    return zahlen


if __name__ == "__main__":
    zahlen = episode_zahlen()
    out = Path(__file__).with_name("e001_zahlen.json")
    out.write_text(json.dumps(zahlen, indent=2, ensure_ascii=False))

    p = zahlen["params"]
    print(f"""
{'=' * 64}
E001 -- Sondertilgung oder ETF?
{'=' * 64}

Deine Annahmen (Params-Klasse oben in der Datei aendern fuer deine Situation):
  Einmalbetrag:          {p['einmalbetrag']:,.0f} EUR
  Restlaufzeit:          {p['jahre']} Jahre
  Kreditzins:            {p['sollzins']:.3%} p.a.
  Erwartete ETF-Rendite: {p['etf_rendite']:.3%} p.a. (vor Steuern)

Ergebnis nach {p['jahre']} Jahren:
  Sondertilgung (garantiert, steuerfrei): {zahlen['sondertilgung_endwert']:,.0f} EUR
  ETF (nach allen Steuern):               {zahlen['etf']['endwert_netto']:,.0f} EUR
  Vorsprung ETF:                          {zahlen['etf_vorsprung_netto']:+,.0f} EUR

  -> Kipppunkt: Ab {zahlen['kipppunkt_rendite_vor_steuern']:.2%} erwarteter ETF-Rendite
     (vor Steuern) schlaegt der ETF die Sondertilgung.

Vollstaendige Rohdaten (auch in e001_zahlen.json):
{json.dumps(zahlen, indent=2, ensure_ascii=False)}
""")
