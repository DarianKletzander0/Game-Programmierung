# Signal Breach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, engine-free vertical arcade shooter with three sectors, bosses, upgrades, persistence, original procedural presentation, tests, and submission documentation.

**Architecture:** Keep the original exercises as historical course work and replace the root prototype with a focused `signal_breach` package. Pure model and system functions own rules; pygame entities and the state machine consume those rules; rendering, generated audio, and persistence remain replaceable adapters.

**Tech Stack:** Python 3.14, pygame-ce, unittest, JSON, reportlab for the submitted PDF documentation

---

## File map

- Create `signal_breach/config.py`: dimensions, palette, tuning, paths.
- Create `signal_breach/model.py`: game-state enum and run/settings data.
- Create `signal_breach/persistence.py`: validated JSON loading and atomic saving.
- Create `signal_breach/scoring.py`: combo, score, currency, and upgrade rules.
- Create `signal_breach/entities.py`: player, enemies, bosses, and projectiles.
- Create `signal_breach/levels.py`: three sector definitions and wave spawning.
- Create `signal_breach/audio.py`: generated sound effects and silent fallback.
- Create `signal_breach/rendering.py`: procedural visuals and screens.
- Create `signal_breach/game.py`: state machine, simulation, collisions, and public test hooks.
- Replace `main.py`: small application entry point.
- Create `tests/test_model_systems.py`, `tests/test_entities.py`, `tests/test_game_flow.py`: behavioral tests.
- Create `README.md`, `docs/DOKUMENTATION.md`, `docs/generate_documentation.py`: submission documentation.
- Create `output/pdf/Signal_Breach_Dokumentation.pdf`: rendered final documentation.

### Task 1: Package skeleton and persistent model

**Files:**
- Modify: `pyproject.toml`
- Create: `signal_breach/__init__.py`
- Create: `signal_breach/config.py`
- Create: `signal_breach/model.py`
- Create: `signal_breach/persistence.py`
- Test: `tests/test_model_systems.py`

- [ ] **Step 1: Write failing model and persistence tests**

```python
def test_missing_or_invalid_save_uses_safe_defaults(tmp_path):
    path = tmp_path / "save.json"
    assert load_profile(path) == Profile()
    path.write_text("not json", encoding="utf-8")
    assert load_profile(path) == Profile()

def test_profile_roundtrip_clamps_values(tmp_path):
    path = tmp_path / "save.json"
    save_profile(path, Profile(highscore=900, best_combo=7, unlocked_sector=99))
    loaded = load_profile(path)
    assert loaded.highscore == 900
    assert loaded.best_combo == 7
    assert loaded.unlocked_sector == 3
```

- [ ] **Step 2: Run the tests and confirm the import failure**

Run: `uv run python -m unittest tests.test_model_systems -v`
Expected: FAIL because `signal_breach.model` does not exist.

- [ ] **Step 3: Implement the model and persistence adapter**

```python
class ScreenState(StrEnum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    SHOP = "shop"
    GAME_OVER = "game_over"
    WON = "won"

@dataclass(slots=True)
class Profile:
    highscore: int = 0
    best_combo: int = 0
    unlocked_sector: int = 1
    fullscreen: bool = False
    sound_enabled: bool = True
```

`load_profile` must accept only a JSON object, coerce integers safely, clamp non-negative statistics and sector range, and fall back to `Profile()` on `OSError`, `ValueError`, `TypeError`, or malformed JSON. `save_profile` must write to a sibling temporary file and replace the target atomically.

- [ ] **Step 4: Run focused and complete tests**

Run: `uv run python -m unittest tests.test_model_systems -v`
Expected: all tests pass.

- [ ] **Step 5: Commit the package foundation**

```powershell
git add pyproject.toml signal_breach tests/test_model_systems.py
git commit -m "Build Signal Breach model and persistence"
```

### Task 2: Scoring and upgrade economy

**Files:**
- Create: `signal_breach/scoring.py`
- Modify: `signal_breach/model.py`
- Modify: `tests/test_model_systems.py`

- [ ] **Step 1: Add failing score and shop tests**

