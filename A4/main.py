# main.py
# Game loop for RealFakeGame Uebung 004.
#
# Controls:
#   Mouse X       - move player left/right
#   1, 2, 3, 4    - buy upgrades in shop
#   Enter/Space   - leave shop / continue
#   R             - restart after game over or win
#   ESC           - quit

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, WHITE
from player import Player
from level import Level
from score import ScoreManager
from shop import UpgradeShop


GAME_PLAYING = "playing"
GAME_SHOP = "shop"
GAME_OVER = "gameover"
GAME_WON = "won"

LEVEL_FILES = ["lvl001.rfg", "lvl002.rfg", "lvl003.rfg"]
SHOP_KEYS = {
    pygame.K_1: "damage",
    pygame.K_2: "fire_rate",
    pygame.K_3: "hp",
    pygame.K_4: "shot_speed",
}


def handle_collisions(
    player: Player,
    level: Level,
    score_manager: ScoreManager | None = None,
) -> None:
    """Resolve obstacle, shot/enemy, and enemy/player collisions."""
    player_rect = player.get_rect()
    for obstacle in level.obstacles:
        if obstacle.collides_with(player_rect):
            obstacle.apply_to_player(player)

    remaining_shots = []
    for shot in player.shots:
        hit_enemy = None
        for enemy in level.enemies:
            if (
                enemy.is_alive()
                and getattr(enemy, "ready", True)
                and shot.get_rect().colliderect(enemy.get_rect())
            ):
                hit_enemy = enemy
                break

        if hit_enemy is None:
            if shot.is_alive():
                remaining_shots.append(shot)
            continue

        killed = damage_enemy(hit_enemy, shot.dmg)
        if killed and score_manager is not None:
            enemy_kind = "boss" if getattr(hit_enemy, "is_boss", False) else "normal"
            score_manager.record_kill(level.frame, enemy_kind)

    player.shots = remaining_shots
    level.enemies = [enemy for enemy in level.enemies if enemy.is_alive()]

    player_rect = player.get_rect()
    for enemy in level.enemies:
        if not getattr(enemy, "is_boss", False) or not hasattr(enemy, "shots"):
            continue

        remaining_boss_shots = []
        for projectile in enemy.shots:
            if projectile.alive and projectile.get_rect().colliderect(player_rect):
                player.hp = max(0, player.hp - projectile.damage)
                projectile.alive = False
            elif projectile.alive:
                remaining_boss_shots.append(projectile)
        enemy.shots = remaining_boss_shots

    remaining_enemies = []
    for enemy in level.enemies:
        if getattr(enemy, "ready", True) and enemy.get_rect().colliderect(player_rect):
            player.hp = max(0, player.hp - enemy.damage)
            if getattr(enemy, "is_boss", False):
                remaining_enemies.append(enemy)
            else:
                enemy.alive = False
        elif enemy.is_alive():
            remaining_enemies.append(enemy)
    level.enemies = remaining_enemies


def damage_enemy(enemy, damage: int) -> bool:
    """Damage an enemy. Normal enemies despawn on hit; bosses lose HP."""
    if getattr(enemy, "is_boss", False):
        if hasattr(enemy, "take_damage"):
            return enemy.take_damage(damage)
        enemy.hp = max(0, enemy.hp - damage)
        enemy.alive = enemy.hp > 0
        return not enemy.alive

    enemy.hp = 0
    enemy.alive = False
    return True


def get_game_state(player: Player, level: Level | None = None) -> str:
    if player.hp <= 0:
        return GAME_OVER
    if level is not None and not level.enemies:
        return GAME_SHOP
    return GAME_PLAYING


def get_progress_state(player: Player, level: Level, level_index: int) -> str:
    """Return shop after a level or won after the final level."""
    state = get_game_state(player, level)
    if state == GAME_SHOP and level_index == len(LEVEL_FILES) - 1:
        return GAME_WON
    return state


def get_weapon_status(player: Player) -> str:
    return f"DMG {player.dmg}  RATE {player.cad}  SPEED {player.shotspd}"


def is_restart_event(event: pygame.event.Event, game_state: str) -> bool:
    return (
        game_state in (GAME_OVER, GAME_WON)
        and event.type == pygame.KEYDOWN
        and event.key == pygame.K_r
    )


def draw_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    player: Player,
    score_manager: ScoreManager | None = None,
    level_index: int = 0,
) -> None:
    hp = max(0, player.hp)
    hp_text = font.render(f"HP: {hp}/{getattr(player, 'max_hp', hp)}", True, WHITE)
    screen.blit(hp_text, (16, 16))

    bar_width = 160
    bar_height = 14
    x = 16
    y = 44
    pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
    fill_width = int(bar_width * min(1.0, hp / max(1, getattr(player, "max_hp", 100))))
    pygame.draw.rect(screen, (54, 210, 92), (x, y, fill_width, bar_height))
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 1)

    small_font = pygame.font.Font(None, 22)
    weapon_text = small_font.render(get_weapon_status(player), True, WHITE)
    screen.blit(weapon_text, (16, 68))

    if score_manager is not None:
        score_text = small_font.render(
            f"LEVEL {level_index + 1}/{len(LEVEL_FILES)}  SCORE {score_manager.score}  $ {score_manager.currency}  HI {score_manager.highscore}",
            True,
            WHITE,
        )
        screen.blit(score_text, (16, 92))

    if player.status_message:
        status_text = small_font.render(player.status_message, True, (255, 220, 90))
        screen.blit(status_text, (16, 116))


