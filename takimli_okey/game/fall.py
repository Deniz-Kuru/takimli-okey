"""Outside/fall state transitions and fall triggers."""

from __future__ import annotations

import pygame

from .. import constants as c
from ..card import Card
from .lanes import bottom_lane_top_for_rect, lane_index_for_rect


def start_fall_from_origin(card: Card, origin: str, board_rect: pygame.Rect) -> None:
    bottom_lane_top = bottom_lane_top_for_rect(card.rect, board_rect)

    if origin == "top":
        target_y = bottom_lane_top
    elif origin == "bottom":
        target_y = bottom_lane_top + (0.5 * card.rect.height)
    else:
        target_y = bottom_lane_top + (1.5 * card.rect.height)

    card.start_fall_to(target_y, c.TILE_FALL_INITIAL_SPEED_PX_PER_FRAME)


def handle_pushed_outside_falls(cards: list[Card], board_rect: pygame.Rect) -> None:
    right_fall_trigger_x = board_rect.right - c.BOARD_RIGHT_EARLY_FALL_TRIGGER_PX

    for card in cards:
        if card.dragging or card.falling or not card.snapped_to_lane:
            continue

        if board_rect.left <= card.rect.centerx <= right_fall_trigger_x:
            continue

        lane_index = lane_index_for_rect(card.rect, board_rect)
        start_fall_from_origin(card, "top" if lane_index ==
                               0 else "bottom", board_rect)
