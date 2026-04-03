"""Main game loop."""

from __future__ import annotations

import importlib
import math
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
    BOARD_RIGHT_EARLY_FALL_TRIGGER_PX,
    BOARD_SNAP_MAX_DIST_X_PX,
    BOARD_SNAP_MAX_DIST_Y_PX,
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
    DRAG_CONTACT_GRACE_MS,
    TABLE_BORDER,
    TABLE_COLOR,
    TILE_COLLISION_CHAIN_MAX_STEPS,
    TILE_COLLISION_GAP_PX,
    TILE_COLLISION_MIN_OVERLAP_RATIO,
    TILE_FALL_ACCEL_PX_PER_FRAME2,
    TILE_FALL_INITIAL_SPEED_PX_PER_FRAME,
    TILE_FALL_MAX_SPEED_PX_PER_FRAME,
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
    "BOARD_RIGHT_EARLY_FALL_TRIGGER_PX",
    "BOARD_SNAP_MAX_DIST_X_PX",
    "BOARD_SNAP_MAX_DIST_Y_PX",
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
    "DRAG_CONTACT_GRACE_MS",
    "OUTSIDE_THRESHOLD",
    "TABLE_BORDER",
    "TABLE_COLOR",
    "TILE_COLLISION_CHAIN_MAX_STEPS",
    "TILE_COLLISION_GAP_PX",
    "TILE_COLLISION_MIN_OVERLAP_RATIO",
    "TILE_FALL_ACCEL_PX_PER_FRAME2",
    "TILE_FALL_INITIAL_SPEED_PX_PER_FRAME",
    "TILE_FALL_MAX_SPEED_PX_PER_FRAME",
    "TILE_BACK_SHADE_ALPHA",
    "TILE_COLOR_TINT_ALPHA",
    "TILE_COLORS",
    "TILE_HOVER_SCALE",
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
        "TILE_HOVER_SCALE",
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
        return pygame.image.load(str(BOARD_IMAGE_PATH)).convert_alpha()
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
    tile_front_raw = _load_tile_front()
    board_surface_raw = _load_board_surface()

    # Shared scale factor keeps tile and board proportion fixed.
    raw_board_w = max(1, board_surface_raw.get_width())
    shared_scale = (BOARD_TARGET_WIDTH /
                    raw_board_w) if BOARD_TARGET_WIDTH > 0 else 1.0

    board_w = max(1, round(board_surface_raw.get_width() * shared_scale))
    board_h = max(1, round(board_surface_raw.get_height() * shared_scale))
    tile_w = max(1, round(tile_front_raw.get_width() * shared_scale))
    tile_h = max(1, round(tile_front_raw.get_height() * shared_scale))

    board_surface = pygame.transform.smoothscale(
        board_surface_raw, (board_w, board_h))
    tile_front = pygame.transform.smoothscale(tile_front_raw, (tile_w, tile_h))
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


def _separate_along_row_axis(
    source: pygame.Rect,
    target: pygame.Rect,
    area: pygame.Rect,
    gap_px: int,
    row_slope_per_px: float,
) -> None:
    """Separate target from source along the lane axis; if blocked, move source opposite."""
    overlap = source.clip(target)
    if overlap.width <= 0 or overlap.height <= 0:
        return

    push_dist = overlap.width + gap_px

    # Tangent axis of the inclined row, normalized.
    axis_len = math.hypot(1.0, row_slope_per_px)
    tx = 1.0 / axis_len
    ty = row_slope_per_px / axis_len

    # Decide push direction based on target position projected onto row axis.
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


def _lane_index_for_rect(
    rect: pygame.Rect,
    board_rect: pygame.Rect,
    lane_base_offset_y: float,
    lane_spacing_y: float,
    lane_slope_per_px: float,
) -> int:
    """Return nearest lane index (0 top, 1 bottom) for the rect center."""
    rel_center_x = rect.centerx - board_rect.left
    lane0_center_y = board_rect.top + lane_base_offset_y + \
        (lane_slope_per_px * rel_center_x)
    lane1_center_y = lane0_center_y + lane_spacing_y
    return 0 if abs(rect.centery - lane0_center_y) <= abs(rect.centery - lane1_center_y) else 1


