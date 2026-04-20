import sys
import pygame
import save_manager
import menu
import level0.level0_main as level0

def main():
    pygame.init()

    # Layout
    DISPLAY_INFO = pygame.display.Info()
    SCREEN_W = DISPLAY_INFO.current_w
    SCREEN_H = DISPLAY_INFO.current_h

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    pygame.display.set_caption("EnergyWorld — 3D Isometric Builder")
    clock = pygame.time.Clock()

    # Shared Fonts
    fonts = (
        pygame.font.SysFont("monospace", 13),
        pygame.font.SysFont("monospace", 20, bold=True),
        pygame.font.SysFont("monospace", 40, bold=True)
    )

    # State
    game_state = "MENU"
    
    # Initialize level buttons
    level_buttons = []
    for i in range(10):
        col = i % 2
        row = i // 2
        bx = SCREEN_W // 2 - 210 + col * 220
        by = SCREEN_H // 2 - 180 + row * 80
        # level_buttons.append(menu.MenuButton(f"LEVEL {i}", bx, by, 200, 60, i, fonts[1]))
        # Wait, the user said Level 0, Level 1 ...
        # I'll create them all, but only Level 0 works for now.
        level_buttons.append(menu.MenuButton(f"LEVEL {i}", bx, by, 200, 60, i, fonts[1]))

    # Session Recovery Button
    continue_btn = None
    if save_manager.has_save():
        continue_btn = menu.MenuButton("CONTINUE SESSION", SCREEN_W // 2 - 150, SCREEN_H // 2 - 360, 300, 60, -1, fonts[1])
        continue_btn.bg_color = (100, 80, 40) # Distinct color for continue

    running = True
    while running:
        if game_state == "MENU":
            # Handle events in the launcher loop to detect selection
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if continue_btn and continue_btn.hovered:
                        game_state = "CONTINUE"
                    for btn in level_buttons:
                        if btn.hovered:
                            if btn.level_id == 0:
                                game_state = "LEVEL0"
                            else:
                                print(f"Level {btn.level_id} not implemented yet.")

            # Render menu
            menu.show_menu(screen, fonts, level_buttons)
            if continue_btn:
                continue_btn.update(pygame.mouse.get_pos())
                continue_btn.draw(screen)
            pygame.display.flip()
            clock.tick(60)

        elif game_state == "LEVEL0":
            # Pass control to level0_main
            result = level0.run(screen, clock, fonts)
            if result == "QUIT":
                running = False
            elif result == "MENU":
                game_state = "MENU"
        
        elif game_state == "CONTINUE":
            sd = save_manager.load_session()
            result = level0.run(screen, clock, fonts, save_data=sd)
            if result == "QUIT":
                running = False
            elif result == "MENU":
                game_state = "MENU"

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
