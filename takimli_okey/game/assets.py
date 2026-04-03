"""Asset loading and sprite preparation."""

from __future__ import annotations

import random

import pygame

from .. import constants as c
from ..card import TileSprites


def tint_surface(base: pygame.Surface, rgb: tuple[int, int, int], alpha: int) -> pygame.Surface:
    tinted = base.copy()
    overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    overlay.fill((*rgb, alpha))
    tinted.blit(overlay, (0, 0))
    return tinted


def make_mask_surf(base: pygame.Surface) -> pygame.Surface:
    mask = pygame.mask.from_surface(base)
    return mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))


def build_back_variant(base: pygame.Surface) -> pygame.Surface:
    shaded = base.copy()
    overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, c.TILE_BACK_SHADE_ALPHA))
    shaded.blit(overlay, (0, 0))
    return shaded


def load_tile_front() -> pygame.Surface:
    try:
        return pygame.image.load(str(c.TILE_IMAGE_PATH)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        fallback = pygame.Surface((c.CARD_W, c.CARD_H), pygame.SRCALPHA)
        fallback.fill((230, 230, 230))
        pygame.draw.rect(fallback, (120, 120, 120),
                         fallback.get_rect(), width=2, border_radius=6)
        return fallback


def load_board_surface() -> pygame.Surface:
    try:
        return pygame.image.load(str(c.BOARD_IMAGE_PATH)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        fallback = pygame.Surface((c.BOARD_TARGET_WIDTH, 220), pygame.SRCALPHA)
        pygame.draw.rect(fallback, (90, 70, 45),
                         fallback.get_rect(), border_radius=22)
        pygame.draw.rect(fallback, (140, 110, 70),
                         fallback.get_rect(), width=3, border_radius=22)
        return fallback


def init_sprites() -> tuple[pygame.Surface, pygame.Surface, tuple[int, int], dict[str, TileSprites]]:
    tile_front_raw = load_tile_front()
    board_surface_raw = load_board_surface()

    raw_board_w = max(1, board_surface_raw.get_width())
    shared_scale = (c.BOARD_TARGET_WIDTH /
                    raw_board_w) if c.BOARD_TARGET_WIDTH > 0 else 1.0

    board_w = max(1, round(board_surface_raw.get_width() * shared_scale))
    board_h = max(1, round(board_surface_raw.get_height() * shared_scale))
    tile_w = max(1, round(tile_front_raw.get_width() * shared_scale))
    tile_h = max(1, round(tile_front_raw.get_height() * shared_scale))

    board_surface = pygame.transform.smoothscale(
        board_surface_raw, (board_w, board_h))
    tile_front = pygame.transform.smoothscale(tile_front_raw, (tile_w, tile_h))
    tile_size = tile_front.get_size()

    mask_surf = make_mask_surf(tile_front)
    sprites: dict[str, TileSprites] = {}
    for color, rgb in c.TILE_COLORS.items():
        tinted_front = tint_surface(tile_front, rgb, c.TILE_COLOR_TINT_ALPHA)
        sprites[color] = TileSprites(
            front=tinted_front, back=build_back_variant(tinted_front), mask_surf=mask_surf)

    return tile_front, board_surface, tile_size, sprites


def random_spawn_position(tile_size: tuple[int, int], game_area: pygame.Rect, board_rect: pygame.Rect) -> tuple[int, int]:
    min_x = game_area.left
    max_x = game_area.right - tile_size[0]
    min_y = game_area.top
    max_y = game_area.bottom - tile_size[1]

    for _ in range(120):
        x = random.randint(min_x, max_x)
        y = random.randint(min_y, max_y)
        if not pygame.Rect(x, y, tile_size[0], tile_size[1]).colliderect(board_rect):
            return x, y

    return min_x, game_area.bottom - tile_size[1]