```python
def test_quick_kills_build_combo_and_currency():
    score = ScoreSystem(combo_window=2.0)
    assert score.record_kill(now=1.0, points=100, currency=1) == 100
    assert score.record_kill(now=2.0, points=100, currency=1) == 150
    assert (score.score, score.combo, score.currency) == (250, 2, 2)

def test_upgrade_purchase_spends_currency_and_changes_stats():
    run = RunStats(currency=6)
    upgrades = UpgradeSystem()
    assert upgrades.buy("damage", run)
    assert run.currency == 3
    assert run.player.damage == 2
```

- [ ] **Step 2: Confirm the tests fail**

Run: `uv run python -m unittest tests.test_model_systems -v`
Expected: FAIL because scoring classes are missing.

- [ ] **Step 3: Implement deterministic score and upgrade rules**

```python
UPGRADES = {
    "damage": Upgrade("Schaden", 3, 4),
    "fire_rate": Upgrade("Feuerrate", 3, 4),
    "max_hp": Upgrade("Integritaet", 2, 4),
    "shot_speed": Upgrade("Projektiltempo", 2, 4),
}

def cost(self, name: str) -> int:
    item = UPGRADES[name]
    return item.base_cost * (self.levels[name] + 1)
```

Damage adds one, fire rate lowers cooldown with a floor, max HP adds 25 and heals, and shot speed increases speed and range. Purchases above max level or without enough currency return `False` and leave data unchanged.

- [ ] **Step 4: Verify score and economy tests**

Run: `uv run python -m unittest tests.test_model_systems -v`
Expected: all tests pass.

- [ ] **Step 5: Commit the systems**

```powershell
git add signal_breach/model.py signal_breach/scoring.py tests/test_model_systems.py
git commit -m "Add scoring combo and upgrade economy"
```

### Task 3: Combat entities

**Files:**
- Create: `signal_breach/entities.py`
- Test: `tests/test_entities.py`

- [ ] **Step 1: Write failing movement and combat tests**

```python
def test_player_movement_is_clamped_to_playfield():
    player = Player(pygame.Vector2(10, 10))
    player.move(pygame.Vector2(-1000, 1000), 1.0)
    assert player.radius <= player.pos.x <= PLAY_WIDTH - player.radius
    assert HUD_HEIGHT + player.radius <= player.pos.y <= SCREEN_HEIGHT - player.radius

def test_damage_uses_invulnerability_and_resets_combo():
    player = Player(pygame.Vector2(300, 700))
    score = ScoreSystem()
    score.combo = 4
    assert player.take_damage(20)
    assert not player.take_damage(20)
    score.on_player_hit()
    assert player.hp == 80
    assert score.combo == 0

def test_splitter_death_creates_two_fragments():
    enemy = Enemy.create("splitter", pygame.Vector2(300, 200), difficulty=1.0)
    spawned = enemy.on_destroyed()
    assert len(spawned) == 2
    assert all(item.kind == "fragment" for item in spawned)
```

- [ ] **Step 2: Confirm the entity tests fail**

Run: `uv run python -m unittest tests.test_entities -v`
Expected: FAIL because entity classes are missing.

- [ ] **Step 3: Implement player, projectile, enemy, and boss classes**

All entities expose `update(dt)`, `rect`, `alive`, and draw-neutral state. `Enemy.create` configures drifter, weaver, charger, splitter, and fragment behavior. `Boss` adds phase thresholds, attack timers, warning time, and sector-specific patterns. Player auto-fire returns new projectiles, impulse removes hostile projectiles within 150 pixels, and damage activates 0.8 seconds of invulnerability.

```python
def take_damage(self, amount: int) -> bool:
    if self.invulnerability > 0 or not self.alive:
        return False
    self.hp = max(0, self.hp - max(0, amount))
    self.invulnerability = 0.8
    self.alive = self.hp > 0
    return True
```

- [ ] **Step 4: Verify entity behavior**

Run: `uv run python -m unittest tests.test_entities -v`
Expected: all tests pass in SDL dummy mode.

- [ ] **Step 5: Commit combat entities**

```powershell
git add signal_breach/entities.py tests/test_entities.py
git commit -m "Implement Signal Breach combat entities"
```

### Task 4: Sectors, waves, and progression

**Files:**
- Create: `signal_breach/levels.py`
- Modify: `tests/test_entities.py`
- Create: `tests/test_game_flow.py`

