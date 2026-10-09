"""Keine doppelten Funktionsnamen in app.js (09.10.: ein neues
`function rotate()` für Heute überschrieb still die Pfeil-Drehung der
Leinwand-Übungen, weil alles in einer IIFE liegt und die spätere
Deklaration gewinnt). Prüft statisch jede Funktion und jede const/let
auf oberster Ebene der IIFE (zwei Leerzeichen Einzug). Kein Server nötig."""
import re, collections

src = open("../app.js", encoding="utf-8").read()
names = re.findall(r"^  (?:async )?function\*? ?([A-Za-z0-9_$]+)\s*\(", src, re.M)
names += re.findall(r"^  (?:const|let|var) ([A-Za-z0-9_$]+)\s*=", src, re.M)
dupes = [n for n, c in collections.Counter(names).items() if c > 1]
print("top-level names checked:", len(names))
print("no duplicate top-level names:", not dupes, dupes[:10])
print("ALL PASS" if not dupes else "SOME FAILED")
