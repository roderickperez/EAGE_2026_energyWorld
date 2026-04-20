import sys
import pygame
import menu
import level0.level0_main as level0
import save_system

def show_continue_prompt(screen, fonts):
    font, large_font, _ = fonts
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    msg = "Saved session found. Continue? [C] Continue | [N] New Game"
    txt = large_font.render(msg, True, (255, 255, 255))
    rect = txt.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
    screen.blit(txt, rect)
    pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    return save_system.load_game()
                if event.key == pygame.K_n:
                    return None

def main():
    pygame.init()
    # ... (rest of setup)

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
                    for btn in level_buttons:
                        if btn.hovered:
                            if btn.level_id == 0:
                                game_state = "LEVEL0"
                            else:
                                print(f"Level {btn.level_id} not implemented yet.")

            # Render menu
            menu.show_menu(screen, fonts, level_buttons)
            pygame.display.flip()
            clock.tick(60)

        elif game_state == "LEVEL0":
            # Pass control to level0_main
            initial_state = None
            if save_system.save_exists():
                initial_state = show_continue_prompt(screen, fonts)
            
            result = level0.run(screen, clock, fonts, initial_state)
            if result == "QUIT":
                running = False
            elif result == "MENU":
                game_state = "MENU"

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
