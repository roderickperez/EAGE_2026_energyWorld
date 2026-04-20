# /home/roderickperez/DataScienceProjects/EAGE_EnergyWorld/core/top_down_app.py
import sys
import pygame

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
GRID_SIZE = 10

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Top-Down Grid")
clock = pygame.time.Clock()


def draw_tile_topdown(
    surface: pygame.Surface,
    gx: int,
    gy: int,
    color: tuple[int, int, int],
) -> None:
    x = gx * TILE_SIZE + 200
    y = gy * TILE_SIZE + 100
    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (0, 0, 0), rect, 1)


def get_tile_at_mouse(mouse_x: int, mouse_y: int) -> tuple[int, int] | None:
    gx = (mouse_x - 200) // TILE_SIZE
    gy = (mouse_y - 100) // TILE_SIZE
    if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
        return gx, gy
    return None


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))

    mouse_x, mouse_y = pygame.mouse.get_pos()
    hovered_tile = get_tile_at_mouse(mouse_x, mouse_y)

    for gx in range(GRID_SIZE):
        for gy in range(GRID_SIZE):
            color = (100, 150, 100)
            if hovered_tile and hovered_tile == (gx, gy):
                color = (150, 200, 150)
            draw_tile_topdown(screen, gx, gy, color)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()