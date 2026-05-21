"""
TANK DAI CHIEN - ULTIMATE EDITION v3.0
========================================
Features:
- Tutorial / How to Play screen
- Enhanced Shop with upgrade tiers
- Themed maps (Desert, Snow, City, Jungle, Lava)
- Boss battles every 5th level
- Minimap
- Weather effects
- Screen transitions
- Enhanced particles & explosions
- Better HUD with skill indicators
- Achievement popups
- Smooth camera
- Premium visuals
"""
import pygame, sys, math, random, heapq, os, json, socket, threading, time, zlib
from sprites import SpriteCache, TS, BOSS_COLORS, _BOSS_DISPLAY
from collections import deque
import collections
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_data.json")

def save_game_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_game_data():
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

# ═══════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════
COLS, ROWS = 40, 20
UI_BAR = 60
SW, SH = 1280, 720
FPS = 60
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

EMPTY = 0; BRICK = 1; STEEL = 2; GRASS = 3; WATER = 4; CRATE = 5; BASE = 6

MAP_THEMES = ["kawaii_woodland", "default", "desert", "snow", "city", "jungle", "lava"]

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Query current desktop monitor resolution
info = pygame.display.Info()
desktop_w = info.current_w
desktop_h = info.current_h

START_WINDOWED = os.environ.get("TANK_WINDOWED", "1") == "1"

# Dynamically initialize premium scaling resolution
if START_WINDOWED:
    # Open at a highly compatible 16:9 windowed resolution (1024x576)
    # that fits beautifully on all screens, including laptops with Windows High-DPI scaling.
    # The game automatically smoothscales 100% perfectly. Player can still drag/resize.
    phys_w = 1024
    phys_h = 576
    if desktop_w - 60 < phys_w:
        phys_w = max(800, desktop_w - 60)
    if desktop_h - 80 < phys_h:
        phys_h = max(450, desktop_h - 80)
    _screen_flags = pygame.RESIZABLE
else:
    # Fullscreen native resolution for ultimate anti-aliased graphics
    phys_w = desktop_w
    phys_h = desktop_h
    _screen_flags = pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE

screen = pygame.display.set_mode((phys_w, phys_h), _screen_flags)
pygame.display.set_caption("Tank Đại Chiến - Ultimate")
clock = pygame.time.Clock()
is_fullscreen = not START_WINDOWED


def _show_boot_splash(message="ĐANG TẢI...", subtitle=""):
    """Paint a quick boot splash so the player never sees a black screen
    while the sprite cache + video frames are being prepared.
    This is called before any heavy initialisation work."""
    try:
        screen.fill((6, 10, 22))
        # Soft vertical gradient
        for y in range(0, phys_h, 4):
            t = y / max(1, phys_h)
            r = int(6 + 20 * t)
            g = int(10 + 14 * t)
            b = int(22 + 50 * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (phys_w, y + 3))
        # Centered title
        try:
            f = pygame.font.SysFont("consolas", 48, bold=True)
            fs = pygame.font.SysFont("consolas", 22)
        except Exception:
            f = pygame.font.Font(None, 56)
            fs = pygame.font.Font(None, 24)
        t1 = f.render("TANK ĐẠI CHIẾN", True, (140, 220, 255))
        screen.blit(t1, ((phys_w - t1.get_width()) // 2, phys_h // 2 - 80))
        t2 = fs.render(message, True, (255, 220, 110))
        screen.blit(t2, ((phys_w - t2.get_width()) // 2, phys_h // 2 - 10))
        if subtitle:
            t3 = fs.render(subtitle, True, (180, 200, 220))
            screen.blit(t3, ((phys_w - t3.get_width()) // 2, phys_h // 2 + 24))
        hint = fs.render("(lần đầu chạy hơi lâu - đang chuẩn bị đồ họa)",
                         True, (130, 150, 180))
        screen.blit(hint, ((phys_w - hint.get_width()) // 2,
                           phys_h // 2 + 60))
        pygame.display.flip()
        pygame.event.pump()
    except Exception:
        pass


# Paint splash immediately so user sees something while sprites build
_show_boot_splash("Đang tải hình ảnh chất lượng cao...")

def toggle_fullscreen():
    global is_fullscreen, phys_w, phys_h
    is_fullscreen = not is_fullscreen
    flags = (pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE) if is_fullscreen else pygame.RESIZABLE
    if is_fullscreen:
        phys_w = desktop_w
        phys_h = desktop_h
    else:
        # Back to a comfortable windowed size (1024x576) that scales perfectly.
        phys_w = 1024
        phys_h = 576
        if desktop_w - 60 < phys_w:
            phys_w = max(800, desktop_w - 60)
        if desktop_h - 80 < phys_h:
            phys_h = max(450, desktop_h - 80)
    pygame.display.set_mode((phys_w, phys_h), flags)

# Dynamic global mouse scaling hook to map hover coordinates perfectly back to logical 1280x720 space
_orig_get_pos = pygame.mouse.get_pos
def get_scaled_mouse_pos():
    x, y = _orig_get_pos()
    return int(x * (1280 / phys_w)), int(y * (720 / phys_h))
pygame.mouse.get_pos = get_scaled_mouse_pos

try:
    FONT_BIG = pygame.font.SysFont("consolas", 40, bold=True)
    FONT_MED = pygame.font.SysFont("consolas", 22, bold=True)
    FONT_SM = pygame.font.SysFont("consolas", 16)
    FONT_TITLE = pygame.font.SysFont("consolas", 54, bold=True)
    FONT_HUGE = pygame.font.SysFont("consolas", 72, bold=True)
except Exception:
    FONT_BIG = pygame.font.Font(None, 40)
    FONT_MED = pygame.font.Font(None, 24)
    FONT_SM = pygame.font.Font(None, 16)
    FONT_TITLE = pygame.font.Font(None, 52)
    FONT_HUGE = pygame.font.Font(None, 64)

sprites = SpriteCache()

# ═══════════════════════════════════════
#  KAWAII UI PRIMITIVES
# ═══════════════════════════════════════
KAWAII_PALETTE = {
    "pink":     (255, 170, 210),
    "rose":     (255, 130, 170),
    "mint":     (130, 230, 200),
    "sky":      (140, 200, 255),
    "lavender": (200, 170, 255),
    "peach":    (255, 200, 140),
    "lemon":    (255, 240, 130),
    "cream":    (255, 245, 220),
    "ink":      (60, 50, 90),
    "shadow":   (35, 30, 60),
}

KAWAII_RAINBOW = [(255, 130, 170), (255, 200, 140), (255, 240, 130),
                  (130, 230, 200), (140, 200, 255), (200, 170, 255)]


def draw_kawaii_panel(surf, rect, fill=(60, 50, 95), border=(255, 200, 230),
                      radius=18, shadow_offset=4, glow=True):
    """Rounded gradient panel with soft drop shadow + optional pastel glow.

    Glow is rendered as an outer halo only (a slightly larger rounded rect
    behind the panel) so it never washes out the panel fill itself.
    """
    x, y, w, h = rect
    # Outer glow (drawn first, behind the panel + shadow)
    if glow:
        gpad = 14
        glow_surf = pygame.Surface((w + gpad * 2, h + gpad * 2), pygame.SRCALPHA)
        for i in range(4):
            a = 30 - i * 6
            if a <= 0:
                break
            pygame.draw.rect(glow_surf, (*border[:3], a),
                             (i, i, w + gpad * 2 - i * 2, h + gpad * 2 - i * 2),
                             border_radius=radius + gpad)
        surf.blit(glow_surf, (x - gpad, y - gpad))
    # Drop shadow
    if shadow_offset:
        sh = pygame.Surface((w + shadow_offset * 2, h + shadow_offset * 2), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 130),
                         (shadow_offset, shadow_offset, w, h), border_radius=radius)
        surf.blit(sh, (x - shadow_offset, y - shadow_offset))
    # Panel body (vertical gradient from `fill` to a slightly darker shade)
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        col = (int(fill[0] * (1 - t * 0.35)),
               int(fill[1] * (1 - t * 0.35)),
               int(fill[2] * (1 - t * 0.25)))
        pygame.draw.line(panel, col, (0, i), (w, i))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(panel, (x, y))
    pygame.draw.rect(surf, border, rect, 2, border_radius=radius)


def draw_kawaii_button(surf, rect, label, font, selected=False,
                       color_idx=0, tick=0, icon_fn=None):
    """Cute rounded button with pastel rainbow palette."""
    base_colors = [
        ((255, 170, 210), (255, 100, 160)),  # pink
        ((255, 220, 140), (255, 170, 60)),   # peach/orange
        ((180, 230, 255), (110, 180, 240)),  # sky
        ((200, 255, 200), (110, 220, 130)),  # mint
        ((220, 200, 255), (170, 130, 240)),  # lavender
    ]
    light, dark = base_colors[color_idx % len(base_colors)]
    x, y, w, h = rect
    pulse = (math.sin(tick * 0.08) + 1) * 0.5 if selected else 0
    # Shadow
    shadow = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 130), (3, 3, w, h), border_radius=h // 2)
    surf.blit(shadow, (x - 3, y - 3))
    # Body gradient
    body = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        col = (int(light[0] * (1 - t * 0.4) + dark[0] * t * 0.4),
               int(light[1] * (1 - t * 0.4) + dark[1] * t * 0.4),
               int(light[2] * (1 - t * 0.4) + dark[2] * t * 0.4))
        pygame.draw.line(body, col, (0, i), (w, i))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=h // 2)
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    # Top gloss highlight
    gloss = pygame.Surface((w, h // 2), pygame.SRCALPHA)
    for i in range(h // 2):
        a = int(160 * (1 - i / max(1, h // 2)))
        pygame.draw.line(gloss, (255, 255, 255, a), (0, i), (w, i))
    g_mask = pygame.Surface((w, h // 2), pygame.SRCALPHA)
    pygame.draw.rect(g_mask, (255, 255, 255, 255), (0, 0, w, h // 2),
                     border_radius=h // 2)
    gloss.blit(g_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    body.blit(gloss, (0, 2))
    surf.blit(body, (x, y))
    # Border — selected gets a bright pastel border, unselected is subtle
    if selected:
        # Gentle pulsing border brightness
        bri = int(220 + 35 * pulse)
        border_col = (min(255, bri), min(255, bri), min(255, bri))
        pygame.draw.rect(surf, border_col, rect, 3, border_radius=h // 2)
        # Thin inner highlight line (top edge only) for a polished look
        inner = pygame.Surface((w - 8, 2), pygame.SRCALPHA)
        pygame.draw.rect(inner, (255, 255, 255, int(80 + 40 * pulse)), (0, 0, w - 8, 2), border_radius=1)
        surf.blit(inner, (x + 4, y + 2))
    else:
        pygame.draw.rect(surf, (90, 70, 110), rect, 2, border_radius=h // 2)
    # Icon (optional, drawn left)
    label_x = x + w // 2
    if icon_fn:
        icon_size = h - 14
        icon_fn(surf, x + 14, y + (h - icon_size) // 2, icon_size)
        label_x = x + w // 2 + 8
    # Label
    label_shadow = font.render(label, True, (40, 30, 60))
    label_surf = font.render(label, True, (255, 255, 255))
    surf.blit(label_shadow, (label_x - label_surf.get_width() // 2 + 2,
                             y + (h - label_surf.get_height()) // 2 + 2))
    surf.blit(label_surf, (label_x - label_surf.get_width() // 2,
                           y + (h - label_surf.get_height()) // 2))


def draw_rainbow_text(surf, text, pos, font, tick=0, jitter=True):
    """Render text with each character in a different pastel rainbow color
    and a small wave animation."""
    cx = pos[0]
    base_y = pos[1]
    total_w = sum(font.size(c)[0] for c in text)
    cx -= total_w // 2
    for i, ch in enumerate(text):
        col = KAWAII_RAINBOW[(i + tick // 6) % len(KAWAII_RAINBOW)]
        offset_y = int(math.sin(tick * 0.12 + i * 0.6) * 4) if jitter else 0
        # Outline
        outline = font.render(ch, True, (40, 30, 60))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
            surf.blit(outline, (cx + dx, base_y + offset_y + dy))
        glyph = font.render(ch, True, col)
        surf.blit(glyph, (cx, base_y + offset_y))
        cx += font.size(ch)[0]


def draw_neon_button(surf, text, cx, cy, w, h, selected=False, tick=0):
    """Draw a neon-styled button centered at (cx, cy)."""
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    bg_c = (30, 25, 60) if not selected else (50, 40, 90)
    pygame.draw.rect(surf, bg_c, rect, border_radius=6)
    border_c = (0, 255, 200) if selected else (80, 80, 120)
    bw = 2 if not selected else 3
    pygame.draw.rect(surf, border_c, rect, bw, border_radius=6)
    if selected:
        glow = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
        glow_a = int(40 + 20 * abs(math.sin(tick * 0.08)))
        pygame.draw.rect(glow, (*border_c, glow_a), (0, 0, w + 8, h + 8), border_radius=8)
        surf.blit(glow, (rect.x - 4, rect.y - 4))
    txt_c = (255, 255, 255) if selected else (180, 180, 200)
    txt_r = FONT_MED.render(text, True, txt_c)
    surf.blit(txt_r, (cx - txt_r.get_width() // 2, cy - txt_r.get_height() // 2))


def draw_giant_shop_pet(surf, pet_id, cx, cy, size, tick):
    """Draw a massive, high-detail procedurally animated pet with seamless joint connections,
    flashing wings, walking/running legs, swinging tails, and rich technology overlays.
    Uses 3x Supersampling to achieve absolute visual perfection and anti-aliased graphics."""
    canvas_size = int(size * 2.0)
    # Create the high-resolution supersampled canvas (3x resolution)
    super_w = canvas_size * 3
    s3 = pygame.Surface((super_w, super_w), pygame.SRCALPHA)
    ccx, ccy = super_w // 2, super_w // 2
    
    # Scale helper for the 3x supersampled space
    def S(v):
        return int(v * (size / 64.0) * 3.0)

    # Curated premium color schemes
    C_MIDNIGHT = (30, 32, 45)
    C_CYBER_BLUE = (0, 200, 255)
    C_CYBER_PINK = (255, 0, 128)
    C_GOLD = (255, 215, 0)
    C_LAVA = (240, 50, 20)
    C_ROSE = (255, 105, 180)
    C_COBALT = (40, 90, 255)

    if pet_id == "wolf":
        # 1. Soft multi-layered ground shadow
        pygame.draw.ellipse(s3, (0, 0, 0, 60), (ccx - S(22), ccy + S(18), S(44), S(11)))
        pygame.draw.ellipse(s3, (0, 0, 0, 35), (ccx - S(16), ccy + S(19), S(32), S(7)))
        
        # 2. Bushy dual-tone tail with pendulum swing and fur spikes
        tail_angle = math.sin(tick * 0.1) * 22
        tail_w, tail_h = S(26), S(16)
        tail_surf = pygame.Surface((tail_w * 2, tail_h * 2), pygame.SRCALPHA)
        # Inner tail base
        pygame.draw.ellipse(tail_surf, (80, 85, 105), (tail_w // 2, tail_h // 2, tail_w, tail_h))
        # Highlighted top coat
        pygame.draw.ellipse(tail_surf, (150, 160, 185), (tail_w // 2 + S(2), tail_h // 2 + S(2), tail_w - S(4), tail_h - S(6)))
        # White tip
        pygame.draw.circle(tail_surf, (240, 245, 255), (tail_w // 2 + tail_w - S(4), tail_h // 2 + tail_h // 2), S(4))
        rot_tail = pygame.transform.rotate(tail_surf, tail_angle)
        s3.blit(rot_tail, (ccx - S(34) - rot_tail.get_width() // 2, ccy - S(2) - rot_tail.get_height() // 2))

        # 3. 4 Legs with beautiful ball hip/shoulder joints for seamless connection
        leg_w, leg_h = S(6.5), S(15)
        leg_walk_phase = tick * 0.15
        
        # Back legs (behind body)
        for idx, offset_x in enumerate([-S(12), S(8)]):
            phase_offset = math.pi if idx == 0 else 0
            leg_angle = math.sin(leg_walk_phase + phase_offset) * 25
            leg_surf = pygame.Surface((leg_w * 2, leg_h * 2), pygame.SRCALPHA)
            # Leg stem
            pygame.draw.rect(leg_surf, (70, 75, 95), (leg_w // 2, leg_h // 2, leg_w, leg_h), border_radius=S(2))
            # Paw with 3 distinct claws
            paw_y = leg_h // 2 + leg_h - S(3)
            pygame.draw.ellipse(leg_surf, (50, 55, 75), (leg_w // 2 - S(1), paw_y, leg_w + S(2), S(4.5)))
            for ci in range(3):
                claw_x = leg_w // 2 + ci * (leg_w // 2)
                pygame.draw.circle(leg_surf, (240, 240, 245), (int(claw_x), int(paw_y + S(3.5))), max(1, S(0.7)))
            rot_leg = pygame.transform.rotate(leg_surf, leg_angle)
            s3.blit(rot_leg, (ccx + offset_x - rot_leg.get_width() // 2, ccy + S(12) - rot_leg.get_height() // 2))

        # 4. Fluffy main body with layered chest fur
        body_w, body_h = S(34), S(24)
        pygame.draw.ellipse(s3, (100, 105, 125), (ccx - body_w // 2, ccy - body_h // 2 + S(2), body_w, body_h))
        pygame.draw.ellipse(s3, (130, 135, 155), (ccx - body_w // 2 + S(2), ccy - body_h // 2 + S(4), body_w - S(4), body_h - S(6)))
        # Fluffy white belly patch
        pygame.draw.ellipse(s3, (230, 235, 245), (ccx - S(10), ccy + S(1), S(18), S(9)))
        # Soft fur spikes on back
        for fi in range(3):
            fx = ccx - S(12) + fi * S(8)
            pygame.draw.polygon(s3, (100, 105, 125), [(fx, ccy - S(10)), (fx - S(3), ccy - S(14)), (fx + S(2), ccy - S(9))])

        # 5. Glowing cyber neon collar with gold pendant
        pygame.draw.ellipse(s3, (0, 240, 255), (ccx + S(2), ccy - S(4), S(13), S(7)))
        pygame.draw.ellipse(s3, (255, 255, 255), (ccx + S(4.5), ccy - S(3), S(8), S(4.5)))
        pygame.draw.circle(s3, C_GOLD, (ccx + S(10), ccy + S(1)), S(2.5))

        # 6. Front legs (in front of body) with seamless shoulder joints
        for idx, offset_x in enumerate([-S(6), S(14)]):
            phase_offset = 0 if idx == 0 else math.pi
            leg_angle = math.sin(leg_walk_phase + phase_offset) * 25
            leg_surf = pygame.Surface((leg_w * 2, leg_h * 2), pygame.SRCALPHA)
            # Leg stem
            pygame.draw.rect(leg_surf, (110, 115, 135), (leg_w // 2, leg_h // 2, leg_w, leg_h), border_radius=S(2))
            # Paw with claws
            paw_y = leg_h // 2 + leg_h - S(3)
            pygame.draw.ellipse(leg_surf, (80, 85, 105), (leg_w // 2 - S(1), paw_y, leg_w + S(2), S(4.5)))
            for ci in range(3):
                claw_x = leg_w // 2 + ci * (leg_w // 2)
                pygame.draw.circle(leg_surf, (240, 240, 245), (int(claw_x), int(paw_y + S(3.5))), max(1, S(0.7)))
            rot_leg = pygame.transform.rotate(leg_surf, leg_angle)
            s3.blit(rot_leg, (ccx + offset_x - rot_leg.get_width() // 2, ccy + S(12) - rot_leg.get_height() // 2))
            # Seamless shoulder joint cap on body
            pygame.draw.circle(s3, (130, 135, 155), (ccx + offset_x, ccy + S(3)), S(5.5))
            pygame.draw.circle(s3, (100, 105, 125), (ccx + offset_x, ccy + S(3)), S(5.5), 1)

        # 7. Head, twitching ears, and glowing visor eyepiece
        hx, hy = ccx + S(14), ccy - S(11)
        for ear_x, ear_flip in [(hx - S(4), False), (hx + S(2), True)]:
            ear_twitch = int(math.sin(tick * 0.08 + (math.pi if ear_flip else 0)) * S(2))
            pygame.draw.polygon(s3, (90, 95, 115), [(ear_x, hy), (ear_x + S(3.5), hy - S(11) + ear_twitch), (ear_x + S(7), hy)])
            pygame.draw.polygon(s3, (255, 180, 190), [(ear_x + S(1.5), hy), (ear_x + S(3.5), hy - S(8) + ear_twitch), (ear_x + S(5.5), hy)])
        pygame.draw.circle(s3, (120, 125, 145), (hx, hy), S(10.5))
        pygame.draw.circle(s3, (145, 150, 170), (hx - S(1), hy - S(1)), S(8.5))
        # Snout & Nose
        pygame.draw.ellipse(s3, (100, 105, 125), (hx + S(4.5), hy - S(2), S(11), S(6.5)))
        pygame.draw.circle(s3, (30, 30, 40), (hx + S(13.5), hy - S(1)), S(2))
        
        # Super-detail: Cyber Visor over the eye (swirling bright pink light!)
        pygame.draw.circle(s3, C_CYBER_PINK, (hx + S(4), hy - S(4.5)), S(3.5))
        pygame.draw.circle(s3, (255, 255, 255), (hx + S(4), hy - S(4.5)), S(2.0))
        # Crosshair line on visor
        pygame.draw.line(s3, (255, 255, 255), (hx + S(1.5), hy - S(4.5)), (hx + S(6.5), hy - S(4.5)), 1)

    elif pet_id == "dragon":
        # 1. Multi-layered lava shadow
        pygame.draw.ellipse(s3, (0, 0, 0, 50), (ccx - S(18), ccy + S(18), S(36), S(10)))
        pygame.draw.ellipse(s3, (180, 40, 20, 30), (ccx - S(14), ccy + S(19), S(28), S(7)))

        # 2. Fire tail swinging (with segmented scale lines)
        tail_wobble = math.sin(tick * 0.08) * 15
        tail_surf = pygame.Surface((S(34), S(34)), pygame.SRCALPHA)
        pygame.draw.ellipse(tail_surf, (160, 35, 15), (0, S(8), S(20), S(9)))
        # Scale detail on tail
        pygame.draw.arc(tail_surf, (255, 100, 50), (S(4), S(9), S(8), S(6)), 0, math.pi, S(1.5))
        # Pulsing tail flame tip
        fire_r = S(6.5) + int(math.sin(tick * 0.2) * S(1.5))
        pygame.draw.circle(tail_surf, (255, 120, 0), (S(20), S(12.5)), fire_r)
        pygame.draw.circle(tail_surf, (255, 215, 0), (S(20), S(12.5)), fire_r - S(2))
        rot_tail = pygame.transform.rotate(tail_surf, tail_wobble)
        s3.blit(rot_tail, (ccx - S(28) - rot_tail.get_width() // 2, ccy + S(2) - rot_tail.get_height() // 2))

        # 3. Flapping wings with double-jointed structural bones
        wing_w, wing_h = S(30), S(22)
        wing_angle = math.sin(tick * 0.18) * 30
        for side in [-1, 1]:
            w_surf = pygame.Surface((wing_w * 2, wing_h * 2), pygame.SRCALPHA)
            # Webbed wing polygon
            pts = [(wing_w, wing_h), (wing_w - S(18), wing_h - S(14)), (wing_w - S(26), wing_h - S(3)),
                   (wing_w - S(22), wing_h + S(11)), (wing_w, wing_h)]
            if side == 1:
                pts = [(wing_w, wing_h), (wing_w + S(18), wing_h - S(14)), (wing_w + S(26), wing_h - S(3)),
                       (wing_w + S(22), wing_h + S(11)), (wing_w, wing_h)]
            pygame.draw.polygon(w_surf, (150, 30, 20), pts)
            pygame.draw.polygon(w_surf, (255, 180, 50), pts, S(1.5))
            # Wing bone ribs
            if side == -1:
                pygame.draw.line(w_surf, (255, 220, 100), (wing_w, wing_h), (wing_w - S(18), wing_h - S(14)), S(2))
                pygame.draw.line(w_surf, (255, 220, 100), (wing_w, wing_h), (wing_w - S(26), wing_h - S(3)), S(1.5))
            else:
                pygame.draw.line(w_surf, (255, 220, 100), (wing_w, wing_h), (wing_w + S(18), wing_h - S(14)), S(2))
                pygame.draw.line(w_surf, (255, 220, 100), (wing_w, wing_h), (wing_w + S(26), wing_h - S(3)), S(1.5))
            
            rot_w = pygame.transform.rotate(w_surf, wing_angle * side)
            s3.blit(rot_w, (ccx - S(10) * side - rot_w.get_width() // 2, ccy - S(12) - rot_w.get_height() // 2))

        # 4. Muscular stepping legs with golden claws
        leg_w, leg_h = S(7.5), S(13.5)
        leg_phase = tick * 0.18
        for idx, offset_x in enumerate([-S(8), S(6)]):
            phase_offset = math.pi if idx == 0 else 0
            leg_ang = math.sin(leg_phase + phase_offset) * 20
            leg_surf = pygame.Surface((leg_w * 2, leg_h * 2), pygame.SRCALPHA)
            # Thigh
            pygame.draw.rect(leg_surf, (180, 40, 20), (leg_w // 2, leg_h // 2, leg_w, leg_h), border_radius=S(2.5))
            # Foot & 3 golden claws
            paw_y = leg_h // 2 + leg_h - S(3)
            pygame.draw.ellipse(leg_surf, (150, 30, 15), (leg_w // 2 - S(1.5), paw_y, leg_w + S(3), S(4.5)))
            for ci in range(3):
                claw_x = leg_w // 2 - S(1) + ci * (leg_w // 2 + S(0.5))
                pygame.draw.circle(leg_surf, C_GOLD, (int(claw_x), int(paw_y + S(3.5))), max(1, S(0.8)))
            
            rot_leg = pygame.transform.rotate(leg_surf, leg_ang)
            s3.blit(rot_leg, (ccx + offset_x - rot_leg.get_width() // 2, ccy + S(14) - rot_leg.get_height() // 2))

        # 5. Dragon main body with textured armor scales
        body_w, body_h = S(30), S(24)
        pygame.draw.ellipse(s3, (180, 40, 20), (ccx - body_w // 2, ccy - body_h // 2 + S(2), body_w, body_h))
        pygame.draw.ellipse(s3, (220, 60, 35), (ccx - body_w // 2 + S(2), ccy - body_h // 2 + S(4), body_w - S(4), body_h - S(6)))
        # Layered yellow-orange scales on belly
        for b_y in range(ccy - S(4), ccy + S(8), S(4)):
            pygame.draw.ellipse(s3, (255, 160, 50), (ccx - S(4.5), b_y, S(9), S(3)))
            pygame.draw.ellipse(s3, (255, 215, 0), (ccx - S(3), b_y + S(1), S(6), S(1.5)))
        # Seamless muscular hip caps
        for side in [-S(8), S(6)]:
            pygame.draw.circle(s3, (180, 40, 20), (ccx + side, ccy + S(5)), S(6))
            pygame.draw.circle(s3, (220, 60, 35), (ccx + side, ccy + S(5)), S(6), 1)

        # 6. Dragon head, long gold horns, and flaming breath sparks
        hx, hy = ccx + S(8), ccy - S(10)
        # Giant crown of sweeping gold horns (4 horns)
        for horn_x, horn_flip in [(hx - S(6), False), (hx - S(2), False), (hx + S(2), True), (hx + S(6), True)]:
            h_len = S(14) if abs(horn_x - hx) > S(4) else S(11)
            pts = [(horn_x, hy), (horn_x + (S(-7) if not horn_flip else S(7)), hy - h_len), (horn_x + S(3), hy)]
            pygame.draw.polygon(s3, C_GOLD, pts)
            pygame.draw.polygon(s3, (255, 255, 200), pts, 1)
        pygame.draw.circle(s3, (200, 45, 22), (hx, hy), S(11))
        pygame.draw.circle(s3, (240, 70, 40), (hx - S(1), hy - S(1)), S(9))
        pygame.draw.polygon(s3, (255, 150, 0), [(hx, hy - S(9.5)), (hx - S(3), hy - S(16)), (hx - S(6), hy - S(7))])
        
        # Glowing Emerald Green slit eyes
        pygame.draw.polygon(s3, (50, 255, 100), [(hx + S(1), hy - S(4.5)), (hx + S(5.5), hy - S(2)), (hx + S(2), hy - S(1))])
        pygame.draw.circle(s3, (255, 255, 255), (hx + S(3), hy - S(3)), max(1, S(0.7)))
        
        pygame.draw.ellipse(s3, (160, 30, 15), (hx + S(4.5), hy, S(8.5), S(6.5)))
        if random.random() < 0.45:
            spark_r = S(3) + random.randint(0, S(2))
            pygame.draw.circle(s3, (255, 140, 0), (hx + S(14), hy + S(3.5) + random.randint(-S(2), S(2))), spark_r)

    elif pet_id == "healer":
        # 1. Shadow
        pygame.draw.ellipse(s3, (0, 0, 0, 30), (ccx - S(14), ccy + S(18), S(28), S(8)))

        # 2. Rapid butterfly wings with detailed glowing veins and golden gems
        wing_w, wing_h = S(24), S(18)
        wing_ang = math.sin(tick * 0.28) * 35
        for side in [-1, 1]:
            w_surf = pygame.Surface((wing_w * 2, wing_h * 2), pygame.SRCALPHA)
            # Wing outer frame
            pygame.draw.ellipse(w_surf, (255, 80, 150, 200), (wing_w // 2, wing_h // 2, wing_w, wing_h))
            pygame.draw.ellipse(w_surf, (255, 255, 255, 240), (wing_w // 2 + S(2), wing_h // 2 + S(2), wing_w - S(4), wing_h - S(4)))
            pygame.draw.ellipse(w_surf, (100, 210, 255, 160), (wing_w // 2 + S(4), wing_h // 2 + S(9), wing_w - S(6), wing_h - S(9)))
            # Glowing gold wing veins
            pygame.draw.line(w_surf, C_GOLD, (wing_w, wing_h), (wing_w + S(14), wing_h + S(4)), S(1))
            pygame.draw.line(w_surf, C_GOLD, (wing_w, wing_h), (wing_w + S(10), wing_h + S(12)), S(1))
            # Sparkling circular spots on wing edges
            pygame.draw.circle(w_surf, (255, 255, 255), (wing_w + S(10), wing_h + S(4)), S(2))
            
            rot_w = pygame.transform.rotate(w_surf, wing_ang * side)
            s3.blit(rot_w, (ccx - S(12) * side - rot_w.get_width() // 2, ccy - S(6) - rot_w.get_height() // 2))

        # 3. Fluffy fairy dress with layered petals
        float_y = int(math.sin(tick * 0.08) * S(4))
        pygame.draw.polygon(s3, (255, 170, 200), [
            (ccx - S(8), ccy + S(2) + float_y), (ccx + S(8), ccy + S(2) + float_y),
            (ccx + S(16), ccy + S(16) + float_y), (ccx - S(16), ccy + S(16) + float_y)
        ])
        pygame.draw.ellipse(s3, (255, 255, 255), (ccx - S(14), ccy + S(11) + float_y, S(28), S(6)))
        # Waist sash (glowing gold)
        pygame.draw.rect(s3, C_GOLD, (ccx - S(8), ccy + S(1) + float_y, S(16), S(3)), border_radius=S(1))

        # 4. Dangling legs with cute kicking movement
        leg_kick = math.sin(tick * 0.15) * 8
        for offset_x in [-S(4), S(4)]:
            pygame.draw.rect(s3, (255, 215, 190), (ccx + offset_x - S(1), ccy + S(14) + float_y, S(3.5), S(9)), border_radius=S(1))
            # Pink shoes
            pygame.draw.circle(s3, C_ROSE, (ccx + offset_x + int(leg_kick * 0.2), ccy + S(22) + float_y), S(2.5))

        # 5. Cute Head, waving ponytails, and gold halo
        hx, hy = ccx, ccy - S(10) + float_y
        # Hair ponytails that wave programmatically
        hair_wave = int(math.sin(tick * 0.1) * S(3))
        pygame.draw.circle(s3, (255, 110, 160), (hx - S(9) + hair_wave, hy - S(4)), S(7))
        pygame.draw.circle(s3, (255, 110, 160), (hx + S(9) - hair_wave, hy - S(4)), S(7))
        # Hair core & bangs
        pygame.draw.circle(s3, (255, 140, 180), (hx, hy), S(10.5))
        pygame.draw.circle(s3, (255, 215, 190), (hx, hy), S(8.5))
        # Large sparkling baby-blue eyes
        pygame.draw.circle(s3, (60, 170, 255), (hx - S(3.5), hy), S(2))
        pygame.draw.circle(s3, (60, 170, 255), (hx + S(3.5), hy), S(2))
        pygame.draw.circle(s3, (255, 255, 255), (hx - S(3), hy - S(1)), S(0.8))
        pygame.draw.circle(s3, (255, 255, 255), (hx + S(4), hy - S(1)), S(0.8))
        # Rosy blushing cheeks
        pygame.draw.circle(s3, (255, 120, 140, 120), (hx - S(5.5), hy + S(3)), S(2))
        pygame.draw.circle(s3, (255, 120, 140, 120), (hx + S(5.5), hy + S(3)), S(2))
        # Halo
        pygame.draw.ellipse(s3, C_GOLD, (hx - S(8), hy - S(14), S(16), S(4.5)), S(1))

        # 6. Waving scepter wand arm with joint spheres
        wand_ang = math.sin(tick * 0.12) * 20
        wand_surf = pygame.Surface((S(18), S(32)), pygame.SRCALPHA)
        pygame.draw.line(wand_surf, (255, 215, 190), (S(4), S(15)), (S(4), S(24)), S(3.5))
        pygame.draw.line(wand_surf, (160, 110, 60), (S(4), S(4)), (S(4), S(20)), S(1.5))
        # Scepter topped with a massive spinning crystal star
        pygame.draw.circle(wand_surf, C_GOLD, (S(4), S(4)), S(4.5))
        pygame.draw.circle(wand_surf, (255, 255, 255), (S(4), S(4)), S(2))
        
        rot_wand = pygame.transform.rotate(wand_surf, wand_ang)
        s3.blit(rot_wand, (ccx + S(8) - rot_wand.get_width() // 2, ccy - S(2) + float_y - rot_wand.get_height() // 2))
        # Seamless shoulder joint sphere
        pygame.draw.circle(s3, (255, 150, 180), (ccx + S(6), ccy + S(4) + float_y), S(3.5))

    elif pet_id == "shield_bot":
        # 1. Soft industrial ground shadow
        pygame.draw.ellipse(s3, (0, 0, 0, 45), (ccx - S(18), ccy + S(18), S(36), S(9)))
        
        bob = int(math.sin(tick * 0.08) * S(3))
        leg_phase = tick * 0.16

        # 2. Marching mechanical legs with heavy shock absorbers
        for idx, offset_x in enumerate([-S(9), S(5)]):
            phase_offset = math.pi if idx == 0 else 0
            leg_y = ccy + S(12) + int(math.sin(leg_phase + phase_offset) * S(3))
            # Pneumatic piston cylinder
            pygame.draw.rect(s3, (80, 85, 100), (ccx + offset_x, leg_y, S(5.5), S(8.5)), border_radius=S(1.5))
            # Heavy magnetic foot pad
            pygame.draw.rect(s3, (50, 55, 70), (ccx + offset_x - S(1.5), leg_y + S(6.5), S(8.5), S(3.5)), border_radius=S(1))
            # Bright yellow hazard stripes on piston
            pygame.draw.line(s3, C_GOLD, (ccx + offset_x + S(1), leg_y + S(3)), (ccx + offset_x + S(4.5), leg_y + S(3)), 2)

        # 3. Main armored heavy body with cybernetic caution plates
        body_rect = (ccx - S(16), ccy - S(13) + bob, S(32), S(26))
        bx, by, bw, bh = body_rect
        pygame.draw.rect(s3, (100, 110, 125), body_rect, border_radius=S(5.5))
        pygame.draw.rect(s3, (135, 145, 165), (bx + S(2), by + S(2), bw - S(4), bh - S(4)), border_radius=S(4.5))
        # Horizontal steel panel groove
        pygame.draw.line(s3, (70, 75, 90), (bx + S(2), by + bh // 2), (bx + bw - S(2), by + bh // 2), S(1))
        # Tech rivets on chassis corners
        for rx, ry in [(bx + S(4), by + S(4)), (bx + bw - S(4), by + S(4)),
                       (bx + S(4), by + bh - S(4)), (bx + bw - S(4), by + bh - S(4))]:
            pygame.draw.circle(s3, (50, 55, 70), (rx, ry), max(1, S(0.8)))
            pygame.draw.circle(s3, (255, 255, 255, 100), (rx - 1, ry - 1), max(1, S(0.4)))

        # 4. Tech glowing visor LED (Pulsing neon blue)
        visor_w = S(20) + int(math.sin(tick * 0.12) * S(1.5))
        pygame.draw.rect(s3, C_CYBER_BLUE, (ccx - visor_w // 2, by + S(4.5), visor_w, S(4.5)), border_radius=S(2))
        pygame.draw.rect(s3, (255, 255, 255), (ccx - visor_w // 2 + S(2), by + S(5.5), visor_w - S(4), S(1.8)), border_radius=S(1))

        # 5. Chest thermonuclear reactor core
        pygame.draw.circle(s3, C_CYBER_BLUE, (ccx, by + S(16.5)), S(4.5))
        pygame.draw.circle(s3, (255, 255, 255), (ccx, by + S(16.5)), S(2))

        # 6. Industrial claw arms with ball joint sockets for seamless connection
        for side in [-1, 1]:
            arm_ang = math.sin(tick * 0.1) * 20 * side
            arm_surf = pygame.Surface((S(14), S(28)), pygame.SRCALPHA)
            # Upper arm sleeve
            pygame.draw.rect(arm_surf, (110, 120, 135), (S(4.5), S(6), S(5), S(13)), border_radius=S(1.5))
            # Heavy metal shoulder armor shield
            pygame.draw.rect(arm_surf, (55, 60, 75), (S(2), S(18), S(10), S(7.5)), border_radius=S(2))
            # 2 mechanical claw fingers
            pygame.draw.line(arm_surf, C_GOLD, (S(4), S(24)), (S(2), S(27)), S(1.5))
            pygame.draw.line(arm_surf, C_GOLD, (S(10), S(24)), (S(12), S(27)), S(1.5))
            
            rot_arm = pygame.transform.rotate(arm_surf, arm_ang)
            s3.blit(rot_arm, (ccx + S(17) * side - rot_arm.get_width() // 2, by + S(10) - rot_arm.get_height() // 2))
            
            # Seamless ball joint cap (eliminates disjointed visual feel)
            pygame.draw.circle(s3, (70, 75, 90), (ccx + S(16) * side, by + S(8)), S(4.5))
            pygame.draw.circle(s3, C_CYBER_BLUE, (ccx + S(16) * side, by + S(8)), S(2))

        # 7. Coiled Holographic energy shield bubble
        shield_pulse = S(29) + int(math.sin(tick * 0.1) * S(3))
        pygame.draw.circle(s3, (0, 240, 255, 30), (ccx, ccy + bob), shield_pulse, S(1.5))
        pygame.draw.arc(s3, (255, 255, 255, 80), (ccx - shield_pulse, ccy + bob - shield_pulse, shield_pulse * 2, shield_pulse * 2), math.pi * 0.2, math.pi * 0.8, S(2))

    elif pet_id == "magnet":
        bob = int(math.sin(tick * 0.05) * S(5))
        wobble = math.sin(tick * 0.08) * 12
        
        # 1. Shadow
        pygame.draw.ellipse(s3, (0, 0, 0, 35), (ccx - S(14), ccy + S(18), S(28), S(7)))

        # 2. U-shaped body with gorgeous copper-wrapped coils
        mag_surf = pygame.Surface((S(38), S(38)), pygame.SRCALPHA)
        mcx, mcy = S(19), S(19)
        # Red side arm (Left)
        pygame.draw.arc(mag_surf, (240, 50, 50), (mcx - S(14), mcy - S(14), S(28), S(28)), math.pi // 2, math.pi * 1.5, S(8.5))
        # Blue side arm (Right)
        pygame.draw.arc(mag_surf, (50, 80, 240), (mcx - S(14), mcy - S(14), S(28), S(28)), -math.pi // 2, math.pi // 2, S(8.5))
        
        # Gloss sheen lines along magnet arms
        pygame.draw.ellipse(mag_surf, (255, 255, 255, 120), (mcx - S(14) + S(2), mcy - S(14) + S(2), S(24), S(24)), S(1))
        
        # Copper-wrapped coils wrapped around both sides of magnet (high-fidelity mechanical detailing)
        for cy_offset in range(-S(6), S(6), S(3)):
            pygame.draw.rect(mag_surf, C_GOLD, (mcx - S(14) + S(1), mcy + cy_offset, S(6), S(1.5)), border_radius=S(0.5))
            pygame.draw.rect(mag_surf, C_GOLD, (mcx + S(7), mcy + cy_offset, S(6), S(1.5)), border_radius=S(0.5))
            
        # Heavy metallic terminal poles with +/- markers
        pygame.draw.rect(mag_surf, (220, 220, 240), (mcx - S(14) - S(0.5), mcy - S(7.5), S(8.5), S(4)), border_radius=S(1))
        pygame.draw.rect(mag_surf, (220, 220, 240), (mcx + S(6), mcy - S(7.5), S(8.5), S(4)), border_radius=S(1))
        
        rot_mag = pygame.transform.rotate(mag_surf, wobble)
        s3.blit(rot_mag, (ccx - rot_mag.get_width() // 2, ccy + bob - rot_mag.get_height() // 2))

        # 3. Yellow plasma energy arcs shooting between poles
        if (tick // 3) % 2 == 0:
            pygame.draw.line(s3, C_GOLD, (ccx - S(9), ccy - S(4) + bob), (ccx + S(9), ccy - S(4) + bob), S(1.8))
            pygame.draw.circle(s3, (255, 255, 255), (ccx + random.randint(-S(7), S(7)), ccy - S(4) + bob), S(2.5))

    elif pet_id == "ghost":
        # 1. Soft ethereal shadow
        pygame.draw.ellipse(s3, (0, 0, 0, 25), (ccx - S(12), ccy + S(18), S(24), S(6)))
        
        float_y = int(math.sin(tick * 0.06) * S(8))
        tail_x = int(math.sin(tick * 0.12) * S(5))

        # 2. Majestic multi-layered vapor comet tail (flowing seamlessly from body)
        pygame.draw.polygon(s3, (180, 220, 255, 100), [
            (ccx - S(8), ccy + S(6) + float_y), (ccx + S(8), ccy + S(6) + float_y),
            (ccx + tail_x - S(4), ccy + S(22) + float_y), (ccx + tail_x + S(4), ccy + S(22) + float_y)
        ])
        pygame.draw.polygon(s3, (180, 220, 255, 180), [
            (ccx - S(5), ccy + S(7) + float_y), (ccx + S(5), ccy + S(7) + float_y),
            (ccx + tail_x, ccy + S(20) + float_y)
        ])

        # 3. Flappy transparent wavy arms flowing from shoulders
        arm_ang = math.sin(tick * 0.15) * 15
        for side in [-1, 1]:
            arm_surf = pygame.Surface((S(14), S(14)), pygame.SRCALPHA)
            # Long wavy energy arm
            pygame.draw.ellipse(arm_surf, (200, 230, 255, 200), (0, 0, S(14), S(8.5)))
            rot_arm = pygame.transform.rotate(arm_surf, arm_ang * side)
            s3.blit(rot_arm, (ccx + S(12) * side - rot_arm.get_width() // 2, ccy + float_y - rot_arm.get_height() // 2))

        # 4. Main body and glowing blushing cheeks
        pygame.draw.circle(s3, (200, 230, 255, 220), (ccx, ccy + float_y), S(13.5))
        pygame.draw.circle(s3, (255, 255, 255, 245), (ccx - S(1), ccy - S(1) + float_y), S(11.5))
        # Rosy blushing cheeks
        pygame.draw.circle(s3, (255, 120, 150, 130), (ccx - S(7.5), ccy + S(3.5) + float_y), S(2.8))
        pygame.draw.circle(s3, (255, 120, 150, 130), (ccx + S(7.5), ccy + S(3.5) + float_y), S(2.8))

        # 5. Glowing star-eyes
        pygame.draw.circle(s3, (60, 150, 255), (ccx - S(4), ccy + float_y), S(2.2))
        pygame.draw.circle(s3, (60, 150, 255), (ccx + S(4), ccy + float_y), S(2.2))
        pygame.draw.circle(s3, (255, 255, 255), (ccx - S(3.5), ccy - S(0.8) + float_y), S(1))
        pygame.draw.circle(s3, (255, 255, 255), (ccx + S(4.5), ccy - S(0.8) + float_y), S(1))

        # Cute small bow accessory on head
        pygame.draw.circle(s3, C_ROSE, (ccx, ccy - S(13) + float_y), S(2.5))
        pygame.draw.polygon(s3, C_ROSE, [(ccx, ccy - S(13) + float_y), (ccx - S(5), ccy - S(16) + float_y), (ccx - S(3), ccy - S(11) + float_y)])
        pygame.draw.polygon(s3, C_ROSE, [(ccx, ccy - S(13) + float_y), (ccx + S(5), ccy - S(16) + float_y), (ccx + S(3), ccy - S(11) + float_y)])

    # Downscale smoothly using bilinear filtering to achieve perfectly anti-aliased (răng cưa) premium edges!
    s = pygame.transform.smoothscale(s3, (canvas_size, canvas_size))
    surf.blit(s, (cx - canvas_size // 2, cy - canvas_size // 2))


def draw_heart_icon(surf, x, y, size, filled=True, outline=(180, 30, 80)):
    """Cute pixel heart at (x, y) with given size."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    fill = (255, 100, 130) if filled else (90, 70, 80)
    # Two circles + triangle
    r = size // 4
    pygame.draw.circle(s, fill, (cx - r, cy - r // 2), r + 1)
    pygame.draw.circle(s, fill, (cx + r, cy - r // 2), r + 1)
    pts = [(cx - 2 * r, cy - r // 4), (cx + 2 * r, cy - r // 4),
           (cx, cy + size // 2 - 1)]
    pygame.draw.polygon(s, fill, pts)
    pygame.draw.circle(s, outline, (cx - r, cy - r // 2), r + 1, 2)
    pygame.draw.circle(s, outline, (cx + r, cy - r // 2), r + 1, 2)
    pygame.draw.lines(s, outline, False,
                      [(cx - 2 * r, cy - r // 4), (cx, cy + size // 2 - 1),
                       (cx + 2 * r, cy - r // 4)], 2)
    # Specular highlight
    pygame.draw.circle(s, (255, 230, 240), (cx - r, cy - r), max(1, r // 3))
    surf.blit(s, (x, y))


def draw_coin_icon(surf, x, y, size):
    """Gold coin with star, rotates slightly with time."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pygame.draw.circle(s, (255, 200, 60), (cx, cy), size // 2 - 1)
    pygame.draw.circle(s, (200, 130, 30), (cx, cy), size // 2 - 1, 2)
    pygame.draw.circle(s, (255, 240, 160),
                       (cx - size // 6, cy - size // 6), max(1, size // 8))
    star = "*"
    f = pygame.font.SysFont("consolas", max(8, size - 6), bold=True)
    g = f.render(star, True, (180, 100, 30))
    s.blit(g, (cx - g.get_width() // 2, cy - g.get_height() // 2 - 1))
    surf.blit(s, (x, y))


def draw_gem_icon(surf, x, y, size):
    """Cyan diamond / gem icon."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    top = 1
    mid_y = size // 3
    bot = size - 2
    pts = [(cx, top), (size - 2, mid_y), (cx, bot), (1, mid_y)]
    pygame.draw.polygon(s, (140, 220, 255), pts)
    pygame.draw.polygon(s, (60, 140, 200), pts, 2)
    # Inner facets
    pygame.draw.line(s, (220, 245, 255), (cx, top), (cx, bot), 1)
    pygame.draw.line(s, (220, 245, 255), (cx, top), (1, mid_y), 1)
    pygame.draw.polygon(s, (255, 255, 255),
                        [(cx, top + 1), (cx + 3, mid_y - 2), (cx - 1, mid_y - 1)])
    surf.blit(s, (x, y))


def draw_sparkle(surf, x, y, size, color=(255, 255, 200), alpha=255):
    """4-point sparkle / star burst."""
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    cx = size
    pygame.draw.line(s, (*color, alpha), (cx, 0), (cx, size * 2 - 1), 2)
    pygame.draw.line(s, (*color, alpha), (0, cx), (size * 2 - 1, cx), 2)
    pygame.draw.line(s, (*color, alpha // 2),
                     (size // 2, size // 2), (size + size // 2, size + size // 2), 1)
    pygame.draw.line(s, (*color, alpha // 2),
                     (size + size // 2, size // 2), (size // 2, size + size // 2), 1)
    pygame.draw.circle(s, (255, 255, 255, alpha), (cx, cx), 2)
    surf.blit(s, (x - cx, y - cx))


def draw_pastel_starfield(surf, tick, density=70):
    """Animated background of soft pastel sparkles + drifting stars."""
    for i in range(density):
        x = (i * 71 + tick * 0.4) % SW
        y = (i * 53 + tick * 0.18) % SH
        col = KAWAII_RAINBOW[i % len(KAWAII_RAINBOW)]
        pulse = abs(math.sin(tick * 0.04 + i * 0.7))
        a = int(60 + pulse * 140)
        sz = 1 + (i % 3)
        ps = pygame.Surface((sz * 2 + 4, sz * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*col, a), (sz + 2, sz + 2), sz)
        surf.blit(ps, (int(x), int(y)))
        if i % 9 == 0:
            draw_sparkle(surf, int(x), int(y), 6,
                         color=(255, 255, 220), alpha=int(120 * pulse + 40))


# ═══════════════════════════════════════
#  SOUND FX
# ═══════════════════════════════════════
def gen_sound(freq, dur=0.08, vol=0.3, wave="sine"):
    import struct as _struct
    sr = 44100; n = int(sr * dur)
    samples = []
    for i in range(n):
        t_val = i / sr
        if wave == "sine":
            w = math.sin(freq * t_val * 2 * math.pi)
        elif wave == "noise":
            w = random.uniform(-1, 1)
        else:
            w = 1.0 if math.sin(freq * t_val * 2 * math.pi) >= 0 else -1.0
        fl = int(n * 0.1)
        env = 1.0
        if fl > 0:
            if i < fl:
                env = i / fl
            elif i >= n - fl:
                env = (n - 1 - i) / fl
        val = int(w * env * vol * 32767)
        val = max(-32768, min(32767, val))
        samples.append(val)
    raw = b''.join(_struct.pack('<hh', s, s) for s in samples)
    snd = pygame.mixer.Sound(buffer=raw)
    return snd

snd_shoot = gen_sound(600, 0.06, 0.2)
snd_explode = gen_sound(100, 0.3, 0.4, "noise")
snd_pickup = gen_sound(880, 0.1, 0.3)
snd_hit = gen_sound(200, 0.15, 0.3, "noise")
snd_steel = gen_sound(1200, 0.05, 0.15)
snd_combo = gen_sound(900, 0.2, 0.35, "square")
snd_levelup = gen_sound(440, 0.4, 0.3, "sine")
snd_boss_alert = gen_sound(150, 0.5, 0.4, "square")
snd_buy = gen_sound(660, 0.12, 0.25)
snd_deny = gen_sound(200, 0.2, 0.2, "square")

def gen_laser_riser(duration=0.55, vol=0.45):
    import array, struct as _struct
    sample_rate = 44100
    n = int(sample_rate * duration)
    samples = []
    for i in range(n):
        t_val = i / sample_rate
        freq = 180 * math.exp(t_val * math.log(1400 / 180) / duration)
        freq += 60 * math.sin(35 * t_val * 2 * math.pi)
        w = 0.6 * math.sin(freq * t_val * 2 * math.pi) + 0.4 * (1.0 if math.sin(freq * t_val * 2 * math.pi) >= 0 else -1.0)
        env = 1.0
        if i < int(n * 0.2):
            env = i / int(n * 0.2)
        elif i >= n - int(n * 0.05):
            env = (n - 1 - i) / int(n * 0.05)
        val = int(w * env * vol * 32767)
        val = max(-32768, min(32767, val))
        samples.append(val)
    raw = b''.join(_struct.pack('<hh', s, s) for s in samples)
    return pygame.mixer.Sound(buffer=raw)

def gen_fat_explosion(duration=0.9, vol=0.7):
    import array, struct as _struct
    sample_rate = 44100
    n = int(sample_rate * duration)
    samples = []
    for i in range(n):
        t_val = i / sample_rate
        low_noise = random.uniform(-1, 1) * math.exp(-6.0 * t_val)
        mid_noise = 0.0
        if random.random() < 0.2:
            mid_noise = random.uniform(-1, 1) * math.exp(-12.0 * t_val)
        bass_freq = max(35, 120 - t_val * 190)
        bass_w = math.sin(bass_freq * t_val * 2 * math.pi) * math.exp(-4.5 * t_val)
        w = 0.5 * low_noise + 0.3 * mid_noise + 0.55 * bass_w
        env = 1.0 - (i / n)
        if i < int(n * 0.02):
            env = i / int(n * 0.02)
        val = int(w * env * vol * 32767)
        val = max(-32768, min(32767, val))
        samples.append(val)
    raw = b''.join(_struct.pack('<hh', s, s) for s in samples)
    return pygame.mixer.Sound(buffer=raw)

def gen_triumphant_fanfare(vol=0.55):
    import array, struct as _struct
    sample_rate = 44100
    notes = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99, 1046.50]
    note_dur = 0.075
    sustain_dur = 0.55
    samples = []
    for f in notes:
        n_samples = int(sample_rate * note_dur)
        for i in range(n_samples):
            t_val = i / sample_rate
            w = 0.55 * math.sin(f * t_val * 2 * math.pi) + 0.35 * (1.0 if math.sin(f * 2 * t_val * 2 * math.pi) >= 0 else -1.0)
            env = 1.0 - (i / n_samples) * 0.2
            if i < int(n_samples * 0.15):
                env = i / int(n_samples * 0.15)
            val = int(w * env * vol * 32767)
            val = max(-32768, min(32767, val))
            samples.append(val)
    f_sustain = notes[-1]
    n_sustain = int(sample_rate * sustain_dur)
    for i in range(n_sustain):
        t_val = i / sample_rate
        w = 0.45 * math.sin(f_sustain * t_val * 2 * math.pi) + 0.3 * math.sin(f_sustain * 1.25 * t_val * 2 * math.pi) + 0.25 * math.sin(f_sustain * 1.5 * t_val * 2 * math.pi)
        env = 1.0 - (i / n_sustain)
        val = int(w * env * vol * 32767)
        val = max(-32768, min(32767, val))
        samples.append(val)
    raw = b''.join(_struct.pack('<hh', s, s) for s in samples)
    return pygame.mixer.Sound(buffer=raw)

def gen_sad_trombone(vol=0.5):
    import array, struct as _struct
    sample_rate = 44100
    notes = [311.13, 293.66, 277.18]
    note_dur = 0.13
    sustain_dur = 0.75
    samples = []
    for f in notes:
        n_samples = int(sample_rate * note_dur)
        for i in range(n_samples):
            t_val = i / sample_rate
            freq = f * (1.0 - 0.04 * (i / n_samples))
            wah = 1.0 + 0.35 * math.sin(35 * t_val * 2 * math.pi)
            w = 0.55 * (2.0 * abs(2.0 * (freq * t_val - math.floor(freq * t_val + 0.5))) - 1.0)
            env = 1.0 - (i / n_samples) * 0.25
            val = int(w * env * wah * vol * 32767)
            val = max(-32768, min(32767, val))
            samples.append(val)
    n_sustain = int(sample_rate * sustain_dur)
    f_start = 261.63
    f_end = 185.00
    for i in range(n_sustain):
        t_val = i / sample_rate
        freq = f_start + (f_end - f_start) * (i / n_sustain)
        wah = 1.0 + 0.5 * math.sin(40 * t_val * 2 * math.pi)
        w = 0.6 * (2.0 * abs(2.0 * (freq * t_val - math.floor(freq * t_val + 0.5))) - 1.0)
        env = 1.0 - (i / n_sustain)
        val = int(w * env * wah * vol * 32767)
        val = max(-32768, min(32767, val))
        samples.append(val)
    raw = b''.join(_struct.pack('<hh', s, s) for s in samples)
    return pygame.mixer.Sound(buffer=raw)

snd_laser_riser = gen_laser_riser()
snd_epic_explosion = gen_fat_explosion()
snd_epic_win = gen_triumphant_fanfare()
snd_fail_trombone = gen_sad_trombone()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

try:
    snd_tach_mp3 = pygame.mixer.Sound(resource_path("TACH.mp3"))
    snd_tach_mp3.set_volume(0.85)
except Exception as e:
    snd_tach_mp3 = snd_fail_trombone

# ═══════════════════════════════════════
#  BACKGROUND MUSIC
# ═══════════════════════════════════════

try:
    pygame.mixer.music.load(resource_path("nhacnen.mp3"))
    pygame.mixer.music.set_volume(0.6)
except Exception as e:
    print(f"Music load error: {e}")

# ═══════════════════════════════════════
#  SCREEN TRANSITION
# ═══════════════════════════════════════
class Transition:
    def __init__(self):
        self.active = False
        self.alpha = 0
        self.target_alpha = 0
        self.speed = 8
        self.callback = None
        self.phase = "idle"

    def start(self, callback=None):
        self.active = True
        self.phase = "fade_out"
        self.alpha = 0
        self.target_alpha = 255
        self.callback = callback

    def update(self):
        if not self.active:
            return
        if self.phase == "fade_out":
            self.alpha = min(255, self.alpha + self.speed)
            if self.alpha >= 255:
                if self.callback:
                    self.callback()
                    self.callback = None
                self.phase = "fade_in"
        elif self.phase == "fade_in":
            self.alpha = max(0, self.alpha - self.speed)
            if self.alpha <= 0:
                self.active = False
                self.phase = "idle"

    def draw(self, surf):
        if not self.active or self.alpha <= 0:
            return
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self.alpha)))
        surf.blit(overlay, (0, 0))

transition = Transition()

# ═══════════════════════════════════════
#  SETTINGS / VIDEO / AUDIO
# ═══════════════════════════════════════
# All in-game SFX (used for the SFX volume slider).  Music has its own slider.
_ALL_SFX = [
    snd_shoot, snd_explode, snd_pickup, snd_hit, snd_steel, snd_combo,
    snd_levelup, snd_boss_alert, snd_buy, snd_deny,
    snd_laser_riser, snd_epic_explosion, snd_epic_win, snd_fail_trombone,
    snd_tach_mp3,
]
_BASE_SFX_VOL = {id(s): s.get_volume() for s in _ALL_SFX}

# Standard resolution presets used by the settings screen
RESOLUTION_PRESETS = [
    (1280, 720),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
]

# Sensible defaults — actual values are loaded from save file
DEFAULT_SETTINGS = {
    "master_volume": 80,     # 0..100
    "music_volume":  60,     # 0..100
    "sfx_volume":    80,     # 0..100
    "fullscreen":    False,
    "resolution_idx": 0,     # index into RESOLUTION_PRESETS (used when windowed)
    "graphics":      2,      # 0=Low, 1=Medium, 2=High, 3=Ultra
    "show_fps":      False,
    "show_minimap":  True,
    "screen_shake":  True,
    "particles":     True,
    "weather_fx":    True,
    "show_hints":    True,
    "vsync":         True,
}

# Map theme cosmetic definitions — used to render map preview thumbnails on
# the level-select / co-op room screens.  Each entry: (display name, sky/floor
# accent, deco accent, wall accent, terrain accent, emoji-style icon).
MAP_THEME_DEFS = {
    "default":          ("Chiến Trường",  (78, 92,  68),  (160, 150, 110), (170, 80, 60),  (90, 110, 70), "BATTLE CITY"),
    "kawaii_woodland":  ("Rừng Kawaii",   (180, 215, 140), (255, 200, 230), (255, 130, 170), (130, 230, 200), "WOODLAND"),
    "desert":           ("Sa Mạc",        (230, 200, 130), (240, 180, 80),  (190, 100, 40), (210, 170, 100), "DESERT"),
    "snow":             ("Băng Giá",      (220, 230, 240), (240, 250, 255), (140, 170, 200), (200, 210, 230), "FROZEN"),
    "city":             ("Thành Phố",     (110, 120, 135), (90,  100, 120),  (60, 65, 85),  (130, 140, 160), "URBAN"),
    "jungle":           ("Rừng Sâu",      (60, 110, 70),   (40, 90, 60),     (90, 70, 50),  (50, 130, 70),  "JUNGLE"),
    "lava":             ("Địa Ngục",      (90, 30, 30),    (200, 60, 30),    (160, 30, 30), (80, 25, 25),   "INFERNO"),
}

# Cache of generated map thumbnails so we don't regenerate every frame
_MAP_THUMB_CACHE = {}

def _theme_for_level(level):
    """Mirror Game.get_theme_for_level for module level helpers."""
    themes = ["jungle", "default", "desert", "kawaii_woodland",
              "snow", "city", "lava"]
    return themes[(level - 1) % len(themes)]

def build_map_thumbnail(theme, w=200, h=130, level_seed=0):
    """Return a Surface that visualises what a level of this theme looks like.
    Uses procedural drawing — no external assets required."""
    key = (theme, w, h, level_seed)
    if key in _MAP_THUMB_CACHE:
        return _MAP_THUMB_CACHE[key]

    info = MAP_THEME_DEFS.get(theme, MAP_THEME_DEFS["default"])
    name, sky, deco, wall, terrain, _ = info

    surf = pygame.Surface((w, h)).convert()
    # Soft vertical gradient sky
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = (int(sky[0] * (1 - t * 0.35)), int(sky[1] * (1 - t * 0.35)),
             int(sky[2] * (1 - t * 0.35)))
        pygame.draw.line(surf, c, (0, yy), (w, yy))

    rng = random.Random(level_seed * 137 + hash(theme) % 9999)
    cols = 18
    rows = 12
    cw = w / cols
    ch = h / rows

    # Floor speckle
    for r in range(rows):
        for c in range(cols):
            if rng.random() < 0.25:
                x = int(c * cw)
                y = int(r * ch)
                shade = rng.randint(-15, 15)
                col = (max(0, min(255, terrain[0] + shade)),
                       max(0, min(255, terrain[1] + shade)),
                       max(0, min(255, terrain[2] + shade)))
                pygame.draw.rect(surf, col, (x, y, int(cw) + 1, int(ch) + 1))

    # Brick walls (small clusters)
    for _ in range(rng.randint(6, 12)):
        bx = rng.randint(1, cols - 3)
        by = rng.randint(1, rows - 3)
        bw_t = rng.randint(2, 4)
        bh_t = rng.randint(1, 2)
        for dx in range(bw_t):
            for dy in range(bh_t):
                if bx + dx >= cols or by + dy >= rows:
                    continue
                x = int((bx + dx) * cw)
                y = int((by + dy) * ch)
                pygame.draw.rect(surf, wall, (x, y, int(cw), int(ch)))
                pygame.draw.rect(surf, (max(0, wall[0] - 30), max(0, wall[1] - 30), max(0, wall[2] - 30)),
                                 (x, y, int(cw), int(ch)), 1)

    # Steel / metal blocks
    steel = (170, 175, 180) if theme != "lava" else (200, 100, 60)
    for _ in range(rng.randint(2, 4)):
        sx = rng.randint(1, cols - 2)
        sy = rng.randint(1, rows - 2)
        x = int(sx * cw)
        y = int(sy * ch)
        pygame.draw.rect(surf, steel, (x, y, int(cw), int(ch)))
        pygame.draw.rect(surf, (90, 95, 100), (x, y, int(cw), int(ch)), 1)

    # Water / lava pool
    pool_col = (60, 130, 220) if theme not in ("lava", "desert") else \
               ((230, 90, 30) if theme == "lava" else (180, 150, 80))
    px = rng.randint(2, cols - 5)
    py = rng.randint(rows - 5, rows - 3)
    pw_t = rng.randint(3, 5)
    ph_t = 2
    pygame.draw.rect(surf, pool_col,
                     (int(px * cw), int(py * ch), int(pw_t * cw), int(ph_t * ch)))

    # Grass tufts
    if theme in ("jungle", "kawaii_woodland", "default"):
        for _ in range(rng.randint(6, 10)):
            gx = rng.randint(0, cols - 1)
            gy = rng.randint(0, rows - 1)
            pygame.draw.circle(surf, (60, 150, 80),
                               (int(gx * cw + cw / 2), int(gy * ch + ch / 2)),
                               max(2, int(cw * 0.35)))

    # Player base (golden eagle dot near bottom)
    bx = int((cols // 2) * cw)
    by = int((rows - 2) * ch)
    pygame.draw.rect(surf, (235, 210, 80), (bx, by, int(cw * 1.5), int(ch * 1.5)))
    pygame.draw.rect(surf, (140, 110, 40), (bx, by, int(cw * 1.5), int(ch * 1.5)), 1)

    # Enemy markers (red dots near top)
    for _ in range(3):
        ex = rng.randint(2, cols - 3)
        ey = rng.randint(1, 3)
        pygame.draw.circle(surf, (235, 80, 80),
                           (int(ex * cw + cw / 2), int(ey * ch + ch / 2)),
                           max(2, int(cw * 0.30)))

    # Theme tint overlay
    tint = pygame.Surface((w, h), pygame.SRCALPHA)
    tint.fill((sky[0], sky[1], sky[2], 30))
    surf.blit(tint, (0, 0))

    # Soft border / frame
    pygame.draw.rect(surf, (255, 255, 255), (0, 0, w, h), 1)

    _MAP_THUMB_CACHE[key] = surf
    return surf


def apply_audio_settings(settings):
    """Apply master/music/sfx volume sliders to the actual mixer."""
    master = max(0.0, min(1.0, settings.get("master_volume", 80) / 100.0))
    music_v = max(0.0, min(1.0, settings.get("music_volume", 60) / 100.0))
    sfx_v = max(0.0, min(1.0, settings.get("sfx_volume", 80) / 100.0))
    try:
        pygame.mixer.music.set_volume(master * music_v)
    except Exception:
        pass
    for s in _ALL_SFX:
        try:
            base = _BASE_SFX_VOL.get(id(s), 1.0)
            s.set_volume(master * sfx_v * base / 0.85 if base else master * sfx_v)
        except Exception:
            pass


def apply_video_settings(settings):
    """Apply window/fullscreen/resolution settings."""
    global is_fullscreen, phys_w, phys_h, screen
    target_full = bool(settings.get("fullscreen", False))
    idx = max(0, min(len(RESOLUTION_PRESETS) - 1, settings.get("resolution_idx", 0)))
    rw, rh = RESOLUTION_PRESETS[idx]
    try:
        if target_full:
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
            phys_w = desktop_w
            phys_h = desktop_h
            screen = pygame.display.set_mode((phys_w, phys_h), flags)
            is_fullscreen = True
        else:
            flags = pygame.RESIZABLE
            phys_w = min(rw, desktop_w)
            phys_h = min(rh, desktop_h)
            screen = pygame.display.set_mode((phys_w, phys_h), flags)
            is_fullscreen = False
    except Exception as _e:
        print("apply_video_settings:", _e)


# ═══════════════════════════════════════
#  WEATHER SYSTEM
# ═══════════════════════════════════════
class WeatherSystem:
    def __init__(self):
        self.particles = []
        self.weather_type = None
        self.intensity = 50

    def set_weather(self, theme):
        self.particles.clear()
        if theme == "snow":
            self.weather_type = "snow"
            self.intensity = 60
        elif theme == "desert":
            self.weather_type = "sand"
            self.intensity = 30
        elif theme == "jungle":
            self.weather_type = "rain"
            self.intensity = 50
        elif theme == "lava":
            self.weather_type = "ember"
            self.intensity = 25
        else:
            self.weather_type = None

    def update(self):
        if not self.weather_type:
            return

        while len(self.particles) < self.intensity:
            if self.weather_type == "snow":
                self.particles.append({
                    'x': random.randint(0, SW), 'y': random.randint(-20, 0),
                    'vx': random.uniform(-0.5, 0.5), 'vy': random.uniform(0.5, 2),
                    'size': random.randint(2, 4), 'alpha': random.randint(100, 200)
                })
            elif self.weather_type == "rain":
                self.particles.append({
                    'x': random.randint(0, SW), 'y': random.randint(-30, 0),
                    'vx': random.uniform(-1, 0), 'vy': random.uniform(6, 12),
                    'size': random.randint(1, 2), 'alpha': random.randint(80, 150)
                })
            elif self.weather_type == "sand":
                self.particles.append({
                    'x': random.randint(-20, 0), 'y': random.randint(0, SH),
                    'vx': random.uniform(2, 5), 'vy': random.uniform(-0.5, 0.5),
                    'size': random.randint(1, 3), 'alpha': random.randint(60, 120)
                })
            elif self.weather_type == "ember":
                self.particles.append({
                    'x': random.randint(0, SW), 'y': random.randint(SH, SH + 20),
                    'vx': random.uniform(-0.5, 0.5), 'vy': random.uniform(-2, -0.5),
                    'size': random.randint(1, 3), 'alpha': random.randint(100, 200)
                })

        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if self.weather_type == "snow":
                p['x'] += math.sin(p['y'] * 0.02) * 0.5
            if (p['y'] > SH + 10 or p['y'] < -30 or p['x'] > SW + 10 or p['x'] < -30):
                self.particles.remove(p)

    def draw(self, surf):
        if not self.weather_type:
            return
        for p in self.particles:
            if self.weather_type == "snow":
                c = (230, 235, 255, p['alpha'])
            elif self.weather_type == "rain":
                c = (150, 180, 255, p['alpha'])
            elif self.weather_type == "sand":
                c = (200, 180, 140, p['alpha'])
            elif self.weather_type == "ember":
                c = (255, random.randint(100, 200), 50, p['alpha'])
            else:
                continue
            ps = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            if self.weather_type == "rain":
                pygame.draw.line(ps, c, (p['size'], 0), (0, p['size'] * 2), 1)
            else:
                pygame.draw.circle(ps, c, (p['size'], p['size']), p['size'])
            surf.blit(ps, (int(p['x']), int(p['y'])))

weather = WeatherSystem()

# ═══════════════════════════════════════
#  ACHIEVEMENT SYSTEM
# ═══════════════════════════════════════
class Achievement:
    def __init__(self, name, desc, icon_color):
        self.name = name
        self.desc = desc
        self.icon_color = icon_color
        self.timer = 180
        self.y_offset = -60

achievement_queue = []

def trigger_achievement(name, desc, color=(255, 220, 50)):
    achievement_queue.append(Achievement(name, desc, color))

# ═══════════════════════════════════════
#  PATHFINDER
# ═══════════════════════════════════════
class Pathfinder:
    @staticmethod
    def a_star_path(grid, start, goal, avoid_tanks=None):
        if start == goal: return [start]
        pq = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}

        while pq:
            _, current = heapq.heappop(pq)
            if current == goal: break
            for dx, dy in DIRS:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS:
                    tile = grid[neighbor[1]][neighbor[0]]
                    if tile in (STEEL, WATER, BASE): continue
                    move_cost = 1
                    if tile in (BRICK, CRATE): move_cost = 8
                    if avoid_tanks and neighbor in avoid_tanks and neighbor != start:
                        move_cost += 5
                    new_cost = cost_so_far[current] + move_cost
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                        heapq.heappush(pq, (priority, neighbor))
                        came_from[neighbor] = current

        path = []
        c = goal
        while c is not None and c in came_from:
            path.append(c)
            c = came_from[c]
        path.reverse()
        return path if path and path[0] == start else [start]

    @staticmethod
    def bfs_path(grid, start, goal, avoid_tanks=None):
        if start == goal: return [start]
        queue = collections.deque([start])
        came_from = {start: None}
        blocked = {STEEL, WATER, BASE, BRICK, CRATE}
        while queue:
            current = queue.popleft()
            if current == goal: break
            for dx, dy in DIRS:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS:
                    if neighbor not in came_from:
                        tile = grid[neighbor[1]][neighbor[0]]
                        is_blocked = tile in blocked
                        if avoid_tanks and neighbor in avoid_tanks: is_blocked = True
                        if neighbor == goal: is_blocked = False
                        if not is_blocked:
                            queue.append(neighbor)
                            came_from[neighbor] = current
        path = []
        c = goal
        while c is not None and c in came_from:
            path.append(c)
            c = came_from[c]
        path.reverse()
        return path if path and path[0] == start else [start]

    @staticmethod
    def dfs_path(grid, start, goal, avoid_tanks=None):
        if start == goal: return [start]
        stack = [start]
        came_from = {start: None}
        blocked = {STEEL, WATER, BASE, BRICK, CRATE}
        while stack:
            current = stack.pop()
            if current == goal: break
            for dx, dy in DIRS:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS:
                    if neighbor not in came_from:
                        tile = grid[neighbor[1]][neighbor[0]]
                        is_blocked = tile in blocked
                        if avoid_tanks and neighbor in avoid_tanks: is_blocked = True
                        if neighbor == goal: is_blocked = False
                        if not is_blocked:
                            stack.append(neighbor)
                            came_from[neighbor] = current
        path = []
        c = goal
        while c is not None and c in came_from:
            path.append(c)
            c = came_from[c]
        path.reverse()
        return path if path and path[0] == start else [start]

    @staticmethod
    def can_shoot(grid, sx, sy, tx, ty):
        if sx == tx:
            step = 1 if ty > sy else -1
            for y in range(sy + step, ty, step):
                if grid[y][sx] in (STEEL, WATER, BASE): return False
            return True
        if sy == ty:
            step = 1 if tx > sx else -1
            for x in range(sx + step, tx, step):
                if grid[sy][x] in (STEEL, WATER, BASE): return False
            return True
        return False

    @staticmethod
    def get_next_direction(current_pos, next_pos):
        cx, cy = current_pos
        nx, ny = next_pos
        if nx > cx: return 1
        if nx < cx: return 3
        if ny > cy: return 2
        if ny < cy: return 0
        return -1

    @staticmethod
    def get_safe_directions(grid, x, y):
        gx, gy = int(x // TS), int(y // TS)
        blocked = {STEEL, WATER, BASE}
        safe = []
        for d in range(4):
            dx, dy = DIRS[d]
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                if grid[ny][nx] not in blocked:
                    safe.append(d)
        return safe

# ═══════════════════════════════════════
#  MAP GENERATOR (THEMED)
# ═══════════════════════════════════════
def generate_map(level=1, cols=26, rows=20):
    """Build the playable grid for a level.  Each of the 20 levels now
    has its own hand-tuned blueprint so the in-game terrain matches the
    small preview thumbnail on the world-map screen — jungle has trees,
    desert has cacti, city has fortress walls, snow has icy water +
    rocky pillars, and the lava finale has chaotic obstacles."""
    global COLS, ROWS
    COLS, ROWS = cols, rows
    grid = [[EMPTY] * cols for _ in range(rows)]

    # Outer steel wall border
    for x in range(cols):
        grid[0][x] = STEEL
        grid[rows - 1][x] = STEEL
    for y in range(rows):
        grid[y][0] = STEEL
        grid[y][cols - 1] = STEEL

    bx, by = cols // 2, rows - 3
    # Player base (heart star crest) removed as requested by the user
    grid[by][bx] = EMPTY

    def is_protected(px, py):
        # Keep spawn / base / corridor clear so the level is playable.
        if py <= 2: return True
        if py >= rows - 4 and abs(px - bx) <= 3: return True
        if py == rows - 2 or py == rows - 3: return True
        if py <= 3 and (px <= 3 or px >= cols - 4): return True
        return False

    def safe_set(x, y, t):
        if 1 <= x < cols - 1 and 1 <= y < rows - 1 \
                and grid[y][x] == EMPTY and not is_protected(x, y):
            grid[y][x] = t

    def cluster(cx, cy, r, t, density=0.7):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r and random.random() < density:
                    safe_set(cx + dx, cy + dy, t)

    def line(x0, y0, x1, y1, t):
        if x0 == x1:
            for y in range(min(y0, y1), max(y0, y1) + 1):
                safe_set(x0, y, t)
        elif y0 == y1:
            for x in range(min(x0, x1), max(x0, x1) + 1):
                safe_set(x, y0, t)

    def filled(x0, y0, w, h, t):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                safe_set(x, y, t)

    def hollow(x0, y0, w, h, t):
        # Outline rectangle (fortress walls)
        for x in range(x0, x0 + w):
            safe_set(x, y0, t)
            safe_set(x, y0 + h - 1, t)
        for y in range(y0, y0 + h):
            safe_set(x0, y, t)
            safe_set(x0 + w - 1, y, t)

    # Seed RNG with level so each map is consistent across runs.
    random.seed(0xCAFE + level)

    cx_mid = cols // 2
    cy_mid = rows // 2
    theme = {
        1: "jungle_start",  2: "open_road",       3: "desert_intro",
        4: "stone_fort",    5: "fortress_boss",
        6: "mountain_pass", 7: "river_crossing",  8: "wild_woods",
        9: "highland",     10: "city_boss",
        11: "village",     12: "bridge_gate",    13: "tribal_village",
        14: "snow_mountain", 15: "river_boss",
        16: "ruins",       17: "ice_field",      18: "castle_gate",
        19: "wasteland",   20: "lava_inferno",
    }.get(level, "open_road")

    if theme == "jungle_start":
        # A few scattered tree clusters + a brick hut or two
        for _ in range(8):
            cluster(random.randint(4, cols - 5), random.randint(4, rows - 6),
                    2, GRASS, 0.6)
        for _ in range(3):
            ox, oy = random.randint(4, cols - 6), random.randint(4, rows - 6)
            filled(ox, oy, 2, 2, BRICK)

    elif theme == "open_road":
        # Sparse cover for a "march" vibe — two parallel hedgerows
        for x in range(4, cols - 4, 4):
            safe_set(x, 5, GRASS); safe_set(x, 6, GRASS)
            safe_set(x, rows - 7, GRASS); safe_set(x, rows - 8, GRASS)
        for _ in range(5):
            cluster(random.randint(4, cols - 5),
                    random.randint(8, rows - 8), 1, BRICK, 1.0)

    elif theme == "desert_intro":
        # Wide open with sparse cacti (GRASS used as cactus) + small ruins
        for _ in range(14):
            x = random.randint(2, cols - 3); y = random.randint(3, rows - 5)
            safe_set(x, y, GRASS)
        for _ in range(4):
            ox = random.randint(3, cols - 5); oy = random.randint(3, rows - 6)
            hollow(ox, oy, 3, 2, BRICK)

    elif theme == "stone_fort":
        # Symmetric stone fortress walls (castle outline)
        hollow(4, 3, cols - 8, rows - 8, STEEL)
        # Gate opening front and back
        for x in range(cx_mid - 1, cx_mid + 2):
            grid[3][x] = EMPTY
            grid[rows - 6][x] = EMPTY if grid[rows-6][x] == STEEL else grid[rows-6][x]
        # Inner BRICK rooms
        for ox in (6, cols - 11):
            filled(ox, 5, 4, 3, BRICK)
        # Two flanking towers
        for ox in (3, cols - 5):
            filled(ox, 3, 2, 3, STEEL)

    elif theme == "fortress_boss":
        # Big symmetric castle for boss 5: outer + inner walls
        hollow(3, 2, cols - 6, rows - 7, STEEL)
        hollow(7, 5, cols - 14, rows - 13, STEEL)
        # Open gates
        for x in range(cx_mid - 1, cx_mid + 2):
            grid[2][x] = EMPTY
            grid[5][x] = EMPTY
        # Corner towers
        for ox, oy in ((2, 1), (cols - 5, 1), (2, rows - 6), (cols - 5, rows - 6)):
            filled(ox, oy, 3, 3, STEEL)
        # Crates inside
        for _ in range(4):
            safe_set(random.randint(8, cols - 9), random.randint(6, rows - 8), CRATE)

    elif theme == "mountain_pass":
        # A narrow corridor — steel mountains on left+right sides
        for y in range(3, rows - 4):
            for x in range(1, 5):
                safe_set(x, y, STEEL)
            for x in range(cols - 5, cols - 1):
                safe_set(x, y, STEEL)
        # Inside the pass: jungle trees
        for _ in range(10):
            cluster(random.randint(6, cols - 7), random.randint(4, rows - 6),
                    1, GRASS, 0.8)

    elif theme == "river_crossing":
        # Horizontal river through the middle with 2-3 bridges
        rw_y = cy_mid
        for x in range(2, cols - 2):
            safe_set(x, rw_y, WATER)
            safe_set(x, rw_y + 1, WATER)
        bridges = [cols // 4, cx_mid, 3 * cols // 4]
        for bxx in bridges:
            grid[rw_y][bxx] = EMPTY
            grid[rw_y + 1][bxx] = EMPTY
        # Small brick outposts on each shore
        for ox in (cols // 4 - 2, 3 * cols // 4):
            filled(ox, rw_y - 3, 3, 2, BRICK)
            filled(ox, rw_y + 3, 3, 2, BRICK)

    elif theme == "wild_woods":
        # Dense jungle: many GRASS clusters
        for _ in range(14):
            cluster(random.randint(3, cols - 4), random.randint(3, rows - 5),
                    2, GRASS, 0.75)
        # Few brick outposts
        for _ in range(2):
            ox = random.randint(4, cols - 6); oy = random.randint(4, rows - 7)
            filled(ox, oy, 2, 2, BRICK)

    elif theme == "highland":
        # Elevated steel "plateaus" + green patches
        for _ in range(4):
            ox = random.randint(3, cols - 7); oy = random.randint(3, rows - 7)
            filled(ox, oy, 3, 3, STEEL)
        for _ in range(6):
            cluster(random.randint(4, cols - 5), random.randint(4, rows - 6),
                    1, GRASS, 0.7)

    elif theme == "city_boss":
        # Hard boss 10 — densely-built city
        # Outer wall
        hollow(2, 2, cols - 4, rows - 6, STEEL)
        # Inner streets (cross pattern in BRICK)
        for x in range(4, cols - 4):
            if x % 5 != 0:
                safe_set(x, cy_mid - 2, BRICK)
                safe_set(x, cy_mid + 2, BRICK)
        for y in range(4, rows - 6):
            if y % 4 != 0:
                safe_set(cx_mid - 4, y, BRICK)
                safe_set(cx_mid + 4, y, BRICK)
        # Watchtowers
        for ox in (4, cols - 6):
            filled(ox, 3, 2, 2, STEEL)

    elif theme == "village":
        # Multiple small brick "houses" + a few green plots
        for _ in range(7):
            ox = random.randint(3, cols - 6); oy = random.randint(3, rows - 8)
            # House (3x2 brick) with a green plot beside it
            filled(ox, oy, 3, 2, BRICK)
            safe_set(ox + 4, oy, GRASS)
            safe_set(ox + 4, oy + 1, GRASS)
        for _ in range(4):
            cluster(random.randint(3, cols - 4), random.randint(3, rows - 5),
                    1, GRASS, 0.7)

    elif theme == "bridge_gate":
        # A river running diagonally with a gate of steel + bricks
        for x in range(2, cols - 2):
            safe_set(x, cy_mid + 2, WATER)
        grid[cy_mid + 2][cx_mid] = EMPTY
        grid[cy_mid + 2][cx_mid - 3] = EMPTY
        grid[cy_mid + 2][cx_mid + 3] = EMPTY
        # Gate walls on either side of base
        for y in range(rows - 8, rows - 4):
            safe_set(cx_mid - 4, y, STEEL)
            safe_set(cx_mid + 4, y, STEEL)
        # Brick hedgerows
        for ox in (4, cols - 7):
            filled(ox, cy_mid - 3, 3, 2, BRICK)

    elif theme == "tribal_village":
        # Dense BRICK huts laid out around a green common area
        for ox, oy in [(4, 4), (10, 4), (16, 4), (cols - 9, 4),
                       (4, rows - 8), (10, rows - 8), (cols - 9, rows - 8)]:
            filled(ox, oy, 2, 2, BRICK)
        cluster(cx_mid, cy_mid - 1, 3, GRASS, 0.7)
        for _ in range(5):
            cluster(random.randint(3, cols - 4), random.randint(3, rows - 5),
                    1, GRASS, 0.8)

    elif theme == "snow_mountain":
        # Tall steel "mountains" + sparse pine trees
        for ox in (3, 7, cols - 9, cols - 5):
            filled(ox, 2, 2, 4, STEEL)
        for ox in (5, cols - 7):
            filled(ox, rows - 8, 2, 3, STEEL)
        for _ in range(10):
            cluster(random.randint(4, cols - 5), random.randint(4, rows - 6),
                    1, GRASS, 0.5)

    elif theme == "river_boss":
        # Boss with a big horizontal water with steel platforms
        for x in range(2, cols - 2):
            safe_set(x, cy_mid - 1, WATER)
            safe_set(x, cy_mid, WATER)
            safe_set(x, cy_mid + 1, WATER)
        # 4 steel "stepping stones" platforms
        for bxx in (5, cx_mid - 4, cx_mid + 3, cols - 7):
            for dx in range(2):
                grid[cy_mid - 1][bxx + dx] = EMPTY
                grid[cy_mid][bxx + dx] = STEEL
                grid[cy_mid + 1][bxx + dx] = EMPTY
        # Brick fort behind base
        hollow(cx_mid - 3, rows - 7, 7, 3, BRICK)

    elif theme == "ruins":
        # Broken brick walls everywhere — like a destroyed city
        for _ in range(12):
            ox = random.randint(2, cols - 5); oy = random.randint(3, rows - 6)
            length = random.randint(2, 5)
            if random.random() < 0.5:
                line(ox, oy, ox + length, oy, BRICK)
            else:
                line(ox, oy, ox, oy + length, BRICK)
        for _ in range(4):
            safe_set(random.randint(3, cols - 4),
                     random.randint(3, rows - 5), STEEL)
        for _ in range(5):
            safe_set(random.randint(3, cols - 4),
                     random.randint(3, rows - 5), CRATE)

    elif theme == "ice_field":
        # Big icy water patches + sparse steel rocks
        for _ in range(6):
            ox = random.randint(3, cols - 7); oy = random.randint(3, rows - 7)
            filled(ox, oy, random.randint(3, 5),
                       random.randint(2, 3), WATER)
        for _ in range(8):
            safe_set(random.randint(3, cols - 4),
                     random.randint(3, rows - 5), STEEL)

    elif theme == "castle_gate":
        # A tall stone gate in the middle of the level
        for y in range(2, rows - 4):
            safe_set(cx_mid - 6, y, STEEL)
            safe_set(cx_mid + 6, y, STEEL)
        # Gate doors (brick)
        for x in range(cx_mid - 1, cx_mid + 2):
            safe_set(x, cy_mid - 1, BRICK)
            safe_set(x, cy_mid, BRICK)
            safe_set(x, cy_mid + 1, BRICK)
        # Towers
        for ox in (cx_mid - 7, cx_mid + 6):
            filled(ox, 2, 2, 3, STEEL)
        # Outer flanks
        for x in range(3, cx_mid - 8):
            safe_set(x, rows - 7, BRICK)
        for x in range(cx_mid + 9, cols - 3):
            safe_set(x, rows - 7, BRICK)

    elif theme == "wasteland":
        # Very open desert with a single hardpoint of broken walls
        for _ in range(10):
            safe_set(random.randint(2, cols - 3),
                     random.randint(3, rows - 5), GRASS)
        for _ in range(5):
            ox = random.randint(4, cols - 6); oy = random.randint(4, rows - 6)
            line(ox, oy, ox + 3, oy, BRICK)
        # Small ruined hut
        hollow(cx_mid - 2, cy_mid - 1, 4, 3, BRICK)

    elif theme == "lava_inferno":
        # Final boss — chaotic steel pillars + lava (WATER) pools
        for _ in range(8):
            ox = random.randint(3, cols - 4); oy = random.randint(3, rows - 5)
            filled(ox, oy, 1, 1, STEEL)
        for _ in range(6):
            ox = random.randint(4, cols - 6); oy = random.randint(4, rows - 6)
            filled(ox, oy, random.randint(2, 4),
                       random.randint(1, 2), WATER)
        # Big central forge — steel arena
        hollow(cx_mid - 5, cy_mid - 3, 11, 7, STEEL)
        for x in range(cx_mid - 4, cx_mid + 5):
            grid[cy_mid - 3][x] = EMPTY if random.random() < 0.5 else STEEL

    # Base protection walls removed as the base is gone
    pass

    # ── BFS REACHABILITY VALIDATION ───────────────────────────────
    # Goal: every EMPTY cell must be drivable from the base / from at
    # least one spawn corner, and the 3 spawn corners must be able to
    # reach the base.  We do this with a flood-fill + "punch holes"
    # repair pass.

    def _flood(start_set):
        seen = set()
        q = collections.deque()
        for a in start_set:
            if (0 <= a[0] < cols and 0 <= a[1] < rows
                    and grid[a[1]][a[0]] in (EMPTY, BASE)):
                seen.add(a); q.append(a)
        while q:
            x, y = q.popleft()
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in seen:
                    if grid[ny][nx] == EMPTY:
                        seen.add((nx, ny)); q.append((nx, ny))
        return seen

    def _punch_corridor(x0, y0, x1, y1):
        # Carve an L-shaped corridor (vertical then horizontal) by
        # turning STEEL/BRICK/CRATE into EMPTY along the path.  Avoids
        # touching the base tile.
        x, y = x0, y0
        while y != y1:
            step = 1 if y1 > y else -1
            y += step
            if 1 <= x < cols - 1 and 1 <= y < rows - 1 \
                    and grid[y][x] != BASE:
                grid[y][x] = EMPTY
        while x != x1:
            step = 1 if x1 > x else -1
            x += step
            if 1 <= x < cols - 1 and 1 <= y < rows - 1 \
                    and grid[y][x] != BASE:
                grid[y][x] = EMPTY

    # Pick approach tile in front of base (one row above).  Always
    # carve a corridor from this tile up to the top spawn row so we
    # never have a level where the base is completely walled off.
    approach = (bx, by - 1)
    if grid[approach[1]][approach[0]] != BASE:
        grid[approach[1]][approach[0]] = EMPTY

    # Reserved spawn anchors near each corner / centre of the top row.
    spawn_targets = [(2, 2), (cols - 3, 2), (cols // 2, 2)]
    for sx, sy in spawn_targets:
        # Ensure the spawn tile itself is EMPTY (unless inside the
        # outer steel border, in which case shift inward).
        ax, ay = sx, sy
        if ax <= 0: ax = 1
        if ax >= cols - 1: ax = cols - 2
        if ay <= 0: ay = 1
        if ay >= rows - 1: ay = rows - 2
        if grid[ay][ax] != BASE:
            grid[ay][ax] = EMPTY
        # Carve an L-corridor from this spawn to the base approach.
        _punch_corridor(ax, ay, approach[0], approach[1])

    # Now flood-fill from the base approach + spawns to find what's
    # reachable.  Any EMPTY cell still cut off gets a punch through to
    # the nearest reachable cell.
    seed = [approach] + spawn_targets
    reachable = _flood(seed)

    # Repair pass: for each isolated EMPTY cell, BFS through walls to
    # find the nearest reachable cell, then clear the wall path.
    def _break_to_reach(target):
        seen = {target: None}
        q = collections.deque([target])
        connect = None
        while q:
            cx, cy = q.popleft()
            if (cx, cy) in reachable:
                connect = (cx, cy); break
            for dx, dy in DIRS:
                nx, ny = cx + dx, cy + dy
                if 1 <= nx < cols - 1 and 1 <= ny < rows - 1 \
                        and (nx, ny) not in seen:
                    if grid[ny][nx] != BASE:
                        seen[(nx, ny)] = (cx, cy); q.append((nx, ny))
        if connect is None:
            return
        cur = connect
        while cur is not None and cur != target:
            prev = seen.get(cur)
            if prev is None:
                break
            if grid[prev[1]][prev[0]] not in (EMPTY, BASE):
                grid[prev[1]][prev[0]] = EMPTY
            cur = prev

    guard = 0
    while guard < 60:
        isolated = [(x, y)
                    for y in range(1, rows - 1)
                    for x in range(1, cols - 1)
                    if grid[y][x] == EMPTY and (x, y) not in reachable]
        if not isolated:
            break
        _break_to_reach(isolated[0])
        reachable = _flood(seed)
        guard += 1

    # A few extra crates spread around for power-ups (only on EMPTY).
    for _ in range(3 + level // 3):
        cx2 = random.randint(2, cols - 3)
        cy2 = random.randint(2, rows - 4)
        if grid[cy2][cx2] == EMPTY and (cx2, cy2) in reachable:
            grid[cy2][cx2] = CRATE

    # Restore RNG to non-seeded for downstream uses.
    random.seed()

    return grid, (bx, by)

# ═══════════════════════════════════════
#  BULLET
# ═══════════════════════════════════════
class Bullet:
    def __init__(self, x, y, direction, owner, speed=6, power=1, kind="normal", angle_offset=0, custom_angle=None):
        self.x, self.y = float(x), float(y)
        self.dir = direction
        self.owner = owner
        self.speed = speed
        self.power = power
        self.kind = kind
        self.alive = True
        self.angle_offset = angle_offset
        self.custom_angle = custom_angle
        self.trail = []
        self.lifetime = 0
        if kind == "rocket":
            self.speed = 3
            self.power = 4
        elif kind == "flame":
            self.speed = 4
            self.power = 2

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.lifetime += 1

        if self.custom_angle is not None:
            self.x += math.cos(self.custom_angle) * self.speed
            self.y += math.sin(self.custom_angle) * self.speed
        else:
            dx, dy = DIRS[self.dir]
            if self.angle_offset != 0:
                rad = math.radians(self.angle_offset)
                nx = dx * math.cos(rad) - dy * math.sin(rad)
                ny = dx * math.sin(rad) + dy * math.cos(rad)
                self.x += nx * self.speed
                self.y += ny * self.speed
            else:
                self.x += dx * self.speed
                self.y += dy * self.speed

        if self.kind == "rocket" and self.lifetime < 30:
            self.speed = min(self.speed + 0.3, 10)
        if self.kind == "flame" and self.lifetime > 20:
            self.alive = False

        if self.x < -100 or self.x >= COLS * TS + 100 or self.y < -100 or self.y >= ROWS * TS + 100:
            self.alive = False

    def get_grid(self):
        return int(self.x // TS), int(self.y // TS)

    def draw(self, surf, offset=(0, 0), scale=1.0):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            dtx = int((tx - offset[0]) * scale)
            dty = int((ty - offset[1]) * scale)
            a = int(60 * (i / max(1, len(self.trail))))
            sz = max(1, int(2 * scale * (i / max(1, len(self.trail)))))
            trail_c = (255, 200, 50) if self.owner == "player" else (255, 100, 80)
            ts = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*trail_c, a), (sz, sz), sz)
            surf.blit(ts, (dtx - sz, dty - sz))

        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)

        img = sprites.bullet
        if self.owner != "player": img = sprites.bullet_enemy
        if self.kind == "pierce": img = sprites.bullet_pierce
        if self.kind == "bomb": img = sprites.bullet_bomb
        if self.kind == "laser": img = sprites.bullet_laser
        if self.kind == "plasma": img = sprites.bullet_plasma
        if self.kind == "rocket": img = getattr(sprites, 'bullet_rocket', sprites.bullet_bomb)
        if self.kind == "flame": img = getattr(sprites, 'bullet_flame', sprites.bullet_laser)

        if scale != 1.0:
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

# ═══════════════════════════════════════
#  PET SYSTEM
# ═══════════════════════════════════════
PET_TYPES = {
    "wolf": {"name": "SÓI CHIẾN", "skill": "attack", "desc": "Tự bắn kẻ địch gần nhất",
             "color": (140, 140, 160), "cooldown": 90, "cost": 2000, "gem_cost": 0},
    "dragon": {"name": "RỒNG LỬA", "skill": "fireball", "desc": "Phun cầu lửa mạnh mẽ",
               "color": (255, 80, 30), "cooldown": 120, "cost": 5000, "gem_cost": 0},
    "healer": {"name": "TIÊN HỒI MÁU", "skill": "heal", "desc": "Tự hồi máu cho chủ",
               "color": (255, 180, 200), "cooldown": 300, "cost": 3000, "gem_cost": 0},
    "shield_bot": {"name": "ROBOT KHIÊN", "skill": "shield", "desc": "Tăng giáp định kỳ",
                   "color": (80, 150, 255), "cooldown": 360, "cost": 3500, "gem_cost": 0},
    "magnet": {"name": "NAM CHÂM", "skill": "magnet", "desc": "Hút vàng & item gần đó",
               "color": (255, 220, 50), "cooldown": 0, "cost": 1500, "gem_cost": 0},
    "ghost": {"name": "MA BÓNG", "skill": "freeze", "desc": "Đóng băng kẻ địch gần nhất",
              "color": (180, 220, 255), "cooldown": 240, "cost": 4000, "gem_cost": 0},
}

class Pet:
    def __init__(self, pet_type, owner):
        self.pet_type = pet_type
        self.info = PET_TYPES[pet_type]
        self.owner = owner
        self.x = float(owner.x - 20)
        self.y = float(owner.y - 20)
        self.skill_cd = 0
        self.alive = True
        self.frame = 0
        self.bob_offset = 0

    def update(self, enemies, items, game):
        if not self.alive or not self.owner.alive:
            return []

        self.frame += 1
        self.bob_offset = math.sin(self.frame * 0.1) * 3

        # Follow owner smoothly
        tx = self.owner.x - 18
        ty = self.owner.y - 18
        self.x += (tx - self.x) * 0.08
        self.y += (ty - self.y) * 0.08

        if self.skill_cd > 0:
            self.skill_cd -= 1

        results = []
        skill = self.info["skill"]

        if self.skill_cd <= 0:
            if skill == "attack":
                nearest = self._find_nearest_enemy(enemies, 200)
                if nearest:
                    dx = nearest.x - self.x
                    dy = nearest.y - self.y
                    d = max(1, math.hypot(dx, dy))
                    bdir = 0
                    if abs(dx) > abs(dy):
                        bdir = 1 if dx > 0 else 3
                    else:
                        bdir = 2 if dy > 0 else 0
                    results.append(Bullet(self.x, self.y, bdir, "player", 7, 1, kind="normal"))
                    self.skill_cd = self.info["cooldown"]

            elif skill == "fireball":
                nearest = self._find_nearest_enemy(enemies, 250)
                if nearest:
                    dx = nearest.x - self.x
                    dy = nearest.y - self.y
                    bdir = 0
                    if abs(dx) > abs(dy):
                        bdir = 1 if dx > 0 else 3
                    else:
                        bdir = 2 if dy > 0 else 0
                    results.append(Bullet(self.x, self.y, bdir, "player", 5, 3, kind="flame"))
                    self.skill_cd = self.info["cooldown"]

            elif skill == "heal":
                if self.owner.hp < self.owner.max_hp:
                    self.owner.hp = min(self.owner.max_hp, self.owner.hp + 1)
                    self.skill_cd = self.info["cooldown"]

            elif skill == "shield":
                if self.owner.shield < 3:
                    self.owner.shield += 1
                    self.skill_cd = self.info["cooldown"]

            elif skill == "freeze":
                nearest = self._find_nearest_enemy(enemies, 150)
                if nearest:
                    nearest.frozen_timer = max(nearest.frozen_timer, 120)
                    self.skill_cd = self.info["cooldown"]

            elif skill == "magnet":
                for item in items:
                    if item.alive:
                        dist = math.hypot(item.x - self.owner.x, item.y - self.owner.y)
                        if dist < 150:
                            item.x += (self.owner.x - item.x) * 0.1
                            item.y += (self.owner.y - item.y) * 0.1

        return results

    def _find_nearest_enemy(self, enemies, max_dist):
        nearest = None
        min_d = max_dist
        for e in enemies:
            if e.alive and e.spawn_timer <= 0:
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < min_d:
                    min_d = d
                    nearest = e
        return nearest

    def draw(self, surf, offset=(0, 0), scale=1.0):
        dx = int((self.x - offset[0]) * scale)
        dy = int((self.y + self.bob_offset - offset[1]) * scale)
        c = self.info["color"]
        size = int(10 * scale)

        # Use sprite if available
        is_attacking = self.skill_cd > 0 and self.skill_cd > self.info["cooldown"] - 20
        frame_key = f"{self.pet_type}_{'attack' if is_attacking else 'idle'}"
        pet_sprite = sprites.pets.get(frame_key)
        if pet_sprite:
            sp_size = int(48 * scale)
            sp = pygame.transform.smoothscale(pet_sprite, (sp_size, sp_size))
            surf.blit(sp, (dx - sp_size // 2, dy - sp_size // 2))
        else:
            pygame.draw.circle(surf, c, (dx, dy), size)
            pygame.draw.circle(surf, (255, 255, 255), (dx, dy), size, 1)
            pygame.draw.circle(surf, (40, 40, 40), (dx - 3, dy - 2), 2)
            pygame.draw.circle(surf, (40, 40, 40), (dx + 3, dy - 2), 2)

        # Skill cooldown indicator
        if self.skill_cd > 0:
            ratio = self.skill_cd / max(1, self.info["cooldown"])
            arc_r = size + 3
            pygame.draw.arc(surf, (255, 255, 100),
                            (dx - arc_r, dy - arc_r, arc_r * 2, arc_r * 2),
                            0, math.pi * 2 * (1 - ratio), 2)

# ═══════════════════════════════════════
#  CHICKEN & DOG
# ═══════════════════════════════════════
class Chicken:
    def __init__(self, gx, gy):
        self.x = float(gx * TS + TS // 2)
        self.y = float(gy * TS + TS // 2)
        self.dir = random.randint(0, 3)
        self.speed = 0.8
        self.alive = True
        self.frame = 0
        self.move_timer = 0

    def update(self, grid):
        self.frame = (self.frame + 0.1) % 8
        if self.move_timer <= 0:
            self.dir = random.randint(0, 3)
            self.move_timer = random.randint(30, 90)
        dx, dy = DIRS[self.dir]
        nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
        gx, gy = int(nx // TS), int(ny // TS)
        if 0 <= gx < COLS and 0 <= gy < ROWS and grid[gy][gx] == EMPTY:
            self.x, self.y = nx, ny
        else:
            self.move_timer = 0
        self.move_timer -= 1

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        img = sprites.chicken_frames[int(self.frame)]
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(32 * scale), int(32 * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

class Dog:
    def __init__(self, gx, gy):
        self.x = float(gx * TS + TS // 2)
        self.y = float(gy * TS + TS // 2)
        self.dir = 2
        self.speed = 2.0
        self.alive = True
        self.frame = 0
        self.bite_cooldown = 0
        self.state = "idle"
        self.dir_key = "down"
        self.move_timer = 0
        self.frozen_timer = 0

    def update(self, grid, player_pos):
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return
        self.frame = (self.frame + 0.15) % 4
        if self.bite_cooldown > 0: self.bite_cooldown -= 1
        dist = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        if dist < 250:
            self.state = "chase"
            dx = 1 if player_pos[0] > self.x else -1
            dy = 1 if player_pos[1] > self.y else -1
            if abs(player_pos[0] - self.x) < 5: dx = 0
            if abs(player_pos[1] - self.y) < 5: dy = 0
            if abs(dx) > abs(dy):
                self.dir_key = "right" if dx > 0 else "left"
            else:
                self.dir_key = "down" if dy > 0 else "up"
            nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
            gx, gy = int(nx // TS), int(ny // TS)
            if 0 <= gx < COLS and 0 <= gy < ROWS and grid[gy][gx] not in (STEEL, WATER):
                self.x, self.y = nx, ny
        else:
            self.state = "idle"
            if self.move_timer <= 0:
                self.dir = random.randint(0, 3)
                self.move_timer = random.randint(60, 150)
                self.dir_key = ["up", "right", "down", "left"][self.dir]
            dx, dy = DIRS[self.dir]
            nx, ny = self.x + dx * 0.5, self.y + dy * 0.5
            gx, gy = int(nx // TS), int(ny // TS)
            if 0 <= gx < COLS and 0 <= gy < ROWS and grid[gy][gx] == EMPTY:
                self.x, self.y = nx, ny
            else:
                self.move_timer = 0
            self.move_timer -= 1

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        img = sprites.dog_frames.get(self.dir_key, sprites.dog_frames["down"])[int(self.frame)]
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(36 * scale), int(36 * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

# ═══════════════════════════════════════
#  EXPLOSION
# ═══════════════════════════════════════
class Explosion:
    def __init__(self, x, y, big=False):
        self.x, self.y = x, y
        self.frame = 0
        self.speed = 0.3 if big else 0.5
        self.big = big
        self.done = False

    def update(self):
        self.frame += self.speed
        if self.frame >= len(sprites.explosion):
            self.done = True

    def draw(self, surf, offset=(0, 0), scale=1.0):
        if self.done: return
        img = sprites.explosion[int(self.frame)]
        base_scale = 1.8 if self.big else 1.0
        final_scale = base_scale * scale
        w, h = int(96 * final_scale), int(96 * final_scale)
        img = pygame.transform.scale(img, (w, h))
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        surf.blit(img, (draw_x - w // 2, draw_y - h // 2))

# ═══════════════════════════════════════
#  ITEM DROP
# ═══════════════════════════════════════
class Item:
    def __init__(self, gx, gy, kind):
        self.gx, self.gy = gx, gy
        self.x = gx * TS + TS // 2
        self.y = gy * TS + TS // 2
        self.kind = kind
        self.timer = 600
        self.alive = True

    def update(self):
        self.timer -= 1
        if self.timer <= 0: self.alive = False

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        if not self.alive: return
        bob = int(math.sin(tick * 0.1) * 3)
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y + bob - offset[1]) * scale)

        pulse = abs(math.sin(tick * 0.08))
        r = int((16 + pulse * 4) * scale)
        a = int(30 + pulse * 30)
        colors = {"health": (255, 80, 80), "shield": (80, 140, 255), "speed": (80, 255, 130),
                  "star": (255, 215, 0), "money": (255, 220, 50), "life": (255, 50, 150),
                  "rapid": (255, 150, 40), "multi": (220, 200, 40), "pierce": (80, 200, 255),
                  "bomb": (150, 150, 150), "laser": (0, 255, 180), "plasma": (200, 50, 255),
                  "freeze": (120, 220, 255), "max_power": (255, 200, 60), "grenade": (90, 200, 90),
                  "rocket": (255, 80, 30), "flame": (255, 150, 0)}
        c = colors.get(self.kind, (255, 255, 100))

        gs = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*c, a), (r * 2, r * 2), r * 2)
        surf.blit(gs, (draw_x - r * 2, draw_y - r * 2))

        if self.kind in sprites.items:
            img = sprites.items[self.kind]
        else:
            img = sprites.items.get("health", sprites.items[list(sprites.items.keys())[0]])
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(30 * scale), int(30 * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

# ═══════════════════════════════════════
#  TANK
# ═══════════════════════════════════════
class Tank:
    def __init__(self, gx, gy, tank_type="player"):
        self.x = float(gx * TS + TS // 2)
        self.y = float(gy * TS + TS // 2)
        self.dir = 0
        self.speed = 1.8
        self.sprint_multiplier = 1.0
        self.energy = 100
        self.max_energy = 100
        self.hp = 3
        self.max_hp = 3
        self.alive = True
        self.tank_type = tank_type
        self.shoot_cd = 0
        self.shoot_delay = 20
        self.bullet_speed = 6
        self.bullet_power = 1
        self.shield = 0
        self.spawn_timer = 60
        self.flash = 0
        self.skill = None
        self.skill_timer = 0
        self.skill_ammo = 0
        self.muzzle_frame = -1
        self.frozen_timer = 0
        self.tier = 0  # player upgrade tier (0..4)
        self.name = ""  # optional name tag (player only)

    def get_grid(self):
        return int(self.x // TS), int(self.y // TS)

    def get_center(self):
        return self.x, self.y

    def can_move_to(self, nx, ny, grid, other_tanks=None):
        half = TS // 2 - 3
        corners = [(nx - half, ny - half), (nx + half, ny - half),
                   (nx - half, ny + half), (nx + half, ny + half)]
        for cx, cy in corners:
            gx, gy = int(cx // TS), int(cy // TS)
            if gx < 0 or gy < 0 or gx >= COLS or gy >= ROWS:
                return False
            if grid[gy][gx] in (BRICK, STEEL, WATER, CRATE, BASE):
                return False
        if other_tanks:
            for other in other_tanks:
                if other is self or not other.alive: continue
                ox, oy = other.get_center()
                new_dist = math.hypot(nx - ox, ny - oy)
                if new_dist < TS - 4:
                    old_dist = math.hypot(self.x - ox, self.y - oy)
                    if new_dist < old_dist:
                        return False
        return True

    def move(self, dx, dy, grid, other_tanks=None):
        if dx == 0 and dy == 0: return False

        # Cardinal input dominance: if moving diagonally, prioritize the stronger input
        if abs(dx) > abs(dy):
            self.dir = 1 if dx > 0 else 3
        else:
            self.dir = 0 if dy < 0 else 2

        nx, ny = self.x + dx, self.y + dy
        spd = math.hypot(dx, dy)

        # ── SMART AUTO-ALIGNMENT TO GRID LANES ──
        # When moving mostly in one direction, automatically pull towards the center of the other axis
        alignment_speed = 1.5  # slide speed towards lane center
        if abs(dx) > abs(dy) * 1.5:
            # Moving horizontally: pull towards center of Y row
            target_y = int(self.y // TS) * TS + TS / 2.0
            diff = target_y - self.y
            if abs(diff) > 0.1:
                ny += math.copysign(min(abs(diff), alignment_speed), diff)
        elif abs(dy) > abs(dx) * 1.5:
            # Moving vertically: pull towards center of X column
            target_x = int(self.x // TS) * TS + TS / 2.0
            diff = target_x - self.x
            if abs(diff) > 0.1:
                nx += math.copysign(min(abs(diff), alignment_speed), diff)

        # Try standard movement
        if self.can_move_to(nx, ny, grid, other_tanks):
            self.x, self.y = nx, ny
            return True

        # ── PREMIUM CORNER-SLIDING / CORNER-ALLEVIATION ──
        # If the primary movement is blocked, check if we can slide around corners!
        slide_tolerance = 12.0  # Max pixels we are willing to auto-slide to bypass a corner
        slide_step = spd        # Speed of sliding

        if abs(dx) > abs(dy):
            # Primary intent is Horizontal. Let's check if we're blocked by a corner.
            # If we are slightly blocked, try shifting Y up or down to bypass the corner.
            for offset in range(1, int(slide_tolerance) + 1):
                # Try shifting UP
                if self.can_move_to(nx, self.y - offset, grid, other_tanks) and self.can_move_to(self.x, self.y - offset, grid, other_tanks):
                    self.y -= min(slide_step, offset)
                    self.x += dx
                    return True
                # Try shifting DOWN
                if self.can_move_to(nx, self.y + offset, grid, other_tanks) and self.can_move_to(self.x, self.y + offset, grid, other_tanks):
                    self.y += min(slide_step, offset)
                    self.x += dx
                    return True
        else:
            # Primary intent is Vertical. Let's check if we can slide X left or right to bypass a corner.
            for offset in range(1, int(slide_tolerance) + 1):
                # Try shifting LEFT
                if self.can_move_to(self.x - offset, ny, grid, other_tanks) and self.can_move_to(self.x - offset, self.y, grid, other_tanks):
                    self.x -= min(slide_step, offset)
                    self.y += dy
                    return True
                # Try shifting RIGHT
                if self.can_move_to(self.x + offset, ny, grid, other_tanks) and self.can_move_to(self.x + offset, self.y, grid, other_tanks):
                    self.x += min(slide_step, offset)
                    self.y += dy
                    return True

        # Fallback to standard sliding along either X or Y using actual component speeds
        can_x = dx != 0 and self.can_move_to(self.x + dx, self.y, grid, other_tanks)
        can_y = dy != 0 and self.can_move_to(self.x, self.y + dy, grid, other_tanks)

        if can_x and can_y:
            self.x += dx
            self.y += dy
            return True
        elif can_x:
            self.x += dx
            self.dir = 1 if dx > 0 else 3
            return True
        elif can_y:
            self.y += dy
            self.dir = 0 if dy < 0 else 2
            return True

        if self.can_move_to(nx, self.y, grid, other_tanks) and nx != self.x:
            self.x = nx; return True
        if self.can_move_to(self.x, ny, grid, other_tanks) and ny != self.y:
            self.y = ny; return True
        return False

    def shoot(self, target_angle=None):
        if self.shoot_cd > 0 or not self.alive: return []
        if self.skill == "rapid" and self.skill_ammo > 0:
            self.shoot_cd = 5
            self.skill_ammo -= 1
            if self.skill_ammo <= 0: self.skill = None
        else:
            self.shoot_cd = self.shoot_delay

        dx, dy = DIRS[self.dir]
        bx = self.x + dx * (TS // 2 + 2)
        by = self.y + dy * (TS // 2 + 2)
        if target_angle is not None:
            bx = self.x + math.cos(target_angle) * (TS // 2 + 4)
            by = self.y + math.sin(target_angle) * (TS // 2 + 4)

        snd_shoot.play()
        self.muzzle_frame = 0

        if self.skill == "ammo" and self.skill_timer > 0:
            if target_angle is not None:
                bullets = [
                    Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, custom_angle=target_angle),
                    Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, custom_angle=target_angle - 0.4),
                    Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, custom_angle=target_angle + 0.4),
                ]
            else:
                bullets = [
                    Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power),
                    Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, angle_offset=-25),
                    Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, angle_offset=25),
                ]
            return bullets

        bullet_kind = "normal"
        if self.skill in ("pierce", "bomb", "laser", "plasma", "rocket", "flame"):
            bullet_kind = self.skill
        if bullet_kind == "flame":
            bullets = []
            if target_angle is not None:
                for ang in (-0.17, 0, 0.17):
                    bullets.append(Bullet(bx, by, self.dir, self.tank_type, 4, 2, kind="flame", custom_angle=target_angle + ang))
            else:
                for ang in (-10, 0, 10):
                    bullets.append(Bullet(bx, by, self.dir, self.tank_type, 4, 2, kind="flame", angle_offset=ang))
            return bullets
        return [Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, kind=bullet_kind, custom_angle=target_angle)]

    def hit(self, power=1):
        if self.shield > 0:
            self.shield -= 1
            snd_steel.play()
            return False
        self.hp -= power
        self.flash = 10
        if self.hp <= 0:
            self.alive = False
            return True
        snd_hit.play()
        return False

    def update(self):
        if self.shoot_cd > 0: self.shoot_cd -= 1
        if self.spawn_timer > 0: self.spawn_timer -= 1
        if self.flash > 0: self.flash -= 1
        if self.skill_timer > 0:
            self.skill_timer -= 1
            if self.skill_timer == 0: self.skill = None
        if self.muzzle_frame >= 0: self.muzzle_frame += 0.5
        if self.muzzle_frame >= len(sprites.muzzle_flash): self.muzzle_frame = -1

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        if not self.alive: return
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        s_ts = int(TS * scale)

        if self.spawn_timer > 0:
            fi = int((60 - self.spawn_timer) / 60 * len(sprites.spawn_effect))
            fi = max(0, min(len(sprites.spawn_effect) - 1, fi))
            img = sprites.spawn_effect[fi]
            if scale != 1.0: img = pygame.transform.scale(img, (s_ts + 8, s_ts + 8))
            surf.blit(img, (draw_x - s_ts // 2 - 4, draw_y - s_ts // 2 - 4))
            if tick % 4 < 2: return

        # Player aura
        if self.tank_type == "player":
            pulse = abs(math.sin(tick * 0.1))
            r = int((s_ts // 2 + 4 + pulse * 4))
            a = int(40 + pulse * 40)
            gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            if self.sprint_multiplier > 1.0:
                aura_c = (255, 200, 50, a)
            elif self.shield > 0:
                aura_c = (80, 150, 255, a + 20)
            else:
                aura_c = (100, 255, 150, a)
            pygame.draw.circle(gs, aura_c, (r, r), r)
            surf.blit(gs, (draw_x - r, draw_y - r))

        # Shield visual
        if self.shield > 0:
            shield_pulse = abs(math.sin(tick * 0.15))
            sr = int(s_ts // 2 + 6 + shield_pulse * 2)
            ss = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ss, (80, 150, 255, int(60 + shield_pulse * 40)), (sr, sr), sr, 2)
            surf.blit(ss, (draw_x - sr, draw_y - sr))

        tank_key = self.tank_type
        if tank_key == "player":
            tier = max(0, min(len(sprites.player_tiers) - 1, getattr(self, "tier", 0)))
            img = sprites.player_tiers[tier][self.dir]
        else:
            if tank_key not in sprites.tanks:
                tank_key = "enemy_a"
            img = sprites.tanks[tank_key][self.dir]
        if scale != 1.0: img = pygame.transform.scale(img, (s_ts, s_ts))

        if self.flash > 0 and tick % 3 < 1:
            white_img = img.copy()
            white_img.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(white_img, (draw_x - s_ts // 2, draw_y - s_ts // 2))
        else:
            surf.blit(img, (draw_x - s_ts // 2, draw_y - s_ts // 2))

        # Frozen overlay
        if getattr(self, "frozen_timer", 0) > 0:
            ice_alpha = int(120 + 60 * abs(math.sin(tick * 0.2)))
            ice = pygame.Surface((s_ts, s_ts), pygame.SRCALPHA)
            ice.fill((140, 220, 255, ice_alpha // 2))
            surf.blit(ice, (draw_x - s_ts // 2, draw_y - s_ts // 2), special_flags=pygame.BLEND_RGBA_ADD)
            # Ice crystals around tank
            cr = s_ts // 2 + 2
            cs = pygame.Surface((cr * 2, cr * 2), pygame.SRCALPHA)
            for ang in range(0, 360, 60):
                rad = math.radians(ang + tick * 1.5)
                xx = cr + math.cos(rad) * cr
                yy = cr + math.sin(rad) * cr
                pygame.draw.circle(cs, (200, 240, 255, 220), (int(xx), int(yy)), 2)
            surf.blit(cs, (draw_x - cr, draw_y - cr))

        # Muzzle flash
        if self.muzzle_frame >= 0 and self.muzzle_frame < len(sprites.muzzle_flash):
            mf_img = sprites.muzzle_flash[int(self.muzzle_frame)]
            mdx, mdy = DIRS[self.dir]
            mx = draw_x + mdx * (s_ts // 2 + 4)
            my = draw_y + mdy * (s_ts // 2 + 4)
            if scale != 1.0:
                mf_img = pygame.transform.scale(mf_img, (int(24 * scale), int(24 * scale)))
            surf.blit(mf_img, (mx - mf_img.get_width() // 2, my - mf_img.get_height() // 2))

        # HP bar
        if self.tank_type == "player" or self.flash > 0:
            bw = int(28 * scale)
            bx_bar = draw_x - bw // 2
            by_bar = draw_y - s_ts // 2 - int(8 * scale)
            pygame.draw.rect(surf, (20, 20, 20), (bx_bar - 1, by_bar - 1, bw + 2, 6), border_radius=2)
            hw = int(bw * self.hp / self.max_hp)
            c = (80, 220, 80) if self.hp > 1 else (220, 60, 60)
            pygame.draw.rect(surf, c, (bx_bar, by_bar, hw, 4), border_radius=2)

            if self.tank_type == "player":
                ey = by_bar + 6
                pygame.draw.rect(surf, (20, 20, 20), (bx_bar - 1, ey, bw + 2, 4), border_radius=1)
                ew = int(bw * self.energy / self.max_energy)
                pygame.draw.rect(surf, (50, 200, 255), (bx_bar, ey + 1, ew, 2), border_radius=1)

        # Floating name tag above player tank
        if self.tank_type == "player" and self.name:
            label = FONT_SM.render(self.name, True, (255, 255, 255))
            tag_w = label.get_width() + 14
            tag_h = label.get_height() + 4
            tag_x = draw_x - tag_w // 2
            tag_y = draw_y - s_ts // 2 - int(20 * scale) - tag_h
            tag = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
            pygame.draw.rect(tag, (40, 30, 70, 220), (0, 0, tag_w, tag_h),
                             border_radius=tag_h // 2)
            pygame.draw.rect(tag, (255, 200, 230, 255), (0, 0, tag_w, tag_h),
                             2, border_radius=tag_h // 2)
            surf.blit(tag, (tag_x, tag_y))
            surf.blit(label, (tag_x + 7, tag_y + 2))

# ═══════════════════════════════════════
#  ENEMY AI
# ═══════════════════════════════════════
class EnemyTank(Tank):
    def __init__(self, gx, gy, tank_type="enemy_a", difficulty=1.0):
        super().__init__(gx, gy, tank_type)
        # Cap difficulty so high levels don't make bots insane
        self.difficulty = min(difficulty, 1.2)
        self.path = []
        self.path_update_timer = 0
        self.stuck_counter = 0
        self.last_pos = (self.x, self.y)
        # Cooldown frames before the AI is allowed to change facing again
        self.turn_cooldown = 0
        # Default minimum frames between turns (overridden per type below)
        self.turn_delay = 14

        if tank_type == "enemy_b":
            self.speed = 0.9 * self.difficulty
            self.hp = 2; self.max_hp = 2
            self.shoot_delay = max(12, int(30 / self.difficulty))
            self.turn_delay = 12
        elif tank_type == "elite":
            self.speed = 0.8 * self.difficulty
            self.hp = 5; self.max_hp = 5
            self.shoot_delay = max(12, int(22 / self.difficulty))
            self.bullet_power = 2
            self.turn_delay = 14
        elif tank_type == "boss":
            self.speed = 0.45 * self.difficulty
            self.hp = 8; self.max_hp = 8
            self.shoot_delay = max(14, int(26 / self.difficulty))
            self.bullet_power = 2
            self.turn_delay = 18
        else:
            base_speed = 0.55 if self.difficulty <= 0.7 else 0.7
            self.speed = base_speed * self.difficulty
            self.hp = 2; self.max_hp = 2
            self.shoot_delay = max(14, int(40 / self.difficulty))
            self.turn_delay = 16

    def get_tank_positions(self, all_tanks):
        positions = set()
        for t in all_tanks:
            if t != self and t.alive:
                positions.add(t.get_grid())
        return positions

    def is_in_viewport(self, cam_x, cam_y, cam_zoom):
        """Check if this tank is visible in the camera viewport"""
        view_w = SW / cam_zoom
        view_h = SH / cam_zoom
        margin = TS * 2
        return (self.x + TS > cam_x - margin and self.x < cam_x + view_w + margin and
                self.y + TS > cam_y - margin and self.y < cam_y + view_h + margin)

    def _try_turn(self, new_dir, force=False):
        """Change facing only if turn-cooldown elapsed. Returns True if turned."""
        if new_dir is None or new_dir == -1 or new_dir == self.dir:
            return False
        if force or self.turn_cooldown <= 0:
            self.dir = new_dir
            self.turn_cooldown = self.turn_delay
            return True
        return False

    def update_ai(self, grid, player, all_tanks, cam_x=0, cam_y=0, cam_zoom=1.0):
        if not self.alive or self.spawn_timer > 0: return None
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return None
        # Tick down turn cooldown
        if self.turn_cooldown > 0:
            self.turn_cooldown -= 1
        my_pos = self.get_grid()
        player_pos = player.get_grid()
        base_pos = (COLS // 2, ROWS - 3)

        in_view = self.is_in_viewport(cam_x, cam_y, cam_zoom)

        dist_to_p = abs(my_pos[0] - player_pos[0]) + abs(my_pos[1] - player_pos[1])
        target_pos = player_pos
        if dist_to_p > 15:
            target_pos = base_pos if random.random() < 0.2 else None
        else:
            if self.tank_type == "enemy_b" and random.random() < 0.3:
                target_pos = base_pos
            elif self.tank_type in ("elite", "boss"):
                dist_to_b = abs(my_pos[0] - base_pos[0]) + abs(my_pos[1] - base_pos[1])
                target_pos = player_pos if dist_to_p < dist_to_b else base_pos

        # Only shoot when enemy is visible in camera viewport
        if in_view and Pathfinder.can_shoot(grid, my_pos[0], my_pos[1], player_pos[0], player_pos[1]):
            if my_pos[0] == player_pos[0]:
                desired = 0 if player_pos[1] < my_pos[1] else 2
            else:
                desired = 1 if player_pos[0] > my_pos[0] else 3
            self._try_turn(desired)
            # Only allow shooting when we're actually facing the player
            if self.dir == desired:
                shoot_chance = 0.05 * (1.0 + self.difficulty)
                if self.tank_type == "boss": shoot_chance *= 1.2
                if random.random() < shoot_chance:
                    self.muzzle_frame = 0
                    return self.shoot()

        # Pathfinding (slower repath so behavior is steadier)
        self.path_update_timer += 1
        should_repath = self.path_update_timer >= 60 or not self.path or self.stuck_counter >= 12
        if not should_repath and self.path:
            last_goal = self.path[-1]
            if target_pos is not None:
                if abs(last_goal[0] - target_pos[0]) + abs(last_goal[1] - target_pos[1]) > 2:
                    should_repath = True

        if should_repath:
            self.path_update_timer = 0
            other_positions = self.get_tank_positions(all_tanks)
            if target_pos is None:
                cx, cy = my_pos
                rx = max(1, min(COLS - 2, cx + random.randint(-4, 4)))
                ry = max(1, min(ROWS - 2, cy + random.randint(-4, 4)))
                target_pos = (rx, ry) if grid[ry][rx] == EMPTY else my_pos
            self.path = Pathfinder.a_star_path(grid, my_pos, target_pos, other_positions)
            self.stuck_counter = 0

        if len(self.path) > 1:
            next_pos = self.path[1]
            tile_next = grid[next_pos[1]][next_pos[0]]
            if tile_next in (BRICK, CRATE):
                desired = Pathfinder.get_next_direction(my_pos, next_pos)
                self._try_turn(desired)
                if random.random() < 0.10:
                    return self.shoot()
            else:
                next_dir = Pathfinder.get_next_direction(my_pos, next_pos)
                if next_dir != -1:
                    # If stuck for a while, force a turn so we don't deadlock
                    self._try_turn(next_dir, force=(self.stuck_counter >= 8))
                    ddx, ddy = DIRS[self.dir]
                    moved = self.move(ddx * self.speed, ddy * self.speed, grid, all_tanks)
                    if not moved or (abs(self.x - self.last_pos[0]) < 1 and abs(self.y - self.last_pos[1]) < 1):
                        self.stuck_counter += 1
                    else:
                        self.stuck_counter = 0
                    if moved and self.get_grid() == next_pos:
                        self.path.pop(0)
                    self.last_pos = (self.x, self.y)
        else:
            safe_dirs = Pathfinder.get_safe_directions(grid, self.x, self.y)
            if safe_dirs:
                if self.dir not in safe_dirs:
                    self._try_turn(random.choice(safe_dirs), force=True)
                ddx, ddy = DIRS[self.dir]
                self.move(ddx * self.speed, ddy * self.speed, grid, all_tanks)
        return None

# ═══════════════════════════════════════
#  BOSS TANK — unique bosses every 5 levels
# ═══════════════════════════════════════
BOSS_LEVEL_MAP = {
    5: "boss_desert",    # Tướng Sa Mạc
    10: "boss_ice",      # Tướng Băng Giá
    15: "boss_jungle",   # Tướng Rừng Rậm
    20: "boss_final",    # Trùm Cuối
}

BOSS_INFO = {
    "boss_desert": {
        # Tăng HP gấp ~2x, bắn nhanh hơn, di chuyển nhanh hơn.
        "name": "TƯỚNG SA MẠC",
        "hp": 45, "speed": 0.75, "shoot_delay": 12,
        "skills": ["sandstorm", "scorpion_rocket", "sand_mines"],
        "skill_names": ["Bão Cát", "Bọ Cạp Tên Lửa", "Mìn Cát"],
    },
    "boss_ice": {
        "name": "TƯỚNG BĂNG GIÁ",
        "hp": 65, "speed": 0.7, "shoot_delay": 10,
        "skills": ["ice_burst", "freeze_ray", "ice_mines"],
        "skill_names": ["Vụ Nổ Băng", "Tia Đóng Băng", "Mìn Băng"],
    },
    "boss_jungle": {
        "name": "TƯỚNG RỪNG RẬM",
        "hp": 90, "speed": 0.85, "shoot_delay": 9,
        "skills": ["vine_whip", "toxic_cloud", "summon_minions"],
        "skill_names": ["Roi Dây Leo", "Mây Độc", "Triệu Hồi Lính"],
    },
    "boss_final": {
        "name": "TRÙM CUỐI",
        "hp": 130, "speed": 0.65, "shoot_delay": 7,
        "skills": ["death_rain", "laser_barrage", "meteor_strike"],
        "skill_names": ["Mưa Chết Chóc", "Laser Hủy Diệt", "Thiên Thạch"],
    },
}


class BossTank(EnemyTank):
    """Boss tank with unique appearance, 3 special skills, and increasing difficulty."""

    def __init__(self, gx, gy, boss_key, difficulty=1.0):
        super().__init__(gx, gy, "boss", difficulty)
        self.boss_key = boss_key
        info = BOSS_INFO[boss_key]
        self.boss_name = info["name"]
        # Boss buffs: HP gấp 2-3x cũ, damage cao, hồi máu nhẹ theo thời gian,
        # giáp giảm sát thương 1/4.
        self.hp = info["hp"]
        self.max_hp = info["hp"]
        self.speed = info["speed"] * min(difficulty, 1.4)
        self.shoot_delay = max(4, info["shoot_delay"] - 2)
        self.bullet_power = 3            # was 2
        self.skills = info["skills"]
        self.current_skill = 0
        self.skill_cooldown = 0
        self.skill_cooldown_max = 120    # was 180 → skill nhanh hơn 33%
        self.boss_armor = 1              # subtract from incoming damage
        self.boss_regen_counter = 0      # tick-based slow self-heal
        self.skill_active = False
        self.skill_timer = 0
        self.aura_tick = 0
        self.phase = 0  # 0 = full hp, 1 = half hp (enraged)
        self.enraged = False
        self.summon_count = 0  # track minion summons
        self.mine_positions = []  # track mines placed

    def get_boss_sprite(self, direction):
        """Get the boss-specific sprite from SpriteCache."""
        if self.boss_key in sprites.boss_tanks:
            return sprites.boss_tanks[self.boss_key][direction]
        return sprites.tanks["boss"][direction]

    def hit(self, power=1):
        """Boss armor: subtract `boss_armor` from incoming damage (min 1)."""
        if self.shield > 0:
            self.shield -= 1
            snd_steel.play()
            return False
        effective = max(1, int(power) - self.boss_armor)
        self.hp -= effective
        self.flash = 10
        if self.hp <= 0:
            self.alive = False
            return True
        snd_hit.play()
        return False

    def update_boss(self):
        """Update boss-specific timers and phase checks."""
        self.aura_tick += 1
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
        # Enrage at half HP — di chuyển nhanh + bắn dày + dame to
        if not self.enraged and self.hp <= self.max_hp // 2:
            self.enraged = True
            self.speed *= 1.5             # was 1.3
            self.shoot_delay = max(3, self.shoot_delay - 2)
            self.bullet_power += 1
            self.skill_cooldown_max = max(60, self.skill_cooldown_max - 60)
        # Slow self-regen so the fight has to be aggressive.
        self.boss_regen_counter += 1
        if self.boss_regen_counter >= 180 and self.hp < self.max_hp:
            self.boss_regen_counter = 0
            self.hp = min(self.max_hp, self.hp + 1)

    def use_skill(self, player, grid):
        """Execute the current boss skill. Returns list of bullets or None."""
        if self.skill_cooldown > 0 or not self.alive:
            return None
        skill = self.skills[self.current_skill]
        self.current_skill = (self.current_skill + 1) % len(self.skills)
        cd = self.skill_cooldown_max
        if self.enraged:
            cd = max(60, cd - 30)
        self.skill_cooldown = cd
        bullets = []

        dx_to_player = player.x - self.x
        dy_to_player = player.y - self.y
        angle_to_player = math.atan2(dy_to_player, dx_to_player)

        if skill == "sandstorm":
            # 5-bullet fan spread
            for i in range(5):
                ang = angle_to_player + math.radians(-30 + i * 15)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 5, 2,
                                      kind="normal", custom_angle=ang))
            self.muzzle_frame = 0

        elif skill == "scorpion_rocket":
            # Fast rocket toward player
            bullets.append(Bullet(self.x, self.y, self.dir, "boss", 3, 4,
                                  kind="rocket", custom_angle=angle_to_player))
            self.muzzle_frame = 0

        elif skill == "sand_mines":
            # Drop 3 mines around self (as bomb bullets that move slowly outward)
            for i in range(3):
                ang = angle_to_player + math.radians(-60 + i * 60)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 1.5, 3,
                                      kind="bomb", custom_angle=ang))

        elif skill == "ice_burst":
            # 8-way bullet burst
            for i in range(8):
                ang = math.radians(i * 45)
                spd = 5 if not self.enraged else 6
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", spd, 2,
                                      kind="normal", custom_angle=ang))
            self.muzzle_frame = 0

        elif skill == "freeze_ray":
            # 3 laser bullets toward player
            for i in range(3):
                ang = angle_to_player + math.radians(-8 + i * 8)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 7, 2,
                                      kind="laser", custom_angle=ang))
            self.muzzle_frame = 0

        elif skill == "ice_mines":
            # 4 slow plasma orbs spreading outward
            for i in range(4):
                ang = math.radians(i * 90 + self.aura_tick * 2)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 1, 2,
                                      kind="plasma", custom_angle=ang))

        elif skill == "vine_whip":
            # 3 fast bullets toward player
            for i in range(3):
                ang = angle_to_player + math.radians(-12 + i * 12)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 8, 2,
                                      kind="pierce", custom_angle=ang))
            self.muzzle_frame = 0

        elif skill == "toxic_cloud":
            # Ring of slow flame bullets
            for i in range(6):
                ang = math.radians(i * 60 + self.aura_tick)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 2, 2,
                                      kind="flame", custom_angle=ang))

        elif skill == "summon_minions":
            # Returns special marker — game loop handles actual spawning
            self.summon_count += 2
            return "summon"

        elif skill == "death_rain":
            # 12-way bullet rain
            n = 12 if not self.enraged else 16
            for i in range(n):
                ang = math.radians(i * (360 / n))
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 4, 3,
                                      kind="normal", custom_angle=ang))
            self.muzzle_frame = 0

        elif skill == "laser_barrage":
            # 5 laser beams toward player
            for i in range(5):
                ang = angle_to_player + math.radians(-16 + i * 8)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 9, 3,
                                      kind="laser", custom_angle=ang))
            self.muzzle_frame = 0

        elif skill == "meteor_strike":
            # 3 powerful rockets toward player
            for i in range(3):
                ang = angle_to_player + math.radians(-20 + i * 20)
                bullets.append(Bullet(self.x, self.y, self.dir, "boss", 3, 5,
                                      kind="rocket", custom_angle=ang))
            self.muzzle_frame = 0

        return bullets if bullets else None

    def update_ai(self, grid, player, all_tanks, cam_x=0, cam_y=0, cam_zoom=1.0):
        """Boss AI: use skills + normal AI movement."""
        if not self.alive or self.spawn_timer > 0:
            return None
        self.update_boss()

        # Try to use a skill
        skill_result = self.use_skill(player, grid)
        if skill_result == "summon":
            return "boss_summon"
        if skill_result:
            return skill_result

        # Fall back to normal AI for movement + basic shooting
        return super().update_ai(grid, player, all_tanks, cam_x, cam_y, cam_zoom)

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        """Draw boss with unique sprite, aura effects, and HP bar."""
        if not self.alive:
            return
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        boss_size = int(_BOSS_DISPLAY * scale)
        half = boss_size // 2

        if self.spawn_timer > 0:
            fi = int((60 - self.spawn_timer) / 60 * len(sprites.spawn_effect))
            fi = max(0, min(len(sprites.spawn_effect) - 1, fi))
            img = sprites.spawn_effect[fi]
            img = pygame.transform.scale(img, (boss_size + 16, boss_size + 16))
            surf.blit(img, (draw_x - half - 8, draw_y - half - 8))
            if tick % 4 < 2:
                return

        # Aura glow effect
        c = BOSS_COLORS[self.boss_key]
        glow_c = c.get("glow_color", c["accent"])
        pulse = abs(math.sin(tick * 0.08))
        aura_r = int((half + 8 + pulse * 6) * scale)
        aura_alpha = int(30 + pulse * 40)
        aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_s, (*glow_c, aura_alpha), (aura_r, aura_r), aura_r)
        surf.blit(aura_s, (draw_x - aura_r, draw_y - aura_r))

        # Enrage aura
        if self.enraged:
            rage_pulse = abs(math.sin(tick * 0.15))
            rage_r = int((half + 12 + rage_pulse * 8) * scale)
            rage_s = pygame.Surface((rage_r * 2, rage_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(rage_s, (255, 50, 0, int(20 + rage_pulse * 30)), (rage_r, rage_r), rage_r)
            surf.blit(rage_s, (draw_x - rage_r, draw_y - rage_r))

        # Boss sprite
        img = self.get_boss_sprite(self.dir)
        if scale != 1.0:
            img = pygame.transform.scale(img, (boss_size, boss_size))

        if self.flash > 0 and tick % 3 < 1:
            white_img = img.copy()
            white_img.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(white_img, (draw_x - half, draw_y - half))
        else:
            surf.blit(img, (draw_x - half, draw_y - half))

        # Frozen overlay
        if getattr(self, "frozen_timer", 0) > 0:
            ice_alpha = int(120 + 60 * abs(math.sin(tick * 0.2)))
            ice = pygame.Surface((boss_size, boss_size), pygame.SRCALPHA)
            ice.fill((140, 220, 255, ice_alpha // 2))
            surf.blit(ice, (draw_x - half, draw_y - half), special_flags=pygame.BLEND_RGBA_ADD)

        # Muzzle flash
        if self.muzzle_frame >= 0 and self.muzzle_frame < len(sprites.muzzle_flash):
            mf_img = sprites.muzzle_flash[int(self.muzzle_frame)]
            mdx, mdy = DIRS[self.dir]
            mx = draw_x + mdx * (half + 4)
            my = draw_y + mdy * (half + 4)
            mf_big = pygame.transform.scale(mf_img, (int(32 * scale), int(32 * scale)))
            surf.blit(mf_big, (mx - mf_big.get_width() // 2, my - mf_big.get_height() // 2))

        # Boss HP bar (above boss)
        bar_w = int(60 * scale)
        bar_h = int(8 * scale)
        bar_x = draw_x - bar_w // 2
        bar_y = draw_y - half - int(14 * scale)
        pygame.draw.rect(surf, (20, 20, 20), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=3)
        hp_w = int(bar_w * self.hp / self.max_hp)
        hp_color = (255, 50, 50) if self.hp < self.max_hp * 0.3 else (255, 150, 0) if self.hp < self.max_hp * 0.6 else (50, 255, 50)
        pygame.draw.rect(surf, hp_color, (bar_x, bar_y, hp_w, bar_h), border_radius=2)
        pygame.draw.rect(surf, (255, 255, 255, 100), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=2)

        # Boss name above HP bar
        name_surf = FONT_SM.render(self.boss_name, True, glow_c)
        surf.blit(name_surf, (draw_x - name_surf.get_width() // 2, bar_y - name_surf.get_height() - 2))

        # Skill indicator dots
        dot_y = bar_y + bar_h + 3
        for i in range(len(self.skills)):
            dot_x = draw_x - len(self.skills) * 5 + i * 10
            dot_color = glow_c if i == self.current_skill else (100, 100, 100)
            pygame.draw.circle(surf, dot_color, (dot_x, int(dot_y)), max(2, int(3 * scale)))


# ═══════════════════════════════════════
#  PARTICLES
# ═══════════════════════════════════════
particles = []
# A single-element list used as a soft reference handle to the active Game
# instance so module-level helpers (spawn_particles, …) can honour the user's
# in-game settings without threading the Game object through every call site.
_GLOBAL_GAME_REF = []

class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'life', 'max_life', 'size']
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        a = random.uniform(0, 6.28)
        v = random.uniform(1, 5)
        self.vx, self.vy = math.cos(a) * v, math.sin(a) * v
        self.color = color
        self.life = random.randint(15, 40)
        self.max_life = self.life
        self.size = random.randint(2, 5)

def spawn_particles(x, y, color, n=10):
    # Honour the "Hiệu ứng hạt" toggle and the graphics-quality choice.
    g = _GLOBAL_GAME_REF[0] if _GLOBAL_GAME_REF else None
    if g is not None:
        if not g.settings.get("particles", True):
            return
        gfx = int(g.settings.get("graphics", 2))
        # Scale particle count by graphics quality.
        scale = [0.25, 0.5, 1.0, 1.6][max(0, min(3, gfx))]
        n = max(1, int(n * scale))
    for _ in range(n):
        particles.append(Particle(x, y, color))

def update_draw_particles(surf, offset=(0, 0), scale=1.0):
    for p in particles[:]:
        p.x += p.vx; p.y += p.vy
        p.vx *= 0.94; p.vy *= 0.94
        p.vy += 0.05
        p.life -= 1
        if p.life <= 0:
            particles.remove(p)
            continue
        draw_x = int((p.x - offset[0]) * scale)
        draw_y = int((p.y - offset[1]) * scale)
        a = p.life / p.max_life
        sz = max(1, int(p.size * a * scale))
        if sz > 1:
            gs = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*p.color, int(50 * a)), (sz * 2, sz * 2), sz * 2)
            surf.blit(gs, (draw_x - sz * 2, draw_y - sz * 2))
        pygame.draw.circle(surf, p.color, (draw_x, draw_y), sz)

# ═══════════════════════════════════════
#  FLOATING TEXT
# ═══════════════════════════════════════
floating_texts = []

class FloatingText:
    def __init__(self, x, y, text, color=(255, 220, 80), center_bounce=False, huge=False):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.center_bounce = center_bounce
        self.huge = huge
        self.life = 80 if (center_bounce or huge) else 50
        self.max_life = self.life

    def update(self):
        if not self.center_bounce:
            self.y -= 0.8
        self.life -= 1

    def draw(self, surf, offset=(0, 0), scale=1.0):
        a = self.life / self.max_life
        font = FONT_BIG if (self.center_bounce or self.huge) else FONT_SM
        t = font.render(self.text, True, self.color)

        if self.center_bounce or self.huge:
            progress = 1.0 - a
            if progress < 0.2: s = 0.5 + (progress / 0.2) * 1.5
            else: s = 1.5 - ((progress - 0.2) / 0.8) * 0.5
            if self.huge: s *= 1.2
            nw, nh = int(t.get_width() * s), int(t.get_height() * s)
            if nw > 0 and nh > 0:
                t = pygame.transform.scale(t, (nw, nh))
            if self.center_bounce:
                draw_x, draw_y = SW // 2, SH // 3
            else:
                draw_x = int((self.x - offset[0]) * scale)
                draw_y = int((self.y - offset[1]) * scale)
        else:
            if scale != 1.0:
                nw, nh = int(t.get_width() * scale), int(t.get_height() * scale)
                if nw > 0 and nh > 0:
                    t = pygame.transform.scale(t, (nw, nh))
            draw_x = int((self.x - offset[0]) * scale)
            draw_y = int((self.y - offset[1]) * scale)

        ts = pygame.Surface(t.get_size(), pygame.SRCALPHA)
        ts.blit(t, (0, 0))
        ts.set_alpha(int(255 * a))
        surf.blit(ts, (draw_x - t.get_width() // 2, draw_y - t.get_height() // 2))

# ═══════════════════════════════════════
#  GAME CLASS
# ═══════════════════════════════════════
class Game:
    def __init__(self):
        # Expose self so module-level helpers can read settings.
        global _GLOBAL_GAME_REF
        _GLOBAL_GAME_REF[:] = [self]

        # Start at the fake-login screen.  After "logging in" the player is
        # taken to the title menu.
        self.state = "login"
        try: pygame.mixer.music.play(-1)
        except Exception: pass
        self.level = 1
        self.score = 0
        self.lives = 3
        self.money = 0
        self.grid = None
        self.base_pos = None
        self.player = None
        self.enemies = []
        self.chickens = []
        self.dogs = []
        self.bullets = []
        self.explosions = []
        self.items = []
        self.enemies_to_spawn = 0
        self.spawn_timer = 0
        self.spawn_points = []
        self.tick = 0
        self.kills = 0
        self.total_enemies = 0
        self.water_frame = 0
        self.shake_amount = 0
        self.shake_x = 0
        self.shake_y = 0
        self.combo = 0
        self.combo_timer = 0
        self.auto_mode = False
        self.auto_path = []
        self.auto_path_update = 0
        self.max_alive = 1
        self.mission_text = ""
        self.mission_timer = 0
        self.won_level = False
        self.bought_skills = {}
        self.auto_algos = ["A*", "BFS", "DFS"]
        self.auto_algo_idx = 0
        self.auto_algo = "A*"
        self.map_theme = "default"
        self.backpack = []
        self.backpack_slots = 1  # start with 1 slot, max 3
        self.total_kills = 0
        self.total_money_earned = 0
        self.player_tier = 0  # persisted across levels
        self.gems = 10
        self.player_name = os.environ.get("TANK_PLAYER_NAME", "Thuanvuse")
        self.owned_pets = []  # list of pet_type strings
        self.active_pet_type = None  # currently selected pet
        self.pet = None  # active Pet instance in-game
        self.scaled_tile_cache = {}

        # Level selection
        self.max_levels = 20
        self.unlocked_levels = {1}
        self.level_sel = 0
        self.level_sel_page = 0

        # Kawaii title menu
        self.menu_buttons = ["CHIẾN ĐẤU", "SHOP", "GA-RA", "CHƠI MẠNG (PVP)", "CHƠI CHUNG (CO-OP)", "VÒNG QUAY", "CÀI ĐẶT"]
        self.menu_sel = 0

        # Fake login screen — rectangles map to the buttons baked into
        # the "TANK TOP 1" background image (1280x720 logical).
        # Each entry is (label, click_rect, provider_for_account_label).
        self.login_buttons = [
            # Top-left back/quit-to-menu button
            ("BACK",      pygame.Rect(8, 6, 165, 52),     "BACK"),
            # Top-right social-login icons
            ("Google",    pygame.Rect(1010, 30, 70, 70),  "Google"),
            ("Facebook",  pygame.Rect(1090, 30, 70, 70),  "Facebook"),
            ("Apple",     pygame.Rect(1175, 30, 70, 70),  "Apple"),
            # Bottom-centre tabs
            ("TT1-CHALLENGER", pygame.Rect(395, 495, 290, 28), "TT1-Challenger"),
            ("GUEST",     pygame.Rect(690, 495, 110, 28),  "Khách"),
            # Form fields (purely visual — clicking just logs in)
            ("USERNAME",  pygame.Rect(475, 528, 235, 34), "TT1-Challenger"),
            ("PASSWORD",  pygame.Rect(475, 565, 235, 34), "TT1-Challenger"),
            # Main "LOG IN" yellow button
            ("LOG IN",    pygame.Rect(735, 528, 120, 68), "TT1-Challenger"),
            # "REGISTER" text below the button
            ("REGISTER",  pygame.Rect(745, 603, 110, 22), "TT1-Challenger"),
        ]
        self.login_providers = [
            ("Facebook",        (24, 119, 242),  "FB"),
            ("Google",          (234, 67, 53),   "G"),
            ("X (Twitter)",     (15, 20, 25),    "X"),
            ("Apple iOS",       (180, 180, 200), "iOS"),
            ("Khách / Chơi ngay", (90, 200, 130), ">"),
        ]
        self.login_sel = 4   # default to LOG IN button when using keyboard
        self.login_username = ""
        self.login_provider = ""
        self.login_done = False

        # Key bindings (player controls).  Saved with the settings.
        self.keybinds = {
            "up":     pygame.K_w,
            "down":   pygame.K_s,
            "left":   pygame.K_a,
            "right":  pygame.K_d,
            "shoot":  pygame.K_SPACE,
            "special":pygame.K_LSHIFT,
            "freeze": pygame.K_f,
            "grenade":pygame.K_g,
            "pause":  pygame.K_ESCAPE,
        }
        self.keybind_labels = [
            ("Tiến lên (lên)",     "up"),
            ("Lùi (xuống)",        "down"),
            ("Sang trái",          "left"),
            ("Sang phải",          "right"),
            ("Bắn",                "shoot"),
            ("Kỹ năng đặc biệt",   "special"),
            ("Đóng băng (Freeze)", "freeze"),
            ("Lựu đạn",            "grenade"),
            ("Tạm dừng",           "pause"),
        ]
        self.keybind_sel = 0
        self.awaiting_keybind = False  # Set true while user is choosing a key

        # Settings (audio + video + gameplay + UX)
        self.settings = dict(DEFAULT_SETTINGS)
        self.settings_sel = 0
        # Each entry: (label, key, kind, params)
        #   kind: "slider" (0..100), "toggle", "choice", "action", "info"
        self.settings_layout = [
            ("Âm lượng tổng",           "master_volume", "slider", None),
            ("Âm lượng nhạc nền",       "music_volume",  "slider", None),
            ("Âm lượng hiệu ứng",       "sfx_volume",    "slider", None),
            ("Chế độ toàn màn hình",    "fullscreen",    "toggle", None),
            ("Độ phân giải (cửa sổ)",   "resolution_idx","choice",
                [f"{w}x{h}" for (w, h) in RESOLUTION_PRESETS]),
            ("Chất lượng đồ hoạ",       "graphics",      "choice",
                ["Thấp", "Vừa", "Cao", "Cực Cao"]),
            ("Hiệu ứng hạt (particle)", "particles",     "toggle", None),
            ("Hiệu ứng thời tiết",      "weather_fx",    "toggle", None),
            ("Rung màn hình khi nổ",    "screen_shake",  "toggle", None),
            ("Hiển thị Mini-map",       "show_minimap",  "toggle", None),
            ("Hiển thị FPS",            "show_fps",      "toggle", None),
            ("Gợi ý phím (hint)",       "show_hints",    "toggle", None),
            ("GÁN PHÍM ĐIỀU KHIỂN",     "_keybinds",     "action", None),
            ("ĐĂNG XUẤT TÀI KHOẢN",     "_logout",       "action", None),
            ("ÁP DỤNG & LƯU",           "_apply",        "action", None),
            ("RESET MẶC ĐỊNH",          "_reset",        "action", None),
            ("QUAY LẠI",                "_back",         "action", None),
        ]

        # Lucky Spin (Vong Quay May Man) state variables
        self.spin_angle = 0.0
        self.spin_active = False
        self.spin_timer = 0
        self.spin_start_angle = 0.0
        self.spin_target_angle = 0.0
        self.target_sector = 0
        self.spin_cost = 100  # Cost in gems
        
        self.reveal_active = False
        self.reveal_timer = 0
        self.reveal_particles = []
        self.lucky_spin_logs = ["Chao mung ban den voi Vong Quay!"]
        
        # Custom UI Assets
        self.bg_main = None
        self.menu_btn_imgs = []
        self.pointer_img = None
        self.login_bg = None
        try:
            bg_path = resource_path(os.path.join("IMG", "br.jpg"))
            if os.path.exists(bg_path):
                self.bg_main = pygame.transform.scale(pygame.image.load(bg_path).convert(), (SW, SH))

            ptr_path = resource_path(os.path.join("IMG", "pointer.png"))
            if os.path.exists(ptr_path):
                self.pointer_img = pygame.transform.scale(pygame.image.load(ptr_path).convert_alpha(), (40, 40))

            btn_files = ["chiendau.png", "cuahang.png", "gara.png", "choimang.png"]
            for f_name in btn_files:
                b_path = resource_path(os.path.join("IMG", f_name))
                if os.path.exists(b_path):
                    self.menu_btn_imgs.append(pygame.image.load(b_path).convert_alpha())

            # Login screen background (the pixel art "TANK TOP 1" image)
            for cand in (
                resource_path(os.path.join("assets", "login_bg.png")),
                resource_path(os.path.join("IMG", "login_bg.png")),
            ):
                if os.path.exists(cand):
                    raw = pygame.image.load(cand).convert()
                    self.login_bg = pygame.transform.smoothscale(raw, (SW, SH))
                    break

            # Title screen background (sci-fi station from the user's video)
            self.title_bg = None
            for cand in (
                resource_path(os.path.join("assets", "title_bg.png")),
                resource_path(os.path.join("IMG", "title_bg.png")),
            ):
                if os.path.exists(cand):
                    raw = pygame.image.load(cand).convert()
                    self.title_bg = pygame.transform.smoothscale(raw, (SW, SH))
                    break

            # Level-select background — the pixel-art world map showing
            # all 20 levels.  When present, draw_level_select switches to
            # a baked-in fast-path that uses this image + transparent
            # click zones over each tile.
            self.level_select_bg = None
            for cand in (
                resource_path(os.path.join("assets", "level_select_bg.jpg")),
                resource_path(os.path.join("assets", "level_select_bg.png")),
                resource_path(os.path.join("IMG", "level_select_bg.png")),
            ):
                if os.path.exists(cand):
                    raw = pygame.image.load(cand).convert()
                    self.level_select_bg = pygame.transform.smoothscale(raw, (SW, SH))
                    break

            # Animated title background — a folder of jpg/png frames looped
            # at 24 fps (matching the source video).  Falls back to the still
            # title_bg if the folder is missing or empty.
            self.title_bg_frames = []
            self.title_bg_fps = 24
            anim_dir = resource_path(os.path.join("assets", "title_anim"))
            if os.path.isdir(anim_dir):
                names = sorted(f for f in os.listdir(anim_dir)
                               if f.lower().endswith((".jpg", ".jpeg", ".png")))
                for fn in names:
                    try:
                        raw = pygame.image.load(os.path.join(anim_dir, fn)).convert()
                        frame = pygame.transform.smoothscale(raw, (SW, SH))
                        self.title_bg_frames.append(frame)
                    except Exception:
                        pass

            # Animated login/splash background — same scheme as title_anim.
            self.login_bg_frames = []
            self.login_bg_fps = 24
            login_dir = resource_path(os.path.join("assets", "login_anim"))
            if os.path.isdir(login_dir):
                names = sorted(f for f in os.listdir(login_dir)
                               if f.lower().endswith((".jpg", ".jpeg", ".png")))
                for fn in names:
                    try:
                        raw = pygame.image.load(os.path.join(login_dir, fn)).convert()
                        frame = pygame.transform.smoothscale(raw, (SW, SH))
                        self.login_bg_frames.append(frame)
                    except Exception:
                        pass

            # Title menu button PNGs (transparent, separated from the bg).
            self.title_btn_imgs = {}
            btn_files = {
                "CHIẾN ĐẤU":          "chien_dau.png",
                "SHOP":                "shop.png",
                "GA-RA":               "garage.png",
                "CHƠI MẠNG (PVP)":    "pvp.png",
                "CHƠI CHUNG (CO-OP)": "coop.png",
                "VÒNG QUAY":          "vong_quay.png",
                "GEAR":                "gear.png",
            }
            btn_dir = resource_path(os.path.join("assets", "buttons"))
            target_btn_w = 300
            gear_size = 170
            for lbl, fn in btn_files.items():
                bp = os.path.join(btn_dir, fn)
                if not os.path.exists(bp):
                    continue
                try:
                    raw = pygame.image.load(bp).convert_alpha()
                    if lbl == "GEAR":
                        img = pygame.transform.smoothscale(raw, (gear_size, gear_size))
                    else:
                        rw, rh = raw.get_size()
                        new_h = max(40, int(target_btn_w * rh / rw))
                        img = pygame.transform.smoothscale(raw, (target_btn_w, new_h))
                    self.title_btn_imgs[lbl] = img
                except Exception:
                    pass
        except Exception as e:
            print("Could not load custom UI assets:", e)

        # Defensive fallbacks in case the asset-loading block raised partway through
        if not hasattr(self, 'title_bg_frames'):
            self.title_bg_frames = []
        if not hasattr(self, 'title_bg_fps'):
            self.title_bg_fps = 24
        if not hasattr(self, 'title_bg'):
            self.title_bg = None
        if not hasattr(self, 'level_select_bg'):
            self.level_select_bg = None
        if not hasattr(self, 'title_btn_imgs'):
            self.title_btn_imgs = {}
        if not hasattr(self, 'login_bg_frames'):
            self.login_bg_frames = []
        if not hasattr(self, 'login_bg_fps'):
            self.login_bg_fps = 24

        # Garage / skin selection
        self.skin_idx = 0
        self.skin_names = ["NEKO KEM", "HOA ANH ĐÀO", "BAY GIỮA TRỜI",
                           "PHÙ THUỶ OẢI HƯƠNG", "CẦU VỒNG MAX"]
        self.unlocked_skins = {0}

        # Achievements (id -> (name_vi, desc_vi))
        self.achievement_defs = [
            ("FIRST_BLOOD", "DIỆT MỞ MÀN", "Diệt kẻ địch đầu tiên"),
            ("LEVEL_5", "VƯỢT MÀN 5", "Hoàn thành màn 5"),
            ("LEVEL_10", "VƯỢT MÀN 10", "Hoàn thành màn 10"),
            ("BOSS_SLAYER", "SÁT THỦ BOSS", "Hạ gục 1 Boss"),
            ("RICH", "PHÚ HỘ", "Tích luỹ 5000 vàng"),
            ("MAX_TIER", "TANK TỐI THƯỢNG", "Đạt tank cấp 4 (MAX)"),
            ("FROZEN_HUNTER", "THỢ SĂN BĂNG", "Dùng ĐÓNG BĂNG 3 lần"),
            ("GRENADIER", "PHÁO THỦ", "Dùng LỰU ĐẠN 5 lần"),
        ]
        self.achievements_unlocked = set()
        self.freeze_uses = 0
        self.grenade_uses = 0
        self.stats = {
            "max_combo": 0,
            "total_kills": 0,
            "bosses_killed": 0,
            "levels_completed": 0,
            "money_spent": 0,
        }

        # PVP properties - core
        self.pvp_is_host = False
        self.pvp_socket = None
        self.pvp_host_addr = None
        self.pvp_menu_sel = 0
        self.pvp_menu_options = ["TẠO PHÒNG (HOST)", "TÌM PHÒNG (JOIN)", "QUAY LẠI"]
        self.pvp_found_hosts = []
        self.pvp_last_sync = time.time()
        self.pvp_active = False
        self.pvp_winner = None  # slot index of winner, "DRAW", "DISCONNECT", or None
        self.pvp_winner_name = ""
        self.pvp_end_timer = 0
        self.pvp_join_sel = 0
        # PVP Multi-player slots (max 4)
        self.pvp_max_slots = 4
        self.pvp_min_start = 2
        self.pvp_clients = []  # HOST: list of dicts {addr, slot, name, pet, last_recv, inputs}
        self.pvp_my_slot = 0   # CLIENT: which slot I am (host=0, clients=1..3)
        self.pvp_others = []   # ALL: list of remote Tank instances (length = max_slots-1 once game starts)
        self.pvp_other_data = []  # ALL: parallel list of dicts {slot, name, pet, chat_msg, chat_timer,
                                  #   freeze_timer, target_x, target_y, interp_init, match_stats, alive, hp}
        self.pvp_lobby_view = []  # list of {slot, name, pet, is_host} shown in lobby (4 entries, empty if no one)
        # PVP Lobby / Prep
        self.pvp_prep_name = self.player_name
        self.pvp_prep_items = []
        self.pvp_prep_pet = self.active_pet_type
        self.pvp_prep_bet_mode = 0  # 0=fun, 1=bet
        self.pvp_prep_bet_amount = 100
        self.pvp_prep_map_size = 0  # 0=small(26x20), 1=medium(36x28), 2=large(46x34)
        self.pvp_prep_field = 0  # which field is active in prep screen
        self.pvp_name_editing = False
        self.pvp_map_sizes = [(26, 20), (36, 28), (46, 34)]
        self.pvp_map_size_names = ["Nhỏ (26x20)", "Vừa (36x28)", "Lớn (46x34)"]
        # PVP Match state
        self.pvp_timer = 0
        self.pvp_timer_max = 7200  # 120s * 60fps
        self.pvp_storm_active = False
        self.pvp_storm_layer = 0
        self.pvp_storm_timer = 0
        self.pvp_storm_warned = False
        self.pvp_map_items = []
        self.pvp_item_spawn_timer = 0
        self.pvp_mines = []
        self.pvp_freeze_timer = 0  # local player's freeze timer
        # PVP Chat
        self.pvp_chat_msg = ""
        self.pvp_chat_timer = 0
        self.pvp_chat_options = ["GG", "LOL", "Giỏi quá", "Thua rồi"]
        # PVP Stats
        self.pvp_match_stats = {"shots": 0, "hits": 0, "damage": 0, "items": 0}
        # PVP End/Rematch
        self.pvp_rematch_sent = False
        self.pvp_rematch_received = False
        self.pvp_rematch_timer = 0
        self.pvp_end_sel = 0
        # PVP Rank & Persistent (defaults, overridden by _load_save)
        self.pvp_rank = 0  # 0=Đồng, 1=Bạc, 2=Vàng, 3=Kim cương
        self.pvp_rank_names = ["Đồng", "Bạc", "Vàng", "Kim Cương"]
        self.pvp_wins = 0
        self.pvp_losses = 0
        self.pvp_daily_bonus_date = ""

        # ── Daily check-in (điểm danh) ──
        self.daily_last_claim_date = ""    # YYYY-MM-DD of last claim
        self.daily_streak = 0              # consecutive days
        self.daily_total_claims = 0
        self.daily_popup_seen_today = False
        self.daily_confetti = []           # particle list when claiming

        # Load saved data (overrides defaults above)
        self._load_save()
        self.pvp_combo_hits = 0
        self.pvp_combo_bonus = 0
        # PVP Room info & Bet
        self.pvp_room_info = {}
        self.pvp_bet_active = False
        self.pvp_bet_amount_match = 0
        # PVP local items/pet for match
        self.pvp_local_items = []
        self.pvp_local_pet = None
        self.pvp_last_recv = time.time()
        self.pvp_recv_thread = None
        self.pvp_recv_queue = []
        self.pvp_recv_lock = threading.Lock()
        self.pvp_manual_ip = ""  # For manual IP join fallback
        self.pvp_manual_ip_editing = False
        self.pvp_bind_error = ""  # Show bind errors to user

        # ── CO-OP state ──
        self.coop_active = False
        self.coop_is_host = False
        self.coop_socket = None
        self.coop_host_addr = None
        self.coop_menu_sel = 0
        self.coop_menu_options = ["TẠO PHÒNG (HOST)", "VÀO PHÒNG (JOIN)", "QUAY LẠI"]
        self.coop_found_hosts = []
        self.coop_clients = []  # HOST: list of {addr, slot, name, last_recv, inputs}
        self.coop_my_slot = 0
        self.coop_others = []   # Remote player Tank instances
        self.coop_other_data = []  # {slot, name, x, y, dir, hp, alive}
        self.coop_lobby_view = []
        self.coop_max_players = 4
        self.coop_prep_name = ""
        self.coop_recv_thread = None
        self.coop_recv_queue = []
        self.coop_recv_lock = threading.Lock()
        self.coop_last_sync = time.time()
        self.coop_last_recv = time.time()
        self.coop_manual_ip = ""
        self.coop_manual_ip_editing = False
        self.coop_bind_error = ""
        self.coop_level = 1  # current co-op level

        # ── CO-OP room configuration (host fills these on coop_prep) ──
        self.coop_prep_field = 0
        self.coop_prep_name_editing = False
        self.coop_prep_room_name_editing = False
        self.coop_prep_room_name = "Phòng Co-Op"
        self.coop_prep_level = 1
        self.coop_prep_difficulty = 1  # 0=Dễ, 1=Vừa, 2=Khó, 3=Địa Ngục
        self.coop_prep_lives = 3
        self.coop_prep_max_players = 4
        self.coop_prep_friendly_fire = False
        self.coop_prep_theme = "auto"  # "auto" or specific MAP_THEME key
        # Difficulty multipliers used at start_level
        self.coop_difficulty_names = ["Dễ", "Vừa", "Khó", "Địa Ngục"]
        # Room info propagated to clients
        self.coop_room_info = {
            "name": self.coop_prep_room_name,
            "diff": self.coop_prep_difficulty,
            "lives": self.coop_prep_lives,
            "ff": self.coop_prep_friendly_fire,
            "theme": self.coop_prep_theme,
        }

        # Pause
        self.pause_items = ["TIẾP TỤC", "CHƠI LẠI", "VÀO SHOP", "CÁCH CHƠI", "CÀI ĐẶT", "VỀ SẢNH", "THOÁT GAME"]
        self.pause_sel = 0

        # Shop
        self.shop_page = 0
        self.shop_sel = 0

        # Camera
        self.cam_x = 0
        self.cam_y = 0
        self.cam_zoom = 1.0
        self.target_zoom = 1.0

        # Tutorial page
        self.tutorial_page = 0

        # Title animation
        self.title_tanks = []
        for i in range(6):
            self.title_tanks.append({
                'x': random.randint(0, SW),
                'y': random.randint(50, SH - 100),
                'dir': random.randint(0, 3),
                'type': random.choice(["player", "enemy_a", "enemy_b", "elite"]),
                'speed': random.uniform(0.3, 1.0),
            })

    def _load_save(self):
        data = load_game_data()
        if data:
            self.money = data.get("money", 0)
            self.score = data.get("score", 0)
            self.gems = data.get("gems", 10)
            self.player_tier = data.get("player_tier", 0)
            self.total_kills = data.get("total_kills", 0)
            self.total_money_earned = data.get("total_money_earned", 0)
            raw_pets = data.get("owned_pets", [])
            self.owned_pets = [p[4:] if p.startswith("pet_") else p for p in raw_pets]
            self.backpack_slots = data.get("backpack_slots", 1)
            self.backpack = list(data.get("backpack") or [])
            self.active_pet_type = data.get("active_pet_type", None)
            unlocked = data.get("unlocked_levels", [1])
            self.unlocked_levels = set(unlocked)
            self.unlocked_skins = set(data.get("unlocked_skins", [0]))
            self.skin_idx = data.get("skin_idx", 0)
            # PVP persistent data
            self.pvp_wins = data.get("pvp_wins", 0)
            self.pvp_losses = data.get("pvp_losses", 0)
            self.pvp_rank = data.get("pvp_rank", 0)
            self.pvp_daily_bonus_date = data.get("pvp_daily_bonus_date", "")
            # Daily check-in restore
            self.daily_last_claim_date = data.get("daily_last_claim_date", "")
            self.daily_streak = data.get("daily_streak", 0)
            self.daily_total_claims = data.get("daily_total_claims", 0)
            self.player_name = data.get("player_name", self.player_name)
            self.pvp_prep_name = self.player_name
            self.pvp_prep_pet = self.active_pet_type
            # Stats and achievements
            saved_stats = data.get("stats", None)
            if saved_stats:
                for k, v in saved_stats.items():
                    self.stats[k] = v
            self.achievements_unlocked = set(data.get("achievements_unlocked", []))
            self.freeze_uses = data.get("freeze_uses", 0)
            self.grenade_uses = data.get("grenade_uses", 0)
            saved_settings = data.get("settings") or {}
            for k, v in saved_settings.items():
                if k in DEFAULT_SETTINGS:
                    self.settings[k] = v
            saved_kb = data.get("keybinds") or {}
            for k, v in saved_kb.items():
                if k in self.keybinds and isinstance(v, int):
                    self.keybinds[k] = v
            saved_login = data.get("login") or {}
            if saved_login.get("done"):
                self.login_done = True
                self.login_username = saved_login.get("username", self.player_name or "Player")
                self.login_provider = saved_login.get("provider", "")
                # Splash video still plays at every launch — but a single
                # click/key in the splash will jump straight to the lobby
                # without overwriting the saved profile.
            # Apply right away so the very first frame already respects the
            # user's preferences.
            try:
                apply_audio_settings(self.settings)
            except Exception:
                pass

    def _save_game(self):
        data = {
            "money": self.money,
            "score": self.score,
            "gems": self.gems,
            "player_tier": self.player_tier,
            "total_kills": self.total_kills,
            "total_money_earned": self.total_money_earned,
            "owned_pets": self.owned_pets,
            "active_pet_type": self.active_pet_type,
            "backpack_slots": self.backpack_slots,
            "backpack": list(self.backpack),
            "unlocked_levels": list(self.unlocked_levels),
            "unlocked_skins": list(self.unlocked_skins),
            "skin_idx": self.skin_idx,
            "pvp_wins": self.pvp_wins,
            "pvp_losses": self.pvp_losses,
            "pvp_rank": self.pvp_rank,
            "pvp_daily_bonus_date": self.pvp_daily_bonus_date,
            "daily_last_claim_date": self.daily_last_claim_date,
            "daily_streak": self.daily_streak,
            "daily_total_claims": self.daily_total_claims,
            "player_name": self.player_name,
            "stats": self.stats,
            "achievements_unlocked": list(self.achievements_unlocked),
            "freeze_uses": self.freeze_uses,
            "grenade_uses": self.grenade_uses,
            "settings": dict(self.settings),
            "keybinds": dict(self.keybinds),
            "login": {
                "done": self.login_done,
                "username": self.login_username,
                "provider": self.login_provider,
            },
        }
        save_game_data(data)

    def get_theme_for_level(self, level):
        """Per-level theme mapping that follows the world-map preview
        artwork — so the in-game tile palette matches the little
        thumbnail the player saw on the level-select screen."""
        level_theme_map = {
            1:  "jungle",  2:  "default", 3:  "desert", 4:  "city",
            5:  "city",    # boss
            6:  "jungle",  7:  "default", 8:  "jungle", 9:  "default",
            10: "city",    # boss
            11: "jungle", 12: "default", 13: "jungle", 14: "snow",
            15: "default", # boss
            16: "city",   17: "snow",   18: "city",   19: "desert",
            20: "lava",    # final boss
        }
        return level_theme_map.get(level, "default")


    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return socket.gethostbyname(socket.gethostname())


    def _pvp_cleanup(self):
        self.pvp_active = False
        if self.pvp_socket:
            try: self.pvp_socket.close()
            except Exception: pass
            self.pvp_socket = None
        if hasattr(self, '_pvp_broadcast_sock') and self._pvp_broadcast_sock:
            try: self._pvp_broadcast_sock.close()
            except Exception: pass
            self._pvp_broadcast_sock = None
        if hasattr(self, '_pvp_listen_sock') and self._pvp_listen_sock:
            try: self._pvp_listen_sock.close()
            except Exception: pass
            self._pvp_listen_sock = None
        self.pvp_host_addr = None
        self.pvp_clients = []
        self.pvp_others = []
        self.pvp_other_data = []
        self.pvp_lobby_view = []
        self.pvp_my_slot = 0
        self.pvp_recv_queue = []

    def _pvp_start_recv_thread(self):
        """Threaded receiver to avoid jitter in main loop."""
        def recv_loop():
            while self.pvp_active and self.pvp_socket:
                try:
                    data, addr = self.pvp_socket.recvfrom(65535)
                    with self.pvp_recv_lock:
                        self.pvp_recv_queue.append((data, addr))
                except socket.timeout:
                    pass
                except Exception:
                    break
        self.pvp_recv_thread = threading.Thread(target=recv_loop, daemon=True)
        self.pvp_recv_thread.start()

    def _pvp_lobby_snapshot(self):
        """Build a snapshot of the 4 lobby slots from the host's authoritative data."""
        slots = [None] * self.pvp_max_slots
        # Slot 0 is always the host
        slots[0] = {
            'slot': 0,
            'name': self.pvp_prep_name,
            'pet': self.pvp_prep_pet or '',
            'is_host': True,
            'skin': self.skin_idx,
        }
        for c in self.pvp_clients:
            si = c.get('slot', 0)
            if 0 < si < self.pvp_max_slots:
                slots[si] = {
                    'slot': si,
                    'name': c.get('name', f'P{si+1}'),
                    'pet': c.get('pet', '') or '',
                    'is_host': False,
                    'skin': c.get('skin', 0),
                }
        return slots

    def _pvp_count_lobby_players(self):
        """Number of filled lobby slots (host + clients)."""
        snap = self._pvp_lobby_snapshot()
        return sum(1 for s in snap if s is not None)

    def _pvp_send_lobby_to_all(self):
        """HOST: send latest lobby state to every joined client.
        Each client gets their own 'your_slot' so they don't need name matching."""
        if not self.pvp_is_host or not self.pvp_socket:
            return
        snap = self._pvp_lobby_snapshot()
        for c in self.pvp_clients:
            pkt = json.dumps({
                'type': 'lobby',
                'slots': snap,
                'min_start': self.pvp_min_start,
                'max_slots': self.pvp_max_slots,
                'room': self.pvp_room_info,
                'your_slot': c.get('slot', 1),  # Tell each client their slot directly
            }, ensure_ascii=False).encode('utf-8')
            try: self.pvp_socket.sendto(pkt, c['addr'])
            except Exception: pass

    def _pvp_broadcast_quit(self):
        """Send a 'quit' packet to all peers (host -> all clients, client -> host)."""
        if not self.pvp_socket:
            return
        try:
            quit_pkt = json.dumps({'type': 'quit'}).encode('utf-8')
        except Exception:
            return
        if self.pvp_is_host:
            for c in self.pvp_clients:
                try: self.pvp_socket.sendto(quit_pkt, c.get('addr'))
                except Exception: pass
        elif self.pvp_host_addr:
            try: self.pvp_socket.sendto(quit_pkt, self.pvp_host_addr)
            except Exception: pass

    def start_pvp_host(self):
        self._pvp_cleanup()
        self.pvp_is_host = True
        self.pvp_active = True
        self.pvp_my_slot = 0
        self.pvp_bind_error = ""
        self.pvp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pvp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bound = False
        for port in [5555, 5557, 5558, 5559]:
            try:
                self.pvp_socket.bind(('0.0.0.0', port))
                bound = True
                break
            except Exception:
                continue
        if not bound:
            self.pvp_bind_error = "Không thể bind port! Đóng game khác hoặc tắt firewall."
            self._pvp_cleanup()
            return False
        self.pvp_socket.settimeout(0.005)
        self.pvp_clients = []
        self._pvp_start_recv_thread()

        # Build room info for broadcast
        self.pvp_room_info = {
            'name': self.pvp_prep_name,
            'mode': 'bet' if self.pvp_prep_bet_mode == 1 else 'fun',
            'bet': self.pvp_prep_bet_amount if self.pvp_prep_bet_mode == 1 else 0,
            'map': self.pvp_prep_map_size,
            'map_name': self.pvp_map_size_names[self.pvp_prep_map_size],
            'max_slots': self.pvp_max_slots,
        }
        self.state = "pvp_waiting"
        # Host always shows up in lobby view
        self.pvp_lobby_view = self._pvp_lobby_snapshot()

        # Store the actual bound port for broadcast info
        host_port = self.pvp_socket.getsockname()[1]
        self.pvp_room_info['port'] = host_port

        def broadcast():
            b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._pvp_broadcast_sock = b_sock
            while self.pvp_active and self.pvp_is_host and self.state in ("pvp_waiting", "pvp_playing"):
                # Keep broadcasting even during play so late joiners can see the room
                try:
                    ip = self._get_local_ip()
                    # Include current player count so clients can show "1/4" etc.
                    info = dict(self.pvp_room_info)
                    info['players'] = self._pvp_count_lobby_players()
                    info['port'] = host_port
                    info_str = json.dumps(info, ensure_ascii=False)
                    msg = f"TANK_PVP_HOST|{ip}|{info_str}".encode('utf-8')
                    b_sock.sendto(msg, ('<broadcast>', 5556))
                except Exception: pass
                time.sleep(0.5)
            try: b_sock.close()
            except Exception: pass
            self._pvp_broadcast_sock = None
        threading.Thread(target=broadcast, daemon=True).start()

        # Deduct bet money for host
        if self.pvp_prep_bet_mode == 1:
            self.pvp_bet_active = True
            self.pvp_bet_amount_match = self.pvp_prep_bet_amount
            self.money -= self.pvp_prep_bet_amount
            self._save_game()

    def start_pvp_join(self):
        self._pvp_cleanup()
        self.pvp_is_host = False
        self.pvp_active = True
        self.pvp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pvp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: self.pvp_socket.bind(('0.0.0.0', 0))
        except Exception: pass
        self.pvp_socket.settimeout(0.005)
        self.pvp_host_addr = None
        self.state = "pvp_joining"
        self.pvp_found_hosts = []
        self.pvp_join_sel = 0
        self.pvp_manual_ip = ""
        self.pvp_manual_ip_editing = False
        self._pvp_start_recv_thread()

        def listen_broadcast():
            l_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            l_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # On Windows, also try SO_EXCLUSIVEADDRUSE=0 for port sharing
            try:
                l_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except Exception: pass
            self._pvp_listen_sock = l_sock
            try:
                l_sock.bind(('0.0.0.0', 5556))
                l_sock.settimeout(1.0)
                # Keep listening as long as we're in joining OR lobby state
                while self.pvp_active and self.state in ("pvp_joining", "pvp_lobby"):
                    try:
                        data, addr = l_sock.recvfrom(4096)
                        msg = data.decode('utf-8')
                        if msg.startswith("TANK_PVP_HOST"):
                            parts = msg.split("|", 2)
                            host_ip = parts[1] if len(parts) > 1 else addr[0]
                            room_info = {}
                            if len(parts) > 2:
                                try: room_info = json.loads(parts[2])
                                except Exception: pass
                            # Detect actual host port from room_info or use default
                            host_port = room_info.get('port', 5555)
                            # Update or add host
                            found = False
                            for i, h in enumerate(self.pvp_found_hosts):
                                if h[0] == host_ip:
                                    self.pvp_found_hosts[i] = (host_ip, host_port, room_info)
                                    found = True
                                    break
                            if not found:
                                self.pvp_found_hosts.append((host_ip, host_port, room_info))
                    except socket.timeout: pass
                    except Exception: pass
            except Exception as e:
                print(f"[PVP] Broadcast listen bind failed: {e}")
            finally:
                try: l_sock.close()
                except Exception: pass
                self._pvp_listen_sock = None
        threading.Thread(target=listen_broadcast, daemon=True).start()

    def connect_pvp_manual_ip(self, ip_str):
        """Connect to a host by manually entered IP address."""
        ip_str = ip_str.strip()
        if not ip_str:
            return
        # Support ip:port format
        if ':' in ip_str:
            parts = ip_str.split(':')
            ip = parts[0]
            try: port = int(parts[1])
            except Exception: port = 5555
        else:
            ip = ip_str
            port = 5555
        host_entry = (ip, port, {})
        self.connect_pvp_host(host_entry)

    def _init_pvp_map(self, cols=26, rows=20):
        global COLS, ROWS
        COLS, ROWS = cols, rows
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]
        self.map_theme = "default"
        weather.active = False
        # Border walls
        for y in range(ROWS):
            for x in range(COLS):
                if x == 0 or x == COLS - 1 or y == 0 or y == ROWS - 1:
                    self.grid[y][x] = STEEL
        # Symmetric cover layout
        mid_x, mid_y = COLS // 2, ROWS // 2
        pvp_walls = [
            (4, 4), (4, 5), (5, 4),
            (COLS-5, 4), (COLS-5, 5), (COLS-6, 4),
            (4, ROWS-5), (4, ROWS-6), (5, ROWS-5),
            (COLS-5, ROWS-5), (COLS-5, ROWS-6), (COLS-6, ROWS-5),
            (mid_x, 3), (mid_x, 4), (mid_x, ROWS-4), (mid_x, ROWS-5),
            (mid_x-1, mid_y), (mid_x+1, mid_y),
            (3, mid_y), (COLS-4, mid_y),
        ]
        # Extra walls for larger maps
        if cols >= 36:
            for dx in [-8, 8]:
                for dy in [-6, 6]:
                    wx, wy = mid_x + dx, mid_y + dy
                    if 1 <= wx < COLS-1 and 1 <= wy < ROWS-1:
                        pvp_walls.append((wx, wy))
                        pvp_walls.append((wx+1, wy))
                        pvp_walls.append((wx, wy+1))
        if cols >= 46:
            for dx in [-14, -7, 7, 14]:
                for dy in [-10, -5, 5, 10]:
                    wx, wy = mid_x + dx, mid_y + dy
                    if 1 <= wx < COLS-1 and 1 <= wy < ROWS-1:
                        pvp_walls.append((wx, wy))
        for wx, wy in pvp_walls:
            if 1 <= wx < COLS-1 and 1 <= wy < ROWS-1:
                self.grid[wy][wx] = BRICK
        steel_spots = [
            (mid_x, mid_y), (6, 6), (COLS-7, ROWS-7), (6, ROWS-7), (COLS-7, 6),
        ]
        for sx, sy in steel_spots:
            if 1 <= sx < COLS-1 and 1 <= sy < ROWS-1:
                self.grid[sy][sx] = STEEL

    def connect_pvp_host(self, host_info):
        host_addr = (host_info[0], host_info[1])
        self.pvp_host_addr = host_addr
        self.pvp_join_time = time.time()
        self.pvp_connecting = True
        room_info = host_info[2] if len(host_info) > 2 else {}
        # Deduct bet for client
        if room_info.get('mode') == 'bet':
            bet = room_info.get('bet', 0)
            self.pvp_bet_active = True
            self.pvp_bet_amount_match = bet
            self.money -= bet
            self._save_game()
        else:
            self.pvp_bet_active = False
            self.pvp_bet_amount_match = 0
        # Send join with player info
        join_data = json.dumps({
            'type': 'join',
            'name': self.pvp_prep_name,
            'items': self.pvp_prep_items,
            'pet': self.pvp_prep_pet,
            'skin': self.skin_idx,
        }, ensure_ascii=False).encode('utf-8')
        try: self.pvp_socket.sendto(join_data, host_addr)
        except Exception: pass

    # Spawn corners for up to 4 players: top-left, bottom-right, top-right, bottom-left
    def _pvp_spawn_corner(self, slot):
        corners = [(2, 2), (COLS - 3, ROWS - 3), (COLS - 3, 2), (2, ROWS - 3)]
        return corners[slot % len(corners)]

    def start_pvp_game(self, cols=26, rows=20, lobby_slots=None):
        """Start the match. lobby_slots is the authoritative list from the host:
        [{slot, name, pet, is_host}, ...] of length pvp_max_slots, with None for empty.
        For HOST, lobby_slots is built from pvp_clients. For CLIENT, lobby_slots is
        received in the 'start' packet so it knows everyone's identity and its own slot.
        """
        self._init_pvp_map(cols, rows)
        self.state = "pvp_playing"

        # Normalize lobby_slots
        if not lobby_slots:
            lobby_slots = [None] * self.pvp_max_slots
            lobby_slots[0] = {'slot': 0, 'name': self.pvp_prep_name,
                              'pet': self.pvp_prep_pet or '', 'is_host': True, 'skin': self.skin_idx}

        # Determine my slot
        if self.pvp_is_host:
            self.pvp_my_slot = 0
            if lobby_slots[0] is not None:
                lobby_slots[0]['skin'] = self.skin_idx
        # client's self.pvp_my_slot has already been set in receive 'start'

        # Spawn local player at its slot corner
        my_corner = self._pvp_spawn_corner(self.pvp_my_slot)
        self.player = Tank(my_corner[0], my_corner[1], "player")
        self.player.hp = 3
        self.player.max_hp = 3
        self.player.name = self.pvp_prep_name
        # Apply skin from lobby info if available
        if lobby_slots[self.pvp_my_slot] is not None:
            self.player.tier = lobby_slots[self.pvp_my_slot].get('skin', self.skin_idx)
        else:
            self.player.tier = self.skin_idx

        # Build pvp_others list for every other (non-empty) slot
        self.pvp_others = []
        self.pvp_other_data = []
        for si, entry in enumerate(lobby_slots):
            if si == self.pvp_my_slot or entry is None:
                continue
            cx, cy = self._pvp_spawn_corner(si)
            t = Tank(cx, cy, "player")
            t.hp = 3
            t.max_hp = 3
            t.tier = entry.get('skin', 0)
            t.name = entry.get('name', f'P{si+1}')
            self.pvp_others.append(t)
            self.pvp_other_data.append({
                'slot': si,
                'name': t.name,
                'pet': entry.get('pet', ''),
                'chat_msg': '',
                'chat_timer': 0,
                'freeze_timer': 0,
                'target_x': t.x,
                'target_y': t.y,
                'interp_init': True,
                'match_stats': {"shots": 0, "hits": 0, "damage": 0, "items": 0},
                'is_host': entry.get('is_host', False),
            })

        # Clear entities
        self.enemies = []
        self.chickens = []
        self.dogs = []
        self.bullets = []
        self.explosions = []
        self.items = []
        self.pvp_map_items = []
        self.pvp_mines = []
        self.pvp_winner = None
        self.pvp_winner_name = ""
        self.pvp_end_timer = 0
        # Timer & storm
        self.pvp_timer = 0
        self.pvp_storm_active = False
        self.pvp_storm_layer = 0
        self.pvp_storm_timer = 0
        self.pvp_storm_warned = False
        self.pvp_item_spawn_timer = 0
        # Freeze
        self.pvp_freeze_timer = 0
        # Chat
        self.pvp_chat_msg = ""
        self.pvp_chat_timer = 0
        # Stats
        self.pvp_match_stats = {"shots": 0, "hits": 0, "damage": 0, "items": 0}
        self.pvp_combo_hits = 0
        self.pvp_combo_bonus = 0
        # Rematch
        self.pvp_rematch_sent = False
        self.pvp_rematch_received = False
        self.pvp_rematch_timer = 0
        self.pvp_end_sel = 0
        # Items brought to match
        self.pvp_local_items = list(self.pvp_prep_items)
        # Camera zoom based on map size
        map_factor = max(COLS / 26.0, ROWS / 20.0)
        self.target_zoom = min(1.2, max(0.7, 1.2 / map_factor))
        self.cam_zoom = self.target_zoom
        self.cam_x = self.player.x - (SW / self.cam_zoom) / 2
        self.cam_y = self.player.y - (SH / self.cam_zoom) / 2
        # Pet
        if self.pvp_prep_pet and self.pvp_prep_pet in self.owned_pets:
            self.pvp_local_pet = Pet(self.pvp_prep_pet, self.player)
        else:
            self.pvp_local_pet = None
        self.pvp_last_sync = time.time()
        self.pvp_last_recv = time.time()
        # Daily bonus check
        today = time.strftime("%Y-%m-%d")
        if self.pvp_daily_bonus_date != today:
            self.pvp_daily_bonus_date = today
            bonus = 50
            self.money += bonus
            self._save_game()

    def _pvp_spawn_map_items(self):
        """Spawn 5-8 random items on the map."""
        item_types = ["health", "shield", "speed", "rapid", "multi", "freeze", "mine", "teleport"]
        count = random.randint(5, 8)
        for _ in range(count):
            for attempt in range(20):
                gx = random.randint(2, COLS - 3)
                gy = random.randint(2, ROWS - 3)
                if self.grid[gy][gx] == EMPTY:
                    kind = random.choice(item_types)
                    self.pvp_map_items.append({'gx': gx, 'gy': gy, 'kind': kind, 'alive': True})
                    break

    def _pvp_apply_storm(self):
        """Remove one layer of border tiles to shrink the arena."""
        layer = self.pvp_storm_layer + 1
        changed = False
        for y in range(ROWS):
            for x in range(COLS):
                if x == layer or x == COLS - 1 - layer or y == layer or y == ROWS - 1 - layer:
                    if x >= layer and x <= COLS - 1 - layer and y >= layer and y <= ROWS - 1 - layer:
                        if self.grid[y][x] != STEEL and self.grid[y][x] != WATER:
                            self.grid[y][x] = WATER
                            changed = True
        if changed:
            self.pvp_storm_layer = layer

    def _pvp_host_start_match(self):
        """HOST: kick off the match for all current lobby players. Sends a
        per-client 'start' packet (each client receives its own 'your_slot')."""
        if not self.pvp_is_host or self.state != "pvp_waiting":
            return
        if self._pvp_count_lobby_players() < self.pvp_min_start:
            return
        snap = self._pvp_lobby_snapshot()
        cols, rows = self.pvp_map_sizes[self.pvp_prep_map_size]
        self.start_pvp_game(cols, rows, lobby_slots=snap)
        self._pvp_prev_grid = [row[:] for row in self.grid]
        for c in self.pvp_clients:
            init_pkt = json.dumps({
                'type': 'start',
                'grid': self.grid,
                'cols': COLS, 'rows': ROWS,
                'slots': snap,
                'your_slot': c.get('slot', 1),
                'bet': self.pvp_bet_amount_match if self.pvp_bet_active else 0,
                'bet_mode': 'bet' if self.pvp_bet_active else 'fun',
            }, ensure_ascii=False).encode('utf-8')
            try: self.pvp_socket.sendto(init_pkt, c['addr'])
            except Exception: pass

    def _pvp_find_client_by_addr(self, addr):
        for c in self.pvp_clients:
            if c.get('addr') == addr:
                return c
        return None

    def _pvp_find_slot_data(self, slot):
        """Find the pvp_other_data entry for a slot."""
        for d in self.pvp_other_data:
            if d.get('slot') == slot:
                return d
        return None

    def _pvp_find_slot_tank(self, slot):
        """Find the pvp_others Tank for a slot, paired with its data entry."""
        for t, d in zip(self.pvp_others, self.pvp_other_data):
            if d.get('slot') == slot:
                return t, d
        return None, None

    def update_pvp(self):
        global COLS, ROWS
        if not self.pvp_socket:
            return

        # Process received packets from thread
        packets = []
        with self.pvp_recv_lock:
            packets = list(self.pvp_recv_queue)
            self.pvp_recv_queue.clear()

        if self.pvp_is_host:
            # =========================================================
            # HOST LOGIC
            # =========================================================
            for data, addr in packets:
                try:
                    # Handle zlib-compressed packets (prefixed with 'Z')
                    if data[:1] == b'Z':
                        data = zlib.decompress(data[1:])
                    pkt = json.loads(data.decode('utf-8'))
                except Exception:
                    continue
                ptype = pkt.get('type') if isinstance(pkt, dict) else None

                if ptype == 'join' and self.state == 'pvp_waiting':
                    # Either existing client refreshing, or a new client
                    existing = self._pvp_find_client_by_addr(addr)
                    if existing is not None:
                        existing['name'] = pkt.get('name', existing.get('name', ''))
                        existing['pet'] = pkt.get('pet', existing.get('pet', ''))
                        existing['skin'] = pkt.get('skin', existing.get('skin', 0))
                        existing['last_recv'] = time.time()
                    else:
                        # Find first empty slot >0
                        taken = {c['slot'] for c in self.pvp_clients}
                        slot = None
                        for si in range(1, self.pvp_max_slots):
                            if si not in taken:
                                slot = si
                                break
                        if slot is None:
                            # Room full - notify and ignore
                            try:
                                full_pkt = json.dumps({'type': 'full'}).encode('utf-8')
                                self.pvp_socket.sendto(full_pkt, addr)
                            except Exception: pass
                            continue
                        self.pvp_clients.append({
                            'addr': addr,
                            'slot': slot,
                            'name': pkt.get('name', f'P{slot+1}'),
                            'pet': pkt.get('pet', ''),
                            'skin': pkt.get('skin', 0),
                            'last_recv': time.time(),
                            'inputs': {},
                        })
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()

                elif ptype == 'leave' and self.state == 'pvp_waiting':
                    self.pvp_clients = [c for c in self.pvp_clients if c.get('addr') != addr]
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()

                elif ptype == 'input' and self.state == 'pvp_playing':
                    c = self._pvp_find_client_by_addr(addr)
                    if c is not None:
                        c['inputs'] = pkt
                        c['last_recv'] = time.time()
                        if pkt.get('chat'):
                            d = self._pvp_find_slot_data(c['slot'])
                            if d is not None:
                                d['chat_msg'] = pkt['chat']
                                d['chat_timer'] = 180

                elif ptype == 'rematch':
                    self.pvp_rematch_received = True

                elif ptype == 'quit':
                    if self.state == 'pvp_playing':
                        # Kill that opponent's tank
                        c = self._pvp_find_client_by_addr(addr)
                        if c is not None:
                            t, d = self._pvp_find_slot_tank(c['slot'])
                            if t is not None:
                                t.alive = False
                        # Remove from clients
                        self.pvp_clients = [cc for cc in self.pvp_clients if cc.get('addr') != addr]

            # Host lobby tick: re-send lobby state periodically so late clients sync
            if self.state == 'pvp_waiting':
                now = time.time()
                if now - self.pvp_last_sync > 0.5:
                    self.pvp_last_sync = now
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()

            # Host simulation
            if self.state in ('pvp_playing', 'pvp_end'):
                # Tick all tanks
                self.player.update()
                for t in self.pvp_others:
                    t.update()

                # Local freeze
                if self.pvp_freeze_timer > 0:
                    self.pvp_freeze_timer -= 1
                # Other freezes
                for d in self.pvp_other_data:
                    if d.get('freeze_timer', 0) > 0:
                        d['freeze_timer'] -= 1

                # Move opponents from their inputs
                for c in self.pvp_clients:
                    slot = c['slot']
                    t, d = self._pvp_find_slot_tank(slot)
                    if t is None or not t.alive or t.spawn_timer > 0:
                        continue
                    if d.get('freeze_timer', 0) > 0:
                        continue
                    inp = c.get('inputs', {})
                    # Build other tanks list (exclude this tank)
                    others_list = [self.player] + [o for o in self.pvp_others if o is not t]
                    mdx = mdy = 0
                    if inp.get('up'): mdy -= 1
                    if inp.get('down'): mdy += 1
                    if inp.get('left'): mdx -= 1
                    if inp.get('right'): mdx += 1
                    
                    is_moving = mdx != 0 or mdy != 0
                    if is_moving and inp.get('sprint') and t.energy > 0:
                        t.sprint_multiplier = 1.8
                        t.energy = max(0, t.energy - 0.5)
                    else:
                        t.sprint_multiplier = 1.0
                        if t.energy < t.max_energy:
                            t.energy = min(t.max_energy, t.energy + 0.15)

                    if mdx != 0 or mdy != 0:
                        mag = math.hypot(mdx, mdy)
                        t.move(mdx / mag * t.speed * t.sprint_multiplier, mdy / mag * t.speed * t.sprint_multiplier, self.grid, others_list)
                    if 'dir' in inp:
                        t.dir = inp['dir']
                    if inp.get('shoot'):
                        new_bullets = t.shoot(inp.get('ang'))
                        if new_bullets:
                            d['match_stats']['shots'] += len(new_bullets)
                            for b in new_bullets:
                                b.owner = "enemy"
                                b.shooter_slot = slot
                            self.bullets.extend(new_bullets)

                # Local player (host) input
                if self.player.alive and self.player.spawn_timer <= 0 and self.pvp_freeze_timer <= 0:
                    keys = pygame.key.get_pressed()
                    mdx = mdy = 0
                    if keys[pygame.K_UP] or keys[pygame.K_w]: mdy -= 1
                    if keys[pygame.K_DOWN] or keys[pygame.K_s]: mdy += 1
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]: mdx -= 1
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: mdx += 1
                    
                    is_moving = mdx != 0 or mdy != 0
                    if is_moving and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.player.energy > 0:
                        self.player.sprint_multiplier = 1.8
                        self.player.energy = max(0, self.player.energy - 0.5)
                    else:
                        self.player.sprint_multiplier = 1.0
                        if self.player.energy < self.player.max_energy:
                            self.player.energy = min(self.player.max_energy, self.player.energy + 0.15)

                    others_list = list(self.pvp_others)
                    if mdx != 0 or mdy != 0:
                        mag = math.hypot(mdx, mdy)
                        self.player.move(mdx / mag * self.player.speed * self.player.sprint_multiplier,
                                         mdy / mag * self.player.speed * self.player.sprint_multiplier,
                                         self.grid, others_list)
                    
                    # Update local player direction based on mouse aiming
                    mx_phys, my_phys = pygame.mouse.get_pos()
                    mx_logical = mx_phys * (SW / phys_w)
                    my_logical = my_phys * (SH / phys_h)
                    
                    cam_x = getattr(self, 'cam_x', 0)
                    cam_y = getattr(self, 'cam_y', 0)
                    cam_zoom = getattr(self, 'cam_zoom', 1.0)
                    mx_map = cam_x + mx_logical / cam_zoom
                    my_map = cam_y + my_logical / cam_zoom
                    
                    pdx = mx_map - self.player.x
                    pdy = my_map - self.player.y
                    if pdx != 0 or pdy != 0:
                        if abs(pdx) > abs(pdy):
                            self.player.dir = 1 if pdx > 0 else 3
                        else:
                            self.player.dir = 0 if pdy < 0 else 2
                            
                    if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:
                        target_angle = math.atan2(my_map - self.player.y, mx_map - self.player.x)
                        new_bullets = self.player.shoot(target_angle)
                        if new_bullets:
                            self.pvp_match_stats["shots"] += len(new_bullets)
                            for b in new_bullets:
                                b.owner = "player"
                                b.shooter_slot = 0
                            self.bullets.extend(new_bullets)

                # Bullet collision
                for b in self.bullets[:]:
                    b.update()
                    gx, gy = int(b.x // TS), int(b.y // TS)
                    if gx < 0 or gy < 0 or gx >= COLS or gy >= ROWS:
                        if b in self.bullets: self.bullets.remove(b)
                        continue
                    tile = self.grid[gy][gx]
                    if tile == STEEL or tile == WATER:
                        if b in self.bullets:
                            self.bullets.remove(b)
                            self.explosions.append(Explosion(b.x, b.y))
                        continue
                    if tile == BRICK:
                        self.grid[gy][gx] = EMPTY
                        if b in self.bullets:
                            self.bullets.remove(b)
                            self.explosions.append(Explosion(b.x, b.y))
                        continue
                    # Hit detection vs all tanks (cannot hit own shooter)
                    shooter = getattr(b, 'shooter_slot', None)
                    hit_anyone = False
                    # Check host's player (slot 0)
                    if shooter != 0 and self.player.alive:
                        if math.hypot(b.x - self.player.x, b.y - self.player.y) < TS * 0.45:
                            self.player.hit(b.power)
                            # Credit shooter
                            if shooter is not None and shooter > 0:
                                d = self._pvp_find_slot_data(shooter)
                                if d is not None:
                                    d['match_stats']['hits'] += 1
                                    d['match_stats']['damage'] += b.power
                            hit_anyone = True
                    if not hit_anyone:
                        for t, d in zip(self.pvp_others, self.pvp_other_data):
                            if d['slot'] == shooter or not t.alive:
                                continue
                            if math.hypot(b.x - t.x, b.y - t.y) < TS * 0.45:
                                t.hit(b.power)
                                if shooter == 0:
                                    self.pvp_match_stats['hits'] += 1
                                    self.pvp_match_stats['damage'] += b.power
                                    self.pvp_combo_hits += 1
                                    if self.pvp_combo_hits >= 3:
                                        self.pvp_combo_bonus += 20
                                elif shooter is not None:
                                    sd = self._pvp_find_slot_data(shooter)
                                    if sd is not None:
                                        sd['match_stats']['hits'] += 1
                                        sd['match_stats']['damage'] += b.power
                                hit_anyone = True
                                break
                    if hit_anyone:
                        if b in self.bullets:
                            self.bullets.remove(b)
                            self.explosions.append(Explosion(b.x, b.y))

                # Mine collision
                for mine in self.pvp_mines[:]:
                    m_owner = mine.get('shooter_slot', 0)
                    # check all tanks except owner
                    all_tanks = [(0, self.player)] + [(d['slot'], t) for t, d in zip(self.pvp_others, self.pvp_other_data)]
                    for slot, tk in all_tanks:
                        if slot == m_owner or not tk.alive:
                            continue
                        if math.hypot(tk.x - mine['x'], tk.y - mine['y']) < TS * 0.5:
                            tk.hit(2)
                            self.explosions.append(Explosion(mine['x'], mine['y']))
                            if mine in self.pvp_mines:
                                self.pvp_mines.remove(mine)
                            break

                # Map item pickup
                for mi in self.pvp_map_items[:]:
                    if not mi['alive']:
                        continue
                    ix = mi['gx'] * TS + TS // 2
                    iy = mi['gy'] * TS + TS // 2
                    if math.hypot(self.player.x - ix, self.player.y - iy) < TS * 0.6:
                        mi['alive'] = False
                        self.pvp_match_stats["items"] += 1
                        self._pvp_apply_item(mi['kind'], 0)
                        continue
                    for t, d in zip(self.pvp_others, self.pvp_other_data):
                        if not t.alive: continue
                        if math.hypot(t.x - ix, t.y - iy) < TS * 0.6:
                            mi['alive'] = False
                            d['match_stats']['items'] += 1
                            self._pvp_apply_item(mi['kind'], d['slot'])
                            break

                # Explosions
                for e in self.explosions[:]:
                    e.update()
                    if e.done: self.explosions.remove(e)

                # Pet update (host's own pet only)
                if self.pvp_local_pet and self.pvp_local_pet.alive:
                    enemies_for_pet = [t for t in self.pvp_others if t.alive]
                    pet_bullets = self.pvp_local_pet.update(enemies_for_pet, [], self)
                    if pet_bullets:
                        for b in pet_bullets:
                            b.owner = "player"
                            b.shooter_slot = 0
                        self.bullets.extend(pet_bullets)

                # Timer & storm
                self.pvp_timer += 1
                if self.pvp_timer >= 3000 and not self.pvp_storm_warned:
                    self.pvp_storm_warned = True
                if self.pvp_timer >= 3600:
                    self.pvp_storm_active = True
                    self.pvp_storm_timer += 1
                    if self.pvp_storm_timer >= 120:
                        self.pvp_storm_timer = 0
                        max_layer = min(COLS, ROWS) // 2 - 2
                        if self.pvp_storm_layer < max_layer:
                            self._pvp_apply_storm()
                self.pvp_item_spawn_timer += 1
                if self.pvp_item_spawn_timer >= 1800:
                    self.pvp_item_spawn_timer = 0
                    self._pvp_spawn_map_items()

                # Win condition: last one standing wins
                if not self.pvp_winner:
                    alive_slots = []
                    if self.player.alive: alive_slots.append(0)
                    for t, d in zip(self.pvp_others, self.pvp_other_data):
                        if t.alive: alive_slots.append(d['slot'])
                    if len(alive_slots) <= 1:
                        if len(alive_slots) == 1:
                            winner_slot = alive_slots[0]
                            self.pvp_winner = winner_slot
                            if winner_slot == 0:
                                self.pvp_winner_name = self.pvp_prep_name
                            else:
                                d = self._pvp_find_slot_data(winner_slot)
                                self.pvp_winner_name = d['name'] if d else f'P{winner_slot+1}'
                        else:
                            self.pvp_winner = "DRAW"
                            self.pvp_winner_name = ""
                        self.pvp_end_timer = 300

                # Timer expiry: highest HP wins, ties -> draw
                if self.pvp_timer >= self.pvp_timer_max and not self.pvp_winner:
                    best_hp = self.player.hp if self.player.alive else -1
                    best_slot = 0 if self.player.alive else None
                    tie = False
                    for t, d in zip(self.pvp_others, self.pvp_other_data):
                        if not t.alive: continue
                        if t.hp > best_hp:
                            best_hp = t.hp; best_slot = d['slot']; tie = False
                        elif t.hp == best_hp:
                            tie = True
                    if best_slot is None or tie:
                        self.pvp_winner = "DRAW"
                        self.pvp_winner_name = ""
                    else:
                        self.pvp_winner = best_slot
                        if best_slot == 0:
                            self.pvp_winner_name = self.pvp_prep_name
                        else:
                            d = self._pvp_find_slot_data(best_slot)
                            self.pvp_winner_name = d['name'] if d else f'P{best_slot+1}'
                    self.pvp_end_timer = 300

                if self.pvp_winner is not None and self.pvp_end_timer == 300:
                    self._pvp_handle_match_end()

                # Chat timers
                if self.pvp_chat_timer > 0: self.pvp_chat_timer -= 1
                for d in self.pvp_other_data:
                    if d.get('chat_timer', 0) > 0: d['chat_timer'] -= 1

                # Broadcast state
                now = time.time()
                if now - self.pvp_last_sync > 0.033:
                    grid_changes = []
                    if not hasattr(self, '_pvp_prev_grid'):
                        self._pvp_prev_grid = [row[:] for row in self.grid]
                    for gy2 in range(len(self.grid)):
                        for gx2 in range(len(self.grid[gy2])):
                            if self.grid[gy2][gx2] != self._pvp_prev_grid[gy2][gx2]:
                                grid_changes.append([gx2, gy2, self.grid[gy2][gx2]])
                                self._pvp_prev_grid[gy2][gx2] = self.grid[gy2][gx2]

                    players_data = [{
                        'slot': 0,
                        'x': round(self.player.x, 1),
                        'y': round(self.player.y, 1),
                        'dir': self.player.dir,
                        'hp': self.player.hp,
                        'alive': self.player.alive,
                        'energy': int(self.player.energy),
                    }]
                    for t, d in zip(self.pvp_others, self.pvp_other_data):
                        players_data.append({
                            'slot': d['slot'],
                            'x': round(t.x, 1),
                            'y': round(t.y, 1),
                            'dir': t.dir,
                            'hp': t.hp,
                            'alive': t.alive,
                            'energy': int(t.energy),
                        })
                    frz = {0: self.pvp_freeze_timer}
                    for d in self.pvp_other_data:
                        frz[d['slot']] = d.get('freeze_timer', 0)
                    chats = {}
                    if self.pvp_chat_msg and self.pvp_chat_timer > 150:
                        chats[0] = self.pvp_chat_msg
                    for d in self.pvp_other_data:
                        if d.get('chat_msg') and d.get('chat_timer', 0) > 150:
                            chats[d['slot']] = d['chat_msg']

                    state_data = {
                        'type': 'state',
                        'players': players_data,
                        'b': [{'x': round(b.x, 1), 'y': round(b.y, 1),
                               'dir': b.dir, 'k': b.kind,
                               'o': b.owner, 's': getattr(b, 'shooter_slot', 0)}
                              for b in self.bullets],
                        'e': [{'x': round(e.x, 1), 'y': round(e.y, 1)} for e in self.explosions],
                        'w': self.pvp_winner,
                        'wn': self.pvp_winner_name,
                        't': self.pvp_timer,
                        'storm': self.pvp_storm_layer,
                        'mi': [{'gx': m['gx'], 'gy': m['gy'], 'k': m['kind']}
                               for m in self.pvp_map_items if m['alive']],
                        'mn': [{'x': m['x'], 'y': m['y'], 's': m.get('shooter_slot', 0)}
                               for m in self.pvp_mines],
                        'frz': {str(k): v for k, v in frz.items()},
                        'chat': {str(k): v for k, v in chats.items()},
                    }
                    if grid_changes:
                        state_data['gc'] = grid_changes
                    if self.pvp_rematch_sent:
                        state_data['rematch'] = True
                    try:
                        msg = json.dumps(state_data, separators=(',', ':')).encode('utf-8')
                        # Compress if packet is large (>4KB) to avoid UDP fragmentation
                        if len(msg) > 4096:
                            compressed = zlib.compress(msg, level=1)
                            msg = b'Z' + compressed  # 'Z' prefix = zlib compressed
                        for c in self.pvp_clients:
                            try: self.pvp_socket.sendto(msg, c['addr'])
                            except Exception: pass
                    except Exception: pass
                    self.pvp_last_sync = now

                # Timeout per-client
                now = time.time()
                stale = []
                for c in self.pvp_clients:
                    if now - c.get('last_recv', now) > 4.0:
                        stale.append(c)
                for c in stale:
                    t, d = self._pvp_find_slot_tank(c['slot'])
                    if t is not None:
                        t.alive = False
                    self.pvp_clients.remove(c)

            # End-timer countdown / rematch (host)
            if self.pvp_winner is not None and self.pvp_end_timer > 0:
                self.pvp_end_timer -= 1
                if self.pvp_rematch_sent and self.pvp_rematch_received:
                    snap = self._pvp_lobby_snapshot()
                    cols, rows = self.pvp_map_sizes[self.pvp_prep_map_size]
                    self.start_pvp_game(cols, rows, lobby_slots=snap)
                    self._pvp_prev_grid = [row[:] for row in self.grid]
                    for c in self.pvp_clients:
                        init_pkt = json.dumps({
                            'type': 'start',
                            'grid': self.grid, 'cols': COLS, 'rows': ROWS,
                            'slots': snap, 'your_slot': c.get('slot', 1),
                            'bet': 0, 'bet_mode': 'fun', 'rematch': True,
                        }, ensure_ascii=False).encode('utf-8')
                        try: self.pvp_socket.sendto(init_pkt, c['addr'])
                        except Exception: pass
                    return

        else:
            # =========================================================
            # CLIENT LOGIC
            # =========================================================
            # Resend join while connecting OR while in lobby
            if self.state in ("pvp_joining", "pvp_lobby") and self.pvp_host_addr:
                now = time.time()
                if now - getattr(self, 'pvp_join_time', 0) > 1.0 or getattr(self, 'pvp_needs_join_resend', False):
                    join_data = json.dumps({
                        'type': 'join', 'name': self.pvp_prep_name,
                        'items': self.pvp_prep_items, 'pet': self.pvp_prep_pet,
                        'skin': self.skin_idx,
                    }, ensure_ascii=False).encode('utf-8')
                    try: self.pvp_socket.sendto(join_data, self.pvp_host_addr)
                    except Exception: pass
                    self.pvp_join_time = now
                    self.pvp_needs_join_resend = False

            # Send inputs while playing or in end screen to prevent timeout
            if self.state in ('pvp_playing', 'pvp_end') and self.pvp_host_addr:
                keys = pygame.key.get_pressed()
                mx_phys, my_phys = pygame.mouse.get_pos()
                mx_logical = mx_phys * (SW / phys_w)
                my_logical = my_phys * (SH / phys_h)
                
                cam_x = getattr(self, 'cam_x', 0)
                cam_y = getattr(self, 'cam_y', 0)
                cam_zoom = getattr(self, 'cam_zoom', 1.0)
                mx_map = cam_x + mx_logical / cam_zoom
                my_map = cam_y + my_logical / cam_zoom
                
                pdx = mx_map - self.player.x
                pdy = my_map - self.player.y
                aimed_dir = self.player.dir
                if pdx != 0 or pdy != 0:
                    if abs(pdx) > abs(pdy):
                        aimed_dir = 1 if pdx > 0 else 3
                    else:
                        aimed_dir = 0 if pdy < 0 else 2
                
                inputs = {
                    'type': 'input',
                    'up': bool(keys[pygame.K_UP] or keys[pygame.K_w]),
                    'down': bool(keys[pygame.K_DOWN] or keys[pygame.K_s]),
                    'left': bool(keys[pygame.K_LEFT] or keys[pygame.K_a]),
                    'right': bool(keys[pygame.K_RIGHT] or keys[pygame.K_d]),
                    'shoot': bool(keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]),
                    'sprint': bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]),
                    'dir': aimed_dir,
                    'ang': float(math.atan2(my_map - self.player.y, mx_map - self.player.x))
                }
                if self.pvp_chat_msg and self.pvp_chat_timer > 150:
                    inputs['chat'] = self.pvp_chat_msg
                try: self.pvp_socket.sendto(json.dumps(inputs).encode('utf-8'), self.pvp_host_addr)
                except Exception: pass

            # Process packets
            for data, addr in packets:
                try:
                    # Handle zlib-compressed packets (prefixed with 'Z')
                    if data[:1] == b'Z':
                        data = zlib.decompress(data[1:])
                    pkt = json.loads(data.decode('utf-8'))
                except Exception:
                    continue
                ptype = pkt.get('type') if isinstance(pkt, dict) else None
                self.pvp_last_recv = time.time()

                if ptype == 'lobby':
                    self.pvp_lobby_view = pkt.get('slots', [])
                    self.pvp_room_info = pkt.get('room', self.pvp_room_info)
                    if self.state == 'pvp_joining':
                        self.state = 'pvp_lobby'
                        self.pvp_connecting = False
                    # Use host-assigned your_slot if provided (reliable)
                    if 'your_slot' in pkt:
                        self.pvp_my_slot = pkt['your_slot']
                    else:
                        # Fallback: determine my_slot by looking up my name
                        for s in self.pvp_lobby_view:
                            if s and s.get('name') == self.pvp_prep_name and not s.get('is_host'):
                                self.pvp_my_slot = s.get('slot', 1)
                                break

                elif ptype == 'full':
                    floating_texts.append(FloatingText(SW // 2, SH // 2,
                        "PHÒNG ĐÃ ĐẦY!", (255, 100, 100), center_bounce=True))
                    # Refund and return
                    if self.pvp_bet_active:
                        self.money += self.pvp_bet_amount_match
                        self.pvp_bet_active = False
                    self._pvp_cleanup()
                    self.state = "pvp_menu"

                elif ptype == 'start':
                    self.grid = pkt['grid']
                    ROWS = len(self.grid)
                    COLS = len(self.grid[0]) if ROWS > 0 else 26
                    self.pvp_connecting = False
                    self.pvp_my_slot = pkt.get('your_slot', 1)
                    self.start_pvp_game(COLS, ROWS, lobby_slots=pkt.get('slots'))
                    self._pvp_prev_grid = [row[:] for row in self.grid]

                elif ptype == 'state' and self.state in ('pvp_playing', 'pvp_end'):
                    # Use a sequence number or just accept all (UDP can be out of order, but since we are on LAN it's mostly fine)
                    # To fix flicker, we must interpolate our own tank too!
                    for pd in pkt.get('players', []):
                        slot = pd['slot']
                        if slot == self.pvp_my_slot:
                            self.pvp_player_target_x = pd['x']
                            self.pvp_player_target_y = pd['y']
                            if not hasattr(self, 'pvp_player_interp_init'):
                                self.player.x = pd['x']
                                self.player.y = pd['y']
                                self.pvp_player_interp_init = True
                            self.player.dir = pd['dir']
                            self.player.hp = pd['hp']
                            self.player.alive = pd['alive']
                            self.player.energy = pd.get('energy', self.player.energy)
                        else:
                            t, d = self._pvp_find_slot_tank(slot)
                            if t is None:
                                continue
                            d['target_x'] = pd['x']
                            d['target_y'] = pd['y']
                            if not d.get('interp_init'):
                                t.x = pd['x']; t.y = pd['y']
                                d['interp_init'] = True
                            t.dir = pd['dir']
                            t.hp = pd['hp']
                            t.alive = pd['alive']
                            t.energy = pd.get('energy', t.energy)

                    # Bullets & explosions
                    self.bullets = []
                    for bd in pkt.get('b', []):
                        nb = Bullet(bd['x'], bd['y'], bd['dir'], bd.get('o', 'player'), kind=bd['k'])
                        nb.shooter_slot = bd.get('s', 0)
                        self.bullets.append(nb)
                    self.explosions = []
                    for ed in pkt.get('e', []):
                        self.explosions.append(Explosion(ed['x'], ed['y']))
                    # Grid changes
                    for gc in pkt.get('gc', []):
                        gx, gy, val = gc
                        if 0 <= gy < len(self.grid) and 0 <= gx < len(self.grid[gy]):
                            self.grid[gy][gx] = val
                    self.pvp_timer = pkt.get('t', self.pvp_timer)
                    self.pvp_storm_layer = pkt.get('storm', 0)
                    self.pvp_storm_active = self.pvp_storm_layer > 0
                    mi_data = pkt.get('mi')
                    if mi_data is not None:
                        self.pvp_map_items = [{'gx': m['gx'], 'gy': m['gy'],
                                               'kind': m['k'], 'alive': True} for m in mi_data]
                    mn_data = pkt.get('mn')
                    if mn_data is not None:
                        self.pvp_mines = [{'x': m['x'], 'y': m['y'],
                                           'shooter_slot': m.get('s', 0)} for m in mn_data]
                    frz = pkt.get('frz', {})
                    self.pvp_freeze_timer = frz.get(str(self.pvp_my_slot), 0)
                    for d in self.pvp_other_data:
                        d['freeze_timer'] = frz.get(str(d['slot']), 0)
                    chats = pkt.get('chat', {})
                    for slot_s, msg in chats.items():
                        try: slot_i = int(slot_s)
                        except Exception: continue
                        if slot_i == self.pvp_my_slot:
                            continue
                        d = self._pvp_find_slot_data(slot_i)
                        if d is not None:
                            d['chat_msg'] = msg
                            d['chat_timer'] = 180
                    if pkt.get('rematch'):
                        self.pvp_rematch_received = True
                    # Winner
                    w = pkt.get('w')
                    if w is not None and self.pvp_winner is None:
                        self.pvp_winner = w
                        self.pvp_winner_name = pkt.get('wn', '')
                        self.pvp_end_timer = 300
                        self._pvp_handle_match_end()

            # Smooth interpolation and timer updates for all opponents and local player
            if self.state in ('pvp_playing', 'pvp_end'):
                self.player.update()
                if hasattr(self, 'pvp_player_interp_init') and not self.pvp_is_host:
                    self.player.x += (getattr(self, 'pvp_player_target_x', self.player.x) - self.player.x) * 0.4
                    self.player.y += (getattr(self, 'pvp_player_target_y', self.player.y) - self.player.y) * 0.4
                for t, d in zip(self.pvp_others, self.pvp_other_data):
                    t.update()
                    if d.get('interp_init'):
                        t.x += (d['target_x'] - t.x) * 0.4
                        t.y += (d['target_y'] - t.y) * 0.4

            # Chat timers
            if self.pvp_chat_timer > 0: self.pvp_chat_timer -= 1
            for d in self.pvp_other_data:
                if d.get('chat_timer', 0) > 0: d['chat_timer'] -= 1

            # Timeout
            if self.state == 'pvp_playing' and time.time() - self.pvp_last_recv > 4.0 and not self.pvp_winner:
                self.pvp_winner = "DISCONNECT"
                self.pvp_end_timer = 120
                self._pvp_handle_match_end()

            # End timer
            if self.pvp_winner is not None and self.pvp_end_timer > 0:
                self.pvp_end_timer -= 1

        # Transition to end screen
        if self.pvp_winner is not None and self.state == 'pvp_playing':
            self.state = 'pvp_end'

    def _pvp_apply_item(self, kind, who_slot):
        """Apply a map item effect. who_slot is the slot index of the picker
        (0 = host, 1..3 = clients). For non-host slots, the target is the Tank
        in pvp_others corresponding to that slot."""
        if who_slot == 0:
            target = self.player
        else:
            target, _ = self._pvp_find_slot_tank(who_slot)
            if target is None:
                return
        if kind == 'health':
            target.hp = min(target.hp + 1, target.max_hp)
        elif kind == 'shield':
            target.shield = min(target.shield + 2, 5)
        elif kind == 'speed':
            target.speed = min(target.speed + 0.5, 4.0)
        elif kind == 'rapid':
            target.shoot_delay = max(target.shoot_delay - 5, 5)
        elif kind == 'multi':
            target.bullet_count = min(getattr(target, 'bullet_count', 1) + 1, 5)
        elif kind == 'freeze':
            # Freeze every other player
            if who_slot != 0:
                self.pvp_freeze_timer = 180
            for d in self.pvp_other_data:
                if d['slot'] != who_slot:
                    d['freeze_timer'] = 180
        elif kind == 'mine':
            self.pvp_mines.append({'x': target.x, 'y': target.y, 'shooter_slot': who_slot})
        elif kind == 'teleport':
            # Find an empty tile that's away from all OTHER players
            for _ in range(50):
                tx = random.randint(2, COLS - 3) * TS + TS // 2
                ty = random.randint(2, ROWS - 3) * TS + TS // 2
                gx, gy = int(tx // TS), int(ty // TS)
                if not (0 <= gx < COLS and 0 <= gy < ROWS and self.grid[gy][gx] == EMPTY):
                    continue
                # Distance from every other player
                ok = True
                if who_slot != 0 and math.hypot(tx - self.player.x, ty - self.player.y) <= TS * 5:
                    ok = False
                else:
                    for t, d in zip(self.pvp_others, self.pvp_other_data):
                        if d['slot'] == who_slot: continue
                        if math.hypot(tx - t.x, ty - t.y) <= TS * 5:
                            ok = False; break
                if ok:
                    target.x = tx; target.y = ty
                    break
        snd_pickup.play()

    def _pvp_handle_match_end(self):
        """Handle match end: update rank, money, save.
        pvp_winner is either a slot index (int), 'DRAW', 'DISCONNECT', or None."""
        # Determine if I am the winner
        if isinstance(self.pvp_winner, int):
            is_local_winner = (self.pvp_winner == self.pvp_my_slot)
        else:
            is_local_winner = False

        total_players = 1 + len(self.pvp_others)
        if self.pvp_winner == 'DRAW' or self.pvp_winner == 'DISCONNECT':
            # Refund bet
            if self.pvp_bet_active:
                self.money += self.pvp_bet_amount_match
        elif is_local_winner:
            self.pvp_wins += 1
            # Winner takes the whole pot (every player's bet)
            if self.pvp_bet_active:
                self.money += self.pvp_bet_amount_match * total_players
            # Win bonus (more for more players)
            self.money += 100 + self.pvp_combo_bonus + 50 * (total_players - 2)
            # Rank up
            if self.pvp_wins >= 30:
                self.pvp_rank = 3
            elif self.pvp_wins >= 15:
                self.pvp_rank = 2
            elif self.pvp_wins >= 5:
                self.pvp_rank = 1
        else:
            self.pvp_losses += 1

        self.pvp_bet_active = False
        self._save_game()

    def _pvp_use_backpack_item(self, idx):
        """Use an item from the PVP backpack (brought from offline)."""
        if idx < len(self.pvp_local_items):
            kind = self.pvp_local_items.pop(idx)
            self._pvp_apply_item(kind, self.pvp_my_slot)

    def _pvp_send_chat(self, msg_idx):
        """Send a quick chat message."""
        if 0 <= msg_idx < len(self.pvp_chat_options):
            self.pvp_chat_msg = self.pvp_chat_options[msg_idx]
            self.pvp_chat_timer = 180

    def _pvp_request_rematch(self):
        """Send rematch request."""
        self.pvp_rematch_sent = True
        self.pvp_rematch_timer = 600  # 10 seconds
        if not self.pvp_is_host and self.pvp_host_addr:
            try:
                pkt = json.dumps({'type': 'rematch'}).encode('utf-8')
                self.pvp_socket.sendto(pkt, self.pvp_host_addr)
            except Exception: pass

    # ═══════════════════════════════════
    # PVP DRAWING METHODS
    # ═══════════════════════════════════
    def draw_pvp_menu(self):
        s = self._surf
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((20, 15, 40))
            draw_pastel_starfield(s, self.tick)
        draw_rainbow_text(s, "CHƠI MẠNG (PVP)", (SW // 2, 50), FONT_TITLE, tick=self.tick)
        ip_text = f"IP: {self._get_local_ip()}"
        ip_r = FONT_SM.render(ip_text, True, (150, 150, 180))
        s.blit(ip_r, (SW // 2 - ip_r.get_width() // 2, 100))
        # Rank display
        rank_txt = f"Hạng: {self.pvp_rank_names[self.pvp_rank]} | Thắng: {self.pvp_wins} | Thua: {self.pvp_losses}"
        rank_r = FONT_SM.render(rank_txt, True, (200, 200, 150))
        s.blit(rank_r, (SW // 2 - rank_r.get_width() // 2, 122))
        if getattr(self, 'pvp_bind_error', ''):
            err_r = FONT_SM.render(self.pvp_bind_error, True, (255, 100, 100))
            s.blit(err_r, (SW // 2 - err_r.get_width() // 2, 142))
        for i, opt in enumerate(self.pvp_menu_options):
            sel = (i == self.pvp_menu_sel)
            bw, bh = 400, 60
            bx = SW // 2 - bw // 2
            by = 160 + i * 80
            rect = pygame.Rect(bx, by, bw, bh)
            draw_kawaii_button(s, rect, opt, FONT_BIG, selected=sel, tick=self.tick)
        hint = FONT_SM.render("[UP/DOWN] Chọn  [ENTER] Xác nhận  [ESC] Quay lại", True, (120, 120, 150))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 40))

    def draw_pvp_prep(self):
        """Draw PVP pre-game lobby — polished card-based UI."""
        s = self._surf
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((20, 15, 40))
            draw_pastel_starfield(s, self.tick)
        draw_rainbow_text(s, "CHUẨN BỊ TRẬN ĐẤU", (SW // 2, 28), FONT_TITLE, tick=self.tick)

        # ── Two-column layout ──
        left_x, left_w = 30, 400
        right_x, right_w = 450, SW - 480
        top_y = 70

        # ══ LEFT COLUMN — Settings ══
        draw_kawaii_panel(s, (left_x, top_y, left_w, 540), fill=(35, 28, 60))

        cy = top_y + 12

        # — Name field —
        name_label = FONT_SM.render("TÊN NGƯỜI CHƠI", True, (255, 220, 150))
        s.blit(name_label, (left_x + 15, cy))
        cy += 22
        name_box = pygame.Rect(left_x + 15, cy, left_w - 30, 34)
        editing = getattr(self, 'pvp_name_editing', False)
        box_border = (100, 200, 255) if editing else (80, 70, 110)
        pygame.draw.rect(s, (25, 20, 45), name_box, border_radius=6)
        pygame.draw.rect(s, box_border, name_box, 2, border_radius=6)
        name_txt = self.pvp_prep_name
        if editing and self.tick % 60 < 30:
            name_txt += "|"
        nt = FONT_MED.render(name_txt, True, (255, 255, 255))
        s.blit(nt, (left_x + 22, cy + 7))
        cy += 46

        # — Mode toggle —
        mode_label = FONT_SM.render("CHẾ ĐỘ", True, (255, 220, 150))
        s.blit(mode_label, (left_x + 15, cy))
        cy += 22
        mode_bw = (left_w - 40) // 2
        fun_rect = pygame.Rect(left_x + 15, cy, mode_bw - 4, 36)
        bet_rect = pygame.Rect(left_x + 15 + mode_bw + 4, cy, mode_bw - 4, 36)
        fun_sel = (self.pvp_prep_bet_mode == 0)
        bet_sel = (self.pvp_prep_bet_mode == 1)
        draw_kawaii_button(s, fun_rect, "VUI VẺ", FONT_SM, selected=fun_sel, color_idx=3, tick=self.tick)
        draw_kawaii_button(s, bet_rect, "CÁ CƯỢC", FONT_SM, selected=bet_sel, color_idx=1, tick=self.tick)
        cy += 44

        # — Bet amount (only if bet mode) —
        if self.pvp_prep_bet_mode == 1:
            bet_label = FONT_SM.render(f"SỐ TIỀN CƯỢC: {self.pvp_prep_bet_amount:,}đ", True, (255, 220, 80))
            s.blit(bet_label, (left_x + 15, cy))
            cy += 22
            # +/- buttons
            minus_rect = pygame.Rect(left_x + 15, cy, 60, 30)
            plus_rect = pygame.Rect(left_x + 85, cy, 60, 30)
            draw_kawaii_button(s, minus_rect, "−100", FONT_SM, selected=False, color_idx=0, tick=self.tick)
            draw_kawaii_button(s, plus_rect, "+100", FONT_SM, selected=False, color_idx=3, tick=self.tick)
            money_t = FONT_SM.render(f"Bạn có: {self.money:,}đ", True, (150, 200, 150))
            s.blit(money_t, (left_x + 160, cy + 6))
            cy += 38
        else:
            cy += 8

        # — Map size —
        map_label = FONT_SM.render("KÍCH THƯỚC MAP", True, (255, 220, 150))
        s.blit(map_label, (left_x + 15, cy))
        cy += 22
        map_names = ["Nhỏ 26x20", "Vừa 36x28", "Lớn 46x34"]
        map_bw = (left_w - 50) // 3
        for mi, mname in enumerate(map_names):
            mx_btn = left_x + 15 + mi * (map_bw + 5)
            mr = pygame.Rect(mx_btn, cy, map_bw, 34)
            draw_kawaii_button(s, mr, mname, FONT_SM,
                               selected=(mi == self.pvp_prep_map_size),
                               color_idx=2, tick=self.tick)
        cy += 44

        # — Player info summary —
        info_panel_y = cy
        draw_kawaii_panel(s, (left_x + 10, info_panel_y, left_w - 20, 90),
                          fill=(45, 35, 70), border=(120, 100, 160), radius=10, shadow_offset=2, glow=False)
        # Tank preview
        tier = min(len(sprites.player_tiers) - 1, self.skin_idx)
        td = (self.tick // 20) % 4
        tank_img = pygame.transform.scale(sprites.player_tiers[tier][td], (50, 50))
        s.blit(tank_img, (left_x + 22, info_panel_y + 20))
        # Info text
        info_lines = [
            f"Xe: {self.skin_names[self.skin_idx]}",
            f"Vàng: {self.money:,}đ",
            f"Hạng: {self.pvp_rank_names[self.pvp_rank]}"
        ]
        for il, iline in enumerate(info_lines):
            it = FONT_SM.render(iline, True, (200, 210, 230))
            s.blit(it, (left_x + 82, info_panel_y + 10 + il * 24))

        # ══ RIGHT COLUMN — Items & Pet ══
        draw_kawaii_panel(s, (right_x, top_y, right_w, 540), fill=(35, 28, 60))

        ry = top_y + 12

        # — Item selection (always visible) —
        item_label = FONT_SM.render(f"VẬT PHẨM MANG THEO ({len(self.pvp_prep_items)}/3)", True, (255, 220, 150))
        s.blit(item_label, (right_x + 15, ry))
        ry += 24
        bp_items = list(self.backpack)
        item_names = {
            "multi": "Đa Hướng", "rapid": "Siêu Tốc", "pierce": "Xuyên Phá",
            "shield": "Giáp", "health": "Hồi Máu", "speed": "NL", "star": "Bom NT",
            "life": "Mạng", "rocket": "Tên Lửa", "flame": "Phun Lửa",
            "freeze": "Đ.Băng", "grenade": "Lựu Đạn", "plasma": "Plasma",
            "laser": "Laser", "max_power": "Max Sức",
        }
        if not bp_items:
            empty_t = FONT_SM.render("(Ba lô trống — mua ở SHOP)", True, (120, 110, 140))
            s.blit(empty_t, (right_x + 15, ry + 10))
        cols_item = min(4, max(1, len(bp_items)))
        iw, ih = 70, 58
        for idx, item_kind in enumerate(bp_items[:12]):
            col = idx % cols_item
            row = idx // cols_item
            ix = right_x + 15 + col * (iw + 8)
            iy = ry + row * (ih + 6)
            is_chosen = item_kind in self.pvp_prep_items
            # Card bg
            bg_c = (40, 100, 50, 200) if is_chosen else (35, 30, 55, 200)
            card_s = pygame.Surface((iw, ih), pygame.SRCALPHA)
            pygame.draw.rect(card_s, bg_c, (0, 0, iw, ih), border_radius=8)
            s.blit(card_s, (ix, iy))
            border_c = (80, 255, 80) if is_chosen else (70, 60, 90)
            pygame.draw.rect(s, border_c, (ix, iy, iw, ih), 2, border_radius=8)
            if is_chosen:
                check = FONT_SM.render("✓", True, (80, 255, 80))
                s.blit(check, (ix + iw - 16, iy + 2))
            if item_kind in sprites.items:
                icon = pygame.transform.scale(sprites.items[item_kind], (30, 30))
                s.blit(icon, (ix + 4, iy + 4))
            name_t = FONT_SM.render(item_names.get(item_kind, item_kind[:6]), True, (200, 200, 220))
            s.blit(name_t, (ix + iw // 2 - name_t.get_width() // 2, iy + ih - 18))
        ry += max(1, (len(bp_items[:12]) + cols_item - 1) // max(1, cols_item)) * (ih + 6) + 12

        # — Pet selection (always visible) —
        pet_label = FONT_SM.render("PET ĐỒNG HÀNH", True, (255, 220, 150))
        s.blit(pet_label, (right_x + 15, ry))
        ry += 24
        pets_list = ["(không)"] + self.owned_pets
        pet_display = {"(không)": "Không", "wolf": "Sói", "dragon": "Rồng",
                       "healer": "Tiên", "shield_bot": "Robot", "magnet": "NC", "ghost": "Ma"}
        pw_btn, ph_btn = 90, 36
        for pi, pet_id in enumerate(pets_list):
            col = pi % 3
            row = pi // 3
            px_btn = right_x + 15 + col * (pw_btn + 8)
            py_btn = ry + row * (ph_btn + 6)
            is_pet_sel = (self.pvp_prep_pet == pet_id) or (pet_id == "(không)" and not self.pvp_prep_pet)
            pet_name = pet_display.get(pet_id, pet_id[:6])
            draw_kawaii_button(s, pygame.Rect(px_btn, py_btn, pw_btn, ph_btn),
                               pet_name, FONT_SM, selected=is_pet_sel,
                               color_idx=4, tick=self.tick)

        # ══ BOTTOM BUTTONS ══
        back_rect = pygame.Rect(30, SH - 60, 160, 44)
        draw_kawaii_button(s, back_rect, "QUAY LẠI", FONT_MED, selected=False, color_idx=0, tick=self.tick)
        create_rect = pygame.Rect(SW // 2 - 100, SH - 60, 400, 44)
        draw_kawaii_button(s, create_rect, "TẠO PHÒNG", FONT_BIG, selected=True, color_idx=3, tick=self.tick)

    def _draw_pvp_lobby_slots(self, surf, slots, top_y=170):
        """Draw the 4-slot lobby grid (2x2). Returns the list of slot rects."""
        self.pvp_lobby_buttons = {}
        slot_w, slot_h = 360, 170
        gap_x, gap_y = 28, 22
        total_w = slot_w * 2 + gap_x
        total_h = slot_h * 2 + gap_y
        start_x = SW // 2 - total_w // 2
        start_y = top_y
        rects = []
        for i in range(self.pvp_max_slots):
            row = i // 2
            col = i % 2
            rx = start_x + col * (slot_w + gap_x)
            ry = start_y + row * (slot_h + gap_y)
            rect = pygame.Rect(rx, ry, slot_w, slot_h)
            rects.append(rect)

            entry = slots[i] if i < len(slots) else None
            # Card background
            card_color = (45, 55, 95, 230) if entry else (30, 30, 50, 180)
            border_color = (255, 220, 100) if (entry and entry.get('is_host')) else \
                           ((130, 200, 255) if entry else (90, 90, 130))
            card = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            pygame.draw.rect(card, card_color, (0, 0, slot_w, slot_h), border_radius=18)
            # Animated glow border when filled
            border_w = 3
            if entry:
                pulse = abs(math.sin(self.tick * 0.05))
                glow_a = int(120 + pulse * 120)
                glow = pygame.Surface((slot_w + 8, slot_h + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*border_color, glow_a),
                                 (0, 0, slot_w + 8, slot_h + 8),
                                 border_radius=22)
                surf.blit(glow, (rx - 4, ry - 4))
                border_w = 4
            pygame.draw.rect(card, border_color, (0, 0, slot_w, slot_h),
                             border_w, border_radius=18)
            surf.blit(card, (rx, ry))

            # Slot label (P1..P4)
            slot_label = FONT_SM.render(f"SLOT {i+1}", True, (200, 200, 230))
            surf.blit(slot_label, (rx + 16, ry + 10))

            if entry:
                # Host badge or P2/P3/P4
                if entry.get('is_host'):
                    badge_t = FONT_SM.render("CHỦ PHÒNG", True, (255, 220, 100))
                    bw_ = badge_t.get_width() + 16
                    pygame.draw.rect(surf, (90, 70, 30),
                                     (rx + slot_w - bw_ - 12, ry + 8, bw_, 22),
                                     border_radius=10)
                    pygame.draw.rect(surf, (255, 220, 100),
                                     (rx + slot_w - bw_ - 12, ry + 8, bw_, 22),
                                     2, border_radius=10)
                    surf.blit(badge_t, (rx + slot_w - bw_ - 4, ry + 12))
                else:
                    badge_t = FONT_SM.render("SẴN SÀNG", True, (130, 200, 255))
                    bw_ = badge_t.get_width() + 16
                    pygame.draw.rect(surf, (30, 60, 90),
                                     (rx + slot_w - bw_ - 12, ry + 8, bw_, 22),
                                     border_radius=10)
                    pygame.draw.rect(surf, (130, 200, 255),
                                     (rx + slot_w - bw_ - 12, ry + 8, bw_, 22),
                                     2, border_radius=10)
                    surf.blit(badge_t, (rx + slot_w - bw_ - 4, ry + 12))

                # Tank icon
                try:
                    skin_idx = entry.get('skin', 0)
                    tier = min(len(sprites.player_tiers) - 1, skin_idx)
                    tank_img = sprites.player_tiers[tier][0]
                    if tank_img:
                        scaled = pygame.transform.scale(tank_img, (72, 72))
                        bob = int(math.sin(self.tick * 0.08 + i) * 4)
                        surf.blit(scaled, (rx + 24, ry + 50 + bob))
                        
                        # Draw arrows for local player
                        if (self.pvp_is_host and i == 0) or (not self.pvp_is_host and getattr(self, 'pvp_my_slot', -1) == entry.get('slot', -1)):
                            # Left arrow
                            draw_left = pygame.Rect(rx - 8, ry + 50 + 20, 26, 36)
                            pygame.draw.polygon(surf, (255, 200, 100), [(draw_left.right, draw_left.top), (draw_left.left, draw_left.centery), (draw_left.right, draw_left.bottom)])
                            # Right arrow
                            draw_right = pygame.Rect(rx + 102, ry + 50 + 20, 26, 36)
                            pygame.draw.polygon(surf, (255, 200, 100), [(draw_right.left, draw_right.top), (draw_right.right, draw_right.centery), (draw_right.left, draw_right.bottom)])
                            
                            # MASSIVE hitboxes for mouse click to ensure it cannot be missed
                            self.pvp_lobby_buttons['skin_left'] = pygame.Rect(rx - 40, ry + 20, 80, 100)
                            self.pvp_lobby_buttons['skin_right'] = pygame.Rect(rx + 80, ry + 20, 80, 100)
                            
                        # Visual click feedback
                        if getattr(self, 'pvp_skin_flash', 0) > 0 and ((self.pvp_is_host and i == 0) or (not self.pvp_is_host and getattr(self, 'pvp_my_slot', -1) == entry.get('slot', -1))):
                            flash_surf = pygame.Surface((72, 72), pygame.SRCALPHA)
                            flash_surf.fill((255, 255, 255, int(self.pvp_skin_flash * 255)))
                            surf.blit(flash_surf, (rx + 24, ry + 50 + bob))
                            self.pvp_skin_flash = max(0, self.pvp_skin_flash - 0.1)
                except Exception:
                    pygame.draw.rect(surf, (180, 180, 200),
                                     (rx + 24, ry + 50, 64, 64), border_radius=8)

                # Name
                name_str = entry.get('name', f"P{i+1}")[:14]
                name_r = FONT_BIG.render(name_str, True, (255, 255, 255))
                surf.blit(name_r, (rx + 130, ry + 60))

                # Edit button (Pen icon)
                if (self.pvp_is_host and i == 0) or (not self.pvp_is_host and getattr(self, 'pvp_my_slot', -1) == entry.get('slot', -1)):
                    pen_rect = pygame.Rect(rx + 130 + name_r.get_width() + 10, ry + 60, 30, 30)
                    pygame.draw.rect(surf, (100, 150, 255), pen_rect, border_radius=6)
                    pygame.draw.line(surf, (255, 255, 255), (pen_rect.right-8, pen_rect.top+8), (pen_rect.left+8, pen_rect.bottom-8), 3)
                    pygame.draw.line(surf, (255, 255, 255), (pen_rect.left+8, pen_rect.bottom-8), (pen_rect.left+12, pen_rect.bottom-6), 2)
                    self.pvp_lobby_buttons['edit_name'] = pygame.Rect(pen_rect.x - 5, pen_rect.y - 5, 40, 40)

                # Pet info
                pet_t = entry.get('pet') or ''
                pet_label = f"Pet: {pet_t}" if pet_t else "Pet: (không)"
                pet_r = FONT_SM.render(pet_label, True, (200, 200, 220))
                surf.blit(pet_r, (rx + 110, ry + 100))

                # Ready dot
                pygame.draw.circle(surf, (80, 230, 120), (rx + 26, ry + 145), 8)
                ready_r = FONT_SM.render("Đã vào phòng", True, (160, 230, 180))
                surf.blit(ready_r, (rx + 42, ry + 138))
            else:
                # Empty slot
                empty_label = FONT_BIG.render("ĐANG TRỐNG", True, (130, 130, 150))
                surf.blit(empty_label,
                          (rx + slot_w // 2 - empty_label.get_width() // 2,
                           ry + slot_h // 2 - 18))
                dots = "." * ((self.tick // 25) % 4)
                wait_label = FONT_SM.render(f"Chờ người chơi{dots}", True, (110, 110, 140))
                surf.blit(wait_label,
                          (rx + slot_w // 2 - wait_label.get_width() // 2,
                           ry + slot_h // 2 + 18))
        return rects

    def _draw_pvp_room_header(self, surf, title):
        s = surf
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((18, 14, 36))
            draw_pastel_starfield(s, self.tick)
        draw_rainbow_text(s, title, (SW // 2, 40), FONT_TITLE, tick=self.tick)
        # Room info row
        mode = self.pvp_room_info.get('mode', 'fun') if self.pvp_room_info else \
               ('bet' if self.pvp_prep_bet_mode == 1 else 'fun')
        mode_str = "Cá cược" if mode == 'bet' else "Vui vẻ"
        bet = self.pvp_room_info.get('bet', 0) if self.pvp_room_info else self.pvp_prep_bet_amount
        map_name = self.pvp_room_info.get('map_name',
                       self.pvp_map_size_names[self.pvp_prep_map_size]) \
                       if self.pvp_room_info else self.pvp_map_size_names[self.pvp_prep_map_size]
        host_name = self.pvp_room_info.get('name',
                       self.pvp_prep_name) if self.pvp_room_info else self.pvp_prep_name
        info_parts = [f"Phòng: {host_name}", f"Map: {map_name}", f"Chế độ: {mode_str}"]
        if mode == 'bet':
            info_parts.append(f"Cược: {bet:,}đ/người")
        info_str = "   |   ".join(info_parts)
        info_r = FONT_MED.render(info_str, True, (230, 230, 250))
        # Subtle panel behind info
        pad = 10
        bg = pygame.Surface((info_r.get_width() + pad * 2, info_r.get_height() + pad), pygame.SRCALPHA)
        pygame.draw.rect(bg, (45, 55, 90, 200), (0, 0, bg.get_width(), bg.get_height()), border_radius=10)
        pygame.draw.rect(bg, (120, 150, 200), (0, 0, bg.get_width(), bg.get_height()), 2, border_radius=10)
        s.blit(bg, (SW // 2 - bg.get_width() // 2, 90))
        s.blit(info_r, (SW // 2 - info_r.get_width() // 2, 90 + pad // 2))

    def _draw_pvp_lobby_footer(self, surf, players, can_start, is_host_view):
        s = surf
        # Players count
        count_txt = f"{players}/{self.pvp_max_slots} người chơi"
        ct_color = (130, 230, 130) if players >= self.pvp_min_start else (240, 200, 130)
        ct_r = FONT_MED.render(count_txt, True, ct_color)
        s.blit(ct_r, (SW // 2 - ct_r.get_width() // 2, SH - 130))

        hint = (f"Cần ít nhất {self.pvp_min_start} người chơi để bắt đầu"
                if players < self.pvp_min_start else
                "Đã đủ người - sẵn sàng chiến đấu!")
        hint_r = FONT_SM.render(hint, True, (200, 200, 230))
        s.blit(hint_r, (SW // 2 - hint_r.get_width() // 2, SH - 105))

        hint_skin_name = FONT_SM.render("[Trái/Phải]: Đổi Xe   |   [Gõ phím]: Đổi Tên", True, (255, 200, 150))
        s.blit(hint_skin_name, (SW // 2 - hint_skin_name.get_width() // 2, SH - 148))

        if is_host_view:
            # Two buttons: BACK and START
            back_rect = pygame.Rect(SW // 2 - 330, SH - 75, 260, 56)
            draw_kawaii_button(s, back_rect, "HỦY PHÒNG", FONT_BIG,
                               selected=False, color_idx=0, tick=self.tick)
            start_rect = pygame.Rect(SW // 2 + 70, SH - 75, 260, 56)
            if can_start:
                draw_kawaii_button(s, start_rect, "BẮT ĐẦU!", FONT_BIG,
                                   selected=True, color_idx=3, tick=self.tick)
            else:
                # Greyed out
                gs = pygame.Surface((start_rect.width, start_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(gs, (60, 60, 75, 220),
                                 (0, 0, start_rect.width, start_rect.height),
                                 border_radius=14)
                pygame.draw.rect(gs, (100, 100, 120),
                                 (0, 0, start_rect.width, start_rect.height),
                                 2, border_radius=14)
                lbl = FONT_BIG.render("BẮT ĐẦU!", True, (140, 140, 150))
                gs.blit(lbl, (start_rect.width // 2 - lbl.get_width() // 2,
                              start_rect.height // 2 - lbl.get_height() // 2))
                s.blit(gs, (start_rect.x, start_rect.y))
            ip_txt = FONT_SM.render(f"IP của bạn: {self._get_local_ip()}   |   ESC: Hủy phòng",
                                    True, (160, 160, 200))
            s.blit(ip_txt, (SW // 2 - ip_txt.get_width() // 2, SH - 22))
        else:
            # Client: only BACK + waiting indicator
            back_rect = pygame.Rect(SW // 2 - 130, SH - 70, 260, 50)
            draw_kawaii_button(s, back_rect, "RỜI PHÒNG", FONT_BIG,
                               selected=False, color_idx=0, tick=self.tick)
            wait_dots = "." * ((self.tick // 25) % 4)
            wait_r = FONT_SM.render(f"Đang chờ chủ phòng bắt đầu{wait_dots}",
                                     True, (200, 220, 255))
            s.blit(wait_r, (SW // 2 - wait_r.get_width() // 2, SH - 18))

    def draw_pvp_waiting(self):
        """Host's lobby view: 4 slots, room info, START button when 2+ players."""
        s = self._surf
        self._draw_pvp_room_header(s, "PHÒNG CỦA BẠN")
        slots = self.pvp_lobby_view if self.pvp_lobby_view else self._pvp_lobby_snapshot()
        # Ensure length
        while len(slots) < self.pvp_max_slots:
            slots.append(None)
        self._draw_pvp_lobby_slots(s, slots, top_y=170)
        players = sum(1 for sl in slots if sl is not None)
        can_start = players >= self.pvp_min_start
        self._draw_pvp_lobby_footer(s, players, can_start, is_host_view=True)

    def draw_pvp_lobby(self):
        """Client's lobby view: 4 slots, waiting for host to start."""
        s = self._surf
        self._draw_pvp_room_header(s, "ĐANG TRONG PHÒNG")
        slots = self.pvp_lobby_view if self.pvp_lobby_view else \
                [None] * self.pvp_max_slots
        while len(slots) < self.pvp_max_slots:
            slots.append(None)
        self._draw_pvp_lobby_slots(s, slots, top_y=170)
        players = sum(1 for sl in slots if sl is not None)
        self._draw_pvp_lobby_footer(s, players, can_start=False, is_host_view=False)

    def draw_pvp_joining(self):
        s = self._surf
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((20, 15, 40))
            draw_pastel_starfield(s, self.tick)
        draw_rainbow_text(s, "TÌM PHÒNG TRÊN MẠNG LAN", (SW // 2, 50), FONT_TITLE, tick=self.tick)
        dots = "." * ((self.tick // 20) % 4)
        if getattr(self, 'pvp_connecting', False):
            conn_txt = FONT_BIG.render(f"Đang kết nối{dots}", True, (255, 255, 100))
            s.blit(conn_txt, (SW // 2 - conn_txt.get_width() // 2, SH // 2 - 20))
        elif not self.pvp_found_hosts:
            search_txt = FONT_MED.render(f"Đang tìm phòng{dots}", True, (150, 200, 255))
            s.blit(search_txt, (SW // 2 - search_txt.get_width() // 2, SH // 2 - 20))
        else:
            found_txt = FONT_MED.render(f"Tìm thấy {len(self.pvp_found_hosts)} phòng:", True, (150, 255, 150))
            s.blit(found_txt, (SW // 2 - found_txt.get_width() // 2, 110))
            for i, host_entry in enumerate(self.pvp_found_hosts):
                host_ip = host_entry[0]
                room_info = host_entry[2] if len(host_entry) > 2 else {}
                sel = (i == self.pvp_join_sel)
                bw, bh = 500, 55
                bx = SW // 2 - bw // 2
                by = 150 + i * 65
                rect = pygame.Rect(bx, by, bw, bh)
                host_name = room_info.get('name', host_ip)
                mode = room_info.get('mode', 'fun')
                bet = room_info.get('bet', 0)
                map_name = room_info.get('map_name', '?')
                num_players = room_info.get('players', '?')
                max_sl = room_info.get('max_slots', 4)
                mode_str = f"Cược {bet:,}đ" if mode == 'bet' else "Vui vẻ"
                label = f"{host_name} | {mode_str} | {map_name} | {num_players}/{max_sl}"
                draw_kawaii_button(s, rect, label, FONT_MED, selected=sel, tick=self.tick)
            enter_txt = FONT_SM.render("[ENTER] Vào phòng  [UP/DOWN] Chọn  [TAB] Nhập IP", True, (200, 200, 230))
            s.blit(enter_txt, (SW // 2 - enter_txt.get_width() // 2, SH - 90))

        # Manual IP input area
        if self.pvp_manual_ip_editing:
            ip_label = FONT_SM.render("Nhập IP host:", True, (255, 220, 100))
            s.blit(ip_label, (SW // 2 - 200, SH - 72))
            ip_box = pygame.Rect(SW // 2 - 60, SH - 75, 200, 24)
            pygame.draw.rect(s, (50, 40, 80), ip_box, border_radius=6)
            pygame.draw.rect(s, (255, 220, 100), ip_box, 2, border_radius=6)
            ip_txt = FONT_SM.render(self.pvp_manual_ip + "_", True, (255, 255, 255))
            s.blit(ip_txt, (ip_box.x + 6, ip_box.y + 4))
        else:
            ip_hint = FONT_SM.render("[TAB] Nhập IP thủ công (nếu không tìm thấy phòng)", True, (130, 130, 160))
            s.blit(ip_hint, (SW // 2 - ip_hint.get_width() // 2, SH - 72))

        back_rect = pygame.Rect(SW // 2 - 80, SH - 50, 160, 40)
        draw_kawaii_button(s, back_rect, "QUAY LẠI", FONT_MED, selected=False, tick=self.tick)

    def draw_pvp_playing(self):
        s = self._surf
        s.fill((10, 10, 15))
        cam_off = (self.cam_x, self.cam_y)
        zoom = self.cam_zoom
        s_ts = int(TS * zoom)

        start_gx = max(0, int(self.cam_x // TS))
        end_gx = min(COLS, int((self.cam_x + SW / zoom) // TS) + 2)
        start_gy = max(0, int(self.cam_y // TS))
        end_gy = min(ROWS, int((self.cam_y + SH / zoom) // TS) + 2)

        # Map tiles
        for y in range(start_gy, end_gy):
            for x in range(start_gx, end_gx):
                tile = self.grid[y][x]
                dx = int((x * TS - self.cam_x) * zoom)
                dy = int((y * TS - self.cam_y) * zoom)
                floor_img = sprites.floor
                if zoom != 1.0: floor_img = pygame.transform.scale(floor_img, (s_ts + 1, s_ts + 1))
                s.blit(floor_img, (dx, dy))
                if tile != EMPTY and tile != GRASS:
                    img = None
                    if tile == BRICK: img = sprites.brick
                    elif tile == STEEL: img = sprites.steel
                    elif tile == WATER: img = sprites.water_frames[self.water_frame % len(sprites.water_frames)]
                    if img:
                        if zoom != 1.0: img = pygame.transform.scale(img, (s_ts + 1, s_ts + 1))
                        s.blit(img, (dx, dy))

        # Map items (blinking)
        for mi in self.pvp_map_items:
            if mi['alive'] and (self.tick % 40 < 30):
                ix = int((mi['gx'] * TS - self.cam_x) * zoom)
                iy = int((mi['gy'] * TS - self.cam_y) * zoom)
                kind = mi['kind']
                if kind in sprites.items:
                    item_img = sprites.items[kind]
                    item_img = pygame.transform.scale(item_img, (s_ts, s_ts))
                    s.blit(item_img, (ix, iy))
                else:
                    pygame.draw.circle(s, (200, 200, 100), (ix + s_ts // 2, iy + s_ts // 2), s_ts // 3)

        # Mines (subtle indicator - friendly if own slot)
        for mine in self.pvp_mines:
            mx = int((mine['x'] - self.cam_x) * zoom)
            my = int((mine['y'] - self.cam_y) * zoom)
            own = (mine.get('shooter_slot', 0) == self.pvp_my_slot)
            mine_c = (200, 50, 50, 100) if own else (50, 50, 200, 100)
            ms = pygame.Surface((int(TS * 0.4 * zoom), int(TS * 0.4 * zoom)), pygame.SRCALPHA)
            pygame.draw.circle(ms, mine_c, (ms.get_width() // 2, ms.get_height() // 2), ms.get_width() // 2)
            s.blit(ms, (mx - ms.get_width() // 2, my - ms.get_height() // 2))

        # Draw all tanks (local + opponents) with name/HP/chat above
        # Slot color palette
        slot_colors = [(100, 255, 100), (255, 100, 100), (100, 180, 255), (255, 200, 80)]
        # Local player first
        tank_entries = [(self.player, self.pvp_my_slot,
                         self.player.name or self.pvp_prep_name,
                         self.pvp_chat_msg, self.pvp_chat_timer,
                         self.pvp_freeze_timer, True)]
        for t, d in zip(self.pvp_others, self.pvp_other_data):
            tank_entries.append((t, d['slot'], d.get('name', f"P{d['slot']+1}"),
                                 d.get('chat_msg', ''), d.get('chat_timer', 0),
                                 d.get('freeze_timer', 0), False))
        for tank, slot, name, chat_msg, chat_timer, freeze_t, is_local in tank_entries:
            if not tank or not tank.alive:
                continue
            tank.draw(s, self.tick, cam_off, zoom)
            tx = int((tank.x - cam_off[0]) * zoom)
            ty = int((tank.y - cam_off[1]) * zoom) - int(22 * zoom)
            name_c = slot_colors[slot % len(slot_colors)]
            # Tag prefix
            tag = "Bạn" if is_local else f"P{slot+1}"
            display = f"[{tag}] {name}" if name else f"[{tag}]"
            nt = FONT_SM.render(display, True, name_c)
            s.blit(nt, (tx - nt.get_width() // 2, ty - 14))
            # HP hearts
            for hi in range(tank.max_hp):
                hx = tx - (tank.max_hp * 8) + hi * 16
                hy = ty
                draw_heart_icon(s, hx + 5, hy + 5, 5, filled=(hi < tank.hp))
            # Freeze indicator
            if freeze_t > 0:
                frz_s = pygame.Surface((int(TS * zoom), int(TS * zoom)), pygame.SRCALPHA)
                frz_s.fill((100, 200, 255, 80))
                s.blit(frz_s, (tx - int(TS * zoom) // 2, ty + 5))
                ft = FONT_SM.render("ĐÓNG BĂNG!", True, (100, 200, 255))
                s.blit(ft, (tx - ft.get_width() // 2, ty + 20))
            # Chat bubble
            if chat_timer > 0 and chat_msg:
                bubble_t = FONT_MED.render(chat_msg, True, (255, 255, 255))
                bw = bubble_t.get_width() + 16
                bh = bubble_t.get_height() + 8
                bubble_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
                pygame.draw.rect(bubble_s, (50, 50, 80, 200), (0, 0, bw, bh), border_radius=8)
                pygame.draw.rect(bubble_s, (150, 150, 200), (0, 0, bw, bh), 2, border_radius=8)
                bubble_s.blit(bubble_t, (8, 4))
                s.blit(bubble_s, (tx - bw // 2, ty - 38))

        # Pet
        if self.pvp_local_pet and self.pvp_local_pet.alive:
            self.pvp_local_pet.draw(s, cam_off, zoom)

        # Bullets & explosions
        for b in self.bullets:
            b.draw(s, cam_off, zoom)
        for e in self.explosions:
            e.draw(s, cam_off, zoom)
        update_draw_particles(s, cam_off, zoom)

        # Timer display (top center)
        remaining = max(0, (self.pvp_timer_max - self.pvp_timer)) // 60
        mins = remaining // 60
        secs = remaining % 60
        timer_color = (255, 80, 80) if remaining < 30 else (255, 255, 200)
        timer_txt = FONT_BIG.render(f"{mins}:{secs:02d}", True, timer_color)
        s.blit(timer_txt, (SW // 2 - timer_txt.get_width() // 2, 8))

        # Storm warning
        if self.pvp_storm_warned and not self.pvp_storm_active:
            if self.tick % 60 < 40:
                warn = FONT_MED.render("⚠ BÃO LỬA ĐANG ĐẾN GẦN! ⚠", True, (255, 100, 50))
                s.blit(warn, (SW // 2 - warn.get_width() // 2, 45))
        elif self.pvp_storm_active:
            storm_t = FONT_SM.render(f"BÃO LỬA (Lớp {self.pvp_storm_layer})", True, (255, 80, 50))
            s.blit(storm_t, (SW // 2 - storm_t.get_width() // 2, 45))

        # Backpack items (bottom left)
        bp_y = SH - 55
        bp_label = FONT_SM.render("VẬT PHẨM:", True, (180, 180, 200))
        s.blit(bp_label, (10, bp_y))
        for i in range(3):
            sx = 10 + bp_label.get_width() + 5 + i * 50
            sy = bp_y - 5
            pygame.draw.rect(s, (30, 30, 50), (sx, sy, 44, 44), border_radius=6)
            pygame.draw.rect(s, (80, 80, 120), (sx, sy, 44, 44), 2, border_radius=6)
            if i < len(self.pvp_local_items):
                kind = self.pvp_local_items[i]
                if kind in sprites.items:
                    icon = pygame.transform.scale(sprites.items[kind], (36, 36))
                    s.blit(icon, (sx + 4, sy + 4))
                num_t = FONT_SM.render(str(i + 1), True, (200, 200, 200))
                s.blit(num_t, (sx + 2, sy + 1))

        # Quick chat buttons (bottom right)
        chat_y = SH - 30
        chat_hint = FONT_SM.render("Chat: 5=GG 6=LOL 7=Giỏi 8=Thua", True, (120, 120, 150))
        s.blit(chat_hint, (SW - chat_hint.get_width() - 10, chat_y))

        # PVP HUD (top area): show every player's name + HP, colored by slot
        hud_entries = [(self.pvp_my_slot, self.player.name or self.pvp_prep_name,
                        self.player.hp, self.player.alive)]
        for t, d in zip(self.pvp_others, self.pvp_other_data):
            hud_entries.append((d['slot'], d.get('name', f"P{d['slot']+1}"),
                                t.hp, t.alive))
        hud_entries.sort(key=lambda x: x[0])
        hud_y = 8
        hud_x = 10
        for slot, name, hp, alive in hud_entries:
            col = slot_colors[slot % len(slot_colors)] if alive else (120, 120, 120)
            txt = f"[P{slot+1}] {name[:10]} HP:{hp if alive else 0}"
            r = FONT_SM.render(txt, True, col)
            s.blit(r, (hud_x, hud_y))
            hud_x += r.get_width() + 18
            if hud_x > SW - 120:
                hud_x = 10
                hud_y += r.get_height() + 4

        # Minimap (bottom right)
        self._draw_pvp_minimap(s)

        # Draw custom neon gaming crosshair/reticle at mouse position
        _mx_phys, _my_phys = pygame.mouse.get_pos()
        mx_logical = int(_mx_phys * (SW / phys_w))
        my_logical = int(_my_phys * (SH / phys_h))
        
        cross_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        r_outer = 18
        
        # 1. Black shadow background outline (for high contrast on light areas)
        pygame.draw.circle(cross_surf, (0, 0, 0, 220), (32, 32), r_outer, 4)
        pygame.draw.line(cross_surf, (0, 0, 0, 220), (32, 32 - r_outer - 1), (32, 32 - r_outer + 5), 4)
        pygame.draw.line(cross_surf, (0, 0, 0, 220), (32, 32 + r_outer + 1), (32, 32 + r_outer - 5), 4)
        pygame.draw.line(cross_surf, (0, 0, 0, 220), (32 - r_outer - 1, 32), (32 - r_outer + 5, 32), 4)
        pygame.draw.line(cross_surf, (0, 0, 0, 220), (32 + r_outer + 1, 32), (32 + r_outer - 5, 32), 4)
        pygame.draw.circle(cross_surf, (0, 0, 0, 220), (32, 32), 5)
        
        # 2. Glowing Neon foreground layer
        pygame.draw.circle(cross_surf, (0, 255, 255, 255), (32, 32), r_outer, 2)
        pygame.draw.line(cross_surf, (0, 255, 255, 255), (32, 32 - r_outer), (32, 32 - r_outer + 4), 2)
        pygame.draw.line(cross_surf, (0, 255, 255, 255), (32, 32 + r_outer), (32, 32 + r_outer - 4), 2)
        pygame.draw.line(cross_surf, (0, 255, 255, 255), (32 - r_outer, 32), (32 - r_outer + 4, 32), 2)
        pygame.draw.line(cross_surf, (0, 255, 255, 255), (32 + r_outer, 32), (32 + r_outer - 4, 32), 2)
        
        # 3. High visibility red center dot
        pygame.draw.circle(cross_surf, (255, 30, 30, 255), (32, 32), 3)
        pygame.draw.circle(cross_surf, (255, 255, 255, 255), (32, 32), 1)
        
        s.blit(cross_surf, (mx_logical - 32, my_logical - 32))

    def _draw_pvp_minimap(self, surf):
        """Draw PVP minimap showing full map, both tanks, walls."""
        mm_scale = max(2, min(4, 160 // max(COLS, ROWS)))
        mm_w = COLS * mm_scale
        mm_h = ROWS * mm_scale
        mm_x = SW - mm_w - 8
        mm_y = SH - mm_h - 60

        mm = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm.fill((20, 25, 30, 180))

        for y in range(ROWS):
            for x in range(COLS):
                tile = self.grid[y][x]
                if tile == STEEL:
                    pygame.draw.rect(mm, (140, 145, 160), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))
                elif tile == BRICK:
                    pygame.draw.rect(mm, (160, 80, 50), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))
                elif tile == WATER:
                    pygame.draw.rect(mm, (40, 80, 180), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))

        # Player dots
        slot_colors = [(50, 255, 100), (255, 60, 60), (90, 170, 255), (255, 200, 80)]
        if self.player and self.player.alive:
            pgx = int(self.player.x / TS * mm_scale)
            pgy = int(self.player.y / TS * mm_scale)
            c = slot_colors[self.pvp_my_slot % len(slot_colors)]
            pygame.draw.rect(mm, c, (pgx - 2, pgy - 2, 5, 5))
        for t, d in zip(self.pvp_others, self.pvp_other_data):
            if not t.alive: continue
            pgx = int(t.x / TS * mm_scale)
            pgy = int(t.y / TS * mm_scale)
            c = slot_colors[d['slot'] % len(slot_colors)]
            pygame.draw.rect(mm, c, (pgx - 2, pgy - 2, 5, 5))

        # Border
        pygame.draw.rect(mm, (100, 150, 220), (0, 0, mm_w, mm_h), 2)
        label = FONT_SM.render("MAP", True, (180, 200, 230))
        surf.blit(mm, (mm_x, mm_y))
        surf.blit(label, (mm_x + mm_w // 2 - label.get_width() // 2, mm_y - label.get_height() - 2))

    def draw_pvp_end(self):
        """Draw PVP match end screen with stats, rematch, etc."""
        s = self._surf
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((15, 10, 30))
            draw_pastel_starfield(s, self.tick)

        # Winner text
        if self.pvp_winner == "DRAW":
            win_text = "HÒA!"
        elif self.pvp_winner == "DISCONNECT":
            win_text = "MẤT KẾT NỐI"
        elif isinstance(self.pvp_winner, int):
            if self.pvp_winner == self.pvp_my_slot:
                win_text = "BẠN THẮNG!"
            else:
                wname = self.pvp_winner_name or f"P{self.pvp_winner+1}"
                win_text = f"{wname} THẮNG!"
        else:
            win_text = "KẾT THÚC"

        draw_rainbow_text(s, win_text, (SW // 2, 60), FONT_HUGE, tick=self.tick)

        # Confetti/firework effect for winner
        if "THẮNG" in win_text and self.pvp_winner == self.pvp_my_slot:
            for i in range(8):
                fx = SW // 2 + int(math.sin(self.tick * 0.05 + i * 0.8) * (100 + i * 20))
                fy = 30 + int(abs(math.sin(self.tick * 0.03 + i)) * 40)
                col = KAWAII_RAINBOW[i % len(KAWAII_RAINBOW)]
                pygame.draw.circle(s, col, (fx, fy), 4 + (self.tick + i * 7) % 4)

        # Stats panel
        panel_x, panel_y = 60, 120
        panel_w = SW - 120
        panel_h = 280
        draw_kawaii_panel(s, (panel_x, panel_y, panel_w, panel_h), fill=(30, 25, 55))

        stats_title = FONT_MED.render("THỐNG KÊ TRẬN ĐẤU", True, (255, 230, 150))
        s.blit(stats_title, (SW // 2 - stats_title.get_width() // 2, panel_y + 10))

        # Collect every player's stats
        all_players = [(self.pvp_my_slot,
                        self.pvp_prep_name or "Bạn",
                        self.pvp_match_stats,
                        True,
                        self.player.alive)]
        for t, d in zip(self.pvp_others, self.pvp_other_data):
            all_players.append((d['slot'], d.get('name', f"P{d['slot']+1}"),
                                 d.get('match_stats', {"shots": 0, "hits": 0,
                                                       "damage": 0, "items": 0}),
                                 False,
                                 t.alive))
        all_players.sort(key=lambda x: x[0])

        # Table header
        cy = panel_y + 45
        col_x = [panel_x + 24, panel_x + 220, panel_x + 320,
                 panel_x + 420, panel_x + 520, panel_x + 620]
        headers = ["Người chơi", "Bắn", "Trúng", "ST", "Item", "Tỉ lệ"]
        for ci, h in enumerate(headers):
            r = FONT_SM.render(h, True, (255, 220, 150))
            s.blit(r, (col_x[ci], cy))
        cy += 28
        slot_colors = [(120, 255, 140), (255, 130, 130), (130, 200, 255), (255, 220, 130)]
        for slot, name, stats, is_local, alive in all_players:
            col = slot_colors[slot % len(slot_colors)]
            shots = stats.get('shots', 0)
            hits = stats.get('hits', 0)
            dmg = stats.get('damage', 0)
            items = stats.get('items', 0)
            acc = (hits / max(1, shots)) * 100
            label = f"P{slot+1} {name[:12]}" + (" (Bạn)" if is_local else "")
            for ci, val in enumerate([label, str(shots), str(hits),
                                       str(dmg), str(items), f"{acc:.0f}%"]):
                r = FONT_SM.render(val, True, col)
                s.blit(r, (col_x[ci], cy))
            cy += 24

        # Rank & info
        cy += 8
        rank_info = (f"Hạng: {self.pvp_rank_names[self.pvp_rank]}   |   "
                     f"Thắng: {self.pvp_wins}   |   Thua: {self.pvp_losses}")
        ri = FONT_SM.render(rank_info, True, (220, 220, 180))
        s.blit(ri, (SW // 2 - ri.get_width() // 2, cy))

        # Buttons
        btn_w, btn_h = 220, 52
        rematch_rect = pygame.Rect(SW // 2 - btn_w - 20, SH - 90, btn_w, btn_h)
        exit_rect = pygame.Rect(SW // 2 + 20, SH - 90, btn_w, btn_h)

        rematch_label = "CHƠI LẠI"
        if self.pvp_rematch_sent:
            rematch_label = "ĐÃ GỬI..."
        draw_kawaii_button(s, rematch_rect, rematch_label, FONT_MED,
                           selected=(self.pvp_end_sel == 0), tick=self.tick)
        draw_kawaii_button(s, exit_rect, "THOÁT", FONT_MED,
                           selected=(self.pvp_end_sel == 1), tick=self.tick)

        if self.pvp_rematch_received and not self.pvp_rematch_sent:
            req_txt = FONT_SM.render("Đối thủ muốn chơi lại!", True, (255, 255, 100))
            s.blit(req_txt, (SW // 2 - req_txt.get_width() // 2, SH - 32))

        hint = FONT_SM.render("[←/→] Chọn  [ENTER] Xác nhận", True, (120, 120, 150))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 15))

    # ═══════════════════════════════════════
    #  CO-OP NETWORKING
    # ═══════════════════════════════════════
    def _coop_cleanup(self):
        self.coop_active = False
        if self.coop_socket:
            try: self.coop_socket.close()
            except Exception: pass
        self.coop_socket = None
        self.coop_host_addr = None
        self.coop_clients = []
        self.coop_others = []
        self.coop_other_data = []
        self.coop_lobby_view = []
        self.coop_recv_thread = None
        self.coop_recv_queue = []
        self.coop_found_hosts = []

    def _coop_start_recv_thread(self):
        def recv_loop():
            while self.coop_active and self.coop_socket:
                try:
                    data, addr = self.coop_socket.recvfrom(65535)
                    with self.coop_recv_lock:
                        self.coop_recv_queue.append((data, addr))
                except socket.timeout:
                    continue
                except Exception:
                    break
        self.coop_recv_thread = threading.Thread(target=recv_loop, daemon=True)
        self.coop_recv_thread.start()

    def _coop_lobby_snapshot(self):
        lobby = [{"slot": 0, "name": self.coop_prep_name or self.player_name, "is_host": self.coop_is_host}]
        for c in self.coop_clients:
            lobby.append({"slot": c["slot"], "name": c["name"], "is_host": False})
        return lobby

    def _coop_count_players(self):
        return 1 + len(self.coop_clients)

    def _coop_send_lobby_to_all(self):
        if not self.coop_is_host:
            return
        lobby = self._coop_lobby_snapshot()
        pkt = json.dumps({"type": "coop_lobby", "lobby": lobby,
                          "level": self.coop_level,
                          "room": self.coop_room_info,
                          "max":  self.coop_max_players}).encode('utf-8')
        for c in self.coop_clients:
            try: self.coop_socket.sendto(pkt, c["addr"])
            except Exception: pass

    def start_coop_host(self):
        self._coop_cleanup()
        self.coop_is_host = True
        self.coop_active = True
        self.coop_my_slot = 0
        self.coop_bind_error = ""
        self.coop_prep_name = self.player_name
        self.coop_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.coop_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bound = False
        for port in [5560, 5561, 5562, 5563]:
            try:
                self.coop_socket.bind(('0.0.0.0', port))
                bound = True
                break
            except Exception:
                continue
        if not bound:
            self.coop_bind_error = "Không thể bind port! Đóng game khác hoặc tắt firewall."
            self._coop_cleanup()
            return False
        self.coop_socket.settimeout(0.005)
        self.coop_clients = []
        self._coop_start_recv_thread()

        host_port = self.coop_socket.getsockname()[1]
        self.coop_level = self.level if self.level > 0 else 1

        def broadcast():
            b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._coop_broadcast_sock = b_sock
            while self.coop_active and self.coop_is_host and self.state in ("coop_waiting", "coop_playing"):
                try:
                    ip = self._get_local_ip()
                    info = {
                        "name": self.coop_prep_name,
                        "mode": "coop",
                        "level": self.coop_level,
                        "players": self._coop_count_players(),
                        "max": self.coop_max_players,
                        "port": host_port,
                    }
                    msg = f"TANK_COOP_HOST|{ip}|{json.dumps(info, ensure_ascii=False)}".encode('utf-8')
                    b_sock.sendto(msg, ('<broadcast>', 5564))
                except Exception: pass
                time.sleep(0.5)
            try: b_sock.close()
            except Exception: pass
            self._coop_broadcast_sock = None
        threading.Thread(target=broadcast, daemon=True).start()
        self.state = "coop_waiting"
        self.coop_lobby_view = self._coop_lobby_snapshot()

    def start_coop_join(self):
        self._coop_cleanup()
        self.coop_is_host = False
        self.coop_active = True
        self.coop_prep_name = self.player_name
        self.coop_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.coop_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: self.coop_socket.bind(('0.0.0.0', 0))
        except Exception: pass
        self.coop_socket.settimeout(0.005)
        self.coop_host_addr = None
        self.state = "coop_joining"
        self.coop_found_hosts = []
        self.coop_menu_sel = 0
        self.coop_manual_ip = ""
        self.coop_manual_ip_editing = False
        self._coop_start_recv_thread()

        def listen_broadcast():
            l_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            l_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try: l_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except Exception: pass
            self._coop_listen_sock = l_sock
            try:
                l_sock.bind(('0.0.0.0', 5564))
                l_sock.settimeout(1.0)
                while self.coop_active and self.state in ("coop_joining", "coop_lobby"):
                    try:
                        data, addr = l_sock.recvfrom(4096)
                        msg = data.decode('utf-8')
                        if msg.startswith("TANK_COOP_HOST|"):
                            parts = msg.split("|", 2)
                            ip = parts[1]
                            info = json.loads(parts[2])
                            found = False
                            for h in self.coop_found_hosts:
                                if h["ip"] == ip and h.get("port") == info.get("port"):
                                    h.update(info)
                                    h["ip"] = ip
                                    found = True
                                    break
                            if not found:
                                info["ip"] = ip
                                self.coop_found_hosts.append(info)
                    except socket.timeout: pass
                    except Exception: pass
            except Exception: pass
            try: l_sock.close()
            except Exception: pass
        threading.Thread(target=listen_broadcast, daemon=True).start()

    def _coop_process_host_packets(self):
        """Process incoming packets on host side."""
        packets = []
        with self.coop_recv_lock:
            packets = list(self.coop_recv_queue)
            self.coop_recv_queue.clear()
        for data, addr in packets:
            try:
                pkt = json.loads(data.decode('utf-8'))
                ptype = pkt.get("type", "")
                if ptype == "coop_join" and self.state == "coop_waiting":
                    if self._coop_count_players() < self.coop_max_players:
                        slot = self._coop_count_players()
                        self.coop_clients.append({
                            "addr": addr, "slot": slot, "name": pkt.get("name", f"P{slot+1}"),
                            "last_recv": time.time(), "inputs": {}
                        })
                        self.coop_lobby_view = self._coop_lobby_snapshot()
                        self._coop_send_lobby_to_all()
                        ack = json.dumps({"type": "coop_accepted", "slot": slot, "level": self.coop_level}).encode('utf-8')
                        self.coop_socket.sendto(ack, addr)
                elif ptype == "coop_input" and self.state == "coop_playing":
                    for c in self.coop_clients:
                        if c["addr"] == addr:
                            c["inputs"] = pkt.get("inputs", {})
                            c["last_recv"] = time.time()
                            # Update other player position
                            c["x"] = pkt.get("x", 0)
                            c["y"] = pkt.get("y", 0)
                            c["dir"] = pkt.get("dir", 0)
                            c["hp"] = pkt.get("hp", 3)
                            c["alive"] = pkt.get("alive", True)
                            break
                elif ptype == "coop_leave":
                    self.coop_clients = [c for c in self.coop_clients if c["addr"] != addr]
                    self.coop_lobby_view = self._coop_lobby_snapshot()
                    self._coop_send_lobby_to_all()
            except Exception: pass

    def _coop_process_client_packets(self):
        """Process incoming packets on client side."""
        packets = []
        with self.coop_recv_lock:
            packets = list(self.coop_recv_queue)
            self.coop_recv_queue.clear()
        for data, addr in packets:
            try:
                pkt = json.loads(data.decode('utf-8'))
                ptype = pkt.get("type", "")
                if ptype == "coop_accepted":
                    self.coop_my_slot = pkt.get("slot", 1)
                    self.coop_level = pkt.get("level", 1)
                    self.state = "coop_lobby"
                elif ptype == "coop_lobby":
                    self.coop_lobby_view = pkt.get("lobby", [])
                    self.coop_level = pkt.get("level", self.coop_level)
                    room = pkt.get("room")
                    if isinstance(room, dict):
                        self.coop_room_info.update(room)
                    self.coop_max_players = pkt.get("max", self.coop_max_players)
                elif ptype == "coop_start":
                    self.coop_level = pkt.get("level", self.coop_level)
                    self.state = "coop_playing"
                    self.start_level(self.coop_level)
                elif ptype == "coop_state":
                    # Update game state from host
                    self.coop_other_data = pkt.get("players", [])
                    enemies_data = pkt.get("enemies", [])
                    bullets_data = pkt.get("bullets", [])
                    self.coop_last_recv = time.time()
                elif ptype == "coop_level_complete":
                    self.coop_level = pkt.get("next_level", self.coop_level + 1)
                    self.state = "coop_playing"
                    self.start_level(self.coop_level)
            except Exception: pass

    def _coop_send_state_to_clients(self):
        """Host sends game state to all clients."""
        if not self.coop_is_host or not self.coop_active:
            return
        players = [{"slot": 0, "name": self.coop_prep_name,
                    "x": self.player.x if self.player else 0,
                    "y": self.player.y if self.player else 0,
                    "dir": self.player.dir if self.player else 0,
                    "hp": self.player.hp if self.player else 0,
                    "alive": self.player.alive if self.player else False}]
        for c in self.coop_clients:
            players.append({"slot": c["slot"], "name": c["name"],
                           "x": c.get("x", 0), "y": c.get("y", 0),
                           "dir": c.get("dir", 0), "hp": c.get("hp", 3),
                           "alive": c.get("alive", True)})
        state = {"type": "coop_state", "players": players,
                "kills": self.kills, "total": self.total_enemies, "level": self.coop_level}
        pkt = json.dumps(state).encode('utf-8')
        for c in self.coop_clients:
            try: self.coop_socket.sendto(pkt, c["addr"])
            except Exception: pass

    def _coop_send_client_input(self):
        """Client sends its input/position to host."""
        if self.coop_is_host or not self.coop_active or not self.coop_host_addr:
            return
        pkt = {
            "type": "coop_input",
            "x": self.player.x if self.player else 0,
            "y": self.player.y if self.player else 0,
            "dir": self.player.dir if self.player else 0,
            "hp": self.player.hp if self.player else 0,
            "alive": self.player.alive if self.player else False,
            "inputs": {},
        }
        try: self.coop_socket.sendto(json.dumps(pkt).encode('utf-8'), self.coop_host_addr)
        except Exception: pass

    def get_scaled_tile(self, img, size):
        key = (id(img), size)
        if key not in self.scaled_tile_cache:
            self.scaled_tile_cache[key] = pygame.transform.scale(img, (size, size))
        return self.scaled_tile_cache[key]

    def start_level(self, level):
        self.level = level
        # Bigger arenas — was 26+2·lvl up to 50.  Now 36+3·lvl up to 70.
        new_cols = min(36 + level * 3, 70)
        new_rows = min(28 + level * 2, 50)

        global COLS, ROWS
        COLS, ROWS = new_cols, new_rows

        self.grid, self.base_pos = generate_map(level, new_cols, new_rows)
        self.lives = 3  # reset lives each level

        # Theme
        self.map_theme = self.get_theme_for_level(level)
        sprites.set_floor_theme(self.map_theme)
        weather.set_weather(self.map_theme)

        # Zoom in CLOSE to the tank and follow it.  Camera smoothly
        # lerps toward the player every frame in update().
        self.target_zoom = 1.8
        self.cam_zoom = 1.8

        # Player
        self.player = Tank(new_cols // 2 - 2, new_rows - 2, "player")
        # Center camera on player immediately, then clamp within the map.
        self.cam_x = self.player.x - (SW / self.cam_zoom) / 2
        self.cam_y = self.player.y - (SH / self.cam_zoom) / 2
        _vw = SW / self.cam_zoom
        _vh = SH / self.cam_zoom
        _mw, _mh = new_cols * 32, new_rows * 32
        self.cam_x = max(0, min(self.cam_x, max(0, _mw - _vw)))
        self.cam_y = max(0, min(self.cam_y, max(0, _mh - _vh)))
        self.player.tier = self.player_tier
        self.player.name = self.player_name

        # Spawn pet if active
        if self.active_pet_type and self.active_pet_type in self.owned_pets:
            self.pet = Pet(self.active_pet_type, self.player)
        else:
            self.pet = None

        if self.auto_mode:
            self.player.speed = 3.5
            self.player.shoot_delay = 5
            self.player.max_hp = 10
            self.player.hp = 10
            self.player.shield = 5
        else:
            self.player.hp = 3 + min(level // 3, 3)
            self.player.max_hp = self.player.hp

        # Apply bought skills
        if getattr(self, 'bought_skills', None):
            for skill, val in self.bought_skills.items():
                if hasattr(self.player, skill):
                    setattr(self.player, skill, val)
            self.bought_skills = {}

        self.enemies = []
        self.chickens = []
        self.dogs = []
        self.bullets = []
        self.explosions = []
        self.items = []
        self.active_boss = None
        self.boss_warning_timer = 0
        particles.clear()
        floating_texts.clear()

        num_chickens = 0
        num_dogs = 0
        is_boss_level = (level % 5 == 0)

        # Story mission descriptions per level
        _story_missions = [
            "Giải phóng làng quê — tiêu diệt 3 xe tăng địch",
            "Tiến quân chiếm tiền đồn — giết gà lấy tiền mua đồ",
            "Phục kích! Chó điên xuất hiện — cẩn thận!",
            "Vượt sa mạc nóng bỏng",
            "BOSS: Tướng Sa Mạc xuất hiện!",
            "Chiến đấu trong bão tuyết",
            "Đột kích căn cứ địch ban đêm",
            "Phá vòng vây của 3 đội quân",
            "Sống sót qua trận tuyết lở",
            "BOSS: Tướng Băng Giá xuất hiện!",
            "Xuyên qua rừng rậm nguy hiểm",
            "Vượt đầm lầy đầy bẫy mìn",
            "Phản công giành lại lãnh thổ",
            "Xâm nhập hang núi bí mật",
            "BOSS: Tướng Rừng Rậm xuất hiện!",
            "Giải phóng thành phố bị chiếm đóng",
            "Đánh chiếm pháo đài cuối cùng",
            "Tổng tấn công toàn tuyến",
            "Mở cổng vào sào huyệt kẻ thù",
            "TRÙM CUỐI: Giải cứu thế giới!",
        ]
        if level == 1:
            self.total_enemies = 3
            self.max_alive = 1
            self.mission_text = _story_missions[0]
            self.mission_timer = 240
        elif level == 2:
            self.total_enemies = 4
            self.max_alive = 2
            num_chickens = 5
            self.mission_text = _story_missions[1]
            self.mission_timer = 240
        elif level == 3:
            self.total_enemies = 8
            self.max_alive = 4
            num_chickens = 4
            num_dogs = 2
            self.mission_text = _story_missions[2]
            self.mission_timer = 240
        elif is_boss_level:
            self.total_enemies = 3 + level
            self.max_alive = min(5 + level // 2, 12)
            num_chickens = 3
            num_dogs = 2
            idx = min(level - 1, len(_story_missions) - 1)
            self.mission_text = _story_missions[idx]
            self.mission_timer = 300
            snd_boss_alert.play()
        else:
            self.total_enemies = 3 + level
            self.max_alive = min(3 + level, 10)
            num_chickens = 3 + level
            num_dogs = 1 + level // 3
            idx = min(level - 1, len(_story_missions) - 1)
            self.mission_text = _story_missions[idx]
            self.mission_timer = 180

        self.enemies_to_spawn = self.total_enemies
        self.kills = 0
        self.spawn_timer = 0
        self.spawn_points = [(2, 1), (new_cols // 2, 1), (new_cols - 3, 1)]
        self.combo = 0
        self.combo_timer = 0

        # Spawn NPCs
        for _ in range(num_chickens):
            rx, ry = random.randint(5, new_cols - 5), random.randint(5, new_rows - 5)
            if self.grid[ry][rx] == EMPTY: self.chickens.append(Chicken(rx, ry))
        for _ in range(num_dogs):
            rx, ry = random.randint(5, new_cols - 5), random.randint(5, new_rows - 5)
            if self.grid[ry][rx] == EMPTY: self.dogs.append(Dog(rx, ry))

        if getattr(self, 'bought_nuke', False):
            self.items.append(Item(new_cols // 2 - 2, new_rows - 3, "star"))
            self.bought_nuke = False

        self.state = "playing"

        for _ in range(min(3, self.enemies_to_spawn)):
            self.spawn_enemy()

    def spawn_enemy(self):
        if self.enemies_to_spawn <= 0: return
        available_spawns = []
        for sp in self.spawn_points:
            occupied = any(e.alive and e.get_grid() == sp for e in self.enemies)
            if not occupied: available_spawns.append(sp)
        if not available_spawns: return

        sp = random.choice(available_spawns)
        is_boss_level = (self.level % 5 == 0)

        types = ["enemy_a"] * 5 + ["enemy_b"] * 3
        if self.level >= 3:
            types += ["elite"] * (self.level - 1)

        difficulty = min(0.4 + self.level * 0.1, 2.5)

        if is_boss_level and self.enemies_to_spawn == 1:
            # Spawn unique BossTank based on level
            boss_key = BOSS_LEVEL_MAP.get(self.level)
            if boss_key is None:
                # For boss levels beyond 20, cycle through bosses with increasing difficulty
                cycle = ((self.level // 5 - 1) % 4)
                boss_keys = list(BOSS_LEVEL_MAP.values())
                boss_key = boss_keys[cycle]
            enemy = BossTank(sp[0], sp[1], boss_key, difficulty)
            self.active_boss = enemy  # track active boss for HP bar
        else:
            etype = random.choice(types)
            enemy = EnemyTank(sp[0], sp[1], etype, difficulty)

        self.enemies.append(enemy)
        self.enemies_to_spawn -= 1
        spawn_particles(sp[0] * TS + TS // 2, sp[1] * TS + TS // 2, (255, 255, 200), 12)

    def register_kill(self, x, y, base_score):
        self.score += base_score
        self.combo += 1
        self.combo_timer = 180
        self.total_kills += 1
        self.stats["total_kills"] += 1
        if self.combo > self.stats["max_combo"]:
            self.stats["max_combo"] = self.combo

        self.shake_amount = min(self.shake_amount + 5, 25)

        if self.combo == 2:
            floating_texts.append(FloatingText(x, y - 20, "HẠ ĐÔI!", (255, 100, 255)))
            self.money += 20
        elif self.combo == 3:
            floating_texts.append(FloatingText(x, y - 20, "HẠ BA!!", (255, 50, 50)))
            self.money += 50
            snd_combo.play()
        elif self.combo == 4:
            floating_texts.append(FloatingText(x, y - 20, "ĐIÊN CUỒNG!!!", (255, 0, 0)))
            self.money += 100
            snd_combo.play()
        elif self.combo >= 5:
            floating_texts.append(FloatingText(x, y - 20, "THẦN THÁNH!!!!!", (255, 0, 255), huge=True))
            self.money += 200
            snd_combo.play()
            trigger_achievement("THẦN THÁNH!", "5+ chuỗi trong 1 loạt!", (255, 0, 255))

        if random.random() < 0.2 + (self.combo * 0.05):
            self.items.append(Item(int(x // TS), int(y // TS), "money"))

    # ═══════════════════════════════════
    # AUTO MODE
    # ═══════════════════════════════════
    def auto_play(self):
        if not self.player.alive or self.player.spawn_timer > 0: return
        my_pos = self.player.get_grid()
        alive_enemies = [e for e in self.enemies if e.alive and e.spawn_timer <= 0]

        # Dodge system
        dodge_dir = -1
        danger_bullets = [b for b in self.bullets if b.owner != "player" and b.alive
                         and math.hypot(b.x - self.player.x, b.y - self.player.y) < TS * 3.5]

        if danger_bullets:
            safe = Pathfinder.get_safe_directions(self.grid, self.player.x, self.player.y)
            if safe:
                best_d = -1; max_safety = -1
                for d in safe:
                    ddx, ddy = DIRS[d]
                    nx = self.player.x + ddx * self.player.speed
                    ny = self.player.y + ddy * self.player.speed
                    current_safety = min((math.hypot(nx - b.x, ny - b.y) for b in danger_bullets), default=1000)
                    if current_safety > max_safety:
                        max_safety = current_safety; best_d = d
                if max_safety < TS * 1.5:
                    dodge_dir = best_d

        # Shoot visible enemies
        visible_enemies = []
        for enemy in alive_enemies:
            epos = enemy.get_grid()
            if Pathfinder.can_shoot(self.grid, my_pos[0], my_pos[1], epos[0], epos[1]):
                dist = abs(my_pos[0] - epos[0]) + abs(my_pos[1] - epos[1])
                visible_enemies.append((dist, enemy))

        if visible_enemies:
            visible_enemies.sort(key=lambda x: x[0])
            target = visible_enemies[0][1]
            epos = target.get_grid()
            if my_pos[0] == epos[0]:
                self.player.dir = 0 if epos[1] < my_pos[1] else 2
            else:
                self.player.dir = 1 if epos[0] > my_pos[0] else 3
            bullets = self.player.shoot()
            if bullets: self.bullets.extend(bullets)

        # Movement
        if dodge_dir != -1:
            ddx, ddy = DIRS[dodge_dir]
            self.player.move(ddx * self.player.speed, ddy * self.player.speed, self.grid, self.enemies)
        else:
            item_target = None
            for it in self.items:
                if it.alive and abs(my_pos[0] - it.gx) + abs(my_pos[1] - it.gy) < 5:
                    item_target = it; break

            nav_goal = None
            if item_target:
                nav_goal = (item_target.gx, item_target.gy)
            elif alive_enemies:
                nearest = min(alive_enemies, key=lambda e: abs(my_pos[0] - e.get_grid()[0]) + abs(my_pos[1] - e.get_grid()[1]))
                nav_goal = nearest.get_grid()

            if nav_goal:
                self.auto_path_update += 1
                if self.auto_path_update >= 20 or not self.auto_path or self.auto_path[-1] != nav_goal:
                    self.auto_path_update = 0
                    if self.auto_algo == "A*":
                        self.auto_path = Pathfinder.a_star_path(self.grid, my_pos, nav_goal)
                    elif self.auto_algo == "BFS":
                        self.auto_path = Pathfinder.bfs_path(self.grid, my_pos, nav_goal)
                    else:
                        self.auto_path = Pathfinder.dfs_path(self.grid, my_pos, nav_goal)

                if len(self.auto_path) > 1:
                    next_node = self.auto_path[1]
                    tile_type = self.grid[int(next_node[1])][int(next_node[0])]
                    if tile_type in (BRICK, CRATE):
                        self.player.dir = Pathfinder.get_next_direction(my_pos, next_node)
                        bullets = self.player.shoot()
                        if bullets: self.bullets.extend(bullets)
                    else:
                        ndir = Pathfinder.get_next_direction(my_pos, next_node)
                        if ndir != -1:
                            ddx, ddy = DIRS[ndir]
                            moved = self.player.move(ddx * self.player.speed, ddy * self.player.speed, self.grid, self.enemies)
                            if moved and self.player.get_grid() == next_node:
                                self.auto_path.pop(0)
                else:
                    self.auto_path = []

    def _activate_menu_selection(self):
        choice = self.menu_buttons[self.menu_sel]
        if choice == "CHIẾN ĐẤU":
            self.state = "level_select"
        elif choice == "SHOP":
            self.state = "shop"
        elif choice == "GA-RA":
            self.state = "garage"
        elif choice == "NÂNG CẤP":
            self.state = "shop"
        elif choice == "THÀNH TỰU":
            self.state = "achievements"
        elif choice == "CHƠI MẠNG (PVP)":
            self.state = "pvp_menu"
            self.pvp_menu_sel = 0
        elif choice == "CHƠI CHUNG (CO-OP)":
            self.state = "coop_menu"
            self.coop_menu_sel = 0
        elif choice == "VÒNG QUAY":
            self.state = "lucky_spin"
            try: pygame.mixer.music.stop()
            except Exception: pass
        elif choice == "CÀI ĐẶT":
            self.state = "settings"
            self.settings_sel = 0
            self._settings_prev_state = "title"


    def handle_event(self, ev):
        # Settings screen owns its own keyboard + mouse handling so that
        # sliders, toggles, choice arrows and action buttons all respond
        # to click + drag.  Route every event there before the generic
        # dispatch below.
        if self.state == "settings" and ev.type in (
            pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION,
        ):
            self._handle_settings_event(ev)
            return
        if ev.type == pygame.KEYDOWN:
            # Global hotkeys (work in any state)
            if ev.key == pygame.K_F11:
                toggle_fullscreen()
                return
            if self.state == "title":
                if ev.key == pygame.K_ESCAPE:
                    self._save_game()
                    pygame.quit()
                    sys.exit()
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_sel = (self.menu_sel + 1) % len(self.menu_buttons)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self.menu_sel = (self.menu_sel - 1) % len(self.menu_buttons)
                elif ev.key == pygame.K_RETURN:
                    self._activate_menu_selection()
                elif ev.key == pygame.K_h:
                    self.state = "tutorial"
                    self.tutorial_page = 0
            elif self.state == "daily_checkin":
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._claim_daily()
                elif ev.key == pygame.K_ESCAPE:
                    self.state = "title"
            elif self.state == "level_select":
                # Grid-mode (world-map background) supports 2-D navigation
                # because the tiles are laid out as a 5×4 grid.
                grid_mode = bool(getattr(self, 'level_select_bg', None))
                if grid_mode and ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.level_sel = min(self.max_levels - 1, self.level_sel + 5)
                elif grid_mode and ev.key in (pygame.K_UP, pygame.K_w):
                    self.level_sel = max(0, self.level_sel - 5)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                    self.level_sel = min(self.max_levels - 1, self.level_sel + 1)
                elif ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                    self.level_sel = max(0, self.level_sel - 1)
                elif ev.key == pygame.K_RETURN:
                    chosen_level = self.level_sel + 1  # 1-based
                    if chosen_level in self.unlocked_levels:
                        def start():
                            self.score = 0; self.lives = 3
                            self.total_kills = 0; self.total_money_earned = 0
                            self.player_tier = self.skin_idx
                            self.start_level(chosen_level)
                            self.state = "level_start"
                            pygame.mixer.music.stop()
                        transition.start(start)
                    else:
                        snd_deny.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            "MÀN NÀY CHƯA MỞ KHÓA!", (255, 80, 80), center_bounce=True))
                elif ev.key == pygame.K_ESCAPE:
                    self.state = "title"
            elif self.state == "garage":
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.skin_idx = (self.skin_idx - 1) % len(self.skin_names)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.skin_idx = (self.skin_idx + 1) % len(self.skin_names)
                elif ev.key == pygame.K_RETURN:
                    if self.skin_idx not in self.unlocked_skins:
                        cost = (self.skin_idx + 1) * 200
                        if self.gems >= cost:
                            self.gems -= cost
                            self.unlocked_skins.add(self.skin_idx)
                elif ev.key == pygame.K_ESCAPE:
                    self.state = "title"
            elif self.state == "achievements":
                if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = "title"
            elif self.state == "tutorial":
                if ev.key == pygame.K_ESCAPE or ev.key == pygame.K_RETURN:
                    self.state = "title"
                elif ev.key == pygame.K_RIGHT:
                    self.tutorial_page = min(3, self.tutorial_page + 1)
                elif ev.key == pygame.K_LEFT:
                    self.tutorial_page = max(0, self.tutorial_page - 1)
            elif self.state == "lucky_spin":
                if ev.key == pygame.K_ESCAPE:
                    if not self.spin_active and not self.reveal_active:
                        self.state = "title"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass

                elif ev.key == pygame.K_RETURN:
                    if not self.spin_active and not self.reveal_active:
                        self.start_lucky_spin()
                    elif self.reveal_active and self.reveal_timer >= 60:
                        self.close_reveal()

            elif self.state == "pvp_menu":
                if ev.key == pygame.K_ESCAPE:
                    self.state = "title"
                elif ev.key == pygame.K_UP:
                    self.pvp_menu_sel = (self.pvp_menu_sel - 1) % len(self.pvp_menu_options)
                elif ev.key == pygame.K_DOWN:
                    self.pvp_menu_sel = (self.pvp_menu_sel + 1) % len(self.pvp_menu_options)
                elif ev.key == pygame.K_RETURN:
                    sel = self.pvp_menu_options[self.pvp_menu_sel]
                    if sel == "TẠO PHÒNG (HOST)":
                        self.state = "pvp_prep"
                        self.pvp_prep_field = 0
                        self.pvp_prep_items = []
                    elif sel == "TÌM PHÒNG (JOIN)":
                        self.start_pvp_join()
                    else:
                        self.state = "title"
            elif self.state == "pvp_prep":
                if ev.key == pygame.K_ESCAPE:
                    self.state = "pvp_menu"
                elif ev.key == pygame.K_UP:
                    self.pvp_prep_field = max(0, self.pvp_prep_field - 1)
                elif ev.key == pygame.K_DOWN:
                    self.pvp_prep_field = min(5, self.pvp_prep_field + 1)
                elif ev.key == pygame.K_RETURN:
                    if self.pvp_prep_field == 0:
                        self.pvp_name_editing = not self.pvp_name_editing
                    elif self.pvp_prep_field == 5:
                        # Create room - cycle map size on enter
                        self.pvp_prep_map_size = (self.pvp_prep_map_size + 1) % 3
                    else:
                        # Start hosting
                        self.player_name = self.pvp_prep_name
                        self.start_pvp_host()
                elif ev.key == pygame.K_LEFT:
                    if self.pvp_prep_field == 2:  # Pet
                        pets = [None] + self.owned_pets
                        idx = 0
                        if self.pvp_prep_pet in pets:
                            idx = pets.index(self.pvp_prep_pet)
                        idx = (idx - 1) % len(pets)
                        self.pvp_prep_pet = pets[idx]
                    elif self.pvp_prep_field == 3:  # Bet mode
                        self.pvp_prep_bet_mode = 1 - self.pvp_prep_bet_mode
                    elif self.pvp_prep_field == 4:  # Bet amount
                        self.pvp_prep_bet_amount = max(100, self.pvp_prep_bet_amount - 100)
                    elif self.pvp_prep_field == 5:  # Map size
                        self.pvp_prep_map_size = (self.pvp_prep_map_size - 1) % 3
                elif ev.key == pygame.K_RIGHT:
                    if self.pvp_prep_field == 2:  # Pet
                        pets = [None] + self.owned_pets
                        idx = 0
                        if self.pvp_prep_pet in pets:
                            idx = pets.index(self.pvp_prep_pet)
                        idx = (idx + 1) % len(pets)
                        self.pvp_prep_pet = pets[idx]
                    elif self.pvp_prep_field == 3:  # Bet mode
                        self.pvp_prep_bet_mode = 1 - self.pvp_prep_bet_mode
                    elif self.pvp_prep_field == 4:  # Bet amount
                        self.pvp_prep_bet_amount = min(int(self.money), self.pvp_prep_bet_amount + 100)
                    elif self.pvp_prep_field == 5:  # Map size
                        self.pvp_prep_map_size = (self.pvp_prep_map_size + 1) % 3
                elif ev.key == pygame.K_SPACE:
                    # Quick create room shortcut
                    self.player_name = self.pvp_prep_name
                    self.start_pvp_host()
                elif self.pvp_name_editing and self.pvp_prep_field == 0:
                    if ev.key == pygame.K_BACKSPACE:
                        self.pvp_prep_name = self.pvp_prep_name[:-1]
                    elif ev.unicode and len(self.pvp_prep_name) < 16:
                        self.pvp_prep_name += ev.unicode
                elif self.pvp_prep_field == 1:
                    # Item selection with number keys
                    if ev.key in range(pygame.K_1, pygame.K_9 + 1):
                        idx = ev.key - pygame.K_1
                        bp = list(self.backpack)
                        if idx < len(bp):
                            item = bp[idx]
                            if item in self.pvp_prep_items:
                                self.pvp_prep_items.remove(item)
                            elif len(self.pvp_prep_items) < 3:
                                self.pvp_prep_items.append(item)
            elif self.state == "pvp_joining":
                if ev.key == pygame.K_ESCAPE:
                    self._pvp_cleanup()
                    self.state = "pvp_menu"
                elif ev.key == pygame.K_TAB:
                    self.pvp_manual_ip_editing = not self.pvp_manual_ip_editing
                elif self.pvp_manual_ip_editing:
                    if ev.key == pygame.K_BACKSPACE:
                        self.pvp_manual_ip = self.pvp_manual_ip[:-1]
                    elif ev.key == pygame.K_RETURN:
                        if self.pvp_manual_ip:
                            self.connect_pvp_manual_ip(self.pvp_manual_ip)
                    elif ev.unicode and (ev.unicode.isdigit() or ev.unicode in '.:') and len(self.pvp_manual_ip) < 21:
                        self.pvp_manual_ip += ev.unicode
                else:
                    if ev.key == pygame.K_UP and self.pvp_found_hosts:
                        self.pvp_join_sel = (self.pvp_join_sel - 1) % len(self.pvp_found_hosts)
                    elif ev.key == pygame.K_DOWN and self.pvp_found_hosts:
                        self.pvp_join_sel = (self.pvp_join_sel + 1) % len(self.pvp_found_hosts)
                    elif ev.key == pygame.K_RETURN and self.pvp_found_hosts:
                        sel_idx = min(self.pvp_join_sel, len(self.pvp_found_hosts) - 1)
                        host_entry = self.pvp_found_hosts[sel_idx]
                        room_info = host_entry[2] if len(host_entry) > 2 else {}
                        # Check if enough money for bet
                        if room_info.get('mode') == 'bet':
                            bet = room_info.get('bet', 0)
                            if self.money < bet:
                                floating_texts.append(FloatingText(SW // 2, SH // 2,
                                    "KHÔNG ĐỦ TIỀN!", (255, 80, 80), center_bounce=True))
                                return
                        self.connect_pvp_host(host_entry)
            elif self.state == "pvp_waiting":
                if ev.key == pygame.K_ESCAPE:
                    # Refund bet if cancelling
                    if self.pvp_bet_active:
                        self.money += self.pvp_bet_amount_match
                        self.pvp_bet_active = False
                        self._save_game()
                    self._pvp_cleanup()
                    self.state = "pvp_menu"
                elif ev.key == pygame.K_RETURN:
                    # Host can press Enter to start the match if enough players
                    if self.pvp_is_host and self._pvp_count_lobby_players() >= self.pvp_min_start:
                        self._pvp_host_start_match()
                    else:
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            f"CẦN ÍT NHẤT {self.pvp_min_start} NGƯỜI CHƠI!",
                            (255, 180, 80), center_bounce=True))
                elif ev.key == pygame.K_LEFT:
                    self.skin_idx = (self.skin_idx - 1) % len(self.skin_names)
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()
                elif ev.key == pygame.K_RIGHT:
                    self.skin_idx = (self.skin_idx + 1) % len(self.skin_names)
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()
                elif ev.key == pygame.K_BACKSPACE:
                    self.pvp_prep_name = self.pvp_prep_name[:-1]
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()
                elif ev.unicode and len(self.pvp_prep_name) < 16 and ev.key != pygame.K_RETURN:
                    self.pvp_prep_name += ev.unicode
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()
            elif self.state == "pvp_lobby":
                if ev.key == pygame.K_ESCAPE:
                    # Client leaves lobby - send leave packet to host then cleanup
                    if self.pvp_socket and self.pvp_host_addr:
                        try:
                            leave_pkt = json.dumps({
                                'type': 'leave',
                                'name': self.pvp_prep_name,
                            }).encode('utf-8')
                            self.pvp_socket.sendto(leave_pkt, self.pvp_host_addr)
                        except Exception: pass
                    # Refund bet if cancelling
                    if self.pvp_bet_active:
                        self.money += self.pvp_bet_amount_match
                        self.pvp_bet_active = False
                        self._save_game()
                    self._pvp_cleanup()
                    self.state = "pvp_menu"
                elif ev.key == pygame.K_LEFT:
                    self.skin_idx = (self.skin_idx - 1) % len(self.skin_names)
                    self.pvp_needs_join_resend = True
                elif ev.key == pygame.K_RIGHT:
                    self.skin_idx = (self.skin_idx + 1) % len(self.skin_names)
                    self.pvp_needs_join_resend = True
                elif ev.key == pygame.K_BACKSPACE:
                    self.pvp_prep_name = self.pvp_prep_name[:-1]
                    self.pvp_needs_join_resend = True
                    for s in self.pvp_lobby_view:
                        if s and s.get('slot', -1) == getattr(self, 'pvp_my_slot', -1):
                            s['name'] = self.pvp_prep_name
                elif ev.unicode and len(self.pvp_prep_name) < 16 and ev.key != pygame.K_RETURN:
                    self.pvp_prep_name += ev.unicode
                    self.pvp_needs_join_resend = True
                    for s in self.pvp_lobby_view:
                        if s and s.get('slot', -1) == getattr(self, 'pvp_my_slot', -1):
                            s['name'] = self.pvp_prep_name
            elif self.state == "pvp_playing":
                if ev.key == pygame.K_ESCAPE:
                    self._pvp_broadcast_quit()
                    self._pvp_cleanup()
                    self.state = "pvp_menu"
                # Quick chat: keys 5-8
                elif ev.key == pygame.K_5:
                    self._pvp_send_chat(0)
                elif ev.key == pygame.K_6:
                    self._pvp_send_chat(1)
                elif ev.key == pygame.K_7:
                    self._pvp_send_chat(2)
                elif ev.key == pygame.K_8:
                    self._pvp_send_chat(3)
                # Use backpack items: keys 1-3
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    idx = ev.key - pygame.K_1
                    self._pvp_use_backpack_item(idx)
            elif self.state == "pvp_end":
                if ev.key == pygame.K_ESCAPE:
                    self._pvp_cleanup()
                    self.state = "pvp_menu"
                elif ev.key == pygame.K_LEFT:
                    self.pvp_end_sel = 0
                elif ev.key == pygame.K_RIGHT:
                    self.pvp_end_sel = 1
                elif ev.key == pygame.K_RETURN:
                    if self.pvp_end_sel == 0:  # Rematch
                        self._pvp_request_rematch()
                    else:  # Exit
                        self._pvp_broadcast_quit()
                        self._pvp_cleanup()
                        self.state = "pvp_menu"
            # ── SETTINGS event handling ──
            elif self.state == "settings":
                self._handle_settings_event(ev)
            elif self.state == "keybinds":
                self._handle_keybinds_event(ev)
            elif self.state == "login":
                self._handle_login_event(ev)
            # ── CO-OP event handling ──
            elif self.state == "coop_menu":
                if ev.key == pygame.K_ESCAPE:
                    self.state = "title"
                elif ev.key == pygame.K_UP:
                    self.coop_menu_sel = (self.coop_menu_sel - 1) % len(self.coop_menu_options)
                elif ev.key == pygame.K_DOWN:
                    self.coop_menu_sel = (self.coop_menu_sel + 1) % len(self.coop_menu_options)
                elif ev.key == pygame.K_RETURN:
                    sel = self.coop_menu_options[self.coop_menu_sel]
                    if sel == "TẠO PHÒNG (HOST)":
                        # Go to the room configuration screen first instead of
                        # opening a barebones LAN socket right away.
                        self.coop_prep_field = 0
                        self.coop_prep_name = self.player_name
                        self.coop_prep_name_editing = False
                        self.coop_prep_room_name_editing = False
                        self.state = "coop_prep"
                    elif sel == "VÀO PHÒNG (JOIN)":
                        self.start_coop_join()
                    else:
                        self.state = "title"
            elif self.state == "coop_prep":
                self._handle_coop_prep_event(ev)
            elif self.state == "coop_waiting":
                if ev.key == pygame.K_ESCAPE:
                    self._coop_cleanup()
                    self.state = "coop_menu"
                elif ev.key == pygame.K_RETURN:
                    if self.coop_is_host and self._coop_count_players() >= 2:
                        # Start co-op game
                        pkt = json.dumps({"type": "coop_start", "level": self.coop_level}).encode('utf-8')
                        for c in self.coop_clients:
                            try: self.coop_socket.sendto(pkt, c["addr"])
                            except Exception: pass
                        self.state = "coop_playing"
                        self.start_level(self.coop_level)
                    elif self._coop_count_players() < 2:
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            "CẦN ÍT NHẤT 2 NGƯỜI CHƠI!", (255, 180, 80), center_bounce=True))
            elif self.state == "coop_joining":
                if ev.key == pygame.K_ESCAPE:
                    self._coop_cleanup()
                    self.state = "coop_menu"
                elif ev.key == pygame.K_TAB:
                    self.coop_manual_ip_editing = not self.coop_manual_ip_editing
                elif self.coop_manual_ip_editing:
                    if ev.key == pygame.K_BACKSPACE:
                        self.coop_manual_ip = self.coop_manual_ip[:-1]
                    elif ev.key == pygame.K_RETURN:
                        if self.coop_manual_ip:
                            try:
                                parts = self.coop_manual_ip.split(":")
                                ip = parts[0]
                                port = int(parts[1]) if len(parts) > 1 else 5560
                                self.coop_host_addr = (ip, port)
                                join_pkt = json.dumps({"type": "coop_join", "name": self.coop_prep_name or self.player_name}).encode('utf-8')
                                self.coop_socket.sendto(join_pkt, self.coop_host_addr)
                            except Exception: pass
                    elif ev.unicode:
                        self.coop_manual_ip += ev.unicode
                elif ev.key == pygame.K_UP:
                    if self.coop_found_hosts:
                        self.coop_menu_sel = (self.coop_menu_sel - 1) % len(self.coop_found_hosts)
                elif ev.key == pygame.K_DOWN:
                    if self.coop_found_hosts:
                        self.coop_menu_sel = (self.coop_menu_sel + 1) % len(self.coop_found_hosts)
                elif ev.key == pygame.K_RETURN:
                    if self.coop_found_hosts and self.coop_menu_sel < len(self.coop_found_hosts):
                        host = self.coop_found_hosts[self.coop_menu_sel]
                        self.coop_host_addr = (host["ip"], host.get("port", 5560))
                        join_pkt = json.dumps({"type": "coop_join", "name": self.coop_prep_name or self.player_name}).encode('utf-8')
                        try: self.coop_socket.sendto(join_pkt, self.coop_host_addr)
                        except Exception: pass
            elif self.state == "coop_lobby":
                if ev.key == pygame.K_ESCAPE:
                    self._coop_cleanup()
                    self.state = "coop_menu"

            elif self.state == "level_start":
                if ev.key == pygame.K_SPACE:
                    self.state = "playing"
            elif self.state == "playing":
                if ev.key == pygame.K_f:
                    self.auto_mode = not self.auto_mode
                    self.auto_path = []
                    if self.auto_mode:
                        self.player.speed = 3.5
                        self.player.shoot_delay = 5
                        self.player.max_hp = 10
                        self.player.hp = 10
                        self.player.shield = 5
                        msg = "BUFF TỰ ĐỘNG: BẬT"
                    else:
                        self.player.speed = 1.8
                        self.player.shoot_delay = 20
                        normal_max = 3 + min(self.level // 3, 3)
                        self.player.max_hp = normal_max
                        self.player.hp = min(self.player.hp, normal_max)
                        msg = "BUFF TỰ ĐỘNG: TẮT"
                    c = (80, 255, 130) if self.auto_mode else (255, 100, 80)
                    floating_texts.append(FloatingText(self.player.x, self.player.y - 40, msg, c))

                if ev.key == pygame.K_g:
                    self.auto_algo_idx = (self.auto_algo_idx + 1) % len(self.auto_algos)
                    self.auto_algo = self.auto_algos[self.auto_algo_idx]
                    self.auto_path = []
                    floating_texts.append(FloatingText(self.player.x, self.player.y - 80, f"THUẬT TOÁN: {self.auto_algo}", (255, 255, 0), huge=True))

                if ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    idx = ev.key - pygame.K_1
                    if idx < len(self.backpack):
                        item_kind = self.backpack.pop(idx)
                        self.apply_item_ultra(item_kind)
                        snd_pickup.play()

                # Quick-fire freeze / grenade via keybinds (if the player has any)
                kb_freeze = self.keybinds.get("freeze") or pygame.K_f
                kb_grenade = self.keybinds.get("grenade") or pygame.K_g
                if ev.key == kb_freeze:
                    # Use a freeze power-up from the backpack if available
                    for ii, it in enumerate(self.backpack):
                        if it == "freeze":
                            self.backpack.pop(ii)
                            self.apply_item_ultra("freeze")
                            snd_pickup.play()
                            break
                elif ev.key == kb_grenade:
                    for ii, it in enumerate(self.backpack):
                        if it == "grenade":
                            self.backpack.pop(ii)
                            self.apply_item_ultra("grenade")
                            snd_pickup.play()
                            break

                if ev.key == pygame.K_ESCAPE or ev.key == (self.keybinds.get("pause") or pygame.K_ESCAPE):
                    self.state = "pause"
                    self.pause_sel = 0

            elif self.state == "pause":
                if ev.key == pygame.K_ESCAPE or ev.key == (self.keybinds.get("pause") or pygame.K_ESCAPE):
                    self.state = "playing"
                elif ev.key == pygame.K_UP:
                    self.pause_sel = (self.pause_sel - 1) % len(self.pause_items)
                elif ev.key == pygame.K_DOWN:
                    self.pause_sel = (self.pause_sel + 1) % len(self.pause_items)
                elif ev.key == pygame.K_RETURN:
                    sel = self.pause_items[self.pause_sel]
                    if sel == "TIẾP TỤC": self.state = "playing"
                    elif sel == "CHƠI LẠI":
                        self.start_level(self.level)
                        pygame.mixer.music.stop()
                    elif sel == "VÀO SHOP":
                        self.state = "shop"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    elif sel == "CÁCH CHƠI":
                        self.state = "tutorial"
                        self.tutorial_page = 0
                    elif sel == "CÀI ĐẶT":
                        self._settings_prev_state = "pause"
                        self.state = "settings"
                        self.settings_sel = 0
                    elif sel == "VỀ SẢNH":
                        self.state = "title"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    elif sel == "THOÁT GAME":
                        self._save_game(); pygame.quit(); sys.exit()

            elif self.state in ("gameover", "level_clear"):
                if ev.key == pygame.K_RETURN:
                    def go_shop():
                        self.state = "shop"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    transition.start(go_shop)

            elif self.state == "shop":
                self.handle_shop_events(ev)

        # ── Mouse click handling for ALL UI screens ──
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # Map mouse event click position perfectly from physical screen coordinates to 1280x720 logical space
            mx = int(ev.pos[0] * (1280 / phys_w))
            my = int(ev.pos[1] * (720 / phys_h))

            # Title screen mouse click
            if self.state == "title":
                # Pixel-art title background → use button rects from layout
                if getattr(self, 'title_bg', None) or getattr(self, 'title_bg_frames', None):
                    # Top-overlay "+" buttons → open shop
                    pg = getattr(self, "_title_plus_gold_rect", None)
                    pm = getattr(self, "_title_plus_gems_rect", None)
                    if pg and pg.collidepoint(mx, my):
                        self.state = "shop"
                        self.shop_tab = 3  # ĐẶC BIỆT tab if it exists
                        return
                    if pm and pm.collidepoint(mx, my):
                        self.state = "shop"
                        self.shop_tab = 3
                        return
                    for _lbl, rect, midx in self._title_button_rects():
                        if rect.collidepoint(mx, my):
                            self.menu_sel = midx
                            self._activate_menu_selection()
                            break
                else:
                    gap = 12
                    total_h = len(self.menu_buttons) * (68 + gap) - gap
                    start_y = (SH - total_h) // 2 + 20
                    for i in range(len(self.menu_buttons)):
                        bw, bh = 260, 68
                        bx = 50
                        by = start_y + i * (bh + gap)

                        draw_x = bx
                        if i == self.menu_sel:
                            draw_x += 15

                        if pygame.Rect(draw_x, by, bw, bh).collidepoint(mx, my):
                            self.menu_sel = i
                            self._activate_menu_selection()
                            break

            elif self.state == "login":
                # Click anywhere on the splash video → enter the game.
                self._skip_splash()

            elif self.state == "daily_checkin":
                close_r = getattr(self, "_daily_close_rect", None)
                claim_r = getattr(self, "_daily_claim_rect", None)
                if close_r and close_r.collidepoint(mx, my):
                    self.state = "title"
                    return
                if claim_r and claim_r.collidepoint(mx, my):
                    self._claim_daily()
                    return

            elif self.state == "lucky_spin":
                # Close X button
                if math.hypot(mx - (SW - 32), my - 28) < 16:
                    if not self.spin_active and not self.reveal_active:
                        self.state = "title"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                        return

                
                # Close reveal popup click
                if self.reveal_active:
                    if self.reveal_timer >= 60:
                        self.close_reveal()
                    return
                
                # Spin button click
                if not self.spin_active and not self.reveal_active:
                    if pygame.Rect(760, 240, 480, 68).collidepoint(mx, my):
                        self.start_lucky_spin()
                        return

            elif self.state == "pvp_menu":
                for i, opt in enumerate(self.pvp_menu_options):
                    bw, bh = 400, 60
                    bx = SW // 2 - bw // 2
                    by = 160 + i * 80
                    if pygame.Rect(bx, by, bw, bh).collidepoint(mx, my):
                        self.pvp_menu_sel = i
                        sel = self.pvp_menu_options[i]
                        if sel == "TẠO PHÒNG (HOST)":
                            self.state = "pvp_prep"
                            self.pvp_prep_field = 0
                            self.pvp_prep_items = []
                        elif sel == "TÌM PHÒNG (JOIN)":
                            self.start_pvp_join()
                        else:
                            self.state = "title"
                        break

            # ── PVP Prep screen (redesigned) ──
            elif self.state == "pvp_prep":
                left_x, left_w = 30, 400
                right_x, right_w = 450, SW - 480
                top_y = 70

                # Back button
                if pygame.Rect(30, SH - 60, 160, 44).collidepoint(mx, my):
                    self.state = "pvp_menu"
                    return
                # Create room button
                if pygame.Rect(SW // 2 - 100, SH - 60, 400, 44).collidepoint(mx, my):
                    self.player_name = self.pvp_prep_name
                    self.start_pvp_host()
                    return

                # — LEFT COLUMN clicks —
                cy = top_y + 12
                # Name field click
                cy += 22  # skip label
                name_box = pygame.Rect(left_x + 15, cy, left_w - 30, 34)
                if name_box.collidepoint(mx, my):
                    self.pvp_name_editing = True
                    return
                else:
                    self.pvp_name_editing = False
                cy += 46

                # Mode toggles
                cy += 22  # skip label
                mode_bw = (left_w - 40) // 2
                fun_rect = pygame.Rect(left_x + 15, cy, mode_bw - 4, 36)
                bet_rect = pygame.Rect(left_x + 15 + mode_bw + 4, cy, mode_bw - 4, 36)
                if fun_rect.collidepoint(mx, my):
                    self.pvp_prep_bet_mode = 0
                    return
                if bet_rect.collidepoint(mx, my):
                    self.pvp_prep_bet_mode = 1
                    return
                cy += 44

                # Bet amount +/- (only if bet mode)
                if self.pvp_prep_bet_mode == 1:
                    cy += 22  # skip label
                    minus_rect = pygame.Rect(left_x + 15, cy, 60, 30)
                    plus_rect = pygame.Rect(left_x + 85, cy, 60, 30)
                    if minus_rect.collidepoint(mx, my):
                        self.pvp_prep_bet_amount = max(100, self.pvp_prep_bet_amount - 100)
                        return
                    if plus_rect.collidepoint(mx, my):
                        self.pvp_prep_bet_amount = min(self.money, self.pvp_prep_bet_amount + 100)
                        return
                    cy += 38
                else:
                    cy += 8

                # Map size buttons
                cy += 22  # skip label
                map_bw = (left_w - 50) // 3
                for mi in range(3):
                    mx_btn = left_x + 15 + mi * (map_bw + 5)
                    mr = pygame.Rect(mx_btn, cy, map_bw, 34)
                    if mr.collidepoint(mx, my):
                        self.pvp_prep_map_size = mi
                        return

                # — RIGHT COLUMN clicks —
                ry = top_y + 12 + 24  # skip label
                bp_items = list(self.backpack)
                cols_item = min(4, max(1, len(bp_items)))
                iw, ih = 70, 58
                for idx, item_kind in enumerate(bp_items[:12]):
                    col = idx % cols_item
                    row = idx // cols_item
                    ix = right_x + 15 + col * (iw + 8)
                    iy = ry + row * (ih + 6)
                    if pygame.Rect(ix, iy, iw, ih).collidepoint(mx, my):
                        if item_kind in self.pvp_prep_items:
                            self.pvp_prep_items.remove(item_kind)
                        elif len(self.pvp_prep_items) < 3:
                            self.pvp_prep_items.append(item_kind)
                        return
                ry += max(1, (len(bp_items[:12]) + cols_item - 1) // max(1, cols_item)) * (ih + 6) + 12

                # Pet buttons
                ry += 24  # skip label
                pets_list = ["(không)"] + self.owned_pets
                pw_btn, ph_btn = 90, 36
                for pi, pet_id in enumerate(pets_list):
                    col = pi % 3
                    row = pi // 3
                    px_btn = right_x + 15 + col * (pw_btn + 8)
                    py_btn = ry + row * (ph_btn + 6)
                    if pygame.Rect(px_btn, py_btn, pw_btn, ph_btn).collidepoint(mx, my):
                        self.pvp_prep_pet = pet_id if pet_id != "(không)" else None
                        return

            # ── PVP Waiting (host lobby) ──
            elif self.state == "pvp_waiting":
                btns = getattr(self, 'pvp_lobby_buttons', {})
                if btns.get('skin_left') and btns['skin_left'].collidepoint(mx, my):
                    try: snd_pickup.play()
                    except Exception: pass
                    self.pvp_skin_flash = 1.0
                    self.skin_idx = (self.skin_idx - 1) % len(self.skin_names)
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()
                elif btns.get('skin_right') and btns['skin_right'].collidepoint(mx, my):
                    try: snd_pickup.play()
                    except Exception: pass
                    self.pvp_skin_flash = 1.0
                    self.skin_idx = (self.skin_idx + 1) % len(self.skin_names)
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()
                elif btns.get('edit_name') and btns['edit_name'].collidepoint(mx, my):
                    try: snd_pickup.play()
                    except Exception: pass
                    self.pvp_prep_name = ""
                    self.pvp_lobby_view = self._pvp_lobby_snapshot()
                    self._pvp_send_lobby_to_all()
                # New lobby footer button rects (must match _draw_pvp_lobby_footer)
                back_rect = pygame.Rect(SW // 2 - 330, SH - 75, 260, 56)
                start_rect = pygame.Rect(SW // 2 + 70, SH - 75, 260, 56)
                if back_rect.collidepoint(mx, my):
                    # Refund bet if cancelling
                    if self.pvp_bet_active:
                        self.money += self.pvp_bet_amount_match
                        self.pvp_bet_active = False
                        self._save_game()
                    self._pvp_cleanup()
                    self.state = "pvp_menu"
                elif start_rect.collidepoint(mx, my):
                    if self._pvp_count_lobby_players() >= self.pvp_min_start:
                        self._pvp_host_start_match()
                    else:
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            f"CẦN ÍT NHẤT {self.pvp_min_start} NGƯỜI CHƠI!",
                            (255, 180, 80), center_bounce=True))

            # ── PVP Lobby (client waiting for host to start) ──
            elif self.state == "pvp_lobby":
                btns = getattr(self, 'pvp_lobby_buttons', {})
                if btns.get('skin_left') and btns['skin_left'].collidepoint(mx, my):
                    try: snd_pickup.play()
                    except Exception: pass
                    self.pvp_skin_flash = 1.0
                    self.skin_idx = (self.skin_idx - 1) % len(self.skin_names)
                    self.pvp_needs_join_resend = True
                    for s in self.pvp_lobby_view:
                        if s and s.get('slot', -1) == getattr(self, 'pvp_my_slot', -1):
                            s['skin'] = self.skin_idx
                elif btns.get('skin_right') and btns['skin_right'].collidepoint(mx, my):
                    try: snd_pickup.play()
                    except Exception: pass
                    self.pvp_skin_flash = 1.0
                    self.skin_idx = (self.skin_idx + 1) % len(self.skin_names)
                    self.pvp_needs_join_resend = True
                    for s in self.pvp_lobby_view:
                        if s and s.get('slot', -1) == getattr(self, 'pvp_my_slot', -1):
                            s['skin'] = self.skin_idx
                elif btns.get('edit_name') and btns['edit_name'].collidepoint(mx, my):
                    try: snd_pickup.play()
                    except Exception: pass
                    self.pvp_prep_name = ""
                    self.pvp_needs_join_resend = True
                    for s in self.pvp_lobby_view:
                        if s and s.get('slot', -1) == getattr(self, 'pvp_my_slot', -1):
                            s['name'] = self.pvp_prep_name
                back_rect = pygame.Rect(SW // 2 - 130, SH - 75, 260, 56)
                if back_rect.collidepoint(mx, my):
                    if self.pvp_socket and self.pvp_host_addr:
                        try:
                            leave_pkt = json.dumps({
                                'type': 'leave',
                                'name': self.pvp_prep_name,
                            }).encode('utf-8')
                            self.pvp_socket.sendto(leave_pkt, self.pvp_host_addr)
                        except Exception: pass
                    if self.pvp_bet_active:
                        self.money += self.pvp_bet_amount_match
                        self.pvp_bet_active = False
                        self._save_game()
                    self._pvp_cleanup()
                    self.state = "pvp_menu"

            # ── PVP Joining (room list) ──
            elif self.state == "pvp_joining":
                # Back button
                if pygame.Rect(SW // 2 - 80, SH - 50, 160, 40).collidepoint(mx, my):
                    self._pvp_cleanup()
                    self.state = "pvp_menu"
                    return
                if self.pvp_found_hosts:
                    for i, host_entry in enumerate(self.pvp_found_hosts):
                        bw, bh = 500, 55
                        bx = SW // 2 - bw // 2
                        by = 150 + i * 65
                        if pygame.Rect(bx, by, bw, bh).collidepoint(mx, my):
                            self.pvp_join_sel = i
                            room_info = host_entry[2] if len(host_entry) > 2 else {}
                            if room_info.get('mode') == 'bet':
                                bet = room_info.get('bet', 0)
                                if self.money < bet:
                                    floating_texts.append(FloatingText(SW // 2, SH // 2,
                                        "KHÔNG ĐỦ TIỀN!", (255, 80, 80), center_bounce=True))
                                    return
                            self.connect_pvp_host(host_entry)
                            break

            # ── PVP Playing (in-match) ──
            elif self.state == "pvp_playing":
                # Click on backpack items (bottom HUD)
                for i in range(min(3, len(self.pvp_local_items))):
                    ix = 10 + i * 45
                    iy = SH - 50
                    if pygame.Rect(ix, iy, 40, 40).collidepoint(mx, my):
                        self._pvp_use_backpack_item(i)
                        break
                # Click on chat buttons
                for i, chat_opt in enumerate(self.pvp_chat_options):
                    cx = SW - 120
                    cy = SH - 180 + i * 35
                    if pygame.Rect(cx, cy, 110, 30).collidepoint(mx, my):
                        self._pvp_send_chat(i)
                        break

            # ── PVP End (match results) ──
            elif self.state == "pvp_end":
                btn_w, btn_h = 200, 50
                rematch_rect = pygame.Rect(SW // 2 - btn_w - 20, SH - 90, btn_w, btn_h)
                exit_rect = pygame.Rect(SW // 2 + 20, SH - 90, btn_w, btn_h)
                if rematch_rect.collidepoint(mx, my):
                    self.pvp_end_sel = 0
                    self._pvp_request_rematch()
                elif exit_rect.collidepoint(mx, my):
                    self.pvp_end_sel = 1
                    self._pvp_broadcast_quit()
                    self._pvp_cleanup()
                    self.state = "pvp_menu"

            # ── Level Select (node map) ──
            elif self.state == "level_select":
                # When the world-map background image is loaded, route clicks
                # through the 20-tile grid + baked-in BACK / PLAY buttons.
                if getattr(self, 'level_select_bg', None):
                    for i, rect in enumerate(self._level_select_tile_rects()):
                        if rect.collidepoint(mx, my):
                            self.level_sel = i
                            break
                    if self._level_select_back_rect().collidepoint(mx, my):
                        self.state = "title"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                        return
                    if self._level_select_play_rect().collidepoint(mx, my):
                        chosen_level = self.level_sel + 1
                        if chosen_level in self.unlocked_levels:
                            def start():
                                self.score = 0; self.lives = 3
                                self.total_kills = 0; self.total_money_earned = 0
                                self.player_tier = self.skin_idx
                                self.start_level(chosen_level)
                                self.state = "level_start"
                                pygame.mixer.music.stop()
                            transition.start(start)
                    return
                # Back button
                if pygame.Rect(10, SH - 44, 140, 36).collidepoint(mx, my):
                    self.state = "title"
                    try: pygame.mixer.music.play(-1)
                    except Exception: pass
                    return
                # Click on level nodes
                if hasattr(self, '_level_nodes'):
                    cam_y = int(getattr(self, '_ls_cam_y', 0))
                    for i in range(self.max_levels):
                        nx, ny = self._level_nodes[i][0], self._level_nodes[i][1] - cam_y
                        if math.hypot(mx - nx, my - ny) < 24:
                            self.level_sel = i
                            break
                # Play button (bottom-right)
                pw, ph, bh_bar = 110, 36, 48
                px = SW - pw - 10
                py = SH - bh_bar + 6
                if pygame.Rect(px, py, pw, ph).collidepoint(mx, my):
                    chosen_level = self.level_sel + 1
                    if chosen_level in self.unlocked_levels:
                        def start():
                            self.score = 0; self.lives = 3
                            self.total_kills = 0; self.total_money_earned = 0
                            self.player_tier = self.skin_idx
                            self.start_level(chosen_level)
                            self.state = "level_start"
                            pygame.mixer.music.stop()
                        transition.start(start)

            # ── Level Start (click to begin) ──
            elif self.state == "level_start":
                self.state = "playing"

            # ── Pause menu ──
            elif self.state == "pause":
                for i, item_label in enumerate(self.pause_items):
                    txt_temp = FONT_MED.render(item_label, True, (255, 255, 255))
                    rect = txt_temp.get_rect(center=(SW // 2, SH // 2 - 60 + i * 45))
                    click_rect = pygame.Rect(rect.x - 20, rect.y - 7, rect.width + 40, rect.height + 14)
                    if click_rect.collidepoint(mx, my):
                        self.pause_sel = i
                        sel = self.pause_items[i]
                        if sel == "TIẾP TỤC": self.state = "playing"
                        elif sel == "CHƠI LẠI":
                            self.start_level(self.level)
                            pygame.mixer.music.stop()
                        elif sel == "VÀO SHOP":
                            self.state = "shop"
                            try: pygame.mixer.music.play(-1)
                            except Exception: pass
                        elif sel == "CÁCH CHƠI":
                            self.state = "tutorial"
                            self.tutorial_page = 0
                        elif sel == "VỀ SẢNH":
                            self.state = "title"
                            try: pygame.mixer.music.play(-1)
                            except Exception: pass
                        elif sel == "THOÁT GAME":
                            self._save_game(); pygame.quit(); sys.exit()
                        break

            # ── Gameover (click continue button) ──
            elif self.state == "gameover":
                cont_rect = pygame.Rect(SW // 2 - 120, SH // 2 + 90, 240, 44)
                if cont_rect.collidepoint(mx, my):
                    def go_shop():
                        self.state = "shop"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    transition.start(go_shop)

            # ── Level Clear (click continue button) ──
            elif self.state == "level_clear":
                cont_rect = pygame.Rect(SW // 2 - 120, SH // 2 + 90, 240, 44)
                if not cont_rect.collidepoint(mx, my):
                    cont_rect = pygame.Rect(SW // 2 - 120, SH // 2 + 100, 240, 44)
                if cont_rect.collidepoint(mx, my):
                    def go_shop():
                        self.state = "shop"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    transition.start(go_shop)

            # ── Tutorial ──
            elif self.state == "tutorial":
                prev_rect = pygame.Rect(SW // 2 - 250, SH - 48, 130, 36)
                next_rect = pygame.Rect(SW // 2 - 65, SH - 48, 130, 36)
                back_rect = pygame.Rect(SW // 2 + 120, SH - 48, 140, 36)
                if prev_rect.collidepoint(mx, my):
                    self.tutorial_page = max(0, self.tutorial_page - 1)
                elif next_rect.collidepoint(mx, my):
                    self.tutorial_page = min(3, self.tutorial_page + 1)
                elif back_rect.collidepoint(mx, my):
                    self.state = "pause"

            # ── Shop ──
            elif self.state == "shop":
                # X close button (top-right circle)
                if math.hypot(mx - (SW - 16), my - 24) < 14:
                    self.state = "title"
                    return
                # Category tabs
                top_h = 58
                tab_y = top_h + 12
                categories = ["VŨ KHÍ", "PHÒNG THỦ", "PET", "ĐẶC BIỆT", "GARA TANK"]
                tab_total_w = SW - 80
                tab_w = tab_total_w // len(categories)
                if not hasattr(self, '_shop_cat'):
                    self._shop_cat = 0
                for ci in range(len(categories)):
                    tx = 40 + ci * tab_w
                    if pygame.Rect(tx, tab_y, tab_w - 8, 38).collidepoint(mx, my):
                        if ci == 4:
                            self.state = "garage"
                            snd_pickup.play()
                        else:
                            self._shop_cat = ci
                            snd_pickup.play()
                        return
                # Continue button (bottom)
                pulse = abs(math.sin(self.tick * 0.08))
                msg = "[ ENTER ] TIẾP TỤC"
                instr = FONT_MED.render(msg, True, (255, 255, 255))
                bw_btn, bh_btn = instr.get_width() + 40, 34
                bx_btn = SW // 2 - bw_btn // 2
                by_btn = SH - bh_btn - 8
                if pygame.Rect(bx_btn, by_btn, bw_btn, bh_btn).collidepoint(mx, my):
                    self.handle_shop_events(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                    return
                # Item card clicks
                all_items = [
                    [("1", 500, "multi"), ("2", 800, "rapid"), ("3", 600, "pierce"),
                     ("4", 1200, "rocket"), ("5", 1000, "flame"), ("6", 900, "laser"),
                     ("7", 750, "plasma"), ("8", 1000, "star")],
                    [("1", 300, "shield"), ("2", 200, "health"), ("3", 1000, "life"),
                     ("4", 150, "speed")],
                    [("1", 2000, "pet_wolf"), ("2", 5000, "pet_dragon"), ("3", 3000, "pet_healer"),
                     ("4", 3500, "pet_shield_bot"), ("5", 1500, "pet_magnet"), ("6", 4000, "pet_ghost")],
                    [("1", 500, "gem10"), ("2", 2000, "gem50"), ("3", 1500, "unlock_slot")],
                ]
                cat = getattr(self, '_shop_cat', 0)
                items = all_items[cat]
                n = len(items)
                cols_n = min(4, n)
                margin_x = 16
                gap = 10
                card_w = (SW - margin_x * 2 - gap * (cols_n - 1)) // cols_n
                card_area_top = tab_y + 38
                card_area_bot = SH - 60
                rows_n = (n + cols_n - 1) // cols_n
                total_card_h = card_area_bot - card_area_top - gap * (rows_n - 1)
                card_h = min(total_card_h // max(1, rows_n), 280)
                for i, (key, cost, kind) in enumerate(items):
                    col = i % cols_n
                    row = i // cols_n
                    cx = margin_x + col * (card_w + gap)
                    cy_card = card_area_top + row * (card_h + gap)
                    if pygame.Rect(cx, cy_card, card_w, card_h).collidepoint(mx, my):
                        fake_ev = pygame.event.Event(pygame.KEYDOWN, key=getattr(pygame, f'K_{key}'))
                        self.handle_shop_events(fake_ev)
                        return

            # ── Garage ──
            elif self.state == "garage":
                # Back button (at bottom-left: x=40, y=SH-85, w=180, h=48)
                if pygame.Rect(40, SH - 85, 180, 48).collidepoint(mx, my):
                    self.state = "title"
                    return
                # Action Buy/Select button
                if pygame.Rect(640, 570, 600, 54).collidepoint(mx, my):
                    fake_ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                    self.handle_event(fake_ev)
                    return
                # Tank card clicks (stack of 5 elegant card rows on the right side)
                n = len(self.skin_names)
                card_x = 640
                card_h = 80
                start_y = 90
                gap = 14
                for i in range(n):
                    cy_card = start_y + i * (card_h + gap)
                    if pygame.Rect(card_x, cy_card, 600, card_h).collidepoint(mx, my):
                        self.skin_idx = i
                        snd_pickup.play()
                        break

            # ── Achievements ──
            elif self.state == "achievements":
                if pygame.Rect(SW // 2 - 80, SH - 50, 160, 40).collidepoint(mx, my):
                    self.state = "title"

    def update(self):
        self.tick += 1
        transition.update()
        weather.update()

        # Control system cursor visibility & mouse grab dynamically to prevent escaping during gameplay
        is_gameplay = self.state in ("playing", "coop_playing", "pvp_playing")
        if is_gameplay:
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
        else:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)

        # Achievement animation
        for ach in achievement_queue[:]:
            ach.timer -= 1
            ach.y_offset = min(10, ach.y_offset + 4)
            if ach.timer <= 0:
                achievement_queue.remove(ach)

        if self.tick % 10 == 0:
            self.water_frame = (self.water_frame + 1) % len(sprites.water_frames)

        # Title tank animation
        if self.state == "title":
            for t in self.title_tanks:
                ddx, ddy = DIRS[t['dir']]
                t['x'] += ddx * t['speed']
                t['y'] += ddy * t['speed']
                if t['x'] < -40 or t['x'] > SW + 40 or t['y'] < -40 or t['y'] > SH + 40:
                    t['dir'] = random.randint(0, 3)
                    if t['dir'] == 0: t['y'] = SH + 30
                    elif t['dir'] == 1: t['x'] = -30
                    elif t['dir'] == 2: t['y'] = -30
                    elif t['dir'] == 3: t['x'] = SW + 30

        if self.state in ("pvp_menu", "pvp_prep", "pvp_waiting", "pvp_joining", "pvp_lobby", "pvp_playing", "pvp_end"):
            self.update_pvp()
            # Camera follow in pvp_playing
            if self.state == "pvp_playing" and self.player:
                self.cam_zoom += (self.target_zoom - self.cam_zoom) * 0.1
                tcx = self.player.x - (SW / self.cam_zoom) / 2
                tcy = self.player.y - (SH / self.cam_zoom) / 2
                self.cam_x += (tcx - self.cam_x) * 0.15
                self.cam_y += (tcy - self.cam_y) * 0.15
                map_w, map_h = COLS * TS, ROWS * TS
                vw = SW / self.cam_zoom
                vh = SH / self.cam_zoom
                self.cam_x = max(0, min(self.cam_x, map_w - vw))
                self.cam_y = max(0, min(self.cam_y, map_h - vh))
            return

        # ── CO-OP update loop ──
        if self.state in ("coop_menu", "coop_waiting", "coop_joining", "coop_lobby", "coop_playing"):
            if self.coop_active:
                if self.coop_is_host:
                    self._coop_process_host_packets()
                    if self.state == "coop_playing" and time.time() - self.coop_last_sync > 0.05:
                        self._coop_send_state_to_clients()
                        self.coop_last_sync = time.time()
                else:
                    self._coop_process_client_packets()
                    if self.state == "coop_playing" and time.time() - self.coop_last_sync > 0.05:
                        self._coop_send_client_input()
                        self.coop_last_sync = time.time()
            if self.state != "coop_playing":
                return
            # In coop_playing, fall through to normal playing logic

        if self.state not in ("playing", "coop_playing"): return

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0: self.combo = 0
        if self.mission_timer > 0: self.mission_timer -= 1

        # Camera — zoomed in, player always centered
        self.cam_zoom += (self.target_zoom - self.cam_zoom) * 0.1
        target_cam_x = self.player.x - (SW / self.cam_zoom) / 2
        target_cam_y = self.player.y - (SH / self.cam_zoom) / 2
        self.cam_x += (target_cam_x - self.cam_x) * 0.15
        self.cam_y += (target_cam_y - self.cam_y) * 0.15
        map_w, map_h = COLS * TS, ROWS * TS
        view_w = SW / self.cam_zoom
        view_h = SH / self.cam_zoom
        self.cam_x = max(0, min(self.cam_x, map_w - view_w))
        self.cam_y = max(0, min(self.cam_y, map_h - view_h))

        # Player input
        keys = pygame.key.get_pressed()
        self.player.update()

        if self.player.alive and self.player.spawn_timer <= 0:
            if self.auto_mode:
                self.auto_play()
            else:
                # Respect user keybinds (with arrow keys as a fallback)
                kb = self.keybinds
                kb_up    = kb.get("up")    or pygame.K_w
                kb_down  = kb.get("down")  or pygame.K_s
                kb_left  = kb.get("left")  or pygame.K_a
                kb_right = kb.get("right") or pygame.K_d
                kb_shoot = kb.get("shoot") or pygame.K_SPACE
                kb_sprint = kb.get("special") or pygame.K_LSHIFT
                mdx, mdy = 0, 0
                if keys[pygame.K_UP] or keys[kb_up]: mdy -= 1
                if keys[pygame.K_DOWN] or keys[kb_down]: mdy += 1
                if keys[pygame.K_LEFT] or keys[kb_left]: mdx -= 1
                if keys[pygame.K_RIGHT] or keys[kb_right]: mdx += 1

                is_moving = mdx != 0 or mdy != 0
                if is_moving and (keys[kb_sprint] or keys[pygame.K_RSHIFT]) and self.player.energy > 0:
                    self.player.sprint_multiplier = 1.8
                    self.player.energy = max(0, self.player.energy - 0.5)
                else:
                    self.player.sprint_multiplier = 1.0
                    if self.player.energy < self.player.max_energy:
                        self.player.energy = min(self.player.max_energy, self.player.energy + 0.15)

                if is_moving:
                    mag = math.hypot(mdx, mdy)
                    spd = self.player.speed * self.player.sprint_multiplier
                    self.player.move(mdx / mag * spd, mdy / mag * spd, self.grid, self.enemies)

                # Update player direction based on mouse aiming
                mx_phys, my_phys = pygame.mouse.get_pos()
                mx_logical = mx_phys * (SW / phys_w)
                my_logical = my_phys * (SH / phys_h)
                
                cam_x = getattr(self, 'cam_x', 0)
                cam_y = getattr(self, 'cam_y', 0)
                cam_zoom = getattr(self, 'cam_zoom', 1.0)
                mx_map = cam_x + mx_logical / cam_zoom
                my_map = cam_y + my_logical / cam_zoom
                
                pdx = mx_map - self.player.x
                pdy = my_map - self.player.y
                if pdx != 0 or pdy != 0:
                    if abs(pdx) > abs(pdy):
                        self.player.dir = 1 if pdx > 0 else 3
                    else:
                        self.player.dir = 0 if pdy < 0 else 2

                if keys[kb_shoot] or keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:
                    target_angle = math.atan2(my_map - self.player.y, mx_map - self.player.x)
                    new_bullets = self.player.shoot(target_angle)
                    if new_bullets: self.bullets.extend(new_bullets)

        # Enemy AI
        for enemy in self.enemies:
            enemy.update()
            new_bullets = enemy.update_ai(self.grid, self.player, self.enemies + [self.player], self.cam_x, self.cam_y, self.cam_zoom)
            if new_bullets:
                if new_bullets == "boss_summon":
                    # Boss summoned minions — spawn extra enemies
                    for _ in range(2):
                        avail = [sp for sp in self.spawn_points if not any(
                            e.alive and e.get_grid() == sp for e in self.enemies)]
                        if avail:
                            sp = random.choice(avail)
                            diff = min(0.4 + self.level * 0.1, 2.5)
                            minion = EnemyTank(sp[0], sp[1], "enemy_b", diff)
                            self.enemies.append(minion)
                            spawn_particles(sp[0] * TS + TS // 2, sp[1] * TS + TS // 2, (100, 255, 50), 15)
                            floating_texts.append(FloatingText(sp[0] * TS, sp[1] * TS, "TRIỆU HỒI!", (100, 255, 50)))
                elif isinstance(new_bullets, list): self.bullets.extend(new_bullets)
                else: self.bullets.append(new_bullets)

        # Pet update
        if self.pet and self.pet.alive:
            pet_bullets = self.pet.update(self.enemies, self.items, self)
            if pet_bullets:
                self.bullets.extend(pet_bullets)

        # Soft separation
        all_tanks = [self.player] + [e for e in self.enemies if e.alive]
        for i in range(len(all_tanks)):
            for j in range(i + 1, len(all_tanks)):
                t1, t2 = all_tanks[i], all_tanks[j]
                if t1.alive and t2.alive:
                    ddx = t1.x - t2.x; ddy = t1.y - t2.y
                    dist = math.hypot(ddx, ddy)
                    if 0 < dist < TS - 5:
                        push_force = (TS - 5 - dist) * 0.05
                        px, py = ddx / dist * push_force, ddy / dist * push_force
                        if t1.can_move_to(t1.x + px, t1.y + py, self.grid):
                            t1.x += px; t1.y += py
                        if t2.can_move_to(t2.x - px, t2.y - py, self.grid):
                            t2.x -= px; t2.y -= py

        # NPC updates
        for c in self.chickens: c.update(self.grid)
        for d in self.dogs:
            d.update(self.grid, (self.player.x, self.player.y))
            if d.alive and self.player.alive and d.bite_cooldown <= 0:
                if math.hypot(d.x - self.player.x, d.y - self.player.y) < 25:
                    killed = self.player.hit(1)
                    d.alive = False
                    spawn_particles(d.x, d.y, (150, 100, 50), 10)
                    self.shake_amount = 10
                    floating_texts.append(FloatingText(self.player.x, self.player.y, "CHÓ CẮN!", (255, 50, 50)))
                    if killed:
                        self.explosions.append(Explosion(self.player.x, self.player.y, big=True))
                        snd_explode.play()
                        self.shake_amount = 15
                        self.lives -= 1
                        if self.lives <= 0:
                            if self.state != "pvp_playing":
                                self.state = "gameover"; self.won_level = False
                        else:
                            self._respawn_player()

        # Spawn timer
        self.spawn_timer += 1
        alive_count = sum(1 for e in self.enemies if e.alive and e.spawn_timer <= 0)
        if self.spawn_timer >= 70 and alive_count < self.max_alive and self.enemies_to_spawn > 0:
            self.spawn_enemy(); self.spawn_timer = 0

        # Bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.alive:
                self.bullets.remove(bullet); continue

            gx, gy = bullet.get_grid()
            if 0 <= gx < COLS and 0 <= gy < ROWS:
                tile = self.grid[gy][gx]
                if tile in (BRICK, STEEL, BASE, CRATE):
                    if tile in (BRICK, CRATE):
                        self.grid[gy][gx] = EMPTY
                        spawn_particles(gx * TS + TS // 2, gy * TS + TS // 2, (150, 100, 50), 8)
                        if tile == CRATE or random.random() < 0.1:
                            item_kinds = ["health", "shield", "speed", "star", "rapid", "multi",
                                          "pierce", "bomb", "freeze", "grenade", "max_power",
                                          "rocket", "flame"]
                            # Sprinkle a rare gem drop (~6%) for kawaii currency
                            if random.random() < 0.06:
                                item_kinds = item_kinds + ["gem"]
                            self.items.append(Item(gx, gy, random.choice(item_kinds)))
                    if bullet.kind != "pierce":
                        bullet.alive = False
                        self.explosions.append(Explosion(int(bullet.x), int(bullet.y)))
                        if tile == STEEL: snd_steel.play()
                        if tile == BASE:
                            # Base is completely invulnerable to all bullets (no more gameover!)
                            continue
                        continue

            # Hit player
            if bullet.owner != "player" and self.player.alive:
                if abs(bullet.x - self.player.x) < 15 and abs(bullet.y - self.player.y) < 15:
                    killed = self.player.hit(bullet.power)
                    bullet.alive = False
                    self.explosions.append(Explosion(int(bullet.x), int(bullet.y)))
                    if killed:
                        self.explosions.append(Explosion(self.player.x, self.player.y, big=True))
                        snd_explode.play(); self.shake_amount = 12
                        self.lives -= 1
                        if self.lives <= 0:
                            if self.state != "pvp_playing":
                                self.state = "gameover"; self.won_level = False
                        else:
                            self._respawn_player()
                    continue

            if bullet.owner == "player":
                for c in self.chickens:
                    if c.alive and abs(bullet.x - c.x) < 15 and abs(bullet.y - c.y) < 15:
                        c.alive = False; bullet.alive = False
                        self.explosions.append(Explosion(c.x, c.y))
                        val = random.choice([50, 100, 200])
                        self.register_kill(c.x, c.y, val)
                        spawn_particles(c.x, c.y, (255, 255, 100), 12)
                        floating_texts.append(FloatingText(c.x, c.y, f"+{val}đ", (255, 215, 0)))

                for d in self.dogs:
                    if d.alive and abs(bullet.x - d.x) < 18 and abs(bullet.y - d.y) < 18:
                        d.alive = False; bullet.alive = False
                        self.register_kill(d.x, d.y, 150)
                        self.explosions.append(Explosion(d.x, d.y))
                        spawn_particles(d.x, d.y, (150, 100, 50), 15)
                        floating_texts.append(FloatingText(d.x, d.y, "HẠ CHÓ!", (255, 150, 50)))

                for enemy in self.enemies:
                    if enemy.alive and abs(bullet.x - enemy.x) < 12 and abs(bullet.y - enemy.y) < 12:
                        killed = enemy.hit(bullet.power)
                        bullet.alive = False if bullet.kind != "pierce" else True
                        if killed:
                            self.kills += 1
                            base_score = 100
                            if enemy.tank_type == "elite": base_score = 300
                            elif enemy.tank_type == "boss":
                                base_score = 2000 if isinstance(enemy, BossTank) else 1000
                                self.stats["bosses_killed"] += 1
                                boss_name = getattr(enemy, 'boss_name', 'Boss')
                                trigger_achievement(f"HẠ {boss_name}!", f"Hạ gục {boss_name} màn {self.level}!", (255, 100, 50))
                                self.active_boss = None
                            self.register_kill(enemy.x, enemy.y, base_score)
                            self.explosions.append(Explosion(enemy.x, enemy.y, big=True))
                            spawn_particles(enemy.x, enemy.y, (255, 150, 50), 20 if isinstance(enemy, BossTank) else 15)
                            # Gem drop from killed enemies (~10%, boss always)
                            gem_chance = 1.0 if enemy.tank_type == "boss" else (0.2 if enemy.tank_type == "elite" else 0.10)
                            if random.random() < gem_chance:
                                self.items.append(Item(enemy.x // TS, enemy.y // TS, "gem"))

        self.enemies = [e for e in self.enemies if e.alive or e.spawn_timer > 0]
        self.chickens = [c for c in self.chickens if c.alive]
        self.dogs = [d for d in self.dogs if d.alive]

        for exp in self.explosions[:]:
            exp.update()
            if exp.done: self.explosions.remove(exp)

        # Item pickup
        for item in self.items[:]:
            item.update()
            if not item.alive: self.items.remove(item); continue
            if abs(self.player.x - item.x) < 20 and abs(self.player.y - item.y) < 20:
                snd_pickup.play()
                if item.kind == "money":
                    gain = random.randint(50, 150)
                    self.money += gain; self.total_money_earned += gain
                    floating_texts.append(FloatingText(self.player.x, self.player.y, f"+{gain}đ", (255, 215, 0)))
                elif item.kind == "gem":
                    gain = random.randint(2, 5)
                    self.gems += gain
                    floating_texts.append(FloatingText(self.player.x,
                        self.player.y, f"+{gain} ĐÁ QUÝ", (140, 220, 255)))
                else:
                    self.apply_item_ultra(item.kind)
                self.items.remove(item)

        # Level clear
        if self.kills >= self.total_enemies and self.enemies_to_spawn <= 0:
            self.won_level = True
            if self.state == "coop_playing" and self.coop_active and self.coop_is_host:
                # Auto-advance in co-op
                self.coop_level += 1
                pkt = json.dumps({"type": "coop_level_complete", "next_level": self.coop_level}).encode('utf-8')
                for c in self.coop_clients:
                    try: self.coop_socket.sendto(pkt, c["addr"])
                    except Exception: pass
                self.start_level(self.coop_level)
                continue_coop = True
            else:
                continue_coop = False
            if not continue_coop:
                self.state = "level_clear"
            self.stats["levels_completed"] += 1
            # Unlock next level
            next_lvl = self.level + 1
            if next_lvl <= self.max_levels:
                self.unlocked_levels.add(next_lvl)
            # Gem reward for clearing level
            gem_reward = 1 + self.level // 5
            self.gems += gem_reward
            floating_texts.append(FloatingText(self.player.x, self.player.y,
                f"+{gem_reward} ĐÁ QUÝ", (140, 220, 255)))
            snd_levelup.play()
            self._save_game()

        # Random items
        if self.tick % 480 == 0:
            for _ in range(10):
                rx, ry = random.randint(1, COLS - 2), random.randint(1, ROWS - 2)
                if self.grid[ry][rx] == EMPTY:
                    kind = random.choice(["health", "shield", "speed", "star", "life",
                                          "rapid", "multi", "pierce", "bomb",
                                          "freeze", "grenade", "max_power"])
                    self.items.append(Item(rx, ry, kind)); break

    def _respawn_player(self):
        ox, oy = self.player.x, self.player.y
        rx, ry = COLS // 2 - 2, ROWS - 2
        for _ in range(20):
            tx, ty = random.randint(1, COLS - 2), random.randint(1, ROWS - 2)
            if self.grid[ty][tx] == EMPTY: rx, ry = tx, ty; break
        self.player = Tank(rx, ry, "player")
        self.player.tier = self.player_tier
        self.player.name = self.player_name
        # Reassign pet to follow new player
        if self.pet and self.pet.alive:
            self.pet.owner = self.player
            self.pet.x = float(self.player.x - 20)
            self.pet.y = float(self.player.y - 20)
        spawn_particles(ox, oy, (255, 50, 50), 20)
        floating_texts.append(FloatingText(ox, oy, "HỒI SINH!", (255, 255, 255)))

    def apply_item_ultra(self, kind):
        if kind == "health":
            self.player.hp = min(self.player.max_hp, self.player.hp + 1)
            floating_texts.append(FloatingText(self.player.x, self.player.y, "+1 MÁU", (80, 255, 80)))
        elif kind == "life":
            self.lives += 1
            if self.player and self.player.alive:
                floating_texts.append(FloatingText(self.player.x, self.player.y, "+1 MẠNG!", (255, 50, 150)))
            else:
                floating_texts.append(FloatingText(SW // 2, SH // 2, "+1 MẠNG!", (255, 50, 150), center_bounce=True))
        elif kind == "shield":
            self.player.shield += 3
            floating_texts.append(FloatingText(self.player.x, self.player.y, "GIÁP +!", (80, 150, 255)))
        elif kind == "speed":
            self.player.energy = self.player.max_energy
            floating_texts.append(FloatingText(self.player.x, self.player.y, "NẠP NĂNG LƯỢNG", (80, 255, 130)))
        elif kind == "rapid":
            self.player.skill = "rapid"; self.player.skill_ammo = 40
            floating_texts.append(FloatingText(self.player.x, self.player.y, "BẮN SIÊU TỐC!", (255, 100, 50)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "multi":
            self.player.skill = "ammo"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "BẮN ĐA HƯỚNG!", (255, 200, 50)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "pierce":
            self.player.skill = "pierce"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "ĐẠN XUYÊN PHÁ!", (80, 200, 255)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "bomb":
            self.player.skill = "bomb"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "ĐẠN NỔ!", (255, 100, 50)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "laser":
            self.player.skill = "laser"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "TIA LASER!", (0, 255, 180)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "plasma":
            self.player.skill = "plasma"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "ĐẠN PLASMA!", (200, 50, 255)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "rocket":
            self.player.skill = "rocket"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "TÊN LỬA!", (255, 80, 30)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "flame":
            self.player.skill = "flame"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "PHUN LỬA!", (255, 150, 0)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "star":
            floating_texts.append(FloatingText(self.player.x, self.player.y, "BÙM BÙM!!!", (255, 50, 50), huge=True))
            # Only destroy enemies visible in player's camera viewport
            view_w = SW / self.cam_zoom
            view_h = SH / self.cam_zoom
            for e in self.enemies:
                if e.alive and e.spawn_timer <= 0:
                    # Check if enemy is within camera viewport
                    in_view = (e.x + TS > self.cam_x and e.x < self.cam_x + view_w and
                               e.y + TS > self.cam_y and e.y < self.cam_y + view_h)
                    if in_view:
                        killed = e.hit(10)
                        if killed:
                            self.kills += 1
                            self.register_kill(e.x, e.y, 100)
                            self.explosions.append(Explosion(e.x, e.y, big=True))
            self.shake_amount = 25
        elif kind == "freeze":
            # Freeze every alive enemy for ~5s (300 ticks at 60 FPS)
            self.freeze_uses += 1
            for e in self.enemies:
                if e.alive and e.spawn_timer <= 0:
                    e.frozen_timer = 300
            for d in self.dogs:
                if d.alive:
                    d.frozen_timer = 300
            floating_texts.append(FloatingText(self.player.x, self.player.y, "ĐÓNG BĂNG!", (120, 220, 255), huge=True))
            self.shake_amount = 6
        elif kind == "max_power":
            # Instantly upgrade tank to max tier
            self.player.tier = 4
            self.player.max_hp = max(self.player.max_hp, 8)
            self.player.hp = self.player.max_hp
            self.player.shield += 3
            self.player.bullet_power = 3
            self.player.shoot_delay = 8
            self.player.skill = "pierce"
            self.player.skill_timer = 900
            floating_texts.append(FloatingText(self.player.x, self.player.y, "SỨC MẠNH TỐI ĐA!", (255, 200, 60), huge=True))
            self.shake_amount = 10
        elif kind == "grenade":
            # AOE explosion centered on player; damages enemies within radius
            self.grenade_uses += 1
            radius = TS * 4
            for e in self.enemies:
                if e.alive and e.spawn_timer <= 0:
                    if math.hypot(e.x - self.player.x, e.y - self.player.y) <= radius:
                        killed = e.hit(4)
                        if killed:
                            self.kills += 1
                            self.register_kill(e.x, e.y, 100)
                            self.explosions.append(Explosion(e.x, e.y, big=True))
            for d in self.dogs:
                if d.alive and math.hypot(d.x - self.player.x, d.y - self.player.y) <= radius:
                    d.alive = False
                    self.register_kill(d.x, d.y, 150)
                    self.explosions.append(Explosion(d.x, d.y))
            for c in self.chickens:
                if c.alive and math.hypot(c.x - self.player.x, c.y - self.player.y) <= radius:
                    c.alive = False
                    self.register_kill(c.x, c.y, 50)
            # Burst of explosions for visual feedback
            for _ in range(6):
                ang = random.uniform(0, math.tau)
                rr = random.uniform(0, radius)
                ex = self.player.x + math.cos(ang) * rr
                ey = self.player.y + math.sin(ang) * rr
                self.explosions.append(Explosion(int(ex), int(ey), big=True))
            spawn_particles(self.player.x, self.player.y, (255, 180, 60), 30)
            floating_texts.append(FloatingText(self.player.x, self.player.y, "LỰU ĐẠN!", (90, 220, 90), huge=True))
            self.shake_amount = 18
            snd_explode.play()

        # Persist tier across levels
        self.player_tier = self.player.tier
        self._check_achievements()

    # ═══════════════════════════════════
    # LUCKY SPIN (VÒNG QUAY MAY MẮN)
    # ═══════════════════════════════════
    def start_lucky_spin(self):
        if self.gems < self.spin_cost:
            snd_deny.play()
            floating_texts.append(FloatingText(SW // 2, SH // 2,
                "BẠN KHÔNG ĐỦ KIM CƯƠNG!", (255, 80, 80), center_bounce=True))
            return
        
        self.gems -= self.spin_cost
        snd_buy.play()
        
        r_val = random.random()
        if r_val < 0.15:
            self.target_sector = 0
        elif r_val < 0.20:
            self.target_sector = 1
        elif r_val < 0.23:
            self.target_sector = 2
        elif r_val < 0.25:
            self.target_sector = 3
        else:
            self.target_sector = random.choice([4, 5, 6, 7])
            
        self.spin_active = True
        self.spin_timer = 0
        self.spin_start_angle = self.spin_angle % 360
        target_offset = 247.5 - self.target_sector * 45
        self.spin_target_angle = 360 * 6 + target_offset
        self.reveal_active = False

    def close_reveal(self):
        self.reveal_active = False
        if self.target_sector == 0:
            self.money += 5000
            self.lucky_spin_logs.append("Trung +5,000 Vang! o")
            floating_texts.append(FloatingText(SW // 2, SH // 2, "+5,000 VANG!", (255, 215, 0), huge=True))
        elif self.target_sector == 1:
            self.money += 10000
            self.lucky_spin_logs.append("Trung +10,000 Vang! o")
            floating_texts.append(FloatingText(SW // 2, SH // 2, "+10,000 VANG!", (255, 215, 0), huge=True))
        elif self.target_sector == 2:
            self.unlocked_skins.add(1)
            self.lucky_spin_logs.append("Trung XE TANG SAKURA! o")
            floating_texts.append(FloatingText(SW // 2, SH // 2, "SAKURA TANK UNLOCKED!", (255, 120, 180), huge=True))
        elif self.target_sector == 3:
            if "wolf" not in self.owned_pets:
                self.owned_pets.append("wolf")
                self.lucky_spin_logs.append("Trung PET SOI CHIEN! o")
                floating_texts.append(FloatingText(SW // 2, SH // 2, "PET SOI CHIEN UNLOCKED!", (140, 160, 255), huge=True))
            else:
                self.money += 3000
                self.lucky_spin_logs.append("Co Soi Chien -> +3,000 Vang! o")
                floating_texts.append(FloatingText(SW // 2, SH // 2, "+3,000 VANG BU!", (255, 215, 0), huge=True))
        else:
            self.lucky_spin_logs.append("Khong trung gi (Ruong rong). o")
            
        if len(self.lucky_spin_logs) > 6:
            self.lucky_spin_logs.pop(0)
            
        self._save_game()

    def draw_lucky_spin(self):
        s = self._surf
        tick = self.tick
        _mx_phys, _my_phys = pygame.mouse.get_pos()
        mx = int(_mx_phys * (SW / phys_w))
        my = int(_my_phys * (SH / phys_h))

        # Update spin physics
        if self.spin_active:
            t = self.spin_timer
            duration = 180.0
            if t < duration:
                progress = t / duration
                ease = 1.0 - (1.0 - progress) ** 3
                self.spin_angle = self.spin_start_angle + (self.spin_target_angle - self.spin_start_angle) * ease
                self.spin_timer += 1
                
                # Boundary ticker tick sound!
                boundary = 45
                prev_angle = self.spin_start_angle + (self.spin_target_angle - self.spin_start_angle) * (1.0 - (1.0 - (t-1)/duration)**3)
                if int(prev_angle / boundary) != int(self.spin_angle / boundary):
                    snd_pickup.play()
            else:
                self.spin_active = False
                self.spin_angle = self.spin_target_angle
                self.reveal_active = True
                self.reveal_timer = 0
                self.reveal_particles = []
        
        # ── BACKGROUND: Cyber Deep Space & Scrolling Neon Nebulas ──
        for y in range(SH):
            t = y / SH
            r = int(8 + 8 * t)
            g = int(4 + 5 * t)
            b = int(20 + 16 * t)
            pygame.draw.line(s, (r, g, b), (0, y), (SW, y))

        # Active glowing pulsing nebulas in backdrop (Blend Additive)
        for ci in range(4):
            cx_neb = int(320 + ci * 220 + math.sin(tick * 0.01 + ci * 1.5) * 50)
            cy_neb = int(280 + math.cos(tick * 0.009 + ci) * 40)
            neb_surf = pygame.Surface((380, 260), pygame.SRCALPHA)
            col = KAWAII_RAINBOW[ci % len(KAWAII_RAINBOW)]
            rad_val = int(110 + 25 * math.sin(tick * 0.018 + ci))
            pygame.draw.ellipse(neb_surf, (*col, 16), (190 - rad_val, 130 - rad_val // 2, rad_val * 2, rad_val))
            s.blit(neb_surf, (cx_neb - 190, cy_neb - 130), special_flags=pygame.BLEND_RGBA_ADD)

        # Perspective Neon Orange Grid
        grid_y = (tick * 1.6) % 40
        for gy in range(int(grid_y), SH, 40):
            pygame.draw.line(s, (255, 128, 0, 18), (0, gy), (SW, gy), 1)
        for gx in range(0, SW, 48):
            pygame.draw.line(s, (255, 128, 0, 18), (gx, 0), (gx, SH), 1)

        # ── TOP BAR: Futuristic Glassmorphic Panel ──
        top_h = 58
        top_bg = pygame.Surface((SW, top_h), pygame.SRCALPHA)
        top_bg.fill((12, 10, 24, 220))
        s.blit(top_bg, (0, 0))

        # Glowing title laser line
        for segment in range(SW // 12):
            col = (255, 120 + int(math.sin(tick * 0.18 + segment) * 60), 0)
            pygame.draw.rect(s, col, (segment * 12, top_h - 3, 12, 3))

        # Gems & Coins Capsules
        self._draw_currency_panel(s, SW - 270, 12)
        
        # Center title with drop glow
        title_str = "VÒNG QUAY MAY MẮN"
        title_t = FONT_BIG.render(title_str, True, (255, 255, 255))
        title_sh = FONT_BIG.render(title_str, True, (255, 128, 0))
        s.blit(title_sh, (SW // 2 - title_t.get_width() // 2 + 2, 11 + 2))
        s.blit(title_t, (SW // 2 - title_t.get_width() // 2, 11))

        # Close X Button
        close_x, close_y = SW - 32, 28
        pygame.draw.circle(s, (255, 45, 80, 210), (close_x, close_y), 16)
        pygame.draw.circle(s, (255, 255, 255), (close_x, close_y), 16, 2)
        pygame.draw.line(s, (255, 255, 255), (close_x - 7, close_y - 7), (close_x + 7, close_y + 7), 3)
        pygame.draw.line(s, (255, 255, 255), (close_x + 7, close_y - 7), (close_x - 7, close_y + 7), 3)

        # ── WHEEL DECK (Left Side) ──
        cx, cy = 400, 370
        wheel_R = 240

        # Outer pulsing ring (neon orange spectrum)
        pygame.draw.circle(s, (255, 128, 0, 35), (cx, cy), wheel_R + 12)
        pygame.draw.circle(s, (25, 20, 38), (cx, cy), wheel_R + 10)
        pygame.draw.circle(s, (255, 128, 0), (cx, cy), wheel_R + 10, width=4)
        pygame.draw.circle(s, (15, 10, 25), (cx, cy), wheel_R + 2)

        # Outer rivets
        for ri in range(24):
            rang = math.radians(ri * 15)
            rx = cx + (wheel_R + 6) * math.cos(rang)
            ry = cy + (wheel_R + 6) * math.sin(rang)
            pygame.draw.circle(s, (255, 215, 0), (int(rx), int(ry)), 4)
            pygame.draw.circle(s, (255, 255, 255), (int(rx), int(ry)), 2)

        # Draw the 3x Supersampled Wheel Canvas (Anti-Aliased)
        canvas_sz = 1440
        wheel_canvas = pygame.Surface((canvas_sz, canvas_sz), pygame.SRCALPHA)
        center_3x = canvas_sz // 2
        r_3x = 700

        sectors = [
            ("5,000 VÀNG", (255, 0, 128, 230), (255, 150, 200)),   # Neon Pink
            ("10,000 VÀNG", (0, 240, 255, 230), (180, 255, 255)),  # Neon Cyan
            ("SAKURA TANK", (255, 200, 0, 230), (255, 255, 150)),  # Neon Yellow
            ("SÓI CHIẾN", (150, 50, 255, 230), (220, 180, 255)),   # Neon Purple
            ("TẠCH", (255, 90, 0, 230), (255, 180, 100)),          # Neon Orange
            ("TẠCH", (50, 255, 100, 230), (180, 255, 200)),         # Neon Green
            ("TẠCH", (30, 100, 255, 230), (150, 200, 255)),        # Neon Blue
            ("TẠCH", (255, 30, 70, 230), (255, 150, 150))          # Neon Red
        ]

        def draw_premium_gift_box(surf, cx, cy, scale=1.0, opened=False, lid_offset_y=0, lid_rot_angle=0):
            # Box body size
            w = int(90 * scale)
            h = int(72 * scale)
            x = cx - w // 2
            y = cy - h // 3
            
            # Ribbon colors
            ribbon_color = (255, 215, 0) # Gold
            box_color = (200, 20, 80) # Dazzling Cherry Red
            box_shade = (140, 10, 50)
            
            if opened:
                # Opened chest base (cracked/shattered open)
                pygame.draw.rect(surf, box_color, (x, y, w, h), border_radius=int(6 * scale))
                pygame.draw.rect(surf, ribbon_color, (cx - int(10 * scale), y, int(20 * scale), h))
                pygame.draw.rect(surf, (20, 10, 30), (x + int(8 * scale), y + int(4 * scale), w - int(16 * scale), int(12 * scale)), border_radius=int(2 * scale))
            else:
                # Closed box body
                pygame.draw.rect(surf, box_color, (x, y, w, h), border_radius=int(6 * scale))
                # Left side shading
                pygame.draw.rect(surf, box_shade, (x, y, w // 2, h), border_radius=int(6 * scale))
                
                # Draw vertical ribbon
                pygame.draw.rect(surf, ribbon_color, (cx - int(10 * scale), y, int(20 * scale), h))
                # Draw horizontal ribbon
                pygame.draw.rect(surf, ribbon_color, (x, y + h // 2 - int(8 * scale), w, int(16 * scale)))
                
                # Border
                pygame.draw.rect(surf, (255, 255, 255), (x, y, w, h), int(2 * scale), border_radius=int(6 * scale))
                
                # Draw the Lid
                lid_w = int(100 * scale)
                lid_h = int(24 * scale)
                lid_x = cx - lid_w // 2
                lid_y = y - lid_h + int(4 * scale) + lid_offset_y
                
                # Lid surface to support rotation if detached
                lid_surf = pygame.Surface((int(200 * scale), int(200 * scale)), pygame.SRCALPHA)
                lcx, lcy = int(100 * scale), int(100 * scale)
                
                # Draw lid on temporary surface
                pygame.draw.rect(lid_surf, (230, 30, 100), (lcx - lid_w // 2, lcy - lid_h, lid_w, lid_h), border_radius=int(4 * scale))
                pygame.draw.rect(lid_surf, ribbon_color, (lcx - int(10 * scale), lcy - lid_h, int(20 * scale), lid_h))
                pygame.draw.rect(lid_surf, (255, 255, 255), (lcx - lid_w // 2, lcy - lid_h, lid_w, lid_h), int(2 * scale), border_radius=int(4 * scale))
                
                # Draw Bow on top of lid
                # Left loop
                pygame.draw.ellipse(lid_surf, ribbon_color, (lcx - int(28 * scale), lcy - lid_h - int(15 * scale), int(24 * scale), int(16 * scale)), int(3 * scale))
                pygame.draw.ellipse(lid_surf, (255, 255, 200), (lcx - int(24 * scale), lcy - lid_h - int(13 * scale), int(16 * scale), int(12 * scale)))
                # Right loop
                pygame.draw.ellipse(lid_surf, ribbon_color, (lcx + int(4 * scale), lcy - lid_h - int(15 * scale), int(24 * scale), int(16 * scale)), int(3 * scale))
                pygame.draw.ellipse(lid_surf, (255, 255, 200), (lcx + int(8 * scale), lcy - lid_h - int(13 * scale), int(16 * scale), int(12 * scale)))
                # Bow center knot
                pygame.draw.circle(lid_surf, (255, 255, 255), (lcx, lcy - lid_h - int(7 * scale)), int(7 * scale))
                pygame.draw.circle(lid_surf, ribbon_color, (lcx, lcy - lid_h - int(7 * scale)), int(7 * scale), int(2 * scale))
                
                # Rotate/draw lid
                if lid_rot_angle != 0:
                    rot_lid = pygame.transform.rotate(lid_surf, lid_rot_angle)
                    surf.blit(rot_lid, (int(cx - rot_lid.get_width() // 2), int(y - lid_h // 2 + lid_offset_y - rot_lid.get_height() // 2)))
                else:
                    surf.blit(lid_surf, (int(cx - 100 * scale), int(y - 100 * scale + lid_offset_y)))

        for i, (label, fill_c, border_c) in enumerate(sectors):
            pts = [(center_3x, center_3x)]
            for deg in range(i * 45, i * 45 + 46):
                rad = math.radians(deg)
                x = center_3x + r_3x * math.cos(rad)
                y = center_3x + r_3x * math.sin(rad)
                pts.append((x, y))
            pygame.draw.polygon(wheel_canvas, fill_c, pts)
            pygame.draw.polygon(wheel_canvas, border_c, pts, width=6)

            # Draw gorgeous mystery gift box aligned facing outward
            sa = math.radians(i * 45 + 22.5)
            lx = center_3x + 460 * math.cos(sa)
            ly = center_3x + 460 * math.sin(sa)
            
            chest_temp = pygame.Surface((220, 220), pygame.SRCALPHA)
            draw_premium_gift_box(chest_temp, 110, 110, scale=1.0, opened=False)
            rot_chest = pygame.transform.rotate(chest_temp, - (i * 45 + 22.5) - 90)
            wheel_canvas.blit(rot_chest, (lx - rot_chest.get_width() // 2, ly - rot_chest.get_height() // 2))

        # Blit rotated wheel to display
        rot_wheel = pygame.transform.rotate(wheel_canvas, self.spin_angle)
        scaled_wheel = pygame.transform.smoothscale(rot_wheel, (wheel_R * 2, wheel_R * 2))
        s.blit(scaled_wheel, (cx - wheel_R, cy - wheel_R))

        # Center cap / axle decoration
        pygame.draw.circle(s, (255, 128, 0), (cx, cy), 28)
        pygame.draw.circle(s, (255, 255, 255), (cx, cy), 28, width=3)
        pygame.draw.circle(s, (15, 8, 22), (cx, cy), 18)

        # Top Indicator pointer triangle
        ptr_y = cy - wheel_R - 6
        pygame.draw.polygon(s, (255, 255, 255), [(cx - 16, ptr_y - 20), (cx + 16, ptr_y - 20), (cx, ptr_y + 8)])
        pygame.draw.polygon(s, (255, 128, 0), [(cx - 10, ptr_y - 18), (cx + 10, ptr_y - 18), (cx, ptr_y + 4)])

        # ── RIGHT PANEL (Controls & History Logs) ──
        if not self.reveal_active:
            # Main Glassmorphic Panel Backdrop
            panel_rect = pygame.Rect(750, 100, 490, 520)
            pygame.draw.rect(s, (15, 10, 28, 220), panel_rect, border_radius=18)
            pygame.draw.rect(s, (255, 128, 0, 150), panel_rect, 2, border_radius=18)

            # Header text
            header_t = FONT_BIG.render("BẢNG ĐIỀU KHIỂN", True, (255, 255, 255))
            header_glow = FONT_BIG.render("BẢNG ĐIỀU KHIỂN", True, (255, 128, 0))
            s.blit(header_glow, (750 + 245 - header_t.get_width() // 2 + 2, 115 + 2))
            s.blit(header_t, (750 + 245 - header_t.get_width() // 2, 115))

            # Instructions description
            desc1 = "Dùng kim cương để quay. Cơ hội nhận"
            desc2 = "vàng khủng, xe Sakura hoặc Sói chiến!"
            d1_t = FONT_SM.render(desc1, True, (170, 160, 190))
            d2_t = FONT_SM.render(desc2, True, (170, 160, 190))
            s.blit(d1_t, (750 + 245 - d1_t.get_width() // 2, 158))
            s.blit(d2_t, (750 + 245 - d2_t.get_width() // 2, 180))

            # Available balance capsule
            bal_y = 205
            draw_gem_icon(s, 770, bal_y, 22)
            gems_lbl = FONT_MED.render(f"{self.gems}  KIM CƯƠNG 💎", True, (0, 255, 255))
            s.blit(gems_lbl, (802, bal_y + 1))

            # Spin Button exactly at Rect(760, 240, 480, 68)
            btn_rect = pygame.Rect(760, 240, 480, 68)
            hover_spin = btn_rect.collidepoint(mx, my)

            if self.spin_active:
                pygame.draw.rect(s, (40, 30, 50), btn_rect, border_radius=34)
                pygame.draw.rect(s, (100, 80, 120), btn_rect, 2, border_radius=34)
                btn_txt = FONT_MED.render("ĐANG QUAY...", True, (150, 140, 165))
            else:
                # Pulsing outline or hover color transition
                btn_fill = (255, 110, 0, 245) if hover_spin else (200, 75, 0, 220)
                btn_border = (255, 215, 0) if hover_spin else (255, 150, 0)
                pygame.draw.rect(s, btn_fill, btn_rect, border_radius=34)
                pygame.draw.rect(s, btn_border, btn_rect, 3, border_radius=34)
                btn_txt = FONT_MED.render(f"QUAY NGAY! ({self.spin_cost} 💎)", True, (255, 255, 255))

            s.blit(btn_txt, (760 + 240 - btn_txt.get_width() // 2, 240 + (68 - btn_txt.get_height()) // 2))

            # Logs / History panel section
            log_title = FONT_MED.render("LỊCH SỬ QUAY THƯỞNG", True, (255, 128, 0))
            s.blit(log_title, (770, 335))
            pygame.draw.line(s, (255, 128, 0, 80), (770, 360), (1220, 360), 2)

            log_start_y = 375
            for li, log in enumerate(reversed(self.lucky_spin_logs)):
                if li >= 6:
                    break
                ly_pos = log_start_y + li * 34
                
                # Check reward status for custom bullet styling
                is_premium = "Sakura" in log or "Soi Chien" in log or "10,000" in log
                bullet_c = (255, 215, 0) if is_premium else ((130, 120, 140) if "Khong trung" in log else (0, 255, 255))
                text_c = (255, 240, 180) if is_premium else ((160, 150, 175) if "Khong trung" in log else (220, 255, 255))
                
                # Bullet dot
                pygame.draw.circle(s, bullet_c, (785, ly_pos + 10), 5)
                # Text line
                log_render = FONT_SM.render(log, True, text_c)
                s.blit(log_render, (802, ly_pos))

        # ── REVEAL ACTIVE POPUP DECK ──
        if self.reveal_active:
            self.reveal_timer += 1
            tick_rev = self.reveal_timer
            
            # Sound trigger immediately at frame 1!
            if tick_rev == 1:
                if self.target_sector in (4, 5, 6, 7):
                    snd_tach_mp3.play()
                else:
                    snd_laser_riser.play()

            # Backdrop dark overlay
            bg_overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
            bg_overlay.fill((4, 2, 8, min(230, tick_rev * 6)))
            s.blit(bg_overlay, (0, 0))

            cx_rev, cy_rev = SW // 2, SH // 2 - 20

            # ── Draw rotating golden/cyan sunburst light wedges in halo background ──
            ray_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
            ray_num = 18
            base_angle = tick * 0.9
            color_ray = (255, 215, 0, 15) if self.target_sector < 4 else (120, 110, 160, 8)
            for ri in range(ray_num):
                angle_rad = math.radians(base_angle + ri * (360.0 / ray_num))
                p1 = (cx_rev, cy_rev)
                p2 = (cx_rev + SW * math.cos(angle_rad - 0.12), cy_rev + SH * math.sin(angle_rad - 0.12))
                p3 = (cx_rev + SW * math.cos(angle_rad + 0.12), cy_rev + SH * math.sin(angle_rad + 0.12))
                pygame.draw.polygon(ray_surf, color_ray, [p1, p2, p3])
            s.blit(ray_surf, (0, 0))

            # Dynamic expansion shockwaves (post-explosion)
            if tick_rev >= 65:
                wave_r = int((tick_rev - 65) * 18)
                if wave_r < 650:
                    wave_alpha = max(0, int(230 * (1 - wave_r / 650)))
                    pygame.draw.circle(s, (0, 255, 255, wave_alpha) if self.target_sector < 4 else (130, 110, 140, wave_alpha), 
                                       (cx_rev, cy_rev), wave_r, width=5)

            # Update and render reveal physics particles (flames, fireworks, shattered box pieces, coins, stars)
            for p in self.reveal_particles[:]:
                p["life"] -= 1
                if p["life"] <= 0:
                    self.reveal_particles.remove(p)
                    continue

                if p.get("is_flame", False):
                    # Flame particle physics: rise, expand, drag
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] -= 0.1
                    p["vx"] *= 0.96
                    p["size"] += 0.25
                    
                    alpha = min(255, int(255 * (p["life"] / p["max_life"])))
                    life_pct = p["life"] / p["max_life"]
                    if life_pct > 0.65:
                        col = (255, 255, 180 + int(75 * (life_pct - 0.65) / 0.35))
                    elif life_pct > 0.3:
                        col = (255, int(255 * (life_pct - 0.3) / 0.35), 20)
                    else:
                        col = (int(255 * life_pct / 0.3), 30, 10)
                        
                    sz = int(p["size"])
                    if sz > 0:
                        flame_surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                        pygame.draw.circle(flame_surf, (*col, alpha), (sz, sz), sz)
                        s.blit(flame_surf, (int(p["x"] - sz), int(p["y"] - sz)), special_flags=pygame.BLEND_RGBA_ADD)

                elif p.get("is_firework", False):
                    # Firework star particle
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] += 0.08
                    p["vx"] *= 0.97
                    
                    alpha = min(255, p["life"] * 6)
                    sz = int(p["size"])
                    if sz > 0:
                        fw_surf = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
                        pts = [
                            (sz * 2, sz * 2 - sz),
                            (sz * 2 + sz // 2, sz * 2),
                            (sz * 2, sz * 2 + sz),
                            (sz * 2 - sz // 2, sz * 2)
                        ]
                        pygame.draw.polygon(fw_surf, (*p["color"], alpha), pts)
                        pygame.draw.circle(fw_surf, (255, 255, 255, alpha), (sz * 2, sz * 2), sz // 2)
                        s.blit(fw_surf, (int(p["x"] - sz * 2), int(p["y"] - sz * 2)), special_flags=pygame.BLEND_RGBA_ADD)

                elif p.get("is_debris", False):
                    # Box debris piece
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] += 0.28
                    p["vx"] *= 0.98
                    p["angle"] += p["rot_speed"]
                    
                    if p["y"] > SH - 40:
                        p["y"] = SH - 40
                        p["vy"] = - abs(p["vy"]) * 0.45
                        p["vx"] *= 0.7
                        p["rot_speed"] *= 0.5
                    
                    alpha = min(255, p["life"] * 5)
                    sz = int(p["size"])
                    if sz > 0:
                        ang = math.radians(p["angle"])
                        w, h = sz * 2, sz
                        pts = []
                        for dx, dy in [(-w, -h), (w, -h), (w, h), (-w, h)]:
                            rx = p["x"] + dx * math.cos(ang) - dy * math.sin(ang)
                            ry = p["y"] + dx * math.sin(ang) + dy * math.cos(ang)
                            pts.append((int(rx), int(ry)))
                        pygame.draw.polygon(s, (*p["color"], alpha), pts)
                        pygame.draw.polygon(s, (255, 255, 255, alpha // 2), pts, width=1)

                else:
                    # Coin/diamond star particle
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] += 0.25
                    p["vx"] *= 0.98
                    
                    if p["y"] > SH - 40:
                        p["y"] = SH - 40
                        p["vy"] = - abs(p["vy"]) * 0.55
                        p["vx"] *= 0.8
                        
                    alpha = min(255, p["life"] * 5)
                    coin_surf = pygame.Surface((p["size"] * 4, p["size"] * 4), pygame.SRCALPHA)
                    
                    if p.get("is_coin", False):
                        coin_w = int(p["size"] * 2.2 * abs(math.sin(p["life"] * 0.16)))
                        coin_h = int(p["size"] * 2.2)
                        pygame.draw.ellipse(coin_surf, (255, 215, 0, alpha), (p["size"] * 2 - coin_w // 2, p["size"] * 2 - coin_h // 2, coin_w, coin_h))
                        pygame.draw.ellipse(coin_surf, (255, 255, 200, alpha), (p["size"] * 2 - coin_w // 4, p["size"] * 2 - coin_h // 2, coin_w // 2, coin_h), width=1)
                    else:
                        pts = [
                            (p["size"] * 2, p["size"] * 2 - p["size"]),
                            (p["size"] * 2 + p["size"] // 2, p["size"] * 2),
                            (p["size"] * 2, p["size"] * 2 + p["size"]),
                            (p["size"] * 2 - p["size"] // 2, p["size"] * 2)
                        ]
                        pygame.draw.polygon(coin_surf, (*p["color"], alpha), pts)
                    
                    s.blit(coin_surf, (int(p["x"] - p["size"] * 2), int(p["y"] - p["size"] * 2)))

            # Sequential fireworks bursts
            if 65 <= tick_rev <= 95 and (tick_rev - 65) % 8 == 0:
                fx = cx_rev + random.randint(-150, 150)
                fy = cy_rev - 120 + random.randint(-100, 50)
                fw_color = random.choice(KAWAII_RAINBOW)
                if self.target_sector < 4:
                    snd_epic_explosion.play()
                
                for _ in range(25):
                    ang = random.uniform(0, math.tau)
                    speed = random.uniform(3, 8)
                    self.reveal_particles.append({
                        "x": fx,
                        "y": fy,
                        "vx": math.cos(ang) * speed,
                        "vy": math.sin(ang) * speed,
                        "color": fw_color,
                        "size": random.randint(3, 6),
                        "life": random.randint(30, 50),
                        "is_firework": True
                    })

            # Explosion particle instant trigger at frame 65
            if tick_rev == 65:
                if self.target_sector < 4:
                    snd_epic_explosion.play()
                else:
                    snd_fail_trombone.play()
                self.shake_amount = 30
                
                for _ in range(40):
                    ang = random.uniform(0, math.tau)
                    speed = random.uniform(4, 11)
                    self.reveal_particles.append({
                        "x": cx_rev,
                        "y": cy_rev - 10,
                        "vx": math.cos(ang) * speed,
                        "vy": math.sin(ang) * speed - 2.5,
                        "size": random.uniform(8, 16),
                        "life": random.randint(20, 35),
                        "max_life": 35,
                        "is_flame": True
                    })
                
                for _ in range(20):
                    ang = random.uniform(0, math.tau)
                    speed = random.uniform(3, 8)
                    self.reveal_particles.append({
                        "x": cx_rev,
                        "y": cy_rev - 10,
                        "vx": math.cos(ang) * speed,
                        "vy": math.sin(ang) * speed - 4,
                        "color": random.choice([(200, 20, 80), (255, 215, 0), (230, 30, 100)]),
                        "size": random.randint(4, 8),
                        "life": random.randint(40, 80),
                        "angle": random.uniform(0, 360),
                        "rot_speed": random.uniform(-10, 10),
                        "is_debris": True
                    })

                if self.target_sector in (4, 5, 6, 7):
                    for _ in range(40):
                        self.reveal_particles.append({
                            "x": cx_rev,
                            "y": cy_rev - 20,
                            "vx": random.uniform(-5.5, 5.5),
                            "vy": random.uniform(-7, 2),
                            "color": (random.randint(65, 85), random.randint(60, 75), random.randint(70, 90)),
                            "size": random.randint(8, 22),
                            "life": random.randint(30, 50),
                            "is_coin": False
                        })
                else:
                    snd_epic_win.play()
                    for _ in range(35):
                        ang = random.uniform(0, math.tau)
                        speed = random.uniform(4.5, 13)
                        self.reveal_particles.append({
                            "x": cx_rev,
                            "y": cy_rev - 20,
                            "vx": math.cos(ang) * speed,
                            "vy": math.sin(ang) * speed - random.uniform(1.5, 6.0),
                            "color": (255, 215, 0),
                            "size": random.randint(6, 11),
                            "life": random.randint(60, 115),
                            "is_coin": True
                        })
                    for _ in range(35):
                        ang = random.uniform(0, math.tau)
                        speed = random.uniform(3, 10)
                        self.reveal_particles.append({
                            "x": cx_rev,
                            "y": cy_rev - 20,
                            "vx": math.cos(ang) * speed,
                            "vy": math.sin(ang) * speed - random.uniform(1, 4),
                            "color": random.choice(KAWAII_RAINBOW),
                            "size": random.randint(4, 9),
                            "life": random.randint(45, 85),
                            "is_coin": False
                        })

            # ── THREE PHASES OF THE CHEST ZOOM & REVEAL ──
            if tick_rev < 45:
                progress = min(1.0, tick_rev / 45.0)
                t_factor = 1.0 - (1.0 - progress) ** 3
                
                chest_x = cx + (cx_rev - cx) * t_factor
                chest_y = ptr_y + (cy_rev - ptr_y) * t_factor
                
                chest_scale = 0.1 + 2.1 * math.sin(progress * math.pi * 0.5)
                
                flying_surf = pygame.Surface((400, 400), pygame.SRCALPHA)
                draw_premium_gift_box(flying_surf, 200, 200, scale=chest_scale, opened=False)
                s.blit(flying_surf, (int(chest_x - 200), int(chest_y - 200)))
                
            elif tick_rev < 65:
                shake = random.randint(-8, 8)
                chest_scale = 2.2
                
                pulse_scale = chest_scale + 0.1 * math.sin((tick_rev - 45) * 0.4)
                
                flying_surf = pygame.Surface((400, 400), pygame.SRCALPHA)
                draw_premium_gift_box(flying_surf, 200, 200, scale=pulse_scale, opened=False)
                s.blit(flying_surf, (int(cx_rev - 200 + shake), int(cy_rev - 200 + shake)))
                
                if random.random() < 0.4:
                    self.reveal_particles.append({
                        "x": cx_rev + random.randint(-20, 20),
                        "y": cy_rev - 30 + random.randint(-10, 10),
                        "vx": random.uniform(-1.5, 1.5),
                        "vy": random.uniform(-3, -1),
                        "size": random.uniform(4, 8),
                        "life": random.randint(15, 25),
                        "max_life": 25,
                        "is_flame": True
                    })
                
                ring_radius = int(190 * (1.0 - (tick_rev - 45) / 20.0))
                if ring_radius > 0:
                    pygame.draw.circle(s, (255, 100, 0), (cx_rev, cy_rev), ring_radius, width=4)
                    pygame.draw.circle(s, (255, 215, 0), (cx_rev, cy_rev), ring_radius + 4, width=1)
                    
            else:
                chest_scale = 2.2
                is_win = (self.target_sector < 4)

                cw_ch, ch_ch = int(90 * chest_scale), int(72 * chest_scale)
                ch_x = cx_rev - cw_ch // 2
                ch_y = cy_rev - ch_ch // 3

                opened_surf = pygame.Surface((400, 400), pygame.SRCALPHA)
                draw_premium_gift_box(opened_surf, 200, 200, scale=chest_scale, opened=True)
                s.blit(opened_surf, (int(cx_rev - 200), int(cy_rev - 200)))

                lid_surf = pygame.Surface((400, 400), pygame.SRCALPHA)
                lid_w = int(100 * chest_scale)
                lid_h = int(24 * chest_scale)
                lid_offset_y = - min(150, (tick_rev - 65) * 6)
                lid_rot_angle = min(90, (tick_rev - 65) * 3)

                pygame.draw.rect(lid_surf, (220, 30, 100), (200 - lid_w // 2, 200 - lid_h, lid_w, lid_h), border_radius=int(4 * chest_scale))
                pygame.draw.rect(lid_surf, (255, 215, 0), (200 - int(10 * chest_scale), 200 - lid_h, int(20 * chest_scale), lid_h))
                pygame.draw.rect(lid_surf, (255, 255, 255), (200 - lid_w // 2, 200 - lid_h, lid_w, lid_h), int(2 * chest_scale), border_radius=int(4 * chest_scale))
                
                pygame.draw.ellipse(lid_surf, (255, 215, 0), (200 - int(28 * chest_scale), 200 - lid_h - int(15 * chest_scale), int(24 * chest_scale), int(16 * chest_scale)), int(3 * chest_scale))
                pygame.draw.ellipse(lid_surf, (255, 255, 200), (200 - int(24 * chest_scale), 200 - lid_h - int(13 * chest_scale), int(16 * chest_scale), int(12 * chest_scale)))
                pygame.draw.ellipse(lid_surf, (255, 215, 0), (200 + int(4 * chest_scale), 200 - lid_h - int(15 * chest_scale), int(24 * chest_scale), int(16 * chest_scale)), int(3 * chest_scale))
                pygame.draw.ellipse(lid_surf, (255, 255, 200), (200 + int(8 * chest_scale), 200 - lid_h - int(13 * chest_scale), int(16 * chest_scale), int(12 * chest_scale)))
                pygame.draw.circle(lid_surf, (255, 255, 255), (200, 200 - lid_h - int(7 * chest_scale)), int(7 * chest_scale))
                pygame.draw.circle(lid_surf, (255, 215, 0), (200, 200 - lid_h - int(7 * chest_scale)), int(7 * chest_scale), int(2 * chest_scale))
                
                rot_lid = pygame.transform.rotate(lid_surf, lid_rot_angle)
                s.blit(rot_lid, (int(cx_rev - rot_lid.get_width() // 2), int(ch_y - rot_lid.get_height() // 2 + lid_offset_y)))

                if not is_win:
                    sad_t = FONT_BIG.render("RƯƠNG RỖNG!", True, (130, 120, 140))
                    sad_sh = FONT_BIG.render("RƯƠNG RỖNG!", True, (60, 50, 70))
                    s.blit(sad_sh, (cx_rev - sad_t.get_width() // 2 + 2, cy_rev - 145 + 2))
                    s.blit(sad_t, (cx_rev - sad_t.get_width() // 2, cy_rev - 145))

                    hint_t = FONT_MED.render("CHÚC BẠN MAY MẮN LẦN SAU!", True, (180, 180, 195))
                    s.blit(hint_t, (cx_rev - hint_t.get_width() // 2, cy_rev + 115))
                else:
                    win_label = ""
                    win_color = (255, 215, 0)
                    if self.target_sector == 0:
                        win_label = "+5,000 VÀNG! 🪙"
                        win_color = (255, 215, 0)
                    elif self.target_sector == 1:
                        win_label = "+10,000 VÀNG! 🪙"
                        win_color = (255, 215, 0)
                    elif self.target_sector == 2:
                        win_label = "XE TĂNG SAKURA! 🌸"
                        win_color = (255, 120, 180)
                    elif self.target_sector == 3:
                        if "wolf" not in self.owned_pets:
                            win_label = "PET SÓI CHIẾN! 🐺"
                            win_color = (140, 160, 255)
                        else:
                            win_label = "+3,000 VÀNG BÙ! 🪙"
                            win_color = (255, 215, 0)

                    float_y = cy_rev - 170 - int(math.sin(tick * 0.1) * 6)
                    prize_t = FONT_BIG.render(win_label, True, (255, 255, 255))
                    prize_glow = FONT_BIG.render(win_label, True, win_color)
                    
                    s.blit(prize_glow, (cx_rev - prize_t.get_width() // 2 + 3, float_y + 3))
                    s.blit(prize_t, (cx_rev - prize_t.get_width() // 2, float_y))

                    sub_win = FONT_MED.render("PHẦN THƯỞNG ĐÃ ĐƯỢC GỬI!", True, (0, 255, 255))
                    s.blit(sub_win, (cx_rev - sub_win.get_width() // 2, cy_rev + 115))

            if tick_rev >= 80:
                ok_w, ok_h = 240, 48
                ok_x = cx_rev - ok_w // 2
                ok_y = cy_rev + 160
                hover_ok = pygame.Rect(ok_x, ok_y, ok_w, ok_h).collidepoint(mx, my)

                ok_fill = (35, 22, 50, 245) if hover_ok else (15, 10, 25, 210)
                ok_border = (255, 128, 0) if hover_ok else (180, 90, 0)
                
                pygame.draw.rect(s, ok_fill, (ok_x, ok_y, ok_w, ok_h), border_radius=24)
                pygame.draw.rect(s, ok_border, (ok_x, ok_y, ok_w, ok_h), 2, border_radius=24)

                ok_txt = FONT_MED.render("[ ENTER ] TIẾP TỤC", True, (255, 255, 255))
                s.blit(ok_txt, (ok_x + ok_w // 2 - ok_txt.get_width() // 2, ok_y + (ok_h - ok_txt.get_height()) // 2))

    def draw_shop(self):
        s = self._surf
        tick = self.tick

        # ── BACKGROUND: Cyber Deep Space Grid ──
        for y in range(SH):
            t = y / SH
            r = int(12 + 10 * t)
            g = int(8 + 12 * t)
            b = int(26 + 28 * t)
            pygame.draw.line(s, (r, g, b), (0, y), (SW, y))

        # Animated matrix tech grid scanlines
        grid_y = (tick * 2) % 40
        for gy in range(grid_y, SH, 40):
            pygame.draw.line(s, (0, 255, 255, 12), (0, gy), (SW, gy), 1)
        for gx in range(0, SW, 40):
            pygame.draw.line(s, (0, 255, 255, 12), (gx, 0), (gx, SH), 1)

        # ── TOP BAR: Futuristic Glassmorphic Panel ──
        top_h = 58
        # Semi-transparent dark backing
        top_bg = pygame.Surface((SW, top_h), pygame.SRCALPHA)
        top_bg.fill((10, 8, 22, 210))
        s.blit(top_bg, (0, 0))

        # Neon bottom border (rainbow spectrum)
        for segment in range(SW // 8):
            col = KAWAII_RAINBOW[(segment + tick // 15) % len(KAWAII_RAINBOW)]
            pygame.draw.rect(s, col, (segment * 8, top_h - 3, 8, 3))

        # Coin capsule
        pygame.draw.rect(s, (24, 20, 10, 180), (14, 11, 150, 32), border_radius=16)
        pygame.draw.rect(s, (255, 220, 50, 100), (14, 11, 150, 32), 1, border_radius=16)
        draw_coin_icon(s, 22, 16, 22)
        coin_t = FONT_MED.render(f"{self.money:,}", True, (255, 235, 100))
        s.blit(coin_t, (50, 18))

        # Gem capsule
        gem_x = 180
        pygame.draw.rect(s, (10, 20, 28, 180), (gem_x, 11, 150, 32), border_radius=16)
        pygame.draw.rect(s, (0, 255, 255, 100), (gem_x, 11, 150, 32), 1, border_radius=16)
        draw_gem_icon(s, gem_x + 8, 16, 22)
        gem_t = FONT_MED.render(f"{self.gems}", True, (140, 220, 255))
        s.blit(gem_t, (gem_x + 36, 18))

        # Login user capsule — anchored to the right side of the top bar so
        # it doesn't clash with the centred "CỬA HÀNG" title.
        if self.login_done and self.login_username:
            nick = self.login_username
            if len(nick) > 22:
                nick = nick[:21] + "…"
            nt = FONT_SM.render(nick, True, (255, 255, 255))
            cap_w_lg = max(120, nt.get_width() + 36)
            login_x = SW - cap_w_lg - 60  # leave room for the close-X
            pygame.draw.rect(s, (24, 16, 36, 180), (login_x, 11, cap_w_lg, 32), border_radius=16)
            pygame.draw.rect(s, (180, 130, 220, 130), (login_x, 11, cap_w_lg, 32), 1, border_radius=16)
            pygame.draw.circle(s, (180, 130, 220), (login_x + 16, 27), 9)
            pygame.draw.circle(s, (24, 16, 36), (login_x + 16, 27), 9, 2)
            s.blit(nt, (login_x + 30, 18))

        # "SHOP" Title (center glowing label)
        title_str = "CỬA HÀNG"
        title_t = FONT_BIG.render(title_str, True, (255, 255, 255))
        title_sh = FONT_BIG.render(title_str, True, (0, 255, 255))
        s.blit(title_sh, (SW // 2 - title_t.get_width() // 2 + 2, 11 + 2))
        s.blit(title_t, (SW // 2 - title_t.get_width() // 2, 11))

        # Close X Button (far right circle)
        close_x, close_y = SW - 32, 28
        pygame.draw.circle(s, (255, 50, 80, 200), (close_x, close_y), 16)
        pygame.draw.circle(s, (255, 255, 255), (close_x, close_y), 16, 2)
        pygame.draw.line(s, (255, 255, 255), (close_x - 7, close_y - 7), (close_x + 7, close_y + 7), 3)
        pygame.draw.line(s, (255, 255, 255), (close_x + 7, close_y - 7), (close_x - 7, close_y + 7), 3)

        # ── CATEGORY TABS: Rounded Translucent Neon Pills ──
        categories = ["VŨ KHÍ", "PHÒNG THỦ", "PET", "ĐẶC BIỆT", "GARA TANK"]
        tab_total_w = SW - 80
        tab_w = tab_total_w // len(categories)
        shop_cat = getattr(self, '_shop_cat', 0)
        tab_y = top_h + 12
        for ci, cat_name in enumerate(categories):
            tx = 40 + ci * tab_w
            is_sel = (ci == shop_cat)
            if is_sel:
                fill_c = (20, 150, 150, 180)
                border_c = (0, 255, 255)
                text_c = (255, 255, 255)
            else:
                fill_c = (15, 12, 28, 140)
                border_c = (60, 50, 85)
                text_c = (140, 130, 160)
            
            # Gold theme highlight for GARA TANK tab to draw attention
            if ci == 4:
                fill_c = (45, 32, 12, 150)
                border_c = (255, 180, 0)
                text_c = (255, 215, 0)
            
            pygame.draw.rect(s, fill_c, (tx, tab_y, tab_w - 8, 38), border_radius=19)
            pygame.draw.rect(s, border_c, (tx, tab_y, tab_w - 8, 38), 2, border_radius=19)
            
            cat_t = FONT_MED.render(cat_name, True, text_c)
            s.blit(cat_t, (tx + (tab_w - 8) // 2 - cat_t.get_width() // 2, tab_y + (38 - cat_t.get_height()) // 2))

        # ── ITEM DATA ──
        all_items = [
            [("1", "ĐẠN ĐA HƯỚNG", 500, "multi", (255, 200, 50)),
             ("2", "SIÊU TỐC", 800, "rapid", (255, 150, 40)),
             ("3", "XUYÊN THẤU", 600, "pierce", (80, 200, 255)),
             ("4", "TÊN LỬA", 1200, "rocket", (255, 80, 30)),
             ("5", "PHUN LỬA", 1000, "flame", (255, 150, 0)),
             ("6", "TIA LASER", 900, "laser", (0, 255, 180)),
             ("7", "PLASMA", 750, "plasma", (200, 50, 255)),
             ("8", "BOM N.TỬ", 1000, "star", (255, 215, 0))],
            [("1", "GIÁP THÉP", 300, "shield", (80, 140, 255)),
             ("2", "SỬA CHỮA", 200, "health", (255, 80, 80)),
             ("3", "THÊM MẠNG", 1000, "life", (255, 50, 150)),
             ("4", "NĂNG LƯỢNG", 150, "speed", (80, 255, 130))],
            [("1", "SÓI CHIẾN", 2000, "pet_wolf", (140, 140, 160)),
             ("2", "RỒNG LỬA", 5000, "pet_dragon", (255, 80, 30)),
             ("3", "TIÊN HỒI MÁU", 3000, "pet_healer", (255, 180, 200)),
             ("4", "ROBOT KHIÊN", 3500, "pet_shield_bot", (80, 150, 255)),
             ("5", "NAM CHÂM", 1500, "pet_magnet", (255, 220, 50)),
             ("6", "MA BÓNG", 4000, "pet_ghost", (180, 220, 255))],
            [("1", "GEM x10", 500, "gem10", (180, 220, 255)),
             ("2", "GEM x50", 2000, "gem50", (180, 220, 255)),
             ("3", "MỞ SLOT BALO", 1500, "unlock_slot", (200, 180, 130))],
        ]
        items = all_items[shop_cat]

        # ── CARD GRID LAYOUT (matches reference image — 4 cols × N rows) ──
        n = len(items)
        cols_n = 4 if n >= 4 else n
        margin_x = 20
        gap = 16
        card_w = (SW - margin_x * 2 - gap * (cols_n - 1)) // cols_n
        rows_n = (n + cols_n - 1) // cols_n
        card_area_top = tab_y + 56
        card_area_bot = SH - 56
        total_card_h = card_area_bot - card_area_top - gap * (rows_n - 1)
        card_h = min(total_card_h // max(1, rows_n), 300)

        # Reusable item description map.
        item_descs = {
            "multi": "Bắn 3 viên cùng lúc", "rapid": "Tốc độ bắn x4",
            "pierce": "Đạn xuyên qua tường", "rocket": "Tên lửa sát thương 4",
            "flame": "Phun 3 tia lửa", "laser": "Tia laser chính xác",
            "plasma": "Đạn plasma mạnh", "star": "Tiêu diệt tất cả",
            "shield": "Chắn 3 đòn đánh", "health": "Hồi 1 máu",
            "life": "Thêm 1 mạng sống", "speed": "Nạp đầy năng lượng",
            "gem10": "Đổi vàng lấy 10 gem", "gem50": "Đổi vàng lấy 50 gem",
            "unlock_slot": "Mở thêm ô balo",
            "pet_wolf": "Tự bắn kẻ địch gần", "pet_dragon": "Phun cầu lửa mạnh",
            "pet_healer": "Hồi máu cho chủ", "pet_shield_bot": "Tăng giáp định kỳ",
            "pet_magnet": "Hút vàng & item", "pet_ghost": "Đóng băng kẻ địch",
        }

        for i, (key, name, price, kind, accent) in enumerate(items):
            col = i % cols_n
            row = i // cols_n
            cx = margin_x + col * (card_w + gap)
            cy = card_area_top + row * (card_h + gap)

            affordable = self.money >= price
            # Pet-already-owned skips the affordability check.
            owned_pet = kind.startswith("pet_") and kind[4:] in self.owned_pets

            # ── Card body: vertical gradient + rounded corners ──
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            top_col = (38, 50, 78)
            bot_col = (14, 22, 42)
            for ly in range(card_h):
                tt = ly / max(1, card_h - 1)
                r = int(top_col[0] * (1 - tt) + bot_col[0] * tt)
                g = int(top_col[1] * (1 - tt) + bot_col[1] * tt)
                b = int(top_col[2] * (1 - tt) + bot_col[2] * tt)
                pygame.draw.line(card_surf, (r, g, b, 240), (0, ly), (card_w, ly))
            mask = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255),
                             (0, 0, card_w, card_h), border_radius=18)
            card_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            # Subtle inner highlight
            pygame.draw.rect(card_surf, (110, 160, 220, 90),
                             (0, 0, card_w, card_h), 2, border_radius=18)
            pygame.draw.rect(card_surf, (40, 80, 140, 200),
                             (1, 1, card_w - 2, card_h - 2), 1, border_radius=17)
            s.blit(card_surf, (cx, cy))

            # ── Item name (bold yellow, top) ──
            name_c = (255, 215, 50) if affordable or owned_pet else (170, 150, 80)
            nt = FONT_MED.render(name, True, name_c)
            # Tiny dark drop-shadow for legibility
            ns = FONT_MED.render(name, True, (15, 10, 0))
            s.blit(ns, (cx + card_w // 2 - nt.get_width() // 2 + 1, cy + 11))
            s.blit(nt, (cx + card_w // 2 - nt.get_width() // 2, cy + 10))

            # ── Description (light grey, just under the name) ──
            desc_text = item_descs.get(kind, "")
            if kind == "unlock_slot":
                desc_text = f"Mở thêm ô balo ({self.backpack_slots}/3)"
            if desc_text:
                dt = FONT_SM.render(desc_text, True,
                                    (210, 220, 240) if affordable or owned_pet else (160, 170, 190))
                s.blit(dt, (cx + card_w // 2 - dt.get_width() // 2, cy + 36))

            # ── Big icon, vertically centered between description and footer ──
            footer_h = 38
            icon_zone_top = cy + 58
            icon_zone_bot = cy + card_h - footer_h - 6
            icon_zone_h = icon_zone_bot - icon_zone_top
            icon_size = min(card_w - 60, icon_zone_h - 6, 130)
            if kind.startswith("pet_"):
                icon_size = min(card_w - 40, icon_zone_h - 4, 150)
            icon_cx = cx + card_w // 2
            icon_cy = icon_zone_top + icon_zone_h // 2

            if kind.startswith("pet_"):
                pet_id = kind[4:]
                draw_giant_shop_pet(s, pet_id, icon_cx, icon_cy, icon_size, tick)
            elif kind in sprites.items:
                ix = icon_cx - icon_size // 2
                iy = icon_cy - icon_size // 2
                icon = pygame.transform.smoothscale(sprites.items[kind],
                                                    (icon_size, icon_size))
                s.blit(icon, (ix, iy))
            elif kind == "gem10":
                draw_gem_icon(s, icon_cx - icon_size // 2,
                              icon_cy - icon_size // 2, icon_size)
            elif kind == "gem50":
                # Cluster of 3 gems for the bigger pack.
                for gi, (dx, dy, sz) in enumerate([
                    (-int(icon_size * 0.25), -int(icon_size * 0.05), int(icon_size * 0.65)),
                    (int(icon_size * 0.15), -int(icon_size * 0.18), int(icon_size * 0.55)),
                    (0, int(icon_size * 0.18), int(icon_size * 0.60)),
                ]):
                    draw_gem_icon(s,
                                  icon_cx + dx - sz // 2,
                                  icon_cy + dy - sz // 2,
                                  sz)
            elif kind == "unlock_slot":
                # Stylized backpack with progress slots underneath
                bpk_w = int(icon_size * 1.0)
                bpk_h = int(icon_size * 0.75)
                bpk_x = icon_cx - bpk_w // 2
                bpk_y = icon_cy - bpk_h // 2 - 6
                # Strap arc
                pygame.draw.arc(s, (180, 140, 80),
                                (bpk_x + bpk_w // 4, bpk_y - bpk_h // 3,
                                 bpk_w // 2, bpk_h // 2),
                                0, math.pi, 4)
                pygame.draw.rect(s, (160, 110, 60),
                                 (bpk_x, bpk_y, bpk_w, bpk_h),
                                 border_radius=10)
                pygame.draw.rect(s, (210, 150, 80),
                                 (bpk_x + 4, bpk_y + 4, bpk_w - 8, bpk_h - 8),
                                 border_radius=8)
                pygame.draw.rect(s, (110, 75, 40),
                                 (bpk_x, bpk_y, bpk_w, bpk_h), 3,
                                 border_radius=10)
                # Slot indicators (3 squares)
                slot_w = (bpk_w - 24) // 3
                for si in range(3):
                    sx_s = bpk_x + 8 + si * (slot_w + 4)
                    sy_s = bpk_y + bpk_h - slot_w - 8
                    unlocked_s = si < self.backpack_slots
                    sc_col = (90, 255, 130) if unlocked_s else (90, 70, 50)
                    pygame.draw.rect(s, sc_col,
                                     (sx_s, sy_s, slot_w, slot_w),
                                     border_radius=4)
                    pygame.draw.rect(s, (40, 30, 20),
                                     (sx_s, sy_s, slot_w, slot_w), 2,
                                     border_radius=4)
            else:
                pygame.draw.circle(s, accent,
                                   (icon_cx, icon_cy), icon_size // 3)

            # ── Footer row: gold-coin price pill (left) + status badge (right)
            footer_y = cy + card_h - footer_h - 4

            # Gold pill — left side
            p_str = f"{price:,}"
            p_t = FONT_MED.render(p_str, True, (255, 215, 50))
            coin_size = 22
            pill_padding = 10
            pill_w = coin_size + 6 + p_t.get_width() + pill_padding * 2
            pill_h = 30
            pill_x = cx + 12
            pill_y = footer_y
            # Backing capsule
            pygame.draw.rect(s, (10, 14, 28, 220),
                             (pill_x, pill_y, pill_w, pill_h), border_radius=15)
            pygame.draw.rect(s, (60, 100, 160, 200),
                             (pill_x, pill_y, pill_w, pill_h), 2, border_radius=15)
            draw_coin_icon(s, pill_x + pill_padding,
                           pill_y + (pill_h - coin_size) // 2 + 1, coin_size)
            s.blit(p_t,
                   (pill_x + pill_padding + coin_size + 6,
                    pill_y + (pill_h - p_t.get_height()) // 2))

            # Status pill — right side: "ĐỦ" / "CHƯA ĐỦ" / "ĐÃ MUA" / "ĐANG DÙNG"
            if owned_pet:
                pet_id = kind[4:]
                is_active = self.active_pet_type == pet_id
                bg_col = (10, 60, 30) if is_active else (10, 30, 60)
                fg_col = (90, 255, 150) if is_active else (140, 200, 255)
                badge_label = "ĐANG DÙNG" if is_active else "ĐÃ MUA"
            elif affordable:
                bg_col = (10, 50, 20)
                fg_col = (90, 255, 130)
                badge_label = "ĐỦ"
            else:
                bg_col = (50, 14, 18)
                fg_col = (255, 90, 110)
                badge_label = "CHƯA ĐỦ"

            badge_t = FONT_SM.render(badge_label, True, fg_col)
            badge_w = badge_t.get_width() + 18
            badge_h = pill_h
            badge_x = cx + card_w - badge_w - 12
            badge_y = footer_y
            pygame.draw.rect(s, (*bg_col, 230),
                             (badge_x, badge_y, badge_w, badge_h),
                             border_radius=15)
            pygame.draw.rect(s, (fg_col[0], fg_col[1], fg_col[2], 220),
                             (badge_x, badge_y, badge_w, badge_h), 2,
                             border_radius=15)
            s.blit(badge_t, (badge_x + (badge_w - badge_t.get_width()) // 2,
                              badge_y + (badge_h - badge_t.get_height()) // 2))

            # Hotkey indicator in the top-right corner
            key_t = FONT_SM.render(f"[{key}]", True, (160, 180, 210))
            s.blit(key_t, (cx + card_w - key_t.get_width() - 12, cy + 12))

        # ── BACKPACK UI: Cyber Monitor Frame ──
        bp_y = SH - 58
        bp_t = FONT_MED.render(f"BA LÔ {len(self.backpack)}/{self.backpack_slots}", True, (200, 220, 255))
        
        # Draw backpack HUD backing
        bp_total_w = bp_t.get_width() + 120
        pygame.draw.rect(s, (12, 10, 24, 180), (10, bp_y - 8, bp_total_w, 48), border_radius=8)
        pygame.draw.rect(s, (0, 255, 255, 80), (10, bp_y - 8, bp_total_w, 48), 1, border_radius=8)
        
        s.blit(bp_t, (22, bp_y + 4))
        for i in range(3):
            sx = 22 + bp_t.get_width() + 16 + i * 32
            sy = bp_y
            # Slot boxes
            is_locked = i >= self.backpack_slots
            fill_slot = (10, 10, 15, 200) if is_locked else (20, 24, 38, 200)
            bord_slot = (50, 45, 60) if is_locked else (0, 255, 255) if i < len(self.backpack) else (60, 65, 80)
            
            pygame.draw.rect(s, fill_slot, (sx, sy, 26, 26), border_radius=6)
            pygame.draw.rect(s, bord_slot, (sx, sy, 26, 26), 2, border_radius=6)
            
            if is_locked:
                # mini lock dot
                pygame.draw.circle(s, (100, 95, 110), (sx + 13, sy + 13), 3)
            elif i < len(self.backpack):
                k = self.backpack[i]
                if k in sprites.items:
                    icon = pygame.transform.smoothscale(sprites.items[k], (20, 20))
                    s.blit(icon, (sx + 3, sy + 3))

        # ── Tab navigation hint ──
        hint_t = FONT_MED.render("Q/E hoặc L/R đổi tab", True, (140, 160, 180))
        s.blit(hint_t, (SW // 2 - hint_t.get_width() // 2, SH - 52))

        # ── CONTINUE BUTTON (embossed neon cyber button) ──
        pulse = abs(math.sin(tick * 0.08))
        msg = "[ ENTER ] TIẾP TỤC"
        instr = FONT_MED.render(msg, True, (int(200 + 55 * pulse), 255, int(200 + 55 * pulse)))
        
        bw, bh = instr.get_width() + 50, 38
        bx = SW - bw - 16
        by = SH - bh - 10
        
        # Dynamic pulse border glow
        border_pulse_c = (int(0 + 155 * pulse), 255, int(200 + 55 * pulse))
        pygame.draw.rect(s, (12, 10, 24, 210), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(s, border_pulse_c, (bx, by, bw, bh), 3, border_radius=10)
        # Gloss highlight
        pygame.draw.rect(s, (255, 255, 255, 50), (bx + 6, by + 3, bw - 12, 2), border_radius=1)
        
        s.blit(instr, (bx + (bw - instr.get_width()) // 2, by + (bh - instr.get_height()) // 2))

    def handle_shop_events(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.state = "title"
                return
            if ev.key == pygame.K_RETURN:
                target_lvl = self.level + 1 if self.won_level else self.level
                if target_lvl > self.max_levels:
                    def go_select():
                        self.state = "level_select"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    transition.start(go_select)
                else:
                    def start_next():
                        self.start_level(target_lvl)
                        self.state = "level_start"
                        pygame.mixer.music.stop()
                    transition.start(start_next)

            # Tab switching with Q/E or LEFT/RIGHT
            if not hasattr(self, '_shop_cat'):
                self._shop_cat = 0
            if ev.key in (pygame.K_q, pygame.K_LEFT):
                self._shop_cat = (self._shop_cat - 1) % 4
                return
            if ev.key in (pygame.K_e, pygame.K_RIGHT):
                self._shop_cat = (self._shop_cat + 1) % 4
                return
            if ev.key == pygame.K_TAB:
                self._shop_cat = (self._shop_cat + 1) % 4
                return

            all_shop = [
                {"1": (500, "multi"), "2": (800, "rapid"), "3": (600, "pierce"),
                 "4": (1200, "rocket"), "5": (1000, "flame"), "6": (900, "laser"),
                 "7": (750, "plasma"), "8": (1000, "star")},
                {"1": (300, "shield"), "2": (200, "health"), "3": (1000, "life"),
                 "4": (150, "speed")},
                {"1": (2000, "pet_wolf"), "2": (5000, "pet_dragon"), "3": (3000, "pet_healer"),
                 "4": (3500, "pet_shield_bot"), "5": (1500, "pet_magnet"), "6": (4000, "pet_ghost")},
                {"1": (500, "gem10"), "2": (2000, "gem50"), "3": (1500, "unlock_slot")},
            ]
            cat = getattr(self, '_shop_cat', 0)
            shop_data = all_shop[cat]
            key_name = pygame.key.name(ev.key)
            if key_name in shop_data:
                cost, kind = shop_data[key_name]
                # Pet purchase
                if kind.startswith("pet_"):
                    pet_id = kind[4:]  # remove "pet_" prefix
                    if pet_id in self.owned_pets:
                        # Already owned — set as active
                        self.active_pet_type = pet_id
                        snd_buy.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            f"CHỌN PET: {PET_TYPES[pet_id]['name']}!",
                            (100, 255, 200), center_bounce=True))
                    elif self.money < cost:
                        snd_deny.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            "KHÔNG ĐỦ VÀNG!", (255, 80, 80), center_bounce=True))
                    else:
                        self.money -= cost
                        self.stats["money_spent"] += cost
                        self.owned_pets.append(pet_id)
                        self.active_pet_type = pet_id
                        snd_buy.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            f"MUA PET: {PET_TYPES[pet_id]['name']}!",
                            (100, 255, 100), center_bounce=True))
                elif self.money < cost:
                    snd_deny.play()
                    floating_texts.append(FloatingText(SW // 2, SH // 2,
                        "KHÔNG ĐỦ VÀNG!", (255, 80, 80), center_bounce=True))
                elif kind in ("gem10", "gem50"):
                    gain = 10 if kind == "gem10" else 50
                    self.money -= cost
                    self.gems += gain
                    self.stats["money_spent"] += cost
                    snd_buy.play()
                    floating_texts.append(FloatingText(SW // 2, SH // 2,
                        f"+{gain} ĐÁ QUÝ!", (180, 220, 255),
                        center_bounce=True))
                elif kind == "unlock_slot":
                    if self.backpack_slots >= 3:
                        snd_deny.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            "BALO ĐÃ TỐI ĐA (3/3)!", (255, 180, 80), center_bounce=True))
                    elif self.money < cost:
                        snd_deny.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            "KHÔNG ĐỦ VÀNG!", (255, 80, 80), center_bounce=True))
                    else:
                        self.money -= cost
                        self.stats["money_spent"] += cost
                        self.backpack_slots += 1
                        snd_buy.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2,
                            f"MỞ SLOT BALO {self.backpack_slots}/3!",
                            (200, 255, 150), center_bounce=True))
                elif len(self.backpack) >= self.backpack_slots:
                    snd_deny.play()
                    msg = "BA LÔ ĐẦY!" if self.backpack_slots >= 3 else "BA LÔ ĐẦY! Mua thêm slot ở ĐẶC BIỆT"
                    floating_texts.append(FloatingText(SW // 2, SH // 2,
                        msg, (255, 80, 80), center_bounce=True))
                else:
                    self.money -= cost
                    self.stats["money_spent"] += cost
                    snd_buy.play()
                    self.backpack.append(kind)
                    floating_texts.append(FloatingText(SW // 2, SH // 2,
                        f"ĐÃ MUA {kind.upper()}!",
                        (100, 255, 100), center_bounce=True))
                # Save after any successful purchase
                self._save_game()

    # ═══════════════════════════════════
    # DRAW
    # ═══════════════════════════════════
    def draw(self):
        # Respect the "Screen shake" setting toggle
        if not self.settings.get("screen_shake", True):
            self.shake_amount = 0
            self.shake_x = 0
            self.shake_y = 0
        if self.shake_amount > 0:
            self.shake_x = random.randint(-int(self.shake_amount), int(self.shake_amount))
            self.shake_y = random.randint(-int(self.shake_amount), int(self.shake_amount))
            self.shake_amount *= 0.85
            if self.shake_amount < 0.5:
                self.shake_amount = 0; self.shake_x = 0; self.shake_y = 0

        game_surf = pygame.Surface((SW, SH))
        game_surf.fill((10, 10, 15))
        self._surf = game_surf

        if self.state == "title": self.draw_title()
        elif self.state == "level_select": self.draw_level_select()
        elif self.state == "tutorial": self.draw_tutorial()
        elif self.state == "garage": self.draw_garage()
        elif self.state == "achievements": self.draw_achievements()
        elif self.state == "level_start": self.draw_level_start()
        elif self.state == "playing": self.draw_game()
        elif self.state == "shop": self.draw_shop()
        elif self.state == "lucky_spin": self.draw_lucky_spin()
        elif self.state == "gameover": self.draw_gameover()
        elif self.state == "level_clear": self.draw_level_clear()
        elif self.state == "pause": self.draw_pause()
        elif self.state == "pvp_menu": self.draw_pvp_menu()
        elif self.state == "pvp_prep": self.draw_pvp_prep()
        elif self.state == "pvp_waiting": self.draw_pvp_waiting()
        elif self.state == "pvp_lobby": self.draw_pvp_lobby()
        elif self.state == "pvp_joining": self.draw_pvp_joining()
        elif self.state == "pvp_playing": self.draw_pvp_playing()
        elif self.state == "pvp_end": self.draw_pvp_end()
        elif self.state == "coop_menu": self.draw_coop_menu()
        elif self.state == "coop_prep": self.draw_coop_prep()
        elif self.state == "coop_waiting": self.draw_coop_waiting()
        elif self.state == "coop_joining": self.draw_coop_joining()
        elif self.state == "coop_lobby": self.draw_coop_lobby()
        elif self.state == "coop_playing": self.draw_game()
        elif self.state == "settings": self.draw_settings()
        elif self.state == "keybinds": self.draw_keybinds()
        elif self.state == "login": self.draw_login()
        elif self.state == "daily_checkin": self.draw_daily_checkin()

        # Mission text overlay (vẽ trực tiếp lên game_surf)
        if self.state == "playing" and self.mission_timer > 0 and self.mission_text:
            if self.tick % 30 < 20:
                txt = FONT_MED.render(self.mission_text, True, (255, 230, 50))
                shadow = FONT_MED.render(self.mission_text, True, (50, 0, 0))
                game_surf.blit(shadow, (SW // 2 - txt.get_width() // 2 + 2, SH // 4 + 2))
                game_surf.blit(txt, (SW // 2 - txt.get_width() // 2, SH // 4))

        # Achievement popup (vẽ trực tiếp lên game_surf)
        for ach in achievement_queue:
            ach_y = int(ach.y_offset)
            a = min(255, ach.timer * 3)
            ach_s = pygame.Surface((300, 50), pygame.SRCALPHA)
            pygame.draw.rect(ach_s, (*ach.icon_color[:3], min(200, a)), (0, 0, 300, 50), border_radius=10)
            pygame.draw.rect(ach_s, (255, 255, 255, min(150, a)), (0, 0, 300, 50), 2, border_radius=10)
            nt = FONT_MED.render(ach.name, True, (255, 255, 255))
            dt = FONT_SM.render(ach.desc, True, (220, 220, 220))
            ach_s.blit(nt, (10, 5))
            ach_s.blit(dt, (10, 28))
            ach_s.set_alpha(a)
            game_surf.blit(ach_s, (SW // 2 - 150, ach_y))

        # Transition (vẽ trực tiếp lên game_surf)
        transition.draw(game_surf)

        # Floating texts (for shop/menus) (vẽ trực tiếp lên game_surf)
        if self.state in ("shop", "settings", "coop_prep", "login", "keybinds"):
            for ft in floating_texts[:]:
                ft.update()
                ft.draw(game_surf)
                if ft.life <= 0: floating_texts.remove(ft)

        # FPS counter (top-right) — respects the "Hiển thị FPS" toggle
        if self.settings.get("show_fps"):
            try:
                fps_val = int(clock.get_fps())
            except Exception:
                fps_val = 0
            fps_t = FONT_SM.render(f"FPS: {fps_val}", True, (200, 255, 220))
            fps_bg = pygame.Surface((fps_t.get_width() + 12, fps_t.get_height() + 6), pygame.SRCALPHA)
            fps_bg.fill((0, 0, 0, 140))
            game_surf.blit(fps_bg, (SW - fps_t.get_width() - 18, 6))
            game_surf.blit(fps_t, (SW - fps_t.get_width() - 12, 9))

        # High-performance bilinear hardware-smoothscale to physical screen size (No-Aliasing / Giảm răng cưa triệt để!)
        screen.fill((0, 0, 0))
        p_w, p_h = screen.get_size()
        scaled_surf = pygame.transform.smoothscale(game_surf, (p_w, p_h))
        # Support screen shake smoothly
        shake_x_phys = int(self.shake_x * (p_w / SW))
        shake_y_phys = int(self.shake_y * (p_h / SH))
        screen.blit(scaled_surf, (shake_x_phys, shake_y_phys))
        pygame.display.flip()

    def draw_game(self):
        s = self._surf
        cam_off = (self.cam_x, self.cam_y)
        zoom = self.cam_zoom
        s_ts = int(TS * zoom)

        start_gx = max(0, int(self.cam_x // TS))
        end_gx = min(COLS, int((self.cam_x + SW / zoom) // TS) + 1)
        start_gy = max(0, int(self.cam_y // TS))
        end_gy = min(ROWS, int((self.cam_y + SH / zoom) // TS) + 1)

        # Map tiles
        for y in range(start_gy, end_gy):
            for x in range(start_gx, end_gx):
                tile = self.grid[y][x]
                dx = int((x * TS - self.cam_x) * zoom)
                dy = int((y * TS - self.cam_y) * zoom)
                floor_img = sprites.floor
                if zoom != 1.0:
                    floor_img = self.get_scaled_tile(floor_img, s_ts + 1)
                s.blit(floor_img, (dx, dy))
                if tile != EMPTY and tile != GRASS:
                    img = None
                    if tile == BRICK: img = sprites.brick
                    elif tile == STEEL: img = sprites.steel
                    elif tile == WATER: img = sprites.water_frames[self.water_frame % len(sprites.water_frames)]
                    elif tile == CRATE: img = sprites.crate
                    elif tile == BASE: img = sprites.base
                    if img:
                        if zoom != 1.0:
                            img = self.get_scaled_tile(img, s_ts + 1)
                        s.blit(img, (dx, dy))

        # Entities
        for enemy in self.enemies: enemy.draw(s, self.tick, cam_off, zoom)
        for chick in self.chickens: chick.draw(s, self.tick, cam_off, zoom)
        for dog in self.dogs: dog.draw(s, self.tick, cam_off, zoom)
        for item in self.items: item.draw(s, self.tick, cam_off, zoom)
        if self.player: self.player.draw(s, self.tick, cam_off, zoom)
        if self.pet and self.pet.alive: self.pet.draw(s, cam_off, zoom)

        # Draw co-op teammates
        if self.state == "coop_playing" and self.coop_active:
            for pd in self.coop_other_data:
                if pd.get("alive", False) and pd.get("slot") != self.coop_my_slot:
                    px = pd.get("x", 0)
                    py = pd.get("y", 0)
                    d = pd.get("dir", 0)
                    draw_x = int((px - cam_off[0]) * zoom)
                    draw_y = int((py - cam_off[1]) * zoom)
                    # Draw teammate tank (blue tint)
                    t_size = int(TS * zoom)
                    img = sprites.tanks["player"][d]
                    if zoom != 1.0:
                        img = self.get_scaled_tile(img, t_size)
                    tinted = img.copy()
                    tinted.fill((100, 150, 255, 60), special_flags=pygame.BLEND_RGBA_ADD)
                    s.blit(tinted, (draw_x, draw_y))
                    # Name tag
                    name = pd.get("name", f"P{pd.get('slot', 0)+1}")
                    name_t = FONT_SM.render(name, True, (100, 200, 255))
                    s.blit(name_t, (draw_x + t_size // 2 - name_t.get_width() // 2, draw_y - 14))

        # Backpack UI
        self.draw_backpack_ui(s)

        # Grass overlay
        for y in range(start_gy, end_gy):
            for x in range(start_gx, end_gx):
                if self.grid[y][x] == GRASS:
                    dx = int((x * TS - self.cam_x) * zoom)
                    dy = int((y * TS - self.cam_y) * zoom)
                    img = sprites.grass
                    if zoom != 1.0:
                        img = self.get_scaled_tile(img, s_ts)
                    s.blit(img, (dx, dy))

        # Effects
        for bullet in self.bullets: bullet.draw(s, cam_off, zoom)
        for exp in self.explosions: exp.draw(s, cam_off, zoom)
        update_draw_particles(s, cam_off, zoom)

        for ft in floating_texts[:]:
            ft.update()
            ft.draw(s, cam_off, zoom)
            if ft.life <= 0: floating_texts.remove(ft)

        # Weather (respect the "Hiệu ứng thời tiết" toggle)
        if self.settings.get("weather_fx", True):
            weather.draw(s)

        # MINIMAP (respect the "Hiển thị Mini-map" toggle)
        if self.settings.get("show_minimap", True):
            self.draw_minimap(s)

        # HUD
        self.draw_hud(s)

        # Auto path
        if self.auto_mode and self.auto_path:
            pts = [(int((px * TS + TS // 2 - cam_off[0]) * zoom),
                    int((py * TS + TS // 2 - cam_off[1]) * zoom))
                   for px, py in self.auto_path]
            if len(pts) > 1:
                path_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
                pygame.draw.lines(path_surf, (255, 100, 100, 120), False, pts, 2)
                # Draw dots at each node
                for pt in pts:
                    pygame.draw.circle(path_surf, (255, 150, 80, 180), pt, max(2, int(3 * zoom)))
                s.blit(path_surf, (0, 0))

        # Draw custom neon gaming crosshair/reticle at mouse position
        if not self.auto_mode:
            _mx_phys, _my_phys = pygame.mouse.get_pos()
            mx_logical = int(_mx_phys * (SW / phys_w))
            my_logical = int(_my_phys * (SH / phys_h))
            
            cross_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            r_outer = 18
            
            # 1. Black shadow background outline (for high contrast on light areas)
            pygame.draw.circle(cross_surf, (0, 0, 0, 220), (32, 32), r_outer, 4)
            pygame.draw.line(cross_surf, (0, 0, 0, 220), (32, 32 - r_outer - 1), (32, 32 - r_outer + 5), 4)
            pygame.draw.line(cross_surf, (0, 0, 0, 220), (32, 32 + r_outer + 1), (32, 32 + r_outer - 5), 4)
            pygame.draw.line(cross_surf, (0, 0, 0, 220), (32 - r_outer - 1, 32), (32 - r_outer + 5, 32), 4)
            pygame.draw.line(cross_surf, (0, 0, 0, 220), (32 + r_outer + 1, 32), (32 + r_outer - 5, 32), 4)
            pygame.draw.circle(cross_surf, (0, 0, 0, 220), (32, 32), 5)
            
            # 2. Glowing Neon foreground layer
            pygame.draw.circle(cross_surf, (0, 255, 255, 255), (32, 32), r_outer, 2)
            pygame.draw.line(cross_surf, (0, 255, 255, 255), (32, 32 - r_outer), (32, 32 - r_outer + 4), 2)
            pygame.draw.line(cross_surf, (0, 255, 255, 255), (32, 32 + r_outer), (32, 32 + r_outer - 4), 2)
            pygame.draw.line(cross_surf, (0, 255, 255, 255), (32 - r_outer, 32), (32 - r_outer + 4, 32), 2)
            pygame.draw.line(cross_surf, (0, 255, 255, 255), (32 + r_outer, 32), (32 + r_outer - 4, 32), 2)
            
            # 3. High visibility red center dot
            pygame.draw.circle(cross_surf, (255, 30, 30, 255), (32, 32), 3)
            pygame.draw.circle(cross_surf, (255, 255, 255, 255), (32, 32), 1)
            
            s.blit(cross_surf, (mx_logical - 32, my_logical - 32))

    def draw_minimap(self, surf):
        # Dynamic scale to fit inside a fixed bounding box of 240x180 pixels
        max_w = 240.0
        max_h = 180.0
        mm_scale = min(max_w / COLS, max_h / ROWS)
        
        mm_w = int(COLS * mm_scale)
        mm_h = int(ROWS * mm_scale)
        mm_x = SW - mm_w - 16
        mm_y = 36

        mm = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm.fill((15, 18, 25, 200))

        for y in range(ROWS):
            for x in range(COLS):
                tile = self.grid[y][x]
                tx = int(x * mm_scale)
                ty = int(y * mm_scale)
                tw = max(1, int((x + 1) * mm_scale) - tx)
                th = max(1, int((y + 1) * mm_scale) - ty)
                if tile == STEEL:
                    pygame.draw.rect(mm, (140, 145, 160), (tx, ty, tw, th))
                elif tile == BRICK:
                    pygame.draw.rect(mm, (160, 80, 50), (tx, ty, tw, th))
                elif tile == WATER:
                    pygame.draw.rect(mm, (40, 80, 180), (tx, ty, tw, th))
                elif tile == BASE:
                    pygame.draw.rect(mm, (255, 220, 50), (tx, ty, tw, th))
                elif tile == CRATE:
                    pygame.draw.rect(mm, (150, 110, 60), (tx, ty, tw, th))

        # Camera viewport indicator
        view_w = SW / self.cam_zoom
        view_h = SH / self.cam_zoom
        vx = int(self.cam_x / TS * mm_scale)
        vy = int(self.cam_y / TS * mm_scale)
        vw = int(view_w / TS * mm_scale)
        vh = int(view_h / TS * mm_scale)
        pygame.draw.rect(mm, (255, 255, 255, 150), (vx, vy, vw, vh), 2)

        # Enemies — bigger dots, blinking for boss
        ew = max(2, int(mm_scale))
        for e in self.enemies:
            if e.alive:
                egx, egy = e.get_grid()
                ex = int(egx * mm_scale)
                ey = int(egy * mm_scale)
                if isinstance(e, BossTank):
                    # Boss with pulsing glow on minimap
                    boss_c = BOSS_COLORS.get(getattr(e, 'boss_key', ''), {})
                    ec = boss_c.get("glow_color", (255, 0, 128))
                    pulse = abs(math.sin(self.tick * 0.15))
                    sz = int(ew + 6 + pulse * 2)
                    pygame.draw.rect(mm, ec, (ex + ew // 2 - sz // 2, ey + ew // 2 - sz // 2, sz, sz))
                    pygame.draw.rect(mm, (255, 255, 255), (ex + ew // 2 - sz // 2, ey + ew // 2 - sz // 2, sz, sz), 1)
                elif e.tank_type == "boss":
                    ec = (255, 0, 128)
                    pygame.draw.rect(mm, ec, (ex - 2, ey - 2, ew + 4, ew + 4))
                    pygame.draw.rect(mm, (255, 255, 255), (ex - 2, ey - 2, ew + 4, ew + 4), 1)
                elif e.tank_type == "elite":
                    ec = (255, 150, 50)
                    pygame.draw.rect(mm, ec, (ex - 1, ey - 1, ew + 2, ew + 2))
                else:
                    ec = (255, 60, 60)
                    pygame.draw.rect(mm, ec, (ex, ey, ew, ew))

        # Player — bright green, larger
        if self.player and self.player.alive:
            pgx, pgy = self.player.get_grid()
            px = int(pgx * mm_scale)
            py = int(pgy * mm_scale)
            pw = max(2, int(mm_scale))
            pygame.draw.rect(mm, (50, 255, 100), (px - 2, py - 2, pw + 4, pw + 4))
            pygame.draw.rect(mm, (255, 255, 255), (px - 2, py - 2, pw + 4, pw + 4), 1)

        # Border with neon glow
        pygame.draw.rect(mm, (0, 255, 255), (0, 0, mm_w, mm_h), 3)

        # Label
        label = FONT_MED.render("BẢN ĐỒ", True, (200, 220, 255))
        surf.blit(mm, (mm_x, mm_y))
        surf.blit(label, (mm_x + mm_w // 2 - label.get_width() // 2, mm_y - label.get_height() - 6))

    def draw_hud(self, surf):
        hud_h = 60
        hud_y = SH - hud_h

        # Kawaii HUD background — pastel gradient bar with rounded top
        hud_bg = pygame.Surface((SW, hud_h), pygame.SRCALPHA)
        for i in range(hud_h):
            t = i / hud_h
            r = int(45 + 25 * t)
            g = int(30 + 20 * t)
            b = int(75 + 30 * t)
            pygame.draw.line(hud_bg, (r, g, b, 235), (0, i), (SW, i))
        surf.blit(hud_bg, (0, hud_y))
        # Rainbow ribbon along the top edge
        for x in range(SW):
            seg = (x // 80) % len(KAWAII_RAINBOW)
            col = KAWAII_RAINBOW[seg]
            for dy in range(2):
                surf.set_at((x, hud_y + dy), col)

        # ── LIVES with heart icons ──
        lives_lbl = FONT_SM.render("MẠNG", True, (255, 220, 240))
        surf.blit(lives_lbl, (12, hud_y + 6))
        for i in range(max(0, self.lives)):
            draw_heart_icon(surf, 12 + i * 26, hud_y + 24, 22, filled=True)

        # ── SCORE ── (under lives)
        score_t = FONT_MED.render(f"{self.score:,}", True, (255, 240, 180))
        surf.blit(score_t, (140, hud_y + 28))
        sc_lbl = FONT_SM.render("ĐIỂM", True, (200, 200, 240))
        surf.blit(sc_lbl, (140, hud_y + 12))

        # Level badge
        badge_w = 200
        badge_x = SW // 2 - badge_w // 2
        theme_colors = {
            "default": (50, 100, 150), "desert": (180, 140, 60), "snow": (100, 150, 200),
            "city": (80, 80, 100), "jungle": (40, 120, 60), "lava": (150, 50, 30),
            "kawaii_woodland": (230, 150, 200),
        }
        bc = theme_colors.get(self.map_theme, (50, 100, 150))
        pygame.draw.rect(surf, bc, (badge_x, hud_y + 6, badge_w, 22), border_radius=11)
        pygame.draw.rect(surf, (200, 220, 255), (badge_x, hud_y + 6, badge_w, 22), 1, border_radius=11)
        theme_short = {
            "default": "CHIẾN TRƯỜNG",
            "desert": "SA MẠC",
            "snow": "BĂNG GIÁ",
            "city": "THÀNH PHỐ",
            "jungle": "RỪNG RẬM",
            "lava": "NÚI LỬA",
            "kawaii_woodland": "RỪNG KAWAII",
        }.get(self.map_theme, self.map_theme.upper())
        lvl_t = FONT_SM.render(f"MÀN {self.level} • {theme_short}", True, (255, 255, 255))
        surf.blit(lvl_t, (badge_x + badge_w // 2 - lvl_t.get_width() // 2, hud_y + 10))

        # Enemies left
        left = max(0, self.total_enemies - self.kills)
        e_t = FONT_SM.render(f"KẺ ĐỊCH: {left}", True, (255, 100, 100))
        surf.blit(e_t, (SW - 150, hud_y + 8))
        for i in range(min(left, 8)):
            mini = pygame.transform.scale(sprites.tanks["enemy_a"][2], (12, 12))
            surf.blit(mini, (SW - 150 + i * 14, hud_y + 28))

        # Auto mode (placed below the level badge so it never overlaps)
        auto_x = badge_x
        auto_y = hud_y + 30
        if self.auto_mode:
            pulse = abs(math.sin(self.tick * 0.2))
            c = (int(50 + 200 * pulse), 255, int(100 + 150 * pulse))
            surf.blit(FONT_SM.render(f"TỰ ĐỘNG: {self.auto_algo}", True, c), (auto_x, auto_y))
            surf.blit(FONT_SM.render("[F]TẮT  [G]ĐỔI", True, (120, 140, 120)), (auto_x + 110, auto_y))
        else:
            surf.blit(FONT_SM.render("[F] TỰ ĐỘNG", True, (80, 100, 80)), (auto_x, auto_y))

        # Skill indicator
        if self.player and self.player.skill:
            skill_colors = {"rapid": (255, 150, 40), "ammo": (255, 200, 50), "pierce": (80, 200, 255),
                           "bomb": (255, 100, 50), "laser": (0, 255, 180), "plasma": (200, 50, 255),
                           "rocket": (255, 80, 30), "flame": (255, 150, 0)}
            sc = skill_colors.get(self.player.skill, (200, 200, 200))
            skill_name = self.player.skill.upper()
            if self.player.skill == "ammo": skill_name = "MULTI"
            st = FONT_SM.render(f"KỸ NĂNG: {skill_name}", True, sc)
            surf.blit(st, (badge_x - 100, hud_y + 35))
            if self.player.skill_timer > 0:
                bar_w = 60
                bar_fill = int(bar_w * self.player.skill_timer / 600)
                pygame.draw.rect(surf, (40, 40, 40), (badge_x - 100, hud_y + 50, bar_w, 4))
                pygame.draw.rect(surf, sc, (badge_x - 100, hud_y + 50, bar_fill, 4))

        # Pet indicator
        if self.pet and self.pet.alive:
            pet_name = self.pet.info["name"]
            pet_c = self.pet.info["color"]
            pt = FONT_SM.render(f"PET: {pet_name}", True, pet_c)
            surf.blit(pt, (12, hud_y - 18))

        # Combo
        if self.combo > 1:
            pulse = abs(math.sin(self.tick * 0.3))
            c = (255, int(150 + pulse * 100), 50)
            combo_t = FONT_MED.render(f"x{self.combo} CHUỖI", True, c)
            surf.blit(combo_t, (badge_x - 90, hud_y + 8))
            cw = 60
            cx = badge_x - 90
            cy = hud_y + 28
            pygame.draw.rect(surf, (40, 40, 40), (cx, cy, cw, 4), border_radius=2)
            fw = int((self.combo_timer / 180) * cw)
            pygame.draw.rect(surf, (255, 100, 50), (cx, cy, fw, 4), border_radius=2)

        # ── BOSS HP BAR (top of screen) ──
        boss = getattr(self, 'active_boss', None)
        if boss and boss.alive:
            bar_w = 400
            bar_h = 20
            bar_x = SW // 2 - bar_w // 2
            bar_y = 10
            boss_c = BOSS_COLORS.get(getattr(boss, 'boss_key', ''), {})
            glow_c = boss_c.get("glow_color", (255, 50, 50))

            # Background glow
            glow_s = pygame.Surface((bar_w + 20, bar_h + 20), pygame.SRCALPHA)
            pulse = abs(math.sin(self.tick * 0.1))
            pygame.draw.rect(glow_s, (*glow_c, int(30 + pulse * 30)), (0, 0, bar_w + 20, bar_h + 20), border_radius=12)
            surf.blit(glow_s, (bar_x - 10, bar_y - 10))

            # Bar background
            pygame.draw.rect(surf, (20, 10, 30), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=6)
            # HP fill
            hp_ratio = max(0, boss.hp / boss.max_hp)
            hp_w = int(bar_w * hp_ratio)
            hp_color = (255, 50, 50) if hp_ratio < 0.3 else (255, 150, 0) if hp_ratio < 0.6 else (50, 255, 50)
            pygame.draw.rect(surf, hp_color, (bar_x, bar_y, hp_w, bar_h), border_radius=4)
            # Shine
            pygame.draw.rect(surf, (255, 255, 255, 50), (bar_x, bar_y, hp_w, bar_h // 2), border_radius=4)
            # Border
            pygame.draw.rect(surf, glow_c, (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), 2, border_radius=6)

            # Boss name
            boss_name = getattr(boss, 'boss_name', 'BOSS')
            name_t = FONT_MED.render(boss_name, True, glow_c)
            surf.blit(name_t, (bar_x, bar_y - name_t.get_height() - 2))
            # HP text
            hp_text = FONT_SM.render(f"{boss.hp}/{boss.max_hp}", True, (255, 255, 255))
            surf.blit(hp_text, (bar_x + bar_w - hp_text.get_width(), bar_y - hp_text.get_height() - 2))

            # Skill indicator
            if hasattr(boss, 'skills') and hasattr(boss, 'current_skill'):
                skill_names = BOSS_INFO.get(getattr(boss, 'boss_key', ''), {}).get('skill_names', [])
                if skill_names:
                    next_skill = skill_names[boss.current_skill % len(skill_names)]
                    cd_ratio = boss.skill_cooldown / max(1, boss.skill_cooldown_max)
                    if cd_ratio > 0:
                        cd_text = FONT_SM.render(f"Chiêu tiếp: {next_skill} ({int(cd_ratio * 100)}%)", True, (200, 200, 200))
                    else:
                        cd_text = FONT_SM.render(f"Đang dùng: {next_skill}!", True, (255, 200, 50))
                    surf.blit(cd_text, (bar_x, bar_y + bar_h + 4))

            # Enrage indicator
            if getattr(boss, 'enraged', False):
                rage_pulse = abs(math.sin(self.tick * 0.2))
                rage_t = FONT_SM.render("CUỒNG NỘ!", True, (255, int(50 + rage_pulse * 100), 50))
                surf.blit(rage_t, (bar_x + bar_w + 10, bar_y + 2))

    # ═══════════════════════════════════════
    #  LOGIN SCREEN  (fake — purely cosmetic)
    # ═══════════════════════════════════════
    def _handle_login_event(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_ESCAPE:
            # ESC on the splash = quit, matches usual UX.
            self._save_game(); pygame.quit(); sys.exit()
            return
        # Any other key advances past the splash video into the lobby.
        self._skip_splash()

    def _login_with_button(self, idx):
        """Activate one of the buttons drawn on the login screen."""
        if idx < 0 or idx >= len(self.login_buttons):
            return
        label, _rect, prov_label = self.login_buttons[idx]
        if label == "BACK":
            # Quit game when the back/login top-left button is clicked.
            self._save_game(); pygame.quit(); sys.exit()
            return
        # Everything else logs the player in instantly.
        self._login_with_provider(prov_label)

    def _login_with(self, idx):
        """Backwards-compatible — translate the old provider index to the
        new button-based flow."""
        try:
            prov_name, _, _ = self.login_providers[idx]
        except Exception:
            prov_name = "Khách"
        self._login_with_provider(prov_name.split(" /")[0].split(" (")[0])

    def _skip_splash(self):
        """Dismiss the intro splash video and enter the lobby.  If the
        player already has a saved login from a previous session, keep
        their nickname/provider intact and just switch state."""
        # Clear any lingering floating texts so the clean lobby video isn't
        # covered by a banner.
        try: floating_texts.clear()
        except Exception: pass
        if self.login_done and self.login_username:
            self.state = "title"
            try: pygame.mixer.music.play(-1)
            except Exception: pass
            return
        self._login_with_provider("Khách")

    def _login_with_provider(self, prov_name):
        """Mark the player as logged in via *prov_name* and switch to the
        title screen.  The login is purely cosmetic — no real auth."""
        self.login_provider = prov_name
        if not self.player_name:
            self.player_name = "Player"
        nick = self.player_name or "Player"
        if prov_name.lower().startswith("kh"):
            self.login_username = nick + " (Khách)"
        else:
            self.login_username = nick + " · " + prov_name
        self.login_done = True
        self.state = "title"
        try: pygame.mixer.music.play(-1)
        except Exception: pass
        self._save_game()

    def draw_login(self):
        """Animated splash / login screen.  Just plays the user-supplied
        login video on loop — no buttons, no overlays.  Clicking anywhere
        or pressing any key enters the game (handled in handle_event)."""
        s = self._surf
        tick = self.tick

        frames = getattr(self, 'login_bg_frames', None) or []
        if frames:
            step = max(1, 60 // max(1, self.login_bg_fps))
            idx = (tick // step) % len(frames)
            s.blit(frames[idx], (0, 0))
        elif getattr(self, 'login_bg', None):
            s.blit(self.login_bg, (0, 0))
        else:
            # Last-resort gradient so something is on screen.
            for yy in range(SH):
                t = yy / SH
                pygame.draw.line(s, (int(20 + 30 * t), int(20 + 25 * t),
                                     int(40 + 30 * t)), (0, yy), (SW, yy))
            warn = FONT_MED.render("(login_anim chưa được nạp)", True, (255, 200, 200))
            s.blit(warn, (SW // 2 - warn.get_width() // 2, SH // 2))

    # ═══════════════════════════════════════
    #  KEY-BINDING SCREEN
    # ═══════════════════════════════════════
    def _handle_keybinds_event(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        if self.awaiting_keybind:
            # Capture the next key press as the new binding.
            if ev.key == pygame.K_ESCAPE:
                self.awaiting_keybind = False
                return
            _, kid = self.keybind_labels[self.keybind_sel]
            # Avoid duplicate binding by clearing any other action using this key
            for other_key, kv in list(self.keybinds.items()):
                if kv == ev.key and other_key != kid:
                    self.keybinds[other_key] = None
            self.keybinds[kid] = ev.key
            self.awaiting_keybind = False
            return

        n = len(self.keybind_labels)
        if ev.key == pygame.K_ESCAPE:
            self._save_game()
            self.state = "settings"
        elif ev.key in (pygame.K_UP, pygame.K_w):
            self.keybind_sel = (self.keybind_sel - 1) % n
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            self.keybind_sel = (self.keybind_sel + 1) % n
        elif ev.key == pygame.K_RETURN:
            self.awaiting_keybind = True
        elif ev.key == pygame.K_r:
            # Reset all bindings to default.
            self.keybinds.update({
                "up": pygame.K_w, "down": pygame.K_s,
                "left": pygame.K_a, "right": pygame.K_d,
                "shoot": pygame.K_SPACE, "special": pygame.K_LSHIFT,
                "freeze": pygame.K_f, "grenade": pygame.K_g,
                "pause": pygame.K_ESCAPE,
            })

    def draw_keybinds(self):
        s = self._surf
        tick = self.tick

        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((15, 10, 30))
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        s.blit(overlay, (0, 0))

        draw_rainbow_text(s, "GÁN PHÍM ĐIỀU KHIỂN", (SW // 2, 50), FONT_TITLE, tick=tick)
        sub = FONT_MED.render("Chọn một dòng và nhấn ENTER, sau đó nhấn phím muốn gán.",
                              True, (200, 215, 235))
        s.blit(sub, (SW // 2 - sub.get_width() // 2, 100))

        panel_w = 700
        panel_h = SH - 220
        panel_x = SW // 2 - panel_w // 2
        panel_y = 140
        pnl = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(pnl, (18, 14, 32, 220), (0, 0, panel_w, panel_h), border_radius=18)
        pygame.draw.rect(pnl, (0, 255, 255, 180), (0, 0, panel_w, panel_h), 2, border_radius=18)
        s.blit(pnl, (panel_x, panel_y))

        row_h = 44
        for i, (label, kid) in enumerate(self.keybind_labels):
            iy = panel_y + 22 + i * row_h
            row_x = panel_x + 22
            is_sel = (i == self.keybind_sel)
            if is_sel:
                hl = pygame.Surface((panel_w - 44, row_h - 6), pygame.SRCALPHA)
                pygame.draw.rect(hl, (0, 255, 255, 55), (0, 0, panel_w - 44, row_h - 6), border_radius=10)
                pygame.draw.rect(hl, (0, 255, 255, 200), (0, 0, panel_w - 44, row_h - 6), 2, border_radius=10)
                s.blit(hl, (row_x, iy))

            lc = (255, 255, 255) if is_sel else (210, 220, 240)
            lt = FONT_MED.render(label, True, lc)
            s.blit(lt, (row_x + 18, iy + (row_h - 6 - lt.get_height()) // 2))

            # Key pill
            kv = self.keybinds.get(kid)
            if kv is None:
                key_name = "—"
            else:
                try: key_name = pygame.key.name(kv).upper()
                except Exception: key_name = str(kv)
            pill_w = 180
            pill_h = row_h - 14
            px = row_x + panel_w - 44 - pill_w
            py = iy + 3
            pill_fill = (0, 200, 200, 220) if is_sel else (60, 80, 110)
            border_c = (255, 255, 255) if is_sel else (140, 160, 180)
            if is_sel and self.awaiting_keybind:
                # Pulsing red — waiting for input
                pulse = abs(math.sin(tick * 0.3))
                pill_fill = (220, int(40 + 80 * pulse), 80)
                key_name = "NHẤN PHÍM..."
            pygame.draw.rect(s, pill_fill, (px, py, pill_w, pill_h), border_radius=10)
            pygame.draw.rect(s, border_c, (px, py, pill_w, pill_h), 2, border_radius=10)
            kt = FONT_MED.render(key_name, True, (255, 255, 255))
            s.blit(kt, (px + pill_w // 2 - kt.get_width() // 2,
                        py + pill_h // 2 - kt.get_height() // 2))

        hint = FONT_SM.render(
            "[↑/↓] chọn  •  [ENTER] gán  •  [R] reset mặc định  •  [ESC] quay lại",
            True, (180, 200, 220))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 32))

    # ═══════════════════════════════════════
    #  SETTINGS SCREEN
    # ═══════════════════════════════════════
    def _settings_value_text(self, key, kind, params):
        v = self.settings.get(key)
        if kind == "slider":
            return f"{int(v):3d}%"
        if kind == "toggle":
            return "BẬT" if v else "TẮT"
        if kind == "choice":
            try:
                return params[int(v)]
            except Exception:
                return "?"
        if kind == "action":
            return ""
        return str(v)

    def _settings_step(self, direction):
        """Adjust the currently focused setting by `direction` (+1 / -1)."""
        item = self.settings_layout[self.settings_sel]
        label, key, kind, params = item
        if kind == "slider":
            self.settings[key] = max(0, min(100, int(self.settings.get(key, 0)) + direction * 5))
            apply_audio_settings(self.settings)
        elif kind == "toggle":
            self.settings[key] = not bool(self.settings.get(key, False))
            if key == "fullscreen":
                apply_video_settings(self.settings)
        elif kind == "choice":
            n = len(params)
            self.settings[key] = (int(self.settings.get(key, 0)) + direction) % n
            if key in ("resolution_idx",) and not self.settings.get("fullscreen", True):
                apply_video_settings(self.settings)

    def _settings_activate(self):
        item = self.settings_layout[self.settings_sel]
        label, key, kind, params = item
        if kind == "action":
            if key == "_apply":
                apply_audio_settings(self.settings)
                apply_video_settings(self.settings)
                self._save_game()
                floating_texts.append(FloatingText(
                    SW // 2, SH // 2 + 220, "ĐÃ LƯU CÀI ĐẶT!",
                    (100, 255, 180), center_bounce=True))
            elif key == "_reset":
                self.settings = dict(DEFAULT_SETTINGS)
                apply_audio_settings(self.settings)
                apply_video_settings(self.settings)
            elif key == "_keybinds":
                self.state = "keybinds"
                self.keybind_sel = 0
                self.awaiting_keybind = False
            elif key == "_logout":
                # Wipe login info and bounce back to the login screen.
                self.login_done = False
                self.login_username = ""
                self.login_provider = ""
                self.state = "login"
                self.login_sel = 0
                self._save_game()
            elif key == "_back":
                prev = getattr(self, "_settings_prev_state", "title")
                self.state = prev if prev in ("title", "pause") else "title"
                self._save_game()
        elif kind == "toggle":
            self._settings_step(1)
        elif kind == "choice":
            self._settings_step(1)
        elif kind == "slider":
            self._settings_step(1)

    def _settings_layout_rects(self):
        """Return a dict {idx: {"row": Rect, "kind": str, "left": Rect|None,
        "right": Rect|None, "track": Rect|None, "value_zone": Rect|None}}
        describing the on-screen position of each settings row so the
        mouse handler can hit-test them.  Mirrors the math in
        draw_settings()."""
        items = self.settings_layout
        n = len(items)
        split_actions = [i for i, e in enumerate(items) if e[2] == "action"]
        split = split_actions[0] if split_actions else n
        left_items  = list(enumerate(items[:split]))
        right_items = list(enumerate(items[split:], start=split))

        hdr_h = 70
        list_y = hdr_h + 16
        list_h = SH - list_y - 40
        col_w = (SW - 60) // 2
        col_gap = 20
        col_x_left = 20
        col_x_right = col_x_left + col_w + col_gap

        rows_per_col = max(1, len(left_items))
        row_step = min(56, max(50, list_h // max(1, rows_per_col)))
        row_h = 50

        rects = {}

        def _row_zones(idx, kind, ox, oy, w):
            row_rect = pygame.Rect(ox, oy, w, row_h)
            val_x = ox + w // 2 + 20
            val_w = w - (w // 2 + 20) - 14
            cy = oy + row_h // 2
            zones = {"row": row_rect, "kind": kind,
                     "left": None, "right": None,
                     "track": None, "value_zone": None,
                     "pill": None, "knob_y": cy}
            if kind == "slider":
                track_w = val_w - 50
                zones["track"] = pygame.Rect(val_x - 6, cy - 12,
                                             track_w + 12, 24)
                zones["track_x"] = val_x
                zones["track_w"] = track_w
            elif kind == "toggle":
                pill_w, pill_h = 64, 26
                px = val_x + val_w - pill_w - 4
                py = cy - pill_h // 2
                zones["pill"] = pygame.Rect(px, py, pill_w, pill_h)
            elif kind == "choice":
                zones["left"]  = pygame.Rect(val_x - 4, cy - 14, 28, 28)
                zones["right"] = pygame.Rect(val_x + val_w - 24,
                                             cy - 14, 28, 28)
                zones["value_zone"] = pygame.Rect(val_x + 24, cy - 14,
                                                  val_w - 52, 28)
            return zones

        for k, (idx, (label, key, kind, params)) in enumerate(left_items):
            rects[idx] = _row_zones(idx, kind, col_x_left,
                                    list_y + k * row_step, col_w)

        right_non_action = [(idx, e) for idx, e in right_items if e[2] != "action"]
        right_actions    = [(idx, e) for idx, e in right_items if e[2] == "action"]

        right_y = list_y
        for k, (idx, (label, key, kind, params)) in enumerate(right_non_action):
            rects[idx] = _row_zones(idx, kind, col_x_right,
                                    right_y, col_w)
            right_y += row_step

        if right_actions:
            btn_h = 42
            act_y = list_y + list_h - len(right_actions) * 48 - 8
            for idx, (label, key, kind, params) in right_actions:
                rects[idx] = {
                    "row":  pygame.Rect(col_x_right, act_y, col_w, btn_h),
                    "kind": "action",
                    "left": None, "right": None,
                    "track": None, "value_zone": None,
                    "pill": None,
                }
                act_y += btn_h + 6

        return rects

    def _handle_settings_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = pygame.mouse.get_pos()
            rects = self._settings_layout_rects()
            for idx, z in rects.items():
                if not z["row"].collidepoint(mx, my):
                    # Slider track may extend slightly outside the row
                    if z.get("track") and z["track"].collidepoint(mx, my):
                        pass
                    else:
                        continue
                self.settings_sel = idx
                kind = z["kind"]
                if kind == "action":
                    self._settings_activate()
                elif kind == "toggle":
                    self._settings_step(1)
                elif kind == "slider":
                    tx = z.get("track_x")
                    tw = z.get("track_w")
                    if tx is not None and tw:
                        ratio = max(0.0, min(1.0, (mx - tx) / max(1, tw)))
                        key = self.settings_layout[idx][1]
                        new_val = int(round(ratio * 100 / 5) * 5)
                        self.settings[key] = max(0, min(100, new_val))
                        apply_audio_settings(self.settings)
                        self._settings_dragging = idx
                elif kind == "choice":
                    if z["left"] and z["left"].collidepoint(mx, my):
                        self._settings_step(-1)
                    elif z["right"] and z["right"].collidepoint(mx, my):
                        self._settings_step(+1)
                    else:
                        # Click on the value text cycles forward
                        self._settings_step(+1)
                return
            return
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self._settings_dragging = None
            return
        if ev.type == pygame.MOUSEMOTION:
            drag = getattr(self, "_settings_dragging", None)
            if drag is not None and drag in self._settings_layout_rects():
                z = self._settings_layout_rects()[drag]
                if z["kind"] == "slider":
                    tx = z.get("track_x")
                    tw = z.get("track_w")
                    if tx is not None and tw:
                        ratio = max(0.0, min(1.0, (ev.pos[0] - tx) / max(1, tw)))
                        key = self.settings_layout[drag][1]
                        self.settings[key] = max(0, min(100, int(round(ratio * 100))))
                        apply_audio_settings(self.settings)
            return
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_ESCAPE:
            prev = getattr(self, "_settings_prev_state", "title")
            self.state = prev if prev in ("title", "pause") else "title"
            self._save_game()
        elif ev.key in (pygame.K_UP, pygame.K_w):
            self.settings_sel = (self.settings_sel - 1) % len(self.settings_layout)
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            self.settings_sel = (self.settings_sel + 1) % len(self.settings_layout)
        elif ev.key in (pygame.K_LEFT, pygame.K_a):
            self._settings_step(-1)
        elif ev.key in (pygame.K_RIGHT, pygame.K_d):
            self._settings_step(+1)
        elif ev.key == pygame.K_RETURN:
            self._settings_activate()

    def draw_settings(self):
        s = self._surf
        tick = self.tick

        # ── Background: smooth gradient + faint moving stars ──
        for yy in range(0, SH, 2):
            t = yy / SH
            r = int(10 + 12 * t)
            g = int(8 + 10 * t)
            b = int(28 + 38 * t)
            pygame.draw.line(s, (r, g, b), (0, yy), (SW, yy + 1))
        if not hasattr(self, '_set_stars'):
            random.seed(31)
            self._set_stars = [(random.randint(0, SW),
                                random.randint(0, SH),
                                random.choice([1, 1, 1, 2]),
                                random.uniform(0, 6.28)) for _ in range(120)]
            random.seed()
        for sx, sy, sz, phase in self._set_stars:
            yy = (sy + int(tick * 0.08)) % SH
            tw = max(80, min(220, 140 + int(80 * math.sin(tick * 0.05 + phase))))
            if sz == 1:
                s.set_at((sx, yy), (tw, tw, tw))
            else:
                pygame.draw.circle(s, (tw, tw, tw), (sx, yy), sz)

        # ── Header card ──
        hdr_h = 70
        hdr_surf = pygame.Surface((SW, hdr_h), pygame.SRCALPHA)
        for ly in range(hdr_h):
            tt = ly / hdr_h
            pygame.draw.line(hdr_surf,
                             (int(20 + 30 * tt), int(30 + 40 * tt),
                              int(60 + 60 * tt), 230),
                             (0, ly), (SW, ly))
        s.blit(hdr_surf, (0, 0))
        pygame.draw.line(s, (90, 220, 255, 200),
                         (0, hdr_h - 1), (SW, hdr_h - 1), 2)
        # Gear icon left
        gicx, gicy, gicr = 36, hdr_h // 2, 16
        pygame.draw.circle(s, (90, 220, 255), (gicx, gicy), gicr, 3)
        pygame.draw.circle(s, (90, 220, 255), (gicx, gicy), gicr - 7, 2)
        for ang in range(0, 360, 45):
            rad = math.radians(ang + tick * 0.7)
            tx = int(gicx + math.cos(rad) * (gicr + 2))
            ty = int(gicy + math.sin(rad) * (gicr + 2))
            pygame.draw.circle(s, (90, 220, 255), (tx, ty), 2)
        title_sh = FONT_BIG.render("CÀI ĐẶT", True, (10, 14, 30))
        title = FONT_BIG.render("CÀI ĐẶT", True, (90, 220, 255))
        s.blit(title_sh, (66, 11))
        s.blit(title, (64, 9))
        sub = FONT_SM.render(
            "Tinh chỉnh trải nghiệm — âm thanh • đồ hoạ • hiển thị",
            True, (210, 220, 240))
        s.blit(sub, (64 + title.get_width() + 16,
                     hdr_h // 2 - sub.get_height() // 2))

        # ── Two-column item layout ──
        # Render all items into two columns, but keep the underlying
        # `settings_layout` linear so input handling (↑/↓) stays unchanged.
        items = self.settings_layout
        n = len(items)
        # Split at the boundary between configurable items and big action
        # buttons.  Actions live in the bottom-right column footer.
        split_actions = [i for i, e in enumerate(items) if e[2] == "action"]
        if split_actions:
            split = split_actions[0]
        else:
            split = n
        left_items  = list(enumerate(items[:split]))
        right_items = list(enumerate(items[split:], start=split))

        # Section background
        list_y = hdr_h + 16
        list_h = SH - list_y - 40
        col_w = (SW - 60) // 2
        col_gap = 20
        col_x_left = 20
        col_x_right = col_x_left + col_w + col_gap

        # Helper: draw card row
        def _draw_row(label, key, kind, params, idx, ox, oy, w):
            row_h = 50
            is_sel = (idx == self.settings_sel)
            row_surf = pygame.Surface((w, row_h), pygame.SRCALPHA)
            base_col = (28, 38, 70, 200) if not is_sel else (50, 110, 160, 230)
            pygame.draw.rect(row_surf, base_col,
                             (0, 0, w, row_h), border_radius=10)
            border_col = (60, 90, 130, 200) if not is_sel else (140, 230, 255, 240)
            pygame.draw.rect(row_surf, border_col,
                             (0, 0, w, row_h), 2, border_radius=10)
            if is_sel:
                pygame.draw.rect(row_surf, (255, 220, 90, 220),
                                 (0, 0, 4, row_h), border_radius=2)
            s.blit(row_surf, (ox, oy))

            lbl_c = (255, 255, 255) if is_sel else (210, 220, 240)
            lt = FONT_SM.render(label, True, lbl_c)
            s.blit(lt, (ox + 14, oy + (row_h - lt.get_height()) // 2))

            val_x = ox + w // 2 + 20
            val_w = w - (w // 2 + 20) - 14
            cy = oy + row_h // 2

            if kind == "slider":
                v = int(self.settings.get(key, 0))
                track_w = val_w - 50
                pygame.draw.rect(s, (40, 50, 80),
                                 (val_x, cy - 3, track_w, 6),
                                 border_radius=3)
                fill_w = int(track_w * v / 100)
                grad_c = (90, 220, 255) if is_sel else (100, 180, 220)
                pygame.draw.rect(s, grad_c,
                                 (val_x, cy - 3, fill_w, 6),
                                 border_radius=3)
                kx = val_x + fill_w
                pygame.draw.circle(s, (255, 255, 255), (kx, cy), 8)
                pygame.draw.circle(s, grad_c, (kx, cy), 5)
                vt = FONT_SM.render(f"{v:3d}%", True, (220, 240, 255))
                s.blit(vt, (val_x + track_w + 10,
                            cy - vt.get_height() // 2))
            elif kind == "toggle":
                on = bool(self.settings.get(key, False))
                pill_w, pill_h = 64, 26
                px = val_x + val_w - pill_w - 4
                py = cy - pill_h // 2
                fill_c = (50, 200, 120) if on else (90, 60, 70)
                pygame.draw.rect(s, fill_c, (px, py, pill_w, pill_h),
                                 border_radius=13)
                pygame.draw.rect(s, (255, 255, 255, 150),
                                 (px, py, pill_w, pill_h), 2,
                                 border_radius=13)
                knob_x = px + pill_w - 17 if on else px + 4
                pygame.draw.circle(s, (255, 255, 255),
                                   (knob_x + 4, py + pill_h // 2), 9)
                lbl_t = FONT_SM.render("ON" if on else "OFF", True,
                                       (255, 255, 255))
                s.blit(lbl_t, (px + pill_w // 2 - lbl_t.get_width() // 2 +
                               (-8 if on else 8),
                               py + pill_h // 2 - lbl_t.get_height() // 2))
            elif kind == "choice":
                text = self._settings_value_text(key, kind, params)
                arrow_c = (90, 220, 255) if is_sel else (160, 200, 220)
                pygame.draw.polygon(s, arrow_c,
                                    [(val_x + 4, cy),
                                     (val_x + 14, cy - 6),
                                     (val_x + 14, cy + 6)])
                rx = val_x + val_w - 8
                pygame.draw.polygon(s, arrow_c,
                                    [(rx, cy),
                                     (rx - 10, cy - 6),
                                     (rx - 10, cy + 6)])
                col_t = (255, 255, 255) if is_sel else (210, 220, 240)
                tt = FONT_SM.render(text, True, col_t)
                s.blit(tt, (val_x + (val_w // 2) - tt.get_width() // 2,
                            cy - tt.get_height() // 2))

        # Left column rows (sliders + toggles + choices)
        rows_per_col = max(1, len(left_items))
        row_step = min(56, max(50, list_h // max(1, rows_per_col)))
        for k, (idx, (label, key, kind, params)) in enumerate(left_items):
            _draw_row(label, key, kind, params,
                      idx, col_x_left, list_y + k * row_step, col_w)

        # Right column: choices/toggles continuation + actions at the bottom
        right_non_action = [(idx, e) for idx, e in right_items if e[2] != "action"]
        right_actions = [(idx, e) for idx, e in right_items if e[2] == "action"]

        # If no non-action items in the right column, fill the top space
        # with an info / profile card so the right side never feels empty.
        right_y = list_y
        if not right_non_action and right_actions:
            info_h = list_h - len(right_actions) * 48 - 20
            info_surf = pygame.Surface((col_w, info_h), pygame.SRCALPHA)
            top_c = (28, 38, 70, 220)
            pygame.draw.rect(info_surf, top_c,
                             (0, 0, col_w, info_h), border_radius=14)
            pygame.draw.rect(info_surf, (90, 220, 255, 200),
                             (0, 0, col_w, info_h), 2, border_radius=14)
            s.blit(info_surf, (col_x_right, right_y))

            hdr_t = FONT_MED.render("THÔNG TIN TÀI KHOẢN", True,
                                    (90, 220, 255))
            s.blit(hdr_t, (col_x_right + col_w // 2 - hdr_t.get_width() // 2,
                            right_y + 14))
            # Divider
            pygame.draw.line(s, (90, 220, 255, 160),
                             (col_x_right + 20, right_y + 50),
                             (col_x_right + col_w - 20, right_y + 50), 1)

            # Avatar circle
            ax, ay, ar = col_x_right + 50, right_y + 100, 30
            pygame.draw.circle(s, (40, 60, 110), (ax, ay), ar)
            pygame.draw.circle(s, (90, 220, 255), (ax, ay), ar, 2)
            uname = (getattr(self, 'login_username', None) or "Khách")[0].upper()
            ut = FONT_BIG.render(uname, True, (255, 255, 255))
            s.blit(ut, (ax - ut.get_width() // 2, ay - ut.get_height() // 2))

            # Username + provider
            user_full = getattr(self, 'login_username', None) or "Khách"
            user_provider = getattr(self, 'login_provider', None) or "Local"
            un_t = FONT_MED.render(user_full, True, (255, 255, 255))
            s.blit(un_t, (ax + ar + 16, ay - un_t.get_height()))
            pr_t = FONT_SM.render(f"Đăng nhập: {user_provider}",
                                  True, (200, 220, 240))
            s.blit(pr_t, (ax + ar + 16, ay + 4))

            # Currency row
            cy_y = right_y + 160
            draw_coin_icon(s, col_x_right + 30, cy_y, 18)
            ct = FONT_MED.render(f"{self.money:,}", True, (255, 230, 130))
            s.blit(ct, (col_x_right + 60, cy_y - 4))
            gx = col_x_right + 60 + ct.get_width() + 30
            draw_gem_icon(s, gx, cy_y, 18)
            gt = FONT_MED.render(f"{self.gems:,}", True, (140, 220, 255))
            s.blit(gt, (gx + 26, cy_y - 4))

            # Tips footer
            tip_y = right_y + info_h - 56
            pygame.draw.line(s, (90, 220, 255, 100),
                             (col_x_right + 20, tip_y - 4),
                             (col_x_right + col_w - 20, tip_y - 4), 1)
            tip1 = FONT_SM.render(
                "Mẹo: nhấn ÁP DỤNG để lưu cấu hình.",
                True, (200, 220, 240))
            s.blit(tip1, (col_x_right + 20, tip_y + 4))
            tip2 = FONT_SM.render(
                "Có thể đổi phím di chuyển trong GÁN PHÍM.",
                True, (200, 220, 240))
            s.blit(tip2, (col_x_right + 20, tip_y + 28))
        else:
            for idx, (label, key, kind, params) in right_non_action:
                _draw_row(label, key, kind, params, idx,
                          col_x_right, right_y, col_w)
                right_y += row_step

        # Actions live at the bottom of the right column as wide buttons.
        if right_actions:
            act_y = list_y + list_h - len(right_actions) * 48 - 8
            for idx, (label, key, kind, params) in right_actions:
                is_sel = (idx == self.settings_sel)
                btn_h = 42
                bx = col_x_right
                bw = col_w
                if key == "_reset":
                    col = (230, 160, 60)
                elif key == "_back":
                    col = (220, 90, 100)
                elif key == "_logout":
                    col = (180, 80, 200)
                elif key == "_keybinds":
                    col = (80, 160, 230)
                else:  # _apply
                    col = (60, 200, 120)
                pygame.draw.rect(s, (5, 8, 18, 200),
                                 (bx + 3, act_y + 3, bw, btn_h),
                                 border_radius=10)
                pygame.draw.rect(s, col,
                                 (bx, act_y, bw, btn_h),
                                 border_radius=10)
                border_c = (255, 255, 255, 240) if is_sel else (255, 255, 255, 120)
                pygame.draw.rect(s, border_c,
                                 (bx, act_y, bw, btn_h), 2,
                                 border_radius=10)
                if is_sel:
                    pulse = abs(math.sin(tick * 0.1))
                    pygame.draw.rect(s, (255, 220, 100,
                                          int(120 + 100 * pulse)),
                                     (bx - 2, act_y - 2, bw + 4, btn_h + 4),
                                     3, border_radius=12)
                bt = FONT_MED.render(label, True, (255, 255, 255))
                s.blit(bt, (bx + bw // 2 - bt.get_width() // 2,
                            act_y + btn_h // 2 - bt.get_height() // 2))
                act_y += btn_h + 6

        # ── Footer hints ──
        hint = FONT_SM.render(
            "Chuột: click trực tiếp · [↑/↓] chọn · [←/→] đổi · [ENTER] kích hoạt · [ESC] quay lại",
            True, (180, 200, 220))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 28))

    # ═══════════════════════════════════════
    #  CO-OP ROOM PREP SCREEN
    # ═══════════════════════════════════════
    def _coop_prep_layout(self):
        """Return list of editable fields shown on coop_prep screen."""
        return [
            ("Tên người chơi",       "name"),
            ("Tên phòng",            "room"),
            ("Màn bắt đầu",          "level"),
            ("Độ khó",               "diff"),
            ("Số mạng",              "lives"),
            ("Số người tối đa",      "max"),
            ("Bắn nhầm đồng đội",    "ff"),
            ("Map theme",            "theme"),
            ("BẮT ĐẦU TẠO PHÒNG",    "_create"),
        ]

    def _handle_coop_prep_event(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        fields = self._coop_prep_layout()
        if ev.key == pygame.K_ESCAPE:
            if self.coop_prep_name_editing:
                self.coop_prep_name_editing = False
            elif self.coop_prep_room_name_editing:
                self.coop_prep_room_name_editing = False
            else:
                self.state = "coop_menu"
            return

        if self.coop_prep_name_editing:
            if ev.key == pygame.K_RETURN:
                self.coop_prep_name_editing = False
            elif ev.key == pygame.K_BACKSPACE:
                self.coop_prep_name = self.coop_prep_name[:-1]
            elif ev.unicode and ev.unicode.isprintable() and len(self.coop_prep_name) < 16:
                self.coop_prep_name += ev.unicode
            return
        if self.coop_prep_room_name_editing:
            if ev.key == pygame.K_RETURN:
                self.coop_prep_room_name_editing = False
            elif ev.key == pygame.K_BACKSPACE:
                self.coop_prep_room_name = self.coop_prep_room_name[:-1]
            elif ev.unicode and ev.unicode.isprintable() and len(self.coop_prep_room_name) < 24:
                self.coop_prep_room_name += ev.unicode
            return

        if ev.key in (pygame.K_UP, pygame.K_w):
            self.coop_prep_field = (self.coop_prep_field - 1) % len(fields)
            return
        if ev.key in (pygame.K_DOWN, pygame.K_s):
            self.coop_prep_field = (self.coop_prep_field + 1) % len(fields)
            return

        _, key = fields[self.coop_prep_field]
        if ev.key in (pygame.K_LEFT, pygame.K_a):
            self._coop_prep_step(key, -1)
            return
        if ev.key in (pygame.K_RIGHT, pygame.K_d):
            self._coop_prep_step(key, +1)
            return
        if ev.key == pygame.K_RETURN:
            self._coop_prep_activate(key)

    def _coop_prep_step(self, key, direction):
        if key == "level":
            unlocked = sorted(self.unlocked_levels)
            if not unlocked:
                return
            if self.coop_prep_level not in unlocked:
                self.coop_prep_level = unlocked[0]
            idx = unlocked.index(self.coop_prep_level)
            idx = (idx + direction) % len(unlocked)
            self.coop_prep_level = unlocked[idx]
        elif key == "diff":
            self.coop_prep_difficulty = (self.coop_prep_difficulty + direction) % 4
        elif key == "lives":
            self.coop_prep_lives = max(1, min(9, self.coop_prep_lives + direction))
        elif key == "max":
            self.coop_prep_max_players = max(2, min(4, self.coop_prep_max_players + direction))
        elif key == "ff":
            self.coop_prep_friendly_fire = not self.coop_prep_friendly_fire
        elif key == "theme":
            themes = ["auto"] + list(MAP_THEME_DEFS.keys())
            if self.coop_prep_theme not in themes:
                self.coop_prep_theme = "auto"
            idx = themes.index(self.coop_prep_theme)
            idx = (idx + direction) % len(themes)
            self.coop_prep_theme = themes[idx]

    def _coop_prep_activate(self, key):
        if key == "name":
            self.coop_prep_name_editing = True
        elif key == "room":
            self.coop_prep_room_name_editing = True
        elif key == "_create":
            # Persist the chosen settings into the live state used by
            # start_coop_host / lobby broadcasting.
            self.player_name = self.coop_prep_name or self.player_name
            self.coop_level = self.coop_prep_level
            self.coop_max_players = self.coop_prep_max_players
            self.coop_room_info = {
                "name":  self.coop_prep_room_name or "Phòng Co-Op",
                "diff":  self.coop_prep_difficulty,
                "lives": self.coop_prep_lives,
                "ff":    self.coop_prep_friendly_fire,
                "theme": self.coop_prep_theme,
            }
            self.start_coop_host()
        else:
            # On enter for non-action toggles, treat like right-arrow step.
            self._coop_prep_step(key, +1)

    def draw_coop_prep(self):
        s = self._surf
        tick = self.tick

        # Background
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((15, 10, 30))
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        s.blit(overlay, (0, 0))

        draw_rainbow_text(s, "TẠO PHÒNG CO-OP", (SW // 2, 40), FONT_TITLE, tick=tick)
        sub = FONT_MED.render("Tuỳ chỉnh phòng theo ý bạn — mời bạn bè vượt ải!",
                              True, (210, 220, 240))
        s.blit(sub, (SW // 2 - sub.get_width() // 2, 88))

        # ── Left settings panel ──
        panel_w = 680
        panel_h = SH - 180
        panel_x = 40
        panel_y = 130
        pnl = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(pnl, (18, 14, 32, 220), (0, 0, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(pnl, (0, 255, 255, 160), (0, 0, panel_w, panel_h), 2, border_radius=20)
        s.blit(pnl, (panel_x, panel_y))

        fields = self._coop_prep_layout()
        item_h = 44
        for i, (label, key) in enumerate(fields):
            iy = panel_y + 24 + i * item_h
            row_x = panel_x + 22
            is_sel = (i == self.coop_prep_field)
            if is_sel:
                hl = pygame.Surface((panel_w - 44, item_h - 6), pygame.SRCALPHA)
                pygame.draw.rect(hl, (0, 255, 255, 55), (0, 0, panel_w - 44, item_h - 6), border_radius=10)
                pygame.draw.rect(hl, (0, 255, 255, 200), (0, 0, panel_w - 44, item_h - 6), 2, border_radius=10)
                s.blit(hl, (row_x, iy))

            # Label
            lc = (255, 255, 255) if is_sel else (210, 220, 240)
            lt = FONT_MED.render(label, True, lc)
            s.blit(lt, (row_x + 14, iy + (item_h - 6 - lt.get_height()) // 2))

            # Value area
            val_x = row_x + 320
            val_w = panel_w - 50 - 320

            if key == "name":
                txt = (self.coop_prep_name or self.player_name) + ("|" if self.coop_prep_name_editing and (tick // 20) % 2 == 0 else "")
                pygame.draw.rect(s, (12, 8, 22), (val_x, iy + 4, val_w, item_h - 14), border_radius=6)
                pygame.draw.rect(s, (0, 255, 255) if self.coop_prep_name_editing else (90, 110, 140),
                                 (val_x, iy + 4, val_w, item_h - 14), 2, border_radius=6)
                tt = FONT_MED.render(txt, True, (255, 255, 255))
                s.blit(tt, (val_x + 8, iy + 7))
            elif key == "room":
                txt = self.coop_prep_room_name + ("|" if self.coop_prep_room_name_editing and (tick // 20) % 2 == 0 else "")
                pygame.draw.rect(s, (12, 8, 22), (val_x, iy + 4, val_w, item_h - 14), border_radius=6)
                pygame.draw.rect(s, (0, 255, 255) if self.coop_prep_room_name_editing else (90, 110, 140),
                                 (val_x, iy + 4, val_w, item_h - 14), 2, border_radius=6)
                tt = FONT_MED.render(txt, True, (255, 255, 255))
                s.blit(tt, (val_x + 8, iy + 7))
            elif key == "level":
                txt = f"Màn {self.coop_prep_level}"
                self._draw_step_value(s, val_x, iy, val_w, item_h, txt, is_sel)
            elif key == "diff":
                colors_d = [(140, 220, 140), (255, 220, 100), (255, 150, 80), (255, 80, 90)]
                self._draw_step_value(s, val_x, iy, val_w, item_h,
                                      self.coop_difficulty_names[self.coop_prep_difficulty],
                                      is_sel, accent=colors_d[self.coop_prep_difficulty])
            elif key == "lives":
                self._draw_step_value(s, val_x, iy, val_w, item_h,
                                      f"{self.coop_prep_lives} mạng", is_sel)
            elif key == "max":
                self._draw_step_value(s, val_x, iy, val_w, item_h,
                                      f"{self.coop_prep_max_players} người", is_sel)
            elif key == "ff":
                on = self.coop_prep_friendly_fire
                pill_w, pill_h = 80, 26
                px = val_x + val_w - pill_w - 8
                py = iy + 6
                fill_c = (220, 80, 90) if on else (40, 200, 120)
                pygame.draw.rect(s, fill_c, (px, py, pill_w, pill_h), border_radius=13)
                pygame.draw.rect(s, (255, 255, 255), (px, py, pill_w, pill_h), 2, border_radius=13)
                knob_x = px + pill_w - 20 if on else px + 6
                pygame.draw.circle(s, (255, 255, 255), (knob_x, py + pill_h // 2), 10)
                lbl_t = FONT_SM.render("ON" if on else "OFF", True, (255, 255, 255))
                s.blit(lbl_t, (px + pill_w // 2 - lbl_t.get_width() // 2 + (10 if on else -10),
                               py + pill_h // 2 - lbl_t.get_height() // 2))
            elif key == "theme":
                if self.coop_prep_theme == "auto":
                    txt = "Tự động theo màn"
                else:
                    txt = MAP_THEME_DEFS.get(self.coop_prep_theme, ("?",))[0]
                self._draw_step_value(s, val_x, iy, val_w, item_h, txt, is_sel)
            elif key == "_create":
                btn_w = 320
                bx = val_x + val_w - btn_w
                by = iy + 2
                bh = item_h - 10
                pulse = abs(math.sin(tick * 0.12))
                col = (int(40 + 60 * pulse), 200 + int(40 * pulse), 100)
                pygame.draw.rect(s, (10, 10, 18, 180), (bx + 3, by + 3, btn_w, bh), border_radius=12)
                pygame.draw.rect(s, col, (bx, by, btn_w, bh), border_radius=12)
                pygame.draw.rect(s, (255, 255, 255, 220), (bx, by, btn_w, bh), 2, border_radius=12)
                bt = FONT_MED.render(label, True, (255, 255, 255))
                s.blit(bt, (bx + btn_w // 2 - bt.get_width() // 2, by + bh // 2 - bt.get_height() // 2))

        # ── Right side: map preview ──
        preview_x = panel_x + panel_w + 22
        preview_w = SW - preview_x - 40
        preview_y = 130
        preview_h = panel_h
        rp = pygame.Surface((preview_w, preview_h), pygame.SRCALPHA)
        pygame.draw.rect(rp, (18, 14, 32, 220), (0, 0, preview_w, preview_h), border_radius=20)
        pygame.draw.rect(rp, (255, 215, 80, 160), (0, 0, preview_w, preview_h), 2, border_radius=20)
        s.blit(rp, (preview_x, preview_y))

        ph = FONT_MED.render("BẢN ĐỒ", True, (255, 230, 130))
        s.blit(ph, (preview_x + preview_w // 2 - ph.get_width() // 2, preview_y + 14))

        # Determine theme for preview
        if self.coop_prep_theme != "auto":
            theme_key = self.coop_prep_theme
        else:
            theme_key = self.get_theme_for_level(self.coop_prep_level)

        thumb_w = preview_w - 40
        thumb_h = int(thumb_w * 0.66)
        thumb = build_map_thumbnail(theme_key, thumb_w, thumb_h, self.coop_prep_level)
        s.blit(thumb, (preview_x + 20, preview_y + 50))
        pygame.draw.rect(s, (255, 230, 130), (preview_x + 20, preview_y + 50, thumb_w, thumb_h), 2)

        # Theme name & code badge
        tname, _, _, _, _, code = MAP_THEME_DEFS.get(theme_key, MAP_THEME_DEFS["default"])
        info_y = preview_y + 60 + thumb_h
        nt = FONT_MED.render(f"Theme: {tname}", True, (255, 255, 255))
        s.blit(nt, (preview_x + 24, info_y))
        ct = FONT_SM.render(f"CODE: {code}", True, (140, 200, 255))
        s.blit(ct, (preview_x + 24, info_y + 26))
        lvl_t = FONT_SM.render(f"Màn: {self.coop_prep_level}    Khó: {self.coop_difficulty_names[self.coop_prep_difficulty]}",
                               True, (255, 220, 140))
        s.blit(lvl_t, (preview_x + 24, info_y + 50))
        ff_t = FONT_SM.render(
            ("Bắn nhầm đồng đội: BẬT" if self.coop_prep_friendly_fire else "Bắn nhầm đồng đội: TẮT"),
            True, (255, 200, 200) if self.coop_prep_friendly_fire else (200, 255, 220))
        s.blit(ff_t, (preview_x + 24, info_y + 74))

        # Footer hint
        hint = FONT_SM.render(
            "[↑/↓] chọn  •  [←/→] đổi giá trị  •  [ENTER] sửa tên / Tạo phòng  •  [ESC] quay lại",
            True, (180, 200, 220))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 32))

    def _draw_step_value(self, surf, x, y, w, h, text, is_sel, accent=None):
        """Draw a left/right stepper UI (◀ value ▶)."""
        # Left arrow
        pygame.draw.polygon(surf, (0, 255, 255),
                            [(x + 4, y + h // 2 - 2), (x + 14, y + h // 2 - 11),
                             (x + 14, y + h // 2 + 7)])
        # Right arrow
        rx = x + w - 18
        pygame.draw.polygon(surf, (0, 255, 255),
                            [(rx + 10, y + h // 2 - 2),
                             (rx, y + h // 2 - 11), (rx, y + h // 2 + 7)])
        tc = accent if accent else ((255, 255, 255) if is_sel else (210, 220, 240))
        tt = FONT_MED.render(text, True, tc)
        surf.blit(tt, (x + (w // 2) - tt.get_width() // 2, y + h // 2 - tt.get_height() // 2 - 2))

    # ═══════════════════════════════════════
    #  CO-OP DRAWING FUNCTIONS
    # ═══════════════════════════════════════
    def draw_coop_menu(self):
        s = self._surf
        # Background
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((15, 10, 30))
        # Semi-transparent overlay
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        s.blit(overlay, (0, 0))

        draw_rainbow_text(s, "CHƠI CHUNG (CO-OP)", (SW // 2, 50), FONT_TITLE, tick=self.tick)
        desc = FONT_SM.render("Cùng bạn bè vượt ải qua mạng LAN / Radmin VPN", True, (200, 200, 220))
        s.blit(desc, (SW // 2 - desc.get_width() // 2, 95))

        for i, opt in enumerate(self.coop_menu_options):
            selected = (i == self.coop_menu_sel)
            y = 160 + i * 60
            draw_neon_button(s, opt, SW // 2, y, 300, 45,
                            selected=selected, tick=self.tick)
        hint = FONT_SM.render("[↑/↓] Chọn  [ENTER] Xác nhận  [ESC] Quay lại", True, (120, 120, 150))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 30))

    def _draw_coop_room_view(self, host_view):
        """Shared draw routine for host (coop_waiting) and client (coop_lobby).
        Shows the room header, map preview, player roster and footer hint."""
        s = self._surf
        tick = self.tick

        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((15, 10, 30))
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        s.blit(overlay, (0, 0))

        # Animated grid scanlines
        for gy in range((tick * 2) % 40, SH, 40):
            pygame.draw.line(s, (0, 255, 255, 14), (0, gy), (SW, gy), 1)

        # Header
        if host_view:
            title = "PHÒNG CO-OP — BẠN LÀ CHỦ"
        else:
            title = "SẢNH CO-OP — ĐANG CHỜ"
        draw_rainbow_text(s, title, (SW // 2, 40), FONT_TITLE, tick=tick)

        # Top capsule with room name & ip
        rn = self.coop_room_info.get("name", "Phòng Co-Op")
        cap_t = FONT_MED.render(f"« {rn} »", True, (255, 240, 200))
        cap_w = cap_t.get_width() + 50
        cap_x = SW // 2 - cap_w // 2
        pygame.draw.rect(s, (15, 12, 30, 220), (cap_x, 78, cap_w, 32), border_radius=16)
        pygame.draw.rect(s, (255, 215, 100), (cap_x, 78, cap_w, 32), 2, border_radius=16)
        s.blit(cap_t, (SW // 2 - cap_t.get_width() // 2, 84))

        # IP info
        try:
            if host_view:
                ip = self._get_local_ip()
                port = self.coop_socket.getsockname()[1] if self.coop_socket else 0
                info_t = FONT_SM.render(f"Địa chỉ: {ip}:{port}  •  Chia sẻ cho bạn bè", True, (0, 255, 200))
            else:
                addr = self.coop_host_addr or ("?", 0)
                info_t = FONT_SM.render(f"Đã kết nối: {addr[0]}:{addr[1]}", True, (0, 255, 200))
            s.blit(info_t, (SW // 2 - info_t.get_width() // 2, 118))
        except Exception:
            pass

        # ── LEFT panel: room settings summary ──
        left_x = 50
        left_y = 155
        left_w = 520
        left_h = SH - left_y - 90
        lp = pygame.Surface((left_w, left_h), pygame.SRCALPHA)
        pygame.draw.rect(lp, (18, 14, 32, 220), (0, 0, left_w, left_h), border_radius=18)
        pygame.draw.rect(lp, (0, 255, 255, 180), (0, 0, left_w, left_h), 2, border_radius=18)
        s.blit(lp, (left_x, left_y))

        head_t = FONT_MED.render("THÔNG TIN PHÒNG", True, (255, 255, 255))
        s.blit(head_t, (left_x + left_w // 2 - head_t.get_width() // 2, left_y + 12))

        info_rows = [
            ("Tên phòng",   rn),
            ("Màn",         f"#{self.coop_level}"),
            ("Độ khó",      self.coop_difficulty_names[self.coop_room_info.get("diff", 1) % 4]),
            ("Số mạng",     str(self.coop_room_info.get("lives", 3))),
            ("Số người tối đa", str(self.coop_max_players)),
            ("Bắn nhầm đồng đội", "BẬT" if self.coop_room_info.get("ff") else "TẮT"),
            ("Map theme",   ("Tự động" if self.coop_room_info.get("theme", "auto") == "auto"
                              else MAP_THEME_DEFS.get(self.coop_room_info.get("theme", "auto"),
                                                     ("?",))[0])),
        ]
        for ri, (lk, lv) in enumerate(info_rows):
            iy = left_y + 50 + ri * 32
            pygame.draw.rect(s, (30, 24, 50, 140), (left_x + 16, iy, left_w - 32, 26), border_radius=6)
            kt = FONT_SM.render(lk, True, (180, 200, 220))
            vt = FONT_MED.render(lv, True, (255, 255, 255))
            s.blit(kt, (left_x + 28, iy + 5))
            s.blit(vt, (left_x + left_w - 28 - vt.get_width(), iy + 1))

        # Map preview thumbnail (inside left panel)
        thumb_w = left_w - 60
        thumb_h = 140
        thumb_x = left_x + 30
        thumb_y = left_y + 50 + len(info_rows) * 32 + 16
        theme_key = self.coop_room_info.get("theme", "auto")
        if theme_key == "auto":
            theme_key = self.get_theme_for_level(self.coop_level)
        thumb = build_map_thumbnail(theme_key, thumb_w, thumb_h, self.coop_level)
        s.blit(thumb, (thumb_x, thumb_y))
        pygame.draw.rect(s, (255, 215, 100), (thumb_x, thumb_y, thumb_w, thumb_h), 2)

        # ── RIGHT panel: player roster ──
        right_x = left_x + left_w + 30
        right_w = SW - right_x - 50
        right_y = left_y
        right_h = left_h
        rp = pygame.Surface((right_w, right_h), pygame.SRCALPHA)
        pygame.draw.rect(rp, (18, 14, 32, 220), (0, 0, right_w, right_h), border_radius=18)
        pygame.draw.rect(rp, (255, 100, 200, 180), (0, 0, right_w, right_h), 2, border_radius=18)
        s.blit(rp, (right_x, right_y))

        rhead = FONT_MED.render(
            f"NGƯỜI CHƠI  {self._coop_count_players()}/{self.coop_max_players}",
            True, (255, 200, 230))
        s.blit(rhead, (right_x + right_w // 2 - rhead.get_width() // 2, right_y + 12))

        # Player slot cards
        slot_h = 60
        for i in range(self.coop_max_players):
            slot_x = right_x + 16
            slot_y = right_y + 50 + i * (slot_h + 8)
            if i < len(self.coop_lobby_view):
                entry = self.coop_lobby_view[i]
                is_host_p = entry.get("is_host", False)
                is_me = entry.get("slot") == self.coop_my_slot
                fill_c = (40, 25, 70, 220) if is_host_p else (25, 35, 55, 220)
                border_c = (255, 220, 100) if is_host_p else (0, 220, 220)
                if is_me:
                    border_c = (100, 255, 180)
                pygame.draw.rect(s, fill_c, (slot_x, slot_y, right_w - 32, slot_h), border_radius=12)
                pygame.draw.rect(s, border_c, (slot_x, slot_y, right_w - 32, slot_h), 2, border_radius=12)
                # Avatar circle
                ac_x = slot_x + 32
                ac_y = slot_y + slot_h // 2
                tank_col = ['p_yellow', 'p_blue', 'p_green', 'p_red'][i % 4]
                if hasattr(sprites, 'tanks') and tank_col in sprites.tanks:
                    av = pygame.transform.smoothscale(sprites.tanks[tank_col][0], (44, 44))
                    s.blit(av, (ac_x - 22, ac_y - 22))
                else:
                    pygame.draw.circle(s, (200, 200, 255), (ac_x, ac_y), 22)
                pygame.draw.circle(s, border_c, (ac_x, ac_y), 22, 2)
                # Name + role
                name = entry.get("name", "???")
                nt = FONT_MED.render(name, True, (255, 255, 255))
                s.blit(nt, (slot_x + 70, slot_y + 8))
                role_text = "★ Chủ phòng" if is_host_p else f"Người chơi {i + 1}"
                if is_me:
                    role_text += "  •  Bạn"
                rt = FONT_SM.render(role_text, True, border_c)
                s.blit(rt, (slot_x + 70, slot_y + 34))
                # Ready ping
                ready_x = slot_x + right_w - 32 - 40
                pygame.draw.circle(s, (80, 230, 120), (ready_x, slot_y + slot_h // 2), 8)
                pygame.draw.circle(s, (255, 255, 255), (ready_x, slot_y + slot_h // 2), 8, 2)
            else:
                # Empty slot — animated dashed border
                dash = 8
                for dseg in range(0, right_w - 32, dash * 2):
                    pygame.draw.rect(s, (90, 100, 120),
                                     (slot_x + dseg, slot_y, dash, 2))
                    pygame.draw.rect(s, (90, 100, 120),
                                     (slot_x + dseg, slot_y + slot_h - 2, dash, 2))
                pygame.draw.rect(s, (90, 100, 120), (slot_x, slot_y, 2, slot_h))
                pygame.draw.rect(s, (90, 100, 120), (slot_x + right_w - 34, slot_y, 2, slot_h))
                pulse = abs(math.sin(tick * 0.08 + i))
                wt = FONT_SM.render("Đang chờ người chơi vào…", True,
                                    (int(120 + 100 * pulse), int(120 + 100 * pulse), 150))
                s.blit(wt, (slot_x + (right_w - 32) // 2 - wt.get_width() // 2,
                            slot_y + slot_h // 2 - wt.get_height() // 2))

        # ── Footer / instructions ──
        count = self._coop_count_players()
        if host_view:
            if count >= 2:
                pulse = abs(math.sin(tick * 0.12))
                btn_w, btn_h = 360, 50
                bx = SW // 2 - btn_w // 2
                by = SH - 70
                pygame.draw.rect(s, (12, 28, 18, 200), (bx + 3, by + 3, btn_w, btn_h), border_radius=14)
                pygame.draw.rect(s, (int(30 + 60 * pulse), int(180 + 60 * pulse), 100),
                                 (bx, by, btn_w, btn_h), border_radius=14)
                pygame.draw.rect(s, (255, 255, 255), (bx, by, btn_w, btn_h), 2, border_radius=14)
                bt = FONT_MED.render("[ENTER] BẮT ĐẦU TRẬN!", True, (255, 255, 255))
                s.blit(bt, (bx + btn_w // 2 - bt.get_width() // 2,
                            by + btn_h // 2 - bt.get_height() // 2))
            else:
                wait_t = FONT_MED.render("Chờ bạn bè vào phòng… Chia sẻ IP cho họ.",
                                         True, (255, 200, 100))
                s.blit(wait_t, (SW // 2 - wait_t.get_width() // 2, SH - 56))
        else:
            wait_t = FONT_MED.render("Chờ chủ phòng bắt đầu trận…",
                                     True, (255, 200, 100))
            s.blit(wait_t, (SW // 2 - wait_t.get_width() // 2, SH - 56))

        hint = FONT_SM.render(
            "[ESC] Rời phòng  •  Mời bạn bè vào cùng vượt ải!",
            True, (180, 200, 220))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 26))

    def draw_coop_waiting(self):
        self._draw_coop_room_view(host_view=True)

    def draw_coop_joining(self):
        s = self._surf
        if getattr(self, 'bg_main', None):
            s.blit(self.bg_main, (0, 0))
        else:
            s.fill((15, 10, 30))
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        s.blit(overlay, (0, 0))

        draw_rainbow_text(s, "TÌM PHÒNG CO-OP", (SW // 2, 40), FONT_TITLE, tick=self.tick)

        # Manual IP
        ip_label = "Nhập IP:" if not self.coop_manual_ip_editing else "IP >"
        ip_c = (0, 255, 200) if self.coop_manual_ip_editing else (150, 150, 180)
        ip_txt = FONT_MED.render(f"{ip_label} {self.coop_manual_ip}_" if self.coop_manual_ip_editing
                                 else f"[TAB] Nhập IP thủ công", True, ip_c)
        s.blit(ip_txt, (SW // 2 - ip_txt.get_width() // 2, 85))

        # Found hosts
        if self.coop_found_hosts:
            y = 140
            for i, host in enumerate(self.coop_found_hosts):
                selected = (i == self.coop_menu_sel)
                name = host.get("name", "???")
                lvl = host.get("level", "?")
                count = host.get("players", 1)
                mx = host.get("max", 4)
                label = f"{name}  |  Màn {lvl}  |  {count}/{mx}"
                draw_neon_button(s, label, SW // 2, y, 500, 45,
                                selected=selected, tick=self.tick)
                y += 55
        else:
            scan = FONT_MED.render("Đang quét mạng LAN...", True, (150, 150, 200))
            s.blit(scan, (SW // 2 - scan.get_width() // 2, 180))
            # Scanning animation
            dots = "." * (1 + (self.tick // 20) % 3)
            scan2 = FONT_SM.render(f"Tìm kiếm{dots}", True, (100, 100, 140))
            s.blit(scan2, (SW // 2 - scan2.get_width() // 2, 215))

        hint = FONT_SM.render("[ESC] Quay lại  [TAB] Nhập IP  [ENTER] Vào phòng", True, (120, 120, 150))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 30))

    def draw_coop_lobby(self):
        self._draw_coop_room_view(host_view=False)

    def draw_level_select(self):
        s = self._surf
        tick = self.tick

        # ── FAST PATH: world-map image background (drawing identical to
        # the reference artwork — no overlays, just transparent click
        # zones over the painted tiles plus a detail panel on the right).
        if getattr(self, 'level_select_bg', None):
            self._draw_level_select_image_mode()
            return

        # ── 1. Deep-space animated background ──
        # Vertical gradient from indigo (top) → deep purple (bottom).
        for y in range(0, SH, 2):
            t = y / SH
            r = int(10 + 12 * t)
            g = int(6 + 8 * t)
            b = int(28 + 36 * t)
            pygame.draw.line(s, (r, g, b), (0, y), (SW, y + 1))

        # Very faint nebula clouds, drifting slowly.  Kept dim so the
        # level nodes always remain the focus.
        if not hasattr(self, '_ls_nebulae'):
            random.seed(7)
            self._ls_nebulae = [
                (random.randint(120, SW - 420),
                 random.randint(120, SH - 240),
                 random.randint(160, 220),
                 random.choice([(40, 20, 70), (25, 35, 80), (55, 25, 65)]))
                for _ in range(2)
            ]
            random.seed()
        for i, (nx, ny, nr, nc) in enumerate(self._ls_nebulae):
            ox = int(math.sin(tick * 0.003 + i) * 10)
            oy = int(math.cos(tick * 0.0025 + i * 0.7) * 7)
            neb = pygame.Surface((nr * 2, nr * 2), pygame.SRCALPHA)
            pygame.draw.circle(neb, (*nc, 8), (nr, nr), nr)
            s.blit(neb, (nx - nr + ox, ny - nr + oy),
                   special_flags=pygame.BLEND_RGBA_ADD)

        # Twinkling star field — three parallax layers.
        if not hasattr(self, '_ls_stars'):
            random.seed(11)
            self._ls_stars = []
            for layer in range(3):
                count = (60, 90, 50)[layer]
                size = (1, 2, 3)[layer]
                speed = (0.10, 0.20, 0.32)[layer]
                for _ in range(count):
                    self._ls_stars.append((
                        random.randint(0, SW),
                        random.randint(0, SH),
                        size, speed,
                        random.uniform(0, 6.28),
                    ))
            random.seed()
        for sx, sy, sz, spd, phase in self._ls_stars:
            yy = (sy + int(tick * spd)) % SH
            twinkle = 140 + int(115 * math.sin(tick * 0.06 + phase))
            twinkle = max(60, min(255, twinkle))
            if sz <= 1:
                s.set_at((sx, yy), (twinkle, twinkle, twinkle))
            else:
                pygame.draw.circle(s, (twinkle, twinkle, twinkle), (sx, yy), sz)
                if sz >= 3:
                    pygame.draw.circle(s, (twinkle, twinkle, twinkle, 60),
                                       (sx, yy), sz + 2, 1)

        # (Galaxy haze removed — keep background clean for nodes.)

        # 4. Node positions calculation
        # Keep the right side reserved for the map preview panel
        right_panel_w = 320
        if not hasattr(self, '_level_nodes') or len(self._level_nodes) != self.max_levels:
            nodes = []
            margin = 70
            uw = SW - margin * 2 - right_panel_w
            per_row = 5
            for i in range(self.max_levels):
                row = i // per_row
                col = i % per_row
                if row % 2 == 0:
                    x = margin + int(col * uw / max(1, per_row - 1))
                else:
                    x = margin + int((per_row - 1 - col) * uw / max(1, per_row - 1))
                y = 90 + row * 105 + int(math.sin(i * 0.8) * 14)
                nodes.append((x, y))
            self._level_nodes = nodes
        nodes = self._level_nodes

        # Camera scroll
        sel_node = nodes[self.level_sel]
        target_cy = max(0, sel_node[1] - SH // 2 + 40)
        if not hasattr(self, '_ls_cam_y'):
            self._ls_cam_y = 0.0
        self._ls_cam_y += (target_cy - self._ls_cam_y) * 0.12
        cy = int(self._ls_cam_y)

        # ── 5. Connecting path — soft glowing arcs between consecutive nodes
        for i in range(len(nodes) - 1):
            x1, y1 = nodes[i][0], nodes[i][1] - cy
            x2, y2 = nodes[i + 1][0], nodes[i + 1][1] - cy
            if (y1 > SH + 50 and y2 > SH + 50) or (y1 < -50 and y2 < -50):
                continue
            both_ul = (i + 1) in self.unlocked_levels and (i + 2) in self.unlocked_levels
            if both_ul:
                outer = (90, 220, 255, 70)
                core = (210, 240, 255, 220)
            else:
                outer = (80, 70, 110, 50)
                core = (130, 120, 160, 80)
            # Thick soft glow + thin crisp core for a "neon path" effect.
            pygame.draw.line(s, outer, (x1, y1), (x2, y2), 8)
            pygame.draw.line(s, core, (x1, y1), (x2, y2), 2)
            # Flowing energy pulse on unlocked segments.
            if both_ul:
                t_pulse = (tick * 0.012 + i * 0.32) % 1.0
                px = int(x1 + (x2 - x1) * t_pulse)
                py = int(y1 + (y2 - y1) * t_pulse)
                glow = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(glow, (180, 240, 255, 90), (12, 12), 11)
                pygame.draw.circle(glow, (255, 255, 255, 240), (12, 12), 4)
                s.blit(glow, (px - 12, py - 12),
                       special_flags=pygame.BLEND_RGBA_ADD)

        # ── 6. Level nodes — clean rings + soft glow ──
        level_themes = [
            "Khởi Đầu", "Tiến Quân", "Phục Kích", "Vượt Sa Mạc", "TƯỚNG SA MẠC",
            "Băng Giá", "Đột Kích", "Bao Vây", "Đầm Lầy", "TƯỚNG BĂNG GIÁ",
            "Rừng Sâu", "Vượt Đầm Lầy", "Phản Công", "Hang Núi", "TƯỚNG RỪNG RẬM",
            "Thành Phố", "Pháo Đài", "Tổng Tấn Công", "Cổng Địa Ngục", "TRẬM CUỐI - BOSS"
        ]

        for i in range(self.max_levels):
            lvl = i + 1
            nx, ny = nodes[i][0], nodes[i][1] - cy
            if ny < -40 or ny > SH + 40:
                continue
            is_ul = lvl in self.unlocked_levels
            is_sel = (i == self.level_sel)
            is_boss = (lvl % 5 == 0)

            if is_boss:
                accent = (255, 90, 170)
                accent_dim = (110, 50, 90)
            else:
                accent = (90, 220, 255)
                accent_dim = (60, 100, 140)

            base_r = 26 if is_sel else 22
            if is_boss:
                base_r += 4

            # Soft outer glow halo
            halo_r = base_r + (12 if is_sel else 6)
            halo = pygame.Surface((halo_r * 2 + 8, halo_r * 2 + 8), pygame.SRCALPHA)
            for r in range(halo_r, halo_r - 8, -1):
                a = max(0, 14 - (halo_r - r) * 2)
                if is_ul:
                    pygame.draw.circle(halo, (*accent, a),
                                       (halo_r + 4, halo_r + 4), r)
                else:
                    pygame.draw.circle(halo, (60, 50, 80, max(0, a - 4)),
                                       (halo_r + 4, halo_r + 4), r)
            s.blit(halo, (nx - halo_r - 4, ny - halo_r - 4),
                   special_flags=pygame.BLEND_RGBA_ADD)

            if is_sel and is_ul:
                pulse = abs(math.sin(tick * 0.1))
                pygame.draw.circle(s, (*accent, int(40 + 50 * pulse)),
                                   (nx, ny), int(base_r * 1.6), 2)

            if is_ul:
                # Inner disc with subtle radial fade
                disc = pygame.Surface((base_r * 2 + 4, base_r * 2 + 4),
                                      pygame.SRCALPHA)
                for r in range(base_r, 0, -1):
                    t = r / base_r
                    cr = int(18 + 6 * (1 - t))
                    cg = int(28 + 10 * (1 - t))
                    cb = int(56 + 30 * (1 - t))
                    pygame.draw.circle(disc, (cr, cg, cb, 240),
                                       (base_r + 2, base_r + 2), r)
                s.blit(disc, (nx - base_r - 2, ny - base_r - 2))
                # Outer ring
                pygame.draw.circle(s, accent, (nx, ny), base_r, 3)
                # Inner thin ring for depth
                pygame.draw.circle(s, (255, 255, 255, 80),
                                   (nx, ny), base_r - 4, 1)
                # Top-left highlight glint
                pygame.draw.circle(s, (255, 255, 255, 70),
                                   (nx - base_r // 3, ny - base_r // 3),
                                   base_r // 3)

                # Number
                num_font = FONT_BIG if is_sel else FONT_MED
                ns = num_font.render(str(lvl), True, (10, 10, 20))
                nt = num_font.render(str(lvl), True, (255, 255, 255))
                s.blit(ns, (nx - nt.get_width() // 2 + 1,
                            ny - nt.get_height() // 2 + 1))
                s.blit(nt, (nx - nt.get_width() // 2,
                            ny - nt.get_height() // 2))

                # Tiny BOSS crown indicator
                if is_boss:
                    cr = base_r - 2
                    crown_pts = [
                        (nx - 10, ny - cr - 10),
                        (nx - 6, ny - cr - 4),
                        (nx, ny - cr - 12),
                        (nx + 6, ny - cr - 4),
                        (nx + 10, ny - cr - 10),
                        (nx + 10, ny - cr - 2),
                        (nx - 10, ny - cr - 2),
                    ]
                    pygame.draw.polygon(s, (255, 200, 60), crown_pts)
                    pygame.draw.polygon(s, (180, 110, 20), crown_pts, 2)
            else:
                # Locked node
                disc = pygame.Surface((base_r * 2 + 4, base_r * 2 + 4),
                                      pygame.SRCALPHA)
                for r in range(base_r, 0, -1):
                    t = r / base_r
                    g = int(28 + 8 * (1 - t))
                    pygame.draw.circle(disc, (g, g, g + 10, 220),
                                       (base_r + 2, base_r + 2), r)
                s.blit(disc, (nx - base_r - 2, ny - base_r - 2))
                pygame.draw.circle(s, (110, 110, 130), (nx, ny), base_r, 2)
                # Padlock icon
                pygame.draw.rect(s, (180, 180, 200),
                                 (nx - 7, ny - 2, 14, 12), border_radius=2)
                pygame.draw.arc(s, (180, 180, 200),
                                (nx - 6, ny - 12, 12, 14),
                                0, math.pi, 3)

            # Level label below the node
            lbl_col = (220, 230, 240) if is_ul else (120, 120, 140)
            if is_sel:
                lbl_col = (255, 220, 90)
            lbl = FONT_SM.render(f"L.{lvl}", True, lbl_col)
            s.blit(lbl, (nx - lbl.get_width() // 2,
                          ny + base_r + 6))

            # Tank skin avatar above selected unlocked node
            if is_sel and is_ul:
                tier = min(len(sprites.player_tiers) - 1, self.skin_idx)
                td = (tick // 15) % 4
                ti = sprites.player_tiers[tier][td]
                tsz = 36
                ti = pygame.transform.smoothscale(ti, (tsz, tsz))
                bob = int(math.sin(tick * 0.12) * 4)
                # Drop shadow
                pygame.draw.ellipse(s, (0, 0, 0, 110),
                                    (nx - 14, ny - base_r - 6, 28, 6))
                s.blit(ti, (nx - tsz // 2,
                            ny - base_r - tsz - 6 + bob))
                pygame.draw.polygon(s, accent,
                                    [(nx - 5, ny - base_r - 2 + bob),
                                     (nx + 5, ny - base_r - 2 + bob),
                                     (nx, ny - base_r + 4 + bob)])

        # 7. Top Bar HUD (Currency display in premium Glass capsule)
        tb_w, tb_h = 270, 36
        tb_surf = pygame.Surface((tb_w, tb_h), pygame.SRCALPHA)
        pygame.draw.rect(tb_surf, (20, 10, 30, 170), (0, 0, tb_w, tb_h), border_radius=12)
        pygame.draw.rect(tb_surf, (0, 255, 255, 70), (0, 0, tb_w, tb_h), width=2, border_radius=12)
        s.blit(tb_surf, (12, 8))
        
        # Floating Gold and Gems icons
        float_top1 = int(math.sin(tick * 0.1) * 2)
        float_top2 = int(math.cos(tick * 0.1) * 2)
        
        # Gold display top
        draw_coin_icon(s, 24, 15 + float_top1, 20)
        ct = FONT_SM.render(f"{self.money:,}", True, (255, 235, 120))
        s.blit(ct, (48, 17))
        
        # Gems display top
        gx = 48 + ct.get_width() + 24
        draw_gem_icon(s, gx, 15 + float_top2, 20)
        gt = FONT_SM.render(f"{self.gems:,}", True, (140, 220, 255))
        s.blit(gt, (gx + 26, 17))

        # ── 7.5  MAP PREVIEW SIDE PANEL (right side) ──
        # Display a procedural thumbnail of the currently selected level's
        # theme — the player can see what the battlefield looks like before
        # committing.
        pv_w = right_panel_w - 30
        pv_x = SW - right_panel_w + 10
        pv_y = 60
        pv_h = SH - pv_y - 130

        chosen_lvl = self.level_sel + 1
        is_boss_p = (chosen_lvl % 5 == 0)
        accent_p = (255, 90, 170) if is_boss_p else (90, 220, 255)

        # Card surface — vertical gradient + rounded corners + clean border.
        pv_surf = pygame.Surface((pv_w, pv_h), pygame.SRCALPHA)
        top_c = (32, 42, 78)
        bot_c = (10, 16, 36)
        for ly in range(pv_h):
            tt = ly / max(1, pv_h - 1)
            r = int(top_c[0] * (1 - tt) + bot_c[0] * tt)
            g = int(top_c[1] * (1 - tt) + bot_c[1] * tt)
            b = int(top_c[2] * (1 - tt) + bot_c[2] * tt)
            pygame.draw.line(pv_surf, (r, g, b, 230), (0, ly), (pv_w, ly))
        mask = pygame.Surface((pv_w, pv_h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255),
                         (0, 0, pv_w, pv_h), border_radius=20)
        pv_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        pygame.draw.rect(pv_surf, (*accent_p, 220),
                         (0, 0, pv_w, pv_h), 2, border_radius=20)
        pygame.draw.rect(pv_surf, (255, 255, 255, 50),
                         (1, 1, pv_w - 2, pv_h - 2), 1, border_radius=19)
        s.blit(pv_surf, (pv_x, pv_y))

        # Header banner inside the card
        hdr_h = 38
        hdr = FONT_MED.render("DEMO BẢN ĐỒ", True, accent_p)
        hdr_sh = FONT_MED.render("DEMO BẢN ĐỒ", True, (15, 10, 20))
        s.blit(hdr_sh, (pv_x + pv_w // 2 - hdr.get_width() // 2 + 1,
                        pv_y + 11))
        s.blit(hdr, (pv_x + pv_w // 2 - hdr.get_width() // 2,
                     pv_y + 10))
        pygame.draw.line(s, (*accent_p, 200),
                         (pv_x + 16, pv_y + hdr_h),
                         (pv_x + pv_w - 16, pv_y + hdr_h), 1)

        # Thumbnail
        theme_p = self.get_theme_for_level(chosen_lvl)
        tname, sky, deco, wall, terrain, code = MAP_THEME_DEFS.get(
            theme_p, MAP_THEME_DEFS["default"])
        thumb_w = pv_w - 28
        thumb_h = int(thumb_w * 0.62)
        thumb = build_map_thumbnail(theme_p, thumb_w, thumb_h, chosen_lvl)
        thumb_x = pv_x + 14
        thumb_y = pv_y + hdr_h + 10
        # Soft glow behind the thumb
        glow = pygame.Surface((thumb_w + 16, thumb_h + 16), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*accent_p, 50),
                         (0, 0, thumb_w + 16, thumb_h + 16), border_radius=10)
        s.blit(glow, (thumb_x - 8, thumb_y - 8),
               special_flags=pygame.BLEND_RGBA_ADD)
        # Round-corner the thumbnail
        thumb_rc = pygame.Surface((thumb_w, thumb_h), pygame.SRCALPHA)
        thumb_rc.blit(thumb, (0, 0))
        thumb_mask = pygame.Surface((thumb_w, thumb_h), pygame.SRCALPHA)
        pygame.draw.rect(thumb_mask, (255, 255, 255, 255),
                         (0, 0, thumb_w, thumb_h), border_radius=8)
        thumb_rc.blit(thumb_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(thumb_rc, (thumb_x, thumb_y))
        pygame.draw.rect(s, accent_p,
                         (thumb_x, thumb_y, thumb_w, thumb_h), 2,
                         border_radius=8)

        # Boss / locked overlay
        if chosen_lvl not in self.unlocked_levels:
            ov = pygame.Surface((thumb_w, thumb_h), pygame.SRCALPHA)
            pygame.draw.rect(ov, (0, 0, 0, 180),
                             (0, 0, thumb_w, thumb_h), border_radius=8)
            s.blit(ov, (thumb_x, thumb_y))
            # Simple drawn padlock (avoids emoji font issues)
            lcx = thumb_x + thumb_w // 2
            lcy = thumb_y + thumb_h // 2 - 6
            pygame.draw.rect(s, (220, 200, 130),
                             (lcx - 16, lcy - 4, 32, 26), border_radius=4)
            pygame.draw.arc(s, (220, 200, 130),
                            (lcx - 12, lcy - 22, 24, 26), 0, math.pi, 4)
            lock_str = FONT_SM.render("CHƯA MỞ KHÓA", True, (255, 220, 120))
            s.blit(lock_str, (thumb_x + thumb_w // 2 - lock_str.get_width() // 2,
                              lcy + 28))
        elif is_boss_p:
            tag_w = 78
            tag_x = thumb_x + thumb_w - tag_w - 6
            tag_y = thumb_y + 6
            pygame.draw.rect(s, (255, 70, 130, 240),
                             (tag_x, tag_y, tag_w, 22), border_radius=11)
            pygame.draw.rect(s, (255, 255, 255, 200),
                             (tag_x, tag_y, tag_w, 22), 1, border_radius=11)
            bt = FONT_SM.render("BOSS", True, (255, 255, 255))
            s.blit(bt, (tag_x + (tag_w - bt.get_width()) // 2,
                        tag_y + (22 - bt.get_height()) // 2))

        # Info block below thumb
        info_y = thumb_y + thumb_h + 14
        tn1 = FONT_MED.render(tname, True, (255, 255, 255))
        s.blit(tn1, (pv_x + pv_w // 2 - tn1.get_width() // 2, info_y))
        ct = FONT_SM.render(f"CODE: {code}", True, (140, 200, 255))
        s.blit(ct, (pv_x + pv_w // 2 - ct.get_width() // 2, info_y + 26))
        tname2 = level_themes[self.level_sel] if self.level_sel < len(level_themes) else "Bí Ẩn"
        lt = FONT_SM.render(f"MÀN {chosen_lvl:02d}: {tname2}", True, (255, 220, 140))
        s.blit(lt, (pv_x + pv_w // 2 - lt.get_width() // 2, info_y + 48))

        # Difficulty pips
        diff_y = info_y + 78
        bar_w = pv_w - 40
        bar_x = pv_x + 20
        diff_count = max(1, (chosen_lvl - 1) // 5 + 1)
        diff_label = FONT_SM.render(
            f"Độ khó: {self.coop_difficulty_names[min(3, diff_count - 1)]}",
            True, (200, 220, 240))
        s.blit(diff_label,
               (pv_x + pv_w // 2 - diff_label.get_width() // 2, diff_y - 22))
        pip_w = (bar_w - 12) // 4
        for di in range(4):
            on = di < diff_count
            if on:
                col = ((100, 220, 130), (255, 220, 90),
                       (255, 160, 80), (255, 80, 110))[diff_count - 1]
            else:
                col = (60, 70, 95)
            pygame.draw.rect(s, col,
                             (bar_x + di * (pip_w + 4),
                              diff_y, pip_w, 10),
                             border_radius=5)
            pygame.draw.rect(s, (10, 14, 28),
                             (bar_x + di * (pip_w + 4),
                              diff_y, pip_w, 10), 1,
                             border_radius=5)

        # ── 8. Selected level HUD card (centre-bottom) ──
        card_w = 540
        card_h = 70
        card_x = (SW - right_panel_w) // 2 - card_w // 2 + 20
        card_y = SH - 130
        chosen = self.level_sel + 1
        can_play = chosen in self.unlocked_levels
        is_boss_c = (chosen % 5 == 0)
        accent_c = (255, 90, 170) if is_boss_c else (90, 220, 255)

        hud_panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        # Gradient body
        top_h = (24, 36, 70)
        bot_h = (10, 16, 36)
        for ly in range(card_h):
            tt = ly / max(1, card_h - 1)
            r = int(top_h[0] * (1 - tt) + bot_h[0] * tt)
            g = int(top_h[1] * (1 - tt) + bot_h[1] * tt)
            b = int(top_h[2] * (1 - tt) + bot_h[2] * tt)
            pygame.draw.line(hud_panel, (r, g, b, 220), (0, ly), (card_w, ly))
        mask = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255),
                         (0, 0, card_w, card_h), border_radius=16)
        hud_panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        pygame.draw.rect(hud_panel, (*accent_c, 220),
                         (0, 0, card_w, card_h), 2, border_radius=16)
        pygame.draw.rect(hud_panel, (255, 255, 255, 60),
                         (1, 1, card_w - 2, card_h - 2), 1, border_radius=15)
        # Left accent strip
        pygame.draw.rect(hud_panel, accent_c,
                         (6, 10, 4, card_h - 20), border_radius=2)
        s.blit(hud_panel, (card_x, card_y))

        # Mini level badge inside card
        bcx = card_x + 42
        bcy = card_y + card_h // 2
        pygame.draw.circle(s, (10, 14, 28), (bcx, bcy), 22)
        pygame.draw.circle(s, accent_c, (bcx, bcy), 22, 2)
        b_lbl = FONT_MED.render(str(chosen), True, (255, 255, 255))
        s.blit(b_lbl, (bcx - b_lbl.get_width() // 2,
                      bcy - b_lbl.get_height() // 2))

        # Level Info Text
        tn = level_themes[self.level_sel] if self.level_sel < len(level_themes) else "Kỳ Ải Bí Ẩn"
        if can_play:
            status_txt = f"MÀN {chosen:02d}: {tn.upper()}"
            status_color = accent_c
            hint_txt = "Ấn [ENTER] hoặc CHIẾN để bắt đầu trận đấu!"
        else:
            status_txt = f"MÀN {chosen:02d}: CHƯA MỞ KHÓA"
            status_color = (255, 90, 100)
            hint_txt = "Hãy vượt qua các màn trước để mở khóa màn này!"

        t_status_shadow = FONT_MED.render(status_txt, True, (10, 10, 15))
        t_status = FONT_MED.render(status_txt, True, status_color)
        text_x = card_x + 78
        s.blit(t_status_shadow, (text_x + 1, card_y + 11))
        s.blit(t_status, (text_x, card_y + 10))
        t_hint = FONT_SM.render(hint_txt, True,
                                (200, 210, 230) if can_play else (255, 140, 140))
        s.blit(t_hint, (text_x, card_y + 40))

        # 9. Bottom Navigation Bar (Back and Play/Chiến buttons in gorgeous capsule style)
        bh = 48
        bb = pygame.Surface((SW, bh), pygame.SRCALPHA)
        pygame.draw.rect(bb, (15, 10, 25, 220), (0, 0, SW, bh))
        pygame.draw.line(bb, (0, 255, 255, 80), (0, 0), (SW, 0), 1)
        s.blit(bb, (0, SH - bh))

        # A. Back button (bottom-left with 3D drop shadow)
        back_rect = pygame.Rect(12, SH - 42, 140, 36)
        pygame.draw.rect(s, (5, 3, 10, 150), (15, SH - 39, 140, 36), border_radius=8)
        pygame.draw.rect(s, (20, 10, 30, 170), back_rect, border_radius=8)
        pygame.draw.rect(s, (255, 80, 80, 160), back_rect, width=2, border_radius=8)
        pygame.draw.rect(s, (255, 255, 255, 45), (13, SH - 41, 138, 34), width=1, border_radius=7)
        
        # Arrow symbol
        pygame.draw.polygon(s, (255, 80, 80), [(22, SH - 24), (32, SH - 30), (32, SH - 18)])
        back_t = FONT_SM.render("QUAY LẠI", True, (255, 255, 255))
        s.blit(back_t, (44, SH - 24 - back_t.get_height() // 2))

        # B. Play button (bottom-right with 3D drop shadow)
        pw, ph = 110, 36
        px = SW - pw - 12
        py = SH - bh + 6
        
        play_btn_color = (0, 200, 100) if can_play else (80, 60, 60)
        play_border_color = (0, 255, 128) if can_play else (100, 80, 80)
        
        pygame.draw.rect(s, (5, 3, 10, 150), (px + 3, py + 3, pw, ph), border_radius=8)
        pygame.draw.rect(s, play_btn_color, (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(s, play_border_color, (px, py, pw, ph), width=2, border_radius=8)
        pygame.draw.rect(s, (255, 255, 255, 45), (px + 1, py + 1, pw - 2, ph - 2), width=1, border_radius=7)
        
        # Play triangle symbol
        if can_play:
            pygame.draw.polygon(s, (255, 255, 255), [(px + 16, py + ph // 2 - 7), (px + 16, py + ph // 2 + 7), (px + 26, py + ph // 2)])
            play_lbl = "CHIẾN !"
        else:
            play_lbl = "KHOÁ"
            
        play_t = FONT_MED.render(play_lbl, True, (255, 255, 255))
        s.blit(play_t, (px + pw // 2 + (4 if can_play else 0) - play_t.get_width() // 2, py + ph // 2 - play_t.get_height() // 2))
        
        # Navigation guide bottom text
        ht = FONT_SM.render("[TRAI/PHẢI] chọn  [ENTER] bắt đầu chiến đấu  [ESC] quay lại", True, (150, 150, 170))
        s.blit(ht, (SW // 2 - ht.get_width() // 2, SH - bh + 16))
        return

    def _draw_level_select_image_mode(self):
        """Image-mode level select: paint the world-map artwork, overlay
        a thin pulsing highlight on the selected tile, lock-icon over
        levels not yet unlocked, and a parchment-style detail panel on
        the right showing the selected map's info.  All 20 tile rects
        plus BACK / VÀO TRẬN ĐẤU are invisible click zones tuned to the
        baked-in artwork — there is no other UI chrome painted on top."""
        s = self._surf
        tick = self.tick

        # 1) Background artwork
        s.blit(self.level_select_bg, (0, 0))

        # 2) Per-tile overlay (lock for locked, glow for selected)
        tiles = self._level_select_tile_rects()
        mx_phys, my_phys = pygame.mouse.get_pos()
        mx = int(mx_phys * (SW / phys_w))
        my = int(my_phys * (SH / phys_h))

        for i, r in enumerate(tiles):
            lvl = i + 1
            is_unlocked = lvl in self.unlocked_levels
            is_sel = (i == self.level_sel)
            is_hover = r.collidepoint(mx, my)

            if not is_unlocked:
                # Strong dark veil so the locked map is clearly inactive.
                veil = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                veil.fill((0, 0, 0, 200))
                s.blit(veil, r.topleft)
                # Inner dim border to feel "frozen out"
                pygame.draw.rect(s, (40, 40, 60, 220),
                                 r.inflate(-4, -4), 2, border_radius=4)

                # Detailed padlock icon — drop shadow, brass body, shaded
                # shackle, riveted keyhole.  Scaled to ~half the tile.
                lcx, lcy = r.centerx, r.centery
                base = max(12, min(r.w, r.h) // 4)   # body half-width
                body_w = base * 2
                body_h = int(base * 1.6)
                body_top = lcy + body_h // 8
                body_rect = pygame.Rect(lcx - body_w // 2,
                                        body_top - body_h // 2,
                                        body_w, body_h)
                # Shadow
                sh = pygame.Surface((body_rect.w + 6, body_rect.h + 6),
                                    pygame.SRCALPHA)
                pygame.draw.rect(sh, (0, 0, 0, 140),
                                 (3, 3, body_rect.w, body_rect.h),
                                 border_radius=6)
                s.blit(sh, (body_rect.x - 3, body_rect.y - 3))
                # Shackle (top hoop) — drawn ABOVE the body as 2 arcs
                shackle_w = int(body_w * 0.75)
                shackle_h = int(body_h * 0.95)
                shackle_rect = pygame.Rect(lcx - shackle_w // 2,
                                           body_rect.top - shackle_h // 2 - 2,
                                           shackle_w, shackle_h)
                # Outer (dark) shackle
                pygame.draw.arc(s, (60, 60, 70),
                                shackle_rect, math.pi, 2 * math.pi,
                                max(4, body_h // 6))
                # Inner highlight on the shackle
                inner_shackle = shackle_rect.inflate(-4, -4)
                pygame.draw.arc(s, (170, 175, 185),
                                inner_shackle, math.pi + 0.15,
                                2 * math.pi - 0.15,
                                max(2, body_h // 12))
                # Body — brass gradient (top lighter, bottom darker)
                for j in range(body_rect.h):
                    t = j / max(1, body_rect.h - 1)
                    rr = int(230 - 70 * t)
                    gg = int(180 - 60 * t)
                    bb = int(60  - 30 * t)
                    pygame.draw.line(s, (rr, gg, bb),
                                     (body_rect.x, body_rect.y + j),
                                     (body_rect.right, body_rect.y + j))
                pygame.draw.rect(s, (90, 60, 10), body_rect, 2,
                                 border_radius=4)
                # Inner bevel
                pygame.draw.rect(s, (255, 230, 130),
                                 body_rect.inflate(-4, -4), 1,
                                 border_radius=3)
                # Keyhole — circle + tail
                khr = max(3, body_h // 6)
                kh_cy = body_rect.centery - body_h // 8
                pygame.draw.circle(s, (50, 30, 5),
                                   (lcx, kh_cy), khr)
                pygame.draw.polygon(s, (50, 30, 5),
                                    [(lcx - max(2, khr // 2), kh_cy),
                                     (lcx + max(2, khr // 2), kh_cy),
                                     (lcx + max(1, khr // 3),
                                      kh_cy + khr + max(4, khr))])

            if is_sel:
                # Big, easy-to-see pulsing highlight that surrounds the
                # painted tile — outer halo + thick yellow border +
                # inner thin white outline + corner brackets.
                pulse = (math.sin(tick * 0.12) + 1) * 0.5
                core_col = (255, 230 + int(pulse * 25),
                                  90 + int(pulse * 60))
                # 1) Outer glow halo
                halo = pygame.Surface((r.w + 40, r.h + 40), pygame.SRCALPHA)
                for k in range(6, 0, -1):
                    a = int(35 + 25 * pulse) - k * 4
                    if a <= 0:
                        continue
                    pygame.draw.rect(halo,
                                     (255, 220, 90, a),
                                     (20 - k * 3, 20 - k * 3,
                                      r.w + k * 6, r.h + k * 6),
                                     border_radius=12)
                s.blit(halo, (r.x - 20, r.y - 20))
                # 2) Thick main border (hugs tile +6 px each side)
                pygame.draw.rect(s, core_col, r.inflate(12, 12), 5,
                                 border_radius=10)
                # 3) Inner thin white outline
                pygame.draw.rect(s, (255, 255, 255),
                                 r.inflate(2, 2), 2, border_radius=6)
                # 4) Corner brackets (arcade feel)
                cl = 18
                for cx, cy, dx, dy in (
                    (r.left  - 8,  r.top    - 8,  1,  1),
                    (r.right + 8,  r.top    - 8, -1,  1),
                    (r.left  - 8,  r.bottom + 8,  1, -1),
                    (r.right + 8,  r.bottom + 8, -1, -1),
                ):
                    pygame.draw.line(s, core_col, (cx, cy),
                                     (cx + dx * cl, cy), 5)
                    pygame.draw.line(s, core_col, (cx, cy),
                                     (cx, cy + dy * cl), 5)
            elif is_hover and is_unlocked:
                pygame.draw.rect(s, (255, 255, 255),
                                 r.inflate(6, 6), 3, border_radius=6)

        # 3) Right detail panel.  The parchment artwork has two inset
        # cream/wood boxes: a small one at the top (header) and a tall
        # one filling the rest (body).  We render text directly inside
        # those rects so nothing overlaps the painted wood frame.
        hdr_rect  = self._LS_HEADER_RECT
        body_rect = self._LS_BODY_RECT

        # Tinted cream panels so text contrasts strongly against the
        # darker baked-in wood — looks like an in-game scroll, not a
        # transparent overlay.
        hdr_bg = pygame.Surface((hdr_rect.w, hdr_rect.h), pygame.SRCALPHA)
        hdr_bg.fill((255, 235, 175, 230))
        s.blit(hdr_bg, hdr_rect.topleft)
        pygame.draw.rect(s, (140, 80, 30), hdr_rect, 3, border_radius=6)

        body_bg = pygame.Surface((body_rect.w, body_rect.h),
                                 pygame.SRCALPHA)
        body_bg.fill((255, 235, 175, 220))
        s.blit(body_bg, body_rect.topleft)
        pygame.draw.rect(s, (140, 80, 30), body_rect, 3, border_radius=8)

        lvl_idx = max(0, min(self.max_levels - 1, self.level_sel))
        lvl_num = lvl_idx + 1
        # Each map matches the painted preview on the world-map artwork.
        themes = [
            "Khởi Đầu",        "Tiến Quân",       "Sa Mạc",
            "Pháo Đài Đá",    "TƯỚNG PHÁO ĐÀI",
            "Khe Núi",         "Vượt Sông",       "Rừng Hoang",
            "Cao Nguyên",      "TƯỚNG ĐÔ THỊ",
            "Làng Quê",        "Cầu Cổng",        "Bản Làng",
            "Núi Tuyết",       "TƯỚNG SÔNG NGÒI",
            "Phế Tích",        "Băng Tuyết",      "Cổng Thành",
            "Hoang Mạc",       "TRẬN CUỐI - HỎA NGỤC",
        ]
        # Codes mirror get_theme_for_level so the in-game terrain matches
        # the preview the player saw on this screen.
        codes = [
            "JUNGLE", "DEFAULT", "DESERT", "CITY",   "CITY-BOSS",
            "JUNGLE", "DEFAULT", "JUNGLE", "DEFAULT", "CITY-BOSS",
            "JUNGLE", "DEFAULT", "JUNGLE", "SNOW",   "DEFAULT-BOSS",
            "CITY",   "SNOW",   "CITY",   "DESERT", "LAVA-BOSS",
        ]
        is_boss = (lvl_num % 5 == 0)
        is_unlocked = lvl_num in self.unlocked_levels

        try:
            f_big = pygame.font.SysFont("consolas", 28, bold=True)
            f_med = pygame.font.SysFont("consolas", 18, bold=True)
            f_sm  = pygame.font.SysFont("consolas", 14, bold=True)
            # The star glyph (U+2605) is not available in consolas on
            # every system, so pick a font that supports it for the
            # BOSS badge.
            f_star = pygame.font.SysFont(
                "dejavusans,arial,segoeuisymbol", 18, bold=True)
        except Exception:
            f_big = FONT_BIG
            f_med = FONT_MED
            f_sm  = FONT_SM
            f_star = FONT_MED

        # Header — big "MÀN xx" + theme name, dark text on cream bg
        title_col = (90, 40, 10)
        sub_col   = (180, 30, 30) if is_boss else (60, 30, 10)
        t1 = f_big.render(f"MÀN {lvl_num:02d}", True, title_col)
        s.blit(t1, (hdr_rect.x + (hdr_rect.w - t1.get_width()) // 2,
                    hdr_rect.y + 8))
        t2 = f_med.render(themes[lvl_idx], True, sub_col)
        s.blit(t2, (hdr_rect.x + (hdr_rect.w - t2.get_width()) // 2,
                    hdr_rect.y + 42))

        # Body — code, status, difficulty, hint
        bx = body_rect.x + 18
        by = body_rect.y + 18

        def _row(label, value, value_col=(80, 35, 10), bold=True):
            nonlocal by
            l = f_sm.render(label, True, (130, 60, 10))
            v = f_med.render(value, True, value_col)
            s.blit(l, (bx, by))
            s.blit(v, (bx, by + 20))
            by += 64

        if is_boss:
            badge_bg = pygame.Surface((body_rect.w - 36, 32),
                                      pygame.SRCALPHA)
            badge_bg.fill((255, 215, 0, 230))
            s.blit(badge_bg, (bx, by))
            badge = f_star.render("★ BOSS ★", True, (140, 60, 0))
            s.blit(badge,
                   (bx + (body_rect.w - 36 - badge.get_width()) // 2,
                    by + 6))
            by += 44

        _row("MÃ ĐỊA HÌNH", codes[lvl_idx])
        if is_unlocked:
            _row("TRẠNG THÁI", "ĐÃ MỞ KHÓA", (30, 110, 30))
        else:
            _row("TRẠNG THÁI", "CHƯA MỞ KHÓA", (160, 30, 30))
        if is_boss:
            diff = "RẤT KHÓ" if lvl_num >= 15 else "KHÓ"
        else:
            diff = ("DỄ" if lvl_num <= 5
                    else ("TRUNG BÌNH" if lvl_num <= 12 else "KHÓ"))
        diff_col = (160, 30, 30) if is_boss else (30, 60, 130)
        _row("ĐỘ KHÓ", diff, diff_col)

        # Stars row (visual difficulty meter)
        n_stars = 1 + (lvl_num - 1) // 4
        n_stars = max(1, min(5, n_stars))
        star_y = by + 4
        # Label above stars
        ls = f_sm.render("ĐỘ KHÓ ĐÁNH GIÁ", True, (130, 60, 10))
        s.blit(ls, (bx, star_y - 18))
        for i in range(5):
            sx = bx + i * 30
            col = (255, 200, 0) if i < n_stars else (160, 130, 80)
            pts = []
            for k in range(10):
                a = -math.pi / 2 + k * math.pi / 5
                r2 = 11 if k % 2 == 0 else 4
                pts.append((sx + 11 + math.cos(a) * r2,
                            star_y + 11 + math.sin(a) * r2))
            pygame.draw.polygon(s, col, pts)
            pygame.draw.polygon(s, (90, 50, 0), pts, 1)
        by = star_y + 40

        # Tip at the bottom of the panel
        tip_lines = [
            ("Click VÀO TRẬN ĐẤU để bắt đầu" if is_unlocked
             else "Hoàn thành màn trước để mở khóa"),
            "[ENTER] vào trận    [ESC] quay lại",
        ]
        for k, line in enumerate(tip_lines):
            tip = f_sm.render(line, True, (110, 60, 10))
            s.blit(tip,
                   (body_rect.x + (body_rect.w - tip.get_width()) // 2,
                    body_rect.bottom - 44 + k * 18))

    def draw_level_start(self):
        self.draw_game()
        s = pygame.Surface((SW, SH), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))

        # Theme name
        theme_names = {"default": "CHIẾN TRƯỜNG", "desert": "SA MẠC", "snow": "BĂNG GIÁ",
                      "city": "THÀNH PHỐ", "jungle": "RỪNG RẬM", "lava": "NÚI LỬA",
                      "kawaii_woodland": "RỪNG KAWAII"}
        theme_name = theme_names.get(self.map_theme, "CHIẾN TRƯỜNG")

        # Level number
        lvl_t = FONT_HUGE.render(f"MÀN {self.level}", True, (255, 220, 50))
        shadow = FONT_HUGE.render(f"MÀN {self.level}", True, (100, 80, 0))
        s.blit(shadow, (SW // 2 - lvl_t.get_width() // 2 + 3, SH // 2 - 100 + 3))
        s.blit(lvl_t, (SW // 2 - lvl_t.get_width() // 2, SH // 2 - 100))

        # Theme
        theme_t = FONT_MED.render(f"ĐỊA HÌNH: {theme_name}", True, (180, 200, 255))
        s.blit(theme_t, (SW // 2 - theme_t.get_width() // 2, SH // 2 - 40))

        # Mission
        if self.mission_text:
            bg_rect = pygame.Rect(20, SH // 2, SW - 40, 45)
            pygame.draw.rect(s, (150, 30, 30, 200), bg_rect, border_radius=8)
            txt = FONT_MED.render(self.mission_text, True, (255, 255, 150))
            s.blit(txt, (SW // 2 - txt.get_width() // 2, SH // 2 + 10))

        # Boss warning
        if self.level % 5 == 0:
            pulse = abs(math.sin(self.tick * 0.15))
            warn_c = (255, int(50 + 200 * pulse), int(50 * pulse))
            warn_t = FONT_BIG.render("!! BOSS XUẤT HIỆN !!", True, warn_c)
            s.blit(warn_t, (SW // 2 - warn_t.get_width() // 2, SH // 2 + 55))

        pulse = abs(math.sin(self.tick * 0.1))
        instr = FONT_MED.render("NHẤN [ SPACE ] ĐỂ BẮT ĐẦU", True, (int(150 + pulse * 105), int(180 + pulse * 75), 255))
        s.blit(instr, (SW // 2 - instr.get_width() // 2, SH // 2 + 100))

        self._surf.blit(s, (0, 0))

    # Title menu click-rect layout.  These hug the baked-in buttons of the
    # lobby video so the player can click directly on the artwork without
    # any visible overlay.
    #   (label, pygame.Rect, menu_index)
    _TITLE_BUTTON_LAYOUT_RECTS = [
        ("CHIẾN ĐẤU",          pygame.Rect(30,   125, 320, 80),  0),
        ("SHOP",                pygame.Rect(50,   210, 290, 80),  1),
        ("GA-RA",               pygame.Rect(50,   295, 290, 80),  2),
        ("CHƠI MẠNG (PVP)",    pygame.Rect(40,   380, 310, 80),  3),
        ("CHƠI CHUNG (CO-OP)", pygame.Rect(45,   470, 305, 80),  4),
        ("VÒNG QUAY",          pygame.Rect(45,   555, 305, 85),  5),
        ("GEAR",                pygame.Rect(1095, 535, 185, 185), 6),
    ]

    def _title_button_rects(self):
        """Yield (label, rect, menu_index) for the title menu — invisible
        hit-zones over the baked-in buttons of the lobby video."""
        for label, rect, midx in self._TITLE_BUTTON_LAYOUT_RECTS:
            yield label, rect, midx

    # ────────────────────────────────────────────────────────────────
    #  LEVEL-SELECT (world-map image) HIT ZONES
    # ────────────────────────────────────────────────────────────────
    # Pixel-precise coordinates measured from the actual 1280×720
    # artwork via edge detection on each painted tile + the parchment
    # frame and BACK/VÀO TRẬN ĐẤU buttons.  Each row has its own height
    # because the cards are laid out organically across the terrain.
    _LS_COL_X = (73, 238, 406, 572, 739)   # left edge of each column
    _LS_COL_W = 134                          # uniform tile width
    _LS_ROW_Y = (28, 158, 315, 465)          # top edge of each row
    _LS_ROW_H = (102, 94, 92, 95)            # height of each row
    _LS_BACK_RECT  = pygame.Rect(15,  625, 210, 90)
    _LS_PLAY_RECT  = pygame.Rect(900, 620, 365, 95)
    _LS_PANEL_RECT = pygame.Rect(890,  18, 380, 590)
    # Inner cream boxes inside the parchment frame for placing text.
    _LS_HEADER_RECT = pygame.Rect(905,  40, 350, 75)
    _LS_BODY_RECT   = pygame.Rect(905, 130, 350, 470)

    def _level_select_tile_rects(self):
        rects = []
        for i in range(self.max_levels):
            col = i % 5
            row = i // 5
            x = self._LS_COL_X[col]
            y = self._LS_ROW_Y[row]
            rects.append(pygame.Rect(x, y, self._LS_COL_W,
                                     self._LS_ROW_H[row]))
        return rects

    def _level_select_back_rect(self):
        return self._LS_BACK_RECT

    def _level_select_play_rect(self):
        return self._LS_PLAY_RECT

    def _draw_title_overlays(self, s, tick):
        """Opaque profile + currency panels that fully cover the baked-in
        UI in the lobby video so the player's real avatar/name/balance/
        XP/streak/coins/gems shows through on top — with animated cyber
        effects (scan-line + sparkle + pulse)."""

        pulse = (math.sin(tick * 0.07) + 1) * 0.5  # 0..1
        # Scan-line position (loops left → right every ~4 sec)
        scan_t = (tick % 240) / 240.0

        def _gradient_panel(rect, c_top, c_bot):
            for j in range(rect.h):
                t = j / max(1, rect.h - 1)
                rr = int(c_top[0] * (1 - t) + c_bot[0] * t)
                gg = int(c_top[1] * (1 - t) + c_bot[1] * t)
                bb = int(c_top[2] * (1 - t) + c_bot[2] * t)
                pygame.draw.line(s, (rr, gg, bb),
                                 (rect.x, rect.y + j),
                                 (rect.right, rect.y + j))

        def _scan_line(rect, color, alpha=80):
            x = rect.x + int(rect.w * scan_t)
            band = pygame.Surface((28, rect.h), pygame.SRCALPHA)
            for k in range(28):
                a = int(alpha * (1 - abs(k - 14) / 14.0))
                if a > 0:
                    pygame.draw.line(band, (*color, a), (k, 0), (k, rect.h))
            # Clip the band so it never spills outside the panel.
            sx = max(rect.x, x - 14)
            ex = min(rect.right, x + 14)
            if ex > sx:
                clip = pygame.Rect(sx - (x - 14), 0, ex - sx, rect.h)
                s.blit(band.subsurface(clip), (sx, rect.y))

        def _sparkles(rect, color):
            for si in range(5):
                ph = (tick * 0.05 + si * 1.7) % (2 * math.pi)
                a = int(40 + 80 * (math.sin(ph) + 1) * 0.5)
                sx = rect.x + 12 + int((si * 73 + tick * 0.6) % (rect.w - 24))
                sy = rect.y + 4 + (si * 17) % (rect.h - 8)
                d = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(d, (*color, a), (3, 3), 3)
                pygame.draw.circle(d, (255, 255, 255, min(255, a + 80)),
                                   (3, 3), 1)
                s.blit(d, (sx, sy))

        # ╔══════════════════ TOP-LEFT: PROFILE PANEL ══════════════════╗
        L_RECT = pygame.Rect(0, 0, 360, 112)
        _gradient_panel(L_RECT, (18, 26, 50), (8, 14, 32))
        # Inner sheen
        sheen = pygame.Surface((L_RECT.w, L_RECT.h // 2), pygame.SRCALPHA)
        sheen.fill((255, 255, 255, 14))
        s.blit(sheen, L_RECT.topleft)

        # Animated cyan border
        border_l = (0, int(200 + 55 * pulse), int(220 + 35 * pulse))
        pygame.draw.rect(s, border_l, L_RECT, 3, border_radius=14)
        pygame.draw.rect(s, (255, 255, 255), L_RECT.inflate(-4, -4), 1,
                         border_radius=12)
        # Corner accent brackets
        for cx, cy, dx, dy in (
            (L_RECT.left + 6, L_RECT.top + 6, 1, 1),
            (L_RECT.right - 6, L_RECT.top + 6, -1, 1),
            (L_RECT.left + 6, L_RECT.bottom - 6, 1, -1),
            (L_RECT.right - 6, L_RECT.bottom - 6, -1, -1),
        ):
            pygame.draw.line(s, border_l, (cx, cy),
                             (cx + dx * 14, cy), 3)
            pygame.draw.line(s, border_l, (cx, cy),
                             (cx, cy + dy * 14), 3)

        _scan_line(L_RECT, (0, 240, 255), 70)
        _sparkles(L_RECT, (120, 220, 255))

        # Avatar plaque
        av_r = 38
        av_cx = L_RECT.x + 14 + av_r
        av_cy = L_RECT.centery
        # Outer ring (rotating arc for life)
        ring_a = (tick * 2) % 360
        for k in range(3):
            start = math.radians(ring_a + k * 120)
            end = start + math.radians(60)
            pygame.draw.arc(s, border_l,
                            (av_cx - av_r - 5, av_cy - av_r - 5,
                             (av_r + 5) * 2, (av_r + 5) * 2),
                            start, end, 3)
        pygame.draw.circle(s, (8, 12, 24), (av_cx, av_cy), av_r + 2)
        pygame.draw.circle(s, (22, 32, 60), (av_cx, av_cy), av_r)
        tier_idx = max(0, min(len(sprites.player_tiers) - 1,
                              getattr(self, "player_tier", 0)))
        try:
            tank_img = sprites.player_tiers[tier_idx][0]
            tank_scaled = pygame.transform.smoothscale(
                tank_img, (av_r * 2 - 6, av_r * 2 - 6))
            s.blit(tank_scaled, (av_cx - av_r + 3, av_cy - av_r + 3))
        except Exception:
            pygame.draw.rect(s, (200, 220, 80),
                             (av_cx - 14, av_cy - 14, 28, 28),
                             border_radius=6)

        # Right column of profile info
        col_x = av_cx + av_r + 14
        # Name
        name_t = FONT_MED.render(getattr(self, "player_name", "Player"),
                                 True, (230, 245, 255))
        s.blit(name_t, (col_x, L_RECT.y + 10))

        # Cấp badge + provider
        cap_lbl = "Cấp " + str(tier_idx + 1)
        badge = FONT_SM.render(cap_lbl, True, (10, 20, 40))
        bw = badge.get_width() + 14
        bh = badge.get_height() + 4
        bx = col_x
        by = L_RECT.y + 10 + name_t.get_height() + 2
        pygame.draw.rect(s, (255, 210, 80), (bx, by, bw, bh),
                         border_radius=8)
        pygame.draw.rect(s, (180, 130, 20), (bx, by, bw, bh), 1,
                         border_radius=8)
        s.blit(badge, (bx + 7, by + 2))

        prov = getattr(self, "login_provider", None)
        if prov:
            prov_t = FONT_SM.render("@" + str(prov).title(),
                                    True, (180, 220, 240))
            s.blit(prov_t, (bx + bw + 8, by + 2))

        # XP / progress bar (use unlocked_levels / 20 as a proxy)
        unlocked = len(getattr(self, "unlocked_levels", {1}) or {1})
        progress = min(1.0, unlocked / 20.0)
        bar_x = col_x
        bar_y = by + bh + 6
        bar_w = L_RECT.right - bar_x - 14
        bar_h = 10
        pygame.draw.rect(s, (10, 16, 30), (bar_x, bar_y, bar_w, bar_h),
                         border_radius=5)
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            # Cyan→magenta gradient fill
            for k in range(fill_w):
                t = k / max(1, fill_w - 1)
                rr = int(0   * (1 - t) + 255 * t)
                gg = int(240 * (1 - t) + 80  * t)
                bb = int(255 * (1 - t) + 200 * t)
                pygame.draw.line(s, (rr, gg, bb),
                                 (bar_x + k, bar_y + 1),
                                 (bar_x + k, bar_y + bar_h - 1))
        pygame.draw.rect(s, border_l, (bar_x, bar_y, bar_w, bar_h), 1,
                         border_radius=5)
        prog_t = FONT_SM.render(f"{unlocked}/20", True, (220, 240, 255))
        s.blit(prog_t, (bar_x + bar_w - prog_t.get_width() - 6,
                        bar_y - prog_t.get_height() - 1))

        # ╔══════════════════ TOP-RIGHT: CURRENCY PANEL ════════════════╗
        R_RECT = pygame.Rect(SW - 360, 0, 360, 112)
        _gradient_panel(R_RECT, (50, 30, 18), (28, 16, 8))
        sheen2 = pygame.Surface((R_RECT.w, R_RECT.h // 2), pygame.SRCALPHA)
        sheen2.fill((255, 255, 255, 14))
        s.blit(sheen2, R_RECT.topleft)

        border_r = (int(240 + 15 * pulse), int(180 + 60 * pulse), 50)
        pygame.draw.rect(s, border_r, R_RECT, 3, border_radius=14)
        pygame.draw.rect(s, (255, 255, 255), R_RECT.inflate(-4, -4), 1,
                         border_radius=12)
        for cx, cy, dx, dy in (
            (R_RECT.left + 6, R_RECT.top + 6, 1, 1),
            (R_RECT.right - 6, R_RECT.top + 6, -1, 1),
            (R_RECT.left + 6, R_RECT.bottom - 6, 1, -1),
            (R_RECT.right - 6, R_RECT.bottom - 6, -1, -1),
        ):
            pygame.draw.line(s, border_r, (cx, cy),
                             (cx + dx * 14, cy), 3)
            pygame.draw.line(s, border_r, (cx, cy),
                             (cx, cy + dy * 14), 3)

        _scan_line(R_RECT, (255, 220, 90), 70)
        _sparkles(R_RECT, (255, 230, 120))

        gold = int(getattr(self, "money", 0))
        gems = int(getattr(self, "gems", 0))

        def _format_compact(n):
            if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
            if n >= 10_000:    return f"{n/1000:.1f}K"
            return f"{n:,}"

        # Gold row
        g_cx = R_RECT.x + 30
        g_cy = R_RECT.y + 30
        # Pulsing halo behind coin
        for k in range(3):
            a = int(45 - k * 12)
            if a > 0:
                halo = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 200, 80, a), (20, 20),
                                   16 + k * 3)
                s.blit(halo, (g_cx - 20, g_cy - 20))
        pygame.draw.circle(s, (255, 220, 70), (g_cx, g_cy), 14)
        pygame.draw.circle(s, (180, 130, 20), (g_cx, g_cy), 14, 2)
        pygame.draw.circle(s, (255, 245, 140), (g_cx - 4, g_cy - 4), 4)
        try:
            star_pts = []
            for ai in range(5):
                ang = -math.pi / 2 + ai * (2 * math.pi / 5)
                star_pts.append((g_cx + 8 * math.cos(ang),
                                 g_cy + 8 * math.sin(ang)))
                ang2 = ang + math.pi / 5
                star_pts.append((g_cx + 4 * math.cos(ang2),
                                 g_cy + 4 * math.sin(ang2)))
            pygame.draw.polygon(s, (180, 130, 20), star_pts)
        except Exception:
            pass
        gold_t = FONT_MED.render(_format_compact(gold), True, (255, 235, 150))
        s.blit(gold_t, (g_cx + 22, g_cy - gold_t.get_height() // 2))

        # "+" nạp button
        plus_r = pygame.Rect(R_RECT.right - 34, g_cy - 12, 24, 24)
        pygame.draw.rect(s, (60, 180, 90), plus_r, border_radius=6)
        pygame.draw.rect(s, (200, 255, 200), plus_r, 1, border_radius=6)
        plus_t = FONT_MED.render("+", True, (10, 30, 10))
        s.blit(plus_t, (plus_r.centerx - plus_t.get_width() // 2,
                        plus_r.centery - plus_t.get_height() // 2 - 2))
        self._title_plus_gold_rect = plus_r

        # Gems row
        gm_cx = R_RECT.x + 30
        gm_cy = R_RECT.y + 64
        for k in range(3):
            a = int(40 - k * 11)
            if a > 0:
                halo = pygame.Surface((36, 36), pygame.SRCALPHA)
                pygame.draw.circle(halo, (80, 180, 255, a), (18, 18),
                                   12 + k * 3)
                s.blit(halo, (gm_cx - 18, gm_cy - 18))
        diamond = [(gm_cx, gm_cy - 12), (gm_cx + 10, gm_cy),
                   (gm_cx, gm_cy + 12), (gm_cx - 10, gm_cy)]
        pygame.draw.polygon(s, (90, 220, 255), diamond)
        pygame.draw.polygon(s, (200, 240, 255), [(gm_cx, gm_cy - 12),
                                                  (gm_cx + 4, gm_cy - 4),
                                                  (gm_cx, gm_cy + 2),
                                                  (gm_cx - 4, gm_cy - 4)])
        pygame.draw.polygon(s, (40, 130, 200), diamond, 2)
        gems_t = FONT_MED.render(_format_compact(gems), True, (180, 230, 255))
        s.blit(gems_t, (gm_cx + 22, gm_cy - gems_t.get_height() // 2))

        plus_r2 = pygame.Rect(R_RECT.right - 34, gm_cy - 12, 24, 24)
        pygame.draw.rect(s, (60, 180, 90), plus_r2, border_radius=6)
        pygame.draw.rect(s, (200, 255, 200), plus_r2, 1, border_radius=6)
        s.blit(plus_t, (plus_r2.centerx - plus_t.get_width() // 2,
                        plus_r2.centery - plus_t.get_height() // 2 - 2))
        self._title_plus_gems_rect = plus_r2

        # Daily streak chip in the centre between rows
        streak = int(getattr(self, "daily_streak",
                             len(getattr(self, "unlocked_levels", {1}) or {1})))
        chip_x = R_RECT.x + 168
        chip_y = R_RECT.y + 18
        chip = pygame.Rect(chip_x, chip_y, 110, 24)
        pygame.draw.rect(s, (60, 30, 14), chip, border_radius=10)
        pygame.draw.rect(s, (255, 140, 40), chip, 1, border_radius=10)
        # Flame icon
        fx = chip.x + 12
        fy = chip.centery
        pygame.draw.polygon(s, (255, 80, 30),
                            [(fx - 6, fy + 6), (fx, fy - 10),
                             (fx + 6, fy + 6), (fx, fy + 2)])
        pygame.draw.polygon(s, (255, 200, 60),
                            [(fx - 3, fy + 5), (fx, fy - 4),
                             (fx + 3, fy + 5)])
        sk_t = FONT_SM.render(f"{streak} ngày", True, (255, 220, 140))
        s.blit(sk_t, (chip.x + 24, chip.centery - sk_t.get_height() // 2))

    # ──────────────────────────────────────────────────────────────────
    # Daily check-in (điểm danh hằng ngày) — popups once per day
    # ──────────────────────────────────────────────────────────────────
    DAILY_REWARDS = [
        ("gold",  100,  "🪙"),   # Day 1
        ("gold",  200,  "🪙"),   # Day 2
        ("gems",  3,    "💎"),   # Day 3
        ("gold",  500,  "🪙"),   # Day 4
        ("gems",  5,    "💎"),   # Day 5
        ("gold",  1000, "🪙"),   # Day 6
        ("gems",  20,   "💎"),   # Day 7 — big reward
    ]

    def _daily_can_claim(self):
        today = time.strftime("%Y-%m-%d")
        return self.daily_last_claim_date != today

    def _open_daily_if_due(self):
        """Open the daily check-in screen automatically once per day."""
        if self._daily_can_claim() and not self.daily_popup_seen_today:
            self.daily_popup_seen_today = True
            self.state = "daily_checkin"

    def _claim_daily(self):
        if not self._daily_can_claim():
            return False
        today = time.strftime("%Y-%m-%d")
        # If they missed a day (or never claimed), restart streak; if
        # yesterday, continue.
        try:
            import datetime
            d_today = datetime.date.fromisoformat(today)
            if self.daily_last_claim_date:
                d_last = datetime.date.fromisoformat(self.daily_last_claim_date)
                if (d_today - d_last).days == 1:
                    self.daily_streak += 1
                else:
                    self.daily_streak = 1
            else:
                self.daily_streak = 1
        except Exception:
            self.daily_streak = max(1, self.daily_streak)

        idx = (self.daily_streak - 1) % len(self.DAILY_REWARDS)
        kind, amt, _icon = self.DAILY_REWARDS[idx]
        if kind == "gold":
            self.money += amt
        elif kind == "gems":
            self.gems += amt

        self.daily_last_claim_date = today
        self.daily_total_claims += 1
        # Confetti burst
        self.daily_confetti = []
        for _ in range(80):
            ang = random.random() * 2 * math.pi
            spd = random.uniform(2, 6)
            self.daily_confetti.append({
                "x": SW // 2, "y": SH // 2,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd - 2,
                "life": random.randint(30, 70),
                "col": random.choice([(255, 220, 100), (255, 80, 100),
                                       (90, 220, 255), (200, 120, 255),
                                       (140, 240, 140), (255, 160, 60)]),
            })
        self._save_game()
        return True

    def draw_daily_checkin(self):
        s = self._surf
        tick = self.tick

        # Dark gradient backdrop
        for j in range(SH):
            t = j / max(1, SH - 1)
            rr = int(8 + 20 * (1 - t))
            gg = int(12 + 24 * (1 - t))
            bb = int(28 + 40 * (1 - t))
            pygame.draw.line(s, (rr, gg, bb), (0, j), (SW, j))

        # Star background twinkles
        for si in range(40):
            sx = (si * 71 + tick // 2) % SW
            sy = (si * 53 + (si * 17) % SH) % SH
            a = int(80 + 100 * (math.sin(tick * 0.04 + si) + 1) * 0.5)
            pygame.draw.circle(s, (255, 255, 255, a), (sx, sy), 1)

        # Header
        title = FONT_TITLE.render("ĐIỂM DANH HẰNG NGÀY", True, (255, 220, 100))
        s.blit(title, (SW // 2 - title.get_width() // 2, 32))
        # Glow under title
        glow = pygame.Surface((title.get_width() + 60, title.get_height() + 30),
                              pygame.SRCALPHA)
        for k in range(8, 0, -1):
            pygame.draw.ellipse(glow,
                                (255, 200, 80, 18),
                                (k * 2, k * 2,
                                 title.get_width() + 60 - k * 4,
                                 title.get_height() + 30 - k * 4))
        s.blit(glow, (SW // 2 - (title.get_width() + 60) // 2, 22))
        s.blit(title, (SW // 2 - title.get_width() // 2, 32))

        sub = FONT_MED.render("Nhận quà miễn phí mỗi ngày · "
                              f"Chuỗi: {self.daily_streak} ngày",
                              True, (200, 220, 240))
        s.blit(sub, (SW // 2 - sub.get_width() // 2, 92))

        # Calculate which day index (1..7) is "today"
        today_idx = ((self.daily_streak if self._daily_can_claim()
                      else max(0, self.daily_streak - 1)) % 7)

        # 7 reward cards in a row (Day 1..Day 7)
        n = 7
        card_w = 140
        card_h = 200
        gap = 16
        total = n * card_w + (n - 1) * gap
        start_x = (SW - total) // 2
        y = 150

        for i in range(n):
            kind, amt, _icon = self.DAILY_REWARDS[i]
            x = start_x + i * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            is_today = (i == today_idx) and self._daily_can_claim()
            is_claimed = (i < today_idx) or (
                i == today_idx and not self._daily_can_claim())

            # Card background gradient
            top = (240, 220, 130) if is_today else (
                (180, 200, 230) if is_claimed else (60, 75, 110))
            bot = (255, 180, 60) if is_today else (
                (110, 130, 170) if is_claimed else (28, 38, 64))
            for j in range(card_h):
                t = j / max(1, card_h - 1)
                rr = int(top[0] * (1 - t) + bot[0] * t)
                gg = int(top[1] * (1 - t) + bot[1] * t)
                bb = int(top[2] * (1 - t) + bot[2] * t)
                pygame.draw.line(s, (rr, gg, bb),
                                 (rect.x, rect.y + j),
                                 (rect.right, rect.y + j))

            # Border
            if is_today:
                pulse = (math.sin(tick * 0.15) + 1) * 0.5
                border = (255, int(230 + 25 * pulse),
                          int(110 + 100 * pulse))
                pygame.draw.rect(s, border, rect, 5, border_radius=14)
                # Outer glow halo
                for k in range(6, 0, -1):
                    a = int(60 - k * 8)
                    if a > 0:
                        halo = pygame.Surface((rect.w + 30, rect.h + 30),
                                              pygame.SRCALPHA)
                        pygame.draw.rect(halo, (255, 200, 80, a),
                                         (15 - k * 2, 15 - k * 2,
                                          rect.w + k * 4, rect.h + k * 4),
                                         border_radius=14)
                        s.blit(halo, (rect.x - 15, rect.y - 15))
            elif is_claimed:
                pygame.draw.rect(s, (180, 200, 220), rect, 3,
                                 border_radius=14)
            else:
                pygame.draw.rect(s, (100, 130, 170), rect, 3,
                                 border_radius=14)

            # Day label
            lbl = FONT_MED.render(f"NGÀY {i + 1}", True,
                                  (40, 30, 10) if is_today else
                                  ((50, 70, 100) if is_claimed
                                   else (200, 220, 240)))
            s.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                         rect.y + 12))

            # Icon
            icon_cx = rect.centerx
            icon_cy = rect.centery - 5
            if kind == "gold":
                # Gold coin
                for k in range(3):
                    pygame.draw.circle(s, (255, 200, 60, 100 - k * 30),
                                       (icon_cx, icon_cy), 32 + k * 4)
                pygame.draw.circle(s, (255, 220, 70),
                                   (icon_cx, icon_cy), 32)
                pygame.draw.circle(s, (180, 130, 20),
                                   (icon_cx, icon_cy), 32, 3)
                pygame.draw.circle(s, (255, 245, 140),
                                   (icon_cx - 10, icon_cy - 10), 8)
                try:
                    star = []
                    for ai in range(5):
                        ang = -math.pi / 2 + ai * (2 * math.pi / 5)
                        star.append((icon_cx + 18 * math.cos(ang),
                                     icon_cy + 18 * math.sin(ang)))
                        ang2 = ang + math.pi / 5
                        star.append((icon_cx + 9 * math.cos(ang2),
                                     icon_cy + 9 * math.sin(ang2)))
                    pygame.draw.polygon(s, (180, 130, 20), star)
                except Exception:
                    pass
            else:
                # Diamond
                dpts = [(icon_cx, icon_cy - 28), (icon_cx + 24, icon_cy),
                        (icon_cx, icon_cy + 28), (icon_cx - 24, icon_cy)]
                pygame.draw.polygon(s, (90, 220, 255), dpts)
                pygame.draw.polygon(s, (200, 240, 255),
                                    [(icon_cx, icon_cy - 28),
                                     (icon_cx + 10, icon_cy - 8),
                                     (icon_cx, icon_cy + 4),
                                     (icon_cx - 10, icon_cy - 8)])
                pygame.draw.polygon(s, (40, 130, 200), dpts, 3)

            # Amount
            txt_col = (40, 30, 10) if is_today else (
                (255, 255, 255) if is_claimed else (220, 230, 250))
            amt_t = FONT_BIG.render(f"+{amt:,}", True, txt_col)
            s.blit(amt_t, (rect.centerx - amt_t.get_width() // 2,
                           rect.bottom - 64))
            label_t = FONT_SM.render("VÀNG" if kind == "gold" else "GEM",
                                     True, txt_col)
            s.blit(label_t, (rect.centerx - label_t.get_width() // 2,
                             rect.bottom - 28))

            # "ĐÃ NHẬN" stamp over the icon for previous days
            if is_claimed:
                stamp = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                stamp.fill((255, 255, 255, 0))
                # diagonal "ĐÃ NHẬN" banner
                bx0, by0 = 0, rect.h // 2 - 14
                pygame.draw.rect(stamp, (40, 160, 80, 200),
                                 (bx0, by0, rect.w, 28))
                pygame.draw.rect(stamp, (20, 90, 40, 220),
                                 (bx0, by0, rect.w, 28), 2)
                lbl_t = FONT_MED.render("ĐÃ NHẬN", True, (255, 255, 255))
                stamp.blit(lbl_t, (rect.w // 2 - lbl_t.get_width() // 2,
                                   by0 + 4))
                s.blit(stamp, rect.topleft)
                # Big check at top-right
                tcx = rect.right - 22
                tcy = rect.top + 22
                pygame.draw.circle(s, (40, 170, 80), (tcx, tcy), 16)
                pygame.draw.circle(s, (255, 255, 255), (tcx, tcy), 16, 2)
                pygame.draw.line(s, (255, 255, 255),
                                 (tcx - 6, tcy + 1),
                                 (tcx - 1, tcy + 6), 3)
                pygame.draw.line(s, (255, 255, 255),
                                 (tcx - 1, tcy + 6),
                                 (tcx + 7, tcy - 4), 3)

        # CLAIM button or already-claimed status
        claim_rect = pygame.Rect(SW // 2 - 200, y + card_h + 40, 400, 70)
        self._daily_claim_rect = claim_rect
        if self._daily_can_claim():
            pulse = (math.sin(tick * 0.12) + 1) * 0.5
            # Animated gradient button
            for j in range(claim_rect.h):
                t = j / max(1, claim_rect.h - 1)
                rr = int(255 - 30 * t)
                gg = int(180 + 50 * pulse - 60 * t)
                bb = int(40 - 20 * t)
                pygame.draw.line(s, (rr, gg, bb),
                                 (claim_rect.x, claim_rect.y + j),
                                 (claim_rect.right, claim_rect.y + j))
            pygame.draw.rect(s, (255, 240, 140), claim_rect, 4,
                             border_radius=18)
            ctxt = FONT_TITLE.render("NHẬN QUÀ", True, (40, 24, 0))
            s.blit(ctxt, (claim_rect.centerx - ctxt.get_width() // 2,
                          claim_rect.centery - ctxt.get_height() // 2))
        else:
            pygame.draw.rect(s, (60, 80, 110), claim_rect, border_radius=18)
            pygame.draw.rect(s, (120, 140, 170), claim_rect, 4,
                             border_radius=18)
            ctxt = FONT_BIG.render("ĐÃ NHẬN HÔM NAY",
                                   True, (200, 220, 240))
            s.blit(ctxt, (claim_rect.centerx - ctxt.get_width() // 2,
                          claim_rect.centery - ctxt.get_height() // 2))

        # Confetti animation (after claim)
        for p in self.daily_confetti[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.18
            p["life"] -= 1
            if p["life"] <= 0:
                self.daily_confetti.remove(p)
                continue
            pygame.draw.rect(s, p["col"],
                             (int(p["x"]), int(p["y"]), 6, 6))

        # Close hint + button
        close_rect = pygame.Rect(SW - 80, 30, 50, 50)
        self._daily_close_rect = close_rect
        pygame.draw.rect(s, (40, 40, 60), close_rect, border_radius=10)
        pygame.draw.rect(s, (200, 80, 80), close_rect, 3, border_radius=10)
        pygame.draw.line(s, (255, 255, 255),
                         (close_rect.x + 15, close_rect.y + 15),
                         (close_rect.right - 15, close_rect.bottom - 15), 4)
        pygame.draw.line(s, (255, 255, 255),
                         (close_rect.right - 15, close_rect.y + 15),
                         (close_rect.x + 15, close_rect.bottom - 15), 4)

        hint = FONT_SM.render("[ESC] Đóng · [ENTER/SPACE] Nhận quà",
                              True, (160, 180, 220))
        s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 36))

    def draw_title(self):
        s = self._surf
        tick = self.tick

        # Auto-popup daily check-in when entering title once per day
        self._open_daily_if_due()

        # ── FAST PATH: full-art title background from the user's video ──
        if getattr(self, 'title_bg', None) or getattr(self, 'title_bg_frames', None):
            frames = getattr(self, 'title_bg_frames', None) or []
            if frames:
                # Loop the animation at title_bg_fps (24 = source rate).
                # self.tick is the pygame loop frame counter (60 fps), so
                # step every (60/fps) ticks.
                step = max(1, 60 // max(1, self.title_bg_fps))
                idx = (self.tick // step) % len(frames)
                s.blit(frames[idx], (0, 0))
            else:
                s.blit(self.title_bg, (0, 0))

            # Update menu_sel based on mouse hover — but draw nothing on top.
            _mx_phys, _my_phys = pygame.mouse.get_pos()
            mx = int(_mx_phys * (SW / phys_w))
            my = int(_my_phys * (SH / phys_h))
            for _lbl, rect, midx in self._title_button_rects():
                if rect.collidepoint(mx, my):
                    self.menu_sel = midx
                    break

            # ── PROFILE + CURRENCY OVERLAYS ─────────────────────────────
            # Two fully opaque panels that completely cover the baked-in
            # UI in the source video (top-left profile box, top-right
            # currency box).  The lobby is otherwise a clean loop of the
            # source video.
            self._draw_title_overlays(s, tick)

            # Floating text overlays only (gameplay popups).
            for ft in floating_texts:
                ft.draw(s, (0, 0), 1.0)
            return

        if getattr(self, 'bg_main', None):
            # Draw custom background
            s.blit(self.bg_main, (0, 0))

            # --- DYNAMIC NEON ANIMATIONS (NEN DONG) ---
            # 1. Scanning laser sweep line
            laser_y = int((tick * 1.5) % SH)
            laser_surf = pygame.Surface((SW, 4), pygame.SRCALPHA)
            pygame.draw.line(laser_surf, (0, 255, 255, 40), (0, 1), (SW, 1), 2)
            pygame.draw.line(laser_surf, (255, 255, 255, 120), (0, 2), (SW, 2), 1)
            s.blit(laser_surf, (0, laser_y))

            # 2. Cyber neon shooting stars
            for si in range(2):
                phase = (tick * 0.015 + si * 3.1) % 6.28
                if math.sin(phase) > 0.88:
                    progress = (math.sin(phase) - 0.88) / 0.12
                    sx = int(50 + si * 350 + progress * 200)
                    sy = int(30 + si * 100 + progress * 120)
                    trail_len = int(35 * (1 - progress * 0.5))
                    a = int(180 * (1 - progress))
                    ts_surf = pygame.Surface((trail_len + 4, 4), pygame.SRCALPHA)
                    for tl in range(trail_len):
                        ta = int(a * (1 - tl / trail_len))
                        pygame.draw.circle(ts_surf, (0, 255, 255, max(0, ta)), (trail_len - tl, 2), 1)
                    s.blit(ts_surf, (sx, sy))

            # 3. Floating glowing neon cyber-particles
            for pi in range(12):
                px = int((pi * 127 + tick * 0.4 + pi * pi) % SW)
                py = int((pi * 83 - tick * 0.25) % SH)
                pa = int(100 + 80 * math.sin(tick * 0.05 + pi * 1.5))
                pc = KAWAII_RAINBOW[pi % len(KAWAII_RAINBOW)]
                ps = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(ps, (*pc, max(0, min(255, pa))), (6, 6), 5)
                pygame.draw.circle(ps, (255, 255, 255, max(0, min(255, pa // 2))), (6, 6), 2)
                s.blit(ps, (px - 6, py - 6))

            # --- 3D ROTATING CYBER GLOBE (REALISTIC 3D HOLOGRAPHIC SPHERE) ---
            cx = SW - 360
            cy = SH // 2 + 30
            R = 135
            
            # A. Globe glowing core radial aura
            core_surf = pygame.Surface((R*2 + 40, R*2 + 40), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, (0, 255, 255, 25), (R + 20, R + 20), R + 10)
            pygame.draw.circle(core_surf, (255, 0, 255, 15), (R + 20, R + 20), R)
            pygame.draw.circle(core_surf, (255, 255, 255, 30), (R + 20, R + 20), R // 3)
            s.blit(core_surf, (cx - R - 20, cy - R - 20))

            # B. Organic Sphere Volume Shading (3D Realistic Depth Mask)
            for r_glow in range(R, 0, -4):
                alpha = int(12 + 24 * (1 - r_glow / R))
                pygame.draw.circle(s, (0, 255, 255, alpha), (cx, cy), r_glow)

            # C. 3D Longitude Spinning Rings
            for i in range(3):
                phase = i * 3.14159 / 3
                angle = tick * 0.015 + phase
                ellipse_w = int(R * math.cos(angle))
                if abs(ellipse_w) > 2:
                    color = (0, 255, 255, 90) if i == 0 else ((255, 0, 255, 70) if i == 1 else (0, 255, 128, 70))
                    pygame.draw.ellipse(s, color, (cx - abs(ellipse_w), cy - R, abs(ellipse_w) * 2, R * 2), 2)

            # D. Latitude Rings (Horizontal Ellipses)
            for dy in [-70, -35, 0, 35, 70]:
                r = int(math.sqrt(max(4, R*R - dy*dy)))
                eh = max(2, int(r * 0.18))
                pygame.draw.ellipse(s, (0, 255, 255, 50), (cx - r, cy + dy - eh // 2, r * 2, eh), 1)

            # E. 3D Rotating Particle Coordinates (Parallax Grid Dots - Extremely Realistic)
            for p_idx in range(24):
                phi = p_idx * 137.5 * (math.pi / 180.0)
                y_pct = 1.0 - (p_idx / 23.0) * 2.0
                radius_at_y = R * math.sqrt(max(0.0, 1.0 - y_pct * y_pct))
                
                lon = phi + tick * 0.022
                px = int(cx + radius_at_y * math.cos(lon))
                py = int(cy + R * y_pct)
                pz = radius_at_y * math.sin(lon)
                
                if pz > 0:
                    alpha = int(170 + 85 * (pz / R))
                    r_dot = int(4 + 2 * (pz / R))
                    color = (0, 255, 255, alpha)
                    pygame.draw.circle(s, color, (px, py), r_dot)
                    pygame.draw.circle(s, (255, 255, 255, alpha), (px, py), r_dot // 2)
                else:
                    alpha = int(35 + 45 * (1 + pz / R))
                    r_dot = int(2 + 1 * (1 + pz / R))
                    color = (0, 140, 180, alpha)
                    pygame.draw.circle(s, color, (px, py), r_dot)

            # F. Massive Golden Diagonal Orbit Ring (Saturn Ring)
            rw = int(R * 1.45)
            rh = int(rw * 0.28)
            pygame.draw.ellipse(s, (255, 215, 0, 70), (cx - rw, cy - rh, rw * 2, rh * 2), 2)
            
            # G. Revolving Satellites
            for sat_idx in range(2):
                sat_angle = tick * 0.012 + sat_idx * 3.14159
                sat_x = cx + int(rw * math.cos(sat_angle))
                sat_y = cy + int(rh * math.sin(sat_angle))
                pygame.draw.circle(s, (255, 255, 255), (sat_x, sat_y), 4)
                pygame.draw.circle(s, (255, 215, 0, 150), (sat_x, sat_y), 7, width=1)

            # H. Radar Crosshair Overlays
            pygame.draw.circle(s, (0, 255, 255, 30), (cx, cy), R + 25, width=1)
            pygame.draw.circle(s, (0, 255, 255, 15), (cx, cy), R + 35, width=1)
            pygame.draw.line(s, (0, 255, 255, 100), (cx - R - 30, cy), (cx - R - 15, cy), 2)
            pygame.draw.line(s, (0, 255, 255, 100), (cx + R + 15, cy), (cx + R + 30, cy), 2)
            pygame.draw.line(s, (0, 255, 255, 100), (cx, cy - R - 30), (cx, cy - R - 15), 2)
            pygame.draw.line(s, (0, 255, 255, 100), (cx, cy + R + 15), (cx, cy + R + 30), 2)

            # I. Scrolling High-Tech Text Overlay
            consolas_font = pygame.font.SysFont("Consolas", 10, bold=True)
            hud_label = consolas_font.render(f"TACTICAL GLOBE // SYS_OK // TICK_{tick:05d}", True, (0, 255, 255, 160))
            s.blit(hud_label, (cx - hud_label.get_width() // 2, cy + R + 35))

            # --- DYNAMIC BACKGROUND TANKS ---
            t1_y = SH - 85
            t1_period = 250
            t1_sub = tick % t1_period
            is_firing = (15 <= t1_sub <= 35)
            shake_x = 0
            if is_firing:
                shake_x = -int(math.sin(tick * 1.2) * 5)
            t1_cycle = tick // t1_period
            base_x = (tick * 1.5) % (SW + 160) - 80
            if t1_sub > 15:
                base_x = ((t1_cycle * t1_period + 15) * 1.5) % (SW + 160) - 80
                if t1_sub > 35:
                    base_x = ((t1_cycle * t1_period + 15 + (t1_sub - 35)) * 1.5) % (SW + 160) - 80
            t1_x = base_x + shake_x

            try:
                skin_sprites = sprites.tanks["player"]
                s_idx = min(len(skin_sprites) - 1, self.skin_idx)
                p_tank_img = pygame.transform.scale(skin_sprites[s_idx], (45, 45))
                p_tank_img = pygame.transform.rotate(p_tank_img, -90)
                s.blit(p_tank_img, (t1_x, t1_y))
            except Exception:
                pygame.draw.rect(s, (100, 200, 100), (t1_x, t1_y + 10, 45, 30), border_radius=6)
                pygame.draw.circle(s, (80, 160, 80), (t1_x + 22, t1_y + 10), 12)
                pygame.draw.line(s, (60, 120, 60), (t1_x + 22, t1_y + 10), (t1_x + 45, t1_y + 10), 4)

            if 15 <= t1_sub <= 70:
                bullet_x = t1_x + 45 + (t1_sub - 15) * 10
                bullet_y = t1_y + 22
                if bullet_x < SW:
                    pygame.draw.circle(s, (0, 255, 255), (int(bullet_x), int(bullet_y)), 5)
                    pygame.draw.circle(s, (255, 255, 255), (int(bullet_x), int(bullet_y)), 2)
                if 15 <= t1_sub <= 25:
                    flash_r = int(10 + 5 * math.sin(tick * 0.8))
                    flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(flash_surf, (255, 150, 0, 180), (flash_r, flash_r), flash_r)
                    pygame.draw.circle(flash_surf, (255, 255, 255, 240), (flash_r, flash_r), flash_r // 2)
                    s.blit(flash_surf, (t1_x + 45 - flash_r, t1_y + 22 - flash_r))

            t2_y = SH - 75
            t2_period = 320
            t2_sub = tick % t2_period
            t2_is_firing = (40 <= t2_sub <= 60)
            t2_shake_x = 0
            if t2_is_firing:
                t2_shake_x = int(math.sin(tick * 1.2) * 5)
            t2_cycle = tick // t2_period
            t2_base_x = SW + 80 - (tick * 1.2) % (SW + 160)
            if t2_sub > 40:
                t2_base_x = SW + 80 - ((t2_cycle * t2_period + 40) * 1.2) % (SW + 160)
                if t2_sub > 60:
                    t2_base_x = SW + 80 - ((t2_cycle * t2_period + 40 + (t2_sub - 60)) * 1.2) % (SW + 160)
            t2_x = t2_base_x + t2_shake_x

            try:
                e_tank_img = pygame.transform.scale(sprites.tanks["enemy"][0], (45, 45))
                e_tank_img = pygame.transform.rotate(e_tank_img, 90)
                s.blit(e_tank_img, (t2_x, t2_y))
            except Exception:
                pygame.draw.rect(s, (220, 80, 80), (t2_x, t2_y + 10, 45, 30), border_radius=6)
                pygame.draw.circle(s, (180, 60, 60), (t2_x + 22, t2_y + 10), 12)
                pygame.draw.line(s, (150, 40, 40), (t2_x + 22, t2_y + 10), (t2_x, t2_y + 10), 4)

            if 40 <= t2_sub <= 95:
                e_bullet_x = t2_x - (t2_sub - 40) * 10
                e_bullet_y = t2_y + 22
                if e_bullet_x > 0:
                    pygame.draw.circle(s, (255, 100, 100), (int(e_bullet_x), int(e_bullet_y)), 5)
                    pygame.draw.circle(s, (255, 255, 255), (int(e_bullet_x), int(e_bullet_y)), 2)
                if 40 <= t2_sub <= 50:
                    flash_r = int(10 + 5 * math.sin(tick * 0.8))
                    flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(flash_surf, (255, 50, 0, 180), (flash_r, flash_r), flash_r)
                    pygame.draw.circle(flash_surf, (255, 255, 255, 240), (flash_r, flash_r), flash_r // 2)
                    s.blit(flash_surf, (t2_x - flash_r, t2_y + 22 - flash_r))

            # Currency & Profile (Standard UI)
            self._draw_currency_panel(s, SW - 270, 12)
            self._draw_profile_panel(s, 12, 12)

            # Draw bottom hint bar
            hint = FONT_SM.render("[UP/DOWN] chon  [ENTER] vao  [H] huong dan  [F11] toan man hinh  [ESC] thoat", True, (200, 200, 220))
            s.blit(hint, (SW // 2 - hint.get_width() // 2, SH - 35))

            # Draw left custom menu buttons (Vẽ trực tiếp bằng Vector sạch đẹp 100% trong suốt)
            gap = 12
            bh = 68
            bw = 260
            total_h = len(self.menu_buttons) * (bh + gap) - gap
            start_y = (SH - total_h) // 2 + 20
            _mx_phys, _my_phys = pygame.mouse.get_pos()
            mx = int(_mx_phys * (SW / phys_w))
            my = int(_my_phys * (SH / phys_h))

            # Hover detection
            for i in range(len(self.menu_buttons)):
                bx = 50
                by = start_y + i * (bh + gap)
                draw_x = bx
                if i == self.menu_sel:
                    draw_x += 15
                if pygame.Rect(draw_x, by, bw, bh).collidepoint(mx, my):
                    self.menu_sel = i

            # Subtitles & Colors mapped to the buttons
            subtitles = {
                "CHIẾN ĐẤU": "[ BATTLE NOW ]",
                "SHOP": "[ ACCESS SHOP ]",
                "GA-RA": "[ ENTER GARAGE ]",
                "CHƠI MẠNG (PVP)": "[ JOIN ONLINE ]",
                "CHƠI CHUNG (CO-OP)": "[ CO-OP MODE ]",
                "VÒNG QUAY": "[ LUCKY SPIN ]"
            }
            colors = {
                "CHIẾN ĐẤU": (0, 255, 255),       # Cyan
                "SHOP": (255, 0, 255),           # Magenta
                "GA-RA": (255, 215, 0),          # Gold
                "CHƠI MẠNG (PVP)": (255, 50, 100), # Bright Rose
                "CHƠI CHUNG (CO-OP)": (50, 200, 255), # Sky Blue
                "VÒNG QUAY": (255, 128, 0)        # Orange
            }

            sub_font = pygame.font.SysFont("Consolas", 11, bold=True)

            for i, label in enumerate(self.menu_buttons):
                bx = 50
                by = start_y + i * (bh + gap)

                draw_x = bx
                is_sel = (i == self.menu_sel)
                if is_sel:
                    draw_x += 15

                pc = colors.get(label, (0, 255, 255))
                sub_txt = subtitles.get(label, "[ CLICK TO ENTER ]")
                
                # 1. 3D DROP SHADOW
                pygame.draw.rect(s, (5, 3, 12, 110), (draw_x + 6, by + 6, bw, bh), border_radius=16)
                
                btn_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)

                # Background capsule
                bg_alpha = 180 if is_sel else 120
                pygame.draw.rect(btn_surf, (20, 10, 30, bg_alpha), (0, 0, bw, bh), border_radius=16)

                # Hover neon glow fill
                if is_sel:
                    pygame.draw.rect(btn_surf, (*pc, 35), (0, 0, bw, bh), border_radius=16)

                # Double neon borders
                pygame.draw.rect(btn_surf, (*pc, 70), (0, 0, bw, bh), width=3, border_radius=16)
                pygame.draw.rect(btn_surf, (255, 255, 255, 200) if is_sel else (*pc, 180), (2, 2, bw - 4, bh - 4), width=1, border_radius=14)

                # 2. 3D Top-Left Light highlight bevel for realism
                pygame.draw.rect(btn_surf, (255, 255, 255, 45), (1, 1, bw - 2, bh - 2), width=1, border_radius=15)

                # 3. Slanted Glass Reflection Sheen (Chân thật như kính)
                sheen_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                pygame.draw.polygon(sheen_surf, (255, 255, 255, 12), [(0, 0), (bw // 2 - 20, 0), (bw // 2 - 70, bh), (0, bh)])
                btn_surf.blit(sheen_surf, (0, 0))

                # Exquisite Tech Corners
                pygame.draw.line(btn_surf, pc, (3, 8), (3, 3), 2)
                pygame.draw.line(btn_surf, pc, (3, 3), (8, 3), 2)
                pygame.draw.line(btn_surf, pc, (bw - 4, 8), (bw - 4, 3), 2)
                pygame.draw.line(btn_surf, pc, (bw - 4, 3), (bw - 9, 3), 2)
                pygame.draw.line(btn_surf, pc, (3, bh - 9), (3, bh - 4), 2)
                pygame.draw.line(btn_surf, pc, (3, bh - 4), (8, bh - 4), 2)
                pygame.draw.line(btn_surf, pc, (bw - 4, bh - 9), (bw - 4, bh - 4), 2)
                pygame.draw.line(btn_surf, pc, (bw - 4, bh - 4), (bw - 9, bh - 4), 2)

                # Active highlight neon left bar and horizontal scanlines
                if is_sel:
                    pygame.draw.rect(btn_surf, pc, (2, 6, 6, bh - 12), border_radius=3)
                    pygame.draw.rect(btn_surf, (255, 255, 255, 220), (4, 10, 2, bh - 20), border_radius=1)
                    
                    # Horizontal scanning scanline
                    scan_x = int((tick * 2.5) % (bw - 20)) + 10
                    pygame.draw.line(btn_surf, (255, 255, 255, 60), (scan_x, 4), (scan_x, bh - 4), 2)

                # Center text
                t_shadow = FONT_MED.render(label, True, (10, 10, 15))
                t_main = FONT_MED.render(label, True, (255, 255, 255))
                
                tx = bw // 2 - t_main.get_width() // 2
                ty = bh // 2 - t_main.get_height() // 2 - (6 if is_sel else 0)

                btn_surf.blit(t_shadow, (tx + 2, ty + 2))
                btn_surf.blit(t_main, (tx, ty))

                # Add subtitle under label if selected
                if is_sel:
                    sub_t = sub_font.render(sub_txt, True, pc)
                    stx = bw // 2 - sub_t.get_width() // 2
                    sty = ty + t_main.get_height() + 2
                    btn_surf.blit(sub_t, (stx, sty))

                # Draw cute pointer hand
                if is_sel and getattr(self, 'pointer_img', None):
                    py = by + (bh - self.pointer_img.get_height()) // 2
                    px = draw_x - self.pointer_img.get_width() - 10 + int(math.sin(tick * 0.15) * 6)
                    s.blit(self.pointer_img, (px, py))

                s.blit(btn_surf, (draw_x, by))
            return
        else:

            # ── Layered sky gradient ──
            # Layered sky gradient
            if getattr(self, 'bg_main', None):
                s.blit(self.bg_main, (0, 0))
            else:
                for y in range(SH):
                    t = y / SH
                    r = int(18 + 45 * t + 12 * math.sin(tick * 0.008 + t * 4))
                    g = int(10 + 35 * t + 8 * math.sin(tick * 0.006 + t * 2))
                    b = int(50 + 60 * t + 10 * math.cos(tick * 0.01 + t * 3))
                    pygame.draw.line(s, (max(0, min(255, r)), max(0, min(255, g)),
                                          max(0, min(255, b))), (0, y), (SW, y))

            # ── Nebula clouds ──
            for ci in range(5):
                cx = int((ci * 173 + tick * 0.15) % (SW + 200)) - 100
                cy = int(60 + ci * 90 + math.sin(tick * 0.005 + ci) * 30)
                neb = pygame.Surface((180, 100), pygame.SRCALPHA)
                nc = KAWAII_RAINBOW[ci % len(KAWAII_RAINBOW)]
                pygame.draw.ellipse(neb, (*nc, 18), (0, 0, 180, 100))
                pygame.draw.ellipse(neb, (*nc, 12), (30, 20, 120, 60))
                s.blit(neb, (cx - 90, cy - 50))

            # ── Crescent moon ──
            moon_x = SW - 90 + int(math.sin(tick * 0.003) * 3)
            moon_y = 55 + int(math.cos(tick * 0.004) * 2)
            glow_s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (255, 255, 220, 12), (20, 20), 18)
            s.blit(glow_s, (moon_x - 20, moon_y - 20))
            pygame.draw.circle(s, (240, 235, 215), (moon_x, moon_y), 12)
            pygame.draw.circle(s, (max(0, min(255, int(18 + 45 * (moon_y / SH)))),
                                   max(0, min(255, int(10 + 35 * (moon_y / SH)))),
                                   max(0, min(255, int(50 + 60 * (moon_y / SH))))),
                               (moon_x + 5, moon_y - 3), 10)

            draw_pastel_starfield(s, tick, density=120)

            # ── Shooting stars ──
            for si in range(3):
                phase = (tick * 0.02 + si * 2.1) % 6.28
                if math.sin(phase) > 0.85:
                    progress = (math.sin(phase) - 0.85) / 0.15
                    sx = int(100 + si * 250 + progress * 150)
                    sy = int(40 + si * 60 + progress * 80)
                    trail_len = int(40 * (1 - progress * 0.5))
                    a = int(200 * (1 - progress))
                    ts_surf = pygame.Surface((trail_len + 6, 6), pygame.SRCALPHA)
                    for tl in range(trail_len):
                        ta = int(a * (1 - tl / trail_len))
                        pygame.draw.circle(ts_surf, (255, 255, 220, max(0, ta)),
                                           (trail_len - tl, 3), max(1, 3 - tl * 3 // trail_len))
                    s.blit(ts_surf, (sx, sy))

            # ── Fireflies ──
            for pi in range(15):
                px = int((pi * 97 + tick * 0.3 + pi * pi) % SW)
                py = int((pi * 61 + math.sin(tick * 0.02 + pi * 0.8) * 40 + 200) % SH)
                pa = int(120 + 80 * math.sin(tick * 0.05 + pi * 1.3))
                pc = KAWAII_RAINBOW[pi % len(KAWAII_RAINBOW)]
                ps = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(ps, (*pc, max(0, min(255, pa))), (4, 4), 3)
                pygame.draw.circle(ps, (255, 255, 255, max(0, min(255, pa // 2))), (4, 4), 1)
                s.blit(ps, (px, py))

            # ── Background tanks ──
            for tank in self.title_tanks:
                tk = tank['type']
                d = tank['dir']
                if tk in sprites.tanks:
                    img = sprites.tanks[tk][d]
                    img = pygame.transform.scale(img, (36, 36))
                    alpha_s = pygame.Surface((36, 36), pygame.SRCALPHA)
                    alpha_s.blit(img, (0, 0))
                    alpha_s.set_alpha(35)
                    s.blit(alpha_s, (int(tank['x']) - 18, int(tank['y']) - 18))

            # ── Ground strip ──
            ground_y = SH - 55
            for gx in range(0, SW, TS):
                if hasattr(sprites, 'floor'):
                    fl = sprites.floor
                    fl_a = pygame.Surface((TS, TS), pygame.SRCALPHA)
                    fl_a.blit(fl, (0, 0))
                    fl_a.set_alpha(60)
                    s.blit(fl_a, (gx, ground_y))
            for gi in range(0, SW, 12):
                gh = 4 + int(math.sin(gi * 0.3 + tick * 0.04) * 2)
                gc = (60 + gi % 40, 160 + gi % 60, 60 + gi % 30)
                pygame.draw.line(s, gc, (gi, ground_y), (gi + 2, ground_y - gh), 2)

            # ── Currency & Profile ──
            self._draw_currency_panel(s, SW - 270, 12)
            self._draw_profile_panel(s, 12, 12)

            # ── Rainbow border ──
            for bx in range(0, SW, 4):
                bc = KAWAII_RAINBOW[(bx // 4 + tick // 8) % len(KAWAII_RAINBOW)]
                ba = int(100 + 50 * math.sin(tick * 0.06 + bx * 0.05))
                bs = pygame.Surface((4, 3), pygame.SRCALPHA)
                pygame.draw.rect(bs, (*bc, max(0, min(255, ba))), (0, 0, 4, 3))
                s.blit(bs, (bx, 88))

            # ── Title ──
            draw_rainbow_text(s, "KAWAII TANK KINGDOM", (SW // 2, 100),
                              FONT_TITLE, tick=tick)
            sub = FONT_SM.render("GIẢI CỨU THẾ GIỚI KHỎI XE TĂNG XÂM LƯỢC", True, (255, 220, 240))
            sub_glow_a = int(40 + 30 * math.sin(tick * 0.06))
            sub_glow = pygame.Surface((sub.get_width() + 20, sub.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(sub_glow, (255, 200, 230, max(0, sub_glow_a)),
                             (0, 0, sub_glow.get_width(), sub_glow.get_height()), border_radius=8)
            s.blit(sub_glow, (SW // 2 - sub.get_width() // 2 - 10, 153))
            s.blit(sub, (SW // 2 - sub.get_width() // 2, 158))
            ver = FONT_SM.render("v3.0 ULTIMATE", True, (180, 160, 220))
            s.blit(ver, (SW // 2 - ver.get_width() // 2, 175))

            # ── Tank preview row ──
            tank_types = ["player", "enemy_a", "enemy_b", "elite", "boss"]
            labels = ["NEKO", "ĐỊCH", "NHANH", "TINH NHUỆ", "BOSS"]
            hp_vals = [3, 2, 2, 5, 15]
            preview_y = 200
            for i, (tk, label) in enumerate(zip(tank_types, labels)):
                bx = SW // 2 - 250 + i * 100
                by = preview_y + int(math.sin(tick * 0.04 + i * 1.2) * 3)
                draw_kawaii_panel(s, (bx, by, 88, 105), fill=(60, 40, 90),
                                  border=KAWAII_RAINBOW[i % len(KAWAII_RAINBOW)],
                                  radius=14, shadow_offset=4, glow=True)
                d = (tick // 20 + i) % 4
                if tk == "player":
                    tier = min(len(sprites.player_tiers) - 1, self.skin_idx)
                    tank_img = sprites.player_tiers[tier][d]
                elif tk in sprites.tanks:
                    tank_img = sprites.tanks[tk][d]
                else:
                    tank_img = None
                if tank_img is not None:
                    big = pygame.transform.scale(tank_img, (56, 56))
                    s.blit(big, (bx + 16, by + 8))
                lbl = FONT_SM.render(label, True, (255, 240, 200))
                s.blit(lbl, (bx + 44 - lbl.get_width() // 2, by + 68))
                hp_text = FONT_SM.render(f"HP:{hp_vals[i]}", True, (255, 150, 150))
                s.blit(hp_text, (bx + 44 - hp_text.get_width() // 2, by + 85))
                sp_phase = math.sin(tick * 0.08 + i * 0.9)
                if sp_phase > 0.7:
                    draw_sparkle(s, bx + 70, by + 5, 5,
                                 color=KAWAII_RAINBOW[i % len(KAWAII_RAINBOW)],
                                 alpha=int(200 * (sp_phase - 0.7) / 0.3))

            # ── Separator ──
            sep_y = preview_y + 120
            for sx_i in range(SW // 2 - 140, SW // 2 + 140, 3):
                sc = KAWAII_RAINBOW[(sx_i // 3 + tick // 10) % len(KAWAII_RAINBOW)]
                pygame.draw.circle(s, sc, (sx_i, sep_y), 1)

            # ── Menu buttons ──
            btn_w, btn_h = 260, 46
            gap = 12
        
            if self.menu_btn_imgs and len(self.menu_btn_imgs) >= len(self.menu_buttons):
                # Custom styled sliced buttons (drawn on the left side, perfectly centered vertically!)
                total_h = 0
                for img in self.menu_btn_imgs[:len(self.menu_buttons)]:
                    total_h += img.get_height() + gap
                total_h -= gap
                start_y = (SH - total_h) // 2 + 20
            
                _mx_phys, _my_phys = pygame.mouse.get_pos()
                mx = int(_mx_phys * (SW / phys_w))
                my = int(_my_phys * (SH / phys_h))
            
                # Hover detection
                for i in range(len(self.menu_buttons)):
                    img = self.menu_btn_imgs[i]
                    bw, bh = img.get_size()
                    bx = 50
                    by = start_y
                    for prev_i in range(i):
                        by += self.menu_btn_imgs[prev_i].get_height() + gap
                
                    draw_x = bx
                    if i == self.menu_sel:
                        draw_x += 15
                
                    if pygame.Rect(draw_x, by, bw, bh).collidepoint(mx, my):
                        self.menu_sel = i
            
                # Draw custom buttons
                for i in range(len(self.menu_buttons)):
                    img = self.menu_btn_imgs[i]
                    bw, bh = img.get_size()
                    bx = 50
                    by = start_y
                    for prev_i in range(i):
                        by += self.menu_btn_imgs[prev_i].get_height() + gap
                
                    draw_x = bx
                    if i == self.menu_sel:
                        draw_x += 15  # Premium slide-out hover animation!
                    s.blit(img, (draw_x, by))
            else:
                # Fallback to centered kawaii buttons
                gap = 10
                total_h = len(self.menu_buttons) * (btn_h + gap) - gap
                start_y = SH - total_h - 55
                icons = [
                    lambda surf, x, y, sz: surf.blit(
                        pygame.transform.scale(sprites.player_tiers[
                            min(len(sprites.player_tiers) - 1, self.skin_idx)][1],
                            (sz, sz)), (x, y)),
                    draw_coin_icon,
                    lambda surf, x, y, sz: surf.blit(
                        pygame.transform.scale(sprites.tanks["player"][2], (sz, sz)),
                        (x, y)),
                    draw_coin_icon,
                    lambda surf, x, y, sz: draw_heart_icon(surf, x, y, sz, filled=True),
                    lambda surf, x, y, sz: surf.blit(
                        pygame.transform.scale(sprites.tanks["player"][0], (sz, sz)),
                        (x, y)),
                ]
                for i, label in enumerate(self.menu_buttons):
                    bx = SW // 2 - btn_w // 2
                    by = start_y + i * (btn_h + gap)
                    icon_fn = icons[i] if i < len(icons) else None
                    draw_kawaii_button(s, (bx, by, btn_w, btn_h), label, FONT_MED,
                                       selected=(i == self.menu_sel), color_idx=i,
                                       tick=tick, icon_fn=icon_fn)

            # ── Corner ornaments ──
            for corner in range(4):
                cx_pos = 25 if corner % 2 == 0 else SW - 25
                cy_pos = SH - 45 if corner >= 2 else 92
                orn_a = int(100 + 60 * math.sin(tick * 0.04 + corner * 1.5))
                orn_c = KAWAII_RAINBOW[corner % len(KAWAII_RAINBOW)]
                orn_s = pygame.Surface((20, 20), pygame.SRCALPHA)
                pts = [(10, 0), (20, 10), (10, 20), (0, 10)]
                pygame.draw.polygon(orn_s, (*orn_c, max(0, min(255, orn_a))), pts)
                pygame.draw.polygon(orn_s, (255, 255, 255, max(0, min(255, orn_a // 2))), pts, 1)
                s.blit(orn_s, (cx_pos - 10, cy_pos - 10))

            # ── Side strips ──
            for sy_i in range(100, SH - 50, 20):
                la = int(40 + 30 * math.sin(tick * 0.03 + sy_i * 0.05))
                lc = KAWAII_RAINBOW[(sy_i // 20) % len(KAWAII_RAINBOW)]
                ls = pygame.Surface((3, 12), pygame.SRCALPHA)
                pygame.draw.rect(ls, (*lc, max(0, min(255, la))), (0, 0, 3, 12), border_radius=1)
                s.blit(ls, (6, sy_i))
                s.blit(ls, (SW - 9, sy_i))

            # ── Footer ──
            footer_bg = pygame.Surface((SW, 32), pygame.SRCALPHA)
            pygame.draw.rect(footer_bg, (20, 15, 40, 150), (0, 0, SW, 32))
            s.blit(footer_bg, (0, SH - 32))
            hint = "  ↑/↓  chọn  •  ENTER  vào  •  H  hướng dẫn  •  F11  toàn màn hình  •  ESC  thoát"
            ht = FONT_SM.render(hint, True, (255, 220, 240))
            s.blit(ht, (SW // 2 - ht.get_width() // 2, SH - 26))

    def _draw_currency_panel(self, surf, x, y):
        # Top-right currency display: gold + gems (Extremely Exquisite Sci-Fi HUD)
        w, h = 250, 70
        
        # Glassmorphic cyber capsule
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (20, 10, 30, 160), (0, 0, w, h), border_radius=16)
        # Gold neon border
        pygame.draw.rect(panel_surf, (255, 215, 0, 70), (0, 0, w, h), width=3, border_radius=16)
        pygame.draw.rect(panel_surf, (255, 255, 255, 120), (2, 2, w - 4, h - 4), width=1, border_radius=14)
        
        # Tech corners
        pygame.draw.line(panel_surf, (255, 215, 0), (3, 8), (3, 3), 2)
        pygame.draw.line(panel_surf, (255, 215, 0), (3, 3), (8, 3), 2)
        pygame.draw.line(panel_surf, (255, 215, 0), (w - 4, 8), (w - 4, 3), 2)
        pygame.draw.line(panel_surf, (255, 215, 0), (w - 4, 3), (w - 9, 3), 2)
        pygame.draw.line(panel_surf, (255, 215, 0), (3, h - 9), (3, h - 4), 2)
        pygame.draw.line(panel_surf, (255, 215, 0), (3, h - 4), (8, h - 4), 2)
        pygame.draw.line(panel_surf, (255, 215, 0), (w - 4, h - 9), (w - 4, h - 4), 2)
        pygame.draw.line(panel_surf, (255, 215, 0), (w - 4, h - 4), (w - 9, h - 4), 2)
        
        surf.blit(panel_surf, (x, y))

        # Dotted Divider Line
        pygame.draw.line(surf, (255, 255, 255, 40), (x + 130, y + 10), (x + 130, y + 60), 1)

        # 1. Gold row (Floating Icon)
        float_y1 = int(math.sin(self.tick * 0.1) * 3)
        pygame.draw.circle(surf, (255, 215, 0, 40), (x + 23, y + 21 + float_y1), 12)
        draw_coin_icon(surf, x + 12, y + 9 + float_y1, 22)
        
        gt_shadow = FONT_MED.render(f"{self.money:,}", True, (10, 10, 15))
        gt_main = FONT_MED.render(f"{self.money:,}", True, (255, 235, 120))
        surf.blit(gt_shadow, (x + 44, y + 11))
        surf.blit(gt_main, (x + 42, y + 9))

        # Plus button Gold (Pulsing Outline)
        pygame.draw.rect(surf, (0, 255, 128, 40), (x + w - 30, y + 10, 20, 20), border_radius=6)
        plus_glow = int(120 + 80 * math.sin(self.tick * 0.15))
        pygame.draw.rect(surf, (0, 255, 128, plus_glow), (x + w - 30, y + 10, 20, 20), width=1, border_radius=6)
        plus_g = FONT_SM.render("+", True, (0, 255, 128))
        surf.blit(plus_g, (x + w - 24, y + 10))

        # 2. Gem row (Floating Icon)
        float_y2 = int(math.cos(self.tick * 0.1) * 3)
        pygame.draw.circle(surf, (0, 220, 255, 40), (x + 23, y + 49 + float_y2), 12)
        draw_gem_icon(surf, x + 12, y + 37 + float_y2, 22)
        
        gemt_shadow = FONT_MED.render(f"{self.gems:,}", True, (10, 10, 15))
        gemt_main = FONT_MED.render(f"{self.gems:,}", True, (140, 220, 255))
        surf.blit(gemt_shadow, (x + 44, y + 39))
        surf.blit(gemt_main, (x + 42, y + 37))

        # Plus button Gems
        pygame.draw.rect(surf, (0, 255, 128, 40), (x + w - 30, y + 38, 20, 20), border_radius=6)
        pygame.draw.rect(surf, (0, 255, 128, plus_glow), (x + w - 30, y + 38, 20, 20), width=1, border_radius=6)
        surf.blit(plus_g, (x + w - 24, y + 38))

    def draw_garage(self):
        s = self._surf
        tick = self.tick

        # ── 1. Cyber metal plate dark background ──
        for y in range(SH):
            t = y / SH
            r = int(20 + 20 * t)
            g = int(12 + 15 * t)
            b = int(32 + 25 * t)
            pygame.draw.line(s, (r, g, b), (0, y), (SW, y))

        # Cyber diagonal grid lines (Parallax grid feel)
        for grid_x in range(0, SW, 60):
            pygame.draw.line(s, (0, 255, 255, 12), (grid_x, 0), (grid_x - 100, SH), 1)
        for grid_y in range(0, SH, 60):
            pygame.draw.line(s, (255, 0, 255, 12), (0, grid_y), (SW, grid_y + 100), 1)

        # ── 2. Screen Title ──
        title_t = FONT_TITLE.render("GA-RA XE TĂNG TỐI THƯỢNG", True, (255, 215, 0))
        title_sh = FONT_TITLE.render("GA-RA XE TĂNG TỐI THƯỢNG", True, (30, 20, 5))
        s.blit(title_sh, (SW // 2 - title_t.get_width() // 2 + 3, 15))
        s.blit(title_t, (SW // 2 - title_t.get_width() // 2, 12))

        # ── 3. Currency (top right) ──
        self._draw_currency_panel(s, SW - 310, 10)

        # Data configurations
        n = len(self.skin_names)
        tier_colors = [(120, 220, 120), (255, 180, 200), (100, 180, 255),
                       (200, 140, 255), (255, 220, 80)]
        tier_hp = [440, 540, 640, 740, 840]
        tier_dmg = [50, 70, 95, 120, 150]

        # ── 4. LEFT HAND PANEL: Selected Tank Containment Pedestal & Stats ──
        # Transparent glass capsule panel for selected tank display
        left_panel_rect = (40, 90, 560, 500)
        lpx, lpy, lpw, lph = left_panel_rect
        pygame.draw.rect(s, (10, 8, 20, 160), left_panel_rect, border_radius=20)
        pygame.draw.rect(s, (0, 255, 255, 60), left_panel_rect, width=2, border_radius=20)
        pygame.draw.rect(s, (255, 255, 255, 20), (lpx + 2, lpy + 2, lpw - 4, lph - 4), width=1, border_radius=18)

        # Draw tech bracket corners
        pygame.draw.line(s, (0, 255, 255), (lpx + 3, lpy + 15), (lpx + 3, lpy + 3), 3)
        pygame.draw.line(s, (0, 255, 255), (lpx + 3, lpy + 3), (lpx + 15, lpy + 3), 3)
        pygame.draw.line(s, (0, 255, 255), (lpx + lpw - 4, lpy + 15), (lpx + lpw - 4, lpy + 3), 3)
        pygame.draw.line(s, (0, 255, 255), (lpx + lpw - 4, lpy + 3), (lpx + lpw - 16, lpy + 3), 3)
        pygame.draw.line(s, (0, 255, 255), (lpx + 3, lpy + lph - 15), (lpx + 3, lpy + lph - 4), 3)
        pygame.draw.line(s, (0, 255, 255), (lpx + 3, lpy + lph - 4), (lpx + 15, lpy + lph - 4), 3)
        pygame.draw.line(s, (0, 255, 255), (lpx + lpw - 4, lpy + lph - 15), (lpx + lpw - 4, lpy + lph - 4), 3)
        pygame.draw.line(s, (0, 255, 255), (lpx + lpw - 4, lpy + lph - 4), (lpx + lpw - 16, lpy + lph - 4), 3)

        # Selected tank parameters
        is_sel_unlocked = self.skin_idx in self.unlocked_skins
        sel_color = tier_colors[self.skin_idx % len(tier_colors)]

        # Teleporter platform / Pedestal for selected tank
        ped_cx, ped_cy = lpx + lpw // 2, lpy + 210
        # Draw platform ellipses (cyber pedestal)
        for p_i in range(5):
            p_w = 180 - p_i * 15
            p_h = 42 - p_i * 4
            p_alpha = 150 - p_i * 25
            pygame.draw.ellipse(s, (0, 240, 255, p_alpha), (ped_cx - p_w // 2, ped_cy - p_h // 2 + p_i * 2, p_w, p_h), width=1)
        pygame.draw.ellipse(s, (20, 10, 30, 200), (ped_cx - 160 // 2, ped_cy - 36 // 2, 160, 36))
        pygame.draw.ellipse(s, (0, 255, 255, 180), (ped_cx - 160 // 2, ped_cy - 36 // 2, 160, 36), width=2)
        # Platform glow aura
        glow_surf = pygame.Surface((220, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (0, 255, 255, 30), (0, 0, 220, 60))
        s.blit(glow_surf, (ped_cx - 110, ped_cy - 30))

        # Glowing dynamic vertical particles rising from pedestal
        for pt_i in range(8):
            pt_x = ped_cx - 60 + int((pt_i * 17 + tick * 0.4) % 120)
            pt_y = ped_cy - 10 - int((pt_i * 11 + tick * 0.8) % 40)
            pt_alpha = max(0, int(150 * (1 - (ped_cy - pt_y) / 50)))
            pygame.draw.circle(s, (0, 255, 255, pt_alpha), (pt_x, pt_y), 2)

        # Draw Selected Tank (Gigantic & Anti-Aliased 3x scale)
        tank_size = 140
        bob = int(math.sin(tick * 0.08) * 8)
        d = (tick // 25) % 4
        tank_img = sprites.player_tiers_highres[self.skin_idx][d]
        scaled_tank = pygame.transform.smoothscale(tank_img, (tank_size, tank_size))

        if is_sel_unlocked:
            s.blit(scaled_tank, (ped_cx - tank_size // 2, ped_cy - tank_size // 2 - 35 + bob))
        else:
            # Draw cyber hologram lock look
            silhouette = scaled_tank.copy()
            silhouette.fill((0, 200, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(silhouette, (ped_cx - tank_size // 2, ped_cy - tank_size // 2 - 35 + bob))
            # Large glowing Lock badge
            pygame.draw.rect(s, (15, 15, 25, 220), (ped_cx - 24, ped_cy - 50 + bob, 48, 36), border_radius=6)
            pygame.draw.rect(s, (255, 0, 128), (ped_cx - 24, ped_cy - 50 + bob, 48, 36), width=2, border_radius=6)
            lock_t = FONT_MED.render("🔒", True, (255, 255, 255))
            s.blit(lock_t, (ped_cx - lock_t.get_width() // 2, ped_cy - 44 + bob))

        # ── STATS HUD inside left panel ──
        hud_top = lpy + 270
        # Tank Name
        name_t = FONT_TITLE.render(self.skin_names[self.skin_idx], True, sel_color)
        name_sh = FONT_TITLE.render(self.skin_names[self.skin_idx], True, (10, 10, 15))
        s.blit(name_sh, (ped_cx - name_t.get_width() // 2 + 2, hud_top + 1))
        s.blit(name_t, (ped_cx - name_t.get_width() // 2, hud_top))

        status_msg = "CHƯA SỞ HỮU"
        status_c = (255, 80, 80)
        if is_sel_unlocked:
            status_msg = "✓ ĐÃ SỞ HỮU & ĐANG CHỌN" if (self.skin_idx == self.skin_idx) else "ĐÃ MỞ KHÓA"
            status_c = (0, 255, 128)
        
        status_t = FONT_MED.render(status_msg, True, status_c)
        s.blit(status_t, (ped_cx - status_t.get_width() // 2, hud_top + 45))

        # Stars (Tier rating)
        num_stars = self.skin_idx + 1
        star_x_start = ped_cx - (num_stars * 26) // 2 + 3
        for star_i in range(num_stars):
            star_txt = FONT_BIG.render("★", True, (255, 215, 0))
            s.blit(star_txt, (star_x_start + star_i * 26, hud_top + 75))

        # Segmented HP progress bar
        hp_val = tier_hp[self.skin_idx]
        max_hp = 1000
        hp_ratio = hp_val / max_hp
        pygame.draw.rect(s, (20, 20, 30), (lpx + 60, hud_top + 130, 440, 24), border_radius=6)
        pygame.draw.rect(s, (0, 255, 128), (lpx + 63, hud_top + 133, int(434 * hp_ratio), 18), border_radius=4)
        hp_lbl = FONT_SM.render(f"ĐIỂM MÁU (HP): {hp_val}/{max_hp}", True, (255, 255, 255))
        s.blit(hp_lbl, (lpx + 72, hud_top + 133))

        # Segmented Damage progress bar
        dmg_val = tier_dmg[self.skin_idx]
        max_dmg = 200
        dmg_ratio = dmg_val / max_dmg
        pygame.draw.rect(s, (20, 20, 30), (lpx + 60, hud_top + 170, 440, 24), border_radius=6)
        pygame.draw.rect(s, (255, 100, 0), (lpx + 63, hud_top + 173, int(434 * dmg_ratio), 18), border_radius=4)
        dmg_lbl = FONT_SM.render(f"SỨC MẠNH BẮN: {dmg_val}/{max_dmg}", True, (255, 255, 255))
        s.blit(dmg_lbl, (lpx + 72, hud_top + 173))


        # ── 5. RIGHT HAND PANEL: Stack of 5 Elegant Skin Card Rows ──
        card_x = 640
        card_w = 600
        card_h = 80
        start_y = 90
        gap = 14

        for i in range(n):
            cy_card = start_y + i * (card_h + gap)
            is_card_sel = (i == self.skin_idx)
            is_card_unlocked = i in self.unlocked_skins
            tc = tier_colors[i % len(tier_colors)]

            # Card panel selection aura glow
            if is_card_sel:
                pulse = abs(math.sin(tick * 0.08))
                glow_card = pygame.Surface((card_w + 12, card_h + 12), pygame.SRCALPHA)
                pygame.draw.rect(glow_card, (*tc, int(45 + 35 * pulse)), (0, 0, card_w + 12, card_h + 12), border_radius=16)
                s.blit(glow_card, (card_x - 6, cy_card - 6))

            # Base card container
            fill = (25, 20, 40, 220) if is_card_sel else ((15, 12, 28, 170) if is_card_unlocked else (10, 8, 20, 100))
            card_border = tc if is_card_sel else ((100, 95, 120) if is_card_unlocked else (50, 45, 60))
            
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, fill, (0, 0, card_w, card_h), border_radius=12)
            pygame.draw.rect(card_surf, card_border, (0, 0, card_w, card_h), width=2 if is_card_sel else 1, border_radius=12)
            s.blit(card_surf, (card_x, cy_card))

            # Slanted glass sheen on selected card
            if is_card_sel:
                pygame.draw.line(s, (255, 255, 255, 80), (card_x + 2, cy_card + 2), (card_x + 8, cy_card + card_h - 2), 1)

            # Miniature tank icon
            mini_sz = 60
            mini_img = sprites.player_tiers_highres[i][1]
            scaled_mini = pygame.transform.smoothscale(mini_img, (mini_sz, mini_sz))
            if not is_card_unlocked:
                mini_dark = scaled_mini.copy()
                mini_dark.fill((0, 100, 180, 160), special_flags=pygame.BLEND_RGBA_MULT)
                s.blit(mini_dark, (card_x + 15, cy_card + 10))
                lock_sm = FONT_SM.render("🔒", True, (255, 255, 255))
                s.blit(lock_sm, (card_x + 35, cy_card + 30))
            else:
                s.blit(scaled_mini, (card_x + 15, cy_card + 10))

            # Tank Title text
            card_title = FONT_MED.render(self.skin_names[i], True, tc if is_card_unlocked else (100, 95, 110))
            s.blit(card_title, (card_x + 95, cy_card + 16))

            # Sub-desc (Tier & HP)
            card_desc = FONT_SM.render(f"CẤP ĐỘ {i+1}  |  HP {tier_hp[i]}", True, (180, 185, 200) if is_card_unlocked else (80, 75, 90))
            s.blit(card_desc, (card_x + 95, cy_card + 46))

            # Active/Selected checkmark or cost tag
            if is_card_unlocked:
                check_msg = "✓ ĐANG CHỌN" if is_card_sel else "ĐÃ MỞ KHÓA"
                check_color = (0, 255, 128) if is_card_sel else (140, 180, 160)
                check_t = FONT_MED.render(check_msg, True, check_color)
                s.blit(check_t, (card_x + card_w - check_t.get_width() - 25, cy_card + 26))
            else:
                cost = (i + 1) * 200
                cost_t = FONT_MED.render(f"{cost} 💎", True, (255, 235, 100))
                s.blit(cost_t, (card_x + card_w - cost_t.get_width() - 25, cy_card + 26))


        # ── 6. BOTTOM RIG DECK: BACK BUTTON & GIANT INTERACTIVE ACTION BUTTON ──
        # A. Back button (bottom-left)
        back_rect = pygame.Rect(40, SH - 85, 180, 48)
        pygame.draw.rect(s, (5, 3, 10, 150), (43, SH - 82, 180, 48), border_radius=12)
        pygame.draw.rect(s, (25, 12, 38, 200), back_rect, border_radius=12)
        pygame.draw.rect(s, (255, 80, 80, 180), back_rect, width=2, border_radius=12)
        pygame.draw.rect(s, (255, 255, 255, 45), (41, SH - 84, 178, 46), width=1, border_radius=11)
        
        pygame.draw.polygon(s, (255, 80, 80), [(52, SH - 61), (66, SH - 70), (66, SH - 52)])
        back_lbl = FONT_MED.render("QUAY LẠI", True, (255, 255, 255))
        s.blit(back_lbl, (80, SH - 61 - back_lbl.get_height() // 2))

        # B. Massive Interactive Cyber Upgrade/Select Action Button (bottom-right)
        action_rect = pygame.Rect(640, start_y + 5 * (card_h + gap) + 10, 600, 54)
        
        # Determine button status & colors
        if not is_sel_unlocked:
            cost = (self.skin_idx + 1) * 200
            btn_lbl = f"MUA XE TĂNG: {cost} 💎"
            btn_color = (255, 0, 128) if (self.gems >= cost) else (90, 40, 60)
            btn_border = (255, 50, 160) if (self.gems >= cost) else (120, 60, 80)
            btn_text_c = (255, 255, 255) if (self.gems >= cost) else (180, 150, 160)
        else:
            btn_lbl = "✓ ĐANG SỬ DỤNG XE NÀY"
            btn_color = (255, 180, 0)
            btn_border = (255, 220, 80)
            btn_text_c = (255, 255, 255)

        pygame.draw.rect(s, (5, 3, 10, 150), (action_rect.x + 4, action_rect.y + 4, action_rect.w, action_rect.h), border_radius=14)
        pygame.draw.rect(s, btn_color, action_rect, border_radius=14)
        pygame.draw.rect(s, btn_border, action_rect, width=2, border_radius=14)
        pygame.draw.rect(s, (255, 255, 255, 45), (action_rect.x + 1, action_rect.y + 1, action_rect.w - 2, action_rect.h - 2), width=1, border_radius=13)
        
        act_t = FONT_BIG.render(btn_lbl, True, btn_text_c)
        s.blit(act_t, (action_rect.x + action_rect.w // 2 - act_t.get_width() // 2, action_rect.y + action_rect.h // 2 - act_t.get_height() // 2))

        # Bottom hint bar
        ht = FONT_SM.render("←/→ HOẶC CLICK đẻ chọn xe tăng   ENTER HOẶC CLICK NÚT MUA để mở khóa", True, (160, 160, 180))
        s.blit(ht, (SW // 2 - ht.get_width() // 2, SH - 24))

    def draw_achievements(self):
        s = self._surf
        for y in range(SH):
            t = y / SH
            pygame.draw.line(s, (int(40 + 20 * t), int(30 + 15 * t),
                                 int(70 + 35 * t)), (0, y), (SW, y))
        draw_pastel_starfield(s, self.tick, density=50)

        draw_rainbow_text(s, "THÀNH TỰU", (SW // 2, 30), FONT_TITLE,
                          tick=self.tick)
        unlocked_count = len(self.achievements_unlocked)
        total = len(self.achievement_defs)
        sub = FONT_MED.render(f"{unlocked_count}/{total} đã đạt",
                              True, (255, 240, 200))
        s.blit(sub, (SW // 2 - sub.get_width() // 2, 95))

        # Grid of achievement cards
        cols = 2
        card_w, card_h = 360, 70
        gap_x, gap_y = 30, 16
        total_w = cols * card_w + (cols - 1) * gap_x
        start_x = SW // 2 - total_w // 2
        start_y = 140
        for i, (key, name_vi, label) in enumerate(self.achievement_defs):
            row = i // cols
            col = i % cols
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            unlocked = key in self.achievements_unlocked
            border = (255, 220, 100) if unlocked else (110, 90, 130)
            fill = (75, 55, 110) if unlocked else (45, 35, 70)
            draw_kawaii_panel(s, (x, y, card_w, card_h), fill=fill,
                              border=border, radius=14, shadow_offset=3,
                              glow=unlocked)
            # Trophy / lock icon
            ic_x, ic_y = x + 18, y + card_h // 2
            if unlocked:
                # Star/trophy
                pygame.draw.circle(s, (255, 220, 80), (ic_x + 14, ic_y), 18)
                pygame.draw.circle(s, (200, 130, 30), (ic_x + 14, ic_y), 18, 3)
                star = FONT_MED.render("*", True, (255, 100, 30))
                s.blit(star, (ic_x + 14 - star.get_width() // 2,
                              ic_y - star.get_height() // 2))
            else:
                pygame.draw.rect(s, (90, 80, 110),
                                 (ic_x, ic_y - 12, 28, 24), border_radius=4)
                pygame.draw.rect(s, (200, 200, 220),
                                 (ic_x + 4, ic_y - 18, 20, 16), 2,
                                 border_radius=8)
            # Text
            nt = FONT_MED.render(name_vi, True,
                                 (255, 240, 220) if unlocked else (170, 160, 190))
            s.blit(nt, (x + 60, y + 14))
            dt = FONT_SM.render(label, True,
                                (220, 220, 250) if unlocked else (140, 130, 160))
            s.blit(dt, (x + 60, y + 40))

        # Back button
        back_rect = pygame.Rect(SW // 2 - 80, SH - 50, 160, 40)
        draw_kawaii_button(s, back_rect, "QUAY LẠI", FONT_MED, selected=False, tick=self.tick)

    def _check_achievements(self):
        u = self.achievements_unlocked
        if self.total_kills >= 1: u.add("FIRST_BLOOD")
        if self.level >= 5 and self.stats.get("levels_completed", 0) >= 5:
            u.add("LEVEL_5")
        if self.level >= 10 and self.stats.get("levels_completed", 0) >= 10:
            u.add("LEVEL_10")
        if self.stats.get("bosses_killed", 0) >= 1: u.add("BOSS_SLAYER")
        if self.total_money_earned >= 5000: u.add("RICH")
        if self.player_tier >= 4: u.add("MAX_TIER")
        if self.freeze_uses >= 3: u.add("FROZEN_HUNTER")
        if self.grenade_uses >= 5: u.add("GRENADIER")

    def _draw_profile_panel(self, surf, x, y):
        # Player profile (top-left): tank avatar + name (Extremely Exquisite Sci-Fi HUD)
        w, h = 240, 70
        
        # Glassmorphic cyber capsule
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (20, 10, 30, 160), (0, 0, w, h), border_radius=16)
        # Cyan neon border
        pygame.draw.rect(panel_surf, (0, 255, 255, 70), (0, 0, w, h), width=3, border_radius=16)
        pygame.draw.rect(panel_surf, (255, 255, 255, 120), (2, 2, w - 4, h - 4), width=1, border_radius=14)
        
        # Tech corners
        pygame.draw.line(panel_surf, (0, 255, 255), (3, 8), (3, 3), 2)
        pygame.draw.line(panel_surf, (0, 255, 255), (3, 3), (8, 3), 2)
        pygame.draw.line(panel_surf, (0, 255, 255), (w - 4, 8), (w - 4, 3), 2)
        pygame.draw.line(panel_surf, (0, 255, 255), (w - 4, 3), (w - 9, 3), 2)
        pygame.draw.line(panel_surf, (0, 255, 255), (3, h - 9), (3, h - 4), 2)
        pygame.draw.line(panel_surf, (0, 255, 255), (3, h - 4), (8, h - 4), 2)
        pygame.draw.line(panel_surf, (0, 255, 255), (w - 4, h - 9), (w - 4, h - 4), 2)
        pygame.draw.line(panel_surf, (0, 255, 255), (w - 4, h - 4), (w - 9, h - 4), 2)
        
        surf.blit(panel_surf, (x, y))

        # Live Scanning Pulse Ring
        pulse_r = 24 + (self.tick % 60) * 0.4
        pulse_a = max(0, int(150 * (1 - (self.tick % 60) / 60)))
        pygame.draw.circle(surf, (0, 255, 255, pulse_a), (x + 35, y + 35), int(pulse_r), width=1)

        # Avatar circle glow
        pygame.draw.circle(surf, (0, 255, 255, 40), (x + 35, y + 35), 24)
        pygame.draw.circle(surf, (0, 255, 255, 150), (x + 35, y + 35), 24, width=1)

        # Avatar tank image
        tier = min(len(sprites.player_tiers) - 1, self.skin_idx)
        avatar = pygame.transform.scale(sprites.player_tiers[tier][0], (36, 36))
        surf.blit(avatar, (x + 17, y + 17))

        # LV.99 Cyber Badge
        badge_font = pygame.font.SysFont("Consolas", 10, bold=True)
        lv_txt = badge_font.render("LV.99", True, (0, 255, 255))
        pygame.draw.rect(surf, (0, 255, 255, 30), (x + 10, y + 4, 32, 12), border_radius=3)
        pygame.draw.rect(surf, (0, 255, 255, 120), (x + 10, y + 4, 32, 12), width=1, border_radius=3)
        surf.blit(lv_txt, (x + 12, y + 4))

        # Title Label — login provider if any, otherwise "CHIEN BINH"
        if self.login_done and self.login_provider:
            role_lbl = f"@ {self.login_provider}"
        else:
            role_lbl = "CHIEN BINH"
        nm_shadow = FONT_SM.render(role_lbl, True, (10, 10, 15))
        nm_main = FONT_SM.render(role_lbl, True, (0, 255, 255))
        surf.blit(nm_shadow, (x + 72, y + 10))
        surf.blit(nm_main, (x + 70, y + 8))

        # Nick Name in bold white (use login username if available)
        nick_str = self.player_name
        if self.login_done and self.login_username:
            # Trim any provider-suffix to keep it readable in the small pill
            nick_str = self.login_username.split(" · ")[0].split(" (")[0]
        nick_shadow = FONT_MED.render(nick_str, True, (10, 10, 15))
        nick_main = FONT_MED.render(nick_str, True, (255, 255, 255))
        surf.blit(nick_shadow, (x + 72, y + 32))
        surf.blit(nick_main, (x + 70, y + 30))

        # segmented XP level progress bar
        bar_x, bar_y, bar_w, bar_h = x + 70, y + 54, 150, 6
        pygame.draw.rect(surf, (20, 20, 35), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        progress_w = int(bar_w * 0.73)
        pygame.draw.rect(surf, (0, 255, 255), (bar_x, bar_y, progress_w, bar_h), border_radius=3)
        pygame.draw.rect(surf, (255, 255, 255), (bar_x, bar_y, progress_w - 2, 2), border_radius=1)

    def draw_tutorial(self):
        s = self._surf
        for y in range(SH):
            t = y / SH
            pygame.draw.line(s, (int(10 + 15 * t), int(12 + 18 * t), int(25 + 35 * t)), (0, y), (SW, y))

        # Header
        title = FONT_TITLE.render("HƯỚNG DẪN CHƠI", True, (255, 220, 50))
        s.blit(title, (SW // 2 - title.get_width() // 2, 15))
        pygame.draw.line(s, (255, 220, 50), (50, 65), (SW - 50, 65), 2)

        pages = [
            {
                "title": "ĐIỀU KHIỂN CƠ BẢN",
                "items": [
                    ("W A S D / Phím Mũi Tên", "Di chuyển xe tăng 4 hướng"),
                    ("SPACE", "Bắn đạn - giữ để bắn liên tục"),
                    ("SHIFT + Di chuyển", "Chạy nhanh (tốn năng lượng)"),
                    ("ESC", "Tạm dừng / Menu"),
                    ("Phím 1, 2, 3", "Sử dụng vật phẩm trong ba lô"),
                ]
            },
            {
                "title": "CHẾ ĐỘ TỰ ĐỘNG (AUTO)",
                "items": [
                    ("Phím F", "Bật/Tắt chế độ tự động (có buff)"),
                    ("Phím G", "Đổi thuật toán: A*, BFS, DFS"),
                    ("A* (Mặc định)", "Tìm đường ngắn nhất, có phá tường"),
                    ("BFS", "Tìm đường rộng, chỉ đi đường trống"),
                    ("DFS", "Tìm đường sâu, ngẫu nhiên hơn"),
                ]
            },
            {
                "title": "VẬT PHẨM & CỬA HÀNG",
                "items": [
                    ("Máu (Health)", "Hồi 1 điểm máu"),
                    ("Giáp (Shield)", "Chặn 3 phát đạn"),
                    ("Năng lượng", "Hồi đầy thanh chạy nhanh"),
                    ("Bom Nguyên Tử (Star)", "Tiêu diệt toàn bộ kẻ địch"),
                    ("Ba lô chứa tối đa 3 vật phẩm", "Mua trong shop, dùng bằng phím 1-3"),
                ]
            },
            {
                "title": "BẢN ĐỒ & BOSS",
                "items": [
                    ("7 địa hình", "Rừng Kawaii, Chiến trường, Sa mạc, Băng, Thành phố, Rừng, Núi lửa"),
                    ("Mỗi 5 màn", "Boss xuất hiện - rất mạnh!"),
                    ("Gà", "Bắn để lấy tiền"),
                    ("Chó", "Đuổi cắn người chơi - nguy hiểm!"),
                    ("Căn cứ", "Bảo vệ căn cứ ở phía dưới bản đồ"),
                ]
            }
        ]

        page = pages[self.tutorial_page]

        # Page title
        pt = FONT_BIG.render(page["title"], True, (100, 220, 255))
        s.blit(pt, (SW // 2 - pt.get_width() // 2, 85))

        # Items
        for i, (key, desc) in enumerate(page["items"]):
            y_pos = 140 + i * 70

            # Key box
            key_bg = pygame.Surface((SW - 80, 55), pygame.SRCALPHA)
            pygame.draw.rect(key_bg, (30, 40, 60, 200), (0, 0, SW - 80, 55), border_radius=8)
            pygame.draw.rect(key_bg, (60, 90, 140), (0, 0, SW - 80, 55), 1, border_radius=8)
            s.blit(key_bg, (40, y_pos))

            # Key label
            key_t = FONT_MED.render(key, True, (255, 220, 80))
            s.blit(key_t, (60, y_pos + 8))

            # Description
            desc_t = FONT_SM.render(desc, True, (180, 185, 200))
            s.blit(desc_t, (60, y_pos + 32))

        # Page indicator
        page_t = FONT_SM.render(f"Trang {self.tutorial_page + 1}/{len(pages)}", True, (150, 150, 170))
        s.blit(page_t, (SW // 2 - page_t.get_width() // 2, SH - 70))

        # Navigation buttons
        prev_rect = pygame.Rect(SW // 2 - 250, SH - 48, 130, 36)
        next_rect = pygame.Rect(SW // 2 - 65, SH - 48, 130, 36)
        back_rect = pygame.Rect(SW // 2 + 120, SH - 48, 140, 36)
        draw_kawaii_button(s, prev_rect, "◄ TRƯỚC", FONT_SM, selected=False, tick=self.tick)
        draw_kawaii_button(s, next_rect, "TIẾP ►", FONT_SM, selected=False, tick=self.tick)
        draw_kawaii_button(s, back_rect, "QUAY LẠI", FONT_SM, selected=False, tick=self.tick)

        # Page dots
        for i in range(len(pages)):
            cx = SW // 2 - (len(pages) * 12) // 2 + i * 12 + 6
            c = (255, 220, 50) if i == self.tutorial_page else (60, 70, 90)
            pygame.draw.circle(s, c, (cx, SH - 85), 4)

    def draw_gameover(self):
        self.draw_game()
        s = self._surf
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        s.blit(overlay, (0, 0))

        # Vignette effect
        for i in range(3):
            vig = pygame.Surface((SW, SH), pygame.SRCALPHA)
            pygame.draw.rect(vig, (80, 0, 0, 20 - i * 5), (i * 10, i * 10, SW - i * 20, SH - i * 20), i * 5 + 5)
            s.blit(vig, (0, 0))

        text = FONT_HUGE.render("KẾT THÚC", True, (255, 50, 50))
        shadow = FONT_HUGE.render("KẾT THÚC", True, (80, 0, 0))
        s.blit(shadow, (SW // 2 - text.get_width() // 2 + 3, SH // 2 - 78))
        s.blit(text, (SW // 2 - text.get_width() // 2, SH // 2 - 80))

        score_t = FONT_MED.render(f"ĐIỂM SỐ: {self.score}", True, (255, 215, 80))
        s.blit(score_t, (SW // 2 - score_t.get_width() // 2, SH // 2 - 10))

        stats_lines = [
            f"Xe tăng tiêu diệt: {self.total_kills}",
            f"Màn đạt được: {self.level}",
            f"Chuỗi cao nhất: {self.stats['max_combo']}",
        ]
        for i, line in enumerate(stats_lines):
            lt = FONT_SM.render(line, True, (180, 185, 200))
            s.blit(lt, (SW // 2 - lt.get_width() // 2, SH // 2 + 20 + i * 22))

        cont_rect = pygame.Rect(SW // 2 - 120, SH // 2 + 90, 240, 44)
        draw_kawaii_button(s, cont_rect, "TIẾP TỤC", FONT_MED, selected=True, tick=self.tick)

    def draw_level_clear(self):
        s = self._surf
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        s.blit(overlay, (0, 0))

        # Victory sparkles
        for i in range(30):
            x = (i * 47 + self.tick * 2) % SW
            y = (i * 31 + self.tick) % SH
            a = int(abs(math.sin(self.tick * 0.1 + i)) * 220)
            c = [(255, 255, 100), (100, 255, 200), (255, 150, 255), (100, 200, 255)][i % 4]
            ps = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*c, max(0, a)), (4, 4), 3)
            s.blit(ps, (int(x), int(y)))

        # Story-driven level clear messages
        _clear_stories = [
            "Làng quê đã được giải phóng!",
            "Tiền đồn phía Bắc đã bị chiếm!",
            "Ổ phục kích đã bị phá!",
            "Đã vượt qua sa mạc thành công!",
            "Tướng Sa Mạc đã bị tiêu diệt! Vùng sa mạc tự do!",
            "Bão tuyết đã qua — chiến thắng!",
            "Căn cứ địch đã bị phá hủy!",
            "Đã phá vòng vây thành công!",
            "Sống sót qua tuyết lở!",
            "Tướng Băng Giá đã bị tiêu diệt! Vùng tuyết tự do!",
            "Rừng rậm đã an toàn!",
            "Đầm lầy đã được giải phóng!",
            "Đã giành lại lãnh thổ!",
            "Hang núi bí mật đã bị phá!",
            "Tướng Rừng Rậm bị tiêu diệt! Vùng rừng tự do!",
            "Thành phố đã được giải phóng!",
            "Pháo đài cuối cùng đã sụp đổ!",
            "Tổng tấn công thành công!",
            "Cổng sào huyệt đã mở!",
            "THẾ GIỚI ĐÃ ĐƯỢC GIẢI CỨU! BẠN LÀ ANH HÙNG!",
        ]

        # Check if this is the final level victory
        is_final = (self.level >= self.max_levels)

        if is_final:
            # Epic final victory
            title_text = "THẾ GIỚI ĐÃ ĐƯỢC GIẢI CỨU!"
            title_color = (255, 215, 0)
            text = FONT_TITLE.render(title_text, True, title_color)
            shadow = FONT_TITLE.render(title_text, True, (100, 80, 0))
            s.blit(shadow, (SW // 2 - text.get_width() // 2 + 2, SH // 2 - 118))
            s.blit(text, (SW // 2 - text.get_width() // 2, SH // 2 - 120))

            hero_t = FONT_MED.render("BẠN LÀ ANH HÙNG CỨU THẾ GIỚI!", True, (255, 255, 100))
            s.blit(hero_t, (SW // 2 - hero_t.get_width() // 2, SH // 2 - 70))
        else:
            text = FONT_TITLE.render(f"MÀN {self.level} HOÀN THÀNH!", True, (80, 255, 130))
            shadow = FONT_TITLE.render(f"MÀN {self.level} HOÀN THÀNH!", True, (0, 60, 20))
            s.blit(shadow, (SW // 2 - text.get_width() // 2 + 2, SH // 2 - 118))
            s.blit(text, (SW // 2 - text.get_width() // 2, SH // 2 - 120))

        # Story message
        idx = min(self.level - 1, len(_clear_stories) - 1)
        story_msg = _clear_stories[idx]
        story_t = FONT_SM.render(story_msg, True, (255, 230, 150))
        s.blit(story_t, (SW // 2 - story_t.get_width() // 2, SH // 2 - 50))

        score_t = FONT_MED.render(f"ĐIỂM: {self.score}", True, (255, 215, 80))
        s.blit(score_t, (SW // 2 - score_t.get_width() // 2, SH // 2 - 20))

        kills_t = FONT_SM.render(f"TIÊU DIỆT: {self.kills} / {self.total_enemies}", True, (200, 220, 200))
        s.blit(kills_t, (SW // 2 - kills_t.get_width() // 2, SH // 2 + 10))

        money_t = FONT_SM.render(f"TIỀN: {self.money}đ", True, (100, 255, 120))
        s.blit(money_t, (SW // 2 - money_t.get_width() // 2, SH // 2 + 35))

        # Gem reward notification
        gem_reward = 1 + self.level // 5  # more gems for boss levels
        gem_msg = FONT_SM.render(f"+ {gem_reward} ĐÁ QUÝ thưởng qua màn!", True, (150, 220, 255))
        s.blit(gem_msg, (SW // 2 - gem_msg.get_width() // 2, SH // 2 + 55))

        if is_final:
            cont_rect = pygame.Rect(SW // 2 - 120, SH // 2 + 90, 240, 44)
            draw_kawaii_button(s, cont_rect, "VỀ SẢNH", FONT_MED, selected=True, tick=self.tick)
        else:
            # Next level preview
            next_theme = self.get_theme_for_level(self.level + 1)
            theme_names = {"default": "CHIẾN TRƯỜNG", "desert": "SA MẠC", "snow": "BĂNG GIÁ",
                          "city": "THÀNH PHỐ", "jungle": "RỪNG RẬM", "lava": "NÚI LỬA",
                          "kawaii_woodland": "RỪNG KAWAII"}
            next_t = FONT_SM.render(f"Màn tiếp theo: {theme_names.get(next_theme, '???')}", True, (160, 180, 220))
            s.blit(next_t, (SW // 2 - next_t.get_width() // 2, SH // 2 + 78))

            cont_rect = pygame.Rect(SW // 2 - 120, SH // 2 + 100, 240, 44)
            draw_kawaii_button(s, cont_rect, "TIẾP TỤC", FONT_MED, selected=True, tick=self.tick)

    def draw_pause(self):
        self.draw_game()
        s = self._surf
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        s.blit(overlay, (0, 0))

        title = FONT_TITLE.render("TẠM DỪNG", True, (255, 255, 255))
        s.blit(title, (SW // 2 - title.get_width() // 2, SH // 4 - 20))

        for i, item in enumerate(self.pause_items):
            is_sel = i == self.pause_sel
            if is_sel:
                pulse = abs(math.sin(self.tick * 0.15))
                color = (min(255, int(255 + 50 * pulse)), min(255, int(220 + 35 * pulse)), 50)
                # Selection background
                txt_temp = FONT_MED.render(item, True, color)
                rect = txt_temp.get_rect(center=(SW // 2, SH // 2 - 60 + i * 45))
                sel_bg = pygame.Surface((rect.width + 40, rect.height + 14), pygame.SRCALPHA)
                pygame.draw.rect(sel_bg, (50, 60, 100, 180), (0, 0, rect.width + 40, rect.height + 14), border_radius=8)
                pygame.draw.rect(sel_bg, (100, 150, 255), (0, 0, rect.width + 40, rect.height + 14), 2, border_radius=8)
                s.blit(sel_bg, (rect.x - 20, rect.y - 7))
            else:
                color = (130, 130, 140)

            txt = FONT_MED.render(item, True, color)
            rect = txt.get_rect(center=(SW // 2, SH // 2 - 60 + i * 45))
            s.blit(txt, rect)

        instr = FONT_SM.render("[ MŨI TÊN ] CHỌN  -  [ ENTER ] ĐỒNG Ý", True, (100, 110, 130))
        s.blit(instr, (SW // 2 - instr.get_width() // 2, SH - 80))

    def draw_backpack_ui(self, surf):
        # Compact backpack: was slot_size=80; shrunk ~40% so it doesn't
        # crowd the HUD on the new wider maps.
        slot_size = 48
        margin = 6
        max_slots = self.backpack_slots
        bp_t = FONT_SM.render("BA LÔ", True, (200, 220, 255))
        label_w = bp_t.get_width()
        by = 8
        label_x = 10
        bx = label_x + label_w + 10

        surf.blit(bp_t, (label_x, by + slot_size // 2 - bp_t.get_height() // 2 + 4))

        for i in range(3):
            sx = bx + i * (slot_size + margin)
            sy = by + 4
            is_locked = i >= max_slots
            has_item = i < len(self.backpack)

            slot_bg = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            if is_locked:
                pygame.draw.rect(slot_bg, (15, 15, 20, 185), (0, 0, slot_size, slot_size), border_radius=7)
                pygame.draw.rect(slot_bg, (40, 35, 50), (0, 0, slot_size, slot_size), 1, border_radius=7)
            else:
                pygame.draw.rect(slot_bg, (25, 28, 40, 210), (0, 0, slot_size, slot_size), border_radius=7)
                border_c = (0, 255, 255) if has_item else (60, 65, 80)
                pygame.draw.rect(slot_bg, border_c, (0, 0, slot_size, slot_size), 2, border_radius=7)
                pygame.draw.rect(slot_bg, (255, 255, 255, 60), (1, 1, slot_size - 2, slot_size - 2), 1, border_radius=6)
            surf.blit(slot_bg, (sx, sy))

            if is_locked:
                lock_cx = sx + slot_size // 2
                lock_cy = sy + slot_size // 2
                pygame.draw.rect(surf, (80, 75, 95), (lock_cx - 6, lock_cy - 2, 12, 10), border_radius=2)
                pygame.draw.arc(surf, (80, 75, 95), (lock_cx - 4, lock_cy - 8, 8, 10), 0, math.pi, 2)
                pygame.draw.circle(surf, (40, 35, 50), (lock_cx, lock_cy + 2), 2)
            else:
                num_t = FONT_SM.render(str(i + 1), True, (130, 140, 160))
                surf.blit(num_t, (sx + 4, sy + 2))

                if has_item:
                    kind = self.backpack[i]
                    if kind in sprites.items:
                        img = pygame.transform.smoothscale(sprites.items[kind], (32, 32))
                        surf.blit(img, (sx + 8, sy + 10))
                    item_names = {
                        "multi": "Đa Hướng", "rapid": "Siêu Tốc", "pierce": "Xuyên Phá",
                        "bomb": "Bom Nổ", "laser": "Laser", "plasma": "Plasma",
                        "shield": "Giáp", "health": "Hồi Máu", "speed": "NL",
                        "star": "Bom NT", "life": "Mạng", "rocket": "Tên Lửa",
                        "flame": "Phun Lửa", "freeze": "Đ.Băng", "grenade": "Lựu Đạn",
                        "max_power": "Max Sức",
                    }
                    tt_name = item_names.get(kind, kind.upper())
                    tt = FONT_SM.render(tt_name, True, (180, 200, 230))
                    surf.blit(tt, (sx + slot_size // 2 - tt.get_width() // 2, sy + slot_size + 2))
                    hl = pygame.Surface((slot_size - 4, 14), pygame.SRCALPHA)
                    pygame.draw.ellipse(hl, (255, 255, 255, 30), (0, 0, slot_size - 4, 14))
                    surf.blit(hl, (sx + 2, sy + 2))

# ═══════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════
def main():
    global phys_w, phys_h
    _show_boot_splash("Đang chuẩn bị video sảnh...",
                      "Tạo các hiệu ứng & cảnh nền")
    game = Game()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                game._save_game(); pygame.quit(); sys.exit()
            elif ev.type == pygame.VIDEORESIZE:
                # Update physical width & height dynamically when user resizes the window
                phys_w, phys_h = ev.size
                if not is_fullscreen:
                    pygame.display.set_mode((phys_w, phys_h), pygame.RESIZABLE)
            game.handle_event(ev)
        game.update()
        game.draw()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
