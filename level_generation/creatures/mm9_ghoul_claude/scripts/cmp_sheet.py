from PIL import Image, ImageDraw
rows = [('MM9','review/mm9_pose/st1_front.png','review/mm9_pose/st1_back.png','review/mm9_pose/st1_q34.png','review/mm9_pose/wk1_q34.png','review/mm9_pose/at1_q34.png','review/mm9_pose/hi1_q34.png','review/mm9_pose/de1_q34.png'),
        ('ours A','review/cmp/a_front.png','review/cmp/a_back.png','review/cmp/a_q.png','review/cmp/wk.png','review/cmp/at.png','review/cmp/hi.png','review/cmp/de.png'),
        ('MM9 B','review/mm9_pose/st2_front.png','review/mm9_pose/st2_back.png','review/mm9_pose/st2_q34.png'), ('ours B','review/cmp/b_front.png','review/cmp/b_back.png','review/cmp/b_q.png'),
        ('MM9 C','review/mm9_pose/st3_front.png','review/mm9_pose/st3_back.png','review/mm9_pose/st3_q34.png'), ('ours C','review/cmp/c_front.png','review/cmp/c_back.png','review/cmp/c_q.png')]
C = 400
s = Image.new('RGB', (7 * C, 6 * C), (35, 35, 35)); d = ImageDraw.Draw(s)
for r, row in enumerate(rows):
    for k, f in enumerate(row[1:]):
        im = Image.open(f).convert('RGB')
        if 'cmp' in f:
            im = im.crop((250, 0, 250 + 763 - 40, 723))
        s.paste(im.resize((C, C)), (k * C, r * C))
    d.text((4, r * C + 4), row[0], fill=(255, 255, 0))
s.save('review/mm9_vs_ours.png')
