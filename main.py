import random  # Fuer Zufallswerte.

import pygame


WIDTH = 800
HEIGHT = 600
WORLD_WIDTH = 2200  # Groesse der Spielwelt.
WORLD_HEIGHT = 1600  # Groesse der Spielwelt.
MIN_WINDOW_WIDTH = 500  # Minimale Fensterbreite.
MAX_WINDOW_WIDTH = 1200  # Maximale Fensterbreite.
MIN_WINDOW_HEIGHT = 400  # Minimale Fensterhoehe.
MAX_WINDOW_HEIGHT = 900  # Maximale Fensterhoehe.
WINDOW_SIZE_STEP = 40  # Schrittweite fuer Fensteraenderungen.
SQUARE_SIZE = 40
SPEED = 5
FPS = 60
BACKGROUND_COLOR = (11, 13, 16)
SQUARE_COLOR = (255, 107, 53)
GRID_COLOR = (35, 40, 48)  # Farbe des Rasters.
GRID_SIZE = 80  # Abstand der Rasterlinien.
BUBBLE_COUNT = 5  # Anzahl aktiver Blasen.
BUBBLE_RADIUS = 24  # Radius der Blasen.
BUBBLE_SPEED_MIN = -3  # Minimale Startgeschwindigkeit.
BUBBLE_SPEED_MAX = 3  # Maximale Startgeschwindigkeit.
BUBBLE_RESPAWN_MS = 10_000  # Intervall fuer neue Blasen.


def random_color() -> tuple[int, int, int]:
    return (
        random.randint(60, 255),
        random.randint(60, 255),
        random.randint(60, 255),
    )  # Erzeugt eine helle Farbe.


def create_bubble() -> dict[str, int | tuple[int, int, int]]:
    dx = 0
    dy = 0
    while dx == 0 and dy == 0:
        dx = random.randint(BUBBLE_SPEED_MIN, BUBBLE_SPEED_MAX)
        dy = random.randint(BUBBLE_SPEED_MIN, BUBBLE_SPEED_MAX)

    return {
        "x": random.randint(BUBBLE_RADIUS, WORLD_WIDTH - BUBBLE_RADIUS),
        "y": random.randint(BUBBLE_RADIUS, WORLD_HEIGHT - BUBBLE_RADIUS),
        "dx": dx,
        "dy": dy,
        "color": random_color(),
    }  # Erzeugt eine Blase.


def scaled_velocity(value: int, multiplier: float) -> float:
    return value * multiplier  # Skaliert die Geschwindigkeit.


def next_window_size(current_width: int, current_height: int) -> tuple[int, int]:
    next_width = current_width + random.choice((-WINDOW_SIZE_STEP, WINDOW_SIZE_STEP))
    next_height = current_height + random.choice((-WINDOW_SIZE_STEP, WINDOW_SIZE_STEP))
    next_width = max(MIN_WINDOW_WIDTH, min(next_width, MAX_WINDOW_WIDTH))
    next_height = max(MIN_WINDOW_HEIGHT, min(next_height, MAX_WINDOW_HEIGHT))
    return next_width, next_height  # Waehlt eine neue Fenstergroesse.


