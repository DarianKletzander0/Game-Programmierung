# Signal Breach

Signal Breach ist ein vollständig selbst programmiertes vertikales Arcade-Spiel. Es verwendet Python und pygame-ce, aber keine Game Engine und keine vorgefertigten Grafik-, Audio- oder Mechanikpakete. Sämtliche Spielgrafiken werden zur Laufzeit aus geometrischen Formen gezeichnet; auch die Soundeffekte entstehen mathematisch im Programm.

## Installation

Voraussetzungen:

- Python 3.14 oder neuer
- [uv](https://docs.astral.sh/uv/) als Paket- und Umgebungsverwaltung

```powershell
uv sync --link-mode copy
uv run python main.py
```

Alternativ kann pygame-ce in einer normalen virtuellen Python-Umgebung installiert werden:

```powershell
python -m pip install pygame-ce
python main.py
```

## Spielziel

Das Datennetz ist in drei Sektoren beschädigt. Steuere das Reparaturprogramm, zerstöre fehlerhafte Prozesse und besiege die Sektorwache am Ende jedes Abschnitts. Abschüsse geben Punkte und Datenfragmente. Zwischen den Sektoren lassen sich damit bleibende Verbesserungen für den aktuellen Durchlauf kaufen.

## Steuerung

| Eingabe | Funktion |
|---|---|
| WASD oder Pfeiltasten | Schiff bewegen |
| Mausbewegung | Schiff alternativ direkt positionieren |
| Leertaste | Impuls gegen nahe gegnerische Projektile |
| P oder Escape | Pause / Fortsetzen |
| 1 bis 4 | Upgrade im Shop kaufen |
| Enter | Starten, bestätigen, nächsten Sektor laden |
| F | Vollbild umschalten |
| M | Ton ein-/ausschalten |
| R | Nach Sieg oder Niederlage zum Menü |

Das Spiel feuert automatisch. Der Impuls besitzt eine Abklingzeit, die oben rechts angezeigt wird.

## Spielmerkmale

- sechs klar getrennte Zustände: Menü, Spiel, Pause, Shop, Niederlage und Sieg
- drei Sektoren mit eigenen Farben, Gegnerwellen und Bossmustern
- Drifter, Weaver, Charger, Splitter und Fragmente mit unterschiedlichem Verhalten
- Bossphasen mit Fächer-, Beschwörungs- und Radialangriffen
- Punkte, Zeit-Combo, Datenfragmente und vier Upgrade-Arten
- persistenter Highscore, beste Combo und Einstellungen
- prozedurale Vektorgrafik und zur Laufzeit erzeugte Audioeffekte
- skalierbares Fenster und Vollbild mit korrekter Eingabeabbildung

## Tests

Unter Windows PowerShell:

```powershell
$env:SDL_VIDEODRIVER='dummy'
$env:SDL_AUDIODRIVER='dummy'
uv run python -m unittest discover -s tests -v
```

Die Suite prüft sowohl das Abschlussprojekt als auch die vorherigen Übungen. Weitere Prüfungen:

```powershell
uv run python -m compileall -q main.py signal_breach tests
uv sync --extra documentation --link-mode copy
uv run --extra documentation python docs/generate_documentation.py
```

## Projektstruktur

```text
main.py                    Anwendungseinstieg und skalierbares Fenster
signal_breach/             Spiellogik, Darstellung, Audio und Persistenz
tests/                     automatisierte Unit- und Integrationstests
docs/DOKUMENTATION.md      technische Projektdokumentation
output/pdf/                fertige PDF-Dokumentation
uebung_003, uebung_004/    erhaltene Kursübungen
```

## Eigenleistung und Assets

Der Code des Abschlussprojekts, das Spieldesign, die Leveldaten, die geometrischen Darstellungen und die Audioerzeugung wurden für dieses Projekt erstellt. Das Abschlussprojekt lädt keine Bild-, Musik- oder Sounddateien. Die Asset-Ordner in `uebung_003` und `uebung_004` gehören ausschließlich zur dokumentierten Entwicklungsgeschichte der Kursübungen und werden von Signal Breach nicht verwendet.

## Dokumentation

Die ausführliche technische Dokumentation liegt unter [docs/DOKUMENTATION.md](docs/DOKUMENTATION.md). Die druckfertige Fassung befindet sich unter [output/pdf/Signal_Breach_Dokumentation.pdf](output/pdf/Signal_Breach_Dokumentation.pdf).
