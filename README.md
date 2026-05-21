<p align="center">
  <img src="screenshots/main_menu.png" width="800" alt="Tank Dai Chien - Main Menu"/>
</p>

<h1 align="center">TANK DAI CHIEN - ULTIMATE EDITION v3.0</h1>

<p align="center">
  <b>Game xe tang arcade phong cach Battle City voi do hoa procedural, ban do theo chu de, boss fight, cua hang nang cap, che do PVP va AI tu dong choi!</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/Pygame-2.5+-green?logo=python&logoColor=white" alt="Pygame"/>
  <img src="https://img.shields.io/badge/License-All%20Rights%20Reserved-red" alt="License"/>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Platform"/>
</p>

---

## Gioi thieu

**Tank Dai Chien** la game ban xe tang 2D lay cam hung tu **Battle City** kinh dien, duoc xay dung hoan toan bang **Python + Pygame**. Diem dac biet cua game la **toan bo sprite (xe tang, gach, dan, vu no, item...)** deu duoc ve procedural tai runtime boi `sprites.py` - **khong can file anh nao** cho gameplay!

### Diem noi bat

- **9,600+ dong code** game logic + **2,200+ dong** sprite engine
- **Do hoa 20x supersampled** - moi sprite duoc render o do phan giai gap 20 lan roi thu nho lai, tao hieu ung anti-alias sac net
- **7 loai ban do** theo chu de: Kawaii Woodland, Default, Desert, Snow, City, Jungle, Lava
- **Boss fight** moi 5 man
- **He thong nang cap tank** 5 tier voi hieu ung visual khac nhau
- **AI Auto-play** voi 3 thuat toan: A*, BFS, DFS
- **Che do PVP** choi mang (LAN)
- **Cua hang & Ba lo** mua item su dung trong tran dau
- **Pet system** - thu cung di theo ho tro chien dau
- **Hieu ung thoi tiet** tuyet, cat, mua, than lua theo tung ban do

---

## Screenshot

### Menu chinh
<p align="center">
  <img src="screenshots/main_menu.png" width="700" alt="Main Menu - Giao dien chinh"/>
</p>
<p align="center"><i>Giao dien menu chinh voi background galaxy, hien thi tien va kim cuong</i></p>

### Chon man choi
<p align="center">
  <img src="screenshots/level_select.png" width="700" alt="Level Select - Chon man"/>
</p>
<p align="center"><i>Ban do chon man voi 100+ man choi duoc ket noi boi duong di</i></p>

### Gameplay - Chien dau
<p align="center">
  <img src="screenshots/gameplay.png" width="700" alt="Gameplay"/>
</p>
<p align="center"><i>Man choi voi dia hinh rung ram - gach, thep, co, nuoc va minimap goc phai</i></p>

<p align="center">
  <img src="screenshots/gameplay_combat.png" width="700" alt="Combat"/>
</p>
<p align="center"><i>Chien dau tieu diet xe tang dich, thu thap item va bao ve can cu</i></p>

### Tam dung & Menu
<p align="center">
  <img src="screenshots/pause_menu.png" width="700" alt="Pause Menu - Tam dung"/>
</p>
<p align="center"><i>Menu tam dung voi cac lua chon: Tiep tuc, Choi lai, Vao Shop, Ve Sanh, Thoat</i></p>

### Cua hang (Shop)
<p align="center">
  <img src="screenshots/shop.png" width="700" alt="Shop - Cua hang"/>
</p>
<p align="center"><i>Cua hang voi nhieu tab: Vu Khi, Phong Thu, Pet, Dac Biet, Gara Tank</i></p>

---

## Yeu cau he thong

| Yeu cau | Chi tiet |
|---------|----------|
| **Python** | 3.9 tro len |
| **Pygame** | >= 2.5.0 |
| **NumPy** | >= 1.24.0 (tuy chon, tang hieu nang) |
| **He dieu hanh** | Windows / Linux / macOS |
| **Man hinh** | Toi thieu 1280x720 |

---

## Cai dat & Chay game

### Cach 1: Chay truc tiep (tat ca he dieu hanh)

```bash
# Clone repo
git clone https://github.com/Thuanvuse/desktop-tutorial.git
cd desktop-tutorial

# Cai dat thu vien
pip install -r requirements.txt

# Chay game (fullscreen)
python tank_game.py

# Hoac chay o che do cua so (debug)
TANK_WINDOWED=1 python tank_game.py
```

### Cach 2: Dung file bat (Windows)

Nhan doi **`setup_and_run.bat`** - file se tu dong:
1. Kiem tra Python da cai chua
2. Cai pygame neu thieu
3. Khoi dong game

### Cach 3: Build thanh file .exe (Windows)

Nhan doi **`build_exe.bat`** de build thanh file `dist/TankBattle.exe` chay doc lap.

---

## Dieu khien

