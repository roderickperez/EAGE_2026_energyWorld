import pygame

class InfoPanel:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.bg_color = (40, 40, 50, 230) # Semi-transparent dark
        self.header_color = (255, 200, 100)
        self.text_color = (200, 200, 220)
        self.energy_history = []
        self.max_hist = 200
        self.demands = [800, 1500, 2500]

    def update_demands(self, res, bus, ind):
        self.demands = [res, bus, ind]

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

        # Energy Production Plot (Stacked Area)
        plot_rect = pygame.Rect(self.rect.x + 10, self.rect.bottom - 110, self.rect.w - 20, 100)
        pygame.draw.rect(surface, (20, 20, 30), plot_rect)
        pygame.draw.rect(surface, (100, 100, 100), plot_rect, 1)
        surface.blit(self.font.render("Production Stack & Demand", True, (255, 255, 100)), (plot_rect.x + 5, plot_rect.y + 2))
        
        if self.energy_history:
            # Assume each entry is (solar, wind, coal)
            # Find max total for scaling
            max_val = 0
            for entry in self.energy_history:
                if isinstance(entry, (tuple, list)):
                    max_val = max(max_val, sum(entry))
                else:
                    max_val = max(max_val, entry)
            max_val = max(max_val, 1000) # Minimum scale for visibility
            
            # Draw Demand Lines (Dashed)
            demands_info = [
                (self.demands[0], (255, 50, 50), "RESIDENTIAL MIN NEED"),
                (self.demands[1], (255, 150, 0), "BUSINESS REQUIREMENTS"),
                (self.demands[2], (200, 100, 255), "INDUSTRIAL MIN REQUIREMENT")
            ]
            
            for threshold, color, label in demands_info:
                demand_y = plot_rect.bottom - 5 - (threshold / max_val * (plot_rect.h - 20))
                if plot_rect.y < demand_y < plot_rect.bottom:
                    for dx in range(plot_rect.x, plot_rect.right, 10):
                        pygame.draw.line(surface, color, (dx, int(demand_y)), (dx + 5, int(demand_y)), 1)
                    surface.blit(self.font.render(label, True, color), (plot_rect.x + 5, int(demand_y) - 15))

            # Stacked Area logic
            num_points = len(self.energy_history)
            if num_points > 1:
                # Layers: Coal (Base), Wind, Solar (Top)
                layers = [
                    ((30, 30, 30, 150), 2),   # Coal: Black/Grey
                    ((0, 255, 255, 180), 1),  # Wind: Cyan
                    ((255, 255, 0, 200), 0)    # Solar: Yellow
                ]
                
                for color_alpha, idx in layers:
                    poly_points = []
                    # Add bottom points for the area fill
                    for i, entry in enumerate(self.energy_history):
                        px = plot_rect.x + (i / self.max_hist) * plot_rect.w
                        
                        # Sum values up to this layer
                        if isinstance(entry, (tuple, list)):
                            val_sum = sum(entry[idx:])
                        else:
                            # Fallback if history is old single-value format
                            val_sum = entry if idx == 2 else 0
                        
                        py = plot_rect.bottom - 5 - (val_sum / max_val * (plot_rect.h - 20))
                        poly_points.append((int(px), int(py)))
                    
                    # Add bottom anchor points to close the polygon
                    last_px = plot_rect.x + ((num_points - 1) / self.max_hist) * plot_rect.w
                    first_px = plot_rect.x
                    poly_points.append((int(last_px), plot_rect.bottom - 5))
                    poly_points.append((int(first_px), plot_rect.bottom - 5))
                    
                    fill_surf = pygame.Surface((plot_rect.w, plot_rect.h), pygame.SRCALPHA)
                    # Translate poly_points to surf local coords
                    local_poly = [(p[0] - plot_rect.x, p[1] - plot_rect.y) for p in poly_points]
                    pygame.draw.polygon(fill_surf, color_alpha, local_poly)
                    surface.blit(fill_surf, plot_rect.topleft)

            # Show total current value
            cur_entry = self.energy_history[-1]
            cur_total = sum(cur_entry) if isinstance(cur_entry, (tuple, list)) else cur_entry
            # Green if meeting residential needs, otherwise Red
            color = (0, 255, 200) if cur_total >= self.demands[0] else (255, 50, 50)
            surface.blit(self.font.render(f"Total Prod: {cur_total:.1f} kW", True, color), (plot_rect.right - 140, plot_rect.y + 2))

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

