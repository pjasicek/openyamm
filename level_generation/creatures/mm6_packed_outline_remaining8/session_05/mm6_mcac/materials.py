"""Single native palette: explicit exact bypass and empty matching mask."""
from PIL import Image

def coverage(image):
    return Image.new('L',image.size,0)

def fit(config,inv,repo):
    return {}

def recolor(image,mask,palette,config,vectors):
    assert palette==config['base_palette']
    return image.copy()
