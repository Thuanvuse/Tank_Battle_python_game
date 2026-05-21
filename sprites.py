"""
PREMIUM ULTRA DELUXE Sprite Engine v3.0 — 20x SUPERSAMPLED EDITION
Tank Dai Chien - ULTIMATE EDITION
Enhanced visuals, detailed tanks, premium tiles, weather effects, minimap support

All sprites are rendered internally at 20x resolution then smoothscaled down
to the original size, producing dramatically sharper, anti-aliased graphics
while keeping TS=32 for full game compatibility.
Chicken and dog sprites feature realistic anatomy with detailed feathers/fur.
"""
import os
import pygame, math, random
from enum import Enum

TS = 32          # tile display size
# Internal render multiplier.  Was 20 (=> 640x640 hi-res tile) which made
# the first launch take 20-40s on slower PCs while the sprite cache built.
# 6x still produces beautifully anti-aliased sprites but is ~10x faster
# to generate.
_R = 6
_RTS = TS * _R   # internal render tile size


def _S(v):
    """Scale a pixel value for internal hi-res rendering."""
    return int(v * _R)


def _downscale(surf, target_w=None, target_h=None):
    """Smoothscale a hi-res surface down to its target display size."""
    if target_w is None:
        target_w = surf.get_width() // _R
    if target_h is None:
        target_h = surf.get_height() // _R
    return pygame.transform.smoothscale(surf, (target_w, target_h))


# Reference asset image
ASSET_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "assets", "tank_battle_assets.png")

PIXEL_ART_ITEM_BOXES = {
    "freeze":    (470, 250, 545, 320),
    "max_power": (545, 320, 620, 390),
    "grenade":   (620, 250, 695, 320),
    "life":      (620, 320, 695, 390),
}


