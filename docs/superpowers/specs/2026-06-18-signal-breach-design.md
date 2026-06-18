# Signal Breach - Design-Spezifikation

Datum: 18.06.2026

## Ziel

Signal Breach ist ein eigenstaendig programmiertes vertikales Arcade-Spiel auf Basis von Python und pygame-ce. Es baut fachlich auf den Uebungen 003 und 004 auf, ersetzt deren Prototyp-Charakter jedoch durch ein vollstaendiges, zusammenhaengendes Spiel mit klarer Progression, eigener Gestaltung und nachvollziehbarer Dokumentation.

Das Projekt verwendet keine Game Engine und keine vorgefertigten Spielmechaniken oder Medien. Darstellung, Effekte, Benutzeroberflaeche, Leveldaten und Audio werden im Projekt selbst erzeugt.

## Spielidee

Der Spieler steuert ein Reparaturprogramm durch drei beschaedigte Sektoren eines Datennetzes. Gegner repraesentieren fehlerhafte Prozesse, Bosse bewachen die Sektorgrenzen. Der Spieler bewegt sich frei innerhalb des Spielfeldes und feuert automatisch. Besiegte Gegner geben Punkte und Datenfragmente. Zwischen den Sektoren koennen Datenfragmente dauerhaft fuer den aktuellen Durchlauf in Verbesserungen investiert werden.

Eine Partie besteht aus:

1. Startmenue und kurzer Einfuehrung.
2. Drei Sektoren mit steigender Schwierigkeit.
3. Je einem Boss am Ende jedes Sektors.
4. Einem Upgrade-Shop zwischen den Sektoren.
5. Sieg- oder Niederlagebildschirm mit Statistik und Neustart.

## Steuerung

- WASD oder Pfeiltasten: Bewegung
- Maus: alternative horizontale und vertikale Steuerung, wenn sie bewegt wird
- Leertaste: Impulsfaehigkeit, sofern aufgeladen
- P oder Escape: Pause und Fortsetzen
- Enter: Auswahl bestaetigen und naechsten Sektor starten
- 1 bis 4: Shop-Upgrades kaufen
- F: Vollbild umschalten

## Kernmechaniken

### Bewegung und Kampf

Das Spielerschiff bleibt innerhalb der sichtbaren Spielflaeche. Es feuert automatisch nach oben. Feuerrate, Projektilschaden, Projektilgeschwindigkeit und maximale Lebenspunkte sind verbesserbar. Treffer erzeugen deutliches visuelles Feedback. Eine Impulsfaehigkeit zerstoert gegnerische Projektile in der Naehe und besitzt eine sichtbare Abklingzeit.

### Gegner

- Drifter: fliegt gerade und schiesst gelegentlich gezielt.
- Weaver: bewegt sich in einer Sinuskurve.
- Charger: kuendigt einen schnellen Angriff auf die Spielerposition an.
- Splitter: zerfaellt beim Tod in zwei kleinere Gegner.

Gegner werden durch datengetriebene Wellen erzeugt. Spaetere Sektoren kombinieren mehr Typen, kuerzere Abstaende, hoehere Geschwindigkeiten und robustere Gegner.

### Bosse

Jeder Sektor endet mit einem eigenen Bossprofil. Bosse besitzen mehrere Lebensphasen und gut erkennbare Angriffsmuster:

- Sektor 1: Faecherschuesse und seitliches Pendeln.
- Sektor 2: wechselnde Salven und beschworene Begleiter.
- Sektor 3: Kombination vorheriger Muster mit radialem Angriff.

Boss-Lebenspunkte und Phasen werden sichtbar dargestellt. Unvermeidbare Trefferketten werden durch Angriffsvorwarnungen und begrenzte Projektilgeschwindigkeiten vermieden.

### Punkte, Combo und Ressourcen

Jeder Abschuss gibt Basispunkte. Schnelle aufeinanderfolgende Abschuesse erhoehen den Combo-Multiplikator, der bei zu langer Pause oder erlittenem Treffer zurueckgesetzt wird. Datenfragmente dienen als Shop-Waehrung. Highscore, beste Combo, abgeschlossene Sektoren und Einstellungen werden lokal in einer JSON-Datei gespeichert.

### Shop

Zwischen Sektoren stehen vier Upgrades zur Wahl:

- Schaden
- Feuerrate
- Maximale Lebenspunkte plus Heilung
- Projektilgeschwindigkeit plus Reichweite

