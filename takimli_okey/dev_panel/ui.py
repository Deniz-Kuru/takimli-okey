"""Developer panel UI and window management."""

import pygame

from ..constants import TILE_COLORS
from .constants import (
    DEV_PANEL_BG_COLOR,
    DEV_PANEL_BORDER_COLOR,
    DEV_PANEL_BUTTON_BG,
    DEV_PANEL_BUTTON_HEIGHT,
    DEV_PANEL_BUTTON_SELECTED_BG,
    DEV_PANEL_NUM_BUTTON_SIZE,
    DEV_PANEL_NUM_COLS,
    DEV_PANEL_PADDING,
    DEV_PANEL_RELOAD_BUTTON_BG,
    DEV_PANEL_SECTION_GAP,
    DEV_PANEL_TEXT_COLOR,
    DEV_PANEL_WINDOW_H,
    DEV_PANEL_WINDOW_W,
)


class DevPanel:
    """Manages the developer panel window and UI state."""

    def __init__(self, font_hud: pygame.font.Font, font_num: pygame.font.Font) -> None:
        """Initialize the dev panel with fonts."""
        self.font_hud = font_hud
        self.font_num = font_num
        self.surface = pygame.Surface((DEV_PANEL_WINDOW_W, DEV_PANEL_WINDOW_H))

        self.selected_color = next(iter(TILE_COLORS.keys()))
        self.selected_number = 1
        self.selected_lane = 0  # 0 = top tier, 1 = bottom tier
        self.selected_slot = 1
        self.max_slot = 20
        self.selected_quantity = 1
        self.max_quantity = 20

        self.layout = self._build_layout()

    def _build_layout(self) -> dict[str, object]:
        """Build layout for the dev panel window."""
        x0 = DEV_PANEL_PADDING
        # Account for title, mouse label, and spacing at the top
        y = DEV_PANEL_PADDING + 60  # Title + mouse info + space
        content_w = DEV_PANEL_WINDOW_W - (2 * DEV_PANEL_PADDING)

        # Color selector section title
        y += 24  # Space for section title

        color_buttons: dict[str, pygame.Rect] = {}
        for color in TILE_COLORS:
            color_buttons[color] = pygame.Rect(
                x0, y, content_w, DEV_PANEL_BUTTON_HEIGHT)
            y += DEV_PANEL_BUTTON_HEIGHT + 8

        y += DEV_PANEL_SECTION_GAP

        # Number selector section title
        y += 24  # Space for section title

        num_buttons: dict[int, pygame.Rect] = {}
        for number in range(1, 14):
            idx = number - 1
            row = idx // DEV_PANEL_NUM_COLS
            col = idx % DEV_PANEL_NUM_COLS
            btn_x = x0 + (col * (DEV_PANEL_NUM_BUTTON_SIZE + 8))
            btn_y = y + (row * (DEV_PANEL_NUM_BUTTON_SIZE + 8))
            num_buttons[number] = pygame.Rect(
                btn_x, btn_y, DEV_PANEL_NUM_BUTTON_SIZE, DEV_PANEL_NUM_BUTTON_SIZE
            )

        num_rows = ((13 - 1) // DEV_PANEL_NUM_COLS) + 1
        y += num_rows * (DEV_PANEL_NUM_BUTTON_SIZE + 8)
        y += DEV_PANEL_SECTION_GAP

        insert_button = pygame.Rect(
            x0, y, content_w, DEV_PANEL_BUTTON_HEIGHT + 6)
        y += DEV_PANEL_BUTTON_HEIGHT + 12

        # Board-grid insertion controls
        y += 24  # Space for section title

        lane_gap = 8
        lane_w = (content_w - lane_gap) // 2
        lane_top_button = pygame.Rect(x0, y, lane_w, DEV_PANEL_BUTTON_HEIGHT)
        lane_bottom_button = pygame.Rect(
            x0 + lane_w + lane_gap, y, lane_w, DEV_PANEL_BUTTON_HEIGHT)
        y += DEV_PANEL_BUTTON_HEIGHT + 8

        slot_btn_w = 40
        slot_dec_button = pygame.Rect(
            x0, y, slot_btn_w, DEV_PANEL_BUTTON_HEIGHT)
        slot_inc_button = pygame.Rect(
            x0 + content_w - slot_btn_w, y, slot_btn_w, DEV_PANEL_BUTTON_HEIGHT)
        slot_value_rect = pygame.Rect(
            x0 + slot_btn_w + 8,
            y,
            content_w - (2 * slot_btn_w) - 16,
            DEV_PANEL_BUTTON_HEIGHT,
        )
        y += DEV_PANEL_BUTTON_HEIGHT + 8

        quantity_dec_button = pygame.Rect(
            x0, y, slot_btn_w, DEV_PANEL_BUTTON_HEIGHT)
        quantity_inc_button = pygame.Rect(
            x0 + content_w - slot_btn_w, y, slot_btn_w, DEV_PANEL_BUTTON_HEIGHT)
        quantity_value_rect = pygame.Rect(
            x0 + slot_btn_w + 8,
            y,
            content_w - (2 * slot_btn_w) - 16,
            DEV_PANEL_BUTTON_HEIGHT,
        )
        y += DEV_PANEL_BUTTON_HEIGHT + 8

        insert_grid_button = pygame.Rect(
            x0, y, content_w, DEV_PANEL_BUTTON_HEIGHT + 4)
        y += DEV_PANEL_BUTTON_HEIGHT + 12

        reload_button = pygame.Rect(
            x0, y, content_w, DEV_PANEL_BUTTON_HEIGHT)

        return {
            "color_buttons": color_buttons,
            "num_buttons": num_buttons,
            "insert_button": insert_button,
            "lane_top_button": lane_top_button,
            "lane_bottom_button": lane_bottom_button,
            "slot_dec_button": slot_dec_button,
            "slot_inc_button": slot_inc_button,
            "slot_value_rect": slot_value_rect,
            "quantity_dec_button": quantity_dec_button,
            "quantity_inc_button": quantity_inc_button,
            "quantity_value_rect": quantity_value_rect,
            "insert_grid_button": insert_grid_button,
            "reload_button": reload_button,
        }

    def handle_click(self, mouse_pos: tuple[int, int]) -> tuple[str | None, int | None, bool, bool, bool]:
        """
        Handle a click on the dev panel.

        Returns:
            (selected_color, selected_number, insert_pressed, insert_grid_pressed, reload_pressed)
            Where selected_color/number are None if not changed.
        """
        color_buttons: dict[str,
                            # type: ignore
                            pygame.Rect] = self.layout["color_buttons"]
        # type: ignore
        num_buttons: dict[int, pygame.Rect] = self.layout["num_buttons"]
        # type: ignore
        insert_button: pygame.Rect = self.layout["insert_button"]
        # type: ignore
        lane_top_button: pygame.Rect = self.layout["lane_top_button"]
        # type: ignore
        lane_bottom_button: pygame.Rect = self.layout["lane_bottom_button"]
        # type: ignore
        slot_dec_button: pygame.Rect = self.layout["slot_dec_button"]
        # type: ignore
        slot_inc_button: pygame.Rect = self.layout["slot_inc_button"]
        # type: ignore
        quantity_dec_button: pygame.Rect = self.layout["quantity_dec_button"]
        # type: ignore
        quantity_inc_button: pygame.Rect = self.layout["quantity_inc_button"]
        # type: ignore
        insert_grid_button: pygame.Rect = self.layout["insert_grid_button"]
        # type: ignore
        reload_button: pygame.Rect = self.layout["reload_button"]

        for color, rect in color_buttons.items():
            if rect.collidepoint(mouse_pos):
                self.selected_color = color
                return color, None, False, False, False

        for number, rect in num_buttons.items():
            if rect.collidepoint(mouse_pos):
                self.selected_number = number
                return None, number, False, False, False

        if insert_button.collidepoint(mouse_pos):
            return None, None, True, False, False

        if lane_top_button.collidepoint(mouse_pos):
            self.selected_lane = 0
            return None, None, False, False, False

        if lane_bottom_button.collidepoint(mouse_pos):
            self.selected_lane = 1
            return None, None, False, False, False

        if slot_dec_button.collidepoint(mouse_pos):
            self.selected_slot = max(1, self.selected_slot - 1)
            return None, None, False, False, False

        if slot_inc_button.collidepoint(mouse_pos):
            self.selected_slot = min(self.max_slot, self.selected_slot + 1)
            return None, None, False, False, False

        if quantity_dec_button.collidepoint(mouse_pos):
            self.selected_quantity = max(1, self.selected_quantity - 1)
            return None, None, False, False, False

        if quantity_inc_button.collidepoint(mouse_pos):
            self.selected_quantity = min(
                self.max_quantity, self.selected_quantity + 1)
            return None, None, False, False, False

        if insert_grid_button.collidepoint(mouse_pos):
            return None, None, False, True, False

        if reload_button.collidepoint(mouse_pos):
            return None, None, False, False, True

        return None, None, False, False, False

    def draw(self, mouse_pos: tuple[int, int]) -> pygame.Surface:
        """Render the dev panel and return the surface."""
        self.surface.fill(DEV_PANEL_BG_COLOR)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         self.surface.get_rect(), width=2)

        # Title and info at the top
        title = self.font_hud.render(
            "Developer Panel", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(title, (DEV_PANEL_PADDING, DEV_PANEL_PADDING))

        mouse_label = self.font_hud.render(
            f"Mouse: {mouse_pos[0]}, {mouse_pos[1]}", True, DEV_PANEL_TEXT_COLOR
        )
        self.surface.blit(
            mouse_label, (DEV_PANEL_PADDING, DEV_PANEL_PADDING + 24))

        # Color selector section
        color_title = self.font_hud.render(
            "Color Selector", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(
            color_title, (DEV_PANEL_PADDING, DEV_PANEL_PADDING + 54))

        # type: ignore
        color_buttons: dict[str, pygame.Rect] = self.layout["color_buttons"]
        for color, rect in color_buttons.items():
            selected = color == self.selected_color
            bg = DEV_PANEL_BUTTON_SELECTED_BG if selected else DEV_PANEL_BUTTON_BG
            pygame.draw.rect(self.surface, bg, rect, border_radius=8)
            pygame.draw.rect(
                self.surface, TILE_COLORS[color], rect, width=2, border_radius=8)
            txt = self.font_hud.render(
                color.capitalize(), True, DEV_PANEL_TEXT_COLOR)
            self.surface.blit(txt, txt.get_rect(center=rect.center))

        # Number selector section title
        first_num_button_y = min(
            r.top for r in self.layout["num_buttons"].values())  # type: ignore
        num_title_y = first_num_button_y - 26
        num_title = self.font_hud.render(
            "Number Selector", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(num_title, (DEV_PANEL_PADDING, num_title_y))

        # type: ignore
        num_buttons: dict[int, pygame.Rect] = self.layout["num_buttons"]
        for number, rect in num_buttons.items():
            selected = number == self.selected_number
            bg = DEV_PANEL_BUTTON_SELECTED_BG if selected else DEV_PANEL_BUTTON_BG
            pygame.draw.rect(self.surface, bg, rect, border_radius=6)
            pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                             rect, width=1, border_radius=6)
            txt = self.font_num.render(str(number), True, DEV_PANEL_TEXT_COLOR)
            self.surface.blit(txt, txt.get_rect(center=rect.center))

        # Insert button
        # type: ignore
        insert_button: pygame.Rect = self.layout["insert_button"]
        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_SELECTED_BG,
                         insert_button, border_radius=8)
        pygame.draw.rect(
            self.surface, DEV_PANEL_BORDER_COLOR, insert_button, width=1, border_radius=8
        )
        insert_label = self.font_hud.render(
            "Insert Tile", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(insert_label, insert_label.get_rect(
            center=insert_button.center))

        # Board-grid insertion controls
        # type: ignore
        lane_top_button: pygame.Rect = self.layout["lane_top_button"]
        # type: ignore
        lane_bottom_button: pygame.Rect = self.layout["lane_bottom_button"]
        # type: ignore
        slot_dec_button: pygame.Rect = self.layout["slot_dec_button"]
        # type: ignore
        slot_inc_button: pygame.Rect = self.layout["slot_inc_button"]
        # type: ignore
        slot_value_rect: pygame.Rect = self.layout["slot_value_rect"]
        # type: ignore
        quantity_dec_button: pygame.Rect = self.layout["quantity_dec_button"]
        # type: ignore
        quantity_inc_button: pygame.Rect = self.layout["quantity_inc_button"]
        # type: ignore
        quantity_value_rect: pygame.Rect = self.layout["quantity_value_rect"]
        # type: ignore
        insert_grid_button: pygame.Rect = self.layout["insert_grid_button"]

        board_title_y = lane_top_button.top - 26
        board_title = self.font_hud.render(
            "Board Insert", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(board_title, (DEV_PANEL_PADDING, board_title_y))

        lane_top_bg = DEV_PANEL_BUTTON_SELECTED_BG if self.selected_lane == 0 else DEV_PANEL_BUTTON_BG
        lane_bottom_bg = DEV_PANEL_BUTTON_SELECTED_BG if self.selected_lane == 1 else DEV_PANEL_BUTTON_BG
        pygame.draw.rect(self.surface, lane_top_bg,
                         lane_top_button, border_radius=8)
        pygame.draw.rect(self.surface, lane_bottom_bg,
                         lane_bottom_button, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         lane_top_button, width=1, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         lane_bottom_button, width=1, border_radius=8)
        top_txt = self.font_hud.render("Top Tier", True, DEV_PANEL_TEXT_COLOR)
        bot_txt = self.font_hud.render(
            "Bottom Tier", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(top_txt, top_txt.get_rect(
            center=lane_top_button.center))
        self.surface.blit(bot_txt, bot_txt.get_rect(
            center=lane_bottom_button.center))

        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_BG,
                         slot_dec_button, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_BG,
                         slot_inc_button, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_SELECTED_BG,
                         slot_value_rect, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         slot_dec_button, width=1, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         slot_inc_button, width=1, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         slot_value_rect, width=1, border_radius=8)
        dec_txt = self.font_hud.render("-", True, DEV_PANEL_TEXT_COLOR)
        inc_txt = self.font_hud.render("+", True, DEV_PANEL_TEXT_COLOR)
        slot_txt = self.font_hud.render(
            f"Grid Slot: {self.selected_slot}", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(dec_txt, dec_txt.get_rect(
            center=slot_dec_button.center))
        self.surface.blit(inc_txt, inc_txt.get_rect(
            center=slot_inc_button.center))
        self.surface.blit(slot_txt, slot_txt.get_rect(
            center=slot_value_rect.center))

        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_BG,
                         quantity_dec_button, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_BG,
                         quantity_inc_button, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_SELECTED_BG,
                         quantity_value_rect, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         quantity_dec_button, width=1, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         quantity_inc_button, width=1, border_radius=8)
        pygame.draw.rect(self.surface, DEV_PANEL_BORDER_COLOR,
                         quantity_value_rect, width=1, border_radius=8)
        qty_txt = self.font_hud.render(
            f"Quantity: {self.selected_quantity}", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(dec_txt, dec_txt.get_rect(
            center=quantity_dec_button.center))
        self.surface.blit(inc_txt, inc_txt.get_rect(
            center=quantity_inc_button.center))
        self.surface.blit(qty_txt, qty_txt.get_rect(
            center=quantity_value_rect.center))

        pygame.draw.rect(self.surface, DEV_PANEL_BUTTON_SELECTED_BG,
                         insert_grid_button, border_radius=8)
        pygame.draw.rect(
            self.surface, DEV_PANEL_BORDER_COLOR, insert_grid_button, width=1, border_radius=8
        )
        grid_label = self.font_hud.render(
            "Insert On Grid (Bulk)", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(grid_label, grid_label.get_rect(
            center=insert_grid_button.center))

        # Reload button
        # type: ignore
        reload_button: pygame.Rect = self.layout["reload_button"]
        pygame.draw.rect(self.surface, DEV_PANEL_RELOAD_BUTTON_BG,
                         reload_button, border_radius=8)
        pygame.draw.rect(
            self.surface, DEV_PANEL_BORDER_COLOR, reload_button, width=1, border_radius=8
        )
        reload_label = self.font_hud.render(
            "Reload Game", True, DEV_PANEL_TEXT_COLOR)
        self.surface.blit(reload_label, reload_label.get_rect(
            center=reload_button.center))

        return self.surface