def _lock_rect_to_lane(
    rect: pygame.Rect,
    lane_index: int,
    board_rect: pygame.Rect,
    lane_base_offset_y: float,
    lane_spacing_y: float,
    lane_slope_per_px: float,
) -> None:
    """Project a rect back onto the exact lane line using its current X."""
    rel_center_x = rect.centerx - board_rect.left
    lane0_center_y = board_rect.top + lane_base_offset_y + \
        (lane_slope_per_px * rel_center_x)
    lane_center_y = lane0_center_y if lane_index == 0 else lane0_center_y + lane_spacing_y
    rect.y = round(lane_center_y - (rect.height / 2))


def _bottom_lane_top_for_rect(
    rect: pygame.Rect,
    board_rect: pygame.Rect,
    lane_base_offset_y: float,
    lane_spacing_y: float,
    lane_slope_per_px: float,
) -> float:
    rel_center_x = rect.centerx - board_rect.left
    lane0_center_y = board_rect.top + lane_base_offset_y + \
        (lane_slope_per_px * rel_center_x)
    lane1_center_y = lane0_center_y + lane_spacing_y
    return lane1_center_y - (rect.height / 2)


def _start_fall_from_origin(
    card: Card,
    origin: str,
    board_rect: pygame.Rect,
    lane_base_offset_y: float,
    lane_spacing_y: float,
    lane_slope_per_px: float,
) -> None:
    """Apply 3-level drop targets according to requested gameplay rules."""
    bottom_lane_top = _bottom_lane_top_for_rect(
        card.rect,
        board_rect,
        lane_base_offset_y,
        lane_spacing_y,
        lane_slope_per_px,
    )

    if origin == "top":
        target_y = bottom_lane_top
    elif origin == "bottom":
        target_y = bottom_lane_top + (0.5 * card.rect.height)
    else:  # hover or unknown
        target_y = bottom_lane_top + (1.5 * card.rect.height)

    card.start_fall_to(target_y, TILE_FALL_INITIAL_SPEED_PX_PER_FRAME)


def _handle_pushed_outside_falls(
    cards: list[Card],
    board_rect: pygame.Rect,
    lane_base_offset_y: float,
    lane_spacing_y: float,
    lane_slope_per_px: float,
) -> None:
    """Tiles pushed beyond board X bounds fall and become outside immediately."""
    right_fall_trigger_x = board_rect.right - BOARD_RIGHT_EARLY_FALL_TRIGGER_PX
    for card in cards:
        if card.dragging or card.falling or not card.snapped_to_lane:
            continue
        # Keep left threshold unchanged; trigger earlier only near the right edge.
        if board_rect.left <= card.rect.centerx <= right_fall_trigger_x:
            continue

        lane_index = _lane_index_for_rect(
            card.rect,
            board_rect,
            lane_base_offset_y,
            lane_spacing_y,
            lane_slope_per_px,
        )
        _start_fall_from_origin(
            card,
            "top" if lane_index == 0 else "bottom",
            board_rect,
            lane_base_offset_y,
            lane_spacing_y,
            lane_slope_per_px,
        )


