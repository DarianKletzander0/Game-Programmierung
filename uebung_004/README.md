# Uebung 004 (10 Punkte)

**Game Programmierung mit Python + pygame-ce**
Basierend auf dem Original von Prof. Dr. Reto Schoelly

---

Bitte den Projekt-Ordner inklusive `assets/`-Verzeichnis einreichen! Bitte nicht den `.venv/`-Ordner einreichen.

## RealFakeGame Teil 2 (2 Punkte pro Aufgabe)

Diese Uebung baut auf eurem Code aus Uebung 003 auf. Ihr arbeitet im selben Projekt weiter.

1. **Tile-bare Hintergruende.** Mache die Levelhintergruende tile-able — also mehrere Hintergruende als kleinere Bilder, die gemeinsam ein Levelbild ergeben. Der Hintergrund sollte sich wiederholen, wenn das Level scrollt.

2. **Punkte & Highscore.** Entwickle ein Punkte- und Highscore-System. Punkte fuer abgeschossene Enemies, Bonus fuer Combos oder schnelle Kills. Der Highscore sollte zwischen Spielrunden persistent sein (z.B. in einer Textdatei gespeichert).

3. **Upgrade-Shop.** Bau ein Level-up / Persistent-Upgrade-System mit In-Game-Waehrung. Keine In-App-Kaeufe! Spieler verdienen Waehrung durch Gameplay und koennen zwischen Leveln Upgrades kaufen (Feuerrate, Schaden, HP, etc.).

4. **Level-Progression.** Entwickle mehrere Level und eine Level-Progression mit immer schwierigeren Gegnern. Die Schwierigkeit sollte spuerbar steigen: mehr Enemies, schnellere Enemies, neue Enemy-Typen.

5. **Boss-Battle.** Am Ende jedes Levels sollte es einen Epic-Boss-Battle geben. Der Boss sollte sich anders verhalten als normale Enemies: mehr HP, spezielle Angriffsmuster, visuelles Feedback.

## Hinweise

- Ihr koennt das `.rfg`-Level-Format erweitern oder eigene Level-Dateien erstellen.
- Fuer die Highscore-Persistenz reicht eine einfache Textdatei (`open()`, `read()`, `write()`).
- Der Upgrade-Shop kann ein eigener Game-State sein (wie "Playing" und "Game Over" aus Uebung 003).
- Boss-Enemies koennen eine eigene Klasse sein, die von `Enemy` erbt.

## Docs

- [pygame-ce Dokumentation](https://pyga.me/docs/)
- [Python File I/O](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files) — Dateien lesen/schreiben
- [pygame.time](https://pyga.me/docs/ref/time.html) — Timer und Timing
