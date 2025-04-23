import pygame
import json
import os

# load once at module import
_JSON_PATH = os.path.join("assets", "descriptions_towers.json")
with open(_JSON_PATH, "r") as f:
    _DESCRIPTIONS = json.load(f)


def _wrap_text(text, font, max_width):
    words = text.split(" ")
    lines, current = [], ""
    for w in words:
        test = current + (" " if current else "") + w
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def info_window(scrn: pygame.Surface, choice: str) -> None:
    """
    Display either:
      • an upgrade description box at (mouse_x-221, mouse_y-42), size 191×79 using upgrade_info.png, or
      • a tower description box at (mouse_x-235, mouse_y-10), size 218×48 using tower_info.png.

    Automatically detects whether `choice` is an upgrade title or a tower key.
    """
    mx, my = pygame.mouse.get_pos()

    # --- detect upgrade vs. tower ---
    upgrade_text = None
    for tower_data in _DESCRIPTIONS.values():
        if choice in tower_data["upgrades"]:
            upgrade_text = tower_data["upgrades"][choice]
            break

    if upgrade_text is not None:
        # upgrade info
        text = upgrade_text
        img_path = "assets/upgrade_info.png"
        box_w, box_h = 191, 79
        x, y = mx - 221, my - 42

    else:
        # tower info
        tower_data = _DESCRIPTIONS.get(choice)
        if tower_data is None:
            return  # nothing to show
        text = tower_data["description"]
        img_path = "assets/tower_info.png"
        box_w, box_h = 218, 48
        x, y = mx - 235, my - 10

    # --- blit background ---
    img = pygame.image.load(img_path).convert_alpha()
    scrn.blit(img, (x, y))

    # --- wrap & possibly shrink text ---
    padding = 6
    max_text_w = box_w - padding * 2
    font_size = 18
    font = pygame.font.SysFont("arial", font_size)
    lines = _wrap_text(text, font, max_text_w)

    # if too many lines to fit vertically, shrink font
    while len(lines) * font_size > (box_h - padding * 2) and font_size > 8:
        font_size -= 1
        font = pygame.font.SysFont("arial", font_size)
        lines = _wrap_text(text, font, max_text_w)

    # --- render centered lines ---
    total_h = len(lines) * font_size
    start_y = y + (box_h - total_h) / 2
    for line in lines:
        surf = font.render(line, True, (0, 0, 0))
        surf_x = x + (box_w - surf.get_width()) / 2
        scrn.blit(surf, (surf_x, start_y))
        start_y += font_size
