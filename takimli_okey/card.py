"""Card model and rendering logic."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from .constants import (
    DRAG_OUTLINE_COLOR,
    DRAG_OUTLINE_THICKNESS,
    OUTSIDE_THRESHOLD,
    TILE_BACK_OFFSET_MAX_PX,
    TILE_COLORS,
    TILE_NUMBER_MARGIN,
    VANISHING_POINT_X,
    VANISHING_POINT_Y,
)


@dataclass(frozen=True)
class TileSprites:
    """Shared images for drawing any card."""

    front: pygame.Surface
    back: pygame.Surface
    # white opaque tile shape; used to build the drag outline at draw-time
    mask_surf: pygame.Surface


def _make_combined_outline(
    mask_surf: pygame.Surface,
    back_offset: tuple[int, int],
    color: tuple[int, int, int],
    thickness: int,
) -> tuple[pygame.Surface, tuple[int, int]]:
    """Build one outline ring around the union shape of front + back tile positions."""
    ox, oy = back_offset
    w, h = mask_surf.get_size()

    min_x = min(0, ox)
    min_y = min(0, oy)
    canvas_w = w + abs(ox) + 2 * thickness
    canvas_h = h + abs(oy) + 2 * thickness

    front_pos = (-min_x + thickness, -min_y + thickness)
    back_pos = (ox - min_x + thickness, oy - min_y + thickness)

    # Stamp both shapes into a combined canvas
    combined = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)
    combined.blit(mask_surf, back_pos)
    combined.blit(mask_surf, front_pos)

    # Expand the union mask outward by `thickness` pixels
    combined_mask = pygame.mask.from_surface(combined)
    shape = combined_mask.to_surface(
        setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    outline = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx == 0 and dy == 0:
                continue
            outline.blit(shape, (dx, dy))

    # Punch the filled union out so only the ring remains
    erase = combined_mask.to_surface(
        setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
    outline.blit(erase, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    # Blit offset: canvas top-left relative to self.rect top-left
    blit_offset = (min_x - thickness, min_y - thickness)
    return outline, blit_offset


class Card:
    """Represents a single okey tile / card."""

    NORMAL = "normal"
    OUTSIDE = "outside"

    def __init__(self, number: int, color: str, x: int, y: int, tile_size: tuple[int, int]):
        self.number = number
        self.color = color
        self.rect = pygame.Rect(x, y, tile_size[0], tile_size[1])
        self.state = Card.NORMAL
        self.dragging = False
        self.snapped_to_lane = False
        self._drag_offset = (0, 0)

    def start_drag(self, mouse_pos: tuple[int, int]) -> None:
        self.dragging = True
        self.snapped_to_lane = False
        self._drag_offset = (
            mouse_pos[0] - self.rect.x,
            mouse_pos[1] - self.rect.y,
        )

    def update_drag(self, mouse_pos: tuple[int, int]) -> None:
        if self.dragging:
            self.rect.x = mouse_pos[0] - self._drag_offset[0]
            self.rect.y = mouse_pos[1] - self._drag_offset[1]

    def stop_drag(self, game_area: pygame.Rect) -> None:
        self.dragging = False
        self.snapped_to_lane = False
        self._update_state(game_area)

    def update_drag_with_state(self, mouse_pos: tuple[int, int], game_area: pygame.Rect) -> None:
        if not self.dragging:
            return
        self.snapped_to_lane = False
        self.rect.x = mouse_pos[0] - self._drag_offset[0]
        self.rect.y = mouse_pos[1] - self._drag_offset[1]
        self._update_state(game_area)

    def _update_state(self, game_area: pygame.Rect) -> None:
        inside_rect = game_area.clip(self.rect)
        inside_area = inside_rect.width * inside_rect.height
        card_area = self.rect.width * self.rect.height
        if inside_area > (card_area * OUTSIDE_THRESHOLD):
            self.state = Card.NORMAL
        else:
            self.state = Card.OUTSIDE

    def _back_offset_toward_center(self, game_area: pygame.Rect) -> tuple[int, int]:
        game_center_x, game_center_y = VANISHING_POINT_X, VANISHING_POINT_Y
        card_center_x, card_center_y = self.rect.center

        dx = game_center_x - card_center_x
        dy = game_center_y - card_center_y
        distance = math.hypot(dx, dy)
        if distance == 0:
            return 0, 0

        max_distance = max(
            math.hypot(game_center_x - game_area.left,
                       game_center_y - game_area.top),
            math.hypot(game_center_x - game_area.right,
                       game_center_y - game_area.top),
            math.hypot(game_center_x - game_area.left,
                       game_center_y - game_area.bottom),
            math.hypot(game_center_x - game_area.right,
                       game_center_y - game_area.bottom),
        )
        relative_distance = min(
            1.0, distance / max_distance) if max_distance else 0.0
        offset_amount = TILE_BACK_OFFSET_MAX_PX * relative_distance

        return (
            round((dx / distance) * offset_amount),
            round((dy / distance) * offset_amount),
        )

    def snap_to_inclined_lanes(
        self,
        board_rect: pygame.Rect,
        lane_base_offset_y: float,
        lane_spacing_y: float,
        lane_slope_per_px: float,
        top_lane_left_padding: int,
        top_lane_right_padding: int,
        bottom_lane_left_padding: int,
        bottom_lane_right_padding: int,
        snap_max_dist_px: float,
    ) -> None:
        """Snap Y to one of two slanted lanes while keeping X free within board bounds."""
        if not self.rect.colliderect(board_rect):
            self.snapped_to_lane = False
            return

        rel_center_x = self.rect.centerx - board_rect.left
        lane0_center_y = board_rect.top + lane_base_offset_y + \
            (lane_slope_per_px * rel_center_x)
        lane1_center_y = lane0_center_y + lane_spacing_y

        card_center_y = self.rect.centery
        dist_lane0 = abs(card_center_y - lane0_center_y)
        dist_lane1 = abs(card_center_y - lane1_center_y)
        nearest_dist = min(dist_lane0, dist_lane1)

        # Only snap when reasonably close to a lane center to avoid large jumps.
        if nearest_dist > snap_max_dist_px:
            self.snapped_to_lane = False
            return

        lane_is_top = dist_lane0 <= dist_lane1
        if lane_is_top:
            min_x = board_rect.left + top_lane_left_padding
            max_x = board_rect.right - self.rect.width - top_lane_right_padding
        else:
            min_x = board_rect.left + bottom_lane_left_padding
            max_x = board_rect.right - self.rect.width - bottom_lane_right_padding

        if max_x >= min_x:
            self.rect.x = max(min_x, min(self.rect.x, max_x))

        rel_center_x = self.rect.centerx - board_rect.left
        lane0_center_y = board_rect.top + lane_base_offset_y + \
            (lane_slope_per_px * rel_center_x)
        lane1_center_y = lane0_center_y + lane_spacing_y
        chosen_lane_center_y = lane0_center_y if lane_is_top else lane1_center_y
        self.rect.y = round(chosen_lane_center_y - (self.rect.height / 2))
        self.snapped_to_lane = True

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        sprites: dict[str, TileSprites],
        game_area: pygame.Rect,
    ) -> None:
        back_offset_x, back_offset_y = self._back_offset_toward_center(
            game_area)
        back_rect = self.rect.move(back_offset_x, back_offset_y)

        tile_sprites = sprites[self.color]
        text_color = (
            100, 100, 100) if self.state == Card.OUTSIDE else TILE_COLORS[self.color]

        surface.blit(tile_sprites.back, back_rect)
        surface.blit(tile_sprites.front, self.rect)

        if self.dragging and self.snapped_to_lane:
            outline, (blit_ox, blit_oy) = _make_combined_outline(
                tile_sprites.mask_surf,
                (back_offset_x, back_offset_y),
                DRAG_OUTLINE_COLOR,
                DRAG_OUTLINE_THICKNESS,
            )
            surface.blit(
                outline, (self.rect.x + blit_ox, self.rect.y + blit_oy))

        num_surf = font.render(str(self.number), True, text_color)
        surface.blit(num_surf, (self.rect.x + TILE_NUMBER_MARGIN,
                     self.rect.y + TILE_NUMBER_MARGIN))

        num_surf_rot = pygame.transform.rotate(num_surf, 180)
        surface.blit(
            num_surf_rot,
            (
                self.rect.right - num_surf_rot.get_width() - TILE_NUMBER_MARGIN,
                self.rect.bottom - num_surf_rot.get_height() - TILE_NUMBER_MARGIN,
            ),
        )
