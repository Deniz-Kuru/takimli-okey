"""Main run loop orchestration."""

from __future__ import annotations

import pygame
import pygame._sdl2.video as sdl2_video

from .. import constants as c
from ..card import Card
from ..dev_panel import DevPanel
from ..dev_panel.constants import DEV_PANEL_WINDOW_H, DEV_PANEL_WINDOW_W
from .assets import init_sprites
from .events import (
    apply_contact_mode_for_dragged,
    can_use_right_click_mode,
    drop_dragged_card,
    handle_dev_click,
)
from .rendering import render_dev, render_main, update_cursor
from .runtime import build_fall_debug_payload, reload_runtime_constants


def run_game() -> None:
    pygame.init()

    main_window = pygame.display.set_mode((c.WINDOW_W, c.WINDOW_H))
    pygame.display.set_caption("Takimli Okey - Game")

    dev_window_sdl = sdl2_video.Window(
        title="Developer Panel", size=(DEV_PANEL_WINDOW_W, DEV_PANEL_WINDOW_H))
    dev_renderer = sdl2_video.Renderer(dev_window_sdl, vsync=True)
    dev_texture = sdl2_video.Texture(
        dev_renderer, (DEV_PANEL_WINDOW_W, DEV_PANEL_WINDOW_H))

    clock = pygame.time.Clock()
    _, board_surface, tile_size, sprites = init_sprites()
    font_num = pygame.font.SysFont("Arial", c.FONT_SIZE_NUM, bold=True)
    font_hud = pygame.font.SysFont("Arial", c.FONT_SIZE_HUD)

    game_area = pygame.Rect(c.GAME_AREA_X, c.GAME_AREA_Y,
                            c.GAME_AREA_W, c.GAME_AREA_H)
    board_rect = board_surface.get_rect(
        midtop=(game_area.centerx, game_area.top + c.BOARD_TOP_OFFSET_Y))

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

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.WINDOWENTER:
                window_obj = getattr(event, "window", None)
                if hasattr(window_obj, "id"):
                    hovered_window_id = window_obj.id
                elif isinstance(window_obj, int):
                    hovered_window_id = window_obj
            elif event.type == pygame.WINDOWLEAVE:
                hovered_window_id = None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
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
                    reload_pending = handle_dev_click(
                        event.pos, dev_panel, tile_size, game_area, board_rect, cards)
                    continue

                if left_click_rearm_required:
                    continue

                for card in reversed(cards):
                    if card.rect.collidepoint(event.pos):
                        dragged_card = card
                        last_held_card = card
                        right_down = bool(pygame.mouse.get_pressed(3)[2])
                        drag_contact_mode = right_down and can_use_right_click_mode(
                            card, board_rect)
                        now_ms = pygame.time.get_ticks()
                        drag_contact_grace_until_ms = (
                            now_ms + c.DRAG_CONTACT_GRACE_MS if drag_contact_mode else 0
                        )
                        cards.remove(card)
                        cards.append(card)
                        card.start_drag(event.pos)
                        card.hover_mode = not drag_contact_mode
                        card.sync_state_with_snap()
                        if drag_contact_mode:
                            apply_contact_mode_for_dragged(
                                dragged_card, cards, board_rect)
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if (
                    dragged_card is not None
                    and pygame.mouse.get_pressed(3)[0]
                    and can_use_right_click_mode(dragged_card, board_rect)
                ):
                    drag_contact_mode = True
                    drag_contact_grace_until_ms = pygame.time.get_ticks() + c.DRAG_CONTACT_GRACE_MS
                    dragged_card.hover_mode = False
                    apply_contact_mode_for_dragged(
                        dragged_card, cards, board_rect)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                left_click_rearm_required = False
                if dragged_card is not None:
                    drop_dragged_card(
                        dragged_card, drag_contact_mode, drag_contact_grace_until_ms, cards, board_rect)
                    dragged_card = None
                    drag_contact_mode = False
                    drag_contact_grace_until_ms = 0

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                if dragged_card is not None:
                    contact_active = drag_contact_mode or (
                        pygame.time.get_ticks() <= drag_contact_grace_until_ms
                    )
                    if contact_active:
                        drop_dragged_card(
                            dragged_card, drag_contact_mode, drag_contact_grace_until_ms, cards, board_rect)
                        dragged_card = None
                        drag_contact_mode = False
                        drag_contact_grace_until_ms = 0
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
                    near_board = can_use_right_click_mode(
                        dragged_card, board_rect)
                    now_ms = pygame.time.get_ticks()
                    if left_down and right_down and near_board:
                        drag_contact_mode = True
                        drag_contact_grace_until_ms = now_ms + c.DRAG_CONTACT_GRACE_MS
                    elif left_down and near_board and now_ms <= drag_contact_grace_until_ms:
                        drag_contact_mode = True
                    else:
                        drag_contact_mode = False

                    dragged_card.update_drag_with_state(event.pos, board_rect)
                    if drag_contact_mode:
                        dragged_card.hover_mode = False
                        apply_contact_mode_for_dragged(
                            dragged_card, cards, board_rect)
                    else:
                        dragged_card.snapped_to_lane = False
                        dragged_card.hover_mode = True
                        dragged_card.sync_state_with_snap()

        if reload_pending:
            reload_runtime_constants()
            main_window = pygame.display.set_mode((c.WINDOW_W, c.WINDOW_H))
            font_num = pygame.font.SysFont("Arial", c.FONT_SIZE_NUM, bold=True)
            font_hud = pygame.font.SysFont("Arial", c.FONT_SIZE_HUD)
            game_area = pygame.Rect(
                c.GAME_AREA_X, c.GAME_AREA_Y, c.GAME_AREA_W, c.GAME_AREA_H)
            _, board_surface, tile_size, sprites = init_sprites()
            board_rect = board_surface.get_rect(
                midtop=(game_area.centerx, game_area.top + c.BOARD_TOP_OFFSET_Y))
            cards.clear()
            dragged_card = None
            last_held_card = None
            reload_pending = False

        for card in cards:
            card.update_fall(c.TILE_FALL_ACCEL_PX_PER_FRAME2,
                             c.TILE_FALL_MAX_SPEED_PX_PER_FRAME)

        cursor_kind = update_cursor(cursor_kind, dragged_card)
        render_main(main_window, board_surface, board_rect,
                    game_area, cards, font_num, font_hud, sprites)

        debug_card = dragged_card if dragged_card is not None else last_held_card
        render_dev(dev_panel, dev_mouse_pos, build_fall_debug_payload(
            debug_card), dev_texture, dev_renderer)

    pygame.quit()
