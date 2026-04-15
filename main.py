import pygame


WIDTH = 800
HEIGHT = 600
SQUARE_SIZE = 40
SPEED = 5
FPS = 60
BACKGROUND_COLOR = (11, 13, 16)
SQUARE_COLOR = (255, 107, 53)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("hello-square")
    clock = pygame.time.Clock()

    x = (WIDTH - SQUARE_SIZE) // 2
    y = (HEIGHT - SQUARE_SIZE) // 2
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x -= SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x += SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            y -= SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            y += SPEED

        screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(screen, SQUARE_COLOR, (x, y, SQUARE_SIZE, SQUARE_SIZE))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
