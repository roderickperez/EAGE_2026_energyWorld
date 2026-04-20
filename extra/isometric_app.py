# main.py
import sys
import pygame
import world # Imports your backend file

pygame.init()

# ── Layout & Constants ────────────────────────────────────────────────────────
DISPLAY_INFO = pygame.display.Info()
SCREEN_W = DISPLAY_INFO.current_w
SCREEN_H = DISPLAY_INFO.current_h

ISO_W   = int(SCREEN_W * 0.80)
PANEL_W = SCREEN_W - ISO_W
PANEL_H = SCREEN_H // 2

BASE_TILE_W = 64
BASE_TILE_H = 32
BLOCK_Z_STEP = 32 # 64x64 tile with 32px top diamond leaves 32px for vertical wall

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption("EnergyWorld — 3D Isometric Builder")
clock = pygame.time.Clock()
font  = pygame.font.SysFont("monospace", 13)
large_font = pygame.font.SysFont("monospace", 20, bold=True)

# ── Load Sprites ──────────────────────────────────────────────────────────────
SPRITES = {}
try:
    SPRITES[1] = pygame.image.load("assests/basicTopSprite.png").convert_alpha()
    SPRITES[2] = pygame.image.load("assests/deepSprite.png").convert_alpha()
except FileNotFoundError as e:
    print(f"Warning: Sprites missing ({e}). Game will render colored polygons instead.")

# ── Init World Data ───────────────────────────────────────────────────────────
print("Generating world and calculating culling... (This takes a second)")
world_data = world.generate_world()
render_list = world.calculate_visible_blocks(world_data)
print(f"Done! Rendering {len(render_list)} visible blocks out of 100,000.")

# ── Interaction States ────────────────────────────────────────────────────────
hover_mode = "CELL"     # Modes: 'CELL', 'INLINE', 'XLINE'
selected_slice = None   # Will store dict: {'type': 'INLINE', 'index': 50}

# ── Helpers ───────────────────────────────────────────────────────────────────
def grid_to_iso_3d(x: int, y: int, z: int, tile_w: float, tile_h: float) -> tuple[float, float]:
    """3D Grid coordinates → isometric pixel offset."""
    px = (x - y) * (tile_w / 2)
    py = (x + y) * (tile_h / 2) - (z * BLOCK_Z_STEP * (tile_w / BASE_TILE_W))
    return px, py

def screen_to_iso_grid(sx: int, sy: int, tile_w: float, tile_h: float, cam_x: float, cam_y: float):
    """Approximates mouse to the TOP layer (Z=9) of the grid."""
    x = sx - ISO_W / 2 - cam_x
    y = sy - SCREEN_H / 2 - cam_y + ( (world.MAX_Z - 1) * BLOCK_Z_STEP * (tile_w / BASE_TILE_W))
    gx = (y / (tile_h / 2) + x / (tile_w / 2)) / 2
    gy = (y / (tile_h / 2) - x / (tile_w / 2)) / 2
    return int(gx), int(gy)

def get_fit_zoom():
    grid_pixel_w = world.GRID_SIZE * BASE_TILE_W
    fit_zoom = min(ISO_W / grid_pixel_w, SCREEN_H / grid_pixel_w)
    return fit_zoom * 0.92

# ── Camera Setup ──────────────────────────────────────────────────────────────
MIN_ZOOM = get_fit_zoom()
zoom = MIN_ZOOM

def get_start_camera(tile_w, tile_h):
    """Accurately calculates the exact center of the 3D grid to start the camera."""
    top_y = grid_to_iso_3d(0, 0, world.MAX_Z - 1, tile_w, tile_h)[1]
    bot_y = grid_to_iso_3d(world.GRID_SIZE - 1, world.GRID_SIZE - 1, 0, tile_w, tile_h)[1]
    return 0, -((top_y + bot_y) / 2)

cam_x, cam_y = get_start_camera(BASE_TILE_W * zoom, BASE_TILE_H * zoom)
dragging = False

