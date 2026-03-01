import os
from PIL import Image, ImageDraw, ImageFont

def make_icon():
    # Define colors
    bg_color = (15, 23, 42)  # Dark slate blue background
    text_color = (56, 189, 248)  # Light blue text
    
    # Create high-res base image
    size = (512, 512)
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to load a nice font, fallback to default if not available
    try:
        # Provide path to a standard Windows font that usually supports these characters
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf" 
        font = ImageFont.truetype(font_path, 250)
    except IOError:
        try:
            # Fallback to bold
            font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
            font = ImageFont.truetype(font_path, 250)
        except IOError:
             font = ImageFont.load_default()
             
    # Draw text €+$ centered
    text = "€+$"
    
    # In newer Pillow versions textlength or textbbox are preferred
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older Pillow
        w, h = draw.textsize(text, font=font)
        
    x = (size[0] - w) / 2
    y = ((size[1] - h) / 2) - 40 # slightly bump up for visual center
    
    draw.text((x, y), text, fill=text_color, font=font)
    
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    icon_png_path = os.path.join(assets_dir, 'icon_new.png')
    icon_ico_path = os.path.join(assets_dir, 'icon.ico')
    
    img.save(icon_png_path, "PNG")
    
    # Save as multi-size ICO
    icon_sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
    img.save(icon_ico_path, format="ICO", sizes=icon_sizes)
    print(f"Icons saved to {assets_dir}")

if __name__ == "__main__":
    make_icon()
