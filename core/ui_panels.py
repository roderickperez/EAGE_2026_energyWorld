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
        

class SolarDashboard:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.tsi_history = []
        self.panel_objs = [] # (gx, gy, production_val)
        self.max_hist = 150
        self.bg_color = (15, 20, 25, 240)

    def update(self, tsi, panels_data):
        self.tsi_history.append(tsi)
        if len(self.tsi_history) > self.max_hist:
            self.tsi_history.pop(0)
        self.panel_objs = panels_data # List of (gx, gy, prod)

    def draw(self, surface):
        # Background
        bg = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg.fill(self.bg_color)
        surface.blit(bg, self.rect.topleft)
        pygame.draw.rect(surface, (0, 200, 255), self.rect, 2)

        # Labels
        x, y = self.rect.x + 10, self.rect.y + 10
        surface.blit(self.font.render("SOLAR ENERGY DASHBOARD", True, (255, 255, 100)), (x, y))

        # Plot 1: Total Solar Irradiance
        p1_rect = pygame.Rect(x, y + 30, self.rect.w - 20, (self.rect.h - 60) // 2 - 10)
        pygame.draw.rect(surface, (30, 30, 40), p1_rect)
        pygame.draw.rect(surface, (100, 100, 100), p1_rect, 1)
        surface.blit(self.font.render("Total Solar Irradiance (TSI)", True, (200, 200, 200)), (p1_rect.x + 5, p1_rect.y + 5))
        
        if len(self.tsi_history) > 1:
            points = []
            for i, val in enumerate(self.tsi_history):
                px = p1_rect.x + (i / self.max_hist) * p1_rect.w
                py = p1_rect.bottom - 5 - (val * (p1_rect.h - 20))
                points.append((int(px), int(py)))
            pygame.draw.lines(surface, (255, 255, 0), False, points, 2)

        # Plot 2: Production per Panel
        p2_rect = pygame.Rect(x, p1_rect.bottom + 20, self.rect.w - 20, p1_rect.h)
        pygame.draw.rect(surface, (30, 30, 40), p2_rect)
        pygame.draw.rect(surface, (100, 100, 100), p2_rect, 1)
        surface.blit(self.font.render("Panel Production & Irradiance", True, (200, 200, 200)), (p2_rect.x + 5, p2_rect.y + 5))

        if self.panel_objs:
            # Bar chart where each bar is a panel
            bar_w = max(2, (p2_rect.w - 20) // len(self.panel_objs))
            for i, (gx, gy, prod) in enumerate(self.panel_objs):
                bx = p2_rect.x + 10 + i * bar_w
                # Bar for production
                bh = min(1.0, prod / 100.0) * (p2_rect.h - 30) 
                brew = pygame.Rect(bx, p2_rect.bottom - 5 - bh, bar_w - 1, bh)
                pygame.draw.rect(surface, (0, 255, 150), brew)
                
                if i % max(1, len(self.panel_objs)//5) == 0:
                    lbl = self.font.render(f"{gx},{gy}", True, (150, 150, 150))
                    # Scale down label if too many panels
                    surface.blit(pygame.transform.rotate(lbl, 90), (bx, p2_rect.bottom - 30))
