import pygame
import sys
import math
import numpy as np
from enum import Enum

# ===== PARAMETERS =====
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SLIDER_PANEL_WIDTH = 300
BACKGROUND_COLOR = (0, 0, 0)  # Black
FPS = 165

# Spot settings
SPOT_COLOR = (0, 255, 0)  # Green
INITIAL_BRIGHTNESS = 1.0
SPOTS_PER_FRAME = 10

# Core dot settings
CORE_RADIUS = 2

# Slider settings
SLIDER_WIDTH = 150
SLIDER_HEIGHT = 15
SLIDER_SPACING = 25
SLIDER_HANDLE_WIDTH = 10

# Dot controls
SIZE_MIN = 2
SIZE_MAX = 20
DECAY_MIN = 0.8
DECAY_MAX = 0.99

# Wave type controls
WAVE_TYPE_MIN = 0
WAVE_TYPE_MAX = 4
FREQ_MIN = 0.1
FREQ_MAX = 5.0
AMP_MIN = 0.1
AMP_MAX = 0.5
OFFSET_MIN = -0.5
OFFSET_MAX = 0.5
POLL_RATE_MIN = 1
POLL_RATE_MAX = 1000

# Default values
DEFAULT_SIZE = 20
DEFAULT_DECAY = 0.95
DEFAULT_WAVE_TYPE = 0
DEFAULT_FREQ = 1.0
DEFAULT_AMP = 0.3
DEFAULT_OFFSET = 0.0
DEFAULT_POLL_RATE = 60


PRESET_VALUES = {
    "X Wave": DEFAULT_WAVE_TYPE,
    "X Freq": 1.0,
    "X Amp": 0.3,
    "X Offset": 0.0,
    "X Phase": 0.0,
    "Y Wave": DEFAULT_WAVE_TYPE,
    "Y Freq": 1.0,
    "Y Amp": 0.3,
    "Y Offset": 0.0,
    "Y Phase": 0.0,
    "Dot Size": DEFAULT_SIZE,
    "Decay Rate": DEFAULT_DECAY,
    "Polling Rate": DEFAULT_POLL_RATE
}

class WaveType(Enum):
    SINE = 0
    SQUARE = 1
    SAWTOOTH = 2
    TRIANGLE = 3

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
        color = (0, 255, 0, int(255 * self.brightness))
        glow_surf = pygame.Surface((current_radius*2, current_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, color, (current_radius, current_radius), current_radius)
        surface.blit(glow_surf, (self.pos[0]-current_radius, self.pos[1]-current_radius))

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label, is_int=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.handle_rect = pygame.Rect(x, y - height//2, SLIDER_HANDLE_WIDTH, height*2)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.is_int = is_int
        self.dragging = False
        self.update_handle_pos()

    def update_handle_pos(self):
        relative_val = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.x = self.rect.x + int(relative_val * (self.rect.width - SLIDER_HANDLE_WIDTH))

    def get_value(self, pos_x):
        relative_pos = (pos_x - self.rect.x) / self.rect.width
        val = self.min_val + relative_pos * (self.max_val - self.min_val)
        return int(val) if self.is_int else val

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.handle_rect, border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255), self.handle_rect, 2, border_radius=3)
        font = pygame.font.SysFont('Arial', 12)
        label_text = font.render(f"{self.label}:", True, (255, 255, 255))
        value = int(self.value) if self.is_int else f"{self.value:.2f}"
        value_text = font.render(str(value), True, (255, 255, 255))
        surface.blit(label_text, (self.rect.x, self.rect.y - 18))
        surface.blit(value_text, (self.rect.x + self.rect.width + 5, self.rect.y - 3))

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False

    def draw(self, surface):
        color = (180, 50, 50) if self.hovered else (150, 0, 0)
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=5)
        font = pygame.font.SysFont('Arial', 16)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

