"""Shared constants for the Takimli Okey app."""

from pathlib import Path

# Affects the size of the main game window in pixels (game window only, not including dev panel).
WINDOW_W, WINDOW_H = 1300, 750

# Game area (the green felt zone where cards "live")
# Affects the top-left position of the table/game area.
GAME_AREA_X, GAME_AREA_Y = 150, 150
# Affects the width/height of the table/game area rectangle.
GAME_AREA_W, GAME_AREA_H = 1000, 500

# Asset paths
# Affects where relative asset paths are resolved from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Affects which folder image assets are loaded from.
ASSETS_DIR = PROJECT_ROOT / "assets"
# Affects which image is used as the tile face sprite.
TILE_IMAGE_PATH = ASSETS_DIR / "tile.png"
# Affects which image is used as the board sprite.
BOARD_IMAGE_PATH = ASSETS_DIR / "board.png"

# Fallback dimensions if tile image cannot be loaded
# Affects fallback tile size when tile image cannot be loaded.
CARD_W, CARD_H = 60, 90

# Card layout
# Affects horizontal spacing used by grid-like tile layout helpers.
TILE_GAP_X = 3
# Affects vertical spacing used by grid-like tile layout helpers.
TILE_GAP_Y = 12
# Affects initial horizontal step between tiles during spawn.
TILE_INITIAL_STEP_X = 36

# Board placement and inclined-lane snap behavior
BOARD_TARGET_WIDTH = GAME_AREA_W  # Affects rendered board width after scaling.
# Affects vertical placement of board within the game area.
BOARD_TOP_OFFSET_Y = 110
# Affects left/right movement bounds for tile snapping on the board.
# BOARD_X_PADDING = 0
# Affects left bound of top tier lane snapping/insertion.
BOARD_TOP_TIER_LEFT_PADDING = 12
# Affects right bound of top tier lane snapping/insertion.
BOARD_TOP_TIER_RIGHT_PADDING = 30
# Affects left bound of bottom tier lane snapping/insertion.
BOARD_BOTTOM_TIER_LEFT_PADDING = 0
# Affects right bound of bottom tier lane snapping/insertion.
BOARD_BOTTOM_TIER_RIGHT_PADDING = 45

# Two inclined lanes where tiles snap vertically
# Affects Y position of the first inclined snap lane on the board.
BOARD_LANE_BASE_OFFSET_Y = 47
# Affects vertical distance between the two snap lanes.
BOARD_LANE_SPACING_Y = 83
# Affects incline amount of both lanes (Y change per pixel of X).
BOARD_LANE_SLOPE_PER_PX = 0.035
# Affects max horizontal distance from board side where auto-snap is allowed.
BOARD_SNAP_MAX_DIST_X_PX = 50
# Affects max vertical distance from a lane center where auto-snap is allowed.
BOARD_SNAP_MAX_DIST_Y_PX = 50

# Perspective / depth control point
# Affects the X coordinate that back-layer offsets are pulled toward.
VANISHING_POINT_X = GAME_AREA_X + 2*(GAME_AREA_W)
# Affects the Y coordinate that back-layer offsets are pulled toward.
VANISHING_POINT_Y = GAME_AREA_Y + (GAME_AREA_H // 2)

# Visual tuning for two-layer tile rendering
# Affects max offset distance of the back layer toward board center.
TILE_BACK_OFFSET_MAX_PX = 10
# Affects visual size multiplier while tile is in hover drag mode.
TILE_HOVER_SCALE = 1.06
# Affects darkness of the back tile layer (0 transparent, 255 black overlay).
TILE_BACK_SHADE_ALPHA = 0
# How strongly the tile color is tinted onto the tile image (0 = none, 255 = solid)
# Affects strength of color tint applied to tile image.
TILE_COLOR_TINT_ALPHA = 0
# Drag-highlight outline traced along the tile's opaque pixels
DRAG_OUTLINE_COLOR = (255, 220, 50)  # Affects color of drag selection outline.
# Affects thickness of drag selection outline in pixels.
DRAG_OUTLINE_THICKNESS = 3

# Number placement and style
TILE_NUMBER_MARGIN = 4  # Affects padding of number text from tile edges.

# Drag collision tuning
# Extra spacing maintained between tile fronts after collision resolution.
TILE_COLLISION_GAP_PX = 0
# Minimum overlap ratio required before push logic activates.
TILE_COLLISION_MIN_OVERLAP_RATIO = 0.08
# Max propagation steps when resolving push chain collisions.
TILE_COLLISION_CHAIN_MAX_STEPS = 40
# Grace time (ms) to keep contact mode active when left/right are not released simultaneously.
DRAG_CONTACT_GRACE_MS = 180

# Outside/fall behavior
# Affects how many pixels earlier right-side push-out fall starts (left side unchanged).
BOARD_RIGHT_EARLY_FALL_TRIGGER_PX = 25
# Affects starting downward speed when a tile begins falling outside.
TILE_FALL_INITIAL_SPEED_PX_PER_FRAME = 1.5
# Affects per-frame increase in downward speed while falling.
TILE_FALL_ACCEL_PX_PER_FRAME2 = 2
# Affects max downward speed reached during outside fall.
TILE_FALL_MAX_SPEED_PX_PER_FRAME = 50.0

# Colors
BG_COLOR = (30, 30, 30)  # Affects overall window background color.
TABLE_COLOR = (34, 100, 34)  # Affects fill color of the table/game area.
TABLE_BORDER = (20, 70, 20)  # Affects border color of the table/game area.
# Affects static tile border color when not dragging.
CARD_BORDER = (100, 100, 100)

# Ratio of card area that must remain inside the game area to stay NORMAL.
# Example: 0.5 means card becomes OUTSIDE when 50% or more is outside.
# Affects inside/outside state cutoff by required inside-area ratio.
OUTSIDE_THRESHOLD = 0.5

# The four okey tile colors and their display colors
TILE_COLORS = {
    "red": (210, 40, 40),  # Affects number/tint color for red tiles.
    "blue": (30, 80, 200),  # Affects number/tint color for blue tiles.
    "black": (20, 20, 20),  # Affects number/tint color for black tiles.
    "yellow": (200, 170, 0),  # Affects number/tint color for yellow tiles.
}

FONT_SIZE_NUM = 22  # Affects rendered tile number font size.
FONT_SIZE_HUD = 18  # Affects HUD/label font size.
