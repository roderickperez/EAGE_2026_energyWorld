import sys
import os
import math
import pygame
import level0.level0_world as world
import time_system
import ui_panels
import save_manager

# Layout constants (shared logic)
BASE_TILE_W = 64
BASE_TILE_H = 32
BLOCK_Z_STEP = 32

def clean_white_background(surf, threshold=20):
    """Surgically cleans ONLY the external background using per-pixel alpha."""
    surf = surf.convert_alpha()
    w, h = surf.get_size()
    # Mask of all pixels near white
    near_white = pygame.mask.from_threshold(surf, (255, 255, 255), (threshold, threshold, threshold, 255))
    
    # Isolate the background component (connected to the corners)
    bg_mask = pygame.mask.Mask((w, h))
    for corner in [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]:
        if near_white.get_at(corner):
            comp = near_white.connected_component(corner)
            bg_mask.draw(comp, (0, 0))
            
    # Create an alpha mask surface: Start fully opaque white
    alpha_mask = pygame.Surface((w, h), pygame.SRCALPHA)
    alpha_mask.fill((255, 255, 255, 255))
    
    # Render background mask as pure transparent white
    bg_surf = bg_mask.to_surface(setcolor=(255, 255, 255, 0), unsetcolor=(0, 0, 0, 0))
    # Punch the background into the alpha mask
    alpha_mask.blit(bg_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    
    # Multiply original by alpha mask to make background transparent while keeping internal white
    surf.blit(alpha_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return surf

def run(screen, clock, fonts, save_data=None):
    font, large_font, huge_font = fonts
    SCREEN_W, SCREEN_H = screen.get_size()
    ISO_W = int(SCREEN_W * 0.80)
    PANEL_W = SCREEN_W - ISO_W
    PANEL_H = SCREEN_H // 2

    time_manager = time_system.TimeManager(time_scale=30000) # 30,000x scale

    # Sprites and Cache
    SPRITES = {}
    SCALED_SPRITES = {}

    try:
        SPRITES[1] = pygame.image.load("assests/basicTopSprite.png").convert_alpha()
        SPRITES[2] = pygame.image.load("assests/deepSprite.png").convert_alpha()
        try:
            SPRITES[3] = pygame.image.load("assests/road1.png").convert_alpha()
            SPRITES[3].set_colorkey((255, 255, 255))
        except: pass
        try:
            SPRITES[4] = pygame.image.load("assests/solarPanel_V1_64x32.png").convert()
            SPRITES[4].set_colorkey(SPRITES[4].get_at((0,0)))
        except: pass
        try:
            # Load animation frames for wind turbine (ID 5)
            SPRITES[5] = []
            frame_paths = [
                "assests/windTurbine_whiteBackground_V2.png",
                "assests/windTurbine_whiteBackground_V3.png",
                "assests/windTurbine_whiteBackground_V4.png",
                "assests/windTurbine_whiteBackground_V5.png"
            ]
            for path in frame_paths:
                raw_frame = pygame.image.load(path).convert()
                # Maintain aspect ratio, scale to reasonable height
                wf, hf = raw_frame.get_size()
                target_hf = 320
                sc = target_hf / hf
                scaled_frame = pygame.transform.smoothscale(raw_frame, (int(wf * sc), target_hf))
                # Clean each frame surgically
                SPRITES[5].append(clean_white_background(scaled_frame, threshold=30))
        except Exception as e:
            print(f"Warning: windTurbine animation load failed: {e}")
            
        try:
            # Load Coal Plant (ID 6)
            raw_coal = pygame.image.load("assests/coalPlant_V2.jpg").convert()
            wc, hc = raw_coal.get_size()
            target_hc = 200 # Plants are substantial but not as tall as turbines
            sc = target_hc / hc
            scaled_coal = pygame.transform.smoothscale(raw_coal, (int(wc * sc), target_hc))
            # Conservative threshold to prevent asset-eating on JPGs
            SPRITES[6] = clean_white_background(scaled_coal, threshold=10)
            print(f"Coal plant asset processed (ID 6). Size: {SPRITES[6].get_size()}")
        except Exception as e:
            print(f"Warning: Coal plant asset load failed: {e}")

        # New: Dynamically load road variants from assests/road/
        ROAD_VARIANTS = {} # id -> filename
        road_id_list = []
        road_folder = "assests/road"
        if os.path.exists(road_folder):
            next_road_id = 100
            for f in sorted(os.listdir(road_folder)):
                if f.lower().endswith(".png"):
                    try:
                        path = os.path.join(road_folder, f)
                        sprite = pygame.image.load(path).convert_alpha()
                        # Apply colorkey for road sprites (white background)
                        sprite.set_colorkey((255, 255, 255))
                        
                        SPRITES[next_road_id] = sprite
                        ROAD_VARIANTS[next_road_id] = f
                        road_id_list.append(next_road_id)
                        next_road_id += 1
                    except Exception as e:
                        print(f"Error loading road sprite {f}: {e}")
        
        # Fallback if no roads found in subfolder
        if not road_id_list and 3 in SPRITES:
            road_id_list = [3]
            ROAD_VARIANTS[3] = "road1.png"
    except FileNotFoundError as e:
        print(f"Warning: Sprites missing ({e}). Game will render colored polygons instead.")

    def update_sprite_cache(zoom_level: float):
        nonlocal SCALED_SPRITES
        tile_w = BASE_TILE_W * zoom_level
        SCALED_SPRITES = {}
        for b_id, sprite in SPRITES.items():
            if isinstance(sprite, list):
                # Handle animation frames
                SCALED_SPRITES[b_id] = []
                for frame in sprite:
                    sw = int(tile_w)
                    sh = int(sw * (frame.get_height() / frame.get_width()))
                    SCALED_SPRITES[b_id].append(pygame.transform.scale(frame, (sw + 1, sh + 1)))
            else:
                scale_w = int(tile_w)
                scale_h = int(scale_w * (sprite.get_height() / sprite.get_width()))
                SCALED_SPRITES[b_id] = pygame.transform.scale(sprite, (scale_w + 1, scale_h + 1))

    # World data
    print("Generating Level 0 world...")
    balance = 1000000
    if save_data:
        world_data = save_data["world_data"]
        time_manager.current_date = save_data["current_date"]
        balance = save_data.get("balance", 1000000)
    else:
        world_data = world.generate_world()
    
    render_list = world.calculate_visible_blocks(world_data)
    
    # Interaction state
    hover_mode = "CELL"
    selected_slice = None
    selected_road_idx = 0

    # Performance: Map Caching
    td_tile = max(1, min(PANEL_W // world.GRID_SIZE, (PANEL_H - 40) // world.GRID_SIZE))
    map_content_surf = pygame.Surface((world.GRID_SIZE * td_tile, world.GRID_SIZE * td_tile))
    cached_map_valid = False

    # UI Panels
    panel_rect = (ISO_W + 10, 10, PANEL_W - 20, PANEL_H - 20)
    info_panel = ui_panels.InfoPanel(*panel_rect, font)
    chat_panel = ui_panels.ChatPanel(*panel_rect, font)
    solar_dashboard = ui_panels.SolarDashboard(*panel_rect, font)
    wind_dashboard = ui_panels.WindDashboard(*panel_rect, font)
    show_info_panel = True
    show_chat_panel = False

    def display_grid_coords(x: int, y: int) -> tuple[int, int]:
        return world.GRID_SIZE - 1 - x, world.GRID_SIZE - 1 - y

    def render_sort_key(block: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        z, y, x, _ = block
        dx, dy = display_grid_coords(x, y)
        return (dx + dy, z, dy, dx)

    def grid_to_iso_3d(x: int, y: int, z: int, tile_w: float, tile_h: float) -> tuple[float, float]:
        dx, dy = display_grid_coords(x, y)
        px = (dx - dy) * (tile_w / 2)
        py = (dx + dy) * (tile_h / 2) - (z * BLOCK_Z_STEP * (tile_w / BASE_TILE_W))
        return px, py

    def screen_to_iso_grid(sx: int, sy: int, tile_w: float, tile_h: float,
                           cam_x: float, cam_y: float) -> tuple[int, int]:
        iso_x = sx - ISO_W / 2 - cam_x
        iso_y = sy - SCREEN_H / 2 - cam_y + ((world.MAX_Z - 1) * BLOCK_Z_STEP * (tile_w / BASE_TILE_W))
        dx = (iso_y / (tile_h / 2) + iso_x / (tile_w / 2)) / 2
        dy = (iso_y / (tile_h / 2) - iso_x / (tile_w / 2)) / 2
        gx = world.GRID_SIZE - 1 - math.floor(dx)
        gy = world.GRID_SIZE - 1 - math.floor(dy)
        return gx, gy

    def block_is_highlighted(x: int, y: int, z: int, hx: int, hy: int) -> bool:
        if hover_mode in ("CELL", "ROAD", "SOLAR", "WIND"):
            return z == world.MAX_Z - 1 and x == hx and y == hy
        if hover_mode == "INLINE":
            return y == hy
        if hover_mode == "XLINE":
            return x == hx
        return False

    def get_fit_zoom() -> float:
        grid_pixel_w = world.GRID_SIZE * BASE_TILE_W
        fit_zoom = min(ISO_W / grid_pixel_w, SCREEN_H / grid_pixel_w)
        return fit_zoom * 0.92

    def get_start_camera(tile_w: float, tile_h: float) -> tuple[float, float]:
        top_y = grid_to_iso_3d(0, 0, world.MAX_Z - 1, tile_w, tile_h)[1]
        bot_y = grid_to_iso_3d(world.GRID_SIZE - 1, world.GRID_SIZE - 1, 0, tile_w, tile_h)[1]
        return 0, -((top__y := top_y) + bot_y) / 2 # Using Walrus just because

    render_list.sort(key=render_sort_key)
    MIN_ZOOM = get_fit_zoom()
    zoom = MIN_ZOOM
    update_sprite_cache(zoom)
    # Corrected target name for walrus used above
    top_y_start = grid_to_iso_3d(0, 0, world.MAX_Z - 1, BASE_TILE_W * zoom, BASE_TILE_H * zoom)[1]
    bot_y_start = grid_to_iso_3d(world.GRID_SIZE - 1, world.GRID_SIZE - 1, 0, BASE_TILE_W * zoom, BASE_TILE_H * zoom)[1]
    cam_x, cam_y = 0, -((top_y_start + bot_y_start) / 2)
    dragging = False

    # Notifications
    notification_text = ""
    notification_timer = 0
    notification_color = (0, 255, 0)

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        time_manager.update(1.0/60.0)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            if event.type == pygame.KEYDOWN:
                if show_chat_panel and chat_panel.active:
                    if event.key == pygame.K_ESCAPE:
                        chat_panel.active = False
                    elif event.key == pygame.K_RETURN:
                        if chat_panel.input_text.strip():
                            chat_panel.add_message("User", chat_panel.input_text)
                            chat_panel.input_text = ""
                            chat_panel.add_message("AI", "Processing energy request...")
                    elif event.key == pygame.K_BACKSPACE:
                        chat_panel.input_text = chat_panel.input_text[:-1]
                    else:
                        chat_panel.input_text += event.unicode
                    continue

                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                elif event.key == pygame.K_i:
                    hover_mode = "CELL"
                    selected_slice = None
                elif event.key == pygame.K_c:
                    hover_mode = "COAL"
                    selected_slice = None
                elif event.key == pygame.K_r:
                    show_info_panel = not show_info_panel
                elif event.key == pygame.K_a:
                    show_chat_panel = not show_chat_panel
                    if show_chat_panel:
                        chat_panel.active = True
                        show_info_panel = False
                elif event.key == pygame.K_x:
                    hover_mode = "XLINE"
                elif event.key == pygame.K_r:
                    if hover_mode == "ROAD" and road_id_list:
                        selected_road_idx = (selected_road_idx + 1) % len(road_id_list)
                    else:
                        hover_mode = "ROAD"
                    selected_slice = None
                elif event.key == pygame.K_s:
                    hover_mode = "SOLAR"
                    selected_slice = None
                elif event.key == pygame.K_w:
                    hover_mode = "WIND"
                    selected_slice = None
                elif event.key == pygame.K_t:
                    hover_mode = "INLINE"
                    selected_slice = None
                elif event.key == pygame.K_d:
                    hover_mode = "DELETE"
                    selected_slice = None
                elif event.key == pygame.K_RETURN:
                    # Alternative placement trigger
                    if is_hovering_map and hover_mode in ("ROAD", "SOLAR", "WIND"):
                        # Re-use logic from mouse click
                        bid = 3
                        if hover_mode == "ROAD" and road_id_list:
                            bid = road_id_list[selected_road_idx]
                        elif hover_mode == "SOLAR": bid = 4
                        elif hover_mode == "WIND": bid = 5
                        
                        world_data[world.MAX_Z - 1][gy_h][gx_h] = bid
                        for i, (z, y, x, b_id) in enumerate(render_list):
                            if z == world.MAX_Z - 1 and y == gy_h and x == gx_h:
                                render_list[i] = (z, y, x, bid)
                                break
                        cached_map_valid = False
                
                elif event.key == pygame.K_F1:
                    save_manager.save_session(world_data, time_manager.current_date, balance)
                    notification_text = "GAME SAVED"
                    notification_timer = pygame.time.get_ticks() + 2000

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2 and event.pos[0] < ISO_W:
                dragging = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                dragging = False
            if event.type == pygame.MOUSEMOTION and dragging:
                cam_x += event.rel[0]
                cam_y += event.rel[1]

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and event.pos[0] < ISO_W:
                gx, gy = screen_to_iso_grid(event.pos[0], event.pos[1], BASE_TILE_W * zoom, BASE_TILE_H * zoom, cam_x, cam_y)
                if 0 <= gx < world.GRID_SIZE and 0 <= gy < world.GRID_SIZE:
                    if hover_mode == "INLINE":
                        selected_slice = {"type": "INLINE", "index": gy}
                    elif hover_mode == "XLINE":
                        selected_slice = {"type": "XLINE", "index": gx}
                    elif hover_mode in ("ROAD", "SOLAR", "WIND", "COAL"):
                        # Placement Logic
                        target_bid = 3
                        cost_buy = 0
                        if hover_mode == "ROAD" and road_id_list:
                            target_bid = road_id_list[selected_road_idx]
                            cost_buy = 500
                        elif hover_mode == "SOLAR": 
                            target_bid = 4
                            cost_buy = 1000
                        elif hover_mode == "WIND": 
                            target_bid = 5
                            cost_buy = 10000
                        elif hover_mode == "COAL":
                            target_bid = 6
                            cost_buy = 50000
                        
                        current_bid = world_data[world.MAX_Z - 1][gy][gx]
                        
                        if current_bid > 2: # Cell is occupied
                            notification_text = "Press [D] to delete current element"
                            notification_color = (255, 160, 0) # Orange
                            notification_timer = pygame.time.get_ticks() + 2500
                        else: # Cell is empty
                            if balance >= cost_buy:
                                balance -= cost_buy
                                world_data[world.MAX_Z - 1][gy][gx] = target_bid
                                for i, (z, y, x, b_id) in enumerate(render_list):
                                    if z == world.MAX_Z - 1 and y == gy and x == gx:
                                        render_list[i] = (z, y, x, target_bid)
                                        break
                                cached_map_valid = False
                            else:
                                notification_text = "INSUFFICIENT FUNDS!"
                                notification_color = (255, 50, 50)
                                notification_timer = pygame.time.get_ticks() + 2000
                    
                    elif hover_mode == "DELETE":
                        current_bid = world_data[world.MAX_Z - 1][gy][gx]
                        if current_bid > 2:
                            # Removal Costs
                            cost_remove = 0
                            if current_bid >= 100 or current_bid == 3: cost_remove = 250 # Road
                            elif current_bid == 4: cost_remove = 2500 # Solar
                            elif current_bid == 5: cost_remove = 20000 # Wind
                            elif current_bid == 6: cost_remove = 15000 # Coal
                            
                            if balance >= cost_remove:
                                balance -= cost_remove
                                world_data[world.MAX_Z - 1][gy][gx] = 1 # Back to grass
                                for i, (z, y, x, b_id) in enumerate(render_list):
                                    if z == world.MAX_Z - 1 and y == gy and x == gx:
                                        render_list[i] = (z, y, x, 1)
                                        break
                                cached_map_valid = False
                                notification_text = "ELEMENT REMOVED"
                                notification_color = (200, 255, 100)
                                notification_timer = pygame.time.get_ticks() + 1500
                            else:
                                notification_text = "NOT ENOUGH CASH TO DELETE!"
                                notification_color = (255, 50, 50)
                                notification_timer = pygame.time.get_ticks() + 2000


            if event.type == pygame.MOUSEBUTTONDOWN and event.pos[0] < ISO_W and event.button in (4, 5):
                prev_zoom = zoom
                zoom = min(2.5, zoom * 1.1) if event.button == 4 else max(MIN_ZOOM, zoom / 1.1)

                px, py = event.pos
                wx, wy = px - ISO_W / 2 - cam_x, py - SCREEN_H / 2 - cam_y
                if prev_zoom != 0:
                    wx *= (zoom / prev_zoom)
                    wy *= (zoom / prev_zoom)
                    cam_x, cam_y = px - ISO_W / 2 - wx, py - SCREEN_H / 2 - wy
                    update_sprite_cache(zoom)

        tile_w, tile_h = BASE_TILE_W * zoom, BASE_TILE_H * zoom
        screen.fill((20, 20, 20))

        # Environmental Data
        solar_irradiance = time_manager.get_solar_irradiance()
        wind_speed = time_manager.get_wind_speed()
        wind_dir = time_manager.get_wind_direction()
        
        installed_panels = []
        installed_turbines = []
        total_production = 0.0
        
        for y in range(world.GRID_SIZE):
            for x in range(world.GRID_SIZE):
                bid = world_data[world.MAX_Z - 1][y][x]
                if bid == 4: # Solar
                    prod = 80 * solar_irradiance
                    installed_panels.append((x, y, prod))
                    total_production += prod
                elif bid == 5: # Wind
                    # Production model: starts at 3m/s, max at 15m/s
                    eff = max(0, min(1.0, (wind_speed - 3) / 12.0))
                    prod = eff * 200.0 # Turbines are more powerful than panels
                    installed_turbines.append((x, y, prod, wind_speed))
                    total_production += prod
        
        solar_dashboard.update(solar_irradiance, installed_panels)
        wind_dashboard.update(total_production if hover_mode == "WIND" else 0, installed_turbines)
        info_panel.energy_history.append(total_production)
        if len(info_panel.energy_history) > info_panel.max_hist:
            info_panel.energy_history.pop(0)

        gx_h, gy_h = screen_to_iso_grid(mx, my, tile_w, tile_h, cam_x, cam_y)
        is_hovering_map = (0 <= gx_h < world.GRID_SIZE and 0 <= gy_h < world.GRID_SIZE and mx < ISO_W)

        # Panel 1: Isometric
        iso_surf = pygame.Surface((ISO_W, SCREEN_H))
        iso_surf.fill((30, 30, 30))

        # North marker corrected to point North-West (Up-Left)
        pygame.draw.line(iso_surf, (255, 100, 100), (50, 70), (25, 45), 3)
        pygame.draw.polygon(iso_surf, (255, 100, 100), [(25, 45), (35, 45), (25, 55)])
        iso_surf.blit(large_font.render("N", True, (255, 100, 100)), (15, 20))

        # Use selected slice as source-of-truth for line modes when available.
        active_hx, active_hy = gx_h, gy_h
        if selected_slice is not None:
            if selected_slice["type"] == "INLINE":
                active_hy = selected_slice["index"]
            elif selected_slice["type"] == "XLINE":
                active_hx = selected_slice["index"]

        # Pass 1: draw full map and highlights (merged to respect depth)
        for z, y, x, b_id in render_list:
            ix, iy = grid_to_iso_3d(x, y, z, tile_w, tile_h)
            cx, cy = ix + ISO_W / 2 + cam_x, iy + SCREEN_H / 2 + cam_y

            # Frustum culling: skip drawing if clearly off-screen
            if cx < -tile_w or cx > ISO_W + tile_w or cy < -tile_h or cy > SCREEN_H + tile_h:
                continue

            # Cube vertex points
            t = (cx, cy - tile_h / 2)
            r = (cx + tile_w / 2, cy)
            b = (cx, cy + tile_h / 2)
            l = (cx - tile_w / 2, cy)
            
            # Bottom vertex points for sides (32px drop)
            rc = (r[0], r[1] + 32)
            bc = (b[0], b[1] + 32)
            lc = (l[0], l[1] + 32)

            sprite = SCALED_SPRITES.get(b_id)
            if sprite:
                # If it's a building or road ID (4, 5, 100+), render sides
                if b_id >= 4:
                    # Draw sides
                    pygame.draw.polygon(iso_surf, (140, 100, 60), [l, b, bc, lc]) # Front-left
                    pygame.draw.polygon(iso_surf, (110, 80, 40), [r, b, bc, rc])  # Front-right
                    # Draw top (usually covered by sprite, but good for safety)
                    pygame.draw.polygon(iso_surf, (100, 150, 100), [t, r, b, l])
                
                offset_y = 0
                if b_id == 4: offset_y = 60 # Float significantly higher above surface
                if b_id == 5: offset_y = 320 # Massive elevation for monumental turbines
                if b_id == 6: offset_y = 60 # Slightly raised to avoid z-depth issues
                
                # Dynamic frame selection for animated sprites
                draw_sprite = sprite
                if isinstance(sprite, list):
                    # Cycle through frames based on ticks (e.g. 100ms per frame)
                    # We use unique seeds to make different turbines out of sync? 
                    # For now just global cycle
                    f_idx = (pygame.time.get_ticks() // 80) % len(sprite)
                    draw_sprite = sprite[f_idx]
                
                rect = draw_sprite.get_rect(centerx=int(cx), top=int(cy - tile_h / 2 - offset_y))
                iso_surf.blit(draw_sprite, rect)
                
                # Apply highlight tint if applicable
                if is_hovering_map and block_is_highlighted(x, y, z, active_hx, active_hy):
                    if hover_mode in ("INLINE", "XLINE"):
                        mask = pygame.mask.from_surface(draw_sprite)
                        red_surf = mask.to_surface(setcolor=(255, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
                        red_surf.set_alpha(170)
                        iso_surf.blit(red_surf, rect)
            else:
                poly_col = (100, 150, 100)
                if b_id == 2: poly_col = (150, 100, 50)
                elif b_id == 3: poly_col = (120, 120, 120)
                elif b_id == 4: poly_col = (255, 255, 0) # Solar Yellow
                elif b_id == 5: poly_col = (0, 255, 255) # Wind Cyan
                elif b_id == 6: poly_col = (0, 0, 0) # Coal Plant Black
                
                # Draw standard cube
                pygame.draw.polygon(iso_surf, poly_col, [t, r, b, l])
                pygame.draw.polygon(iso_surf, (140, 100, 60), [l, b, bc, lc]) # Side L
                pygame.draw.polygon(iso_surf, (110, 80, 40), [r, b, bc, rc])  # Side R

        # Apply Lighting Tint to Isometric View BEFORE UI/Highlights
        tint = time_manager.get_lighting_tint()
        if tint != (255, 255, 255):
            lighting_overlay = pygame.Surface((ISO_W, SCREEN_H))
            lighting_overlay.fill(tint)
            iso_surf.blit(lighting_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Pass 2: Highlights (Not tinted, making them luminous at night)
        if is_hovering_map:
            if hover_mode in ("CELL", "ROAD", "SOLAR", "WIND", "COAL", "DELETE"):
                # Optimize: Direct drawing for single cell modes
                ix, iy = grid_to_iso_3d(active_hx, active_hy, world.MAX_Z - 1, tile_w, tile_h)
                cx, cy = ix + ISO_W / 2 + cam_x, iy + SCREEN_H / 2 + cam_y
                
                t_f = (cx, cy - tile_h / 2)
                r_f = (cx + tile_w / 2, cy)
                b_f = (cx, cy + tile_h / 2)
                l_f = (cx - tile_w / 2, cy)
                
                if hover_mode == "ROAD":
                    rid = road_id_list[selected_road_idx] if road_id_list else 3
                    spr = SCALED_SPRITES.get(rid)
                    if spr:
                        rect = spr.get_rect(centerx=int(cx), top=int(cy - tile_h / 2))
                        iso_surf.blit(spr, rect)
                    else:
                        pygame.draw.polygon(iso_surf, (120, 120, 120), [t_f, r_f, b_f, l_f])
                    pygame.draw.polygon(iso_surf, (200, 200, 200), [t_f, r_f, b_f, l_f], 2)
                elif hover_mode == "SOLAR":
                    pygame.draw.polygon(iso_surf, (255, 255, 0), [t_f, r_f, b_f, l_f])
                    pygame.draw.polygon(iso_surf, (255, 255, 200), [t_f, r_f, b_f, l_f], 2)
                elif hover_mode == "WIND":
                    pygame.draw.polygon(iso_surf, (0, 255, 255), [t_f, r_f, b_f, l_f])
                    pygame.draw.polygon(iso_surf, (200, 255, 255), [t_f, r_f, b_f, l_f], 2)
                elif hover_mode == "COAL":
                    pygame.draw.polygon(iso_surf, (20, 20, 20), [t_f, r_f, b_f, l_f])
                    pygame.draw.polygon(iso_surf, (150, 150, 150), [t_f, r_f, b_f, l_f], 2)
                elif hover_mode == "DELETE":
                    pygame.draw.polygon(iso_surf, (255, 50, 50), [t_f, r_f, b_f, l_f])
                    pygame.draw.polygon(iso_surf, (255, 200, 200), [t_f, r_f, b_f, l_f], 2)
                else: # CELL
                    pygame.draw.polygon(iso_surf, (255, 50, 50), [t_f, r_f, b_f, l_f])
                    pygame.draw.polygon(iso_surf, (255, 255, 255), [t_f, r_f, b_f, l_f], 2)
            else:
                # Traditional loop for volumetric highlights (Line modes)
                z_step = BLOCK_Z_STEP * (tile_w / BASE_TILE_W)
                for z, y, x, b_id in render_list:
                    if block_is_highlighted(x, y, z, active_hx, active_hy):
                        ix, iy = grid_to_iso_3d(x, y, z, tile_w, tile_h)
                        cx, cy = ix + ISO_W / 2 + cam_x, iy + SCREEN_H / 2 + cam_y
                        if cx < -tile_w or cx > ISO_W + tile_w or cy < -tile_h or cy > SCREEN_H + tile_h:
                            continue
                        
                        t_f, r_f, b_f, l_f = (cx, cy - tile_h / 2), (cx + tile_w / 2, cy), (cx, cy + tile_h / 2), (cx - tile_w / 2, cy)
                        
                        # Only highlight faces that are actually visible (exposed)
                        # Top Face
                        if z == world.MAX_Z - 1 or world_data[z+1][y][x] == 0:
                            col = (255, 50, 50)
                            # Darker red for current cell
                            if x == active_hx and y == active_hy and z == world.MAX_Z - 1:
                                col = (150, 0, 0)
                            pygame.draw.polygon(iso_surf, col, [t_f, r_f, b_f, l_f])
                            pygame.draw.polygon(iso_surf, (255, 255, 255), [t_f, r_f, b_f, l_f], 1)
                        
                        # Front-Left Side Face
                        if y == 0 or world_data[z][y-1][x] == 0:
                            col = (200, 40, 40)
                            if x == active_hx and y == active_hy: col = (120, 0, 0)
                            l_f_d = (l_f[0], l_f[1] + z_step)
                            b_f_d = (b_f[0], b_f[1] + z_step)
                            pygame.draw.polygon(iso_surf, col, [l_f, b_f, b_f_d, l_f_d])
                            pygame.draw.polygon(iso_surf, (255, 255, 255), [l_f, b_f, b_f_d, l_f_d], 1)

                        # Front-Right Side Face
                        if x == 0 or world_data[z][y][x-1] == 0:
                            col = (180, 30, 30)
                            if x == active_hx and y == active_hy: col = (100, 0, 0)
                            r_f_d = (r_f[0], r_f[1] + z_step)
                            b_f_d = (b_f[0], b_f[1] + z_step)
                            pygame.draw.polygon(iso_surf, col, [r_f, b_f, b_f_d, r_f_d])
                            pygame.draw.polygon(iso_surf, (255, 255, 255), [r_f, b_f, b_f_d, r_f_d], 1)


        # UI Overlay (Not tinted)
        iso_surf.blit(font.render("3D ISOMETRIC VIEW", True, (180, 180, 180)), (10, 10))
        m_txt = f"Mode: {hover_mode}"
        if hover_mode == "ROAD" and road_id_list:
            m_txt += f" ({ROAD_VARIANTS[road_id_list[selected_road_idx]]})"
        iso_surf.blit(font.render(f"{m_txt} (Press R, S, W, I, X, C)", True, (255, 200, 100)), (10, 28))
        
        # Level 0 label
        lvl0_surf = huge_font.render("Level 0", True, (255, 255, 255))
        lvl0_surf.set_alpha(80)
        iso_surf.blit(lvl0_surf, (20, SCREEN_H - 60))

        # Time UI
        date_str = time_manager.get_formatted_date()
        time_str = time_manager.get_formatted_time()
        
        hud_str = f"{date_str} - {time_str}"
        time_surf = large_font.render(hud_str, True, (255, 255, 255))
        time_rect = time_surf.get_rect(topright=(ISO_W - 20, 20))
        iso_surf.blit(time_surf, time_rect)
        
        screen.blit(iso_surf, (0, 0))

        # Right Hand UI Panels
        if hover_mode == "SOLAR":
            solar_dashboard.draw(screen)
        elif hover_mode == "WIND":
            wind_dashboard.draw(screen)
        elif show_info_panel:
            g_info = {
                "Grid": f"{world.GRID_SIZE}x{world.GRID_SIZE}x{world.MAX_Z}",
                "Hover": f"({active_hx}, {active_hy})",
                "Date": date_str,
                "Time": time_str,
                "Irradiance": f"{solar_irradiance:.2f}"
            }
            controls = [
                "[I] - Info / Cell Selection",
                "[T] - Inline Selection",
                "[X] - Xline Selection",
                "[R] - Road (Cycle variants)",
                "[S] - Solar Mode",
                "[W] - Wind Mode",
                "[C] - Industrial Coal Plant",
                "[A] - Toggle AI Chat",
                "L Click - Select/Place",
                "MMB - Pan Camera",
                "Wheel - Zoom",
                "ESC - Back to Menu"
            ]
            info_panel.draw(screen, g_info, controls)

        if show_chat_panel and hover_mode != "SOLAR":
            chat_panel.draw(screen)

        # Panel 3: map/cross-section (Persistent for now)
        bot_surf = pygame.Surface((PANEL_W, PANEL_H))
        bot_surf.fill((30, 30, 30))
        pygame.draw.rect(bot_surf, (80, 120, 80), (0, 0, PANEL_W, PANEL_H), 2)

        if selected_slice is None:
            bot_surf.blit(font.render("TOP-DOWN MAP (Centered)", True, (180, 180, 180)), (10, 10))
            # td_tile already calculated at startup
            off_x = (PANEL_W - (world.GRID_SIZE * td_tile)) // 2
            off_y = (PANEL_H - (world.GRID_SIZE * td_tile)) // 2 + 10
            bot_surf.blit(large_font.render("N ↑", True, (255, 100, 100)), (10, 30))

            # Optimize Top-down map rendering with surface caching
            if hover_mode == "SOLAR":
                # Render Irradiance Map (Plasma)
                bot_surf.blit(font.render("SOLAR IRRADIANCE MAP (Plasma)", True, (255, 255, 0)), (10, 10))
                # Add a small randomness to make it "almost" constant but visual
                noise = (math.sin(pygame.time.get_ticks() / 1000) * 0.05)
                intensity = max(0, min(1.0, solar_irradiance + noise))
                
                # Simple Plasma approximation: 0.0 (Purple/Dark) -> 1.0 (Yellow/Bright)
                def get_plasma(v):
                    # v: 0.0 to 1.0
                    if v < 0.3: return (int(13+200*v), int(8+100*v), 135) # Purple to Pink-ish
                    elif v < 0.7: return (int(177+50*v), int(42+150*v), int(144-100*v)) # Pink to orange
                    else: return (255, 255, int(255*(1-v)*3)) # Yellow
                
                plasma_col = get_plasma(intensity)
                map_content_surf.fill(plasma_col)
                # Overdraw panels on the irradiance map
                for y in range(world.GRID_SIZE):
                    for x in range(world.GRID_SIZE):
                        if world_data[world.MAX_Z - 1][y][x] == 4:
                            # 90-degree rotated map alignment
                            m_x_pos = y * td_tile
                            m_y_pos = (world.GRID_SIZE - 1 - x) * td_tile
                            pygame.draw.rect(map_content_surf, (255, 255, 255), (m_x_pos, m_y_pos, td_tile, td_tile), 2)
                bot_surf.blit(map_content_surf, (off_x, off_y))
            elif hover_mode == "WIND":
                bot_surf.blit(font.render("WIND VELOCITY MAP (Intensity + Vectors)", True, (0, 255, 255)), (10, 10))
                # Intensity purely based on global wind speed for now
                norm_speed = min(1.0, wind_speed / 20.0)
                int_val = int(40 + 120 * norm_speed)
                map_content_surf.fill((20, int_val, int_val // 2)) # Bluish-green intensity
                
                # Draw vectors (arrows) per grid cell
                for y in range(world.GRID_SIZE):
                    for x in range(world.GRID_SIZE):
                        # 90-degree rotated map coordinates
                        mc_x = y * td_tile + td_tile // 2
                        mc_y = (world.GRID_SIZE - 1 - x) * td_tile + td_tile // 2
                        
                        # Arrow pointing to wind_dir
                        # Adjust for 90-deg rotation: Map X is Iso Y, Map Y is Iso -X
                        rad = math.radians(wind_dir - 180) # Angle tweak for rotated map view
                        lv = 10 * norm_speed + 2
                        ex = mc_x + math.cos(rad) * lv
                        ey = mc_y + math.sin(rad) * lv
                        pygame.draw.line(map_content_surf, (200, 255, 255), (mc_x, mc_y), (ex, ey), 1)
                        pygame.draw.circle(map_content_surf, (200, 255, 255), (int(ex), int(ey)), 2)
                
                bot_surf.blit(map_content_surf, (off_x, off_y))
            elif not cached_map_valid:
                map_content_surf.fill((100, 150, 100)) # Base grass
                for y in range(world.GRID_SIZE):
                    for x in range(world.GRID_SIZE):
                        bid_top = world_data[world.MAX_Z - 1][y][x]
                        if bid_top == 1: continue # Grass is base
                        color = (120, 120, 120) if (bid_top == 3 or bid_top >= 100) else (255, 255, 0) if bid_top == 4 else (0, 255, 255) if bid_top == 5 else (100, 150, 100)
                        
                        # 90-degree rotated map alignment: iso_y -> map_x, iso_x -> map_y (inverted)
                        m_x_pos = y * td_tile
                        m_y_pos = (world.GRID_SIZE - 1 - x) * td_tile
                        pygame.draw.rect(map_content_surf, color, (m_x_pos, m_y_pos, td_tile, td_tile))
                cached_map_valid = True
                bot_surf.blit(map_content_surf, (off_x, off_y))
            else:
                bot_surf.blit(map_content_surf, (off_x, off_y))

            if is_hovering_map:
                highlight_color = (255, 50, 50)
                if hover_mode == "SOLAR": highlight_color = (255, 255, 0)
                elif hover_mode == "WIND": highlight_color = (0, 255, 255)
                elif hover_mode == "ROAD": highlight_color = (120, 120, 120)
                elif hover_mode == "COAL": highlight_color = (0, 0, 0)
                
                # Draw hover on top of cached map
                if gx_h < world.GRID_SIZE and gy_h < world.GRID_SIZE:
                    if hover_mode in ("INLINE", "XLINE"):
                        # Semi-transparent slice highlight
                        slice_surf = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
                        h_col = (255, 50, 50, 150)
                        if hover_mode == "INLINE":
                            # Inline is constant Y -> Horizontal on rotated map
                            m_y_val = (world.GRID_SIZE - 1 - gx_h) * td_tile + off_y # Since iso_x maps to map_y
                            pygame.draw.rect(slice_surf, h_col, (off_x, m_y_val, world.GRID_SIZE * td_tile, td_tile))
                        else:
                            # Xline is constant X -> Vertical on rotated map
                            m_x_val = gy_h * td_tile + off_x # Since iso_y maps to map_x
                            pygame.draw.rect(slice_surf, h_col, (m_x_val, off_y, td_tile, world.GRID_SIZE * td_tile))
                        bot_surf.blit(slice_surf, (0, 0))
                        
                        # Draw active cell darker (90 deg rotated)
                        h_x = gy_h * td_tile + off_x
                        h_y = (world.GRID_SIZE - 1 - gx_h) * td_tile + off_y
                        pygame.draw.rect(bot_surf, (150, 0, 0), (h_x, h_y, td_tile, td_tile))
                    else:
                        # Single cell highlight (90 deg rotated)
                        h_x = gy_h * td_tile + off_x
                        h_y = (world.GRID_SIZE - 1 - gx_h) * td_tile + off_y
                        pygame.draw.rect(bot_surf, highlight_color, (h_x, h_y, td_tile, td_tile))

        else:
            title = f"CROSS-SECTION: {selected_slice['type']} {selected_slice['index']}"
            bot_surf.blit(font.render(title, True, (255, 200, 100)), (10, 10))
            cs_w = max(1, PANEL_W // world.GRID_SIZE)
            cs_h = max(1, (PANEL_H - 60) // world.MAX_Z)
            cs_off_x = (PANEL_W - (world.GRID_SIZE * cs_w)) // 2
            cs_off_y = (PANEL_H - (world.MAX_Z * cs_h)) // 2 + 20

            for z in range(world.MAX_Z):
                for i in range(world.GRID_SIZE):
                    x = i if selected_slice["type"] == "INLINE" else selected_slice["index"]
                    y = selected_slice["index"] if selected_slice["type"] == "INLINE" else i
                    block_id = world_data[z][y][x]
                    color = (150, 100, 50) # Brown for all layers in cross-section
                    if block_id == 3: color = (120, 120, 120) # Grey for road
                    elif block_id == 4: color = (255, 255, 0) # Yellow for solar
                    elif block_id == 5: color = (0, 255, 255) # Cyan for wind
                    screen_z = (world.MAX_Z - 1) - z
                    rect = (i * cs_w + cs_off_x, screen_z * cs_h + cs_off_y, cs_w, cs_h)
                    pygame.draw.rect(bot_surf, color, rect)


        screen.blit(bot_surf, (ISO_W, PANEL_H))
        pygame.draw.line(screen, (60, 60, 60), (ISO_W, 0), (ISO_W, SCREEN_H), 2)
        pygame.draw.line(screen, (60, 60, 60), (ISO_W, PANEL_H), (SCREEN_W, PANEL_H), 2)

        # Notifications (Upper Left, but centered-ish)
        if pygame.time.get_ticks() < notification_timer:
            notif_surf = large_font.render(notification_text, True, notification_color)
            notif_rect = notif_surf.get_rect(center=(ISO_W // 2, 50))
            # Background logic for better visibility
            bg_rect = notif_rect.inflate(40, 20)
            pygame.draw.rect(screen, (30, 30, 30, 200), bg_rect, border_radius=10)
            pygame.draw.rect(screen, notification_color, bg_rect, 2, border_radius=10)
            screen.blit(notif_surf, notif_rect)

        # Balance Overlay (Bottom Right of Isometric View)
        balance_str = f"BALANCE: ${balance:,}"
        bal_surf = large_font.render(balance_str, True, (0, 255, 100))
        bal_rect = bal_surf.get_rect(bottomright=(ISO_W - 20, SCREEN_H - 20))
        # Semi-transparent backing
        bg_bal = bal_rect.inflate(20, 10)
        pygame.draw.rect(screen, (20, 20, 20, 180), bg_bal, border_radius=5)
        screen.blit(bal_surf, bal_rect)

        pygame.display.flip()
        clock.tick(60)

    return "MENU"