class ChannelControls:
    def __init__(self, x, y, channel_name):
        self.x = x
        self.y = y
        self.channel_name = channel_name
        self.sliders = []
        self.create_sliders()

    def create_sliders(self):
        y_pos = self.y
        self.sliders.append(Slider(self.x, y_pos, SLIDER_WIDTH, SLIDER_HEIGHT, WAVE_TYPE_MIN, WAVE_TYPE_MAX, DEFAULT_WAVE_TYPE, f"{self.channel_name} Wave", True))
        y_pos += SLIDER_SPACING
        self.sliders.append(Slider(self.x, y_pos, SLIDER_WIDTH, SLIDER_HEIGHT, FREQ_MIN, FREQ_MAX, DEFAULT_FREQ, f"{self.channel_name} Freq"))
        y_pos += SLIDER_SPACING
        self.sliders.append(Slider(self.x, y_pos, SLIDER_WIDTH, SLIDER_HEIGHT, AMP_MIN, AMP_MAX, DEFAULT_AMP, f"{self.channel_name} Amp"))
        y_pos += SLIDER_SPACING
        self.sliders.append(Slider(self.x, y_pos, SLIDER_WIDTH, SLIDER_HEIGHT, OFFSET_MIN, OFFSET_MAX, DEFAULT_OFFSET, f"{self.channel_name} Offset"))
        y_pos += SLIDER_SPACING
        self.sliders.append(Slider(self.x, y_pos, SLIDER_WIDTH, SLIDER_HEIGHT, 0.0, 1.0, 0.0, f"{self.channel_name} Phase"))

    def get_wave_type(self):
        return WaveType(int(self.sliders[0].value))
    def get_frequency(self):
        return self.sliders[1].value
    def get_amplitude(self):
        return self.sliders[2].value
    def get_offset(self):
        return self.sliders[3].value
    def get_phase(self):
        return self.sliders[4].value

    def draw(self, surface):
        for slider in self.sliders:
            slider.draw(surface)

    def handle_event(self, event):
        for slider in self.sliders:
            if event.type == pygame.MOUSEBUTTONDOWN and slider.handle_rect.collidepoint(event.pos):
                slider.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                slider.dragging = False
            elif event.type == pygame.MOUSEMOTION and slider.dragging:
                mouse_x = max(slider.rect.left, min(event.pos[0], slider.rect.right - SLIDER_HANDLE_WIDTH))
                slider.value = slider.get_value(mouse_x)
                slider.update_handle_pos()

class SignalGenerator:
    def __init__(self, x_controls, y_controls):
        self.time = 0
        self.dt = 1/FPS
        self.x_controls = x_controls
        self.y_controls = y_controls

    def generate_wave(self, wave_type, freq, amp, offset, t, phase):
        normalized_t = 2 * math.pi * freq * (t + phase / freq)
        if wave_type == WaveType.SINE:
            value = math.sin(normalized_t)
        elif wave_type == WaveType.SQUARE:
            value = 1 if math.sin(normalized_t) >= 0 else -1
        elif wave_type == WaveType.SAWTOOTH:
            value = 2 * (normalized_t % (2 * math.pi) / (2 * math.pi) - 1)
        elif wave_type == WaveType.TRIANGLE:
            value = 2 * abs(2 * (normalized_t % (2 * math.pi) / (2 * math.pi) - 1) - 1)
        return amp * value + offset

    def get_xy_position(self, canvas_width, screen_height, time_offset):
        t = time_offset
        x_wave = self.x_controls.get_wave_type()
        x_freq = self.x_controls.get_frequency()
        x_amp = self.x_controls.get_amplitude()
        x_offset = self.x_controls.get_offset()
        x_phase = self.x_controls.get_phase()

        y_wave = self.y_controls.get_wave_type()
        y_freq = self.y_controls.get_frequency()
        y_amp = self.y_controls.get_amplitude()
        y_offset = self.y_controls.get_offset()
        y_phase = self.y_controls.get_phase()

        x = canvas_width // 2 + int((canvas_width // 2) * self.generate_wave(x_wave, x_freq, x_amp, x_offset, t, x_phase))
        y = screen_height // 2 + int((screen_height // 2) * self.generate_wave(y_wave, y_freq, y_amp, y_offset, t, y_phase))

        return max(0, min(canvas_width, x)), max(0, min(screen_height, y))

