import re

def filter_images(content: str) -> tuple[str, dict]:
    """Filter images with short placeholders"""
    image_map = {}
    filtered = content
    
    patterns = {
        'IMG': r'<img[^>]+>',
        'SVG': r'<svg[\s\S]*?</svg>',
        'B64': r'data:image\/[^;]+;base64,[a-zA-Z0-9+/]+'
    }
    
    counter = 1
    for type_key, pattern in patterns.items():
        for match in re.finditer(pattern, filtered):
            placeholder = f"__{type_key}{counter}__"
            image_map[placeholder] = match.group(0)
            filtered = filtered.replace(match.group(0), placeholder)
            counter += 1
            
    return filtered, image_map

def restore_images(content: str, image_map: dict) -> str:
    """Restore images from map"""
    for placeholder, image in image_map.items():
        content = content.replace(placeholder, image)
    return content
