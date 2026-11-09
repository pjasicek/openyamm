from pathlib import Path

from PIL import Image, ImageDraw

stage = Path(__file__).resolve().parent
frames = stage / 'review_frames'
for clip, end in [('walking', 25), ('running', 16)]:
    for view in ('front', 'side'):
        columns = 7
        rows = (end + columns) // columns
        board = Image.new('RGB', (columns * 256, rows * 308), (30, 34, 39))
        draw = ImageDraw.Draw(board)
        for frame in range(end + 1):
            source = Image.open(frames / f'{clip}_{view}_{frame:02d}.png').convert('RGB')
            source = source.resize((256, 288), Image.Resampling.LANCZOS)
            x, y = (frame % columns) * 256, (frame // columns) * 308
            board.paste(source, (x, y + 20))
            draw.text((x + 6, y + 4), f'{clip} {view} — {frame}/24 s', fill=(230, 233, 236))
        board.save(stage / f'{clip}_{view}_poses.jpg', quality=94)
    animation = []
    for frame in range(end):
        combined = Image.new('RGB', (1280, 720))
        for offset, view in [(0, 'front'), (640, 'side')]:
            source = Image.open(frames / f'{clip}_{view}_{frame:02d}.png').convert('RGB')
            combined.paste(source, (offset, 0))
        animation.append(combined.resize((768, 432), Image.Resampling.LANCZOS))
    # GIF time is quantized to centiseconds; the GLB retains exact source timing.
    duration = [round((frame + 1) * 100 / 24) * 10 - round(frame * 100 / 24) * 10
                for frame in range(end)]
    animation[0].save(stage / f'{clip}_review.gif', save_all=True, append_images=animation[1:],
                      loop=0, duration=duration, disposal=2)
print('Created four complete-pose sheets and two animation previews')