def draw_game_over(
    screen: pygame.Surface,
    font: pygame.font.Font,
    player: Player,
    score_manager: ScoreManager | None = None,
) -> None:
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    title = font.render("GAME OVER", True, WHITE)
    hp_text = font.render(f"HP: {max(0, player.hp)}", True, WHITE)
    score_text = font.render(
        f"Score: {score_manager.score if score_manager else 0}",
        True,
        WHITE,
    )
    restart_text = font.render("Press R to restart", True, WHITE)
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
    screen.blit(hp_text, hp_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10)))
    screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))
    screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)))


def draw_shop(
    screen: pygame.Surface,
    font: pygame.font.Font,
    player: Player,
    score_manager: ScoreManager,
    shop: UpgradeShop,
    level_index: int,
) -> None:
    screen.fill((14, 18, 30))
    title = font.render(f"UPGRADE SHOP - Level {level_index + 1} complete", True, WHITE)
    screen.blit(title, (48, 56))

    small_font = pygame.font.Font(None, 26)
    currency = small_font.render(f"Currency: {score_manager.currency}", True, (255, 230, 110))
    screen.blit(currency, (48, 104))

    stats = small_font.render(
        f"HP {player.hp}/{player.max_hp}   DMG {player.dmg}   RATE {player.cad}   SHOT {player.shotspd}",
        True,
        WHITE,
    )
    screen.blit(stats, (48, 138))

    y = 200
    for key, label, cost, level, description in shop.get_rows():
        color = (110, 230, 150) if score_manager.currency >= cost else (170, 170, 170)
        row = small_font.render(
            f"{key}. {label:<10} cost {cost:<2} lvl {level:<2} {description}",
            True,
            color,
        )
        screen.blit(row, (48, y))
        y += 42

    message = small_font.render(shop.last_message, True, (255, 230, 110))
    screen.blit(message, (48, y + 18))
    continue_text = small_font.render("Enter/Space: next level", True, WHITE)
    screen.blit(continue_text, (48, y + 58))


def draw_win(screen: pygame.Surface, font: pygame.font.Font, score_manager: ScoreManager) -> None:
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    title = font.render("YOU WON", True, WHITE)
    score = font.render(f"Score: {score_manager.score}", True, WHITE)
    restart = font.render("Press R to restart", True, WHITE)
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
    screen.blit(score, score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
    screen.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))


def create_player() -> Player:
    player = Player()
    player.setup(
        x=SCREEN_WIDTH // 2,
        y=SCREEN_HEIGHT - 50,
        dx=0,
        dy=0,
        image_prefix="player_stage",
        anim_speed=1,
        hp=100,
    )
    player.set_might(rng=180, dmg=1, cad=35, shotspd=5)
    return player


def reset_player_for_level(player: Player) -> Player:
    player.pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
    player.dir = pygame.Vector2(0, 0)
    player.shots = []
    player.hp = max(player.hp, max(1, player.max_hp // 2))
    player.status_message = ""
    player._cad_counter = player.cad
    return player


def load_level(level_index: int) -> Level:
    level = Level()
    level.load(LEVEL_FILES[level_index])
    return level


def create_game(
    level_index: int = 0,
    score_manager: ScoreManager | None = None,
    player: Player | None = None,
) -> tuple[Player, Level, str, int, ScoreManager]:
    player = create_player() if player is None else reset_player_for_level(player)
    level = load_level(level_index)
    score_manager = score_manager or ScoreManager()
    score_manager.start_level()
    return player, level, GAME_PLAYING, level_index, score_manager


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("RealFakeGame")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)

    player, level, game_state, level_index, score_manager = create_game()
    shop = UpgradeShop()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif is_restart_event(event, game_state):
                player, level, game_state, level_index, score_manager = create_game()
                shop = UpgradeShop()
            elif game_state == GAME_SHOP and event.type == pygame.KEYDOWN:
                if event.key in SHOP_KEYS:
                    shop.buy(SHOP_KEYS[event.key], player, score_manager)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    next_level = level_index + 1
                    if next_level >= len(LEVEL_FILES):
                        score_manager.save_highscore()
                        game_state = GAME_WON
                    else:
                        player, level, game_state, level_index, score_manager = create_game(
                            next_level,
                            score_manager,
                            player,
                        )

        if game_state == GAME_PLAYING:
            player.step()
            level.step(player.pos)
            handle_collisions(player, level, score_manager)
            game_state = get_progress_state(player, level, level_index)
            if game_state in (GAME_SHOP, GAME_WON):
                score_manager.save_highscore()
            elif game_state == GAME_OVER:
                score_manager.save_highscore()

        screen.fill(BLACK)
        if game_state == GAME_SHOP:
            draw_shop(screen, font, player, score_manager, shop, level_index)
        else:
            level.draw(screen)
            player.draw(screen)
            draw_hud(screen, font, player, score_manager, level_index)

        if game_state == GAME_OVER:
            draw_game_over(screen, font, player, score_manager)
        elif game_state == GAME_WON:
            draw_win(screen, font, score_manager)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
