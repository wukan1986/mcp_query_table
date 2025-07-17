from pathlib import Path
from typing import List, Tuple


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