Kosten steigen pro Kauf. Nicht ausreichende Waehrung und erreichte Maximalstufen werden klar angezeigt. Upgrades gelten fuer den laufenden Durchlauf; Highscore und Einstellungen bleiben ueber Neustarts hinweg erhalten.

## Zustaende und Datenfluss

Die Anwendung besitzt explizite Zustaende: `menu`, `playing`, `paused`, `shop`, `game_over` und `won`. Eingaben werden zuerst vom aktuellen Zustand verarbeitet. Nur `playing` aktualisiert die Spielsimulation. Rendering ist von der Simulation getrennt, damit Pausen, Tests und Screenshots reproduzierbar sind.

Der Datenfluss pro Frame ist:

1. Eingaben lesen.
2. Zustandsaktion bestimmen.
3. Simulation mit begrenztem Delta aktualisieren.
4. Kollisionen und Ereignisse auswerten.
5. Zustand wechseln oder Spielwelt aufraeumen.
6. Aktuellen Zustand rendern.

## Architektur

- `main.py`: Einstiegspunkt und Hauptschleife.
- `signal_breach/game.py`: Zustandsautomat und Ablauf einer Partie.
- `signal_breach/entities.py`: Spieler, Gegner und Projektile.
- `signal_breach/levels.py`: Wellen- und Bosskonfigurationen.
- `signal_breach/systems.py`: Kollision, Punkte, Shop und Persistenz.
- `signal_breach/rendering.py`: prozedurale Grafiken, UI, Effekte und Hintergruende.
- `signal_breach/audio.py`: zur Laufzeit erzeugte Soundeffekte mit stummem Fallback.
- `tests/`: isolierte Unit- und Integrationstests.

Abhaengigkeiten werden ueber kleine, explizite Schnittstellen gehalten. Die Spiellogik kann ohne sichtbares Fenster getestet werden. Fehlerhafte oder fehlende Speicherdateien fuehren zu sicheren Standardwerten und verhindern den Spielstart nicht. Nicht verfuegbares Audio deaktiviert nur die Tonausgabe.

## Visuelles und akustisches Konzept

Das Spiel verwendet eine kontrastreiche Neon-Palette auf hellem, tiefblauem Hintergrund. Geometrische Schiffe, Gegner, Partikel, Raster und Symbole werden mit pygame-Zeichenfunktionen generiert. Das vermeidet externe Bilddateien und erzeugt einen konsistenten Stil. Bildschirmtexte bleiben kurz und deutschsprachig.

Kurze Klaenge fuer Schuss, Treffer, Kauf, Bosswarnung und Zustandswechsel werden beim Start mathematisch als Wellenformen erzeugt. Die Lautstaerke ist begrenzt und in den Einstellungen deaktivierbar.

## Teststrategie

Automatisierte Tests pruefen mindestens:

- Begrenzung der Spielerbewegung.
- Schaden, Unverwundbarkeitszeit und Tod.
- Projektil- und Gegnerkollisionen.
- Combo, Punkte und Datenfragmente.
- Upgrade-Kosten und Wirkungen.
- Wellen-, Boss- und Levelprogression.
- Wechsel aller Spielzustaende.
- robuste JSON-Persistenz.

Zusaetzlich wird das Spiel im Dummy-Videomodus ueber mehrere simulierte Frames ausgefuehrt. Ein realer Smoke-Test startet das Fenster, prueft Menue, Bewegung, Pause, Shop, Sieg/Niederlage und Neustart. Screenshots der wichtigsten Zustaende werden visuell kontrolliert.

## Dokumentation und Abgabe

Die Abgabe enthaelt:

- ein direkt startbares Spiel,
- eine deutsche `README.md` mit Installation und Steuerung,
- eine technische Dokumentation als Markdown und PDF,
- eine Beschreibung der Eigenleistung und verwendeten Werkzeuge,
- automatisierte Tests,
- einen Quellenhinweis, der ausschliesslich Python und pygame-ce als externe Software nennt,
- keine virtuelle Umgebung, Cache-Dateien oder fremden Medien.

## Abnahmekriterien

Das Projekt gilt als abgeschlossen, wenn es aus einem frischen Checkout mit den dokumentierten Befehlen startet, alle automatisierten Tests bestehen, alle sechs Spielzustaende erreichbar sind, drei unterschiedliche Sektoren inklusive Bossen spielbar sind, Punkte und Einstellungen gespeichert werden und die Dokumentation den Aufbau sowie die Eigenleistung nachvollziehbar erklaert.
