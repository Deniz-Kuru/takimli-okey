"""Event handling for input and dev-panel interactions."""

from __future__ import annotations

import pygame

from .. import constants as c
from ..card import Card
from ..dev_panel import DevPanel
from .assets import random_spawn_position
from .collision import resolve_drag_collisions
from .fall import handle_pushed_outside_falls, start_fall_from_origin
from .lanes import board_insert_position


def can_use_right_click_mode(dragged_card: Card | None, board_rect: pygame.Rect) -> bool:
    """Right-click interactions are only active near the board."""
    if dragged_card is None:
        return False
    vicinity = board_rect.inflate(
        2 * c.RIGHT_CLICK_BOARD_VICINITY_PX,
        2 * c.RIGHT_CLICK_BOARD_VICINITY_PX,
    )
    return dragged_card.rect.colliderect(vicinity)


def apply_contact_mode_for_dragged(dragged_card: Card | None, cards: list[Card], board_rect: pygame.Rect) -> None:
    if dragged_card is None:
        return

    dragged_card.snap_to_inclined_lanes(
        board_rect,
        c.BOARD_LANE_BASE_OFFSET_Y,
        c.BOARD_LANE_SPACING_Y,
        c.BOARD_LANE_SLOPE_PER_PX,
        c.BOARD_TOP_TIER_LEFT_PADDING,
        c.BOARD_TOP_TIER_RIGHT_PADDING,
        c.BOARD_BOTTOM_TIER_LEFT_PADDING,
        c.BOARD_BOTTOM_TIER_RIGHT_PADDING,
        c.BOARD_SNAP_MAX_DIST_X_PX,
        c.BOARD_SNAP_MAX_DIST_Y_PX,
        False,
    )
    resolve_drag_collisions(dragged_card, cards, board_rect)
    handle_pushed_outside_falls(cards, board_rect)
    dragged_card.sync_state_with_snap()


def handle_dev_click(
    pos: tuple[int, int],
    dev_panel: DevPanel,
    tile_size: tuple[int, int],
    game_area: pygame.Rect,
    board_rect: pygame.Rect,
    cards: list[Card],
) -> bool:
    _, _, insert_pressed, insert_grid_pressed, reload_pressed = dev_panel.handle_click(
        pos)
    if reload_pressed:
        return True

    if insert_pressed:
        for _ in range(dev_panel.selected_quantity):
            spawn_x, spawn_y = random_spawn_position(
                tile_size, game_area, board_rect)
            new_card = Card(dev_panel.selected_number,
                            dev_panel.selected_color, spawn_x, spawn_y, tile_size)
            new_card.stop_drag(game_area)
            cards.append(new_card)

    if insert_grid_pressed:
        for offset in range(dev_panel.selected_quantity):
            slot = dev_panel.selected_slot + offset
            if slot > dev_panel.max_slot:
                break

            board_x, board_y = board_insert_position(
                tile_size, board_rect, dev_panel.selected_lane, slot)
            new_card = Card(dev_panel.selected_number,
                            dev_panel.selected_color, board_x, board_y, tile_size)
            new_card.snapped_to_lane = True
            new_card.stop_drag(game_area)
            cards.append(new_card)

    return False


def drop_dragged_card(dragged_card: Card | None, drag_contact_mode: bool, drag_contact_grace_until_ms: int, cards: list[Card], board_rect: pygame.Rect) -> None:
    if dragged_card is None:
        return

    near_board = can_use_right_click_mode(dragged_card, board_rect)
    contact_at_drop = near_board and (
        drag_contact_mode or (pygame.time.get_ticks() <=
                              drag_contact_grace_until_ms)
    )
    if contact_at_drop:
        apply_contact_mode_for_dragged(dragged_card, cards, board_rect)
    else:
        start_fall_from_origin(dragged_card, "hover", board_rect)
    dragged_card.stop_drag(board_rect)
