from flask import Flask, render_template, send_file, jsonify, request
from flask_cors import CORS
import os
import tempfile
import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
import io
import zipfile
import requests
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

def download_font():
    """Télécharge la police d'horreur"""
    font_url = "https://github.com/google/fonts/raw/main/ofl/nosifer/Nosifer-Regular.ttf"
    font_path = "/tmp/Nosifer-Regular.ttf"
    try:
        r = requests.get(font_url)
        with open(font_path, 'wb') as f:
            f.write(r.content)
        return font_path
    except:
        return None

def generate_horror_poster():
    """Génère l'affiche d'horreur"""
    # Paramètres
    W, H = 2480, 3508
    CENTER = (W//2, H//2)
    
    # Police
    font_path = download_font()
    
    # 1. Fond
    bg = Image.new('RGB', (W, H), (5, 0, 2))
    draw = ImageDraw.Draw(bg)
    
    # Dégradé
    for y in range(0, H, 10):
        for x in range(0, W, 10):
            dx = x - CENTER[0]
            dy = y - CENTER[1]
            dist = math.sqrt(dx*dx + dy*dy)
            val = int(30 * (1 - dist/1800))
            val = max(0, min(val, 30))
            draw.rectangle([x, y, x+10, y+10], fill=(val, 0, 0))
    
    # Vignette
    vignette = Image.new('L', (W, H), 0)
    v_draw = ImageDraw.Draw(vignette)
    for y in range(0, H, 8):
        for x in range(0, W, 8):
            dx = x - CENTER[0]
            dy = y - CENTER[1]
            dist = math.sqrt(dx*dx + dy*dy)
            alpha = int(200 * (dist / 2000)**1.5)
            alpha = min(200, alpha)
            v_draw.rectangle([x, y, x+8, y+8], fill=alpha)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=30))
    bg.paste((0, 0, 0), mask=vignette)
    
    # Bruit
    noise = np.random.normal(0, 12, (H, W, 3)).astype(np.int16)
    bg_arr = np.array(bg).astype(np.int16) + noise
    bg_arr = np.clip(bg_arr, 0, 255).astype(np.uint8)
    bg = Image.fromarray(bg_arr)
    
    # Brume
    mist = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mist)
    for _ in range(40):
        x = random.randint(0, W)
        y = random.randint(int(H*0.75), H)
        r = random.randint(200, 600)
        alpha = random.randint(5, 25)
        m_draw.ellipse([x-r, y-r, x+r, y+r], fill=(50, 0, 0, alpha))
    mist = mist.filter(ImageFilter.GaussianBlur(radius=60))
    bg = Image.alpha_composite(bg.convert('RGBA'), mist).convert('RGB')
    
    # 2. Effets
    fx = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    fx_draw = ImageDraw.Draw(fx)
    
    # Griffures
    for _ in range(30):
        x = random.randint(0, W)
        y = random.randint(0, H)
        angle = random.uniform(0, 2*math.pi)
        length = random.randint(80, 300)
        dx = length * math.cos(angle)
        dy = length * math.sin(angle)
        for i in range(3):
            fx_draw.line([(x+i, y+i), (x+dx+i, y+dy+i)], 
                        fill=(0, 0, 0, random.randint(40, 100)), width=1)
    
    # Éclaboussures de sang
    for _ in range(20):
        cx = random.randint(100, W-100)
        cy = random.randint(100, H-500)
        size = random.randint(20, 60)
        alpha = random.randint(40, 100)
        fx_draw.ellipse([cx-size, cy-size, cx+size, cy+size], 
                       fill=(120, 0, 0, alpha))
        for _ in range(4):
            sx = cx + random.randint(-size, size)
            sy = cy + random.randint(-size, size)
            sr = random.randint(3, 10)
            fx_draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], 
                          fill=(100, 0, 0, alpha//2))
    
    # Coulures
    for _ in range(12):
        x = random.randint(100, W-100)
        y_start = random.randint(300, 1800)
        length = random.randint(80, 250)
        for step in range(length):
            alpha = max(0, 120 - step)
            fx_draw.ellipse([x-4, y_start+step, x+4, y_start+step+8], 
                          fill=(80, 0, 0, alpha))
    
    # 3. Titre
    title = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(title)
    
    if font_path and os.path.exists(font_path):
        font1 = ImageFont.truetype(font_path, 380)
        font2 = ImageFont.truetype(font_path, 500)
    else:
        font1 = ImageFont.load_default()
        font2 = font1
    
    text1 = "DEADLY"
    text2 = "DEAD"
    y1 = 1000
    y2 = y1 + 480
    
    # Ombres
    for off in [(10, 10), (14, 14), (18, 18)]:
        t_draw.text((CENTER[0], y1), text1, font=font1, 
                   fill=(0, 0, 0, 180), anchor='mm', 
                   stroke_width=off[0], stroke_fill=(0, 0, 0, 100))
        t_draw.text((CENTER[0], y2), text2, font=font2, 
                   fill=(0, 0, 0, 180), anchor='mm', 
                   stroke_width=off[0], stroke_fill=(0, 0, 0, 100))
    
    # Texte
    t_draw.text((CENTER[0], y1), text1, font=font1, 
               fill=(200, 15, 15, 255), anchor='mm', 
               stroke_width=12, stroke_fill=(60, 0, 0, 255))
    t_draw.text((CENTER[0], y2), text2, font=font2, 
               fill=(220, 20, 20, 255), anchor='mm', 
               stroke_width=15, stroke_fill=(80, 0, 0, 255))
    
    # Coulures titre
    bleed_points = [(CENTER[0]-300, y2+180), (CENTER[0]+50, y2+240), 
                   (CENTER[0]+250, y2+150)]
    for bx, by in bleed_points:
        length = random.randint(100, 200)
        for d in range(length):
            alpha = max(0, 150 - d)
            t_draw.ellipse([bx-3, by+d, bx+3, by+d+10], 
                         fill=(180, 0, 0, alpha))
    
    # 4. Sous-titre
    sub = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(sub)
    
    if font_path and os.path.exists(font_path):
        sub_font = ImageFont.truetype(font_path, 140)
    else:
        sub_font = ImageFont.load_default()
    
    y_sub = 2300
    s_draw.text((CENTER[0], y_sub), "THEY ARE COMING BACK", 
               font=sub_font, fill=(210, 210, 210, 220), 
               anchor='mm', stroke_width=5, stroke_fill=(0, 0, 0, 200))
    
    # Lignes
    for ly in [y_sub-90, y_sub+90]:
        s_draw.line([(W//4, ly), (3*W//4, ly)], 
                   fill=(160, 0, 0, 200), width=4)
    
    # 5. Footer
    footer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(footer)
    
    if font_path and os.path.exists(font_path):
        foot_font = ImageFont.truetype(font_path, 80)
    else:
        foot_font = ImageFont.load_default()
    
    y_foot = 3100
    f_draw.text((CENTER[0], y_foot), "COMING SOON", 
               font=foot_font, fill=(150, 150, 150, 200), 
               anchor='mm', stroke_width=3, stroke_fill=(0, 0, 0, 180))
    
    # Assemblage PSD
    psd = PSDImage.new(mode='RGBA', size=(W, H))
    
    bg_rgba = bg.convert('RGBA')
    psd.append(PixelLayer.frompil(bg_rgba, psd, name="Background"))
    psd.append(PixelLayer.frompil(fx, psd, name="Horror Effects"))
    psd.append(PixelLayer.frompil(sub, psd, name="Subtitle"))
    psd.append(PixelLayer.frompil(title, psd, name="Title - DEADLY DEAD"))
    psd.append(PixelLayer.frompil(footer, psd, name="Footer - Coming Soon"))
    
    return psd

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        psd = generate_horror_poster()
        
        # Sauvegarder en mémoire
        psd_buffer = io.BytesIO()
        psd.save(psd_buffer)
        psd_buffer.seek(0)
        
        return send_file(
            psd_buffer,
            mimetype='image/vnd.adobe.photoshop',
            as_attachment=True,
            download_name='deadly_dead_poster.psd'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
