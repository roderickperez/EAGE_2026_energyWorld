import pygame

class InfoPanel:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.bg_color = (40, 40, 50, 230) # Semi-transparent dark
        self.header_color = (255, 200, 100)
        self.text_color = (200, 200, 200)

    def draw(self, surface, grid_info, controls):
        # Draw semi-transparent background
        bg_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg_surf.fill(self.bg_color)
        surface.blit(bg_surf, self.rect.topleft)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 2)

        x, y = self.rect.x + 10, self.rect.y + 10
        surface.blit(self.font.render("INFO PANEL", True, self.header_color), (x, y))
        
        y += 30
        for key, val in grid_info.items():
            surface.blit(self.font.render(f"{key}: {val}", True, self.text_color), (x, y))
            y += 20
        
        y += 20
        surface.blit(self.font.render("Controls:", True, self.header_color), (x, y))
        y += 25
        for ctrl in controls:
            surface.blit(self.font.render(ctrl, True, self.text_color), (x, y))
            y += 18

class ChatPanel:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.bg_color = (30, 35, 45, 245)
        self.border_color = (0, 180, 255)
        self.messages = [("AI", "Hello Rodperez! How can I help you manage EnergyWorld today?")]
        self.input_text = ""
        self.active = False # For text input

    def add_message(self, author, text):
        self.messages.append((author, text))
        if len(self.messages) > 15:
            self.messages.pop(0)

    def draw(self, surface):
        # Background
        bg_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg_surf.fill(self.bg_color)
        surface.blit(bg_surf, self.rect.topleft)
        pygame.draw.rect(surface, self.border_color, self.rect, 3)

        x, y = self.rect.x + 15, self.rect.y + 15
        surface.blit(self.font.render("AI ENERGY ASSISTANT", True, (0, 255, 255)), (x, y))
        
        y += 40
        # Messages area
        msg_area = pygame.Rect(x, y, self.rect.w - 30, self.rect.h - 100)
        pygame.draw.rect(surface, (20, 20, 30), msg_area)
        
        inner_y = y + 5
        for author, msg in self.messages[-10:]:
            color = (0, 200, 255) if author == "AI" else (200, 255, 200)
            prefix = f"[{author}]: "
            surface.blit(self.font.render(prefix + msg, True, color), (x + 5, inner_y))
            inner_y += 25
            
        # Input area
        y_in = self.rect.bottom - 40
        input_rect = pygame.Rect(x, y_in, self.rect.w - 30, 30)
        pygame.draw.rect(surface, (50, 50, 70), input_rect)
        if self.active:
            pygame.draw.rect(surface, (255, 255, 255), input_rect, 1)
        
        txt = self.input_text + ("_" if (pygame.time.get_ticks() // 500) % 2 == 0 else "")
        surface.blit(self.font.render(txt, True, (255, 255, 255)), (x + 5, y_in + 5))