def interpolate_points(p1, p2, steps):
    return [
        (int(p1[0] + (p2[0] - p1[0]) * i / steps), int(p1[1] + (p2[1] - p1[1]) * i / steps))
        for i in range(1, steps + 1)
    ]

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Advanced Oscilloscope Simulator")
    clock = pygame.time.Clock()
    spots = []
    running = True

    x_controls = ChannelControls(0, 20, "X")
    y_controls = ChannelControls(0, 20 + SLIDER_SPACING*5, "Y")
    size_slider = Slider(0, 20 + SLIDER_SPACING*10, SLIDER_WIDTH, SLIDER_HEIGHT, SIZE_MIN, SIZE_MAX, DEFAULT_SIZE, "Dot Size", True)
    decay_slider = Slider(0, 20 + SLIDER_SPACING*11, SLIDER_WIDTH, SLIDER_HEIGHT, DECAY_MIN, DECAY_MAX, DEFAULT_DECAY, "Decay Rate")
    poll_rate_slider = Slider(0, 20 + SLIDER_SPACING*12, SLIDER_WIDTH, SLIDER_HEIGHT, POLL_RATE_MIN, POLL_RATE_MAX, DEFAULT_POLL_RATE, "Polling Rate", True)
    
    signal_gen = SignalGenerator(x_controls, y_controls)
    mouse_mode = True
    active_slider = None

    polling_rate = poll_rate_slider.value  # Start with slider value
    polling_interval = 1.0 / polling_rate
    time_since_last_poll = 0.0
    poll_positions = []

    def reset_sliders():
        all_sliders = x_controls.sliders + y_controls.sliders + [size_slider, decay_slider, poll_rate_slider]
        for slider in all_sliders:
            if slider.label in PRESET_VALUES:
                slider.value = PRESET_VALUES[slider.label]
                slider.update_handle_pos()
    reset_button = Button(0, 0, 120, 30, "Reset", reset_sliders)

    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds elapsed this frame

        screen_width, screen_height = screen.get_size()
        canvas_width = screen_width - SLIDER_PANEL_WIDTH
        screen.fill(BACKGROUND_COLOR)
        pygame.draw.line(screen, (50, 50, 50), (canvas_width, 0), (canvas_width, screen_height))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                mouse_mode = not mouse_mode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for slider in [size_slider, decay_slider, poll_rate_slider] + x_controls.sliders + y_controls.sliders:
                    if slider.handle_rect.collidepoint(event.pos):
                        active_slider = slider
                        break
            elif event.type == pygame.MOUSEBUTTONUP:
                active_slider = None
            elif event.type == pygame.MOUSEMOTION and active_slider:
                mouse_x = max(active_slider.rect.left, min(event.pos[0], active_slider.rect.right - SLIDER_HANDLE_WIDTH))
                active_slider.value = active_slider.get_value(mouse_x)
                active_slider.update_handle_pos()

            x_controls.handle_event(event)
            y_controls.handle_event(event)
            reset_button.handle_event(event)


        # Update polling rate from slider dynamically
        polling_rate = poll_rate_slider.value
        polling_interval = 1.0 / polling_rate

        if mouse_mode:
            current_pos = pygame.mouse.get_pos()
            if len(spots) > 0 and current_pos != spots[-1].pos:
                for pos in interpolate_points(spots[-1].pos, current_pos, SPOTS_PER_FRAME):
                    spots.append(Spot(pos, size_slider.value, decay_slider.value))
            spots.append(Spot(current_pos, size_slider.value, decay_slider.value))
        else:
            # Accumulate time for polling
            time_since_last_poll += dt

            # Poll signal position multiple times if needed
            while time_since_last_poll >= polling_interval:
                time_since_last_poll -= polling_interval
                # Advance signal time by polling interval
                signal_gen.time += polling_interval
                pos = signal_gen.get_xy_position(canvas_width, screen_height, signal_gen.time)
                poll_positions.append(pos)

            # If we have at least 2 positions, interpolate spots between them
            if len(poll_positions) >= 2:
                for i in range(len(poll_positions) - 1):
                    interp_points = interpolate_points(poll_positions[i], poll_positions[i + 1], SPOTS_PER_FRAME)
                    for p in interp_points:
                        spots.append(Spot(p, size_slider.value, decay_slider.value))
                # Keep only the last poll position for next interpolation
                poll_positions = [poll_positions[-1]]

        for spot in spots[:]:
            spot.update()
            spot.draw(screen)
            if spot.brightness <= 0.01:
                spots.remove(spot)

        pygame.draw.circle(screen, SPOT_COLOR, current_pos, CORE_RADIUS)

        # Position sliders on the panel
        panel_x = canvas_width + 20
        for i, ctrl in enumerate([x_controls, y_controls]):
            for j, slider in enumerate(ctrl.sliders):
                slider.rect.x = slider.handle_rect.x = panel_x
                slider.rect.y = 20 + SLIDER_SPACING * (j + i*5)
                slider.update_handle_pos()
        for i, slider in enumerate([size_slider, decay_slider, poll_rate_slider]):
            slider.rect.x = slider.handle_rect.x = panel_x
            slider.rect.y = 20 + SLIDER_SPACING * (10 + i)
            slider.update_handle_pos()

        reset_button.rect.x = panel_x
        reset_button.rect.y = screen_height - 50
        reset_button.draw(screen)


        x_controls.draw(screen)
        y_controls.draw(screen)
        size_slider.draw(screen)
        decay_slider.draw(screen)
        poll_rate_slider.draw(screen)

        font = pygame.font.SysFont('Arial', 24)
        mode_text = font.render(f"Mode: {'Mouse' if mouse_mode else 'X/Y Signals'} (SPACE)", True, (255, 255, 255))
        screen.blit(mode_text, (canvas_width - 250, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()