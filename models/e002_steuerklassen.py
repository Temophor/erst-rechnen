"""E002 — Steuerklasse 3/5 vs. 4/4: Liquiditaet vs. echtes Geld (Elterngeld-Hebel).

Kernaussagen, die das Modell belegen soll:
  1. Die JAHRES-Steuer ist bei Verheirateten identisch, egal welche Klassen-Kombi —
     die Veranlagung (Splittingtarif) korrigiert alles. 3/5 verschiebt nur Liquiditaet.
  2. Wer 3/5 waehlt, bekommt unterjaehrig mehr Netto und zahlt es bei der
     Steuererklaerung zurueck (Nachzahlung) — ein zinsloser Kredit, kein Geschenk.
  3. ECHTES Geld entsteht nur ueber Lohnersatzleistungen: Elterngeld bemisst sich
     am Netto — die Klasse des kuenftig pausierenden Elternteils entscheidet
     ueber tausende Euro. (Frist: Wechsel muss i.d.R. 7 Monate vor Beginn des
     Mutterschutzes wirksam sein — im Video betonen!)

Vereinfachungen (Tafel): LSt-Naeherung nach § 39b auf Jahresbetrag ~ Brutto;
SV pauschal 21 % (Elterngeldstellen-Logik); kein Soli/Kirchensteuer.
Reform-Hinweis: Abschaffung 3/5 ist politisch geplant (Umstellung auf 4/4 mit
Faktor), Stand 07/2026 nicht in Kraft — vor Produktion checken."""

from __future__ import annotations
import json
from pathlib import Path

from steuer_2026 import est_splitting, lst_klasse, netto_monat

BRUTTO_A = 58_000.0   # Lisa
BRUTTO_B = 32_000.0   # Jan (geht in Elternzeit)
ELTERNGELD_SATZ = 0.65
ELTERNGELD_MAX = 1_800.0
BEZUGSMONATE = 12


def kombi(brutto_a: float, ka: int, brutto_b: float, kb: int) -> dict:
    netto_a, netto_b = netto_monat(brutto_a, ka), netto_monat(brutto_b, kb)
    lst_summe = lst_klasse(brutto_a, ka) + lst_klasse(brutto_b, kb)
    veranlagt = est_splitting(brutto_a + brutto_b)
    return {"netto_monat_gesamt": round(netto_a + netto_b, 2),
            "netto_a": netto_a, "netto_b": netto_b,
            "lohnsteuer_jahr": round(lst_summe, 2),
            "veranlagte_est": veranlagt,
            "erstattung": round(lst_summe - veranlagt, 2)}  # negativ = Nachzahlung


def elterngeld_monat(brutto: float, klasse: int) -> float:
    return round(min(ELTERNGELD_MAX, ELTERNGELD_SATZ * netto_monat(brutto, klasse)), 2)


def zahlen() -> dict:
    k44 = kombi(BRUTTO_A, 4, BRUTTO_B, 4)
    k35 = kombi(BRUTTO_A, 3, BRUTTO_B, 5)   # klassisch: Besserverdiener nimmt 3
    k53 = kombi(BRUTTO_A, 5, BRUTTO_B, 3)   # Elterngeld-Optimierung: Jan nimmt 3!
    eg = {f"klasse_{k}": elterngeld_monat(BRUTTO_B, k) for k in (3, 4, 5)}
    eg_hebel = round((eg["klasse_3"] - eg["klasse_5"]) * BEZUGSMONATE, 2)
    return {
        "annahmen": {"brutto_a": BRUTTO_A, "brutto_b": BRUTTO_B,
                     "elterngeld_satz": ELTERNGELD_SATZ, "bezugsmonate": BEZUGSMONATE,
                     "sv_pauschal": 0.21, "hinweis": "LSt-Naeherung §39b, ohne Soli/KiSt"},
        "kombi_4_4": k44, "kombi_3_5": k35, "kombi_5_3": k53,
        "monats_plus_durch_3_5": round(k35["netto_monat_gesamt"] - k44["netto_monat_gesamt"], 2),
        "nachzahlung_bei_3_5": round(-k35["erstattung"], 2),
        "jahressteuer_identisch": k44["veranlagte_est"] == k35["veranlagte_est"] == k53["veranlagte_est"],
        "elterngeld_jan_je_klasse": eg,
        "elterngeld_hebel_12_monate": eg_hebel,
    }


def _selbsttest():
    z = zahlen()
    assert z["jahressteuer_identisch"] is True            # Kernaussage 1
    assert z["monats_plus_durch_3_5"] > 0                 # 3/5 fuehlt sich reicher an
    assert z["nachzahlung_bei_3_5"] > 0                   # ... und zahlt zurueck
    assert z["elterngeld_jan_je_klasse"]["klasse_3"] > z["elterngeld_jan_je_klasse"]["klasse_5"]
    k = kombi(BRUTTO_A, 4, BRUTTO_B, 4)
    assert abs(k["erstattung"]) < 1500                    # 4/4 liegt nah an der Veranlagung


if __name__ == "__main__":
    _selbsttest()
    z = zahlen()
    Path(__file__).with_name("e002_zahlen.json").write_text(
        json.dumps(z, indent=2, ensure_ascii=False))
    print(json.dumps(z, indent=2, ensure_ascii=False))
