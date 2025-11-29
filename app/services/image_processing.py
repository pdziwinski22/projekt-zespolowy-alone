from pathlib import Path
from datetime import datetime

from PIL import Image, ImageEnhance

from .openai_client import describe_image


def _apply_sepia(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    pixels = list(img.getdata())
    new_pixels = []

    for r, g, b in pixels:
        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
        new_pixels.append((min(255, tr), min(255, tg), min(255, tb)))

    img.putdata(new_pixels)
    return img


def _apply_standard_effect(img: Image.Image, effect: str) -> Image.Image:
    effect = (effect or "").lower()

    if effect == "grayscale":
        img = img.convert("L").convert("RGB")
    elif effect == "sepia":
        img = _apply_sepia(img)
    elif effect == "brighten":
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.2)
    elif effect == "contrast":
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
    elif effect == "compress":
        # kompresję robimy przy zapisie
        pass

    return img


def process_image(original_path: Path, result_dir: Path, effect: str):
    img = Image.open(original_path)
    effect = (effect or "").lower()

    img = _apply_standard_effect(img, effect)
    save_effect = effect or "none"

    quality = 50 if effect == "compress" else 90

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    result_name = f"{original_path.stem}_{save_effect}_{ts}.jpg"
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / result_name

    img.save(result_path, format="JPEG", quality=quality, optimize=True)

    # TU wołamy OpenAI
    ai_desc, tokens_in, tokens_out = describe_image(result_path)
    print(">>> process_image AI:", ai_desc, tokens_in, tokens_out)

    return result_name, ai_desc, tokens_in, tokens_out