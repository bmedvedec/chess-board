"""
Input Handler for Chess GUI
---------------------------
Comprehensive mouse and keyboard input management for chess interactions.

This module implements a robust input handling system that supports multiple
interaction patterns for making chess moves. It manages selection state,
validates moves, provides visual feedback, and supports premove functionality.
"""

import chess
from typing import Optional, Tuple, List

from gui.board_gui import BoardGUI
from gui.board_state import BoardState
from gui.colors import Colors
from gui.promotion_dialog import PromotionDialog
from utils.config import Config


class InputHandler:
    """
    User input manager for chess piece interactions with premove support.

    Handles all mouse and keyboard input related to selecting and moving chess
    pieces. Supports both click-to-move and drag-and-drop interaction patterns,
    provides visual feedback, validates moves, and allows premove input during
    engine's turn.
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
            board_gui.screen, board_gui.piece_loader
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

        # Track how the last move was made (for animation decision)
        self.last_move_method: Optional[str] = None  # "click" or "drag"

        # Premove state - allows move input during engine's turn
        self.premove_queue: List[chess.Move] = []  # Queue of premoves
        self.virtual_board: Optional[chess.Board] = (
            None  # Simulated board for premove input
        )
        self.is_premove_mode: bool = False  # True when showing premove selection

        print("[InputHandler] Initialized successfully with premove support")

    def handle_mouse_click(
        self, pos: Tuple[int, int], engine_thinking: bool = False
    ) -> bool:
        """
        Process mouse click events for click-to-move interaction pattern.

        Implements a two-click system: first click selects a piece and shows
        legal moves, second click either moves to a destination, reselects a
        different piece, or deselects the current piece.

        With premove enabled, allows piece selection even during engine's turn.

        Args:
            pos (Tuple[int, int]): Mouse cursor position (x, y) in screen pixels
            engine_thinking (bool): True if engine is currently calculating a move

        Returns:
            bool: True if a move was successfully executed, False otherwise
        """
        print(f"[DEBUG] handle_mouse_click called - engine_thinking: {engine_thinking}")

        # Convert screen pixel coordinates to chess square index
        square = self.board_gui.coords_to_square(pos[0], pos[1])

        if square is None:
            # Click was outside the board boundaries - clear selection
            self._deselect()
            self._clear_premove()
            return False

        print(f"[DEBUG] Clicked square: {chess.square_name(square)}")

        # Determine what piece (if any) is at the clicked square
        piece = self.board_state.board.piece_at(square)
        print(f"[DEBUG] Piece at square: {piece.symbol() if piece else 'None'}")

        # Check if premove is enabled and engine is thinking
        if Config.ENABLE_PREMOVE and engine_thinking:
            print(f"[DEBUG] Routing to _handle_premove_click")
            # Premove mode - allow selection but don't execute moves
            return self._handle_premove_click(square, piece)

        # Normal gameplay - route to appropriate handler based on selection state
        if self.selected_square is None:
            # No piece currently selected - handle new selection
            return self._handle_selection(square, piece)
        else:
            # Piece already selected - handle move attempt or reselection
            return self._handle_move_or_reselect(square, piece)

    def _handle_premove_click(
        self, square: chess.Square, piece: Optional[chess.Piece]
    ) -> bool:
        human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK

        # Use visual board (real board + queued premoves) for both selection and legality
        visual_board = self.build_visual_board()

        if self.selected_square is None:
            # Selection phase: get piece from visual board
            piece = visual_board.piece_at(square)
            if piece is None or piece.color != human_color:
                return False

            self.selected_square = square
            self.selected_piece = piece
            self.is_premove_mode = True

            # Legal moves from this premove position
            visual_board.turn = human_color
            self.legal_moves_from_selected = [
                move for move in visual_board.legal_moves if move.from_square == square
            ]

            print(f"[Premove] Selected {piece.symbol()} at {chess.square_name(square)}")
            print(
                f"          Showing {len(self.legal_moves_from_selected)} legal moves"
            )
            return False

        else:
            # Second click: maybe reselect own piece on visual board
            piece = visual_board.piece_at(square)
            if piece is not None and piece.color == human_color:
                self._deselect()
                return self._handle_premove_click(square, piece)

            # Queue the move, checking legality on visual board
            promotion = None
            from_piece = self.selected_piece
            if from_piece and from_piece.piece_type == chess.PAWN:
                to_rank = chess.square_rank(square)
                if (from_piece.color == chess.WHITE and to_rank == 7) or (
                    from_piece.color == chess.BLACK and to_rank == 0
                ):
                    is_white = from_piece.color == chess.WHITE
                    promotion = self.promotion_dialog.show(is_white)
                    if promotion is None:
                        self._deselect()
                        return False

            move = chess.Move(self.selected_square, square, promotion)

            visual_board.turn = human_color
            if move not in visual_board.legal_moves:
                print(f"[Premove] Illegal premove on visual board: {move.uci()}")
                self._deselect()
                return False

            self.premove_queue.append(move)
            print(f"[Premove] Queued move: {move.uci()}")
            self._deselect()
            return False

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
        self.is_premove_mode = False  # Regular selection, not premove

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

        # Clicking empty square or opponent piece
        # If clicked on empty square or opponent's piece, try to make a move
        # If the move is illegal, it will deselect automatically
        # Mark this as a click-to-move method
        self.last_move_method = "click"

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

    def execute_next_premove_if_valid(self) -> bool:
        if not self.premove_queue:
            return False

        move = self.premove_queue[0]
        print(f"[Premove] Attempting to execute: {move.uci()}")

        if move in self.board_state.board.legal_moves:
            self.last_move_method = "click"
            move_san = self.board_state.board.san(move)
            success = self.board_state.make_move(move)

            if success:
                print(f"[Premove] ✅ Executed: {move_san} ({move.uci()})")
                self.premove_queue.pop(0)

                if not self.premove_queue:
                    self.virtual_board = None

                self._deselect()
                return True

        # Invalid or failed
        print(f"[Premove] ❌ No longer legal / failed")
        self.premove_queue.clear()
        self.virtual_board = None
        self._deselect()
        return False

    def has_premove(self) -> bool:
        """
        Check if a premove is currently queued.

        Returns:
            bool: True if premove is queued, False otherwise
        """
        return len(self.premove_queue) > 0

    def is_in_premove_mode(self) -> bool:
        """
        Check if currently in premove mode (selecting during engine's turn).

        Returns:
            bool: True if premove mode is active with a piece selected
        """
        return self.is_premove_mode and self.selected_square is not None

    def _clear_premove(self):
        """
        Clear all premove state.
        """
        self.premove_queue.clear()
        self.virtual_board = None
        self.is_premove_mode = False

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
        self.is_premove_mode = False

    def handle_mouse_down(self, pos: Tuple[int, int], engine_thinking: bool = False):
        """
        Handle mouse button press event - prepare for potential drag.

        Records the initial state when mouse button is pressed on a piece.
        With premove enabled, allows drag preparation even during engine's turn.

        Args:
            pos (Tuple[int, int]): Mouse cursor position (x, y) when button pressed
            engine_thinking (bool): True if engine is currently calculating
        """
        # Convert screen position to board square
        square = self.board_gui.coords_to_square(pos[0], pos[1])
        if square is None:
            return

        # Determine human player's color
        human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK

        if engine_thinking:
            if not Config.ENABLE_PREMOVE:
                return

            # Use visual board (real + queued premoves) for premove drag
            visual_board = self.build_visual_board()
            piece = visual_board.piece_at(square)

            # Allow drag preparation for human's pieces only in premove position
            if piece is not None and piece.color == human_color:
                self.drag_start_square = square
                self.drag_piece = piece
                self.drag_start_pos = pos
                self.mouse_moved = False
                print(f"[Premove] Prepared drag from {chess.square_name(square)}")
                return

            # No valid premove piece here
            return

        # Normal gameplay (not engine thinking) – keep existing logic
        piece = self.board_state.board.piece_at(square)
        if piece is not None and piece.color == self.board_state.board.turn:
            self.drag_start_square = square
            self.drag_piece = piece
            self.drag_start_pos = pos
            self.mouse_moved = False

    def handle_mouse_up(
        self, pos: Tuple[int, int], engine_thinking: bool = False
    ) -> bool:
        """
        Handle mouse button release event - complete drag or signal click.

        If a drag was in progress, completes the drag move. Otherwise, returns
        False to signal that this was a click (not a drag) and should be
        handled by the click handler.

        With premove enabled, queues the move if engine is thinking instead of executing.

        Args:
            pos (Tuple[int, int]): Mouse cursor position (x, y) when button released
            engine_thinking (bool): True if engine is currently calculating

        Returns:
            bool: True if drag move was completed/queued, False if this was a click
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
                self._deselect()
                return False  # Don't treat as click

            # Handle drop on same square (drag cancelled)
            if to_square == self.drag_start_square:
                print(f"[Input] Dropped on same square")
                self.drag_piece = None
                self.drag_start_square = None
                self.drag_start_pos = None
                # Keep selection for click-to-move
                return False  # Let click handler select the piece

            # Check if this is a premove drag
            if engine_thinking and Config.ENABLE_PREMOVE:
                # Build premove logic board: real board + all queued premoves
                logic_board = self._get_premove_logic_board()
                human_color = (
                    chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
                )

                # Get piece from logic board at drag start square
                from_piece = logic_board.piece_at(self.drag_start_square)
                if from_piece is None or from_piece.color != human_color:
                    # Not our piece in premove position -> invalid premove
                    self.drag_piece = None
                    self.drag_start_square = None
                    self.drag_start_pos = None
                    self._deselect()
                    return False

                promotion = None
                if from_piece.piece_type == chess.PAWN:
                    to_rank = chess.square_rank(to_square)
                    if (from_piece.color == chess.WHITE and to_rank == 7) or (
                        from_piece.color == chess.BLACK and to_rank == 0
                    ):
                        is_white = from_piece.color == chess.WHITE
                        promotion = self.promotion_dialog.show(is_white)
                        if promotion is None:
                            self._deselect()
                            self.drag_piece = None
                            self.drag_start_square = None
                            self.drag_start_pos = None
                            return False

                move = chess.Move(self.drag_start_square, to_square, promotion)

                # Check legality on logic board (premove position)
                if move not in logic_board.legal_moves:
                    print(
                        f"[Premove] Illegal premove drag on logic board: {move.uci()}"
                    )
                    self._deselect()
                    self.drag_piece = None
                    self.drag_start_square = None
                    self.drag_start_pos = None
                    return False

                # Queue premove
                self.premove_queue.append(move)

                if promotion:
                    print(
                        f"[Premove] Queued drag promotion: "
                        f"{chess.square_name(self.drag_start_square)} -> {chess.square_name(to_square)} "
                        f"({chess.PIECE_NAMES[promotion]})"
                    )
                else:
                    print(
                        f"[Premove] Queued drag move: "
                        f"{chess.square_name(self.drag_start_square)} -> {chess.square_name(to_square)}"
                    )

                # Clear drag state
                self.drag_piece = None
                self.drag_start_square = None
                self.drag_start_pos = None
                self._deselect()
                return True  # Handled as premove queue

            # Normal drag - attempt to execute the move immediately
            self.last_move_method = "drag"
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

    def handle_mouse_motion(self, pos: Tuple[int, int], engine_thinking: bool = False):
        """
        Handle mouse movement - initiate or update drag operation.

        Detects when mouse has moved enough to start a drag (>5 pixels),
        then tracks the cursor position for visual feedback.
        With premove enabled, supports dragging during engine's turn.

        Args:
            pos (Tuple[int, int]): Current mouse cursor position (x, y)
            engine_thinking (bool): True if engine is currently calculating
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

                    # Set premove mode if engine is thinking
                    self.is_premove_mode = engine_thinking and Config.ENABLE_PREMOVE

                    # Calculate legal moves - fix for premove during engine's turn
                    if self.is_premove_mode:
                        # During engine's turn, flip board to get OUR legal moves
                        temp_board = self.board_state.board.copy()
                        temp_board.turn = self.drag_piece.color
                        self.legal_moves_from_selected = [
                            move
                            for move in temp_board.legal_moves
                            if move.from_square == self.drag_start_square
                        ]
                    else:
                        # Normal play - use current board
                        self.legal_moves_from_selected = [
                            move
                            for move in self.board_state.board.legal_moves
                            if move.from_square == self.drag_start_square
                        ]

                    if self.is_premove_mode:
                        print(
                            f"[Premove] Started dragging {self.drag_piece.symbol()} from {chess.square_name(self.drag_start_square)}"
                        )
                    else:
                        print(
                            f"[Input] Started dragging {self.drag_piece.symbol()} from {chess.square_name(self.drag_start_square)}"
                        )

        # Update cursor position if already dragging
        # This allows the dragged piece to follow the cursor smoothly
        if self.dragging:
            self.drag_pos = pos

    def get_last_move_method(self) -> Optional[str]:
        """
        Get the method used for the last move.

        Returns:
            Optional[str]: "click" if move was made via click-to-move,
                          "drag" if move was made via drag-and-drop,
                          None if no move has been made yet
        """
        return self.last_move_method

    def clear_move_method(self):
        """
        Clear the last move method tracking.

        Should be called after consuming the move method information.
        """
        self.last_move_method = None

    def render_square_highlights(self, engine_thinking: bool = False):
        """
        Render square highlight overlays (drawn UNDER pieces).

        Draws semi-transparent colored overlays on selected squares and premove
        queued squares. This should be called before drawing pieces.

        Args:
            engine_thinking (bool): True if engine is currently calculating
        """
        if self.selected_square is not None:
            # Highlight the selected square with semi-transparent overlay
            # Use different color for premove mode
            if self.is_premove_mode:
                # Slightly different color for premove (more blue-ish)
                highlight_color = (150, 170, 100, 180)
            else:
                highlight_color = Colors.SELECTED_SQUARE

            self.board_gui.highlight_square(self.selected_square, highlight_color)

        # Also highlight queued premove if it exists (but don't show dots again)
        if self.has_premove() and self.selected_square is None:
            premove_highlight = (100, 150, 200, 150)
            for move in self.premove_queue:
                self.board_gui.highlight_square(move.from_square, premove_highlight)
                self.board_gui.highlight_square(move.to_square, premove_highlight)

    def render_legal_move_dots(self, engine_thinking: bool = False):
        """
        Render legal move indicators (drawn OVER pieces).

        Draws dots and circles showing where the selected piece can move.
        This should be called after drawing pieces so dots are visible on top.

        Args:
            engine_thinking (bool): True if engine is currently calculating
        """
        # Draw legal move indicators (dots on empty squares, circles on captures)
        # ALWAYS show if we have legal moves calculated, regardless of whose turn it is
        if self.selected_square is not None and self.legal_moves_from_selected:
            self.board_gui.draw_legal_move_indicators(
                self.legal_moves_from_selected, self.board_state.board
            )

    def render_selection_highlights(self, engine_thinking: bool = False):
        """
        Render visual feedback for selected piece and legal moves.

        DEPRECATED: Use render_square_highlights() and render_legal_move_dots() separately
        for proper layering. This method calls both for backwards compatibility.

        Args:
            engine_thinking (bool): True if engine is currently calculating
        """
        # Call both methods for backwards compatibility
        self.render_square_highlights(engine_thinking)
        self.render_legal_move_dots(engine_thinking)

    def render_dragged_piece(self):
        """
        Render the piece currently being dragged (if any).

        Draws the dragged piece image centered on the cursor position.
        This provides visual feedback during drag operations, making the
        piece appear to "follow" the mouse.
        """
        if self.dragging and self.drag_piece is not None and self.drag_pos is not None:
            # Get piece image using piece_loader
            image = self.board_gui.piece_loader.get_piece_image(
                self.drag_piece, self.board_gui.square_size
            )

            if image:
                # Draw centered on cursor position
                x = self.drag_pos[0] - image.get_width() // 2
                y = self.drag_pos[1] - image.get_height() // 2

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

        Clears all selection, drag, premove, and interaction state, returning
        the input handler to its initial state.
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

        # Clear premove state
        self._clear_premove()

        # Clear move method tracking
        self.last_move_method = None

        print("[InputHandler] State reset (including premove)")

    def soft_reset(self):
        """
        Soft reset - clears drag and selection but preserves premove queue.

        Used after engine moves to clear any pending input state while keeping
        queued premoves for immediate execution.
        """
        # Clear drag state
        self.dragging = False
        self.drag_piece = None
        self.drag_start_square = None
        self.drag_pos = None
        self.drag_start_pos = None
        self.mouse_moved = False

        # Clear selection (in case partial premove selection)
        self._deselect()

        # Clear move method tracking
        self.last_move_method = None

        print("[InputHandler] Soft reset (cleared selection)")

    def build_visual_board(self) -> chess.Board:
        """
        Build a board representing what should be visually shown:
        current real position + all queued premoves applied in order.
        """
        temp = self.board_state.board.copy()

        human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK

        for move in self.premove_queue:
            try:
                temp.turn = human_color
                temp.push(move)
            except Exception as e:
                print(f"[Premove] visual push failed for {move.uci()}: {e}")
                break

        return temp

    def _get_premove_logic_board(self) -> chess.Board:
        """
        Board used for premove legality: real board + all queued premoves.
        """
        temp = self.board_state.board.copy()
        human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK

        # Always set turn to human before applying each queued premove
        for move in self.premove_queue:
            temp.turn = human_color
            temp.push(move)

        # After applying premoves, it's still human's turn for the next premove
        temp.turn = human_color
        return temp
