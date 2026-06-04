# main.py
# Game loop for RealFakeGame.
#
# Controls:
#   Mouse X - move player left/right
#   ESC     - quit

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, WHITE
from player import Player
from level import Level


GAME_PLAYING = "playing"
GAME_OVER = "gameover"


def handle_collisions(player: Player, level: Level) -> None:
    """Resolve obstacle, shot/enemy, and enemy/player collisions."""
    player_rect = player.get_rect()
    for obstacle in level.obstacles:
        if obstacle.collides_with(player_rect):
            obstacle.apply_to_player(player)

    remaining_shots = []
    for shot in player.shots:
        hit_enemy = None
        for enemy in level.enemies:
            if enemy.is_alive() and shot.get_rect().colliderect(enemy.get_rect()):
                hit_enemy = enemy
                break

        if hit_enemy is None:
            if shot.is_alive():
                remaining_shots.append(shot)
            continue

        hit_enemy.hp = 0
        hit_enemy.alive = False
    player.shots = remaining_shots
    level.enemies = [enemy for enemy in level.enemies if enemy.is_alive()]

    player_rect = player.get_rect()
    remaining_enemies = []
    for enemy in level.enemies:
        if enemy.get_rect().colliderect(player_rect):
            player.hp = max(0, player.hp - enemy.damage)
            enemy.alive = False
        elif enemy.is_alive():
            remaining_enemies.append(enemy)
    level.enemies = remaining_enemies


def get_game_state(player: Player) -> str:
    return GAME_OVER if player.hp <= 0 else GAME_PLAYING


def get_weapon_status(player: Player) -> str:
    return f"DMG {player.dmg}  RATE {player.cad}  SPEED {player.shotspd}"


def is_restart_event(event: pygame.event.Event, game_state: str) -> bool:
    return (
        game_state == GAME_OVER
        and event.type == pygame.KEYDOWN
        and event.key == pygame.K_r
    )


def draw_hud(screen: pygame.Surface, font: pygame.font.Font, player: Player) -> None:
    hp = max(0, player.hp)
    hp_text = font.render(f"HP: {hp}", True, WHITE)
    screen.blit(hp_text, (16, 16))

    bar_width = 160
    bar_height = 14
    x = 16
    y = 44
    pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))
    fill_width = int(bar_width * min(1.0, hp / 100))
    pygame.draw.rect(screen, (54, 210, 92), (x, y, fill_width, bar_height))
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 1)

    small_font = pygame.font.Font(None, 22)
    weapon_text = small_font.render(get_weapon_status(player), True, WHITE)
    screen.blit(weapon_text, (16, 68))

    if player.status_message:
        status_text = small_font.render(player.status_message, True, (255, 220, 90))
        screen.blit(status_text, (16, 92))


def draw_game_over(screen: pygame.Surface, font: pygame.font.Font, player: Player) -> None:
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    title = font.render("GAME OVER", True, WHITE)
    hp_text = font.render(f"HP: {max(0, player.hp)}", True, WHITE)
    restart_text = font.render("Press R to restart", True, WHITE)
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))
    screen.blit(hp_text, hp_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))
    screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)))


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


def create_game() -> tuple[Player, Level, str]:
    player = create_player()
    level = Level()
    level.load("lvl001.rfg")
    return player, level, GAME_PLAYING


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("RealFakeGame")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)

    player, level, game_state = create_game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif is_restart_event(event, game_state):
                player, level, game_state = create_game()

        if game_state == GAME_PLAYING:
            player.step()
            level.step(player.pos)
            handle_collisions(player, level)
            game_state = get_game_state(player)

        screen.fill(BLACK)
        level.draw(screen)
        player.draw(screen)
        draw_hud(screen, font, player)

        if game_state == GAME_OVER:
            draw_game_over(screen, font, player)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
