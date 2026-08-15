from PIL import Image
import os

# V8 = Pendulum Color Version 3 Nightmare Soldiers
SRC = r"c:/Users/roy/CodeBuddy/Digital-MonsterVpet/Digital-MonsterVpet/sprites/V8/V8.png"
OUT_DIR = r"c:/Users/roy/CodeBuddy/Digital-MonsterVpet/Digital-MonsterVpet/sprites/V8"
os.makedirs(OUT_DIR, exist_ok=True)

img = Image.open(SRC).convert("RGBA")
pix = img.load()
w, h = img.size
print(f"V8 原圖尺寸: {w} x {h}, mode={img.mode}")

# 1) 找出所有完全同色的列/行（洋紅色分隔線）
sep_rows = [y for y in range(h) if len({pix[x, y] for x in range(w)}) <= 1]
sep_cols = [x for x in range(w) if len({pix[x, y] for y in range(h)}) <= 1]

# 2) 找出所有 16px tile 起始位置
def get_starts(sep_list):
    out = []
    for a, b in zip(sep_list, sep_list[1:]):
        if b - a - 1 == 16:
            out.append(a + 1)
    return out

all_col_starts = get_starts(sep_cols)
all_row_starts = get_starts(sep_rows)

# 3) 自動選取最大的連續網格
def find_largest_grid(col_starts, row_starts):
    best_cols = []
    best_rows = []
    for i, cs in enumerate(col_starts):
        group = [cs]
        for j in range(i+1, len(col_starts)):
            if col_starts[j] - group[-1] == 17:
                group.append(col_starts[j])
            elif col_starts[j] - group[-1] > 17:
                break
        if len(group) > len(best_cols):
            best_cols = group[:]
    for i, rs in enumerate(row_starts):
        group = [rs]
        for j in range(i+1, len(row_starts)):
            if row_starts[j] - group[-1] == 17:
                group.append(row_starts[j])
            elif row_starts[j] - group[-1] > 17:
                break
        if len(group) > len(best_rows):
            best_rows = group[:]
    return best_cols, best_rows

COL_STARTS, ROW_STARTS = find_largest_grid(all_col_starts, all_row_starts)

num_rows = len(ROW_STARTS)
num_cols = len(COL_STARTS)
print(f"檢測到主網格: {num_rows} 行 x {num_cols} 列 = {num_rows * num_cols} tile")
print(f"列起點: {COL_STARTS}")
print(f"行起點（前 5 + 後 3）: {ROW_STARTS[:5]} ... {ROW_STARTS[-3:]}")

if num_rows == 0 or num_cols == 0:
    print("錯誤：無法找到有效的 tile 網格！")
    exit(1)

# 4) 去底（洋紅色 / 白底）
MAGENTA = (255, 0, 255)
def clean(tile):
    p = tile.load()
    for y in range(16):
        for x in range(16):
            r, g, b, a = p[x, y]
            if (r, g, b) == MAGENTA or (a > 0 and (r, g, b) == (255, 255, 255)):
                p[x, y] = (0, 0, 0, 0)
    return tile

# 5) 擷取所有 tile
all_tiles = []
for rs in ROW_STARTS:
    row = []
    for cs in COL_STARTS:
        t = img.crop((cs, rs, cs + 16, rs + 16)).convert("RGBA")
        row.append(clean(t))
    all_tiles.append(row)

# 6) 提取 egg（通常在第 0 行第 0 列）
if len(all_tiles) > 0 and len(all_tiles[0]) > 0:
    egg_tile = all_tiles[0][0]
    egg_pix = egg_tile.load()
    has_content = any(egg_pix[x, y][3] > 0 for y in range(16) for x in range(16))
    if has_content:
        egg_tile.save(os.path.join(OUT_DIR, "V8_egg.png"))
        print("[V8_egg.png] 已保存")

# 7) 每行存一張 V8_XX.png（00-31）
GAP = 1
for r in range(num_rows):
    row_tiles = all_tiles[r]
    rw = num_cols * 16 + (num_cols - 1) * GAP
    ri = Image.new("RGBA", (rw, 16), (0, 0, 0, 0))
    for c, t in enumerate(row_tiles):
        ri.paste(t, (c * (16 + GAP), 0), t)
    fname = os.path.join(OUT_DIR, f"V8_{r:02d}.png")
    ri.save(fname)
    print(f"[V8_{r:02d}.png] {num_cols} 幀已保存")

# 8) 拼成完整網格圖（預覽）
gw = num_cols * 16 + (num_cols - 1) * GAP
gh = num_rows * 16 + (num_rows - 1) * GAP
grid = Image.new("RGBA", (gw, gh), (255, 0, 255, 255))
for r in range(num_rows):
    for c, t in enumerate(all_tiles[r]):
        grid.paste(t, (c * (16 + GAP), r * (16 + GAP)), t)
pg = grid.load()
for y in range(gh):
    for x in range(gw):
        if pg[x, y] == (255, 0, 255, 255):
            pg[x, y] = (0, 0, 0, 0)
grid.save(os.path.join(OUT_DIR, "all_grid.png"))
print(f"[all_grid.png] {gw}x{gh} 完整網格預覽")

print("完成！")