# ── Main Loop ─────────────────────────────────────────────────────────────────
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
            
        # Keyboard Mode Switching
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                hover_mode = "CELL"
                selected_slice = None
            elif event.key == pygame.K_i:
                hover_mode = "INLINE"
            elif event.key == pygame.K_x:
                hover_mode = "XLINE"

        # Mouse Dragging
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2 and event.pos[0] < ISO_W:
            dragging = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            dragging = False
        if event.type == pygame.MOUSEMOTION and dragging:
            cam_x += event.rel[0]
            cam_y += event.rel[1]
            
        # Selection Click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and event.pos[0] < ISO_W:
            gx, gy = screen_to_iso_grid(event.pos[0], event.pos[1], BASE_TILE_W * zoom, BASE_TILE_H * zoom, cam_x, cam_y)
            if 0 <= gx < world.GRID_SIZE and 0 <= gy < world.GRID_SIZE:
                if hover_mode == "INLINE":
                    selected_slice = {'type': 'INLINE', 'index': gy}
                elif hover_mode == "XLINE":
                    selected_slice = {'type': 'XLINE', 'index': gx}
            
        # Zoom
        if event.type == pygame.MOUSEBUTTONDOWN and event.pos[0] < ISO_W and event.button in (4, 5):
            prev_zoom = zoom
            zoom = min(2.5, zoom * 1.1) if event.button == 4 else max(MIN_ZOOM, zoom / 1.1)
            
            px, py = event.pos
            wx, wy = px - ISO_W / 2 - cam_x, py - SCREEN_H / 2 - cam_y
            if prev_zoom != 0:
                wx *= (zoom / prev_zoom)
                wy *= (zoom / prev_zoom)
                cam_x, cam_y = px - ISO_W / 2 - wx, py - SCREEN_H / 2 - wy

    tile_w, tile_h = BASE_TILE_W * zoom, BASE_TILE_H * zoom
    screen.fill((20, 20, 20))
    mx, my = pygame.mouse.get_pos()

    gx_h, gy_h = screen_to_iso_grid(mx, my, tile_w, tile_h, cam_x, cam_y)
    is_hovering_map = (0 <= gx_h < world.GRID_SIZE and 0 <= gy_h < world.GRID_SIZE and mx < ISO_W)

    # ── PANEL 1: ISOMETRIC 3D VIEW ───────────────────────────────────────────
    iso_surf = pygame.Surface((ISO_W, SCREEN_H))
    iso_surf.fill((30, 30, 30))

    pygame.draw.line(iso_surf, (255, 100, 100), (80, 100), (50, 70), 3)
    pygame.draw.polygon(iso_surf, (255, 100, 100), [(50,70), (60,70), (50,80)])
    iso_surf.blit(large_font.render("N", True, (255, 100, 100)), (35, 50))

    # PASS 1: DRAW ALL BLOCKS (No Highlights)
    for block in render_list:
        z, y, x, b_id = block
        ix, iy = grid_to_iso_3d(x, y, z, tile_w, tile_h)
        cx, cy = ix + ISO_W / 2 + cam_x, iy + SCREEN_H / 2 + cam_y
        
        sprite = SPRITES.get(b_id)
        if sprite:
            scale_w = int(tile_w)
            scale_h = int(scale_w * (sprite.get_height() / sprite.get_width()))
            s_sprite = pygame.transform.scale(sprite, (scale_w + 1, scale_h + 1))
            rect = s_sprite.get_rect(centerx=int(cx), top=int(cy - tile_h / 2))
            iso_surf.blit(s_sprite, rect)
        else:
            top    = (cx,              cy - tile_h / 2)
            right  = (cx + tile_w / 2, cy)
            bottom = (cx,              cy + tile_h / 2)
            left   = (cx - tile_w / 2, cy)
            poly_col = (100, 150, 100) if b_id == 1 else (150, 100, 50)
            pygame.draw.polygon(iso_surf, poly_col, [top, right, bottom, left])
            pygame.draw.polygon(iso_surf, (0, 0, 0), [top, right, bottom, left], 1)

    # PASS 2: DRAW HIGHLIGHTS ON TOP OF FINISHED MAP
    if is_hovering_map:
        for block in render_list:
            z, y, x, b_id = block
            if z == world.MAX_Z - 1:
                highlight = False
                if hover_mode == "CELL" and x == gx_h and y == gy_h: highlight = True
                elif hover_mode == "INLINE" and y == gy_h: highlight = True
                elif hover_mode == "XLINE" and x == gx_h: highlight = True

                if highlight:
                    ix, iy = grid_to_iso_3d(x, y, z, tile_w, tile_h)
                    cx, cy = ix + ISO_W / 2 + cam_x, iy + SCREEN_H / 2 + cam_y
                    
                    # Calculate ONLY the top diamond coordinates
                    top    = (cx,              cy - tile_h / 2)
                    right  = (cx + tile_w / 2, cy)
                    bottom = (cx,              cy + tile_h / 2)
                    left   = (cx - tile_w / 2, cy)
                    
                    # FIX: Draw the solid red fill for EVERY highlighted block
                    pygame.draw.polygon(iso_surf, (255, 50, 50), [top, right, bottom, left])
                        
                    # Draw a crisp white outline to make the selection pop
                    pygame.draw.polygon(iso_surf, (255, 255, 255), [top, right, bottom, left], 2)

    iso_surf.blit(font.render("3D ISOMETRIC VIEW", True, (180, 180, 180)), (10, 10))
    iso_surf.blit(font.render(f"Mode: {hover_mode} (Press I, X, C)", True, (255, 200, 100)), (10, 28))
    screen.blit(iso_surf, (0, 0))

    # ── PANEL 2: INFO PANEL ──────────────────────────────────────────────────
    info_surf = pygame.Surface((PANEL_W, PANEL_H))
    info_surf.fill((40, 40, 55))
    pygame.draw.rect(info_surf, (80, 80, 120), (0, 0, PANEL_W, PANEL_H), 2)

    lines = [
        "INFO PANEL", "",
        f"Grid: {world.GRID_SIZE}x{world.GRID_SIZE}x{world.MAX_Z}",
        f"Hover: ({gx_h}, {gy_h})" if is_hovering_map else "Hover: None",
        "", "Controls:",
        " [C] = Cell Selection",
        " [I] = Inline Selection",
        " [X] = Xline Selection",
        " L-Click = Select Slice",
        " MMB = Pan Camera",
        " Wheel = Zoom"
    ]
    for i, line in enumerate(lines):
        info_surf.blit(font.render(line, True, (200, 200, 220)), (10, 10 + i * 19))
    screen.blit(info_surf, (ISO_W, 0))

    # ── PANEL 3: DYNAMIC MAP / CROSS-SECTION ─────────────────────────────────
    bot_surf = pygame.Surface((PANEL_W, PANEL_H))
    bot_surf.fill((30, 30, 30))
    pygame.draw.rect(bot_surf, (80, 120, 80), (0, 0, PANEL_W, PANEL_H), 2)

    if selected_slice is None:
        bot_surf.blit(font.render("TOP-DOWN MAP (Centered)", True, (180, 180, 180)), (10, 10))
        
        TD_TILE = max(1, min(PANEL_W // world.GRID_SIZE, (PANEL_H - 40) // world.GRID_SIZE))
        off_x = (PANEL_W - (world.GRID_SIZE * TD_TILE)) // 2
        off_y = (PANEL_H - (world.GRID_SIZE * TD_TILE)) // 2 + 10
        
        bot_surf.blit(large_font.render("N ↑", True, (255, 100, 100)), (10, 30))

        for y in range(world.GRID_SIZE):
            for x in range(world.GRID_SIZE):
                color = (100, 150, 100)
                if is_hovering_map:
                    if hover_mode == "CELL" and x == gx_h and y == gy_h: color = (255, 50, 50)
                    elif hover_mode == "INLINE" and y == gy_h: color = (255, 50, 50)
                    elif hover_mode == "XLINE" and x == gx_h: color = (255, 50, 50)
                
                rect = (x * TD_TILE + off_x, y * TD_TILE + off_y, TD_TILE, TD_TILE)
                pygame.draw.rect(bot_surf, color, rect)

    else:
        title = f"CROSS-SECTION: {selected_slice['type']} {selected_slice['index']}"
        bot_surf.blit(font.render(title, True, (255, 200, 100)), (10, 10))
        
        CS_W = max(1, PANEL_W // world.GRID_SIZE)
        CS_H = max(1, (PANEL_H - 60) // world.MAX_Z)
        cs_off_x = (PANEL_W - (world.GRID_SIZE * CS_W)) // 2
        cs_off_y = (PANEL_H - (world.MAX_Z * CS_H)) // 2 + 20

        for z in range(world.MAX_Z):
            for i in range(world.GRID_SIZE):
                x = i if selected_slice['type'] == 'INLINE' else selected_slice['index']
                y = selected_slice['index'] if selected_slice['type'] == 'INLINE' else i
                
                block_id = world_data[z][y][x]
                color = (100, 150, 100) if block_id == 1 else (150, 100, 50)
                
                screen_z = (world.MAX_Z - 1) - z 
                rect = (i * CS_W + cs_off_x, screen_z * CS_H + cs_off_y, CS_W, CS_H)
                pygame.draw.rect(bot_surf, color, rect)

    screen.blit(bot_surf, (ISO_W, PANEL_H))
    
    # ── Dividers ──────────────────────────────────────────────────────────────
    pygame.draw.line(screen, (60, 60, 60), (ISO_W, 0), (ISO_W, SCREEN_H), 2)
    pygame.draw.line(screen, (60, 60, 60), (ISO_W, PANEL_H), (SCREEN_W, PANEL_H), 2)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()