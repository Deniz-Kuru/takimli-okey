"""Main game loop."""

from __future__ import annotations

import importlib
import random

import pygame
import pygame._sdl2.video as sdl2_video

from . import card as card_module
from . import constants as constants_module
from .card import Card, TileSprites
from .dev_panel import DevPanel
from .dev_panel.constants import DEV_PANEL_WINDOW_H, DEV_PANEL_WINDOW_W
from .constants import (
    BG_COLOR,
    BOARD_BOTTOM_TIER_LEFT_PADDING,
    BOARD_BOTTOM_TIER_RIGHT_PADDING,
    BOARD_IMAGE_PATH,
    BOARD_LANE_BASE_OFFSET_Y,
    BOARD_LANE_SLOPE_PER_PX,
    BOARD_LANE_SPACING_Y,
    BOARD_SNAP_MAX_DIST_PX,
    BOARD_TOP_TIER_LEFT_PADDING,
    BOARD_TOP_TIER_RIGHT_PADDING,
    BOARD_TARGET_WIDTH,
    BOARD_TOP_OFFSET_Y,
    CARD_H,
    CARD_W,
    FONT_SIZE_HUD,
    FONT_SIZE_NUM,
    GAME_AREA_H,
    GAME_AREA_W,
    GAME_AREA_X,
    GAME_AREA_Y,
    TABLE_BORDER,
    TABLE_COLOR,
    TILE_BACK_SHADE_ALPHA,
    TILE_COLOR_TINT_ALPHA,
    TILE_COLORS,
    TILE_IMAGE_PATH,
    WINDOW_H,
    WINDOW_W,
)


RUNTIME_CONSTANT_NAMES = [
    "BG_COLOR",
    "BOARD_BOTTOM_TIER_LEFT_PADDING",
    "BOARD_BOTTOM_TIER_RIGHT_PADDING",
    "BOARD_IMAGE_PATH",
    "BOARD_LANE_BASE_OFFSET_Y",
    "BOARD_LANE_SLOPE_PER_PX",
    "BOARD_LANE_SPACING_Y",
    "BOARD_SNAP_MAX_DIST_PX",
    "BOARD_TOP_TIER_LEFT_PADDING",
    "BOARD_TOP_TIER_RIGHT_PADDING",
    "BOARD_TARGET_WIDTH",
    "BOARD_TOP_OFFSET_Y",
    "CARD_H",
    "CARD_W",
    "FONT_SIZE_HUD",
    "FONT_SIZE_NUM",
    "GAME_AREA_H",
    "GAME_AREA_W",
    "GAME_AREA_X",
    "GAME_AREA_Y",
    "OUTSIDE_THRESHOLD",
    "TABLE_BORDER",
    "TABLE_COLOR",
    "TILE_BACK_SHADE_ALPHA",
    "TILE_COLOR_TINT_ALPHA",
    "TILE_COLORS",
    "TILE_IMAGE_PATH",
    "TILE_BACK_OFFSET_MAX_PX",
    "TILE_NUMBER_MARGIN",
    "VANISHING_POINT_X",
    "VANISHING_POINT_Y",
    "WINDOW_H",
    "WINDOW_W",
]


def _reload_runtime_constants() -> None:
    """Reload constants module and update game/card runtime values."""
    importlib.reload(constants_module)

    # Update this module's constant bindings so all helper functions use fresh values.
    for name in RUNTIME_CONSTANT_NAMES:
        if hasattr(constants_module, name):
            globals()[name] = getattr(constants_module, name)

    # Card module imported constants as plain names; resync them too.
    for name in [
        "DRAG_OUTLINE_COLOR",
        "DRAG_OUTLINE_THICKNESS",
        "OUTSIDE_THRESHOLD",
        "TILE_BACK_OFFSET_MAX_PX",
        "TILE_COLORS",
        "TILE_NUMBER_MARGIN",
        "VANISHING_POINT_X",
        "VANISHING_POINT_Y",
    ]:
        if hasattr(constants_module, name):
            setattr(card_module, name, getattr(constants_module, name))


def _tint_surface(base: pygame.Surface, rgb: tuple[int, int, int], alpha: int) -> pygame.Surface:
    tinted = base.copy()
    overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    overlay.fill((*rgb, alpha))
    tinted.blit(overlay, (0, 0))
    return tinted


