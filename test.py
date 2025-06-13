import pygame
import sys
import math
import numpy as np

# ===== PARAMETERS =====
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BACKGROUND_COLOR = (0, 0, 0)  # Black

# Spot settings
SPOT_COLOR = (0, 255, 0)  # Green
INITIAL_BRIGHTNESS = 1.0
SPOTS_PER_FRAME = 5  # Number of spots to add between positions

# Core dot settings
CORE_RADIUS = 2
FPS = 165

# Slider settings
SLIDER_WIDTH = 200
SLIDER_HEIGHT = 20
SLIDER_SPACING = 40
SLIDER_X = 50
SLIDER_Y = 50
SLIDER_HANDLE_WIDTH = 15

# Size slider
SIZE_MIN = 2
SIZE_MAX = 20
INITIAL_SIZE = 10

# Decay slider
DECAY_MIN = 0.8
DECAY_MAX = 0.99
INITIAL_DECAY = 0.9

# Signal generation
SIGNAL_FREQ_X = 0.5  # Hz
SIGNAL_FREQ_Y = 1.0   # Hz
SIGNAL_AMP_X = 0.4    # Screen width multiplier
SIGNAL_AMP_Y = 0.4    # Screen height multiplier
# ======================

class Spot:
    def __init__(self, pos, radius, decay_rate, brightness=INITIAL_BRIGHTNESS):
        self.pos = pos
        self.initial_radius = radius
        self.brightness = brightness
        self.decay_rate = decay_rate
        self.age = 0

    def update(self):
        self.brightness *= self.decay_rate
        self.age += 1

    @property
    def radius(self):
        return int(self.initial_radius * math.sqrt(self.brightness))

    def draw(self, surface):
        if self.brightness <= 0.01:
            return
        
        current_radius = self.radius
        color = (*SPOT_COLOR, int(255 * self.brightness))
        glow_surf = pygame.Surface((current_radius*2, current_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, color, (current_radius, current_radius), current_radius)
        surface.blit(glow_surf, (self.pos[0]-current_radius, self.pos[1]-current_radius))

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.handle_rect = pygame.Rect(x, y - height//2, SLIDER_HANDLE_WIDTH, height*2)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        self.update_handle_pos()

    def update_handle_pos(self):
        relative_val = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.x = self.rect.x + int(relative_val * (self.rect.width - SLIDER_HANDLE_WIDTH))

    def get_value(self, pos_x):
        relative_pos = (pos_x - self.rect.x) / self.rect.width
        return max(self.min_val, min(self.max_val, 
                self.min_val + relative_pos * (self.max_val - self.min_val)))

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.handle_rect, border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255), self.handle_rect, 2, border_radius=3)
        
        font = pygame.font.SysFont('Arial', 16)
        label_text = font.render(f"{self.label}:", True, (255, 255, 255))
        value_text = font.render(f"{self.value:.2f}" if isinstance(self.value, float) else f"{int(self.value)}", 
                               True, (255, 255, 255))
        
        surface.blit(label_text, (self.rect.x, self.rect.y - 25))
        surface.blit(value_text, (self.rect.x + self.rect.width + 10, self.rect.y))

class SignalGenerator:
    def __init__(self):
        self.time = 0
        self.dt = 1/FPS
        
    def get_xy_position(self):
        self.time += self.dt
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # Generate X and Y signals (sine waves by default)
        x = center_x + int(SCREEN_WIDTH * SIGNAL_AMP_X * math.sin(2 * math.pi * SIGNAL_FREQ_X * self.time))
        y = center_y + int(SCREEN_HEIGHT * SIGNAL_AMP_Y * math.cos(2 * math.pi * SIGNAL_FREQ_Y * self.time))
        
        # Constrain to screen
        x = max(0, min(SCREEN_WIDTH, x))
        y = max(0, min(SCREEN_HEIGHT, y))
        
        return (x, y)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Oscilloscope with X/Y Channels")
    clock = pygame.time.Clock()

    spots = []
    running = True
    
    # Initialize sliders
    size_slider = Slider(SLIDER_X, SLIDER_Y, 
                        SLIDER_WIDTH, SLIDER_HEIGHT,
                        SIZE_MIN, SIZE_MAX, INITIAL_SIZE, "Size")
    
    decay_slider = Slider(SLIDER_X, SLIDER_Y + SLIDER_SPACING,
                         SLIDER_WIDTH, SLIDER_HEIGHT,
                         DECAY_MIN, DECAY_MAX, INITIAL_DECAY, "Decay")

    # Signal generator
    signal_gen = SignalGenerator()
    
    # Mode switching
    mouse_mode = True
    active_slider = None

    while running:
        screen.fill(BACKGROUND_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if size_slider.handle_rect.collidepoint(event.pos):
                    active_slider = size_slider
                elif decay_slider.handle_rect.collidepoint(event.pos):
                    active_slider = decay_slider
                else:
                    # Click anywhere else to toggle mouse/signal mode
                    mouse_mode = not mouse_mode
            elif event.type == pygame.MOUSEBUTTONUP:
                active_slider = None
            elif event.type == pygame.MOUSEMOTION and active_slider:
                mouse_x = max(active_slider.rect.left, 
                             min(event.pos[0], active_slider.rect.right - SLIDER_HANDLE_WIDTH))
                active_slider.value = active_slider.get_value(mouse_x)
                active_slider.update_handle_pos()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    mouse_mode = not mouse_mode

        # Get current position based on mode
        if mouse_mode:
            current_pos = pygame.mouse.get_pos()
        else:
            current_pos = signal_gen.get_xy_position()

        # Add new spots
        if len(spots) == 0 or current_pos != spots[-1].pos:
            spots.append(Spot(current_pos, size_slider.value, decay_slider.value))

        # Update and draw all spots
        for spot in spots[:]:
            spot.update()
            spot.draw(screen)
            if spot.brightness <= 0.01:
                spots.remove(spot)

        # Draw core dot
        pygame.draw.circle(screen, SPOT_COLOR, current_pos, CORE_RADIUS)
        
        # Draw sliders
        size_slider.draw(screen)
        decay_slider.draw(screen)
        
        # Draw mode indicator
        font = pygame.font.SysFont('Arial', 24)
        mode_text = font.render(f"Mode: {'Mouse' if mouse_mode else 'X/Y Signals'}", True, (255, 255, 255))
        screen.blit(mode_text, (SCREEN_WIDTH - 200, 20))
        
        # Draw signal info
        if not mouse_mode:
            info_text = font.render(f"X: {SIGNAL_FREQ_X}Hz, Y: {SIGNAL_FREQ_Y}Hz", True, (255, 255, 255))
            screen.blit(info_text, (SCREEN_WIDTH - 200, 50))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()