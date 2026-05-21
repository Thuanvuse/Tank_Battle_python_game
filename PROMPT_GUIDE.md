# PROMPT_GUIDE.md — Hướng dẫn tạo ảnh & video cho Tank Battle

File này gom tất cả prompt + spec để bạn (hoặc nhóm tạo asset) sản xuất hình ảnh và video bổ sung cho game.

---

## A. CÁCH TÍCH HỢP

### Ảnh tĩnh (preview map, nút PNG…)
- Đặt file vào `assets/<tên_file>.png` (transparent background nếu là nút/icon)
- Tôi sẽ wire vào code theo từng vị trí cụ thể

### Video động (background sảnh, splash, garage…)
1. Đặt file MP4 vào `assets/<tên>.mp4`
2. Trích frames bằng FFmpeg ở **đúng FPS gốc của video** (không upscale, không interpolate):
   ```bash
   ffmpeg -i assets/your_video.mp4 -vf "fps=24" -q:v 8 assets/your_anim/f_%03d.jpg
   ```
3. Game sẽ tự load tất cả ảnh trong `assets/<your_anim>/` và phát loop
4. Spec chuẩn: **1280×720, 24fps, 8–15 giây, loop seamless, không có chữ tiếng Việt**

---

## B. PROMPT TẠO UI SẢNH GAME (lobby)

Theo phong cách neon arcade kiểu game mobile cao cấp (giống ảnh tham khảo bạn gửi):

### Prompt chính (Midjourney / DALL-E / Leonardo / Stable Diffusion XL)

```
Top-down hero shot of a futuristic battle tank command lobby UI for a mobile game,
1280x720 cinematic widescreen, central tactical command center room with a giant
glowing 3D planet hologram in the middle, holographic radar grid floor, neon cyan
and magenta lighting, animated electric particles drifting upward, sci-fi tech
panels lining the bottom edge with HUD bars, glowing power crystals on the sides,
satellites orbiting around the planet, depth-of-field background, dark navy and
purple ambient tones, ultra-detailed glass surfaces and panel reflections,
4-direction lighting, AAA mobile game art style — clean negative space on the
LEFT side for vertical menu buttons (do NOT draw any buttons or text in the image,
leave that area as empty wall/floor), camera elevated slightly, no characters,
no logos, no watermarks, no text, ratio 16:9, ultra high detail, vibrant colors,
volumetric lighting, ray-traced reflections, render in Octane.
--ar 16:9 --quality 2 --stylize 250
```

### Prompt phụ — biến thể "Mặt trận / chiến địa"
```
Heroic command bunker viewed from front, futuristic war operations room interior
1280x720, multiple holographic screens floating, mission briefing displays, dark
metal walls with neon orange and cyan accent strips, war room atmosphere, red
warning lights pulsing on the perimeter, central holographic earth slowly spinning,
empty floor area on left where buttons will be overlaid, no UI text in image,
realistic 3D rendered look, cinematic 4K quality.
```

### Prompt phụ — biến thể "Hangar tank"
```
Wide-angle interior of a futuristic tank hangar, 5 battle tanks lined up in
spotlights, neon ground markings, technicians silhouettes in the background,
holographic stats floating above each tank, cyan and gold accent lighting,
dust particles in the air shafts, industrial sci-fi vibe, 16:9 1280x720,
clean empty area at left for menu buttons, no text or labels, photorealistic 3D.
```

### Hậu kỳ
- Đổi file thành animated MP4 bằng AI-to-video (Runway Gen-3, Kling AI, Pika 1.5)
- Hoặc dùng tool After Effects → Animate camera nhẹ, particles drifting, lights pulsing
- Loop seamless 8–12 giây

---

## C. PROMPT MAP PREVIEW (7 theme bản đồ)

Sử dụng để tạo ảnh preview hiển thị ở panel "DEMO BẢN ĐỒ" trong màn level_select.