def _make_mask_surf(base: pygame.Surface) -> pygame.Surface:
    """Return an opaque-white surface shaped to the tile's non-transparent pixels."""
    mask = pygame.mask.from_surface(base)
    return mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))


def _build_back_variant(base: pygame.Surface) -> pygame.Surface:
    shaded = base.copy()
    overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, TILE_BACK_SHADE_ALPHA))
    shaded.blit(overlay, (0, 0))
    return shaded


def _load_tile_front() -> pygame.Surface:
    try:
        return pygame.image.load(str(TILE_IMAGE_PATH)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        fallback = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        fallback.fill((230, 230, 230))
        pygame.draw.rect(fallback, (120, 120, 120),
                         fallback.get_rect(), width=2, border_radius=6)
        return fallback


def _load_board_surface() -> pygame.Surface:
    try:
        board = pygame.image.load(str(BOARD_IMAGE_PATH)).convert_alpha()
        if BOARD_TARGET_WIDTH > 0 and board.get_width() != BOARD_TARGET_WIDTH:
            scale = BOARD_TARGET_WIDTH / board.get_width()
            board_h = max(1, round(board.get_height() * scale))
            board = pygame.transform.smoothscale(
                board, (BOARD_TARGET_WIDTH, board_h))
        return board
    except (pygame.error, FileNotFoundError):
        fallback = pygame.Surface((BOARD_TARGET_WIDTH, 220), pygame.SRCALPHA)
        pygame.draw.rect(fallback, (90, 70, 45),
                         fallback.get_rect(), border_radius=22)
        pygame.draw.rect(fallback, (140, 110, 70),
                         fallback.get_rect(), width=3, border_radius=22)
        return fallback


def _random_spawn_position(tile_size: tuple[int, int], game_area: pygame.Rect, board_rect: pygame.Rect) -> tuple[int, int]:
    """Return a random tile top-left position inside game area but outside board area."""
    min_x = game_area.left
    max_x = game_area.right - tile_size[0]
    min_y = game_area.top
    max_y = game_area.bottom - tile_size[1]

    for _ in range(120):
        x = random.randint(min_x, max_x)
        y = random.randint(min_y, max_y)
        trial = pygame.Rect(x, y, tile_size[0], tile_size[1])
        if not trial.colliderect(board_rect):
            return x, y

    fallback_x = min_x
    fallback_y = game_area.bottom - tile_size[1]
    return fallback_x, fallback_y


def _init_sprites() -> tuple[pygame.Surface, pygame.Surface, tuple[int, int], dict[str, TileSprites]]:
    """Initialize all sprite assets. Returns (tile_front, board_surface, tile_size, sprites)."""
    tile_front = _load_tile_front()
    board_surface = _load_board_surface()
    tile_size = tile_front.get_size()

    mask_surf = _make_mask_surf(tile_front)
    sprites: dict[str, TileSprites] = {}
    for color, rgb in TILE_COLORS.items():
        tinted_front = _tint_surface(tile_front, rgb, TILE_COLOR_TINT_ALPHA)
        sprites[color] = TileSprites(
            front=tinted_front,
            back=_build_back_variant(tinted_front),
            mask_surf=mask_surf,
        )

    return tile_front, board_surface, tile_size, sprites


def _board_insert_position(
    tile_size: tuple[int, int],
    board_rect: pygame.Rect,
    lane_index: int,
    slot_index: int,
) -> tuple[int, int]:
    """Compute top-left position for direct insertion onto a board lane slot."""
    if lane_index == 0:
        min_x = board_rect.left + BOARD_TOP_TIER_LEFT_PADDING
        max_x = board_rect.right - tile_size[0] - BOARD_TOP_TIER_RIGHT_PADDING
    else:
        min_x = board_rect.left + BOARD_BOTTOM_TIER_LEFT_PADDING
        max_x = board_rect.right - \
            tile_size[0] - BOARD_BOTTOM_TIER_RIGHT_PADDING

    # Keep a readable step while allowing many slots such as slot 10.
    step_x = tile_size[0] + 4
    x = min_x + ((slot_index - 1) * step_x)
    x = max(min_x, min(x, max_x))

    rel_center_x = (x + (tile_size[0] / 2)) - board_rect.left
    lane0_center_y = board_rect.top + BOARD_LANE_BASE_OFFSET_Y + \
        (BOARD_LANE_SLOPE_PER_PX * rel_center_x)
    lane_center_y = lane0_center_y if lane_index == 0 else lane0_center_y + \
        BOARD_LANE_SPACING_Y
    y = round(lane_center_y - (tile_size[1] / 2))

    return int(x), int(y)


def run_game() -> None:
    pygame.init()

    # Create main game window
    main_window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Takimli Okey - Game")

    # Create second SDL2 window for dev panel (independent OS window)
    dev_window_sdl = sdl2_video.Window(
        title="Developer Panel",
        size=(DEV_PANEL_WINDOW_W, DEV_PANEL_WINDOW_H),
    )
    dev_renderer = sdl2_video.Renderer(dev_window_sdl, vsync=True)
    # Pre-create a texture for rendering the dev panel
    dev_texture = sdl2_video.Texture(
        dev_renderer, (DEV_PANEL_WINDOW_W, DEV_PANEL_WINDOW_H))

    clock = pygame.time.Clock()

    # Initialize sprites
    tile_front, board_surface, tile_size, sprites = _init_sprites()

    font_num = pygame.font.SysFont("Arial", FONT_SIZE_NUM, bold=True)
    font_hud = pygame.font.SysFont("Arial", FONT_SIZE_HUD)

    game_area = pygame.Rect(GAME_AREA_X, GAME_AREA_Y, GAME_AREA_W, GAME_AREA_H)
    board_rect = board_surface.get_rect(
        midtop=(game_area.centerx, game_area.top + BOARD_TOP_OFFSET_Y))

    # Create dev panel instance
    dev_panel = DevPanel(font_hud, font_num)
    dev_window_id = dev_window_sdl.id
    hovered_window_id: int | None = None
    dev_mouse_pos = (0, 0)

    cards: list[Card] = []
    dragged_card: Card | None = None
    reload_pending = False

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.WINDOWENTER:
                # event.window may be an int id or an object with an id attribute.
                window_obj = getattr(event, "window", None)
                if hasattr(window_obj, "id"):
                    hovered_window_id = window_obj.id
                elif isinstance(window_obj, int):
                    hovered_window_id = window_obj

            elif event.type == pygame.WINDOWLEAVE:
                hovered_window_id = None

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                event_window_id = None
                window_obj = getattr(event, "window", None)
                if hasattr(window_obj, "id"):
                    event_window_id = window_obj.id
                elif isinstance(window_obj, int):
                    event_window_id = window_obj
                elif hovered_window_id is not None:
                    event_window_id = hovered_window_id

                if event_window_id == dev_window_id:
                    selected_color, selected_number, insert_pressed, insert_grid_pressed, reload_pressed = dev_panel.handle_click(
                        event.pos
                    )

                    if reload_pressed:
                        reload_pending = True

                    if insert_pressed:
                        for _ in range(dev_panel.selected_quantity):
                            spawn_x, spawn_y = _random_spawn_position(
                                tile_size, game_area, board_rect)
                            new_card = Card(
                                dev_panel.selected_number,
                                dev_panel.selected_color,
                                spawn_x,
                                spawn_y,
                                tile_size,
                            )
                            new_card.stop_drag(game_area)
                            cards.append(new_card)

                    if insert_grid_pressed:
                        for offset in range(dev_panel.selected_quantity):
                            slot = dev_panel.selected_slot + offset
                            if slot > dev_panel.max_slot:
                                break

                            board_x, board_y = _board_insert_position(
                                tile_size,
                                board_rect,
                                dev_panel.selected_lane,
                                slot,
                            )
                            new_card = Card(
                                dev_panel.selected_number,
                                dev_panel.selected_color,
                                board_x,
                                board_y,
                                tile_size,
                            )
                            new_card.stop_drag(game_area)
                            cards.append(new_card)
                    continue

                # Store the click position for processing game window clicks
                last_click_pos = event.pos
                for card in reversed(cards):
                    if card.rect.collidepoint(last_click_pos):
                        dragged_card = card
                        cards.remove(card)
                        cards.append(card)
                        card.start_drag(last_click_pos)
                        break

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragged_card is not None:
                    dragged_card.snap_to_inclined_lanes(
                        board_rect,
                        BOARD_LANE_BASE_OFFSET_Y,
                        BOARD_LANE_SPACING_Y,
                        BOARD_LANE_SLOPE_PER_PX,
                        BOARD_TOP_TIER_LEFT_PADDING,
                        BOARD_TOP_TIER_RIGHT_PADDING,
                        BOARD_BOTTOM_TIER_LEFT_PADDING,
                        BOARD_BOTTOM_TIER_RIGHT_PADDING,
                        BOARD_SNAP_MAX_DIST_PX,
                    )
                    dragged_card.stop_drag(board_rect)
                    dragged_card = None

            elif event.type == pygame.MOUSEMOTION:
                event_window_id = None
                window_obj = getattr(event, "window", None)
                if hasattr(window_obj, "id"):
                    event_window_id = window_obj.id
                elif isinstance(window_obj, int):
                    event_window_id = window_obj
                elif hovered_window_id is not None:
                    event_window_id = hovered_window_id

                if event_window_id == dev_window_id:
                    dev_mouse_pos = event.pos
                    continue

                if dragged_card is not None:
                    dragged_card.update_drag_with_state(event.pos, board_rect)
                    dragged_card.snap_to_inclined_lanes(
                        board_rect,
                        BOARD_LANE_BASE_OFFSET_Y,
                        BOARD_LANE_SPACING_Y,
                        BOARD_LANE_SLOPE_PER_PX,
                        BOARD_TOP_TIER_LEFT_PADDING,
                        BOARD_TOP_TIER_RIGHT_PADDING,
                        BOARD_BOTTOM_TIER_LEFT_PADDING,
                        BOARD_BOTTOM_TIER_RIGHT_PADDING,
                        BOARD_SNAP_MAX_DIST_PX,
                    )

        # Handle game reload
        if reload_pending:
            _reload_runtime_constants()

            # Recreate main window in case size constants changed.
            main_window = pygame.display.set_mode((WINDOW_W, WINDOW_H))

            # Rebuild fonts/layout in case related constants changed.
            font_num = pygame.font.SysFont("Arial", FONT_SIZE_NUM, bold=True)
            font_hud = pygame.font.SysFont("Arial", FONT_SIZE_HUD)
            game_area = pygame.Rect(
                GAME_AREA_X, GAME_AREA_Y, GAME_AREA_W, GAME_AREA_H)

            tile_front, board_surface, tile_size, sprites = _init_sprites()
            board_rect = board_surface.get_rect(
                midtop=(game_area.centerx, game_area.top + BOARD_TOP_OFFSET_Y))
            # Full refresh: clear current table state so reload has visible effect.
            cards.clear()
            dragged_card = None
            reload_pending = False

        # Render game area
        main_window.fill(BG_COLOR)
        pygame.draw.rect(main_window, TABLE_COLOR, game_area, border_radius=12)
        pygame.draw.rect(main_window, TABLE_BORDER,
                         game_area, width=3, border_radius=12)
        main_window.blit(board_surface, board_rect)

        label = font_hud.render("Game Area", True, (200, 200, 200))
        main_window.blit(label, (GAME_AREA_X, GAME_AREA_Y - 28))

        for card in cards:
            card.draw(main_window, font_num, sprites, game_area)

        # Render HUD
        normal_count = sum(1 for c in cards if c.state == Card.NORMAL)
        outside_count = sum(1 for c in cards if c.state == Card.OUTSIDE)
        hud = font_hud.render(
            f"Tiles: {len(cards)}  In board: {normal_count}  Outside board: {outside_count}  |  ESC to quit",
            True,
            (220, 220, 220),
        )
        main_window.blit(hud, (GAME_AREA_X, GAME_AREA_Y + GAME_AREA_H + 16))

        pygame.display.flip()

        # Render dev panel to SDL2 window
        dev_panel_surface = dev_panel.draw(dev_mouse_pos)
        dev_texture.update(dev_panel_surface)
        dev_renderer.clear()
        dev_renderer.blit(dev_texture)
        dev_renderer.present()

    pygame.quit()
