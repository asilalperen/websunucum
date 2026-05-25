import urllib.request
headers = {'User-Agent': 'Mozilla/5.0'}
d = 'app/static/cursors/'

files = [
    ('https://win98icons.alexmeub.com/icons/png/cursor-0.png', 'retro.png'),
    ('https://cdn.custom-cursor.com/db/8615/32/minecraft-diamond-sword-cursor.png', 'minecraft.png'),
    ('https://cdn.custom-cursor.com/db/9764/32/league-of-legends-yasuo-sword-cursor.png', 'lol.png')
]

for url, filename in files:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response, open(d + filename, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
    except Exception as e:
        print(f"Failed {filename}: {e}")
