import pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = clock.tick(fps) each frame to cap speed and measure delta time." data-tip-url="https://pyga.me/docs/ref/time.html#pygame.time.Clock">pygame.time.Clock()
x, y = 400, 300  # the whole world in two numbers
 
running = True
while running:  # 60 times per second
    # ---- events ----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
 
    # ---- update ----
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:  x -= 5
    if keys[pygame.K_RIGHT]: x += 5
    if keys[pygame.K_UP]:    y -= 5
    if keys[pygame.K_DOWN]:  y += 5
 
    # ---- draw ----
    screen.fill((11, 13, 16))
    pygame.draw.rect(screen, (255, 107, 53), (x, y, 40, 40))
    pygame.display.flip()
    clock.tick(60)
 
pygame.quit()