- [ ] **Step 1: Write failing level progression tests**

```python
def test_three_sectors_increase_difficulty_and_end_with_distinct_bosses():
    assert len(SECTORS) == 3
    assert [sector.boss_pattern for sector in SECTORS] == ["fan", "summon", "core"]
    assert SECTORS[0].difficulty < SECTORS[1].difficulty < SECTORS[2].difficulty
    assert all(sector.waves for sector in SECTORS)

def test_spawner_emits_each_wave_once():
    spawner = SectorRuntime(SECTORS[0])
    first = spawner.update(1.1)
    second = spawner.update(0.0)
    assert first
    assert second == []
```

- [ ] **Step 2: Confirm progression tests fail**

Run: `uv run python -m unittest tests.test_game_flow -v`
Expected: FAIL because sector data is missing.

- [ ] **Step 3: Implement immutable wave data and runtime spawning**

```python
@dataclass(frozen=True, slots=True)
class Wave:
    at: float
    kind: str
    count: int
    formation: str

@dataclass(frozen=True, slots=True)
class SectorDefinition:
    name: str
    difficulty: float
    color: tuple[int, int, int]
    waves: tuple[Wave, ...]
    boss_pattern: str
```

Each sector must last roughly 60-90 seconds for a normal player, use at least three enemy types overall, and spawn its boss only after all scheduled waves and remaining normal enemies are resolved.

- [ ] **Step 4: Verify level tests**

Run: `uv run python -m unittest tests.test_game_flow -v`
Expected: all level tests pass.

- [ ] **Step 5: Commit sector progression**

```powershell
git add signal_breach/levels.py tests/test_game_flow.py tests/test_entities.py
git commit -m "Define three escalating Signal Breach sectors"
```

### Task 5: State machine, collisions, rendering, and generated audio

**Files:**
- Create: `signal_breach/game.py`
- Create: `signal_breach/rendering.py`
- Create: `signal_breach/audio.py`
- Replace: `main.py`
- Modify: `tests/test_game_flow.py`

- [ ] **Step 1: Add failing end-to-end state tests**

```python
def test_menu_pause_shop_win_and_restart_flow(tmp_path):
    game = Game(profile_path=tmp_path / "profile.json", audio=False)
    assert game.state is ScreenState.MENU
    game.start_run()
    assert game.state is ScreenState.PLAYING
    game.toggle_pause()
    assert game.state is ScreenState.PAUSED
    game.toggle_pause()
    game.complete_sector()
    assert game.state is ScreenState.SHOP
    game.sector_index = 2
    game.complete_sector()
    assert game.state is ScreenState.WON
    game.restart()
    assert game.state is ScreenState.MENU

def test_combat_update_removes_hits_and_awards_score(tmp_path):
    game = Game(profile_path=tmp_path / "profile.json", audio=False)
    game.start_run()
    enemy = Enemy.create("drifter", Vector2(300, 250), 1.0)
    enemy.hp = 1
    game.enemies = [enemy]
    game.player_shots = [Projectile(Vector2(300, 250), Vector2(), 1, False)]
    game.update(1 / 60)
    assert game.enemies == []
    assert game.score.score > 0
```

- [ ] **Step 2: Confirm state tests fail**

Run: `uv run python -m unittest tests.test_game_flow -v`
Expected: FAIL because `Game` is missing.

- [ ] **Step 3: Implement the game state machine and collision pipeline**

`Game.handle_event` owns menu, gameplay, pause, shop, end-screen, fullscreen, keyboard, and mouse actions. `Game.update` updates only while playing, uses a maximum delta of 1/30 second, resolves projectile/enemy, projectile/player, enemy/player, pickup/player collisions, then performs cleanup and state transitions. Public `start_run`, `toggle_pause`, `complete_sector`, and `restart` methods provide deterministic test hooks.

- [ ] **Step 4: Implement procedural presentation and generated sound**

`Renderer` draws a star/grid background, geometric entities, particles, HUD, boss bar, menu, pause, shop, game-over, and win screens without loading image files. `AudioManager` builds short signed-16-bit mono buffers for shoot, hit, explosion, purchase, and warning sounds and becomes a no-op if mixer initialization fails.

