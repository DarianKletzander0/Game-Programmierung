# Uebung 003 (10 Punkte)

**Game Programmierung mit Python + pygame-ce**
Basierend auf dem Original von Prof. Dr. Reto Schoelly

---

Bitte den Projekt-Ordner inklusive `assets/`-Verzeichnis einreichen! Bitte nicht den `.venv/`-Ordner einreichen.

## RealFakeGame Teil 1 (2 Punkte pro Aufgabe)

1. **Code lesen.** In diesem Ordner gibt es eine rudimentaer funktionierende Variante des RealFakeGames. Lies dir den Code durch, bis du ihn verstanden hast. Starte mit `main.py`, dann `entity.py`, dann `player.py` und `shot.py`. Schau dir an, wie die Klassen zusammenhaengen.

2. **Obstacles.** Es gibt bereits eine Klasse namens `Obstacle` (in `obstacle.py`). Erweitere sie dahingehend, dass Obstacles Upgrades oder Downgrades fuer den Player bringen, wenn er sie beruehrt. Sie sollten auch Enemies daran hindern, sie zu ueberschreiten. Upgrades koennten eine hoehere Feuerrate sein, oder mehrere Schuesse auf einmal, oder aehnliches. Die Darstellung kann ueber einfache Rechtecke mit einem Text ausgefuehrt werden. Tipp: `pygame.font.Font()` fuer Textdarstellung.

3. **Enemies.** Fuege Enemies hinzu, welche eine gewisse Schadenskapazitaet haben, die bei Kollision mit dem Player die Hitpoints verringern. Bei Kollision sollten die Enemies auch verschwinden (Despawn). Die Enemies sollten auch verschwinden, wenn sie vom Player getroffen werden. Es koennte sein, dass die Reichweite der Player-Schuesse vergroessert werden muss (`player.set_might()`).

4. **Hitpoints-Anzeige.** Die Hitpoints des Players sollten angezeigt werden, entweder als Text (`pygame.font`) oder als Health Bar (`pygame.draw.rect`). Tipp: [pygame.font Docs](https://pyga.me/docs/ref/font.html)

5. **Game Loop & Death.** Bau eine Game Loop und eine Death-Mechanik ein. Das Spiel sollte mindestens die Zustaende "Playing" und "Game Over" haben. Bei Tod des Players (HP <= 0) sollte ein Game-Over-Bildschirm erscheinen.

## Setup

```bash
# In diesem Ordner:
uv init .
uv add pygame-ce
uv run main.py
```

Oder falls du ein neues Projekt anlegen willst, kopiere alle `.py`-Dateien und den `assets/`-Ordner hinein.

## Steuerung (Skeleton)

- **Maus** — Player folgt der Maus-X-Position
- **R** — Neustart nach Game Over
- **ESC** — Beenden

## Architektur

```
Entity (Basisklasse: Position, Richtung, HP, Animation)
├── Player   — folgt Maus, feuert automatisch Shots
├── Shot     — Projektil mit Reichweite und Schaden
├── Enemy    — STUB: Felder vorhanden, Verhalten fehlt
└── Level    — laedt .rfg-Datei, Hintergrund, Obstacles

Obstacle     — Datenklasse (Koordinaten berechnet, nicht gezeichnet)
```

Die mit `# TODO` markierten Stellen zeigen, wo ihr Code hinzufuegen muesst.

## Docs

- [pygame-ce Dokumentation](https://pyga.me/docs/)
- [pygame.sprite](https://pyga.me/docs/ref/sprite.html) — Sprite-Gruppen und Kollision
- [pygame.font](https://pyga.me/docs/ref/font.html) — Textdarstellung
- [pygame.Rect.colliderect](https://pyga.me/docs/ref/rect.html#pygame.Rect.colliderect) — Rechteck-Kollision
