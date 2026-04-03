"""Lane geometry and board placement helpers."""

from __future__ import annotations

import pygame

from .. import constants as c


def board_insert_position(
    tile_size: tuple[int, int],
    board_rect: pygame.Rect,
    lane_index: int,
    slot_index: int,
) -> tuple[int, int]:
    if lane_index == 0:
        min_x = board_rect.left + c.BOARD_TOP_TIER_LEFT_PADDING
        max_x = board_rect.right - \
            tile_size[0] - c.BOARD_TOP_TIER_RIGHT_PADDING
    else:
        min_x = board_rect.left + c.BOARD_BOTTOM_TIER_LEFT_PADDING
        max_x = board_rect.right - \
            tile_size[0] - c.BOARD_BOTTOM_TIER_RIGHT_PADDING

    step_x = tile_size[0] + 4
    x = min_x + ((slot_index - 1) * step_x)
    x = max(min_x, min(x, max_x))

    rel_center_x = (x + (tile_size[0] / 2)) - board_rect.left
    lane0_center_y = board_rect.top + c.BOARD_LANE_BASE_OFFSET_Y + \
        (c.BOARD_LANE_SLOPE_PER_PX * rel_center_x)
    lane_center_y = lane0_center_y if lane_index == 0 else lane0_center_y + \
        c.BOARD_LANE_SPACING_Y
    y = round(lane_center_y - (tile_size[1] / 2))
    return int(x), int(y)


def lane_index_for_rect(rect: pygame.Rect, board_rect: pygame.Rect) -> int:
    rel_center_x = rect.centerx - board_rect.left
    lane0_center_y = board_rect.top + c.BOARD_LANE_BASE_OFFSET_Y + \
        (c.BOARD_LANE_SLOPE_PER_PX * rel_center_x)
    lane1_center_y = lane0_center_y + c.BOARD_LANE_SPACING_Y
    return 0 if abs(rect.centery - lane0_center_y) <= abs(rect.centery - lane1_center_y) else 1


def lock_rect_to_lane(rect: pygame.Rect, lane_index: int, board_rect: pygame.Rect) -> None:
    rel_center_x = rect.centerx - board_rect.left
    lane0_center_y = board_rect.top + c.BOARD_LANE_BASE_OFFSET_Y + \
        (c.BOARD_LANE_SLOPE_PER_PX * rel_center_x)
    lane_center_y = lane0_center_y if lane_index == 0 else lane0_center_y + \
        c.BOARD_LANE_SPACING_Y
    rect.y = round(lane_center_y - (rect.height / 2))


def bottom_lane_top_for_rect(rect: pygame.Rect, board_rect: pygame.Rect) -> float:
    rel_center_x = rect.centerx - board_rect.left
    lane0_center_y = board_rect.top + c.BOARD_LANE_BASE_OFFSET_Y + \
        (c.BOARD_LANE_SLOPE_PER_PX * rel_center_x)
    lane1_center_y = lane0_center_y + c.BOARD_LANE_SPACING_Y
    return lane1_center_y - (rect.height / 2)
