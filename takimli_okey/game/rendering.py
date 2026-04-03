"""Rendering helpers for game and dev windows."""

from __future__ import annotations

import pygame
import pygame._sdl2.video as sdl2_video

from .. import constants as c
from ..card import Card, TileSprites
from ..dev_panel import DevPanel
from .lanes import lane_index_for_rect


def update_cursor(cursor_kind: str, dragged_card: Card | None) -> str:
    next_cursor_kind = "arrow"
    if pygame.mouse.get_focused() and dragged_card is not None and pygame.mouse.get_pressed(3)[0]:
        next_cursor_kind = "hand"

    if next_cursor_kind != cursor_kind:
        try:
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND if next_cursor_kind == "hand" else pygame.SYSTEM_CURSOR_ARROW
            )
            return next_cursor_kind
        except pygame.error:
            return cursor_kind
    return cursor_kind


def render_main(
    main_window: pygame.Surface,
    board_surface: pygame.Surface,
    board_rect: pygame.Rect,
    game_area: pygame.Rect,
    cards: list[Card],
    font_num: pygame.font.Font,
    font_hud: pygame.font.Font,
    sprites: dict[str, TileSprites],
) -> None:
    main_window.fill(c.BG_COLOR)
    pygame.draw.rect(main_window, c.TABLE_COLOR, game_area, border_radius=12)
    pygame.draw.rect(main_window, c.TABLE_BORDER,
                     game_area, width=3, border_radius=12)
    main_window.blit(board_surface, board_rect)
    main_window.blit(font_hud.render("Game Area", True,
                     (200, 200, 200)), (c.GAME_AREA_X, c.GAME_AREA_Y - 28))

    draw_cards = sorted(
        cards,
        key=lambda card: (
            lane_index_for_rect(
                card.rect, board_rect) if card.snapped_to_lane else 2,
            card.rect.centerx,
            card.rect.centery,
        ),
    )
    for card in draw_cards:
        card.draw(main_window, font_num, sprites, game_area)

    normal_count = sum(1 for card in cards if card.state == Card.NORMAL)
    outside_count = sum(1 for card in cards if card.state == Card.OUTSIDE)
    hud = font_hud.render(
        f"Tiles: {len(cards)}  In board: {normal_count}  Outside board: {outside_count}  |  ESC to quit",
        True,
        (220, 220, 220),
    )
    main_window.blit(hud, (c.GAME_AREA_X, c.GAME_AREA_Y + c.GAME_AREA_H + 16))
    pygame.display.flip()


def render_dev(
    dev_panel: DevPanel,
    dev_mouse_pos: tuple[int, int],
    fall_debug: dict[str, str],
    dev_texture: sdl2_video.Texture,
    dev_renderer: sdl2_video.Renderer,
) -> None:
    dev_panel_surface = dev_panel.draw(dev_mouse_pos, fall_debug)
    dev_texture.update(dev_panel_surface)
    dev_renderer.clear()
    dev_renderer.blit(dev_texture)
    dev_renderer.present()