**Spec chung:** 400×260 PNG, top-down view (camera bird's eye), tile-based map, đặt vào `assets/map_previews/<theme>.png`

### 1. `kawaii_woodland.png`
```
Top-down view of a cute kawaii forest battlefield, soft pastel green grass tiles,
pink cherry blossom trees scattered around, mushroom houses, small wooden bridge
over a stream, fluffy clouds, sunshine, 400x260 pixel art style, no characters,
no text, soft pastel colors, isometric perspective slightly tilted, looks like
Animal Crossing meets tank game, vibrant but soft palette.
```

### 2. `default.png`
```
Top-down view of a classic green grassland battlefield with brick walls forming
a maze, steel walls in corners, bushes scattered, blue water river running
horizontally, 400x260 retro arcade style, Battle City Tank 1990 aesthetic but
modernized, no characters or tanks visible, no text, vibrant green and red tones.
```

### 3. `desert.png`
```
Top-down view of a sandy desert battlefield with golden sand tiles, rocky walls,
cactus plants, ancient ruins of stone columns, dried-up cracked earth, sandstorm
particles in the corners, 400x260 game asset style, warm orange and tan palette,
no characters, no text.
```

### 4. `snow.png`
```
Top-down view of a snowy frozen battlefield, icy blue and white snow tiles,
ice block walls, frozen lake in the center, pine trees with snow caps, snowflakes
falling, aurora borealis in the corner sky, 400x260 game art style, cool blue
and white palette, no characters, no text, magical atmosphere.
```

### 5. `city.png`
```
Top-down view of a destroyed cyberpunk city block battlefield, gray concrete
tiles, ruined skyscrapers, neon billboards still flickering, abandoned cars,
broken glass on the streets, smoke rising, 400x260 game art style, gritty urban
warfare aesthetic, dark tones with neon highlights, no characters, no text.
```

### 6. `jungle.png`
```
Top-down view of a dense tropical jungle battlefield, deep green foliage tiles,
ancient temple stone walls overgrown with vines, banana plants, a crashed
helicopter wreck, muddy paths, river crossing, 400x260 game art style, lush
saturated green palette, Vietnam war vibe, no characters, no text.
```

### 7. `lava.png`
```
Top-down view of a volcanic hell battlefield, glowing orange lava rivers, dark
basalt rock walls, cracked obsidian floor tiles, fire geysers, ember particles
floating up, dramatic red-orange lighting from below, 400x260 game art style,
intense hot color palette, no characters, no text, looks like Hades game level.
```

---

## D. VIDEO BACKGROUND CHO CÁC SẢNH KHÁC

Hiện game đã có 2 video: `assets/title_anim/` (sảnh chính) và `assets/login_anim/` (splash).

Đây là prompt cho các sảnh còn lại — gửi cho Runway/Kling/Pika/Sora để tạo MP4.

### D1. Garage (Sảnh Ga-ra)
**Spec:** 1280×720, 24fps, 10s loop, MP4
```
Cinematic 10-second loop of a futuristic tank garage interior, single tank
on a rotating circular platform in the center under cone spotlights,
diagnostic holograms floating around the tank (stats, weapons icons),
mechanic robots working in the background, blue and orange accent lighting,
slow camera orbit around the tank, sparks flying occasionally, neon ground
markings, ultra detailed 3D AAA mobile game art style, no characters faces,
no text, seamless loop, deep navy ambient.
```

### D2. Co-op Lobby (Sảnh Co-op)
**Spec:** 1280×720, 24fps, 10s loop, MP4
```
Cinematic 10-second loop of a futuristic squad assembly room, 4 tanks
parked in a fan formation under spotlights, holographic squad roster
projected on the far wall (no text visible, just shapes), team color flags
hanging (red, blue, yellow, green), industrial sci-fi corridor in the
background, slow pan from left to right, particle effects, ambient blue
lighting, looped, no characters, no text, AAA quality.
```

### D3. PVP Versus screen
**Spec:** 1280×720, 24fps, 8s loop, MP4
```
Dramatic versus screen background — two opposing tank armies facing each
other across a battlefield, glowing red on left side, glowing blue on
right side, electric sparks crackling between them in the center,
zoom-in slow motion, dust and embers floating, dark gray sky with
lightning, cinematic 8-second loop, no text, no character faces,
intense rivalry atmosphere, anime/manga inspired energy waves.
```

### D4. Shop (Sảnh cửa hàng)
**Spec:** 1280×720, 24fps, 10s loop, MP4
```
Cinematic 10-second loop of a futuristic weapons shop interior,
display cases lining the walls showing various weapons (turrets, missiles,
armor) under spotlights, holographic price tags floating, gold coins
swirling in the air, neon "SHOP" sign glowing softly, warm golden ambient
lighting, slow camera dolly forward through the center aisle, no characters,
no readable text, AAA mobile game art quality, seamless loop.
```

### D5. Level Select (nếu muốn thay nền galaxy hiện tại)
**Spec:** 1280×720, 24fps, 12s loop, MP4
```
Cinematic 12-second loop of a tactical world map hologram view, glowing
network of 20 nodes connected by neon cyan lines floating in a dark space
environment, distant nebulae and stars in the background, slow camera
orbit, occasional data pulses traveling along the connection lines,
some nodes glow bright (unlocked), others remain dim (locked), no text,
no UI, just the floating tactical map, sci-fi command center vibe.
```

---

## E. PROMPT NÚT PNG TRONG SUỐT (transparent)

Nếu muốn thay nút baked-in của lobby bằng nút PNG riêng để khớp pixel-perfect:

**Spec mỗi nút:** PNG with alpha, kích thước ~290×70px, đặt vào `assets/buttons/<tên>.png`

### Template prompt
```
Single futuristic neon arcade button shape for a mobile game UI, 290x70px
horizontal pill/rectangle, [COLOR] gradient background with [TEXT] label in
bold uppercase Vietnamese font, glowing edge, glass reflection on top, drop
shadow at the bottom, [ACCENT_COLOR] inner border, isolated on TRANSPARENT
background, no extra elements, button only.
```

Cụ thể:
| File | [COLOR] | [TEXT] | [ACCENT_COLOR] |
|---|---|---|---|
| `chien_dau.png` | red-orange | CHIẾN ĐẤU | gold |
| `shop.png` | gold-yellow | SHOP | orange |
| `garage.png` | steel-blue | GA-RA | cyan |
| `pvp.png` | purple-pink | PVP | magenta |
| `coop.png` | green-mint | CO-OP | lime |
| `vong_quay.png` | rainbow | VÒNG QUAY | gold |
| `gear.png` | (gear icon only, no text) silver-blue | — | cyan |

---

## F. TOOLS ĐỀ XUẤT

### Tạo ảnh tĩnh
- **Midjourney v6+** — chất lượng AAA cao nhất, có discord bot
- **DALL-E 3** (qua ChatGPT Plus) — tốt cho prompt phức tạp
- **Leonardo.ai** — free tier, có model "Phoenix" rất phù hợp game art
- **Stable Diffusion XL** + Comfy UI — chạy local, nhiều control net

### Tạo video động (AI-to-video)
- **Runway Gen-3 Alpha** — top tier, $15-$76/tháng
- **Kling AI 1.5** — free đến 6 video/ngày, chất lượng tốt
- **Pika 1.5** — tốt cho looping động
- **Sora** (OpenAI) — đỉnh nhất, beta limited access
- **Hailuo (MiniMax)** — free, chất lượng ổn
- **LumaLabs Dream Machine** — text-to-video chất lượng cao

### Edit hậu kỳ
- **DaVinci Resolve** (free) — cắt, ghép, color grade
- **After Effects** — animation, particles, motion graphics
- **HandBrake** — nén MP4

---

## G. CHECKLIST KHI GỬI ASSET CHO TÔI

Trước khi gửi file, kiểm tra:
- [ ] File có đúng định dạng (PNG cho ảnh, MP4 cho video)?
- [ ] Kích thước đúng (1280×720 cho background, 400×260 cho preview)?
- [ ] Video có loop seamless không (frame đầu = frame cuối)?
- [ ] Không có chữ tiếng Việt trong asset?
- [ ] Không có watermark / logo AI tool?
- [ ] File size hợp lý (<10MB cho video 10s, <2MB cho ảnh)?

---

## H. MẸO ĐỂ KẾT QUẢ ĐẸP HƠN

1. **Không thêm chữ vào trong asset** — game đã có text tiếng Việt riêng. Thêm chữ trong ảnh AI sẽ:
   - Méo khi scale
   - Đè lên text game
   - Bị Vietnamese diacritic lỗi
2. **Giữ negative space cho UI** — vùng trái/phải để game vẽ button đè lên
3. **Loop seamless** — frame đầu phải gần giống frame cuối. Có 3 cách:
   - Render scene tuần hoàn (clock circling, planet rotating 360°)
   - Crossfade 1s đầu vào 1s cuối trong After Effects
   - Dùng prompt `seamless loop` + `cinemagraph style`
4. **Tránh camera quá lắc** — chỉ pan/zoom nhẹ. Quá lắc gây mệt mắt
5. **Color grade consistent** — toàn bộ các sảnh nên cùng tông (cyan + purple chính là tông hiện tại)
6. **Render ratio chuẩn 16:9** — đừng để 4:3 hay 1:1, sẽ bị crop méo

---

## I. CÁCH BÁO TÔI

Khi bạn có asset mới, chỉ cần:
1. Kéo thả file vào chat
2. Ghi rõ "đây là cho sảnh X" (vd. "đây là video cho garage" hoặc "đây là preview cho map snow")
3. Tôi sẽ tự đặt vào đúng vị trí + wire vào code + test rồi gửi zip mới

Nếu file nhiều, có thể zip lại và đặt tên thư mục theo loại:
- `lobby_assets.zip` chứa background + buttons
- `map_previews.zip` chứa 7 ảnh preview
- `screen_videos.zip` chứa các video sảnh khác
