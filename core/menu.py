import pygame

class MenuButton:
    def __init__(self, text, x, y, w, h, level_id, font):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.level_id = level_id
        self.font = font
        self.hovered = False

    def draw(self, surf):
        # Premium look: darker base, lighter highlight on hover
        base_color = (40, 45, 60)
        hover_color = (70, 80, 110)
        color = hover_color if self.hovered else base_color
        
        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        pygame.draw.rect(surf, (100, 120, 180), self.rect, 2, border_radius=12)
        
        # Subtle shadow
        shadow_rect = self.rect.move(3, 3)
        pygame.draw.rect(surf, (10, 10, 15), shadow_rect, border_radius=12, width=1)

        txt_color = (255, 255, 255) if self.hovered else (200, 200, 220)
        txt_surf = self.font.render(self.text, True, txt_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surf.blit(txt_surf, txt_rect)

    def update(self, mpos):
        self.hovered = self.rect.collidepoint(mpos)


def show_menu(screen, fonts, level_buttons):
    """Render the menu and return the selected level_id or None."""
    font, large_font, huge_font = fonts
    mx, my = pygame.mouse.get_pos()
    
    screen.fill((20, 22, 30))
    
    # Title
    title_surf = huge_font.render("ENERGY WORLD", True, (255, 255, 255))
    sw, sh = screen.get_size()
    title_rect = title_surf.get_rect(center=(sw // 2, sh // 2 - 280))
    screen.blit(title_surf, title_rect)
    
    subtitle_surf = font.render("Select a Exploration Level", True, (150, 160, 180))
    subtitle_rect = subtitle_surf.get_rect(center=(sw // 2, sh // 2 - 240))
    screen.blit(subtitle_surf, subtitle_rect)

    selected_level = None
    for btn in level_buttons:
        btn.update((mx, my))
        btn.draw(screen)
        
    return selected_level