def main() -> None:
    pygame.init()
    window_width = WIDTH  # Aktuelle Fensterbreite.
    window_height = HEIGHT  # Aktuelle Fensterhoehe.
    screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption("bubble popping")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)  # Schrift fuer die Anzeige.

    x = WORLD_WIDTH // 2  # Startposition X.
    y = WORLD_HEIGHT // 2  # Startposition Y.
    square_color = SQUARE_COLOR  # Aktuelle Farbe der Figur.
    background_color = BACKGROUND_COLOR  # Aktuelle Hintergrundfarbe.
    bubbles = [create_bubble() for _ in range(BUBBLE_COUNT)]  # Startet mit Blasen.
    last_bubble_respawn = pygame.time.get_ticks()  # Startzeit fuer Respawn.
    score = 0  # Punktestand.
    bubble_speed_multiplier = 1.0  # Aktueller Tempofaktor.
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        moved = False  # Bewegung im aktuellen Frame.
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x -= SPEED
            moved = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x += SPEED
            moved = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            y -= SPEED
            moved = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            y += SPEED
            moved = True

        x = max(0, min(x, WORLD_WIDTH - SQUARE_SIZE))  # Begrenzt X.
        y = max(0, min(y, WORLD_HEIGHT - SQUARE_SIZE))  # Begrenzt Y.

        if moved and random.random() < 0.08:  # Aendert die Figurfarbe gelegentlich.
            square_color = random_color()

        for bubble in bubbles:
            bubble["x"] += scaled_velocity(bubble["dx"], bubble_speed_multiplier)  # Bewegt die Blase.
            bubble["y"] += scaled_velocity(bubble["dy"], bubble_speed_multiplier)  # Bewegt die Blase.

            if bubble["x"] <= BUBBLE_RADIUS or bubble["x"] >= WORLD_WIDTH - BUBBLE_RADIUS:
                bubble["dx"] *= -1  # Prallt horizontal ab.
                bubble["color"] = random_color()  # Aendert die Farbe.
            if bubble["y"] <= BUBBLE_RADIUS or bubble["y"] >= WORLD_HEIGHT - BUBBLE_RADIUS:
                bubble["dy"] *= -1  # Prallt vertikal ab.
                bubble["color"] = random_color()  # Aendert die Farbe.

        player_center_x = x + SQUARE_SIZE // 2
        player_center_y = y + SQUARE_SIZE // 2
        remaining_bubbles = []
        for bubble in bubbles:
            distance_x = player_center_x - bubble["x"]
            distance_y = player_center_y - bubble["y"]
            collision_distance = BUBBLE_RADIUS + SQUARE_SIZE // 2
            if distance_x * distance_x + distance_y * distance_y <= collision_distance * collision_distance:
                score += 1  # Erhoeht den Punktestand.
                background_color = random_color()  # Aendert den Hintergrund.
                bubble_speed_multiplier += 0.1  # Erhoeht das Tempo.
                window_width, window_height = next_window_size(window_width, window_height)  # Aendert die Fenstergroesse.
                screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)  # Aktualisiert das Fenster.
            else:
                remaining_bubbles.append(bubble)
        bubbles = remaining_bubbles  # Entfernt geplatzte Blasen.

        now = pygame.time.get_ticks()
        if now - last_bubble_respawn >= BUBBLE_RESPAWN_MS:
            while len(bubbles) < BUBBLE_COUNT:
                bubbles.append(create_bubble())  # Fuellt Blasen wieder auf.
            last_bubble_respawn = now  # Setzt den Timer neu.

        camera_x = max(0, min(x - window_width // 2, WORLD_WIDTH - window_width))  # Berechnet Kamera X.
        camera_y = max(0, min(y - window_height // 2, WORLD_HEIGHT - window_height))  # Berechnet Kamera Y.

        screen.fill(background_color)
        for grid_x in range(0, WORLD_WIDTH + 1, GRID_SIZE):  # Zeichnet vertikale Linien.
            pygame.draw.line(
                screen,
                GRID_COLOR,
                (grid_x - camera_x, -camera_y),
                (grid_x - camera_x, WORLD_HEIGHT - camera_y),
            )
        for grid_y in range(0, WORLD_HEIGHT + 1, GRID_SIZE):  # Zeichnet horizontale Linien.
            pygame.draw.line(
                screen,
                GRID_COLOR,
                (-camera_x, grid_y - camera_y),
                (WORLD_WIDTH - camera_x, grid_y - camera_y),
            )

        for bubble in bubbles:
            bubble_screen_x = bubble["x"] - camera_x
            bubble_screen_y = bubble["y"] - camera_y
            pygame.draw.circle(
                screen,
                bubble["color"],
                (int(bubble_screen_x), int(bubble_screen_y)),
                BUBBLE_RADIUS,
            )  # Zeichnet die Blase.

        player_screen_x = x - camera_x  # Bildschirmposition X.
        player_screen_y = y - camera_y  # Bildschirmposition Y.
        pygame.draw.rect(screen, square_color, (player_screen_x, player_screen_y, SQUARE_SIZE, SQUARE_SIZE))
        score_surface = font.render(f"Punkte: {score}", True, (245, 245, 245))
        screen.blit(score_surface, (20, 20))  # Zeichnet die Punkte.
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