| Phim | Hanh dong |
|------|-----------|
| **WASD** / **Phim mui ten** | Di chuyen xe tang |
| **Space** | Ban |
| **Enter** | Xac nhan / Bat dau / Tiep tuc |
| **Esc** | Tam dung (trong game) / Quay lai |
| **F** | Bat/Tat che do AUTO (AI choi) |
| **G** | Chuyen thuat toan AUTO (A* / BFS / DFS) |
| **1 / 2 / 3** | Su dung item trong ba lo |
| **H** | Huong dan choi (tu menu chinh) |
| **F11** | Chuyen doi fullscreen / cua so |
| **Q / E** | Chuyen tab trong cua hang |
| **0-9** | Mua item (trong cua hang) |

---

## Tinh nang chi tiet

### Ban do theo chu de
Game co **7 loai ban do** xoay vong theo man choi:

| Ban do | Dac diem | Thoi tiet |
|--------|----------|-----------|
| Kawaii Woodland | Rung xinh xan phong cach kawaii | Hoa roi |
| Default | Phong cach co dien Battle City | Binh thuong |
| Desert | Sa mac nong bong | Bao cat |
| Snow | Tuyet trang bao phu | Tuyet roi |
| City | Thanh pho hien dai | Mua |
| Jungle | Rung ram nhiet doi | Mua nhiet doi |
| Lava | Nui lua nong chay | Than lua |

### He thong tier xe tang
Thu thap vu khi nang cap de tien hoa xe tang qua **5 tier**:

| Tier | Mau sac | Dac diem |
|------|---------|----------|
| 1 | Xanh la | Co ban |
| 2 | Vang | Tang toc do ban |
| 3 | Cam | Dan manh hon |
| 4 | Do cam | Dan xuyen thau |
| 5 | Chrome Premium | Suc manh toi da |

### Item trong game

| Item | Hieu ung |
|------|----------|
| Health | +1 HP |
| Life | Them 1 mang |
| Shield | +3 khien bao ve |
| Speed | Nap day nang luong |
| Rapid | Ban lien thanh |
| Multi | Ban 3 huong |
| Pierce | Dan xuyen tuong |
| Bomb | Dan no |
| Laser | Tia laser |
| Plasma | Dan plasma |
| Star | Bom xoa man hinh |
| Freeze | Dong bang tat ca dich 5 giay |
| Max Power | Nang cap tang toi da ngay lap tuc |
| Grenade | No vung rong (ban kinh 4 o) |

### Cua hang & Ba lo
- Mua item bang tien kiem duoc trong tran
- Ba lo 3 slot - nhan **1/2/3** de su dung
- 5 tab: **Vu Khi**, **Phong Thu**, **Pet**, **Dac Biet**, **Gara Tank**

### Che do PVP (Choi mang)
- Ket noi qua mang LAN
- Dau tank 1v1 voi nguoi choi khac
- He thong xep hang va tien thuong hang ngay

### AI Auto-play
Nhan **F** de bat che do AI tu dong choi, nhan **G** de chuyen thuat toan:
- **A*** - Tim duong toi uu
- **BFS** - Tim duong theo chieu rong
- **DFS** - Tim duong theo chieu sau

---

## Cau truc du an

```
desktop-tutorial/
├── tank_game.py          # Game chinh - vong lap, logic, state machine (9,600+ dong)
├── sprites.py            # Engine sprite procedural 20x supersampled (2,200+ dong)
├── requirements.txt      # Thu vien can thiet
├── save_data.json        # Du lieu luu tien do
├── nhacnen.mp3           # Nhac nen game
├── TACH.mp3              # Hieu ung am thanh
├── setup_and_run.bat     # Script cai dat & chay (Windows)
├── build_exe.bat         # Script build file .exe (Windows)
├── IMG/                  # Hinh anh giao dien
│   ├── br.jpg            # Background menu chinh
│   ├── pointer.png       # Con tro chuot tuy chinh
│   ├── chiendau.png      # Nut "Chien Dau"
│   ├── cuahang.png       # Nut "Cua Hang"
│   ├── gara.png          # Nut "Gara"
│   ├── choimang.png      # Nut "Choi Mang"
│   ├── nangcap.png       # Nut "Nang Cap"
│   ├── thanhtuu.png      # Nut "Thanh Tuu"
│   └── button.png        # Template nut bam
├── screenshots/          # Anh chup man hinh demo
│   ├── main_menu.png
│   ├── level_select.png
│   ├── level_start.png
│   ├── gameplay.png
│   ├── gameplay_combat.png
│   ├── pause_menu.png
│   └── shop.png
└── README.md
```

---

## Cong nghe su dung

- **Python 3** - Ngon ngu chinh
- **Pygame** - Framework game 2D
- **NumPy** (tuy chon) - Tang hieu nang tinh toan
- **Procedural Generation** - Toan bo sprite ve bang code, khong dung file anh
- **A*/BFS/DFS** - Thuat toan tim duong cho AI
- **Socket/Threading** - He thong mang cho PVP
- **JSON** - Luu tien do nguoi choi

---

## Tac gia

**Thuanvuse** - Du an hoc tap va giai tri

---

<p align="center">
  <img src="screenshots/gameplay.png" width="400" alt="Gameplay preview"/>
  <img src="screenshots/shop.png" width="400" alt="Shop preview"/>
</p>

<p align="center">
  <b>Chuc ban choi vui ve! Have fun playing!</b>
</p>
