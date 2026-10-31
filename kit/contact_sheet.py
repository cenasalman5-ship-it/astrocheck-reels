"""QA sheets from rendered frames (phone-size tiles 180x320, timestamps):
  python3 kit/contact_sheet.py <reel_dir>  ->  <reel_dir>/qa/sheet_0-2s.jpg (6 fps) + qa/sheet_full.jpg (2 fps)"""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
D = os.path.abspath(sys.argv[1]); F = sorted(glob.glob(D + '/frames/f*.jpg')); fps = 30; os.makedirs(D + '/qa', exist_ok=True)
try: font = ImageFont.truetype(os.path.dirname(os.path.abspath(__file__)) + '/fonts/InterDisplay-Bold.otf', 22)
except Exception: font = ImageFont.load_default()
def sheet(idx, name, cols):
    W, H = 180, 320; rows = (len(idx) + cols - 1) // cols; im = Image.new('RGB', (cols * W, rows * (H + 30)), (20, 20, 24)); d = ImageDraw.Draw(im)
    for k, i in enumerate(idx):
        x, y = (k % cols) * W, (k // cols) * (H + 30); im.paste(Image.open(F[i]).resize((W, H)), (x, y + 30)); d.text((x + 6, y + 4), f'{i / fps:.2f}s', fill=(255, 220, 120), font=font)
    im.save(f'{D}/qa/{name}', quality=82); return im.size
print(sheet([i for i in range(0, min(len(F), 2 * fps + 1), 5)], 'sheet_0-2s.jpg', 7), sheet(list(range(0, len(F), 15)), 'sheet_full.jpg', 10))