def _slice_pixel_art_item(asset_surface, box, output_size=30):
    left, top, right, bottom = box
    w = right - left
    h = bottom - top
    if (left < 0 or top < 0 or
            right > asset_surface.get_width() or
            bottom > asset_surface.get_height()):
        return None

    cell = pygame.Surface((w, h), pygame.SRCALPHA)
    src_rect = pygame.Rect(left, top, w, h)
    cell.blit(asset_surface, (0, 0), src_rect)

    samples = []
    step = max(1, w // 8)
    for x in range(0, w, step):
        samples.append(cell.get_at((x, 0))[:3])
        samples.append(cell.get_at((x, h - 1))[:3])
    step = max(1, h // 8)
    for y in range(0, h, step):
        samples.append(cell.get_at((0, y))[:3])
        samples.append(cell.get_at((w - 1, y))[:3])

    out = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            r, g, b, _ = cell.get_at((x, y))
            keep = True
            if r + g + b < 60:
                keep = False
            else:
                for sr, sg, sb in samples:
                    dr, dg, db = r - sr, g - sg, b - sb
                    if dr * dr + dg * dg + db * db < 25 * 25:
                        keep = False
                        break
            if keep:
                out.set_at((x, y), (r, g, b, 255))

    return pygame.transform.smoothscale(out, (output_size, output_size))


def try_load_pixel_art_items(asset_path=ASSET_IMAGE_PATH):
    if not os.path.exists(asset_path):
        return {}
    try:
        asset = pygame.image.load(asset_path).convert_alpha()
    except Exception as exc:
        print(f"[sprites] Could not load pixel art asset: {exc}")
        return {}

    result = {}
    for kind, box in PIXEL_ART_ITEM_BOXES.items():
        try:
            icon = _slice_pixel_art_item(asset, box)
            if icon is not None:
                result[kind] = icon
        except Exception as exc:
            print(f"[sprites] Slice failed for {kind}: {exc}")
    return result

# ═══════════════════════════════════════════════
#  MATERIAL & COLOR SYSTEM
# ═══════════════════════════════════════════════
class Material(Enum):
    MATTE = 0
    METALLIC = 1
    RUSTY = 2
    CAMO = 3
    CHROME = 4
    NEON = 5

bullet_colors = {
    "normal": (255, 225, 80),
    "enemy": (255, 110, 85),
    "pierce": (80, 200, 255),
    "bomb": (255, 100, 50),
    "laser": (0, 255, 180),
    "plasma": (200, 50, 255),
}

TANK_COLORS = {
    "player": {
        "body_base": (50, 200, 80), "body_shadow": (30, 140, 45), "body_highlight": (120, 255, 150),
        "body_specular": (200, 255, 220), "material": Material.METALLIC,
        "turret_base": (40, 170, 60), "turret_highlight": (100, 220, 130),
        "barrel_base": (70, 210, 100), "barrel_highlight": (150, 245, 170),
        "track_base": (30, 70, 35), "track_highlight": (55, 110, 60), "track_rivet": (80, 140, 85),
        "accent": (200, 255, 180), "eye_bg": (255, 255, 245), "pupil": (20, 20, 25),
        "blush": (255, 140, 140), "camo_color": (100, 200, 70),
        "stripe": (255, 220, 50), "emblem": (255, 255, 255),
    },
    "enemy_a": {
        "body_base": (220, 60, 60), "body_shadow": (160, 30, 30), "body_highlight": (255, 130, 120),
        "body_specular": (255, 190, 180), "material": Material.RUSTY,
        "turret_base": (190, 45, 45), "turret_highlight": (240, 120, 110),
        "barrel_base": (245, 95, 85), "barrel_highlight": (255, 160, 150),
        "track_base": (100, 30, 30), "track_highlight": (140, 50, 50), "track_rivet": (170, 70, 70),
        "accent": (255, 180, 170), "eye_bg": (255, 245, 240), "pupil": (25, 20, 20),
        "blush": (255, 160, 160), "camo_color": (190, 70, 50),
        "stripe": (200, 40, 40), "emblem": (255, 200, 200),
    },
    "enemy_b": {
        "body_base": (60, 90, 220), "body_shadow": (30, 50, 160), "body_highlight": (110, 140, 255),
        "body_specular": (170, 200, 255), "material": Material.METALLIC,
        "turret_base": (45, 65, 190), "turret_highlight": (110, 130, 240),
        "barrel_base": (80, 110, 245), "barrel_highlight": (140, 170, 255),
        "track_base": (25, 40, 100), "track_highlight": (45, 65, 140), "track_rivet": (65, 85, 170),
        "accent": (170, 190, 255), "eye_bg": (245, 248, 255), "pupil": (20, 20, 25),
        "blush": (160, 180, 255), "camo_color": (50, 70, 190),
        "stripe": (100, 130, 255), "emblem": (200, 220, 255),
    },
    "elite": {
        "body_base": (50, 50, 55), "body_shadow": (25, 25, 30), "body_highlight": (90, 90, 100),
        "body_specular": (140, 140, 155), "material": Material.CHROME,
        "turret_base": (40, 40, 45), "turret_highlight": (80, 80, 95),
        "barrel_base": (70, 70, 80), "barrel_highlight": (120, 120, 135),
        "track_base": (20, 20, 25), "track_highlight": (40, 40, 50), "track_rivet": (60, 60, 70),
        "accent": (255, 80, 30), "eye_bg": (255, 250, 245), "pupil": (255, 40, 10),
        "blush": (100, 10, 10), "camo_color": (35, 35, 40),
        "stripe": (255, 150, 0), "emblem": (255, 50, 50),
    },
    "boss": {
        "body_base": (80, 20, 100), "body_shadow": (50, 10, 65), "body_highlight": (140, 60, 180),
        "body_specular": (200, 120, 240), "material": Material.NEON,
        "turret_base": (70, 15, 90), "turret_highlight": (130, 50, 170),
        "barrel_base": (120, 40, 160), "barrel_highlight": (180, 100, 220),
        "track_base": (40, 10, 55), "track_highlight": (60, 20, 80), "track_rivet": (90, 40, 110),
        "accent": (255, 0, 200), "eye_bg": (255, 200, 255), "pupil": (255, 0, 100),
        "blush": (200, 50, 200), "camo_color": (100, 20, 130),
        "stripe": (255, 0, 255), "emblem": (255, 150, 255),
    },
}

# ═══════════════════════════════════════════════
#  BOSS COLOR SCHEMES — 4 unique bosses
# ═══════════════════════════════════════════════
BOSS_COLORS = {
    "boss_desert": {  # Boss 1 (Level 5) — Tướng Sa Mạc — scorpion gold/sand
        "body_base": (200, 160, 60), "body_shadow": (140, 100, 30), "body_highlight": (255, 220, 120),
        "body_specular": (255, 245, 180), "material": Material.CHROME,
        "turret_base": (180, 130, 40), "turret_highlight": (240, 200, 100),
        "barrel_base": (220, 170, 60), "barrel_highlight": (255, 230, 140),
        "track_base": (100, 70, 20), "track_highlight": (140, 100, 40), "track_rivet": (180, 140, 60),
        "accent": (255, 100, 0), "eye_bg": (255, 240, 200), "pupil": (200, 50, 0),
        "blush": (255, 120, 60), "camo_color": (180, 140, 50),
        "stripe": (255, 80, 0), "emblem": (255, 200, 50),
        "glow_color": (255, 150, 30), "spike_color": (200, 100, 0),
    },
    "boss_ice": {  # Boss 2 (Level 10) — Tướng Băng Giá — crystal ice blue
        "body_base": (60, 140, 220), "body_shadow": (30, 80, 160), "body_highlight": (140, 210, 255),
        "body_specular": (200, 240, 255), "material": Material.CHROME,
        "turret_base": (40, 120, 200), "turret_highlight": (120, 190, 255),
        "barrel_base": (80, 160, 240), "barrel_highlight": (160, 220, 255),
        "track_base": (20, 60, 120), "track_highlight": (40, 90, 160), "track_rivet": (60, 120, 200),
        "accent": (0, 200, 255), "eye_bg": (220, 245, 255), "pupil": (0, 80, 200),
        "blush": (100, 180, 255), "camo_color": (50, 100, 180),
        "stripe": (0, 220, 255), "emblem": (180, 240, 255),
        "glow_color": (100, 200, 255), "spike_color": (0, 150, 255),
    },
    "boss_jungle": {  # Boss 3 (Level 15) — Tướng Rừng Rậm — toxic green/purple
        "body_base": (40, 160, 40), "body_shadow": (20, 100, 20), "body_highlight": (100, 230, 80),
        "body_specular": (160, 255, 140), "material": Material.NEON,
        "turret_base": (30, 140, 30), "turret_highlight": (80, 210, 70),
        "barrel_base": (60, 180, 50), "barrel_highlight": (120, 240, 100),
        "track_base": (15, 60, 15), "track_highlight": (30, 90, 25), "track_rivet": (50, 120, 40),
        "accent": (180, 0, 255), "eye_bg": (200, 255, 200), "pupil": (150, 0, 200),
        "blush": (100, 200, 50), "camo_color": (30, 120, 30),
        "stripe": (200, 50, 255), "emblem": (150, 255, 100),
        "glow_color": (100, 255, 50), "spike_color": (180, 0, 220),
    },
    "boss_final": {  # Boss 4 (Level 20) — Trùm Cuối — dark crimson/black skull
        "body_base": (140, 20, 20), "body_shadow": (80, 5, 5), "body_highlight": (220, 60, 40),
        "body_specular": (255, 120, 80), "material": Material.NEON,
        "turret_base": (120, 10, 10), "turret_highlight": (200, 50, 30),
        "barrel_base": (180, 30, 20), "barrel_highlight": (240, 80, 50),
        "track_base": (40, 5, 5), "track_highlight": (70, 15, 10), "track_rivet": (100, 30, 20),
        "accent": (255, 0, 0), "eye_bg": (255, 200, 180), "pupil": (255, 0, 0),
        "blush": (200, 20, 20), "camo_color": (100, 10, 10),
        "stripe": (255, 30, 0), "emblem": (255, 100, 50),
        "glow_color": (255, 50, 0), "spike_color": (255, 0, 50),
    },
}

PLAYER_TIER_COLORS = [
    {  # Tier 0 - cream mint
        "body_base": (255, 240, 180), "body_shadow": (200, 180, 120), "body_highlight": (255, 255, 230),
        "body_specular": (255, 255, 250), "material": Material.MATTE,
        "turret_base": (250, 220, 150), "turret_highlight": (255, 245, 200),
        "barrel_base": (240, 200, 130), "barrel_highlight": (255, 240, 190),
        "track_base": (160, 130, 90), "track_highlight": (200, 170, 130), "track_rivet": (240, 215, 175),
        "accent": (255, 230, 160), "eye_bg": (255, 255, 255), "pupil": (50, 30, 70),
        "blush": (255, 170, 200), "camo_color": (240, 220, 160),
        "stripe": (255, 200, 210), "emblem": (255, 230, 245),
    },
    {  # Tier 1 - pastel pink
        "body_base": (255, 180, 215), "body_shadow": (210, 130, 170), "body_highlight": (255, 220, 240),
        "body_specular": (255, 240, 250), "material": Material.MATTE,
        "turret_base": (240, 150, 195), "turret_highlight": (255, 200, 230),
        "barrel_base": (235, 140, 195), "barrel_highlight": (255, 210, 240),
        "track_base": (170, 90, 130), "track_highlight": (210, 130, 170), "track_rivet": (245, 180, 220),
        "accent": (255, 225, 240), "eye_bg": (255, 255, 255), "pupil": (60, 30, 80),
        "blush": (255, 130, 175), "camo_color": (245, 165, 210),
        "stripe": (255, 240, 230), "emblem": (255, 230, 245),
    },
    {  # Tier 2 - pastel sky blue
        "body_base": (160, 210, 255), "body_shadow": (110, 160, 220), "body_highlight": (210, 240, 255),
        "body_specular": (240, 250, 255), "material": Material.METALLIC,
        "turret_base": (130, 190, 250), "turret_highlight": (200, 230, 255),
        "barrel_base": (120, 180, 245), "barrel_highlight": (190, 225, 255),
        "track_base": (60, 110, 170), "track_highlight": (100, 150, 200), "track_rivet": (170, 210, 240),
        "accent": (210, 240, 255), "eye_bg": (255, 255, 255), "pupil": (40, 60, 90),
        "blush": (255, 165, 200), "camo_color": (140, 195, 245),
        "stripe": (255, 230, 245), "emblem": (240, 250, 255),
    },
    {  # Tier 3 - pastel lavender
        "body_base": (210, 180, 255), "body_shadow": (150, 120, 200), "body_highlight": (235, 215, 255),
        "body_specular": (250, 240, 255), "material": Material.METALLIC,
        "turret_base": (190, 155, 240), "turret_highlight": (230, 200, 255),
        "barrel_base": (180, 150, 235), "barrel_highlight": (220, 195, 255),
        "track_base": (110, 80, 160), "track_highlight": (155, 120, 200), "track_rivet": (210, 180, 240),
        "accent": (235, 220, 255), "eye_bg": (255, 255, 255), "pupil": (50, 30, 80),
        "blush": (255, 150, 200), "camo_color": (200, 175, 240),
        "stripe": (255, 230, 245), "emblem": (250, 240, 255),
    },
    {  # Tier 4 - rainbow chrome
        "body_base": (255, 200, 230), "body_shadow": (200, 130, 180), "body_highlight": (255, 240, 255),
        "body_specular": (255, 255, 255), "material": Material.CHROME,
        "turret_base": (230, 180, 240), "turret_highlight": (255, 220, 250),
        "barrel_base": (210, 220, 255), "barrel_highlight": (240, 245, 255),
        "track_base": (120, 80, 130), "track_highlight": (180, 140, 200), "track_rivet": (240, 210, 250),
        "accent": (255, 230, 240), "eye_bg": (255, 255, 255), "pupil": (255, 100, 180),
        "blush": (255, 140, 190), "camo_color": (220, 180, 240),
        "stripe": (255, 240, 80), "emblem": (255, 255, 255),
    },
]

# ═══════════════════════════════════════════════
#  HELPER DRAWING FUNCTIONS (operate at hi-res)
# ═══════════════════════════════════════════════

def draw_bevel_rect(surf, color, rect, bevel_depth=2, border_radius=0):
    pygame.draw.rect(surf, color, rect, border_radius=border_radius)
    x, y, w, h = rect
    hl = [min(255, c + 50) for c in color]
    sh = [max(0, c - 50) for c in color]
    for i in range(bevel_depth):
        a = int(220 * (1 - i / max(1, bevel_depth)))
        pygame.draw.line(surf, (*hl[:3],), (x+i, y+i), (x+w-i-1, y+i), 1)
        pygame.draw.line(surf, (*hl[:3],), (x+i, y+i), (x+i, y+h-i-1), 1)
        pygame.draw.line(surf, (*sh[:3],), (x+w-i-1, y+i+1), (x+w-i-1, y+h-i-1), 1)
        pygame.draw.line(surf, (*sh[:3],), (x+i+1, y+h-i-1), (x+w-i-1, y+h-i-1), 1)

def draw_gloss_overlay(surf, rect, intensity=120):
    x, y, w, h = rect
    gloss = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h // 2):
        a = int(intensity * (1 - i / (h / 2)) * 0.5)
        pygame.draw.line(gloss, (255, 255, 255, max(0, a)), (0, i), (w, i))
    surf.blit(gloss, (x, y))

def draw_noise_texture(surf, rect, base_color, variance=15, density=0.4):
    x, y, w, h = rect
    for _ in range(int(w * h * density)):
        px = x + random.randint(0, w - 1)
        py = y + random.randint(0, h - 1)
        offset = random.randint(-variance, variance)
        nc = tuple(max(0, min(255, c + offset)) for c in base_color)
        surf.set_at((px, py), nc)

def draw_metallic_streak(surf, rect):
    x, y, w, h = rect
    for i in range(0, w + h, 3):
        dist = abs(i - (w + h) // 3)
        if dist < 12:
            a = int(100 * (1 - dist / 12))
            pygame.draw.line(surf, (255, 255, 255, max(0, a)),
                           (x + min(i, w-1), y), (x + max(0, i - h), y + min(i, h-1)), 1)

# ═══════════════════════════════════════════════
#  MAP TILES - ULTRA PREMIUM (supersampled 10x)
# ═══════════════════════════════════════════════

def make_brick_tile_ultra():
    R = _RTS
    s = pygame.Surface((R, R))
    s.fill((140, 65, 38))
    bh = _S(8)
    bw = _S(16)
    for y in range(0, R, bh):
        offset = bh if (y // bh) % 2 == 1 else 0
        pygame.draw.line(s, (70, 30, 18), (0, y), (R, y), _S(1))
        for x in range(0, R, bw):
            bx = (x + offset) % R
            pygame.draw.line(s, (70, 30, 18), (bx, y), (bx, y + bh), _S(1))
            # Elegant premium color-shifting bricks with quartz gold specks
            brick_c = (random.randint(155, 195), random.randint(70, 95), random.randint(38, 55))
            draw_bevel_rect(s, brick_c, (bx + _S(1), y + _S(1), _S(14), _S(6)), _S(1))
            # Specular highlight on brick edges
            pygame.draw.rect(s, (255, 255, 255, 30), (bx + _S(1), y + _S(1), _S(14), _S(6)), 1)
            for _ in range(_S(2)):
                px = bx + random.randint(_S(2), _S(12))
                py_v = y + random.randint(_S(2), _S(5))
                if 0 <= px < R and 0 <= py_v < R:
                    # Gold quartz sparks!
                    s.set_at((px, py_v), (255, 215, 0) if random.random() < 0.2 else (random.randint(120, 150), random.randint(55, 75), random.randint(30, 45)))
    return _downscale(s, TS, TS)

def make_steel_tile_ultra():
    R = _RTS
    s = pygame.Surface((R, R))
    s.fill((110, 115, 130))
    # Elegant dark brushed metal border
    draw_bevel_rect(s, (140, 145, 160), (_S(2), _S(2), R - _S(4), R - _S(4)), _S(4))
    for i in range(_S(2), R - _S(2), _S(4)):
        pygame.draw.line(s, (160, 165, 180), (i, _S(2)), (i, R - _S(3)), _S(1))
    
    # ── CYBER NEON GRIDLINES (Vẽ đường mạch năng lượng siêu ngầu) ──
    pygame.draw.line(s, (0, 240, 255), (_S(4), _S(4)), (R - _S(4), _S(4)), _S(1.5))
    pygame.draw.line(s, (0, 240, 255), (_S(4), _S(4)), (_S(4), R - _S(4)), _S(1.5))
    pygame.draw.line(s, (0, 240, 255), (R - _S(4), _S(4)), (R - _S(4), R - _S(4)), _S(1.5))
    pygame.draw.line(s, (0, 240, 255), (_S(4), R - _S(4)), (R - _S(4), R - _S(4)), _S(1.5))

    # Corner power rivets
    for dx, dy in [(_S(6), _S(6)), (R - _S(7), _S(6)), (_S(6), R - _S(7)), (R - _S(7), R - _S(7))]:
        pygame.draw.circle(s, (0, 255, 180), (dx, dy), _S(3))
        pygame.draw.circle(s, (255, 255, 255), (dx, dy), _S(1.5))
        pygame.draw.circle(s, (0, 100, 80), (dx, dy), _S(3), _S(1))
    center = R // 2
    # Cyber core insignia
    pygame.draw.line(s, (0, 240, 255), (center - _S(4), center), (center + _S(4), center), _S(2))
    pygame.draw.line(s, (0, 240, 255), (center, center - _S(4)), (center, center + _S(4)), _S(2))
    pygame.draw.circle(s, (255, 255, 255), (center, center), _S(1.5))
    draw_gloss_overlay(s, (_S(2), _S(2), R - _S(4), R - _S(4)), 80)
    return _downscale(s, TS, TS)

def make_grass_tile_ultra():
    R = _RTS
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    # Layered dynamic grass blades
    for _ in range(50 * _R):
        gx = random.randint(0, R - 1)
        gy = random.randint(0, R - 1)
        height = random.randint(_S(6), _S(14))
        sway = random.randint(-_S(3), _S(3))
        # Color transition from lush forest green to neon emerald
        gc = (random.randint(25, 60), random.randint(160, 235), random.randint(40, 85))
        width = random.randint(_S(1), _S(2))
        pygame.draw.line(s, gc, (gx, gy), (gx + sway, gy - height), width)
        # Specular glint on tips
        if random.random() < 0.15:
            pygame.draw.circle(s, (255, 255, 255, 180), (gx + sway, gy - height), _S(1))
            
    # Beautiful wild blossoms (Làm hoa hồng, tím cực xinh động)
    for _ in range(6 * _R):
        fx = random.randint(_S(4), R - _S(5))
        fy = random.randint(_S(4), R - _S(5))
        # Rich pastel flower colors
        fc = random.choice([(255, 90, 160), (255, 190, 80), (160, 100, 255), (80, 230, 255)])
        pygame.draw.circle(s, fc, (fx, fy), _S(2.5))
        pygame.draw.circle(s, (255, 255, 200), (fx, fy), _S(1))
    return _downscale(s, TS, TS)

def make_crate_tile_ultra():
    R = _RTS
    s = pygame.Surface((R, R))
    s.fill((135, 95, 55))
    # Elegant detailed premium wood crate
    draw_bevel_rect(s, (160, 120, 70), (_S(2), _S(2), R - _S(4), R - _S(4)), _S(3))
    pygame.draw.rect(s, (80, 55, 30), (_S(2), _S(2), R - _S(4), R - _S(4)), _S(2))
    # Double reinforced cross bands
    pygame.draw.line(s, (80, 55, 30), (_S(2), _S(2)), (R - _S(3), R - _S(3)), _S(3))
    pygame.draw.line(s, (80, 55, 30), (R - _S(3), _S(2)), (_S(2), R - _S(3)), _S(3))
    # Shiny bronze corner brackets
    for bx, by in [(_S(3), _S(3)), (R - _S(6), _S(3)), (_S(3), R - _S(6)), (R - _S(6), R - _S(6))]:
        pygame.draw.circle(s, (255, 215, 0), (bx, by), _S(2))
        pygame.draw.circle(s, (80, 55, 30), (bx, by), _S(2), _S(1))
    pygame.draw.circle(s, (90, 65, 35), (R // 2, R // 2), _S(5))
    pygame.draw.circle(s, (255, 215, 0), (R // 2, R // 2), _S(5), _S(1))
    draw_noise_texture(s, (_S(3), _S(3), R - _S(6), R - _S(6)), (150, 110, 65), 12, 0.20)
    return _downscale(s, TS, TS)

def make_water_tile_ultra(frame=0):
    R = _RTS
    s = pygame.Surface((R, R))
    base_b = 180 + int(math.sin(frame * 0.3) * 15)
    s.fill((25, 65, base_b))
    off = int(math.sin(frame * 0.25) * _S(5))
    off2 = int(math.cos(frame * 0.18) * _S(3))
    # Detailed dynamic wave caustics
    for y in range(0, R, _S(3)):
        wave_off = int(math.sin((y / _R + frame * 2.2) * 0.18) * _S(4))
        c1 = (45 + wave_off * 2 // _R, 105 + wave_off * 3 // _R, min(255, 245 + wave_off * 2 // _R))
        pygame.draw.line(s, c1, (off + wave_off, y), (off + R + wave_off, y), _S(1.2))
        c2 = (80, 160, 255, 120)
        pygame.draw.line(s, c2, (off2, y + _S(1)), (off2 + R, y + _S(1)), _S(1))
    # Translucent rising bubbles
    for _ in range(4 * _R):
        sx = random.randint(_S(4), R - _S(8)) + int(math.sin(frame * 0.1) * _S(2))
        sy = random.randint(_S(4), R - _S(8))
        pygame.draw.ellipse(s, (255, 255, 255, 90), (sx, sy, _S(5), _S(3)))
        pygame.draw.circle(s, (255, 255, 255, 150), (sx + _S(1), sy + _S(1)), _S(1))
    return _downscale(s, TS, TS)

def make_floor_tile_ultra(theme="default"):
    R = _RTS
    s = pygame.Surface((R, R))
    if theme == "desert":
        s.fill((180, 160, 120))
        for _ in range(8 * _R):
            px, py = random.randint(0, R-1), random.randint(0, R-1)
            c = (random.randint(170, 195), random.randint(150, 175), random.randint(110, 135))
            pygame.draw.circle(s, c, (px, py), random.randint(_S(1), _S(2)))
    elif theme == "snow":
        s.fill((220, 225, 235))
        for _ in range(6 * _R):
            px, py = random.randint(0, R-1), random.randint(0, R-1)
            c = (random.randint(210, 240), random.randint(215, 245), random.randint(225, 250))
            pygame.draw.circle(s, c, (px, py), random.randint(_S(1), _S(3)))
    elif theme == "city":
        s.fill((60, 62, 70))
        for y in range(0, R, _S(16)):
            for x in range(0, R, _S(16)):
                pygame.draw.rect(s, (55, 57, 64), (x, y, _S(15), _S(15)))
                pygame.draw.line(s, (70, 72, 80), (x, y), (x + _S(15), y), _S(1))
                pygame.draw.line(s, (70, 72, 80), (x, y), (x, y + _S(15)), _S(1))
    elif theme == "jungle":
        s.fill((35, 55, 30))
        for _ in range(12 * _R):
            px, py = random.randint(0, R-1), random.randint(0, R-1)
            c = (random.randint(25, 50), random.randint(45, 70), random.randint(20, 40))
            pygame.draw.circle(s, c, (px, py), random.randint(_S(1), _S(2)))
    elif theme == "lava":
        s.fill((40, 15, 10))
        for _ in range(5 * _R):
            px, py = random.randint(0, R-1), random.randint(0, R-1)
            c = (random.randint(60, 90), random.randint(15, 30), random.randint(5, 15))
            pygame.draw.circle(s, c, (px, py), random.randint(_S(1), _S(3)))
    elif theme == "kawaii_woodland":
        s.fill((205, 175, 140))
        for y in range(0, R, _S(4)):
            for x in range(0, R, _S(4)):
                if (x // _R + y // _R) % 8 == 0:
                    c = (random.randint(195, 220), random.randint(165, 190),
                         random.randint(125, 160))
                    pygame.draw.circle(s, c, (x + _S(2), y + _S(2)), _S(1))
        for _ in range(3 * _R):
            fx = random.randint(_S(3), R - _S(4))
            fy = random.randint(_S(3), R - _S(4))
            fc = random.choice([(255, 200, 220), (255, 230, 200),
                                (220, 200, 255), (200, 230, 255)])
            pygame.draw.circle(s, fc, (fx, fy), _S(2))
            pygame.draw.circle(s, (255, 240, 150), (fx, fy), _S(1))
    else:
        s.fill((28, 30, 38))
        for _ in range(10 * _R):
            px, py = random.randint(0, R-1), random.randint(0, R-1)
            pygame.draw.circle(s, (38, 40, 48), (px, py), _S(1))
    return _downscale(s, TS, TS)


def make_brick_tile_kawaii():
    R = _RTS
    s = pygame.Surface((R, R))
    s.fill((255, 195, 215))
    bh = _S(8)
    bw = _S(16)
    for y in range(0, R, bh):
        offset = bh if (y // bh) % 2 == 1 else 0
        for x in range(0, R, bw):
            bx = (x + offset) % R
            brick_c = (random.randint(245, 255), random.randint(170, 200),
                       random.randint(195, 225))
            draw_bevel_rect(s, brick_c, (bx + _S(1), y + _S(1), _S(14), _S(6)), _S(1), border_radius=_S(3))
            pygame.draw.circle(s, (255, 240, 245), (bx + _S(4), y + _S(3)), _S(1))
    pygame.draw.rect(s, (220, 130, 170), (0, 0, R, R), _S(1), border_radius=_S(4))
    return _downscale(s, TS, TS)


def make_steel_tile_kawaii():
    R = _RTS
    s = pygame.Surface((R, R))
    s.fill((180, 195, 235))
    draw_bevel_rect(s, (210, 220, 250), (_S(2), _S(2), R - _S(4), R - _S(4)), _S(4), border_radius=_S(8))
    for i in range(_S(4), R - _S(4), _S(6)):
        pygame.draw.line(s, (235, 240, 255), (i, _S(4)), (i, R - _S(4)), _S(1))
    for dx, dy in [(_S(6), _S(6)), (R - _S(7), _S(6)), (_S(6), R - _S(7)), (R - _S(7), R - _S(7))]:
        pygame.draw.circle(s, (245, 230, 240), (dx, dy), _S(3))
        pygame.draw.circle(s, (200, 180, 220), (dx, dy), _S(3), _S(1))
        pygame.draw.circle(s, (255, 255, 255), (dx - _S(1), dy - _S(1)), _S(1))
    pygame.draw.rect(s, (155, 175, 220), (0, 0, R, R), _S(2), border_radius=_S(8))
    draw_gloss_overlay(s, (_S(2), _S(2), R - _S(4), R - _S(4)), 100)
    return _downscale(s, TS, TS)


def make_grass_tile_kawaii():
    R = _RTS
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    for _ in range(30 * _R):
        gx = random.randint(0, R - 1)
        gy = random.randint(0, R - 1)
        height = random.randint(_S(4), _S(9))
        sway = random.randint(-_S(2), _S(2))
        gc = (random.randint(140, 200), random.randint(220, 255),
              random.randint(160, 210))
        pygame.draw.line(s, gc, (gx, gy), (gx + sway, gy - height), _S(2))
    for _ in range(4 * _R):
        fx = random.randint(_S(5), R - _S(6))
        fy = random.randint(_S(5), R - _S(6))
        petal_c = random.choice([(255, 180, 215), (200, 200, 255),
                                 (255, 220, 180), (180, 240, 230)])
        for ang in range(0, 360, 72):
            rad = math.radians(ang)
            px = fx + int(math.cos(rad) * _S(3))
            py = fy + int(math.sin(rad) * _S(3))
            pygame.draw.circle(s, petal_c, (px, py), _S(2))
        pygame.draw.circle(s, (255, 240, 130), (fx, fy), _S(2))
    if random.random() < 0.45:
        mx = random.randint(_S(5), R - _S(8))
        my = random.randint(_S(8), R - _S(6))
        pygame.draw.rect(s, (255, 250, 230), (mx + _S(2), my, _S(3), _S(5)))
        pygame.draw.ellipse(s, (255, 130, 150), (mx, my - _S(4), _S(7), _S(6)))
        pygame.draw.circle(s, (255, 240, 240), (mx + _S(2), my - _S(3)), _S(1))
        pygame.draw.circle(s, (255, 240, 240), (mx + _S(5), my - _S(2)), _S(1))
    return _downscale(s, TS, TS)

def make_base_tile_ultra():
    R = _RTS
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.circle(s, (240, 200, 60), (R // 2, R // 2), R // 2 - _S(1))
    pygame.draw.circle(s, (200, 160, 40), (R // 2, R // 2), R // 2 - _S(4))
    pygame.draw.circle(s, (255, 220, 80), (R // 2, R // 2), R // 2 - _S(4), _S(2))
    pygame.draw.circle(s, (160, 120, 30), (R // 2, R // 2), R // 2 - _S(1), _S(2))
    star_pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = _S(8) if i % 2 == 0 else _S(4)
        star_pts.append((R // 2 + math.cos(angle) * r, R // 2 + math.sin(angle) * r))
    pygame.draw.polygon(s, (255, 240, 150), star_pts)
    draw_gloss_overlay(s, (_S(4), _S(4), R - _S(8), R // 2 - _S(4)), 80)
    return _downscale(s, TS, TS)

# ═══════════════════════════════════════════════
#  TANK SPRITES - ULTRA DETAILED (supersampled)
# ═══════════════════════════════════════════════

def _draw_gradient_rect(surf, rect, top_color, bot_color, border_radius=0):
    """Fill a rect with a vertical gradient from top_color to bot_color."""
    x, y, w, h = rect
    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        r = int(top_color[0] * (1 - t) + bot_color[0] * t)
        g = int(top_color[1] * (1 - t) + bot_color[1] * t)
        b = int(top_color[2] * (1 - t) + bot_color[2] * t)
        pygame.draw.line(tmp, (r, g, b), (0, i), (w, i))
    if border_radius > 0:
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=border_radius)
        tmp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(tmp, (x, y))


def _draw_ambient_shadow(surf, rect, radius=None):
    """Draw a soft ambient shadow under a rectangular area."""
    x, y, w, h = rect
    r = radius or _S(2)
    sh = pygame.Surface((w + r * 2, h + r * 2), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 25), (0, r, w + r * 2, h), border_radius=r)
    pygame.draw.rect(sh, (0, 0, 0, 15), (r // 2, r // 2, w + r, h + r), border_radius=r)
    surf.blit(sh, (x - r, y - r // 2))


def make_tank_surface_from_colors(c, direction):
    R = _RTS
    s = pygame.Surface((R, R), pygame.SRCALPHA)

    # ── SHADOW under whole tank ──
    shadow = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 30), (_S(3), _S(8), _S(26), _S(20)))
    s.blit(shadow, (0, 0))

    # ── TRACKS with gradient, treads, road wheels, sprockets ──
    track_l = (_S(2), _S(4), _S(7), _S(24))
    track_r = (_S(23), _S(4), _S(7), _S(24))
    for tr in [track_l, track_r]:
        tx, ty, tw, th = tr
        # Track body gradient (darker at bottom)
        track_top = c["track_base"]
        track_bot = tuple(max(0, v - 30) for v in c["track_base"])
        _draw_gradient_rect(s, tr, track_top, track_bot, border_radius=_S(2))
        # Track border
        pygame.draw.rect(s, tuple(max(0, v - 40) for v in c["track_base"]),
                         tr, max(1, _S(0.6)), border_radius=_S(2))
        # Tread links
        for i in range(ty + _S(2), ty + th - _S(1), _S(2)):
            a = 80 + int(40 * ((i - ty) / th))
            pygame.draw.line(s, c["track_highlight"], (tx + _S(1), i), (tx + tw - _S(2), i), max(1, _S(0.6)))
        # Road wheels (circles with detail)
        for wi in range(ty + _S(4), ty + th - _S(2), _S(5)):
            wcx = tx + tw // 2
            # Wheel body
            pygame.draw.circle(s, c["track_rivet"], (wcx, wi), _S(2))
            pygame.draw.circle(s, c["track_highlight"], (wcx, wi), _S(1.5))
            # Wheel hub
            pygame.draw.circle(s, c["track_rivet"], (wcx, wi), max(1, _S(0.6)))
        # Sprocket at top and bottom
        pygame.draw.circle(s, c["track_rivet"], (tx + tw // 2, ty + _S(2)), _S(1.5))
        pygame.draw.circle(s, c["track_highlight"], (tx + tw // 2, ty + _S(2)), max(1, _S(0.8)))
        pygame.draw.circle(s, c["track_rivet"], (tx + tw // 2, ty + th - _S(2)), _S(1.5))
        pygame.draw.circle(s, c["track_highlight"], (tx + tw // 2, ty + th - _S(2)), max(1, _S(0.8)))

    # ── BODY with gradient fill, detailed armor, engine vents, and cyber wiring ──
    body_rect = (_S(5), _S(5), _S(22), _S(22))
    bx, by, bw, bh = body_rect
    # Ambient shadow under body
    _draw_ambient_shadow(s, body_rect)
    # Body gradient fill
    body_top = c["body_highlight"]
    body_bot = c["body_shadow"]
    _draw_gradient_rect(s, body_rect, body_top, body_bot, border_radius=_S(3))
    # Body border
    pygame.draw.rect(s, c["body_shadow"], body_rect, max(1, _S(0.7)), border_radius=_S(3))

    # 1. High-Tech Engine Exhaust Grills (at the back of the tank chassis)
    vent_y = by + bh - _S(5)
    for vi in range(3):
        vy = vent_y + vi * _S(1.5)
        # Deep dark grill groove
        pygame.draw.rect(s, (30, 30, 40), (bx + _S(4), vy, bw - _S(8), max(1, _S(0.7))))
        # Glowing exhaust embers inside groove
        pygame.draw.rect(s, (255, 80, 0), (bx + _S(6), vy, bw - _S(12), max(1, _S(0.4))))

    # 2. Cybernetic Power Piping (Neon glow cabling on the armor plates)
    pygame.draw.line(s, (0, 240, 255), (bx + _S(3), by + _S(8)), (bx + _S(8), by + _S(12)), max(1, _S(0.6)))
    pygame.draw.line(s, (255, 0, 128), (bx + bw - _S(3), by + _S(8)), (bx + bw - _S(8), by + _S(12)), max(1, _S(0.6)))

    # 3. Holographic Visor scanner (At the front of the tank hull)
    pygame.draw.rect(s, (0, 180, 255), (bx + _S(4), by + _S(2), bw - _S(8), _S(1.5)), border_radius=_S(0.5))
    pygame.draw.rect(s, (255, 255, 255), (bx + bw // 2 - _S(2), by + _S(2), _S(4), _S(1.0)), border_radius=_S(0.5))

    # Armor panel lines with depth
    panel_c = tuple(max(0, v - 25) for v in c["body_base"])
    panel_hl = tuple(min(255, v + 15) for v in c["body_base"])
    # Vertical panels
    for px in [bx + _S(5), bx + bw - _S(5)]:
        pygame.draw.line(s, panel_c, (px, by + _S(2)), (px, by + bh - _S(2)), max(1, _S(0.5)))
        pygame.draw.line(s, panel_hl, (px + 1, by + _S(2)), (px + 1, by + bh - _S(2)), max(1, _S(0.3)))
    # Horizontal panel
    pygame.draw.line(s, panel_c, (bx + _S(2), by + bh // 2), (bx + bw - _S(2), by + bh // 2), max(1, _S(0.5)))
    pygame.draw.line(s, panel_hl, (bx + _S(2), by + bh // 2 + 1), (bx + bw - _S(2), by + bh // 2 + 1), max(1, _S(0.3)))

    # Rivets on body corners
    rivet_c = tuple(min(255, v + 30) for v in c["body_shadow"])
    for rx, ry in [(bx + _S(3), by + _S(3)), (bx + bw - _S(3), by + _S(3)),
                   (bx + _S(3), by + bh - _S(3)), (bx + bw - _S(3), by + bh - _S(3))]:
        pygame.draw.circle(s, rivet_c, (rx, ry), max(1, _S(0.8)))
        pygame.draw.circle(s, c["body_specular"], (rx - 1, ry - 1), max(1, _S(0.3)))

    # Material effects
    mat = c["material"]
    if mat == Material.METALLIC:
        draw_gloss_overlay(s, body_rect, 60)
    elif mat == Material.CHROME:
        draw_gloss_overlay(s, body_rect, 100)
        draw_metallic_streak(s, body_rect)
    elif mat == Material.RUSTY:
        draw_noise_texture(s, body_rect, c["body_base"], 25, 0.25)
    elif mat == Material.NEON:
        glow_s = pygame.Surface((bw + _S(4), bh + _S(4)), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*c["accent"][:3], 30), (0, 0, bw + _S(4), bh + _S(4)), border_radius=_S(5))
        s.blit(glow_s, (bx - _S(2), by - _S(2)))
        # Inner neon edge
        pygame.draw.rect(s, (*c["accent"][:3], 80), body_rect, max(1, _S(0.8)), border_radius=_S(3))

    # Stripe decoration
    stripe_c = c.get("stripe", c["accent"])
    pygame.draw.line(s, stripe_c, (bx + _S(3), by + _S(4)), (bx + bw - _S(3), by + _S(4)), max(1, _S(1)))
    # Secondary thin stripe
    stripe_dim = tuple(max(0, v - 40) for v in stripe_c)
    pygame.draw.line(s, stripe_dim, (bx + _S(3), by + _S(6)), (bx + bw - _S(3), by + _S(6)), max(1, _S(0.5)))

    # ── TURRET with gradient, ring, hatch, periscope ──
    tur_cx, tur_cy = R // 2, R // 2 + _S(1)
    tur_r = _S(8)
    # Turret shadow
    pygame.draw.circle(s, (0, 0, 0, 20), (tur_cx + _S(1), tur_cy + _S(1)), tur_r + _S(1))
    # Turret base ring
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), tur_r + _S(1))
    # Turret body with gradient effect
    for ri in range(int(tur_r), 0, -1):
        t = 1 - ri / tur_r
        r = int(c["turret_base"][0] * (1 - t * 0.4) + c["turret_highlight"][0] * t * 0.8)
        g = int(c["turret_base"][1] * (1 - t * 0.4) + c["turret_highlight"][1] * t * 0.8)
        b = int(c["turret_base"][2] * (1 - t * 0.4) + c["turret_highlight"][2] * t * 0.8)
        pygame.draw.circle(s, (min(255, r), min(255, g), min(255, b)), (tur_cx, tur_cy), ri)
    # Turret rim
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), tur_r, max(1, _S(0.8)))
    # Hatch circle
    pygame.draw.circle(s, c["turret_highlight"], (tur_cx, tur_cy), _S(3))
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), _S(3), max(1, _S(0.5)))
    # Specular highlight (light source top-left)
    pygame.draw.circle(s, c["body_specular"], (tur_cx - _S(2), tur_cy - _S(2)), _S(2))
    # Periscope nub
    pygame.draw.rect(s, c["body_shadow"], (tur_cx + tur_r - _S(2), tur_cy - _S(1), _S(3), _S(2)),
                     border_radius=max(1, _S(0.5)))

    # ── BARREL with gradient, bands, muzzle brake ──
    barrel_w, barrel_h = _S(5), _S(15)
    barrel = pygame.Surface((barrel_w, barrel_h), pygame.SRCALPHA)
    # Barrel gradient
    b_top = c["barrel_highlight"]
    b_bot = c["barrel_base"]
    _draw_gradient_rect(barrel, (0, 0, barrel_w, barrel_h), b_top, b_bot, border_radius=max(1, _S(0.8)))
    # Barrel border
    pygame.draw.rect(barrel, tuple(max(0, v - 30) for v in c["barrel_base"]),
                     (0, 0, barrel_w, barrel_h), max(1, _S(0.5)), border_radius=max(1, _S(0.8)))
    # Reinforcement bands
    for band_y in [_S(3), barrel_h // 2, barrel_h - _S(3)]:
        pygame.draw.rect(barrel, c["barrel_highlight"], (0, band_y, barrel_w, max(1, _S(0.8))))
    # Muzzle end
    muzzle_c = tuple(min(255, v + 35) for v in c["barrel_base"])
    pygame.draw.rect(barrel, muzzle_c, (-1, 0, barrel_w + 2, _S(2)), border_radius=max(1, _S(0.5)))
    # Bore (dark center line)
    pygame.draw.line(barrel, (0, 0, 0, 60), (barrel_w // 2, 0), (barrel_w // 2, _S(1)), max(1, _S(0.5)))

    # ── Compose final with rotation ──
    final = pygame.Surface((R, R), pygame.SRCALPHA)
    if direction == 0:
        final.blit(s, (0, 0))
        final.blit(barrel, (R // 2 - barrel_w // 2, -_S(1)))
    elif direction == 1:
        rs = pygame.transform.rotate(s, -90)
        rb = pygame.transform.rotate(barrel, -90)
        final.blit(rs, (0, 0))
        final.blit(rb, (R - barrel_h + _S(1), R // 2 - barrel_w // 2))
    elif direction == 2:
        rs = pygame.transform.rotate(s, 180)
        rb = pygame.transform.rotate(barrel, 180)
        final.blit(rs, (0, 0))
        final.blit(rb, (R // 2 - barrel_w // 2, R - barrel_h + _S(1)))
    elif direction == 3:
        rs = pygame.transform.rotate(s, 90)
        rb = pygame.transform.rotate(barrel, 90)
        final.blit(rs, (0, 0))
        final.blit(rb, (-_S(1), R // 2 - barrel_w // 2))

    return _downscale(final, TS, TS)

def make_tank_surface_ultra(tank_key, direction):
    return make_tank_surface_from_colors(TANK_COLORS[tank_key], direction)


# ═══════════════════════════════════════════════
#  BOSS SPRITE RENDERING — 1280x1280 supersampled
# ═══════════════════════════════════════════════
_BOSS_RENDER = 384  # was 1280 - cut for fast startup; still looks crisp
_BOSS_DISPLAY = 64  # boss displayed at 2x tile size

def _BS(v):
    """Scale value for boss hi-res rendering (1280px canvas, display 64px)."""
    return int(v * _BOSS_RENDER / _BOSS_DISPLAY)

def make_boss_surface(boss_key, direction):
    """Render a unique boss tank at 1280x1280, smoothscale to 64x64.
    Each boss_key gets distinct decorations: spikes, horns, aura, skull, crystals."""
    c = BOSS_COLORS[boss_key]
    R = _BOSS_RENDER
    s = pygame.Surface((R, R), pygame.SRCALPHA)

    # ── OUTER AURA / GLOW ──
    glow_c = c.get("glow_color", c["accent"])
    for gi in range(4, 0, -1):
        aura = pygame.Surface((R, R), pygame.SRCALPHA)
        ar = R // 2 - _BS(2) + gi * _BS(1)
        alpha = 15 + gi * 8
        pygame.draw.circle(aura, (*glow_c, alpha), (R // 2, R // 2), ar)
        s.blit(aura, (0, 0))

    # ── GROUND SHADOW ──
    shadow = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 50), (_BS(4), _BS(10), _BS(56), _BS(44)))
    s.blit(shadow, (0, 0))

    # ── TRACKS — wider, heavier ──
    track_l = (_BS(2), _BS(4), _BS(10), _BS(56))
    track_r = (_BS(52), _BS(4), _BS(10), _BS(56))
    for tr in [track_l, track_r]:
        tx, ty, tw, th = tr
        track_top = c["track_base"]
        track_bot = tuple(max(0, v - 30) for v in c["track_base"])
        _draw_gradient_rect(s, tr, track_top, track_bot, border_radius=_BS(3))
        pygame.draw.rect(s, tuple(max(0, v - 40) for v in c["track_base"]),
                         tr, max(1, _BS(1)), border_radius=_BS(3))
        for i in range(ty + _BS(3), ty + th - _BS(2), _BS(3)):
            pygame.draw.line(s, c["track_highlight"], (tx + _BS(1), i), (tx + tw - _BS(2), i), max(1, _BS(1)))
        for wi in range(ty + _BS(5), ty + th - _BS(3), _BS(7)):
            wcx = tx + tw // 2
            pygame.draw.circle(s, c["track_rivet"], (wcx, wi), _BS(3))
            pygame.draw.circle(s, c["track_highlight"], (wcx, wi), _BS(2))
            pygame.draw.circle(s, c["track_rivet"], (wcx, wi), max(1, _BS(1)))

    # ── BODY — larger, armored ──
    body_rect = (_BS(8), _BS(6), _BS(48), _BS(52))
    bx, by, bw, bh = body_rect
    _draw_ambient_shadow(s, body_rect)
    _draw_gradient_rect(s, body_rect, c["body_highlight"], c["body_shadow"], border_radius=_BS(4))
    pygame.draw.rect(s, c["body_shadow"], body_rect, max(1, _BS(1)), border_radius=_BS(4))

    # Armor panels
    panel_c = tuple(max(0, v - 25) for v in c["body_base"])
    panel_hl = tuple(min(255, v + 15) for v in c["body_base"])
    for px in [bx + _BS(8), bx + bw - _BS(8)]:
        pygame.draw.line(s, panel_c, (px, by + _BS(3)), (px, by + bh - _BS(3)), max(1, _BS(1)))
        pygame.draw.line(s, panel_hl, (px + 1, by + _BS(3)), (px + 1, by + bh - _BS(3)), max(1, _BS(0.5)))
    for py_line in [by + bh // 3, by + bh * 2 // 3]:
        pygame.draw.line(s, panel_c, (bx + _BS(3), py_line), (bx + bw - _BS(3), py_line), max(1, _BS(1)))

    # Engine exhaust grills
    for vi in range(4):
        vy = by + bh - _BS(8) + vi * _BS(2)
        pygame.draw.rect(s, (30, 30, 40), (bx + _BS(6), vy, bw - _BS(12), max(1, _BS(1))))
        pygame.draw.rect(s, glow_c, (bx + _BS(8), vy, bw - _BS(16), max(1, _BS(0.6))))

    # Neon power piping
    pygame.draw.line(s, glow_c, (bx + _BS(4), by + _BS(10)), (bx + _BS(10), by + _BS(18)), max(1, _BS(1.2)))
    pygame.draw.line(s, glow_c, (bx + bw - _BS(4), by + _BS(10)), (bx + bw - _BS(10), by + _BS(18)), max(1, _BS(1.2)))

    # Holographic visor
    pygame.draw.rect(s, glow_c, (bx + _BS(6), by + _BS(3), bw - _BS(12), _BS(2.5)), border_radius=_BS(1))
    pygame.draw.rect(s, (255, 255, 255), (bx + bw // 2 - _BS(3), by + _BS(3), _BS(6), _BS(1.5)), border_radius=_BS(0.5))

    # Rivets
    rivet_c = tuple(min(255, v + 30) for v in c["body_shadow"])
    for rx, ry in [(bx + _BS(4), by + _BS(4)), (bx + bw - _BS(4), by + _BS(4)),
                   (bx + _BS(4), by + bh - _BS(4)), (bx + bw - _BS(4), by + bh - _BS(4)),
                   (bx + bw // 2, by + _BS(4)), (bx + bw // 2, by + bh - _BS(4))]:
        pygame.draw.circle(s, rivet_c, (rx, ry), max(1, _BS(1.5)))
        pygame.draw.circle(s, c["body_specular"], (rx - 1, ry - 1), max(1, _BS(0.6)))

    # Material effects
    mat = c["material"]
    if mat == Material.CHROME:
        draw_gloss_overlay(s, body_rect, 100)
        draw_metallic_streak(s, body_rect)
    elif mat == Material.NEON:
        glow_s = pygame.Surface((bw + _BS(6), bh + _BS(6)), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*c["accent"][:3], 40), (0, 0, bw + _BS(6), bh + _BS(6)), border_radius=_BS(6))
        s.blit(glow_s, (bx - _BS(3), by - _BS(3)))
        pygame.draw.rect(s, (*c["accent"][:3], 100), body_rect, max(1, _BS(1.2)), border_radius=_BS(4))

    # Stripes
    stripe_c = c.get("stripe", c["accent"])
    pygame.draw.line(s, stripe_c, (bx + _BS(4), by + _BS(6)), (bx + bw - _BS(4), by + _BS(6)), max(1, _BS(1.5)))
    stripe_dim = tuple(max(0, v - 40) for v in stripe_c)
    pygame.draw.line(s, stripe_dim, (bx + _BS(4), by + _BS(9)), (bx + bw - _BS(4), by + _BS(9)), max(1, _BS(0.8)))

    # ═══════ BOSS-SPECIFIC DECORATIONS ═══════
    spike_c = c.get("spike_color", c["accent"])

    if boss_key == "boss_desert":
        # Scorpion tail spikes on sides
        for side_x in [bx - _BS(2), bx + bw + _BS(2)]:
            for sy in range(by + _BS(8), by + bh - _BS(8), _BS(8)):
                pts = [(side_x, sy), (side_x + (-_BS(6) if side_x < R // 2 else _BS(6)), sy + _BS(2)),
                       (side_x, sy + _BS(4))]
                pygame.draw.polygon(s, spike_c, pts)
                pygame.draw.polygon(s, c["accent"], pts, max(1, _BS(0.6)))
        # Sand symbol on body
        pygame.draw.circle(s, (*c["accent"][:3], 140), (R // 2, by + bh // 2), _BS(5))
        pygame.draw.circle(s, (255, 255, 200, 180), (R // 2, by + bh // 2), _BS(3))

    elif boss_key == "boss_ice":
        # Crystal spikes on corners
        for cx, cy in [(bx - _BS(1), by - _BS(1)), (bx + bw + _BS(1), by - _BS(1)),
                       (bx - _BS(1), by + bh + _BS(1)), (bx + bw + _BS(1), by + bh + _BS(1))]:
            for ang_off in range(0, 360, 60):
                rad = math.radians(ang_off)
                tip_x = cx + math.cos(rad) * _BS(6)
                tip_y = cy + math.sin(rad) * _BS(6)
                base1_x = cx + math.cos(rad + 0.3) * _BS(2)
                base1_y = cy + math.sin(rad + 0.3) * _BS(2)
                base2_x = cx + math.cos(rad - 0.3) * _BS(2)
                base2_y = cy + math.sin(rad - 0.3) * _BS(2)
                pygame.draw.polygon(s, (*spike_c, 180),
                                    [(int(tip_x), int(tip_y)), (int(base1_x), int(base1_y)), (int(base2_x), int(base2_y))])
        # Ice crystal center emblem
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            x1 = R // 2 + int(math.cos(rad) * _BS(2))
            y1 = R // 2 + int(math.sin(rad) * _BS(2))
            x2 = R // 2 + int(math.cos(rad) * _BS(5))
            y2 = R // 2 + int(math.sin(rad) * _BS(5))
            pygame.draw.line(s, (200, 240, 255, 200), (x1, y1), (x2, y2), max(1, _BS(1)))

    elif boss_key == "boss_jungle":
        # Vine tentacles extending from body
        for vi in range(6):
            ang = vi * 60
            rad = math.radians(ang)
            sx = R // 2 + int(math.cos(rad) * _BS(20))
            sy = R // 2 + int(math.sin(rad) * _BS(20))
            ex = R // 2 + int(math.cos(rad) * _BS(30))
            ey = R // 2 + int(math.sin(rad) * _BS(30))
            # Vine body
            pygame.draw.line(s, (30, 140, 30), (sx, sy), (ex, ey), max(1, _BS(2)))
            pygame.draw.line(s, (60, 200, 40), (sx, sy), (ex, ey), max(1, _BS(1)))
            # Vine tip thorns
            pygame.draw.circle(s, spike_c, (ex, ey), _BS(2))
            pygame.draw.circle(s, (255, 50, 255), (ex, ey), max(1, _BS(1)))
        # Toxic symbol
        pygame.draw.circle(s, (*c["accent"][:3], 100), (R // 2, R // 2), _BS(6))
        pygame.draw.circle(s, (0, 0, 0, 80), (R // 2, R // 2), _BS(4))
        pygame.draw.circle(s, c["accent"], (R // 2, R // 2), _BS(2))

    elif boss_key == "boss_final":
        # Skull horns
        for side in [-1, 1]:
            hx = R // 2 + side * _BS(18)
            pts = [(hx, by - _BS(2)),
                   (hx + side * _BS(8), by - _BS(14)),
                   (hx + side * _BS(4), by - _BS(4)),
                   (hx, by + _BS(2))]
            pygame.draw.polygon(s, (60, 0, 0), pts)
            pygame.draw.polygon(s, c["accent"], pts, max(1, _BS(1)))
        # Skull face on turret area
        cx, cy = R // 2, R // 2
        # Eyes
        pygame.draw.circle(s, (255, 0, 0, 200), (cx - _BS(5), cy - _BS(2)), _BS(3))
        pygame.draw.circle(s, (255, 0, 0, 200), (cx + _BS(5), cy - _BS(2)), _BS(3))
        pygame.draw.circle(s, (0, 0, 0), (cx - _BS(5), cy - _BS(2)), _BS(1.5))
        pygame.draw.circle(s, (0, 0, 0), (cx + _BS(5), cy - _BS(2)), _BS(1.5))
        # Nose
        pygame.draw.polygon(s, (80, 0, 0),
                            [(cx, cy + _BS(1)), (cx - _BS(1.5), cy + _BS(3)), (cx + _BS(1.5), cy + _BS(3))])
        # Teeth
        for tx in range(-3, 4):
            pygame.draw.rect(s, (200, 200, 180),
                             (cx + tx * _BS(2) - _BS(1), cy + _BS(4), _BS(1.5), _BS(2)))

    # ── TURRET — larger ──
    tur_cx, tur_cy = R // 2, R // 2 + _BS(2)
    tur_r = _BS(14)
    pygame.draw.circle(s, (0, 0, 0, 25), (tur_cx + _BS(2), tur_cy + _BS(2)), tur_r + _BS(2))
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), tur_r + _BS(2))
    for ri in range(int(tur_r), 0, -1):
        t = 1 - ri / tur_r
        r = int(c["turret_base"][0] * (1 - t * 0.4) + c["turret_highlight"][0] * t * 0.8)
        g = int(c["turret_base"][1] * (1 - t * 0.4) + c["turret_highlight"][1] * t * 0.8)
        b = int(c["turret_base"][2] * (1 - t * 0.4) + c["turret_highlight"][2] * t * 0.8)
        pygame.draw.circle(s, (min(255, r), min(255, g), min(255, b)), (tur_cx, tur_cy), ri)
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), tur_r, max(1, _BS(1.2)))
    pygame.draw.circle(s, c["turret_highlight"], (tur_cx, tur_cy), _BS(5))
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), _BS(5), max(1, _BS(0.8)))
    pygame.draw.circle(s, c["body_specular"], (tur_cx - _BS(3), tur_cy - _BS(3)), _BS(3))

    # ── BARREL — dual barrels for bosses ──
    barrel_w, barrel_h = _BS(4), _BS(22)
    for offset in [-_BS(4), _BS(4)]:
        barrel = pygame.Surface((barrel_w, barrel_h), pygame.SRCALPHA)
        _draw_gradient_rect(barrel, (0, 0, barrel_w, barrel_h), c["barrel_highlight"], c["barrel_base"],
                            border_radius=max(1, _BS(1)))
        pygame.draw.rect(barrel, tuple(max(0, v - 30) for v in c["barrel_base"]),
                         (0, 0, barrel_w, barrel_h), max(1, _BS(0.8)), border_radius=max(1, _BS(1)))
        for band_y in [_BS(4), barrel_h // 2, barrel_h - _BS(4)]:
            pygame.draw.rect(barrel, c["barrel_highlight"], (0, band_y, barrel_w, max(1, _BS(1))))
        muzzle_c = tuple(min(255, v + 35) for v in c["barrel_base"])
        pygame.draw.rect(barrel, muzzle_c, (-1, 0, barrel_w + 2, _BS(3)), border_radius=max(1, _BS(0.8)))
        # Muzzle glow
        pygame.draw.rect(barrel, (*glow_c, 120), (0, 0, barrel_w, _BS(2)), border_radius=max(1, _BS(0.5)))

        # Place barrel on canvas
        if direction == 0:
            s.blit(barrel, (R // 2 - barrel_w // 2 + offset, -_BS(2)))
        elif direction == 1:
            rb = pygame.transform.rotate(barrel, -90)
            s.blit(rb, (R - barrel_h + _BS(2), R // 2 - barrel_w // 2 + offset))
        elif direction == 2:
            rb = pygame.transform.rotate(barrel, 180)
            s.blit(rb, (R // 2 - barrel_w // 2 + offset, R - barrel_h + _BS(2)))
        elif direction == 3:
            rb = pygame.transform.rotate(barrel, 90)
            s.blit(rb, (-_BS(2), R // 2 - barrel_w // 2 + offset))

    # ── Compose with rotation ──
    final = pygame.Surface((R, R), pygame.SRCALPHA)
    if direction == 0:
        final.blit(s, (0, 0))
    elif direction == 1:
        final = pygame.transform.rotate(s, -90)
    elif direction == 2:
        final = pygame.transform.rotate(s, 180)
    elif direction == 3:
        final = pygame.transform.rotate(s, 90)

    # Ensure final is exactly R x R after rotation
    if final.get_width() != R or final.get_height() != R:
        centered = pygame.Surface((R, R), pygame.SRCALPHA)
        cx = (R - final.get_width()) // 2
        cy = (R - final.get_height()) // 2
        centered.blit(final, (cx, cy))
        final = centered

    return pygame.transform.smoothscale(final, (_BOSS_DISPLAY, _BOSS_DISPLAY))


def make_player_tier_surface(tier, direction, target_size=None):
    """Draw player tank with tier-specific detail: higher tier = more accessories & beauty."""
    tier = max(0, min(len(PLAYER_TIER_COLORS) - 1, tier))
    c = PLAYER_TIER_COLORS[tier]
    R = _RTS
    s = pygame.Surface((R, R), pygame.SRCALPHA)

    # ── GROUND SHADOW ──
    shadow = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 25 + tier * 5), (_S(2), _S(7), _S(28), _S(22)))
    s.blit(shadow, (0, 0))

    # ── TRACKS with gradient, road wheels, sprockets ──
    track_w = _S(6) + tier * _S(0.4)
    tw_int = int(track_w)
    track_l = (_S(2), _S(3), tw_int, _S(26))
    track_r = (_S(32) - _S(2) - tw_int, _S(3), tw_int, _S(26))
    for idx_tr, tr in enumerate([track_l, track_r]):
        tx, ty, tw, th = tr
        # Track gradient body
        track_top = c["track_base"]
        track_bot = tuple(max(0, v - 35) for v in c["track_base"])
        _draw_gradient_rect(s, tr, track_top, track_bot, border_radius=_S(3))
        # Track border
        pygame.draw.rect(s, tuple(max(0, v - 45) for v in c["track_base"]),
                         tr, max(1, _S(0.6)), border_radius=_S(3))
        # Tread links — denser at higher tier
        tread_gap = max(_S(1.5), _S(2.5) - tier * _S(0.2))
        for i in range(ty + _S(2), ty + th - _S(1), int(tread_gap)):
            pygame.draw.line(s, c["track_highlight"], (tx + _S(1), i), (tx + tw - _S(2), i), max(1, _S(0.5)))
        # Road wheels — more detailed
        wh_gap = max(_S(3), _S(5) - tier * _S(0.4))
        for wi in range(ty + _S(4), ty + th - _S(3), int(wh_gap)):
            wcx = tx + tw // 2
            wr = _S(1.8) + tier * _S(0.2)
            # Wheel outer
            pygame.draw.circle(s, c["track_rivet"], (wcx, wi), int(wr))
            # Wheel gradient fill
            pygame.draw.circle(s, c["track_highlight"], (wcx, wi), int(wr - _S(0.5)))
            # Wheel hub
            pygame.draw.circle(s, c["track_rivet"], (wcx, wi), max(1, _S(0.7)))
            # Wheel rim
            pygame.draw.circle(s, tuple(max(0, v - 20) for v in c["track_base"]),
                               (wcx, wi), int(wr), max(1, _S(0.3)))
            # Hub highlight
            pygame.draw.circle(s, c["body_specular"], (wcx - 1, wi - 1), max(1, _S(0.3)))
        # Drive sprocket (top) and idler (bottom)
        for sp_y in [ty + _S(2), ty + th - _S(2)]:
            spr = _S(2) + tier * _S(0.2)
            pygame.draw.circle(s, c["track_rivet"], (tx + tw // 2, sp_y), int(spr))
            pygame.draw.circle(s, c["track_highlight"], (tx + tw // 2, sp_y), int(spr - _S(0.5)))
            pygame.draw.circle(s, c["track_rivet"], (tx + tw // 2, sp_y), max(1, _S(0.5)))

        # Tier 2+: side skirt plates
        if tier >= 2:
            skirt_c = tuple(max(0, v - 15) for v in c["body_base"])
            skirt_hl = tuple(min(255, v + 20) for v in c["body_base"])
            if idx_tr == 0:
                _draw_gradient_rect(s, (tx - _S(1), ty + _S(2), _S(2), th - _S(4)), skirt_hl, skirt_c, _S(1))
            else:
                _draw_gradient_rect(s, (tx + tw - _S(1), ty + _S(2), _S(2), th - _S(4)), skirt_hl, skirt_c, _S(1))
        # Tier 3+: track guard with bolts
        if tier >= 3:
            guard_c = tuple(max(0, v - 10) for v in c["body_shadow"])
            gx = tx - _S(1.5) if idx_tr == 0 else tx + tw - _S(0.5)
            pygame.draw.rect(s, guard_c, (int(gx), ty, _S(2), th), border_radius=_S(1))
            for bi in range(ty + _S(3), ty + th - _S(2), _S(5)):
                pygame.draw.circle(s, c["accent"], (int(gx) + _S(1), bi), max(1, _S(0.5)))
        # Tier 4: decorative track trim
        if tier >= 4:
            trim_c = c.get("stripe", (255, 220, 50))
            if idx_tr == 0:
                pygame.draw.line(s, trim_c, (tx, ty + _S(1)), (tx, ty + th - _S(1)), max(1, _S(0.4)))
            else:
                pygame.draw.line(s, trim_c, (tx + tw - 1, ty + _S(1)), (tx + tw - 1, ty + th - _S(1)), max(1, _S(0.4)))

    # ── BODY — gradient-filled, wider at higher tiers, and decorated with premium technology components ──
    body_inset = _S(4) - tier * _S(0.3)
    body_rect = (int(body_inset) + _S(1), _S(4), int(_S(32) - 2 * body_inset - _S(2)), _S(24))
    bx, by, bw, bh = body_rect
    # Ambient shadow
    _draw_ambient_shadow(s, body_rect)
    # Body gradient fill (highlight top → shadow bottom)
    _draw_gradient_rect(s, body_rect, c["body_highlight"], c["body_shadow"], border_radius=_S(3))
    # Body outline
    pygame.draw.rect(s, c["body_shadow"], body_rect, max(1, _S(0.7)), border_radius=_S(3))

    # 1. Premium mechanical engine vent grills (higher tier = more power grids!)
    vent_y = by + bh - _S(5)
    num_vents = 2 + tier // 2
    for vi in range(num_vents):
        vy = vent_y + vi * _S(1.5)
        # Deep groove
        pygame.draw.rect(s, (20, 22, 30), (bx + _S(3), vy, bw - _S(6), max(1, _S(0.8))))
        # Super-glowing thermal grids (Teal/Red/Gold depending on tier)
        glow_color = (0, 240, 255) if tier % 2 == 0 else (255, 80, 0)
        if tier >= 4:
            glow_color = (255, 215, 0)
        pygame.draw.rect(s, glow_color, (bx + _S(5), vy, bw - _S(10), max(1, _S(0.4))))

    # 2. Cyber wiring running from power cores
    pygame.draw.line(s, (0, 255, 150), (bx + _S(2), by + _S(7)), (bx + _S(6), by + _S(11)), max(1, _S(0.6)))
    pygame.draw.line(s, (255, 0, 150), (bx + bw - _S(2), by + _S(7)), (bx + bw - _S(6), by + _S(11)), max(1, _S(0.6)))

    # 3. Active Glowing Front Scanning Visor (pulses dynamically with tier!)
    visor_color = (0, 180, 255) if tier < 3 else (255, 0, 128)
    pygame.draw.rect(s, visor_color, (bx + _S(3), by + _S(2), bw - _S(6), _S(1.5)), border_radius=_S(0.5))
    pygame.draw.rect(s, (255, 255, 255), (bx + bw // 2 - _S(2), by + _S(2), _S(4), _S(1.0)), border_radius=_S(0.5))

    # Armor panel lines with depth (3D effect)
    panel_c = tuple(max(0, v - 25) for v in c["body_base"])
    panel_hl = tuple(min(255, v + 15) for v in c["body_base"])
    # Vertical panels
    for px in [bx + _S(5), bx + bw - _S(5)]:
        pygame.draw.line(s, panel_c, (px, by + _S(2)), (px, by + bh - _S(2)), max(1, _S(0.5)))
        pygame.draw.line(s, panel_hl, (px + 1, by + _S(2)), (px + 1, by + bh - _S(2)), max(1, _S(0.3)))
    # Horizontal panel
    if tier >= 1:
        pygame.draw.line(s, panel_c, (bx + _S(2), by + bh // 2), (bx + bw - _S(2), by + bh // 2), max(1, _S(0.5)))
        pygame.draw.line(s, panel_hl, (bx + _S(2), by + bh // 2 + 1), (bx + bw - _S(2), by + bh // 2 + 1), max(1, _S(0.3)))
    if tier >= 2:
        pygame.draw.line(s, panel_c, (bx + _S(2), by + _S(4)), (bx + bw - _S(2), by + _S(4)), max(1, _S(0.4)))
        pygame.draw.line(s, panel_c, (bx + _S(2), by + bh - _S(4)), (bx + bw - _S(2), by + bh - _S(4)), max(1, _S(0.4)))

    # Corner rivets — more at higher tiers
    rivet_c = tuple(min(255, v + 25) for v in c["body_shadow"])
    rivet_positions = [(bx + _S(3), by + _S(3)), (bx + bw - _S(3), by + _S(3)),
                       (bx + _S(3), by + bh - _S(3)), (bx + bw - _S(3), by + bh - _S(3))]
    if tier >= 2:
        rivet_positions += [(bx + bw // 2, by + _S(3)), (bx + bw // 2, by + bh - _S(3))]
    if tier >= 3:
        rivet_positions += [(bx + _S(3), by + bh // 2), (bx + bw - _S(3), by + bh // 2)]
    for rx, ry in rivet_positions:
        pygame.draw.circle(s, rivet_c, (rx, ry), max(1, _S(0.7)))
        pygame.draw.circle(s, c["body_specular"], (rx - 1, ry - 1), max(1, _S(0.3)))

    # Material effects
    mat = c["material"]
    if mat == Material.MATTE:
        draw_gloss_overlay(s, body_rect, 35 + tier * 8)
    elif mat == Material.METALLIC:
        draw_gloss_overlay(s, body_rect, 60 + tier * 10)
    elif mat == Material.CHROME:
        draw_gloss_overlay(s, body_rect, 100 + tier * 8)
        draw_metallic_streak(s, body_rect)

    # ── STRIPE / DECORATION ──
    stripe_c = c.get("stripe", c["accent"])
    if tier == 0:
        pygame.draw.line(s, stripe_c, (bx + _S(4), by + _S(4)), (bx + bw - _S(4), by + _S(4)), max(1, _S(0.8)))
    elif tier == 1:
        pygame.draw.line(s, stripe_c, (bx + _S(3), by + _S(3)), (bx + bw - _S(3), by + _S(3)), _S(1))
        pygame.draw.line(s, stripe_c, (bx + _S(3), by + _S(5)), (bx + bw - _S(3), by + _S(5)), max(1, _S(0.6)))
    elif tier == 2:
        # Chevron V
        mid_x = bx + bw // 2
        pygame.draw.line(s, stripe_c, (mid_x, by + _S(2)), (bx + _S(4), by + _S(5)), _S(1))
        pygame.draw.line(s, stripe_c, (mid_x, by + _S(2)), (bx + bw - _S(4), by + _S(5)), _S(1))
        # Second faint chevron
        stripe_dim = tuple(max(0, v - 50) for v in stripe_c)
        pygame.draw.line(s, stripe_dim, (mid_x, by + _S(4)), (bx + _S(5), by + _S(7)), max(1, _S(0.6)))
        pygame.draw.line(s, stripe_dim, (mid_x, by + _S(4)), (bx + bw - _S(5), by + _S(7)), max(1, _S(0.6)))
    elif tier == 3:
        # Tiger stripes with gradient
        for si in range(4):
            sx = bx + _S(3) + si * _S(6)
            pygame.draw.line(s, stripe_c, (sx, by + _S(2)), (sx + _S(2), by + bh - _S(2)), _S(1))
            stripe_dim = tuple(max(0, v - 40) for v in stripe_c)
            pygame.draw.line(s, stripe_dim, (sx + _S(1), by + _S(2)), (sx + _S(3), by + bh - _S(2)), max(1, _S(0.5)))
    else:
        # Gold racing stripes
        gold = (255, 220, 50)
        gold_dim = (200, 170, 30)
        pygame.draw.line(s, gold, (bx + _S(3), by + _S(2)), (bx + _S(3), by + bh - _S(2)), _S(1))
        pygame.draw.line(s, gold_dim, (bx + _S(4), by + _S(2)), (bx + _S(4), by + bh - _S(2)), max(1, _S(0.5)))
        pygame.draw.line(s, gold, (bx + bw - _S(3), by + _S(2)), (bx + bw - _S(3), by + bh - _S(2)), _S(1))
        pygame.draw.line(s, gold_dim, (bx + bw - _S(4), by + _S(2)), (bx + bw - _S(4), by + bh - _S(2)), max(1, _S(0.5)))
        # Star emblem
        ecx, ecy = bx + bw // 2, by + bh // 2 + _S(2)
        star_r = _S(3)
        for si in range(5):
            a1 = math.radians(si * 72 - 90)
            a2 = math.radians(si * 72 + 36 - 90)
            ox = ecx + int(math.cos(a1) * star_r)
            oy = ecy + int(math.sin(a1) * star_r)
            ix = ecx + int(math.cos(a2) * star_r * 0.4)
            iy = ecy + int(math.sin(a2) * star_r * 0.4)
            pygame.draw.line(s, c["emblem"], (ecx, ecy), (ox, oy), max(1, _S(0.6)))
            pygame.draw.line(s, c["emblem"], (ox, oy), (ix, iy), max(1, _S(0.4)))

    # ── REACTIVE ARMOR (tier 3+) ──
    if tier >= 3:
        ra_c = tuple(min(255, v + 30) for v in c["body_base"])
        ra_sh = tuple(max(0, v - 10) for v in c["body_base"])
        num_era = 3 if tier == 3 else 4
        for ri in range(num_era):
            ry = by + _S(2) + ri * (bh - _S(4)) // num_era
            for side_x in [bx - _S(1), bx + bw - _S(1)]:
                _draw_gradient_rect(s, (side_x, ry, _S(2), _S(4)), ra_c, ra_sh, max(1, _S(0.5)))
                pygame.draw.rect(s, c["body_shadow"], (side_x, ry, _S(2), _S(4)), max(1, _S(0.3)), border_radius=max(1, _S(0.5)))

    # ── FRONT ARMOR PLATE (tier 2+) ──
    if tier >= 2:
        plate_top = tuple(min(255, v + 10) for v in c["body_base"])
        plate_bot = tuple(max(0, v - 20) for v in c["body_base"])
        _draw_gradient_rect(s, (bx + _S(1), by - _S(1), bw - _S(2), _S(2)), plate_top, plate_bot, _S(1))

    # ── TURRET with gradient, ring, details ──
    tur_cx, tur_cy = R // 2, R // 2 + _S(1)
    tur_r = _S(7) + tier * _S(0.8)
    # Turret shadow
    pygame.draw.circle(s, (0, 0, 0, 18), (tur_cx + _S(1), tur_cy + _S(1)), int(tur_r + _S(1)))
    # Turret base ring
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), int(tur_r + _S(1)))
    # Turret body with radial gradient
    for ri in range(int(tur_r), 0, -1):
        t = 1 - ri / tur_r
        r = int(c["turret_base"][0] * (1 - t * 0.5) + c["turret_highlight"][0] * t * 0.9)
        g = int(c["turret_base"][1] * (1 - t * 0.5) + c["turret_highlight"][1] * t * 0.9)
        b = int(c["turret_base"][2] * (1 - t * 0.5) + c["turret_highlight"][2] * t * 0.9)
        pygame.draw.circle(s, (min(255, r), min(255, g), min(255, b)), (tur_cx, tur_cy), ri)
    # Turret rim
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), int(tur_r), max(1, _S(0.8)))
    # Inner ring
    inner_r = int(tur_r - _S(2))
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), inner_r, max(1, _S(0.4)))
    # Hatch
    hatch_r = _S(2.5) + tier * _S(0.3)
    pygame.draw.circle(s, c["turret_highlight"], (tur_cx, tur_cy), int(hatch_r))
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), int(hatch_r), max(1, _S(0.4)))
    # Specular highlight
    pygame.draw.circle(s, c["body_specular"], (tur_cx - _S(2), tur_cy - _S(2)), _S(2))
    pygame.draw.circle(s, (255, 255, 255, 60), (tur_cx - _S(1.5), tur_cy - _S(1.5)), max(1, _S(0.8)))

    # Tier 2+: periscope
    if tier >= 2:
        pygame.draw.rect(s, c["body_shadow"], (tur_cx + int(tur_r) - _S(2), tur_cy - _S(1), _S(3), _S(2)),
                         border_radius=max(1, _S(0.5)))
        pygame.draw.rect(s, c["body_specular"], (tur_cx + int(tur_r) - _S(1.5), tur_cy - _S(0.5), _S(1.5), _S(0.8)))
    # Tier 3+: turret basket
    if tier >= 3:
        pygame.draw.rect(s, c["track_base"], (tur_cx - int(tur_r) - _S(1), tur_cy + int(tur_r) - _S(2), _S(3), _S(3)),
                         border_radius=max(1, _S(0.5)))
        pygame.draw.rect(s, c["track_highlight"], (tur_cx - int(tur_r), tur_cy + int(tur_r) - _S(1.5), _S(2), _S(2)),
                         border_radius=max(1, _S(0.3)))
    # Tier 4: commander's cupola
    if tier >= 4:
        cup_r = _S(2.5)
        pygame.draw.circle(s, c["body_specular"], (tur_cx + _S(2), tur_cy - _S(2)), int(cup_r))
        pygame.draw.circle(s, c["turret_base"], (tur_cx + _S(2), tur_cy - _S(2)), int(cup_r), max(1, _S(0.4)))
        pygame.draw.circle(s, (255, 255, 255, 50), (tur_cx + _S(1.5), tur_cy - _S(2.5)), max(1, _S(0.6)))

    # ── ANTENNA (tier 3+) ──
    if tier >= 3:
        ant_x = tur_cx - int(tur_r) + _S(1)
        ant_y = tur_cy - _S(2)
        ant_top_y = ant_y - _S(7)
        pygame.draw.line(s, c["track_highlight"], (ant_x, ant_y), (ant_x - _S(2), ant_top_y), max(1, _S(0.5)))
        # Antenna tip glow
        pygame.draw.circle(s, c["accent"], (ant_x - _S(2), ant_top_y), max(1, _S(0.8)))
        pygame.draw.circle(s, (255, 255, 255, 80), (ant_x - _S(2), ant_top_y), max(1, _S(0.5)))
    if tier >= 4:
        ant2_x = tur_cx + int(tur_r) - _S(1)
        ant2_top_y = ant_y - _S(6)
        pygame.draw.line(s, c["track_highlight"], (ant2_x, ant_y), (ant2_x + _S(1), ant2_top_y), max(1, _S(0.5)))
        pygame.draw.circle(s, (255, 80, 80), (ant2_x + _S(1), ant2_top_y), max(1, _S(0.7)))

    # ── HEADLIGHT (tier 1+) ──
    if tier >= 1:
        hl_x = tur_cx + int(tur_r)
        hl_y = tur_cy + _S(3)
        # Light housing
        pygame.draw.circle(s, c["body_shadow"], (hl_x, hl_y), _S(1.5))
        # Light lens
        pygame.draw.circle(s, (255, 255, 220), (hl_x, hl_y), max(1, _S(1)))
        # Light glow
        glow = pygame.Surface((_S(5), _S(5)), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 180, 30), (_S(2.5), _S(2.5)), _S(2.5))
        s.blit(glow, (int(hl_x - _S(2.5)), int(hl_y - _S(2.5))))
    if tier >= 4:
        hl2_x = tur_cx - int(tur_r)
        pygame.draw.circle(s, c["body_shadow"], (hl2_x, hl_y), _S(1.5))
        pygame.draw.circle(s, (255, 255, 220), (hl2_x, hl_y), max(1, _S(1)))

    # ── BARREL(S) — gradient fill, bands, muzzle brake ──
    num_barrels = 1 if tier < 2 else 2
    barrel_w = _S(4) + tier * _S(0.3)
    barrel_h = _S(14) + tier * _S(1)
    bw_int = int(barrel_w)
    bh_int = int(barrel_h)

    barrels_surfs = []
    for _ in range(num_barrels):
        b_s = pygame.Surface((bw_int, bh_int), pygame.SRCALPHA)
        # Barrel gradient
        _draw_gradient_rect(b_s, (0, 0, bw_int, bh_int), c["barrel_highlight"], c["barrel_base"],
                            border_radius=max(1, _S(0.8)))
        # Barrel outline
        pygame.draw.rect(b_s, tuple(max(0, v - 30) for v in c["barrel_base"]),
                         (0, 0, bw_int, bh_int), max(1, _S(0.4)), border_radius=max(1, _S(0.8)))
        # Reinforcement bands
        band_c = c["barrel_highlight"]
        for band_y in [_S(2), bh_int // 2, bh_int - _S(2)]:
            pygame.draw.rect(b_s, band_c, (0, int(band_y), bw_int, max(1, _S(0.7))))
        if tier >= 1:
            pygame.draw.rect(b_s, band_c, (0, bh_int // 3, bw_int, max(1, _S(0.5))))
        # Muzzle end
        muzzle_c = tuple(min(255, v + 35) for v in c["barrel_base"])
        if tier >= 3:
            # Muzzle brake — wider
            pygame.draw.rect(b_s, muzzle_c, (-_S(1), 0, bw_int + _S(2), _S(3)), border_radius=max(1, _S(0.5)))
            # Muzzle brake slots
            pygame.draw.line(b_s, c["body_shadow"], (_S(1), _S(1)), (bw_int - _S(1), _S(1)), max(1, _S(0.3)))
        else:
            pygame.draw.rect(b_s, muzzle_c, (0, 0, bw_int, _S(2)), border_radius=max(1, _S(0.5)))
        # Bore (dark center)
        pygame.draw.line(b_s, (0, 0, 0, 50), (bw_int // 2, 0), (bw_int // 2, _S(1)), max(1, _S(0.4)))
        # Bore evacuator (tier 4)
        if tier >= 4:
            evac_y = bh_int // 3
            pygame.draw.ellipse(b_s, c["barrel_highlight"], (-_S(0.5), evac_y, bw_int + _S(1), _S(3)))
            pygame.draw.ellipse(b_s, c["barrel_base"], (-_S(0.5), evac_y, bw_int + _S(1), _S(3)), max(1, _S(0.3)))
        barrels_surfs.append(b_s)

    # ── Compose final with rotation ──
    final = pygame.Surface((R, R), pygame.SRCALPHA)
    if direction == 0:  # UP
        final.blit(s, (0, 0))
        if num_barrels == 1:
            final.blit(barrels_surfs[0], (R // 2 - bw_int // 2, -_S(1)))
        else:
            final.blit(barrels_surfs[0], (R // 2 - bw_int - _S(1), -_S(1)))
            final.blit(barrels_surfs[1], (R // 2 + _S(1), -_S(1)))
    elif direction == 1:  # RIGHT
        rs = pygame.transform.rotate(s, -90)
        final.blit(rs, (0, 0))
        for bi, b_sf in enumerate(barrels_surfs):
            rb = pygame.transform.rotate(b_sf, -90)
            if num_barrels == 1:
                final.blit(rb, (R - bh_int + _S(1), R // 2 - bw_int // 2))
            else:
                offset = -bw_int - _S(1) + bi * (bw_int + _S(2))
                final.blit(rb, (R - bh_int + _S(1), R // 2 + offset))
    elif direction == 2:  # DOWN
        rs = pygame.transform.rotate(s, 180)
        final.blit(rs, (0, 0))
        for bi, b_sf in enumerate(barrels_surfs):
            rb = pygame.transform.rotate(b_sf, 180)
            if num_barrels == 1:
                final.blit(rb, (R // 2 - bw_int // 2, R - bh_int + _S(1)))
            else:
                offset = -bw_int - _S(1) + bi * (bw_int + _S(2))
                final.blit(rb, (R // 2 + offset, R - bh_int + _S(1)))
    elif direction == 3:  # LEFT
        rs = pygame.transform.rotate(s, 90)
        final.blit(rs, (0, 0))
        for bi, b_sf in enumerate(barrels_surfs):
            rb = pygame.transform.rotate(b_sf, 90)
            if num_barrels == 1:
                final.blit(rb, (-_S(1), R // 2 - bw_int // 2))
            else:
                offset = -bw_int - _S(1) + bi * (bw_int + _S(2))
                final.blit(rb, (-_S(1), R // 2 + offset))

    if target_size is not None:
        return pygame.transform.smoothscale(final, (target_size, target_size))
    return _downscale(final, TS, TS)

# ═══════════════════════════════════════════════
#  BULLETS - ENHANCED (supersampled)
# ═══════════════════════════════════════════════

def make_bullet(color=(255, 225, 80)):
    R = _S(12)
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color[:3], 60), (R // 2, R // 2), _S(5))
    pygame.draw.circle(s, (*color[:3], 180), (R // 2, R // 2), _S(3))
    pygame.draw.circle(s, (255, 255, 255, 220), (_S(5), _S(5)), _S(1))
    return _downscale(s, 12, 12)

def make_bullet_advanced(kind="pierce"):
    R = _S(16)
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    if kind == "pierce":
        pygame.draw.ellipse(s, (80, 200, 255, 60), (0, _S(2), R, _S(12)))
        pygame.draw.ellipse(s, (80, 200, 255, 200), (_S(2), _S(4), _S(12), _S(8)))
        pygame.draw.ellipse(s, (200, 240, 255), (_S(4), _S(6), _S(8), _S(4)))
    elif kind == "bomb":
        pygame.draw.circle(s, (60, 60, 60), (R // 2, R // 2), _S(7))
        pygame.draw.circle(s, (255, 120, 50), (R // 2, R // 2), _S(5))
        pygame.draw.circle(s, (255, 200, 100), (R // 2, R // 2), _S(3))
        pygame.draw.circle(s, (40, 40, 40), (R // 2, R // 2), _S(7), _S(1))
    elif kind == "laser":
        pygame.draw.rect(s, (0, 255, 180, 60), (_S(2), _S(6), _S(12), _S(4)))
        pygame.draw.rect(s, (0, 255, 180, 200), (_S(4), _S(7), _S(8), _S(2)))
        pygame.draw.rect(s, (200, 255, 240), (_S(5), _S(7), _S(6), _S(1)))
    elif kind == "plasma":
        pygame.draw.circle(s, (200, 50, 255, 60), (R // 2, R // 2), _S(7))
        pygame.draw.circle(s, (200, 50, 255, 180), (R // 2, R // 2), _S(5))
        pygame.draw.circle(s, (255, 200, 255), (R // 2, R // 2), _S(2))
    elif kind == "rocket":
        # Rocket: elongated body with fire trail
        pygame.draw.ellipse(s, (100, 100, 100), (_S(2), _S(4), _S(12), _S(6)))
        pygame.draw.ellipse(s, (180, 50, 30), (_S(3), _S(5), _S(10), _S(4)))
        pygame.draw.ellipse(s, (255, 200, 50), (_S(1), _S(6), _S(4), _S(3)))  # flame
        pygame.draw.ellipse(s, (255, 100, 30, 150), (0, _S(5), _S(3), _S(4)))  # trail
        pygame.draw.circle(s, (255, 80, 30), (_S(12), R // 2), _S(2))  # nose
    elif kind == "flame":
        # Flame: orange-red fire blob
        pygame.draw.circle(s, (255, 100, 0, 80), (R // 2, R // 2), _S(7))
        pygame.draw.circle(s, (255, 150, 0, 160), (R // 2, R // 2), _S(5))
        pygame.draw.circle(s, (255, 220, 50, 200), (R // 2, R // 2), _S(3))
        pygame.draw.circle(s, (255, 255, 200), (R // 2, R // 2), _S(1))
    return _downscale(s, 16, 16)

# ═══════════════════════════════════════════════
#  EXPLOSIONS - CINEMATIC (supersampled)
# ═══════════════════════════════════════════════

def make_explosion_ultra(num_frames=24):
    frames = []
    R = _S(96)
    cx, cy = R // 2, R // 2
    for i in range(num_frames):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        t = i / num_frames

        r_out = int(_S(8) + _S(40) * t)
        a_out = int(200 * (1 - t))
        fire_c = (255, max(0, int(200 - 200 * t)), max(0, int(50 - 50 * t)), max(0, a_out))
        pygame.draw.circle(s, fire_c, (cx, cy), r_out)

        r_mid = int(_S(6) + _S(30) * t)
        a_mid = int(255 * max(0, 1 - t * 1.3))
        glow_c = (255, max(0, int(255 - 200 * t)), max(0, int(100 - 100 * t)), max(0, a_mid))
        pygame.draw.circle(s, glow_c, (cx, cy), r_mid)

        if t < 0.5:
            r_core = int(_S(4) + _S(15) * t)
            a_core = int(255 * (1 - t * 2))
            pygame.draw.circle(s, (255, 255, max(0, int(200 - 200 * t)), max(0, a_core)), (cx, cy), r_core)

        if t < 0.7:
            for j in range(6):
                angle = math.radians(j * 60 + i * 15)
                dist = _S(10) + _S(35) * t
                sx = cx + math.cos(angle) * dist
                sy = cy + math.sin(angle) * dist
                spark_a = int(200 * (1 - t / 0.7))
                pygame.draw.circle(s, (255, 200, 50, max(0, spark_a)), (int(sx), int(sy)), max(_S(1), int(_S(3) * (1 - t))))

        if t > 0.3:
            smoke_t = (t - 0.3) / 0.7
            r_smoke = int(_S(20) + _S(25) * smoke_t)
            a_smoke = int(80 * (1 - smoke_t))
            pygame.draw.circle(s, (100, 100, 100, max(0, a_smoke)), (cx, cy), r_smoke, max(_S(1), int(_S(4) * (1 - smoke_t))))

        frames.append(_downscale(s, 96, 96))
    return frames

def make_muzzle_flash_ultra():
    frames = []
    R = _S(24)
    for i in range(8):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        t = i / 8
        r = int(_S(4) + _S(8) * (1 - t))
        a = int(255 * (1 - t))
        pygame.draw.circle(s, (255, 255, 200, max(0, a)), (R // 2, R // 2), r)
        if t < 0.5:
            pygame.draw.circle(s, (255, 255, 255, max(0, int(200 * (1 - t * 2)))), (R // 2, R // 2), max(_S(1), r // 2))
        frames.append(_downscale(s, 24, 24))
    return frames

def make_spawn_effect_ultra():
    frames = []
    orig_size = TS + 8  # spawn effect slightly larger than tile
    R = orig_size * _R
    for i in range(16):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        t = i / 16
        cx, cy = R // 2, R // 2

        for ring in range(3):
            rt = max(0, t - ring * 0.1) / (1 - ring * 0.1)
            if rt > 0:
                r = int(_S(4) + _S(20) * rt)
                a = int(180 * (1 - rt))
                pygame.draw.circle(s, (100, 200, 255, max(0, a)), (cx, cy), r, _S(2))

        if t < 0.5:
            fa = int(255 * (1 - t * 2))
            pygame.draw.circle(s, (255, 255, 255, max(0, fa)), (cx, cy), max(_S(1), int(_S(6) * (1 - t * 2))))

        for corner in range(4):
            angle = math.radians(corner * 90 + 45 + t * 180)
            dist = _S(5) + _S(15) * t
            sx = cx + math.cos(angle) * dist
            sy = cy + math.sin(angle) * dist
            sa = int(150 * (1 - t))
            pygame.draw.circle(s, (150, 220, 255, max(0, sa)), (int(sx), int(sy)), max(_S(1), int(_S(2) * (1 - t))))

        frames.append(_downscale(s, orig_size, orig_size))
    return frames

# ═══════════════════════════════════════════════
#  ITEMS - PREMIUM QUALITY (supersampled)
# ═══════════════════════════════════════════════

def make_item_surface(kind):
    orig = 30
    R = _S(orig)
    s = pygame.Surface((R, R), pygame.SRCALPHA)

    colors = {
        "health": (240, 60, 60), "shield": (60, 120, 240),
        "speed": (60, 240, 120), "star": (255, 100, 50),
        "money": (255, 220, 50), "life": (255, 50, 150),
        "rapid": (255, 150, 40), "multi": (220, 200, 40),
        "pierce": (80, 200, 255), "bomb": (100, 100, 100),
        "laser": (0, 255, 180), "plasma": (200, 50, 255),
        "freeze": (120, 220, 255), "max_power": (255, 200, 60),
        "grenade": (90, 180, 90), "gem": (140, 220, 255),
        "rocket": (255, 80, 30), "flame": (255, 150, 0),
    }
    c = colors.get(kind, (200, 200, 200))
    gl = (min(255, c[0] + 60), min(255, c[1] + 60), min(255, c[2] + 60))

    # 1. Gorgeous 3D Outer Halo Glow
    glow = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*c, 45), (R // 2, R // 2), _S(14))
    pygame.draw.circle(glow, (*gl, 20), (R // 2, R // 2), _S(16))
    s.blit(glow, (0, 0))

    # 2. Sleek metallic outer beveled ring
    pygame.draw.circle(s, (15, 15, 25), (R // 2, R // 2), _S(14))
    pygame.draw.circle(s, gl, (R // 2, R // 2), _S(13), max(1, _S(1.5)))
    
    # 3. Polished dark mechanical base center
    pygame.draw.circle(s, (28, 30, 42), (R // 2, R // 2), _S(11))
    
    # Specular ring sheen
    pygame.draw.circle(s, (255, 255, 255, 60), (R // 2 - _S(1), R // 2 - _S(1)), _S(10), 1)

    # 4. Icon drawing with glowing cyber highlights
    if kind == "health":
        pygame.draw.rect(s, c, (_S(11), _S(7), _S(8), _S(16)), border_radius=_S(2))
        pygame.draw.rect(s, c, (_S(7), _S(11), _S(16), _S(8)), border_radius=_S(2))
        pygame.draw.rect(s, gl, (_S(12), _S(8), _S(6), _S(14)), border_radius=_S(1))
        pygame.draw.rect(s, gl, (_S(8), _S(12), _S(14), _S(6)), border_radius=_S(1))
    elif kind == "life":
        pygame.draw.ellipse(s, gl, (_S(8), _S(8), _S(8), _S(10)))
        pygame.draw.ellipse(s, gl, (_S(14), _S(8), _S(8), _S(10)))
        pygame.draw.polygon(s, gl, [(_S(8), _S(14)), (_S(22), _S(14)), (_S(15), _S(22))])
        # Core reflection
        pygame.draw.circle(s, (255, 255, 255), (_S(11), _S(11)), _S(1.5))
        pygame.draw.circle(s, (255, 255, 255), (_S(17), _S(11)), _S(1.5))
    elif kind == "shield":
        pts = [(_S(9), _S(8)), (_S(21), _S(8)), (_S(21), _S(15)), (_S(15), _S(22)), (_S(9), _S(15))]
        pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, gl, pts, _S(2))
        pygame.draw.line(s, gl, (_S(15), _S(8)), (_S(15), _S(20)), _S(2))
    elif kind == "speed":
        pts = [(_S(16), _S(6)), (_S(10), _S(14)), (_S(15), _S(14)), (_S(14), _S(24)), (_S(21), _S(12)), (_S(16), _S(12))]
        pygame.draw.polygon(s, gl, pts)
        pygame.draw.polygon(s, (255, 255, 255), pts, 1)
    elif kind == "star":
        pygame.draw.circle(s, gl, (_S(15), _S(15)), _S(4))
        for angle in [0, 120, 240]:
            rad = math.radians(angle - 90)
            x = _S(15) + math.cos(rad) * _S(8)
            y = _S(15) + math.sin(rad) * _S(8)
            pygame.draw.circle(s, c, (int(x), int(y)), _S(4))
            pygame.draw.circle(s, (255, 255, 255), (int(x), int(y)), _S(1))
    elif kind == "money":
        pygame.draw.circle(s, (255, 205, 10), (_S(15), _S(15)), _S(8))
        pygame.draw.circle(s, (255, 255, 130), (_S(15), _S(15)), _S(8), _S(1.5))
        pygame.draw.line(s, (150, 100, 0), (_S(15), _S(10)), (_S(15), _S(20)), _S(2))
        pygame.draw.arc(s, (150, 100, 0), (_S(12), _S(10), _S(6), _S(6)), math.pi / 2, math.pi * 1.5, _S(2))
        pygame.draw.arc(s, (150, 100, 0), (_S(12), _S(14), _S(6), _S(6)), -math.pi / 2, math.pi / 2, _S(2))
    elif kind in ["rapid", "multi"]:
        if kind == "multi":
            pygame.draw.ellipse(s, gl, (_S(13), _S(8), _S(4), _S(10)))
            pygame.draw.ellipse(s, gl, (_S(8), _S(10), _S(4), _S(10)))
            pygame.draw.ellipse(s, gl, (_S(18), _S(10), _S(4), _S(10)))
        else:
            pygame.draw.rect(s, gl, (_S(10), _S(8), _S(4), _S(12)), border_radius=_S(2))
            pygame.draw.rect(s, gl, (_S(16), _S(8), _S(4), _S(12)), border_radius=_S(2))
            pygame.draw.rect(s, (255, 255, 255), (_S(11), _S(9), _S(2), _S(10)), border_radius=_S(1))
            pygame.draw.rect(s, (255, 255, 255), (_S(17), _S(9), _S(2), _S(10)), border_radius=_S(1))
    elif kind == "pierce":
        pts = [(_S(15), _S(6)), (_S(9), _S(16)), (_S(12), _S(16)), (_S(12), _S(22)), (_S(18), _S(22)), (_S(18), _S(16)), (_S(21), _S(16))]
        pygame.draw.polygon(s, gl, pts)
        pygame.draw.line(s, (255, 255, 255), (_S(15), _S(7)), (_S(15), _S(21)), _S(1))
    elif kind == "bomb":
        pygame.draw.circle(s, (50, 50, 50), (_S(14), _S(16)), _S(6.5))
        pygame.draw.circle(s, c, (_S(14), _S(16)), _S(4.5))
        pygame.draw.rect(s, gl, (_S(12), _S(8), _S(4), _S(4)))
        # Lit fuse spark
        pygame.draw.circle(s, (255, 120, 0), (_S(14), _S(6)), _S(2.5))
        pygame.draw.circle(s, (255, 255, 150), (_S(14), _S(6)), _S(1))
    elif kind == "laser":
        pygame.draw.line(s, gl, (_S(8), _S(15)), (_S(22), _S(15)), _S(3))
        pygame.draw.line(s, (255, 255, 255), (_S(10), _S(15)), (_S(20), _S(15)), _S(1))
        pygame.draw.circle(s, (255, 255, 255), (_S(22), _S(15)), _S(2))
    elif kind == "plasma":
        pygame.draw.circle(s, gl, (_S(15), _S(15)), _S(6.5))
        pygame.draw.circle(s, (255, 250, 255), (_S(15), _S(15)), _S(3.5))
        # Orbital spark circles
        for ang in (0, 120, 240):
            rad = math.radians(ang)
            px = _S(15) + math.cos(rad) * _S(5)
            py = _S(15) + math.sin(rad) * _S(5)
            pygame.draw.circle(s, (255, 255, 255), (int(px), int(py)), _S(1))
    elif kind == "freeze":
        pygame.draw.circle(s, (235, 245, 255), (_S(15), _S(15)), _S(8))
        pygame.draw.circle(s, (60, 80, 120), (_S(15), _S(15)), _S(8), _S(2))
        pygame.draw.rect(s, (60, 80, 120), (_S(13), _S(4), _S(4), _S(3)), border_radius=_S(1))
        for ang in (0, 90, 180, 270):
            rad = math.radians(ang)
            x = _S(15) + math.cos(rad) * _S(6)
            y = _S(15) + math.sin(rad) * _S(6)
            pygame.draw.circle(s, (60, 80, 120), (int(x), int(y)), _S(1))
        pygame.draw.line(s, (40, 60, 100), (_S(15), _S(15)), (_S(15), _S(10)), _S(2))
        pygame.draw.line(s, (40, 60, 100), (_S(15), _S(15)), (_S(19), _S(17)), _S(2))
        pygame.draw.circle(s, (180, 230, 255), (_S(12), _S(12)), _S(2))
    elif kind == "max_power":
        pygame.draw.rect(s, (60, 60, 70), (_S(6), _S(12), _S(14), _S(5)))
        pygame.draw.rect(s, gl, (_S(6), _S(12), _S(14), _S(5)), _S(1))
        pygame.draw.rect(s, (40, 40, 50), (_S(16), _S(10), _S(8), _S(4)))
        pygame.draw.rect(s, gl, (_S(24), _S(11), _S(1), _S(2)))
        pygame.draw.polygon(s, (90, 60, 40), [(_S(8), _S(17)), (_S(14), _S(17)), (_S(12), _S(24)), (_S(10), _S(24))])
        pygame.draw.polygon(s, (140, 90, 50), [(_S(8), _S(17)), (_S(14), _S(17)), (_S(12), _S(24)), (_S(10), _S(24))], _S(1))
        pygame.draw.circle(s, (60, 60, 70), (_S(13), _S(18)), _S(2), _S(1))
    elif kind == "grenade":
        pygame.draw.rect(s, (60, 90, 50), (_S(10), _S(12), _S(10), _S(12)), border_radius=_S(2))
        pygame.draw.rect(s, c, (_S(10), _S(12), _S(10), _S(12)), _S(1), border_radius=_S(2))
        for gy in range(_S(14), _S(23), _S(3)):
            pygame.draw.line(s, (40, 60, 35), (_S(11), gy), (_S(19), gy), _S(1))
        for gx in range(_S(12), _S(20), _S(3)):
            pygame.draw.line(s, (40, 60, 35), (gx, _S(13)), (gx, _S(23)), _S(1))
        pygame.draw.rect(s, (180, 180, 60), (_S(12), _S(9), _S(6), _S(3)))
        pygame.draw.circle(s, (220, 220, 80), (_S(19), _S(8)), _S(2), _S(1))
        pygame.draw.line(s, (200, 200, 70), (_S(18), _S(9)), (_S(15), _S(11)), _S(1))
    elif kind == "gem":
        diamond = [(_S(15), _S(6)), (_S(22), _S(13)), (_S(15), _S(24)), (_S(8), _S(13))]
        pygame.draw.polygon(s, c, diamond)
        pygame.draw.polygon(s, (255, 255, 255), diamond, _S(1))
        pygame.draw.line(s, (255, 255, 255), (_S(15), _S(6)), (_S(15), _S(24)), _S(1))
        pygame.draw.line(s, (255, 255, 255), (_S(8), _S(13)), (_S(22), _S(13)), _S(1))
        pygame.draw.circle(s, (255, 255, 255), (_S(12), _S(11)), _S(1))
    else:
        pygame.draw.circle(s, c, (_S(15), _S(15)), _S(8))

    # 5. Top glassy highlight overlay
    gloss = pygame.Surface((_S(20), _S(10)), pygame.SRCALPHA)
    pygame.draw.ellipse(gloss, (255, 255, 255, 45), (0, 0, _S(20), _S(10)))
    s.blit(gloss, (_S(5), _S(3)))

    return _downscale(s, orig, orig)

# ═══════════════════════════════════════════════
#  MISC SPRITES (supersampled)
# ═══════════════════════════════════════════════

def make_score_popup_font():
    try:
        f = pygame.font.SysFont("consolas", 16, bold=True)
    except Exception:
        f = pygame.font.Font(None, 20)
    return {v: f.render(f"+{v}", True, (255, 255, 255)) for v in [50, 100, 150, 200, 500]}

def make_chicken_frames_ultra(num_frames=8):
    frames = []
    R = _S(32)
    for i in range(num_frames):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        bob = math.sin(i * 0.8) * _S(2)
        by = int(bob)

        # --- Shadow on ground ---
        pygame.draw.ellipse(s, (0, 0, 0, 25), (_S(5), _S(26) + by, _S(22), _S(5)))

        # --- Feet / legs ---
        leg_phase = math.sin(i * 1.2) * _S(1.5)
        foot_c = (230, 160, 50)
        foot_dk = (190, 120, 30)
        # left leg
        lx = _S(11) + int(leg_phase)
        pygame.draw.line(s, foot_c, (lx, _S(24) + by), (lx, _S(27) + by), _S(1))
        pygame.draw.line(s, foot_dk, (lx - _S(2), _S(27) + by), (lx + _S(2), _S(27) + by), _S(1))
        # right leg
        rx = _S(19) - int(leg_phase)
        pygame.draw.line(s, foot_c, (rx, _S(24) + by), (rx, _S(27) + by), _S(1))
        pygame.draw.line(s, foot_dk, (rx - _S(2), _S(27) + by), (rx + _S(2), _S(27) + by), _S(1))
        # toes
        for fx in [lx, rx]:
            pygame.draw.line(s, foot_dk, (fx, _S(27) + by), (fx - _S(1), _S(28) + by), _S(0.5))
            pygame.draw.line(s, foot_dk, (fx, _S(27) + by), (fx + _S(1), _S(28) + by), _S(0.5))

        # --- Tail feathers ---
        for tf in range(4):
            ta = math.radians(150 + tf * 15 + math.sin(i * 0.6) * 5)
            tx = _S(8) + math.cos(ta) * _S(8)
            ty = _S(17) + by + math.sin(ta) * _S(5)
            tc = random.choice([(240, 200, 60), (255, 220, 80), (220, 180, 40)])
            pygame.draw.line(s, tc, (_S(8), _S(17) + by), (int(tx), int(ty)), _S(1.5))

        # --- Body (plump ellipse) ---
        body_x, body_y = _S(6), _S(12) + by
        body_w, body_h = _S(20), _S(14)
        pygame.draw.ellipse(s, (245, 220, 70), (body_x, body_y, body_w, body_h))
        # feather texture strokes on body
        for _ in range(18):
            fx = body_x + random.randint(_S(3), body_w - _S(3))
            fy = body_y + random.randint(_S(2), body_h - _S(3))
            fc = random.choice([(255, 235, 90), (235, 210, 55), (250, 225, 75)])
            ang = random.uniform(-0.3, 0.3)
            ex = fx + int(math.cos(ang) * _S(2))
            ey = fy + int(math.sin(ang) * _S(1.5))
            pygame.draw.line(s, fc, (fx, fy), (ex, ey), max(1, _S(0.5)))
        # belly highlight
        pygame.draw.ellipse(s, (255, 245, 130), (body_x + _S(4), body_y + _S(5), body_w - _S(8), body_h - _S(6)))

        # --- Wing ---
        wing_phase = math.sin(i * 1.5) * _S(1)
        wing_w = _S(10) + int(wing_phase)
        wing_c = (255, 240, 100)
        wing_dk = (230, 200, 50)
        pygame.draw.ellipse(s, wing_c, (_S(6), _S(15) + by, wing_w, _S(8)))
        pygame.draw.ellipse(s, wing_dk, (_S(6), _S(15) + by, wing_w, _S(8)), max(1, _S(0.5)))
        # feather lines on wing
        for wf in range(3):
            wy = _S(16) + by + wf * _S(2)
            pygame.draw.line(s, wing_dk, (_S(7), wy), (_S(7) + wing_w - _S(3), wy + _S(1)), max(1, _S(0.3)))

        # --- Head ---
        hx, hy = _S(20), _S(8) + by
        pygame.draw.circle(s, (255, 240, 110), (hx, hy), _S(7))
        # head feather texture
        for _ in range(8):
            hfx = hx + random.randint(-_S(4), _S(4))
            hfy = hy + random.randint(-_S(4), _S(4))
            if math.hypot(hfx - hx, hfy - hy) < _S(6):
                pygame.draw.circle(s, random.choice([(255, 245, 120), (250, 235, 100)]), (hfx, hfy), max(1, _S(0.5)))

        # --- Comb (red crest on top) ---
        comb_c = (220, 40, 40)
        comb_hl = (255, 90, 80)
        for ci in range(3):
            cx = hx - _S(2) + ci * _S(2)
            cy = hy - _S(7) - ci % 2 * _S(1)
            pygame.draw.circle(s, comb_c, (cx, cy), _S(2))
            pygame.draw.circle(s, comb_hl, (cx - _S(0.5), cy - _S(0.5)), max(1, _S(0.7)))

        # --- Wattle (red thing under beak) ---
        pygame.draw.ellipse(s, (210, 50, 40), (hx + _S(2), hy + _S(4), _S(3), _S(4)))

        # --- Beak ---
        beak_pts = [(hx + _S(6), hy - _S(1)),
                    (hx + _S(10), hy + _S(1)),
                    (hx + _S(6), hy + _S(2))]
        pygame.draw.polygon(s, (255, 170, 40), beak_pts)
        pygame.draw.polygon(s, (220, 130, 20), beak_pts, max(1, _S(0.4)))
        # beak divider line
        pygame.draw.line(s, (200, 120, 20), (hx + _S(6), hy + _S(0.5)), (hx + _S(9), hy + _S(1)), max(1, _S(0.3)))

        # --- Eye ---
        ex, ey_pos = hx + _S(2), hy - _S(1)
        pygame.draw.circle(s, (255, 255, 255), (ex, ey_pos), _S(2.5))
        pygame.draw.circle(s, (20, 20, 30), (ex + _S(0.5), ey_pos), _S(1.5))
        pygame.draw.circle(s, (255, 255, 255), (ex + _S(1), ey_pos - _S(0.7)), max(1, _S(0.5)))
        # eyelid subtle
        pygame.draw.arc(s, (200, 180, 60), (ex - _S(2.5), ey_pos - _S(3), _S(5), _S(4)),
                        math.pi * 0.1, math.pi * 0.9, max(1, _S(0.3)))

        # --- Blush ---
        blush_s = pygame.Surface((_S(4), _S(3)), pygame.SRCALPHA)
        pygame.draw.ellipse(blush_s, (255, 150, 150, 60), (0, 0, _S(4), _S(3)))
        s.blit(blush_s, (hx - _S(1), hy + _S(2)))

        frames.append(_downscale(s, 32, 32))
    return frames

def make_dog_frames_ultra():
    frames = {}
    body_c = (160, 110, 65)
    body_dk = (120, 80, 45)
    body_lt = (190, 145, 95)
    belly_c = (220, 185, 145)
    nose_c = (30, 25, 25)
    ear_c = (130, 85, 50)
    ear_inner = (180, 120, 90)
    tongue_c = (230, 100, 110)
    R = _S(36)

    for d in ["up", "down", "left", "right"]:
        df = []
        for i in range(4):
            s = pygame.Surface((R, R), pygame.SRCALPHA)
            walk = math.sin(i * 1.5) * _S(2)
            wk = int(walk)

            # --- Shadow ---
            pygame.draw.ellipse(s, (0, 0, 0, 20), (_S(6), _S(30), _S(24), _S(4)))

            # --- Tail ---
            tail_wag = math.sin(i * 2.0) * _S(3)
            if d == "right":
                tx0, ty0 = _S(8), _S(16)
                tx1 = tx0 - _S(5)
                ty1 = ty0 - _S(3) + int(tail_wag)
                pygame.draw.line(s, body_c, (tx0, ty0), (tx1, ty1), _S(2.5))
                pygame.draw.circle(s, body_lt, (tx1, ty1), _S(1.5))
            elif d == "left":
                tx0, ty0 = _S(28), _S(16)
                tx1 = tx0 + _S(5)
                ty1 = ty0 - _S(3) + int(tail_wag)
                pygame.draw.line(s, body_c, (tx0, ty0), (tx1, ty1), _S(2.5))
                pygame.draw.circle(s, body_lt, (tx1, ty1), _S(1.5))
            elif d == "up":
                tx0, ty0 = _S(18), _S(25)
                ty1 = ty0 + _S(5)
                tx1 = tx0 + int(tail_wag)
                pygame.draw.line(s, body_c, (tx0, ty0), (tx1, ty1), _S(2.5))
                pygame.draw.circle(s, body_lt, (tx1, ty1), _S(1.5))
            else:
                tx0, ty0 = _S(18), _S(8)
                ty1 = ty0 - _S(4)
                tx1 = tx0 + int(tail_wag)
                pygame.draw.line(s, body_c, (tx0, ty0), (tx1, ty1), _S(2.5))
                pygame.draw.circle(s, body_lt, (tx1, ty1), _S(1.5))

            # --- Legs ---
            leg_off1 = int(math.sin(i * 1.5) * _S(2))
            leg_off2 = int(math.sin(i * 1.5 + math.pi) * _S(2))
            paw_c = (180, 140, 100)
            if d in ["left", "right"]:
                # front legs
                fl_x = _S(22) if d == "right" else _S(14)
                pygame.draw.line(s, body_dk, (fl_x, _S(23)), (fl_x + leg_off1, _S(29)), _S(2))
                pygame.draw.ellipse(s, paw_c, (fl_x + leg_off1 - _S(1.5), _S(28), _S(3), _S(2)))
                # back legs
                bl_x = _S(12) if d == "right" else _S(22)
                pygame.draw.line(s, body_dk, (bl_x, _S(23)), (bl_x + leg_off2, _S(29)), _S(2))
                pygame.draw.ellipse(s, paw_c, (bl_x + leg_off2 - _S(1.5), _S(28), _S(3), _S(2)))
            else:
                # 4 legs from above/below
                for lx_off, lo in [(_S(10), leg_off1), (_S(14), leg_off2),
                                    (_S(22), leg_off1), (_S(26), leg_off2)]:
                    ly = _S(28) if d == "down" else _S(8)
                    sign = 1 if d == "down" else -1
                    pygame.draw.line(s, body_dk, (lx_off, ly), (lx_off, ly + sign * _S(3) + lo), _S(1.5))
                    pygame.draw.ellipse(s, paw_c, (lx_off - _S(1), ly + sign * _S(3) + lo - _S(0.5), _S(2.5), _S(2)))

            # --- Body ---
            bx, by_v, bw, bh_v = _S(7), _S(12), _S(22), _S(14)
            pygame.draw.ellipse(s, body_c, (bx, by_v, bw, bh_v))
            # fur texture
            for _ in range(25):
                fx = bx + random.randint(_S(2), bw - _S(2))
                fy = by_v + random.randint(_S(2), bh_v - _S(2))
                dist = math.hypot(fx - (bx + bw / 2), fy - (by_v + bh_v / 2))
                if dist < bw / 2 - _S(1):
                    fc = random.choice([body_lt, body_dk, (150, 105, 60)])
                    ang = random.uniform(-0.5, 0.5)
                    ex = fx + int(math.cos(ang) * _S(2))
                    ey = fy + int(math.sin(ang) * _S(1))
                    pygame.draw.line(s, fc, (fx, fy), (ex, ey), max(1, _S(0.4)))
            # belly lighter patch
            pygame.draw.ellipse(s, belly_c, (bx + _S(5), by_v + _S(5), bw - _S(10), bh_v - _S(6)))
            # spot pattern (random darker patch)
            spot_x = bx + random.randint(_S(4), bw - _S(6))
            spot_y = by_v + random.randint(_S(2), bh_v - _S(5))
            pygame.draw.ellipse(s, body_dk, (spot_x, spot_y, _S(5), _S(4)))

            # --- Head ---
            if d == "right":
                hx, hy = _S(26), _S(12)
                # head
                pygame.draw.circle(s, body_c, (hx, hy), _S(8))
                pygame.draw.circle(s, body_lt, (hx + _S(1), hy - _S(1)), _S(5))
                # ear (floppy)
                ear_pts = [(hx - _S(3), hy - _S(7)),
                           (hx - _S(6), hy - _S(2)),
                           (hx - _S(1), hy - _S(4))]
                pygame.draw.polygon(s, ear_c, ear_pts)
                pygame.draw.polygon(s, ear_inner, [(ear_pts[0][0]+_S(1), ear_pts[0][1]+_S(1)),
                                                    (ear_pts[1][0]+_S(1), ear_pts[1][1]),
                                                    (ear_pts[2][0], ear_pts[2][1])], max(1, _S(0.5)))
                # snout / muzzle
                pygame.draw.ellipse(s, belly_c, (hx + _S(3), hy - _S(2), _S(7), _S(5)))
                pygame.draw.circle(s, nose_c, (hx + _S(8), hy - _S(1)), _S(1.5))
                pygame.draw.circle(s, (60, 50, 50), (hx + _S(8), hy - _S(1)), _S(1.5), max(1, _S(0.3)))
                # nose highlight
                pygame.draw.circle(s, (80, 70, 70), (hx + _S(7.5), hy - _S(1.5)), max(1, _S(0.5)))
                # mouth line
                pygame.draw.arc(s, body_dk, (hx + _S(4), hy, _S(5), _S(3)),
                               -math.pi * 0.8, 0, max(1, _S(0.3)))
                # tongue
                if i % 3 == 0:
                    pygame.draw.ellipse(s, tongue_c, (hx + _S(5), hy + _S(2), _S(3), _S(2.5)))
                # eye
                pygame.draw.circle(s, (255, 255, 250), (hx + _S(2), hy - _S(2)), _S(2.5))
                pygame.draw.circle(s, (50, 35, 20), (hx + _S(2.5), hy - _S(2)), _S(1.5))
                pygame.draw.circle(s, (255, 255, 255), (hx + _S(3), hy - _S(2.5)), max(1, _S(0.6)))
                # eyebrow
                pygame.draw.arc(s, body_dk, (hx, hy - _S(5), _S(5), _S(3)),
                               math.pi * 0.2, math.pi * 0.8, max(1, _S(0.4)))

            elif d == "left":
                hx, hy = _S(10), _S(12)
                pygame.draw.circle(s, body_c, (hx, hy), _S(8))
                pygame.draw.circle(s, body_lt, (hx - _S(1), hy - _S(1)), _S(5))
                # ear
                ear_pts = [(hx + _S(3), hy - _S(7)),
                           (hx + _S(6), hy - _S(2)),
                           (hx + _S(1), hy - _S(4))]
                pygame.draw.polygon(s, ear_c, ear_pts)
                pygame.draw.polygon(s, ear_inner, [(ear_pts[0][0]-_S(1), ear_pts[0][1]+_S(1)),
                                                    (ear_pts[1][0]-_S(1), ear_pts[1][1]),
                                                    (ear_pts[2][0], ear_pts[2][1])], max(1, _S(0.5)))
                # snout
                pygame.draw.ellipse(s, belly_c, (hx - _S(10), hy - _S(2), _S(7), _S(5)))
                pygame.draw.circle(s, nose_c, (hx - _S(8), hy - _S(1)), _S(1.5))
                pygame.draw.circle(s, (80, 70, 70), (hx - _S(7.5), hy - _S(1.5)), max(1, _S(0.5)))
                # mouth
                pygame.draw.arc(s, body_dk, (hx - _S(9), hy, _S(5), _S(3)),
                               math.pi, math.pi * 1.8, max(1, _S(0.3)))
                if i % 3 == 0:
                    pygame.draw.ellipse(s, tongue_c, (hx - _S(8), hy + _S(2), _S(3), _S(2.5)))
                # eye
                pygame.draw.circle(s, (255, 255, 250), (hx - _S(2), hy - _S(2)), _S(2.5))
                pygame.draw.circle(s, (50, 35, 20), (hx - _S(2.5), hy - _S(2)), _S(1.5))
                pygame.draw.circle(s, (255, 255, 255), (hx - _S(3), hy - _S(2.5)), max(1, _S(0.6)))
                pygame.draw.arc(s, body_dk, (hx - _S(5), hy - _S(5), _S(5), _S(3)),
                               math.pi * 0.2, math.pi * 0.8, max(1, _S(0.4)))

            elif d == "up":
                hx, hy = _S(18), _S(8)
                pygame.draw.circle(s, body_c, (hx, hy), _S(8))
                pygame.draw.circle(s, body_lt, (hx, hy - _S(1)), _S(5))
                # ears (both visible from back)
                for ex_off in [-_S(6), _S(6)]:
                    ep = [(hx + ex_off, hy - _S(7)),
                          (hx + ex_off - _S(2), hy - _S(1)),
                          (hx + ex_off + _S(2), hy - _S(1))]
                    pygame.draw.polygon(s, ear_c, ep)
                    pygame.draw.polygon(s, ear_inner, ep, max(1, _S(0.5)))
                # back of head fur tuft
                for _ in range(6):
                    fx = hx + random.randint(-_S(3), _S(3))
                    fy = hy + random.randint(-_S(3), _S(3))
                    pygame.draw.circle(s, random.choice([body_c, body_lt]), (fx, fy), max(1, _S(0.6)))

            else:  # down
                hx, hy = _S(18), _S(20)
                pygame.draw.circle(s, body_c, (hx, hy), _S(8))
                pygame.draw.circle(s, body_lt, (hx, hy + _S(1)), _S(5))
                # ears
                for ex_off in [-_S(6), _S(6)]:
                    ep = [(hx + ex_off, hy - _S(6)),
                          (hx + ex_off - _S(2), hy),
                          (hx + ex_off + _S(2), hy)]
                    pygame.draw.polygon(s, ear_c, ep)
                    pygame.draw.polygon(s, ear_inner, ep, max(1, _S(0.5)))
                # face - snout
                pygame.draw.ellipse(s, belly_c, (hx - _S(4), hy + _S(2), _S(8), _S(5)))
                # nose
                pygame.draw.circle(s, nose_c, (hx, hy + _S(4)), _S(1.5))
                pygame.draw.circle(s, (80, 70, 70), (hx - _S(0.5), hy + _S(3.5)), max(1, _S(0.5)))
                # mouth
                pygame.draw.arc(s, body_dk, (hx - _S(2), hy + _S(4), _S(4), _S(2)),
                               -math.pi * 0.9, -math.pi * 0.1, max(1, _S(0.3)))
                if i % 3 == 0:
                    pygame.draw.ellipse(s, tongue_c, (hx - _S(1), hy + _S(6), _S(2.5), _S(2)))
                # eyes
                for exx in [-_S(3), _S(3)]:
                    pygame.draw.circle(s, (255, 255, 250), (hx + exx, hy - _S(1)), _S(2.2))
                    pygame.draw.circle(s, (50, 35, 20), (hx + exx, hy - _S(0.5)), _S(1.3))
                    pygame.draw.circle(s, (255, 255, 255), (hx + exx + _S(0.5), hy - _S(1.2)), max(1, _S(0.4)))
                # eyebrows
                for exx in [-_S(3), _S(3)]:
                    pygame.draw.arc(s, body_dk, (hx + exx - _S(2), hy - _S(4), _S(4), _S(3)),
                                   math.pi * 0.2, math.pi * 0.8, max(1, _S(0.4)))

            df.append(_downscale(s, 36, 36))
        frames[d] = df
    return frames

# ═══════════════════════════════════════════════
#  WEATHER EFFECTS (supersampled)
# ═══════════════════════════════════════════════

def make_rain_drop():
    R_w, R_h = _S(4), _S(12)
    s = pygame.Surface((R_w, R_h), pygame.SRCALPHA)
    pygame.draw.line(s, (150, 180, 255, 120), (_S(2), 0), (_S(1), _S(11)), _S(1))
    return _downscale(s, 4, 12)

def make_snow_flake():
    R = _S(6)
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.circle(s, (230, 235, 255, 150), (R // 2, R // 2), _S(2))
    return _downscale(s, 6, 6)

def make_sand_particle():
    R = _S(4)
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    pygame.draw.circle(s, (230, 200, 150, 150), (R // 2, R // 2), _S(2))
    return _downscale(s, 4, 4)

# ═══════════════════════════════════════════════
#  MINIMAP ICONS (supersampled)
# ═══════════════════════════════════════════════

def make_minimap_player_icon():
    R = _S(6)
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    # Bright glowing neon cyan player dot with a white center
    pygame.draw.circle(s, (0, 240, 255), (R // 2, R // 2), _S(3))
    pygame.draw.circle(s, (255, 255, 255), (R // 2, R // 2), _S(1.5))
    return _downscale(s, 6, 6)

def make_minimap_enemy_icon():
    R = _S(6)
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    # Glowing neon red enemy dot with a dark core
    pygame.draw.circle(s, (255, 30, 30), (R // 2, R // 2), _S(3))
    pygame.draw.circle(s, (255, 250, 250), (R // 2, R // 2), _S(1.2))
    return _downscale(s, 6, 6)

def make_minimap_base_icon():
    R = _S(8)
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    # High-tech glowing gold base core
    pygame.draw.circle(s, (255, 215, 0), (R // 2, R // 2), _S(4))
    pygame.draw.circle(s, (255, 255, 255), (R // 2, R // 2), _S(2))
    pygame.draw.circle(s, (255, 100, 0), (R // 2, R // 2), _S(4), _S(1))
    return _downscale(s, 8, 8)

# ═══════════════════════════════════════════════
#  UI ELEMENTS
# ═══════════════════════════════════════════════

def make_button_bg(w, h, color=(40, 60, 100), border_color=(80, 130, 200)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, 235), (0, 0, w, h), border_radius=8)
    pygame.draw.rect(s, border_color, (0, 0, w, h), 2, border_radius=8)
    # Bright top sheen line
    pygame.draw.line(s, (255, 255, 255, 90), (4, 2), (w - 5, 2), 1)
    draw_gloss_overlay(s, (2, 2, w - 4, h // 2), 50)
    return s

def make_panel_bg(w, h, color=(20, 25, 40)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, 240), (0, 0, w, h), border_radius=12)
    pygame.draw.rect(s, (70, 90, 140), (0, 0, w, h), 2, border_radius=12)
    # Beveled edge inside
    pygame.draw.rect(s, (255, 255, 255, 20), (2, 2, w - 4, h - 4), 1, border_radius=10)
    return s

def make_pet_sprites():
    """Create pet sprites: each pet has 'idle' and 'attack' frames, 48x48 output.
    Rendered at 30x internal resolution for ultra-detailed results."""
    pets = {}
    out = 48
    _PR = 8   # pet render multiplier (was 30 - cut for fast startup)
    R = _PR * out  # internal render size

    def S(v):
        return int(v * _PR)

    # ── WOLF ──
    for frame in ("idle", "attack"):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        cx, cy = R // 2, R // 2
        # Ground shadow
        shadow = pygame.Surface((R, R), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 30), (cx - S(11), cy + S(7), S(22), S(5.5)))
        s.blit(shadow, (0, 0))
        # Tail (bushy, behind body)
        tail_pts = [(cx - S(8), cy), (cx - S(14), cy - S(8)), (cx - S(12), cy - S(10)),
                     (cx - S(10), cy - S(9)), (cx - S(9), cy - S(6)), (cx - S(7), cy - S(2))]
        pygame.draw.polygon(s, (90, 95, 115), tail_pts)
        pygame.draw.polygon(s, (115, 120, 140), tail_pts, max(1, S(0.6)))
        # Tail tip highlight
        pygame.draw.circle(s, (180, 200, 220), (cx - S(12), cy - S(9)), S(2))
        # Fur strokes on tail
        for _ in range(15):
            fx = cx - S(10) + random.randint(-S(3), S(2))
            fy = cy - S(6) + random.randint(-S(3), S(2))
            fc = random.choice([(100, 105, 125), (130, 135, 155), (80, 85, 105)])
            ang = random.uniform(-1.0, -0.3)
            pygame.draw.line(s, fc, (fx, fy), (fx + int(math.cos(ang)*S(2)), fy + int(math.sin(ang)*S(2))), max(1, S(0.5)))
        # Body (gradient ellipse)
        body_x, body_y, body_w, body_h = cx - S(9), cy - S(4), S(18), S(12)
        _draw_gradient_rect(s, (body_x, body_y, body_w, body_h), (130, 135, 155), (80, 85, 105), S(4))
        pygame.draw.ellipse(s, (110, 115, 135), (body_x, body_y, body_w, body_h))
        pygame.draw.ellipse(s, (140, 145, 165), (body_x + S(1), body_y + S(1), body_w - S(2), body_h - S(2)))
        # Belly lighter patch
        pygame.draw.ellipse(s, (180, 190, 210), (cx - S(5), cy + S(1), S(10), S(5)))
        # Fur texture on body
        for _ in range(35):
            fx = body_x + random.randint(S(2), body_w - S(2))
            fy = body_y + random.randint(S(2), body_h - S(2))
            fc = random.choice([(150, 160, 180), (100, 105, 125), (120, 130, 150)])
            ang = random.uniform(-0.4, 0.4)
            pygame.draw.line(s, fc, (fx, fy), (fx + int(math.cos(ang)*S(2)), fy + int(math.sin(ang)*S(1.5))), max(1, S(0.5)))
        
        # ── CYBER NEON COLLAR (Giao diện vòng cổ công nghệ cực đỉnh) ──
        pygame.draw.ellipse(s, (0, 240, 255), (cx + S(1.5), cy - S(4), S(6), S(3)))
        pygame.draw.ellipse(s, (255, 255, 255), (cx + S(2.5), cy - S(3.5), S(4), S(2)))

        # Legs with paw detail
        leg_y = cy + S(6)
        for li, lx in enumerate([cx - S(6), cx - S(3), cx + S(3), cx + S(6)]):
            pygame.draw.rect(s, (90, 95, 115), (lx, leg_y, S(2.5), S(5)), border_radius=S(0.5))
            # Paw
            pygame.draw.ellipse(s, (110, 115, 135), (lx - S(0.3), leg_y + S(4), S(3), S(1.5)))
            pygame.draw.ellipse(s, (80, 85, 105), (lx - S(0.3), leg_y + S(4), S(3), S(1.5)), max(1, S(0.3)))
        # Neck
        pygame.draw.ellipse(s, (120, 125, 145), (cx + S(2), cy - S(6), S(8), S(8)))
        # Head
        hx, hy = cx + S(6), cy - S(6)
        pygame.draw.circle(s, (110, 115, 135), (hx, hy), S(6))
        pygame.draw.circle(s, (140, 145, 165), (hx, hy), S(5))
        # Snout
        pygame.draw.ellipse(s, (150, 155, 175), (hx + S(2), hy - S(1.5), S(6), S(4)))
        # Head fur
        for _ in range(20):
            fx = hx + random.randint(-S(4), S(4))
            fy = hy + random.randint(-S(4), S(2))
            if math.hypot(fx - hx, fy - hy) < S(5):
                fc = random.choice([(160, 170, 190), (135, 140, 160)])
                pygame.draw.circle(s, fc, (fx, fy), max(1, S(0.6)))
        # Ears (pointed, detailed)
        for ear_x, flip in [(hx - S(3), -1), (hx + S(2), 1)]:
            ear_pts = [(ear_x, hy - S(4)), (ear_x + flip * S(1), hy - S(10)), (ear_x + flip * S(3), hy - S(4))]
            pygame.draw.polygon(s, (90, 95, 115), ear_pts)
            inner = [(ear_x + flip * S(0.5), hy - S(4.5)), (ear_x + flip * S(1.2), hy - S(8.5)), (ear_x + flip * S(2.5), hy - S(4.5))]
            pygame.draw.polygon(s, (255, 130, 160), inner)
        # Eyes (glowing cyan cyber energy!)
        for ex_off in [-S(2), S(3)]:
            eye_x = hx + ex_off
            eye_y = hy - S(1.5)
            # Eye glow
            glow = pygame.Surface((S(4), S(4)), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 240, 255, 60), (S(2), S(2)), S(2))
            s.blit(glow, (eye_x - S(2), eye_y - S(2)))
            pygame.draw.circle(s, (0, 255, 240), (eye_x, eye_y), S(1.5))
            pygame.draw.circle(s, (255, 255, 255), (eye_x - S(0.3), eye_y - S(0.5)), max(1, S(0.5)))
        # Nose
        pygame.draw.ellipse(s, (25, 20, 25), (hx + S(6), hy - S(1), S(2), S(1.5)))
        # Whiskers / Cheek sparks
        if frame == "attack":
            for _ in range(8):
                sx = hx + S(6) + random.randint(-S(2), S(6))
                sy = hy + random.randint(-S(3), S(3))
                pygame.draw.circle(s, (0, 240, 255, 200), (sx, sy), max(1, S(0.5)))
        pets[f"wolf_{frame}"] = pygame.transform.smoothscale(s, (out, out))

    # ── DRAGON ──
    for frame in ("idle", "attack"):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        cx, cy = R // 2, R // 2
        # Shadow
        shadow = pygame.Surface((R, R), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 35), (cx - S(10), cy + S(7), S(20), S(5)))
        s.blit(shadow, (0, 0))
        # Tail (curved with spikes)
        pygame.draw.arc(s, (180, 30, 10), (cx - S(13), cy, S(12), S(8)), 0.5, 3.14, max(1, S(1.5)))
        pygame.draw.polygon(s, (255, 140, 0), [(cx - S(11), cy + S(4)), (cx - S(13), cy + S(2)), (cx - S(10), cy + S(2))])
        # Body (gradient red/orange scale veins)
        pygame.draw.ellipse(s, (180, 30, 10), (cx - S(7), cy - S(3), S(14), S(10)))
        pygame.draw.ellipse(s, (230, 60, 20), (cx - S(6), cy - S(2), S(12), S(8)))
        # Glowing lava scales
        pygame.draw.ellipse(s, (255, 150, 0), (cx - S(4), cy, S(8), S(4)))
        # Wings (highly detailed, spread)
        for side in (-1, 1):
            w_sign = side
            wing_pts = [
                (cx + w_sign * S(4), cy - S(2)),
                (cx + w_sign * S(13), cy - S(10)),
                (cx + w_sign * S(9), cy - S(4)),
                (cx + w_sign * S(14), cy - S(5)),
                (cx + w_sign * S(6), cy)
            ]
            # Dark outer wing frame
            pygame.draw.polygon(s, (140, 20, 10), wing_pts)
            # Translucent golden wing webbing
            webbing = [
                (cx + w_sign * S(5), cy - S(2.5)),
                (cx + w_sign * S(12), cy - S(9)),
                (cx + w_sign * S(8.5), cy - S(3.5)),
                (cx + w_sign * S(13), cy - S(4.5)),
                (cx + w_sign * S(6.5), cy - S(0.5))
            ]
            pygame.draw.polygon(s, (255, 180, 0, 190), webbing)
            pygame.draw.polygon(s, (255, 255, 100, 130), webbing, max(1, S(0.5)))
        # Head
        hx, hy = cx + S(4), cy - S(5)
        pygame.draw.circle(s, (190, 40, 15), (hx, hy), S(4.5))
        pygame.draw.circle(s, (230, 70, 25), (hx, hy), S(3.5))
        # Golden Horns
        pygame.draw.polygon(s, (255, 215, 0), [(hx - S(2), hy - S(3)), (hx - S(1), hy - S(8)), (hx, hy - S(3))])
        pygame.draw.polygon(s, (255, 215, 0), [(hx + S(1), hy - S(3)), (hx + S(2), hy - S(8)), (hx + S(3), hy - S(3))])
        # Glowing bright neon eyes
        pygame.draw.circle(s, (255, 255, 0), (hx - S(1.2), hy - S(1)), S(1))
        pygame.draw.circle(s, (255, 255, 0), (hx + S(1.8), hy - S(1)), S(1))
        pygame.draw.circle(s, (255, 255, 255), (hx - S(1.2), hy - S(1.2)), max(1, S(0.4)))
        pygame.draw.circle(s, (255, 255, 255), (hx + S(1.8), hy - S(1.2)), max(1, S(0.4)))
        # Belly scales
        for i in range(3):
            pygame.draw.arc(s, (255, 215, 0, 180), (cx - S(3) + S(i * 2), cy + S(1.5), S(3), S(3)), 3.14, 6.28, max(1, S(0.8)))
        if frame == "attack":
            # Fire breath particles!
            for i in range(6):
                fx = hx + S(5) + S(i * 2.2)
                fr = S(3.5) - S(i) // 2
                fa = max(0, 240 - i * 38)
                pygame.draw.circle(s, (255, max(0, 220 - i * 40), 0, fa), (fx, hy + S(1)), max(1, fr))
            pygame.draw.circle(s, (255, 255, 255, 240), (hx + S(5), hy + S(1)), S(2))
        pets[f"dragon_{frame}"] = pygame.transform.smoothscale(s, (out, out))

    # ── HEALER (fairy) ──
    for frame in ("idle", "attack"):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        cx, cy = R // 2, R // 2
        # Radiant healing halo aura
        pygame.draw.circle(s, (255, 120, 180, 45), (cx, cy), S(12))
        pygame.draw.circle(s, (255, 180, 220, 30), (cx, cy), S(9))
        
        # ── Double layered butterfly wings ──
        for side in (-1, 1):
            wx = cx + side * S(5)
            # Translucent gradient butterfly wings (Shifting pink-blue-cyan)
            pts = [(cx + side * S(2), cy - S(3)), (wx, cy - S(8.5)), (wx + side * S(3.5), cy - S(3.5)),
                   (wx, cy + S(2)), (cx + side * S(2), cy)]
            pygame.draw.polygon(s, (255, 100, 180, 150), pts)
            pygame.draw.polygon(s, (0, 240, 255, 120), pts, max(1, S(0.8)))
            # Inner wing cell highlight
            pygame.draw.polygon(s, (255, 255, 255, 120), [(cx + side * S(2.5), cy - S(3.5)), (wx - side * S(1), cy - S(6.5)), (wx + side * S(1.5), cy - S(4))])

        # Body (dress with gradient)
        pygame.draw.polygon(s, (255, 130, 180), [(cx - S(3), cy - S(2)), (cx + S(3), cy - S(2)), (cx + S(5.5), cy + S(5)), (cx - S(5.5), cy + S(5))])
        pygame.draw.polygon(s, (255, 200, 230), [(cx - S(2), cy - S(2)), (cx + S(2), cy - S(2)), (cx + S(4.5), cy + S(4.5)), (cx - S(4.5), cy + S(4.5))])
        # Head
        pygame.draw.circle(s, (255, 210, 190), (cx, cy - S(5.5)), S(4))
        pygame.draw.circle(s, (255, 225, 210), (cx, cy - S(5.5)), S(3))
        # Hair
        pygame.draw.arc(s, (255, 180, 100), (cx - S(5), cy - S(10.5), S(10), S(8)), 0, 3.14, S(1))
        pygame.draw.circle(s, (255, 180, 100), (cx - S(4), cy - S(5.5)), S(1.2))
        pygame.draw.circle(s, (255, 180, 100), (cx + S(4), cy - S(5.5)), S(1.2))
        # Golden crown
        pygame.draw.polygon(s, (255, 215, 0), [(cx - S(2.5), cy - S(8.5)), (cx, cy - S(11.5)), (cx + S(2.5), cy - S(8.5))])
        pygame.draw.circle(s, (255, 50, 120), (cx, cy - S(11.5)), max(1, S(0.8)))
        # Cute sparkling eyes
        pygame.draw.circle(s, (100, 30, 140), (cx - S(1.2), cy - S(5.5)), max(1, S(1)))
        pygame.draw.circle(s, (100, 30, 140), (cx + S(1.2), cy - S(5.5)), max(1, S(1)))
        pygame.draw.circle(s, (255, 255, 255), (cx - S(1.2), cy - S(5.5)), max(1, S(0.4)))
        pygame.draw.circle(s, (255, 255, 255), (cx + S(1.2), cy - S(5.5)), max(1, S(0.4)))
        # Mouth (smile)
        pygame.draw.arc(s, (255, 80, 100), (cx - S(1), cy - S(4.5), S(2), S(2)), 3.14, 6.28, max(1, S(0.5)))
        # Magic wand
        pygame.draw.line(s, (255, 215, 0), (cx + S(4), cy - S(2)), (cx + S(7.5), cy + S(4.5)), max(1, S(0.8)))
        pygame.draw.circle(s, (255, 255, 150), (cx + S(7.5), cy + S(4.5)), S(1.8))
        if frame == "attack":
            # Healing sparkles
            for i in range(6):
                angle = i * 60
                rad = math.radians(angle)
                sx = cx + math.cos(rad) * S(8.5)
                sy = cy + math.sin(rad) * S(8.5)
                pygame.draw.circle(s, (255, 255, 180, 240), (int(sx), int(sy)), max(1, S(0.8)))
            # Healing cross symbol
            pygame.draw.rect(s, (50, 255, 150, 230), (cx + S(5), cy - S(8), S(4), S(1.2)))
            pygame.draw.rect(s, (50, 255, 150, 230), (cx + S(6.4), cy - S(9.4), S(1.2), S(4)))
        pets[f"healer_{frame}"] = pygame.transform.smoothscale(s, (out, out))

    # ── SHIELD BOT (robot) ──
    for frame in ("idle", "attack"):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        cx, cy = R // 2, R // 2
        # Body (detailed cyber steel plates)
        pygame.draw.rect(s, (45, 60, 95), (cx - S(6), cy - S(4), S(12), S(10)), border_radius=S(2.2))
        pygame.draw.rect(s, (70, 95, 145), (cx - S(5), cy - S(3), S(10), S(8)), border_radius=S(1.2))
        # Specular glint on bot corners
        pygame.draw.rect(s, (255, 255, 255, 45), (cx - S(5), cy - S(3), S(10), S(8)), 1, border_radius=S(1.2))
        # Chest plate
        pygame.draw.rect(s, (90, 130, 195), (cx - S(3.5), cy - S(1), S(7), S(4)), border_radius=S(1))
        # Head (cyber visor look)
        pygame.draw.rect(s, (55, 75, 115), (cx - S(4.5), cy - S(8), S(9), S(5)), border_radius=S(1))
        pygame.draw.rect(s, (80, 110, 160), (cx - S(3.5), cy - S(7.2), S(7), S(3.5)), border_radius=S(1))
        # Glowing LED visor eyes
        pygame.draw.line(s, (0, 240, 255), (cx - S(2.5), cy - S(6.2)), (cx + S(2.5), cy - S(6.2)), max(1, S(1)))
        pygame.draw.circle(s, (255, 255, 255), (cx - S(1.5), cy - S(6.2)), max(1, S(0.5)))
        pygame.draw.circle(s, (255, 255, 255), (cx + S(1.5), cy - S(6.2)), max(1, S(0.5)))
        # Antenna
        pygame.draw.line(s, (90, 115, 160), (cx, cy - S(8)), (cx, cy - S(11.5)), max(1, S(0.6)))
        pygame.draw.circle(s, (0, 255, 120), (cx, cy - S(11.5)), max(1, S(1.2)))
        # Arms
        pygame.draw.rect(s, (50, 70, 110), (cx - S(8.2), cy - S(2), S(3), S(6.5)), border_radius=S(1))
        pygame.draw.rect(s, (50, 70, 110), (cx + S(5.2), cy - S(2), S(3), S(6.5)), border_radius=S(1))
        # Legs
        pygame.draw.rect(s, (40, 60, 95), (cx - S(4), cy + S(5.2), S(3), S(4.5)), border_radius=S(1))
        pygame.draw.rect(s, (40, 60, 95), (cx + S(1), cy + S(5.2), S(3), S(4.5)), border_radius=S(1))
        if frame == "attack":
            # Elegant glowing cyber grid shield projection
            pygame.draw.circle(s, (0, 240, 255, 45), (cx, cy), S(12.5))
            pygame.draw.circle(s, (0, 240, 255), (cx, cy), S(12.5), max(1, S(0.8)))
            # Grid mesh rings
            pygame.draw.circle(s, (150, 230, 255, 100), (cx, cy), S(10.5), max(1, S(0.5)))
            # Chest reactor core glowing
            pygame.draw.circle(s, (0, 240, 255, 220), (cx, cy + S(1)), S(1.8))
        pets[f"shield_bot_{frame}"] = pygame.transform.smoothscale(s, (out, out))

    # ── MAGNET ──
    for frame in ("idle", "attack"):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        cx, cy = R // 2, R // 2
        # Glow
        pygame.draw.circle(s, (255, 215, 0, 45), (cx, cy), S(11.5))
        # Polished metallic U-shape body
        pygame.draw.arc(s, (190, 30, 30), (cx - S(6.2), cy - S(4), S(12.4), S(12)), 3.14, 6.28, S(3))
        # Red tip left
        pygame.draw.rect(s, (220, 30, 30), (cx - S(7.2), cy - S(4.2), S(4), S(5.2)), border_radius=S(1))
        pygame.draw.rect(s, (255, 100, 100), (cx - S(6.2), cy - S(3.2), S(2), S(3.2)), border_radius=S(1))
        # Blue tip right
        pygame.draw.rect(s, (30, 50, 190), (cx + S(3.2), cy - S(4.2), S(4), S(5.2)), border_radius=S(1))
        pygame.draw.rect(s, (100, 140, 255), (cx + S(4.2), cy - S(3.2), S(2), S(3.2)), border_radius=S(1))
        # Center silver core band
        pygame.draw.arc(s, (170, 175, 185), (cx - S(5.2), cy - S(3), S(10.4), S(10)), 3.14, 6.28, S(2))
        # Glowing cute eyes
        pygame.draw.circle(s, (255, 255, 255), (cx - S(2.2), cy + S(1)), S(1.2))
        pygame.draw.circle(s, (30, 30, 35), (cx - S(2.2), cy + S(1)), max(1, S(0.6)))
        pygame.draw.circle(s, (255, 255, 255), (cx + S(2.2), cy + S(1)), S(1.2))
        pygame.draw.circle(s, (30, 30, 35), (cx + S(2.2), cy + S(1)), max(1, S(0.6)))
        # Smile
        pygame.draw.arc(s, (50, 50, 50), (cx - S(1), cy + S(1), S(2), S(2)), 3.14, 6.28, max(1, S(0.5)))
        if frame == "attack":
            # Magnetic field plasma lines
            for i in range(4):
                r = S(8) + S(i * 2.2)
                a = max(0, 195 - i * 40)
                pygame.draw.circle(s, (255, 215, 0, a), (cx, cy), r, max(1, S(0.6)))
            # Sparkles being attracted
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                sx = cx + math.cos(rad) * S(9.5)
                sy = cy + math.sin(rad) * S(9.5)
                pygame.draw.circle(s, (255, 255, 200, 240), (int(sx), int(sy)), max(1, S(0.8)))
        pets[f"magnet_{frame}"] = pygame.transform.smoothscale(s, (out, out))

    # ── GHOST ──
    for frame in ("idle", "attack"):
        s = pygame.Surface((R, R), pygame.SRCALPHA)
        cx, cy = R // 2, R // 2
        # Ghost body (translucent, wavy bottom)
        pygame.draw.ellipse(s, (180, 210, 255, 120), (cx - S(7), cy - S(7), S(14), S(12)))
        pygame.draw.ellipse(s, (200, 230, 255, 80), (cx - S(6), cy - S(6), S(12), S(10)))
        # Wavy bottom
        wave_pts = [(cx - S(7), cy + S(3))]
        for i in range(7):
            wx = cx - S(7) + S(i * 2)
            wy = cy + S(5) + (S(2) if i % 2 == 0 else 0)
            wave_pts.append((wx, wy))
        wave_pts.append((cx + S(7), cy + S(3)))
        pygame.draw.polygon(s, (180, 210, 255, 120), wave_pts)
        # Inner glow
        pygame.draw.circle(s, (220, 240, 255, 60), (cx, cy - S(1)), S(5))
        # Eyes (big, cute)
        pygame.draw.circle(s, (40, 40, 80), (cx - S(3), cy - S(3)), S(2))
        pygame.draw.circle(s, (40, 40, 80), (cx + S(3), cy - S(3)), S(2))
        pygame.draw.circle(s, (200, 220, 255), (cx - S(3), cy - S(3)), S(1))
        pygame.draw.circle(s, (200, 220, 255), (cx + S(3), cy - S(3)), S(1))
        # Mouth (O shape)
        pygame.draw.circle(s, (100, 120, 180, 150), (cx, cy), S(1))
        # Blush
        pygame.draw.circle(s, (255, 180, 200, 80), (cx - S(5), cy - S(1)), S(1))
        pygame.draw.circle(s, (255, 180, 200, 80), (cx + S(5), cy - S(1)), S(1))
        if frame == "attack":
            # Ice/freeze rays
            for i in range(6):
                angle = i * 60
                rad = math.radians(angle)
                ex = cx + math.cos(rad) * S(9)
                ey = cy + math.sin(rad) * S(9)
                pygame.draw.line(s, (120, 200, 255, 200), (cx, cy), (int(ex), int(ey)), max(1, S(1) // 2))
                pygame.draw.circle(s, (180, 230, 255, 200), (int(ex), int(ey)), max(1, S(1)))
            # Snowflake at center
            pygame.draw.circle(s, (200, 240, 255, 180), (cx, cy - S(1)), S(2))
        pets[f"ghost_{frame}"] = pygame.transform.smoothscale(s, (out, out))

    return pets


# ═══════════════════════════════════════════════
#  SPRITE CACHE
# ═══════════════════════════════════════════════

class SpriteCache:
    def __init__(self):
        print(f"Loading ULTRA PREMIUM sprites v3.0 (20x supersampled, _R={_R})...")

        # Tiles (default style)
        self._brick_default = make_brick_tile_ultra()
        self._steel_default = make_steel_tile_ultra()
        self._grass_default = make_grass_tile_ultra()
        self.brick = self._brick_default
        self.steel = self._steel_default
        self.grass = self._grass_default
        self.crate = make_crate_tile_ultra()
        self.base = make_base_tile_ultra()
        self.water_frames = [make_water_tile_ultra(i) for i in range(12)]

        # Theme-specific tile overrides
        self.brick_themes = {"kawaii_woodland": make_brick_tile_kawaii()}
        self.steel_themes = {"kawaii_woodland": make_steel_tile_kawaii()}
        self.grass_themes = {"kawaii_woodland": make_grass_tile_kawaii()}

        # Floor themes
        self.floors = {}
        for theme in ["default", "desert", "snow", "city", "jungle", "lava",
                      "kawaii_woodland"]:
            self.floors[theme] = make_floor_tile_ultra(theme)
        self.floor = self.floors["default"]

        # Tanks (including boss)
        self.tanks = {k: [make_tank_surface_ultra(k, d) for d in range(4)] for k in TANK_COLORS}

        # Boss sprites — 4 unique bosses rendered at 1280x1280
        self.boss_tanks = {k: [make_boss_surface(k, d) for d in range(4)] for k in BOSS_COLORS}

        # Player tier sprites (5 tiers x 4 directions)
        self.player_tiers = [[make_player_tier_surface(t, d) for d in range(4)]
                             for t in range(len(PLAYER_TIER_COLORS))]
        self.player_tiers_highres = [[make_player_tier_surface(t, d, target_size=256) for d in range(4)]
                                     for t in range(len(PLAYER_TIER_COLORS))]

        # Bullets
        self.bullet = make_bullet()
        self.bullet_enemy = make_bullet((255, 100, 100))
        self.bullet_pierce = make_bullet_advanced("pierce")
        self.bullet_bomb = make_bullet_advanced("bomb")
        self.bullet_laser = make_bullet_advanced("laser")
        self.bullet_plasma = make_bullet_advanced("plasma")
        self.bullet_rocket = make_bullet_advanced("rocket")
        self.bullet_flame = make_bullet_advanced("flame")

        # Pets
        self.pets = make_pet_sprites()

        # Effects
        self.explosion = make_explosion_ultra()
        self.muzzle_flash = make_muzzle_flash_ultra()
        self.spawn_effect = make_spawn_effect_ultra()

        # Items
        all_items = ["health", "shield", "speed", "star", "money", "life",
                     "rapid", "multi", "pierce", "bomb", "laser", "plasma",
                     "freeze", "max_power", "grenade", "gem", "rocket", "flame"]
        self.items = {k: make_item_surface(k) for k in all_items}

        # Try to override a few items with pixel art sliced from the
        # reference asset image.
        pixel_art = try_load_pixel_art_items()
        if pixel_art:
            print(f"Loaded {len(pixel_art)} pixel-art item(s) from asset image: "
                  f"{sorted(pixel_art.keys())}")
            self.items.update(pixel_art)

        # Score popups
        self.score_popups = make_score_popup_font()

        # Entities
        self.chicken_frames = make_chicken_frames_ultra()
        self.dog_frames = make_dog_frames_ultra()

        # Weather
        self.rain_drop = make_rain_drop()
        self.snow_flake = make_snow_flake()
        self.sand_particle = make_sand_particle()

        # Minimap icons
        self.minimap_player = make_minimap_player_icon()
        self.minimap_enemy = make_minimap_enemy_icon()
        self.minimap_base = make_minimap_base_icon()

        print("Sprites loaded successfully!")

    def set_floor_theme(self, theme):
        if theme in self.floors:
            self.floor = self.floors[theme]
        self.brick = self.brick_themes.get(theme, self._brick_default)
        self.steel = self.steel_themes.get(theme, self._steel_default)
        self.grass = self.grass_themes.get(theme, self._grass_default)
