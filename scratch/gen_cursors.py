from PIL import Image, ImageDraw

d='app/static/cursors/'

def create_cursor(filename, color):
    # 32x32 transparent background
    img = Image.new('RGBA', (32, 32), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    # Simple arrow shape
    draw.polygon([(0, 0), (20, 10), (10, 15), (15, 30), (8, 30), (5, 20), (0, 25)], fill=color, outline='black')
    img.save(d + filename)

create_cursor('retro.png', 'white')
create_cursor('minecraft.png', '#00ff00')
create_cursor('lol.png', 'gold')
print("Cursors generated!")
