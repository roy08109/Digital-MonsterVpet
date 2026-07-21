from PIL import Image
import os

SRC = r"c:/Users/roy/CodeBuddy/Digital MonsterVpet/522623.png"
OUT_DIR = r"c:/Users/roy/CodeBuddy/Digital MonsterVpet/sprites"
os.makedirs(OUT_DIR, exist_ok=True)

img = Image.open(SRC).convert("RGBA")
pix = img.load()
w, h = img.size

# 1) 找出所有完全同色的列/欄（洋紅色分隔線）
sep_rows = [y for y in range(h) if len({pix[x, y] for x in range(w)}) <= 1]
sep_cols = [x for x in range(w) if len({pix[x, y] for y in range(h)}) <= 1]

def get_starts(sep_list):
    out = []
    for a, b in zip(sep_list, sep_list[1:]):
        if b - a - 1 == 16:
            out.append(a + 1)
    return out

# 右半部正規精靈格 (12 欄 x 18 列)
COL_STARTS = [c for c in get_starts(sep_cols) if c >= 96]   # 12 個
ROW_STARTS = [r for r in get_starts(sep_rows) if r >= 44]   # 18 個

print("格: %d 列 x %d 行 = %d tile" % (len(ROW_STARTS), len(COL_STARTS), len(ROW_STARTS)*len(COL_STARTS)))

# 2) 去底
MAGENTA = (255, 0, 255)
def clean(tile):
    p = tile.load()
    for y in range(16):
        for x in range(16):
            r, g, b, a = p[x, y]
            if (r, g, b) == MAGENTA or (a > 0 and (r, g, b) == (255, 255, 255)):
                p[x, y] = (0, 0, 0, 0)
    return tile

# 3) 擷取所有 tile
all_tiles = []
for rs in ROW_STARTS:
    row = []
    for cs in COL_STARTS:
        t = img.crop((cs, rs, cs + 16, rs + 16)).convert("RGBA")
        row.append(clean(t))
    all_tiles.append(row)

# 4) 左上角單一格 (16x16)
all_tiles[0][0].save(os.path.join(OUT_DIR, "tile_topleft.png"))
print("[tile_topleft.png] 16x16 單格")

# 第一個真正的精靈格 (row=1, col=0)
all_tiles[1][0].save(os.path.join(OUT_DIR, "tile_botamon_idle.png"))
print("[tile_botamon_idle.png] 16x16 單格 (Botamon 待機)")

# 5) 拼成 18x12 完整表 (1px 洋紅分隔線)
GAP = 1
gw = 12 * 16 + 11 * GAP
gh = 18 * 16 + 17 * GAP
grid = Image.new("RGBA", (gw, gh), (255, 0, 255, 255))
for r, row in enumerate(all_tiles):
    for c, t in enumerate(row):
        grid.paste(t, (c * (16 + GAP), r * (16 + GAP)), t)
grid.save(os.path.join(OUT_DIR, "all_grid.png"))
print("[all_grid.png] %dx%d 18 列 x 12 行 (含洋紅分隔)" % (gw, gh))

# 6) 分隔線改透明版本
p = grid.load()
for y in range(gh):
    for x in range(gw):
        if p[x, y] == (255, 0, 255, 255):
            p[x, y] = (0, 0, 0, 0)
grid.save(os.path.join(OUT_DIR, "all_grid_transparent.png"))
print("[all_grid_transparent.png] 分隔線全透明版")

# 7) 每行存一張 (方便選用)
for r, row in enumerate(all_tiles):
    rw = 12 * 16 + 11 * GAP
    ri = Image.new("RGBA", (rw, 16), (0, 0, 0, 0))
    for c, t in enumerate(row):
        ri.paste(t, (c * (16 + GAP), 0), t)
    ri.save(os.path.join(OUT_DIR, "row_%02d.png" % r))

print("[+] 18 張 row_XX.png 已輸出")
print("完成！")