class WindDashboard:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.production_history = []
        self.turbine_objs = [] # (gx, gy, production_val, wind_speed)
        self.max_hist = 150
        self.bg_color = (15, 25, 20, 240) # Slightly more green-tinted background

    def update(self, total_prod, turbines_data):
        self.production_history.append(total_prod)
        if len(self.production_history) > self.max_hist:
            self.production_history.pop(0)
        self.turbine_objs = turbines_data # List of (gx, gy, prod, speed)

    def draw(self, surface):
        # Background
        bg = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg.fill(self.bg_color)
        surface.blit(bg, self.rect.topleft)
        pygame.draw.rect(surface, (0, 220, 150), self.rect, 2)

        # Labels
        x, y = self.rect.x + 10, self.rect.y + 10
        surface.blit(self.font.render("WIND ENERGY DASHBOARD", True, (150, 255, 200)), (x, y))

        # Plot 1: Historic Wind Energy Production
        p1_rect = pygame.Rect(x, y + 30, self.rect.w - 20, (self.rect.h - 60) // 2 - 10)
        pygame.draw.rect(surface, (20, 30, 25), p1_rect)
        pygame.draw.rect(surface, (80, 120, 100), p1_rect, 1)
        surface.blit(self.font.render("Historic Wind Energy Production (kW)", True, (200, 220, 210)), (p1_rect.x + 5, p1_rect.y + 5))
        
        if len(self.production_history) > 1:
            points = []
            max_p = max(self.production_history) if max(self.production_history) > 0 else 1
            for i, val in enumerate(self.production_history):
                px = p1_rect.x + (i / self.max_hist) * p1_rect.w
                py = p1_rect.bottom - 5 - (val / max_p * (p1_rect.h - 20))
                points.append((int(px), int(py)))
            pygame.draw.lines(surface, (0, 255, 200), False, points, 2)

        # Section 2: Production per Turbine
        p2_rect = pygame.Rect(x, p1_rect.bottom + 20, self.rect.w - 20, p1_rect.h)
        pygame.draw.rect(surface, (20, 30, 25), p2_rect)
        pygame.draw.rect(surface, (80, 120, 100), p2_rect, 1)
        surface.blit(self.font.render("Turbine Real-time Production", True, (200, 220, 210)), (p2_rect.x + 5, p2_rect.y + 5))

        if self.turbine_objs:
            inner_y = p2_rect.y + 30
            # Display first 8 turbines to avoid overflow, scroll logic could be added later
            for gx, gy, prod, speed in self.turbine_objs[:8]:
                txt = f"Turbine @ [{gx:2d}, {gy:2d}]: {prod:>6.1f} kW (v={speed:.1f} m/s)"
                surface.blit(self.font.render(txt, True, (150, 255, 220)), (p2_rect.x + 10, inner_y))
                inner_y += 18
            
            if len(self.turbine_objs) > 8:
                surface.blit(self.font.render(f"... and {len(self.turbine_objs)-8} more", True, (100, 150, 130)), (p2_rect.x + 10, inner_y))

class CoalDashboard:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.production_history = []
        self.contamination_history = []
        self.max_hist = 150
        self.bg_color = (25, 20, 20, 240) # Slightly more red/ash-tinted background

    def update(self, total_prod, total_contam):
        self.production_history.append(total_prod)
        self.contamination_history.append(total_contam)
        if len(self.production_history) > self.max_hist:
            self.production_history.pop(0)
        if len(self.contamination_history) > self.max_hist:
            self.contamination_history.pop(0)

    def draw(self, surface):
        # Background
        bg = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg.fill(self.bg_color)
        surface.blit(bg, self.rect.topleft)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2)

        # Labels
        x, y = self.rect.x + 10, self.rect.y + 10
        surface.blit(self.font.render("COAL ENERGY & CONTAMINATION DASHBOARD", True, (255, 100, 100)), (x, y))

        # Plot 1: Total Coal Energy Production (Constant line per plant)
        p1_rect = pygame.Rect(x, y + 30, self.rect.w - 20, (self.rect.h - 60) // 2 - 10)
        pygame.draw.rect(surface, (30, 20, 20), p1_rect)
        pygame.draw.rect(surface, (120, 80, 80), p1_rect, 1)
        surface.blit(self.font.render("Historic Coal Energy Production (kW)", True, (220, 200, 200)), (p1_rect.x + 5, p1_rect.y + 5))
        
        if len(self.production_history) > 1:
            points = []
            max_p = max(self.production_history) if max(self.production_history) > 0 else 1
            for i, val in enumerate(self.production_history):
                px = p1_rect.x + (i / self.max_hist) * p1_rect.w
                py = p1_rect.bottom - 5 - (val / max_p * (p1_rect.h - 20))
                points.append((int(px), int(py)))
            pygame.draw.lines(surface, (255, 100, 100), False, points, 2)

        # Plot 2: Contamination Levels
        p2_rect = pygame.Rect(x, p1_rect.bottom + 20, self.rect.w - 20, p1_rect.h)
        pygame.draw.rect(surface, (30, 20, 20), p2_rect)
        pygame.draw.rect(surface, (120, 80, 80), p2_rect, 1)
        surface.blit(self.font.render("Total Regional Contamination (Index)", True, (220, 200, 200)), (p2_rect.x + 5, p2_rect.y + 5))

        if len(self.contamination_history) > 1:
            points = []
            max_c = max(self.contamination_history) if max(self.contamination_history) > 0 else 1
            for i, val in enumerate(self.contamination_history):
                px = p2_rect.x + (i / self.max_hist) * p2_rect.w
                py = p2_rect.bottom - 5 - (val / max_c * (p2_rect.h - 20))
                points.append((int(px), int(py)))
            pygame.draw.lines(surface, (180, 180, 180), False, points, 2) # Grey/Ash smoke line
