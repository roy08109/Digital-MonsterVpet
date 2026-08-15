from PIL import Image
import os

SRC = r"c:/Users/roy/CodeBuddy/Digital-MonsterVpet/Digital-MonsterVpet/sprites/V8/V8.png"
OUT_DIR = r"c:/Users/roy/CodeBuddy/Digital-MonsterVpet/Digital-MonsterVpet/sprites/V8"
os.makedirs(OUT_DIR, exist_ok=True)

img = Image.open(SRC).convert("RGBA")
pix = img.load()
W, H = img.size
TILE = 16
STEP = TILE + 1  # 17
print(f"V8 原圖: {W}x{H}")

# 1) 找所有「整列/行同色」的分隔線位置
sep_rows = [y for y in range(H) if len({pix[x, y] for x in range(W)}) <= 1]
sep_cols = [x for x in range(W) if len({pix[x, y] for y in range(H)}) <= 1]

# 2) 找 positions 中最長的等 step 距離子序列（長度 ≥ min_len）
def longest_eq(positions, step=STEP, min_len=4):
    best = []
    for i, p in enumerate(positions):
        run = [p]
        for j in range(i + 1, len(positions)):
            if positions[j] - run[-1] == step:
                run.append(positions[j])
            elif positions[j] - run[-1] > step:
                break
        if len(run) >= min_len and len(run) > len(best):
            best = run[:]
    return best

# 行方向：用 dense_rows 而不是 sep_rows（避免標題/裝飾誤判）
dense_rows = []
y = 0
while y < H:
    if len({pix[x, y] for x in range(W)}) > 1:
        end = y
        while end < H and len({pix[x, end] for x in range(W)}) > 1:
            end += 1
        if end - y == TILE:
            dense_rows.append(y)
            y = end + 1
            continue
    y += 1

row_sub = longest_eq(dense_rows, STEP, 8)
print(f"row 17-步距子序列: {len(row_sub)} 個, 從 y={row_sub[0]} 到 y={row_sub[-1]}")
if len(row_sub) < 32:
    print(f"錯誤: 至少需 32 行，目前 {len(row_sub)}")
    exit(1)
rows = row_sub[:32]

# 列方向：用 sep_cols 等步距子序列 + 向前推一個虛擬 sep
col_sub = longest_eq(sep_cols, STEP, 4)
print(f"col 17-步距子序列: {len(col_sub)} 個, 從 x={col_sub[0]} 到 x={col_sub[-1]}")
if len(col_sub) < 11:
    print(f"錯誤: 至少需 11 個 col sep，目前 {len(col_sub)}")
    exit(1)
# tile 起點 = 虛擬前置 sep+1 加上 子序列 sep+1，取前 12 個
cols = [col_sub[0] - STEP + 1] + [s + 1 for s in col_sub]
cols = cols[:12]
print(f"col 起點: {cols}")

print(f"網格: 32 行 x 12 列 (tile {TILE}x{TILE})")
print(f"row 起點: {rows[0]}..{rows[-1]}, col 起點: {cols[0]}..{cols[-1]}")

# 洋紅 / 白底去背
MAG = (255, 0, 255)
def clean(t):
    p = t.load()
    for y in range(TILE):
        for x in range(TILE):
            r, g, b, a = p[x, y]
            if (r, g, b) == MAG or (a > 0 and (r, g, b) == (255, 255, 255)):
                p[x, y] = (0, 0, 0, 0)

# 輸出 V8_00.png ~ V8_31.png（每張 203x16：12 個 16x16 tile，tile 間 1px 透明 gap）
# 與 index.html 的 PITCH = CELL_SIZE + GAP = 17 對齊（frame c 位於 x = c*17）
GAP = 1
out_w = 12 * TILE + 11 * GAP  # 12*16 + 11*1 = 203
for r in range(32):
    out = Image.new("RGBA", (out_w, TILE), (0, 0, 0, 0))
    for c in range(12):
        x = cols[c]
        y = rows[r]
        t = img.crop((x, y, x + TILE, y + TILE))
        clean(t)
        out.paste(t, (c * (TILE + GAP), 0), t)
    out.save(os.path.join(OUT_DIR, f"V8_{r:02d}.png"))
    print(f"[V8_{r:02d}.png] 已保存 {out.size}")

print("完成!")
