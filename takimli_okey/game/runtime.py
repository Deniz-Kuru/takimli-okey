"""Runtime helpers for constants reload and dev debug payloads."""

from __future__ import annotations

import importlib

from .. import card as card_module
from .. import constants as c
from ..card import Card


def reload_runtime_constants() -> None:
    importlib.reload(c)

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
        if hasattr(c, name):
            setattr(card_module, name, getattr(c, name))


def build_fall_debug_payload(debug_card: Card | None) -> dict[str, str]:
    if debug_card is None:
        return {
            "Tile": "-",
            "Falling": "no",
            "Velocity": "0.00 px/f",
            "Accel": f"{c.TILE_FALL_ACCEL_PX_PER_FRAME2:.2f} px/f^2",
            "Start Speed": f"{c.TILE_FALL_INITIAL_SPEED_PX_PER_FRAME:.2f} px/f",
            "Max Speed": f"{c.TILE_FALL_MAX_SPEED_PX_PER_FRAME:.2f} px/f",
        }

    return {
        "Tile": f"{debug_card.number} {debug_card.color}",
        "Falling": "yes" if debug_card.falling else "no",
        "Velocity": f"{debug_card.fall_velocity_y:.2f} px/f",
        "Accel": f"{c.TILE_FALL_ACCEL_PX_PER_FRAME2:.2f} px/f^2",
        "Start Speed": f"{c.TILE_FALL_INITIAL_SPEED_PX_PER_FRAME:.2f} px/f",
        "Max Speed": f"{c.TILE_FALL_MAX_SPEED_PX_PER_FRAME:.2f} px/f",
    }
