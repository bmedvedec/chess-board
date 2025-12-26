"""
Input Handler for Chess GUI
---------------------------
Comprehensive mouse and keyboard input management for chess interactions.

This module implements a robust input handling system that supports multiple
interaction patterns for making chess moves. It manages selection state,
validates moves, and provides visual feedback to the user.
"""

import chess
from typing import Optional, Tuple, List

from gui.board_gui import BoardGUI
from gui.board_state import BoardState
from gui.colors import Colors
from gui.promotion_dialog import PromotionDialog


class InputHandler:
    """
    User input manager for chess piece interactions.

    Handles all mouse and keyboard input related to selecting and moving chess
    pieces. Supports both click-to-move and drag-and-drop interaction patterns,
    provides visual feedback, and validates moves before execution.
    """

    def __init__(self, board_gui: BoardGUI, board_state: BoardState):
        """
        Initialize the input handler with GUI and game state references.

        Args:
            board_gui (BoardGUI): Board renderer for coordinate conversion and visual feedback
            board_state (BoardState): Game state manager for move validation and execution
        """
        # Store references to GUI and game state
        self.board_gui = board_gui
        self.board_state = board_state

        # Initialize promotion dialog
        self.promotion_dialog = PromotionDialog(
            board_gui.screen, board_gui.piece_images
        )

        # Selection state (click-to-move mode)
        # These track which piece the player has selected via clicking
        self.selected_square: Optional[chess.Square] = None  # Square of selected piece
        self.selected_piece: Optional[chess.Piece] = None  # The selected piece itself
        self.legal_moves_from_selected: List[chess.Move] = []  # Cached legal moves

        # Drag and drop state
        # These track the current drag operation (if any)
        self.dragging = False  # True when actively dragging a piece
        self.drag_piece: Optional[chess.Piece] = None  # Piece being dragged
        self.drag_start_square: Optional[chess.Square] = None  # Origin square
        self.drag_pos: Optional[Tuple[int, int]] = None  # Current cursor position
        self.drag_start_pos: Optional[Tuple[int, int]] = (
            None  # Initial mouse down position
        )
        self.mouse_moved = False  # True if mouse moved since button press

        print("[InputHandler] Initialized successfully")

    def handle_mouse_click(self, pos: Tuple[int, int]) -> bool:
        """
        Process mouse click events for click-to-move interaction pattern.

        Implements a two-click system: first click selects a piece and shows
        legal moves, second click either moves to a destination, reselects a
        different piece, or deselects the current piece.

        Args:
            pos (Tuple[int, int]): Mouse cursor position (x, y) in screen pixels

        Returns:
            bool: True if a move was successfully executed, False otherwise
        """
        # Convert screen pixel coordinates to chess square index
        square = self.board_gui.coords_to_square(pos[0], pos[1])

        if square is None:
            # Click was outside the board boundaries - clear selection
            self._deselect()
            return False

        # Determine what piece (if any) is at the clicked square
        piece = self.board_state.board.piece_at(square)

        # Route to appropriate handler based on selection state
        if self.selected_square is None:
            # No piece currently selected - handle new selection
            return self._handle_selection(square, piece)
        else:
            # Piece already selected - handle move attempt or reselection
            return self._handle_move_or_reselect(square, piece)

    def _handle_selection(
        self, square: chess.Square, piece: Optional[chess.Piece]
    ) -> bool:
        """
        Handle initial piece selection when no piece is currently selected.

        Validates that a valid piece can be selected (must be player's own piece),
        then updates selection state and calculates legal moves for visual feedback.

        Args:
            square (chess.Square): Square index that was clicked
            piece (Optional[chess.Piece]): Piece at the clicked square, or None

        Returns:
            bool: Always returns False (selection doesn't make a move)
        """
        # Empty square clicked - nothing to select
        if piece is None:
            return False

        # Opponent's piece clicked - not allowed to select
        if piece.color != self.board_state.board.turn:
            print(
                f"[Input] Cannot select opponent's piece at {chess.square_name(square)}"
            )
            return False

        # Valid piece to select - update selection state
        self.selected_square = square
        self.selected_piece = piece

        # Calculate and cache all legal moves from this square
        # This is used for highlighting and move validation
        self.legal_moves_from_selected = [
            move
            for move in self.board_state.board.legal_moves
            if move.from_square == square
        ]

        # Log selection for debugging
        print(f"[Input] Selected {piece.symbol()} at {chess.square_name(square)}")
        print(f"        Legal moves: {len(self.legal_moves_from_selected)}")

        return False

    def _handle_move_or_reselect(
        self, square: chess.Square, piece: Optional[chess.Piece]
    ) -> bool:
        """
        Handle second click when a piece is already selected.

        Implements smart click behavior: deselect if clicking same square,
        reselect if clicking different own piece, or attempt move otherwise.

        Args:
            square (chess.Square): Square that was clicked
            piece (Optional[chess.Piece]): Piece at the clicked square, or None

        Returns:
            bool: True if a move was successfully made, False otherwise
        """
        # Clicking the same square - toggle selection off
        if square == self.selected_square:
            print(f"[Input] Deselected {chess.square_name(square)}")
            self._deselect()
            return False

        # Clicking a different piece of our own color - reselect it
        # This allows quick piece switching without deselecting first
        if piece is not None and piece.color == self.board_state.board.turn:
            print(f"[Input] Reselecting piece at {chess.square_name(square)}")
            self._deselect()
            return self._handle_selection(square, piece)

        # Clicking empty square or opponent piece - attempt move
        return self._try_make_move(square)

    def _try_make_move(self, to_square: chess.Square) -> bool:
        """
        Attempt to execute a move from the selected square to a target square.

        Validates the move, handles pawn promotion, executes if legal, and
        updates game state. Provides console feedback on success or failure.

        Args:
            to_square (chess.Square): Destination square for the move

        Returns:
            bool: True if move was successfully executed, False if move was illegal
        """
        # Safety check - should always have a selected square at this point
        if self.selected_square is None:
            return False

        # Construct move object from source and destination
        move = chess.Move(self.selected_square, to_square)

        # Handle pawn promotion special case
        if self._is_promotion_move(move):
            # Show promotion dialog
            piece = self.board_state.board.piece_at(self.selected_square)
            is_white = piece.color == chess.WHITE if piece else True

            print("[Input] Pawn promotion detected - showing dialog")
            promotion_piece = self.promotion_dialog.show(is_white)

            if promotion_piece is None:
                # Dialog was cancelled (window closed)
                print("[Input] Promotion cancelled")
                self._deselect()
                return False

            # Create move with chosen promotion piece
            move = chess.Move(
                self.selected_square, to_square, promotion=promotion_piece
            )
            promotion_names = {
                chess.QUEEN: "Queen",
                chess.ROOK: "Rook",
                chess.BISHOP: "Bishop",
                chess.KNIGHT: "Knight",
            }
            print(f"[Input] Promoting to {promotion_names[promotion_piece]}")

        # Validate move legality
        if move not in self.board_state.board.legal_moves:
            print(f"[Input] Illegal move: {move.uci()}")
            self._deselect()
            return False

        # Move is legal - execute it
        # Get SAN notation BEFORE making the move (depends on current position)
        move_san = self.board_state.board.san(move)
        success = self.board_state.make_move(move)

        if success:
            # Move executed successfully
            print(f"[Input] Move made: {move_san} ({move.uci()})")
            print(f"        Status: {self.board_state.get_game_status()}")
            self._deselect()
            return True
        else:
            # Move execution failed (shouldn't happen after validation)
            print(f"[Input] Failed to make move: {move.uci()}")
            self._deselect()
            return False

    def _is_promotion_move(self, move: chess.Move) -> bool:
        """
        Detect whether a move is a pawn promotion.

        Checks if the moving piece is a pawn and if it's reaching the
        opposite end of the board (rank 8 for white, rank 1 for black).

        Args:
            move (chess.Move): Move object to check

        Returns:
            bool: True if this move is a pawn promotion, False otherwise
        """
        # Get the piece being moved
        piece = self.board_state.board.piece_at(move.from_square)
        if piece is None or piece.piece_type != chess.PAWN:
            return False

        # Check if pawn is reaching the promotion rank
        to_rank = chess.square_rank(move.to_square)
        if piece.color == chess.WHITE:
            return to_rank == 7  # Rank 8 (0-indexed as 7)
        else:
            return to_rank == 0  # Rank 1 (0-indexed as 0)

    def _deselect(self):
        """
        Clear all piece selection state.

        Resets the selection state variables, removing highlights and
        clearing cached legal moves. Used when deselecting a piece or
        after making a move.
        """
        self.selected_square = None
        self.selected_piece = None
        self.legal_moves_from_selected = []

    def handle_mouse_down(self, pos: Tuple[int, int]):
        """
        Handle mouse button press event - prepare for potential drag.

        Records the initial state when mouse button is pressed on a piece.

        Args:
            pos (Tuple[int, int]): Mouse cursor position (x, y) when button pressed
        """
        # Convert screen position to board square
        square = self.board_gui.coords_to_square(pos[0], pos[1])
        if square is None:
            return

        # Check what's at the clicked square
        piece = self.board_state.board.piece_at(square)

        # Prepare for potential drag if clicking on player's own piece
        if piece is not None and piece.color == self.board_state.board.turn:
            self.drag_start_square = square
            self.drag_piece = piece
            self.drag_start_pos = pos
            self.mouse_moved = False
            # Don't start dragging yet - wait to see if mouse moves
            # This allows clicks without movement to work as click-to-move

    def handle_mouse_up(self, pos: Tuple[int, int]) -> bool:
        """
        Handle mouse button release event - complete drag or signal click.

        If a drag was in progress, completes the drag move. Otherwise, returns
        False to signal that this was a click (not a drag) and should be
        handled by the click handler.

        Args:
            pos (Tuple[int, int]): Mouse cursor position (x, y) when button released

        Returns:
            bool: True if drag move was completed, False if this was a click
        """
        # Check if we were actively dragging
        if self.dragging:
            # Determine where the piece was dropped
            to_square = self.board_gui.coords_to_square(pos[0], pos[1])

            # End drag state
            self.dragging = False
            self.drag_pos = None
            self.mouse_moved = False

            # Handle drop outside board
            if to_square is None or self.drag_start_square is None:
                print(f"[Input] Dropped outside board")
                self.drag_piece = None
                self.drag_start_square = None
                self.drag_start_pos = None
                return False  # Don't treat as click

            # Handle drop on same square (drag cancelled)
            if to_square == self.drag_start_square:
                print(f"[Input] Dropped on same square")
                self.drag_piece = None
                self.drag_start_square = None
                self.drag_start_pos = None
                return False  # Let click handler select the piece

            # Attempt to execute the dragged move
            # This uses the same validation and execution as click-to-move
            move_made = self._try_make_move(to_square)

            # Clear all drag state
            self.drag_piece = None
            self.drag_start_square = None
            self.drag_start_pos = None

            return move_made  # True if move succeeded, False if illegal

        # No drag was in progress - this is a regular click
        # Clear any drag preparation state
        self.drag_start_square = None
        self.drag_piece = None
        self.drag_start_pos = None
        self.mouse_moved = False
        return False  # Signal to main loop to process as click

    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """
        Handle mouse movement - initiate or update drag operation.

        Detects when mouse has moved enough to start a drag (>5 pixels),
        then tracks the cursor position for visual feedback.

        Args:
            pos (Tuple[int, int]): Current mouse cursor position (x, y)
        """
        # Check if we should initiate a drag operation
        if self.drag_start_pos is not None and not self.dragging:
            # Calculate Euclidean distance from initial position
            dx = pos[0] - self.drag_start_pos[0]
            dy = pos[1] - self.drag_start_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5

            # 5-pixel threshold prevents accidental drags from small hand movements
            if distance > 5:
                self.dragging = True
                self.mouse_moved = True
                self.drag_pos = pos

                # Select the piece being dragged to show legal move indicators
                if self.drag_start_square is not None and self.drag_piece is not None:
                    self.selected_square = self.drag_start_square
                    self.selected_piece = self.drag_piece
                    # Cache legal moves for highlighting
                    self.legal_moves_from_selected = [
                        move
                        for move in self.board_state.board.legal_moves
                        if move.from_square == self.drag_start_square
                    ]
                    print(
                        f"[Input] Started dragging {self.drag_piece.symbol()} from {chess.square_name(self.drag_start_square)}"
                    )

        # Update cursor position if already dragging
        # This allows the dragged piece to follow the cursor smoothly
        if self.dragging:
            self.drag_pos = pos

    def render_selection_highlights(self):
        """
        Render visual feedback for selected piece and legal moves.

        Draws highlight overlays on the board to show the user which piece
        is selected and where it can move.
        """
        if self.selected_square is not None:
            # Highlight the selected square with semi-transparent overlay
            self.board_gui.highlight_square(
                self.selected_square, Colors.SELECTED_SQUARE
            )

            # Draw legal move indicators (dots on empty squares, circles on captures)
            # Passes board_state for capture detection
            self.board_gui.draw_legal_move_indicators(
                self.legal_moves_from_selected, self.board_state.board
            )

    def render_dragged_piece(self):
        """
        Render the piece currently being dragged (if any).

        Draws the dragged piece image centered on the cursor position.
        This provides visual feedback during drag operations, making the
        piece appear to "follow" the mouse.
        """
        if self.dragging and self.drag_piece is not None and self.drag_pos is not None:
            # Look up the piece image for this piece
            symbol = self.drag_piece.symbol()
            if symbol in self.board_gui.piece_images:
                image = self.board_gui.piece_images[symbol]

                # Calculate position to center image on cursor
                x = self.drag_pos[0] - image.get_width() // 2
                y = self.drag_pos[1] - image.get_height() // 2

                # Blit piece image at cursor position
                self.board_gui.screen.blit(image, (x, y))

    def is_square_selected(self) -> bool:
        """
        Check if any square is currently selected.

        Returns:
            bool: True if a piece is selected, False otherwise
        """
        return self.selected_square is not None

    def get_selected_square(self) -> Optional[chess.Square]:
        """
        Get the currently selected square index.

        Returns:
            Optional[chess.Square]: Selected square index (0-63), or None if no selection
        """
        return self.selected_square

    def reset(self):
        """
        Reset all input handler state (for new game or board reset).

        Clears all selection, drag, and interaction state, returning the
        input handler to its initial state.
        """
        # Clear selection state
        self._deselect()

        # Clear drag state
        self.dragging = False
        self.drag_piece = None
        self.drag_start_square = None
        self.drag_pos = None
        self.drag_start_pos = None
        self.mouse_moved = False

        print("[InputHandler] State reset")
