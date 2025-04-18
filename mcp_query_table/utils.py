import random
import string
from pathlib import Path
from typing import List, Tuple

from playwright_stealth import StealthConfig


def is_image(path: str) -> bool:
    """判断是否是图片文件"""
    img_ext = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    ext = Path(path).suffix.lower()
    return ext in img_ext


def split_images(files: List[str]) -> Tuple[List[str], List[str]]:
    """图片列表分成两部分"""
    imgs = []
    docs = []
    for f in files:
        if is_image(f):
            imgs.append(f)
        else:
            docs.append(f)
    return imgs, docs


class GlobalVars:
    """全局变量"""

    def __init__(self):
        self.text = ""

    def set_text(self, text):
        self.text = text

    def get_text(self):
        return self.text


# https://github.com/AtuboDad/playwright_stealth/issues/31#issuecomment-2342541305
class FixedConfig(StealthConfig):

    @property
    def enabled_scripts(self):
        key = "".join(random.choices(string.ascii_letters, k=10))
        for script in super().enabled_scripts:
            if "const opts" in script:
                yield script.replace("const opts", f"window.{key}")
                continue
            yield script.replace("opts", f"window.{key}")