```python
def tone(frequency: float, seconds: float, volume: float = 0.18) -> bytes:
    frames = int(44_100 * seconds)
    return b"".join(
        pack("<h", int(32767 * volume * sin(2 * pi * frequency * i / 44_100)))
        for i in range(frames)
    )
```

Root `main.py` initializes pygame, creates a resizable window, maps fullscreen correctly, runs at 60 FPS, and delegates events, updates, and drawing to `Game` and `Renderer`.

- [ ] **Step 5: Verify the complete automated suite**

Run: `$env:SDL_VIDEODRIVER='dummy'; $env:SDL_AUDIODRIVER='dummy'; uv run python -m unittest discover -s tests -v`
Expected: all old exercise tests and new game tests pass.

- [ ] **Step 6: Commit the playable game**

```powershell
git add main.py signal_breach tests/test_game_flow.py
git commit -m "Complete playable Signal Breach game loop"
```

### Task 6: Documentation and PDF

**Files:**
- Create: `README.md`
- Create: `docs/DOKUMENTATION.md`
- Create: `docs/generate_documentation.py`
- Create: `output/pdf/Signal_Breach_Dokumentation.pdf`
- Modify: `.gitignore`

- [ ] **Step 1: Write the user and technical documentation**

`README.md` must contain setup with `uv sync`, start with `uv run python main.py`, controls, game goal, test command, project layout, and asset statement. `docs/DOKUMENTATION.md` must cover assignment, concept, requirements traceability, architecture, state flow, algorithms, class responsibilities, collision logic, level design, persistence, generated media, test strategy and results, limitations, conclusion, and sources.

- [ ] **Step 2: Add a reproducible PDF generator**

`docs/generate_documentation.py` must parse Markdown headings, paragraphs, lists, and fenced code into reportlab flowables, include page numbers and a title page, and write `output/pdf/Signal_Breach_Dokumentation.pdf` with embedded standard fonts.

- [ ] **Step 3: Generate and inspect the PDF**

Run: `uv run python docs/generate_documentation.py`
Expected: PDF is created with more than five pages and no generation errors.

Render the PDF to PNG pages with the available PDF rendering runtime, inspect title, contents, code blocks, page breaks, footer numbers, and final sources page, then correct any clipping or overflow.

- [ ] **Step 4: Commit documentation**

```powershell
git add README.md docs output/pdf/Signal_Breach_Dokumentation.pdf .gitignore pyproject.toml uv.lock
git commit -m "Document and package Signal Breach submission"
```

### Task 7: Final gameplay verification

**Files:**
- Modify as defects require: `signal_breach/*.py`, `tests/*.py`, `README.md`, `docs/DOKUMENTATION.md`
- Create: `output/screenshots/menu.png`
- Create: `output/screenshots/gameplay.png`
- Create: `output/screenshots/shop.png`
- Create: `output/screenshots/boss.png`
- Create: `output/screenshots/win.png`

- [ ] **Step 1: Run static and automated checks**

Run: `uv run python -m compileall -q main.py signal_breach tests docs/generate_documentation.py`
Expected: exit code 0.

Run: `$env:SDL_VIDEODRIVER='dummy'; $env:SDL_AUDIODRIVER='dummy'; uv run python -m unittest discover -s tests -v`
Expected: all tests pass.

- [ ] **Step 2: Run a deterministic screenshot harness**

Create each required game state through public `Game` methods, render it to a 960x720 surface, and save the five screenshots. Inspect every image for readable text, contrast, visible entities, unclipped HUD, and correct state-specific controls.

- [ ] **Step 3: Perform a real-window smoke test**

Run: `uv run python main.py`
Expected: start menu opens; Enter starts; WASD and arrows move; auto-fire works; Space triggers impulse; P/Escape pauses and resumes; shop keys purchase; Enter advances; F toggles fullscreen; R restarts end screens; closing the window exits cleanly.

- [ ] **Step 4: Re-run regression checks after fixes**

Run both compile and unittest commands again and regenerate the documentation PDF if documented behavior changed. Expected: clean exit and all tests pass.

- [ ] **Step 5: Commit verified final state**

```powershell
git add main.py signal_breach tests README.md docs output
git commit -m "Verify complete Signal Breach submission"
```
