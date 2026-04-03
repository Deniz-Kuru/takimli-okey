"""Collision and push-chain handling for contact drag mode."""

from __future__ import annotations

import math

import pygame

from .. import constants as c
from ..card import Card
from .lanes import lane_index_for_rect, lock_rect_to_lane


def separate_along_row_axis(
    source: pygame.Rect,
    target: pygame.Rect,
    gap_px: int,
) -> None:
    overlap = source.clip(target)
    if overlap.width <= 0 or overlap.height <= 0:
        return

    push_dist = overlap.width + gap_px
    axis_len = math.hypot(1.0, c.BOARD_LANE_SLOPE_PER_PX)
    tx = 1.0 / axis_len
    ty = c.BOARD_LANE_SLOPE_PER_PX / axis_len

    proj = (target.centerx - source.centerx) * tx + \
        (target.centery - source.centery) * ty
    direction = 1.0 if proj >= 0 else -1.0

    old_target_pos = target.x, target.y
    target.x += round(tx * push_dist * direction)
    target.y += round(ty * push_dist * direction)

    moved_dx = target.x - old_target_pos[0]
    moved_dy = target.y - old_target_pos[1]
    moved_along = (moved_dx * tx * direction) + (moved_dy * ty * direction)
    remaining = max(0.0, push_dist - max(0.0, moved_along))
    if remaining > 0:
        source.x += round(-tx * remaining * direction)
        source.y += round(-ty * remaining * direction)


def resolve_push_chain(moved_card: Card, cards: list[Card], board_rect: pygame.Rect) -> None:
    queue: list[Card] = [moved_card]
    steps = 0

    while queue and steps < c.TILE_COLLISION_CHAIN_MAX_STEPS:
        current = queue.pop(0)
        current_lane = lane_index_for_rect(current.rect, board_rect)
        lock_rect_to_lane(current.rect, current_lane, board_rect)

        for other in cards:
            if other is current:
                continue

            other_lane = lane_index_for_rect(other.rect, board_rect)
            if other_lane != current_lane:
                continue

            overlap = current.rect.clip(other.rect)
            if overlap.width <= 0 or overlap.height <= 0:
                continue

            current_area = max(1, current.rect.width * current.rect.height)
            overlap_ratio = (overlap.width * overlap.height) / current_area
            if overlap_ratio < c.TILE_COLLISION_MIN_OVERLAP_RATIO:
                continue

            separate_along_row_axis(
                current.rect, other.rect, c.TILE_COLLISION_GAP_PX)
            lock_rect_to_lane(current.rect, current_lane, board_rect)
            lock_rect_to_lane(other.rect, other_lane, board_rect)
            queue.append(other)
            steps += 1
            if steps >= c.TILE_COLLISION_CHAIN_MAX_STEPS:
                break


def resolve_drag_collisions(dragged_card: Card, cards: list[Card], board_rect: pygame.Rect) -> None:
    passes = 0
    max_passes = max(1, c.TILE_COLLISION_CHAIN_MAX_STEPS // 2)

    while passes < max_passes:
        had_overlap = False
        dragged_lane = lane_index_for_rect(dragged_card.rect, board_rect)
        lock_rect_to_lane(dragged_card.rect, dragged_lane, board_rect)

        for other in reversed(cards):
            if other is dragged_card:
                continue

            other_lane = lane_index_for_rect(other.rect, board_rect)
            if other_lane != dragged_lane:
                continue

            overlap = dragged_card.rect.clip(other.rect)
            if overlap.width <= 0 or overlap.height <= 0:
                continue

            dragged_area = max(1, dragged_card.rect.width *
                               dragged_card.rect.height)
            overlap_ratio = (overlap.width * overlap.height) / dragged_area
            if overlap_ratio < c.TILE_COLLISION_MIN_OVERLAP_RATIO:
                continue

            had_overlap = True
            separate_along_row_axis(
                dragged_card.rect, other.rect, c.TILE_COLLISION_GAP_PX)
            lock_rect_to_lane(dragged_card.rect, dragged_lane, board_rect)
            lock_rect_to_lane(other.rect, other_lane, board_rect)
            resolve_push_chain(other, cards, board_rect)

        if not had_overlap:
            break
        passes += 1