def _resolve_push_chain(
    moved_card: Card,
    cards: list[Card],
    game_area: pygame.Rect,
    board_rect: pygame.Rect,
    lane_base_offset_y: float,
    lane_spacing_y: float,
    gap_px: int,
    max_steps: int,
    row_slope_per_px: float,
) -> None:
    """Resolve cascading overlaps caused by pushing one card."""
    queue: list[Card] = [moved_card]
    steps = 0

    while queue and steps < max_steps:
        current = queue.pop(0)
        current_lane = _lane_index_for_rect(
            current.rect,
            board_rect,
            lane_base_offset_y,
            lane_spacing_y,
            row_slope_per_px,
        )
        _lock_rect_to_lane(
            current.rect,
            current_lane,
            board_rect,
            lane_base_offset_y,
            lane_spacing_y,
            row_slope_per_px,
        )
        for other in cards:
            if other is current:
                continue

            other_lane = _lane_index_for_rect(
                other.rect,
                board_rect,
                lane_base_offset_y,
                lane_spacing_y,
                row_slope_per_px,
            )
            if other_lane != current_lane:
                continue

            overlap = current.rect.clip(other.rect)
            if overlap.width <= 0 or overlap.height <= 0:
                continue

            current_area = max(1, current.rect.width * current.rect.height)
            overlap_ratio = (overlap.width * overlap.height) / current_area
            if overlap_ratio < TILE_COLLISION_MIN_OVERLAP_RATIO:
                continue

            _separate_along_row_axis(
                current.rect,
                other.rect,
                game_area,
                gap_px,
                row_slope_per_px,
            )
            _lock_rect_to_lane(
                current.rect,
                current_lane,
                board_rect,
                lane_base_offset_y,
                lane_spacing_y,
                row_slope_per_px,
            )
            _lock_rect_to_lane(
                other.rect,
                other_lane,
                board_rect,
                lane_base_offset_y,
                lane_spacing_y,
                row_slope_per_px,
            )
            queue.append(other)
            steps += 1
            if steps >= max_steps:
                break


