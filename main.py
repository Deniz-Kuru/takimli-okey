"""
Takimli Okey - Basic Pygame Starter
====================================
Run with:  python main.py

Controls
--------
Left-click + drag : move a card
Release            : drop the card

Card states
-----------
- NORMAL  : card is inside the game area  (full color)
- OUTSIDE : card has been moved outside the game area (greyed out)
"""

import pygame
import sys

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WINDOW_W, WINDOW_H = 1100, 750

# Game area (the green felt zone where cards "live")
GAME_AREA_X, GAME_AREA_Y = 50, 150
GAME_AREA_W, GAME_AREA_H = 1000, 500

# Card dimensions
CARD_W, CARD_H = 60, 90

# Colors
BG_COLOR        = (30,  30,  30)
TABLE_COLOR     = (34, 100,  34)   # dark green felt
TABLE_BORDER    = (20,  70,  20)
CARD_BACK       = (220, 220, 220)  # off-white card face
CARD_BORDER     = (100, 100, 100)
OUTSIDE_OVERLAY = (160, 160, 160)  # greyscale tint when outside

# The four okey tile colors and their display colors
TILE_COLORS = {
    "red":    (210,  40,  40),
    "blue":   ( 30,  80, 200),
    "black":  ( 20,  20,  20),
    "yellow": (200, 170,   0),
}

FONT_SIZE_NUM  = 22
FONT_SIZE_HUD  = 18

# ---------------------------------------------------------------------------
# Card class
# ---------------------------------------------------------------------------

class Card:
    """Represents a single okey tile / card."""

    # Possible states
    NORMAL  = "normal"
    OUTSIDE = "outside"

    def __init__(self, number: int, color: str, x: int, y: int):
        self.number = number          # 1-13
        self.color  = color           # one of TILE_COLORS keys
        self.rect   = pygame.Rect(x, y, CARD_W, CARD_H)
        self.state  = Card.NORMAL
        self.dragging   = False
        self._drag_offset = (0, 0)   # mouse offset from card top-left when drag starts

    # ------------------------------------------------------------------
    # Drag helpers
    # ------------------------------------------------------------------

    def start_drag(self, mouse_pos: tuple[int, int]) -> None:
        self.dragging = True
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
        self._update_state(game_area)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _update_state(self, game_area: pygame.Rect) -> None:
        if game_area.contains(self.rect):
            self.state = Card.NORMAL
        else:
            self.state = Card.OUTSIDE

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Card shadow
        shadow_rect = self.rect.move(3, 3)
        pygame.draw.rect(surface, (0, 0, 0, 80), shadow_rect, border_radius=6)

        # Card background
        if self.state == Card.OUTSIDE:
            bg = OUTSIDE_OVERLAY
        else:
            bg = CARD_BACK
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)

        # Card border (highlight when dragging)
        border_col = (255, 220, 50) if self.dragging else CARD_BORDER
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=6)

        # Number text
        if self.state == Card.OUTSIDE:
            text_color = (100, 100, 100)
        else:
            text_color = TILE_COLORS[self.color]

        num_surf = font.render(str(self.number), True, text_color)
        # Top-left corner
        surface.blit(num_surf, (self.rect.x + 4, self.rect.y + 4))
        # Bottom-right corner (rotated 180°)
        num_surf_rot = pygame.transform.rotate(num_surf, 180)
        surface.blit(
            num_surf_rot,
            (
                self.rect.right - num_surf_rot.get_width() - 4,
                self.rect.bottom - num_surf_rot.get_height() - 4,
            ),
        )

        # Color pip in the center
        pip_radius = 8
        pip_color  = (130, 130, 130) if self.state == Card.OUTSIDE else TILE_COLORS[self.color]
        pygame.draw.circle(
            surface,
            pip_color,
            self.rect.center,
            pip_radius,
        )


# ---------------------------------------------------------------------------
# Helper: build the starting hand of cards
# ---------------------------------------------------------------------------

def create_cards() -> list[Card]:
    """Create one row of cards per color, arranged inside the game area."""
    cards: list[Card] = []
    colors = list(TILE_COLORS.keys())
    start_x = GAME_AREA_X + 20
    start_y = GAME_AREA_Y + 30
    gap_x = CARD_W + 8
    gap_y = CARD_H + 12

    for row, color in enumerate(colors):
        for col in range(13):
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            cards.append(Card(number=col + 1, color=color, x=x, y=y))
    return cards


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Takimli Okey")
    clock = pygame.time.Clock()

    font_num = pygame.font.SysFont("Arial", FONT_SIZE_NUM, bold=True)
    font_hud = pygame.font.SysFont("Arial", FONT_SIZE_HUD)

    game_area = pygame.Rect(GAME_AREA_X, GAME_AREA_Y, GAME_AREA_W, GAME_AREA_H)
    cards     = create_cards()
    dragged_card: Card | None = None

    running = True
    while running:
        clock.tick(60)

        # ----------------------------------------------------------------
        # Events
        # ----------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Pick up the topmost card under the cursor
                mouse_pos = event.pos
                for card in reversed(cards):
                    if card.rect.collidepoint(mouse_pos):
                        dragged_card = card
                        # Bring to front
                        cards.remove(card)
                        cards.append(card)
                        card.start_drag(mouse_pos)
                        break

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragged_card is not None:
                    dragged_card.stop_drag(game_area)
                    dragged_card = None

            elif event.type == pygame.MOUSEMOTION:
                if dragged_card is not None:
                    dragged_card.update_drag(event.pos)

        # ----------------------------------------------------------------
        # Draw
        # ----------------------------------------------------------------
        screen.fill(BG_COLOR)

        # Game area background
        pygame.draw.rect(screen, TABLE_COLOR, game_area, border_radius=12)
        pygame.draw.rect(screen, TABLE_BORDER, game_area, width=3, border_radius=12)

        # Game area label
        label = font_hud.render("Game Area  (drag cards outside to change their state)", True, (200, 200, 200))
        screen.blit(label, (GAME_AREA_X, GAME_AREA_Y - 28))

        # Cards (draw non-dragged first, then dragged on top)
        for card in cards:
            card.draw(screen, font_num)

        # HUD: count cards by state
        normal_count  = sum(1 for c in cards if c.state == Card.NORMAL)
        outside_count = sum(1 for c in cards if c.state == Card.OUTSIDE)
        hud = font_hud.render(
            f"Inside: {normal_count}   Outside (greyed): {outside_count}   |   ESC to quit",
            True,
            (220, 220, 220),
        )
        screen.blit(hud, (GAME_AREA_X, GAME_AREA_Y + GAME_AREA_H + 16))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