def _resolve_drag_collisions(
    dragged_card: Card,
    cards: list[Card],
    game_area: pygame.Rect,
    board_rect: pygame.Rect,
    lane_base_offset_y: float,
    lane_spacing_y: float,
    row_slope_per_px: float,
) -> None:
    """Resolve overlaps by pushing along each row's angled horizontal axis."""
    passes = 0
    max_passes = max(1, TILE_COLLISION_CHAIN_MAX_STEPS // 2)

    while passes < max_passes:
        had_overlap = False
        dragged_lane = _lane_index_for_rect(
            dragged_card.rect,
            board_rect,
            lane_base_offset_y,
            lane_spacing_y,
            row_slope_per_px,
        )
        _lock_rect_to_lane(
            dragged_card.rect,
            dragged_lane,
            board_rect,
            lane_base_offset_y,
            lane_spacing_y,
            row_slope_per_px,
        )
        for other in reversed(cards):
            if other is dragged_card:
                continue

            other_lane = _lane_index_for_rect(
                other.rect,
                board_rect,
                lane_base_offset_y,
                lane_spacing_y,
                row_slope_per_px,
            )
            if other_lane != dragged_lane:
                continue

            overlap = dragged_card.rect.clip(other.rect)
            if overlap.width <= 0 or overlap.height <= 0:
                continue

            dragged_area = max(1, dragged_card.rect.width *
                               dragged_card.rect.height)
            overlap_ratio = (overlap.width * overlap.height) / dragged_area
            if overlap_ratio < TILE_COLLISION_MIN_OVERLAP_RATIO:
                continue

            had_overlap = True
            _separate_along_row_axis(
                dragged_card.rect,
                other.rect,
                game_area,
                TILE_COLLISION_GAP_PX,
                row_slope_per_px,
            )
            _lock_rect_to_lane(
                dragged_card.rect,
                dragged_lane,
                board_rect,
                lane_base_offset_y,
                lane_spacing_y,
                row_slope_per_px,
            )
            _lock_rect_to_lane(
                other.rect,
                other_lane,
                board_rect,
                lane_base_offset_y,
                lane_spacing_y,
                row_slope_per_px,
            )
            _resolve_push_chain(
                other,
                cards,
                game_area,
                board_rect,
                lane_base_offset_y,
                lane_spacing_y,
                TILE_COLLISION_GAP_PX,
                TILE_COLLISION_CHAIN_MAX_STEPS,
                row_slope_per_px,
            )

        if not had_overlap:
            break
        passes += 1


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
    cursor_kind = "arrow"

    try:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    except pygame.error:
        pass

    cards: list[Card] = []
    dragged_card: Card | None = None
    last_held_card: Card | None = None
    drag_contact_mode = False
    drag_contact_grace_until_ms = 0
    left_click_rearm_required = False
    reload_pending = False

    def _apply_contact_mode_for_dragged() -> None:
        if dragged_card is None:
            return
        dragged_card.snap_to_inclined_lanes(
            board_rect,
            BOARD_LANE_BASE_OFFSET_Y,
            BOARD_LANE_SPACING_Y,
            BOARD_LANE_SLOPE_PER_PX,
            BOARD_TOP_TIER_LEFT_PADDING,
            BOARD_TOP_TIER_RIGHT_PADDING,
            BOARD_BOTTOM_TIER_LEFT_PADDING,
            BOARD_BOTTOM_TIER_RIGHT_PADDING,
            BOARD_SNAP_MAX_DIST_X_PX,
            BOARD_SNAP_MAX_DIST_Y_PX,
            False,
        )
        _resolve_drag_collisions(
            dragged_card,
            cards,
            game_area,
            board_rect,
            BOARD_LANE_BASE_OFFSET_Y,
            BOARD_LANE_SPACING_Y,
            BOARD_LANE_SLOPE_PER_PX,
        )
        _handle_pushed_outside_falls(
            cards,
            board_rect,
            BOARD_LANE_BASE_OFFSET_Y,
            BOARD_LANE_SPACING_Y,
            BOARD_LANE_SLOPE_PER_PX,
        )
        dragged_card.sync_state_with_snap()

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
                            new_card.snapped_to_lane = True
                            new_card.stop_drag(game_area)
                            cards.append(new_card)
                    continue

                if left_click_rearm_required:
                    continue

                # Store the click position for processing game window clicks
                last_click_pos = event.pos
                for card in reversed(cards):
                    if card.rect.collidepoint(last_click_pos):
                        dragged_card = card
                        last_held_card = card
                        right_down = bool(pygame.mouse.get_pressed(3)[2])
                        drag_contact_mode = right_down
                        now_ms = pygame.time.get_ticks()
                        drag_contact_grace_until_ms = now_ms + DRAG_CONTACT_GRACE_MS if right_down else 0
                        cards.remove(card)
                        cards.append(card)
                        card.start_drag(last_click_pos)
                        card.hover_mode = not drag_contact_mode
                        card.sync_state_with_snap()
                        if drag_contact_mode:
                            _apply_contact_mode_for_dragged()
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if dragged_card is not None and pygame.mouse.get_pressed(3)[0]:
                    drag_contact_mode = True
                    drag_contact_grace_until_ms = pygame.time.get_ticks() + DRAG_CONTACT_GRACE_MS
                    dragged_card.hover_mode = False
                    _apply_contact_mode_for_dragged()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                left_click_rearm_required = False
                if dragged_card is not None:
                    contact_at_drop = drag_contact_mode or (
                        pygame.time.get_ticks() <= drag_contact_grace_until_ms
                    )
                    if contact_at_drop:
                        _apply_contact_mode_for_dragged()
                    else:
                        _start_fall_from_origin(
                            dragged_card,
                            "hover",
                            board_rect,
                            BOARD_LANE_BASE_OFFSET_Y,
                            BOARD_LANE_SPACING_Y,
                            BOARD_LANE_SLOPE_PER_PX,
                        )
                    dragged_card.stop_drag(board_rect)
                    dragged_card = None
                    drag_contact_mode = False
                    drag_contact_grace_until_ms = 0

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                if dragged_card is not None:
                    contact_at_drop = drag_contact_mode or (
                        pygame.time.get_ticks() <= drag_contact_grace_until_ms
                    )
                    if contact_at_drop:
                        _apply_contact_mode_for_dragged()
                    else:
                        _start_fall_from_origin(
                            dragged_card,
                            "hover",
                            board_rect,
                            BOARD_LANE_BASE_OFFSET_Y,
                            BOARD_LANE_SPACING_Y,
                            BOARD_LANE_SLOPE_PER_PX,
                        )

                    dragged_card.stop_drag(board_rect)
                    dragged_card = None
                    drag_contact_mode = False
                    drag_contact_grace_until_ms = 0

                    # Force true release/re-click behavior for left mouse button.
                    if pygame.mouse.get_pressed(3)[0]:
                        left_click_rearm_required = True

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
                    left_down = bool(event.buttons[0]) if len(
                        event.buttons) > 0 else False
                    right_down = bool(event.buttons[2]) if len(
                        event.buttons) > 2 else False
                    now_ms = pygame.time.get_ticks()
                    if left_down and right_down:
                        drag_contact_mode = True
                        drag_contact_grace_until_ms = now_ms + DRAG_CONTACT_GRACE_MS
                    elif left_down and now_ms <= drag_contact_grace_until_ms:
                        drag_contact_mode = True
                    else:
                        drag_contact_mode = False

                    dragged_card.update_drag_with_state(event.pos, board_rect)

                    if drag_contact_mode:
                        dragged_card.hover_mode = False
                        _apply_contact_mode_for_dragged()
                    else:
                        dragged_card.snapped_to_lane = False
                        dragged_card.hover_mode = True
                        dragged_card.sync_state_with_snap()

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
            last_held_card = None
            reload_pending = False

        # Update gravity for outside/falling tiles.
        for card in cards:
            card.update_fall(
                TILE_FALL_ACCEL_PX_PER_FRAME2,
                TILE_FALL_MAX_SPEED_PX_PER_FRAME,
            )

        # Main-window cursor feedback: hand only while left-dragging a card.
        next_cursor_kind = "arrow"
        if pygame.mouse.get_focused() and dragged_card is not None:
            if pygame.mouse.get_pressed(3)[0]:
                next_cursor_kind = "hand"

        if next_cursor_kind != cursor_kind:
            try:
                if next_cursor_kind == "hand":
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                cursor_kind = next_cursor_kind
            except pygame.error:
                pass

        # Render game area
        main_window.fill(BG_COLOR)
        pygame.draw.rect(main_window, TABLE_COLOR, game_area, border_radius=12)
        pygame.draw.rect(main_window, TABLE_BORDER,
                         game_area, width=3, border_radius=12)
        main_window.blit(board_surface, board_rect)

        label = font_hud.render("Game Area", True, (200, 200, 200))
        main_window.blit(label, (GAME_AREA_X, GAME_AREA_Y - 28))

        draw_cards = sorted(
            cards,
            key=lambda c: (
                _lane_index_for_rect(
                    c.rect,
                    board_rect,
                    BOARD_LANE_BASE_OFFSET_Y,
                    BOARD_LANE_SPACING_Y,
                    BOARD_LANE_SLOPE_PER_PX,
                ) if c.snapped_to_lane else 2,
                c.rect.centerx,
                c.rect.centery,
            ),
        )
        for card in draw_cards:
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
        debug_card = dragged_card if dragged_card is not None else last_held_card
        if debug_card is None:
            fall_debug = {
                "Tile": "-",
                "Falling": "no",
                "Velocity": "0.00 px/f",
                "Accel": f"{TILE_FALL_ACCEL_PX_PER_FRAME2:.2f} px/f^2",
                "Start Speed": f"{TILE_FALL_INITIAL_SPEED_PX_PER_FRAME:.2f} px/f",
                "Max Speed": f"{TILE_FALL_MAX_SPEED_PX_PER_FRAME:.2f} px/f",
            }
        else:
            fall_debug = {
                "Tile": f"{debug_card.number} {debug_card.color}",
                "Falling": "yes" if debug_card.falling else "no",
                "Velocity": f"{debug_card.fall_velocity_y:.2f} px/f",
                "Accel": f"{TILE_FALL_ACCEL_PX_PER_FRAME2:.2f} px/f^2",
                "Start Speed": f"{TILE_FALL_INITIAL_SPEED_PX_PER_FRAME:.2f} px/f",
                "Max Speed": f"{TILE_FALL_MAX_SPEED_PX_PER_FRAME:.2f} px/f",
            }

        dev_panel_surface = dev_panel.draw(dev_mouse_pos, fall_debug)
        dev_texture.update(dev_panel_surface)
        dev_renderer.clear()
        dev_renderer.blit(dev_texture)
        dev_renderer.present()

    pygame.quit()
