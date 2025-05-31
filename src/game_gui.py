import sys
import os
import math
import time
import weakref
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene, QGraphicsObject,
    QFrame, QSizePolicy, QAction, QDialog, QTextEdit, QInputDialog
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QPropertyAnimation, QTimer, QObject
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor

# Import game components
from card import Card
from deck import Deck
from player import Player
from game_engine_controls import GuiGameEngine


def _load_card_pixmap(card):
    """Load card image with proper naming convention"""
    # Map suit names to file abbreviations
    suit_map = {
        's': 'S',  # Spades
        'h': 'H',  # Hearts
        'd': 'D',  # Diamonds
        'c': 'C'  # Clubs
    }

    rank_map = {
        '10': '10',
        'J': 'J',
        'Q': 'Q',
        'K': 'K',
        'A': 'A'
    }

    # Get normalized rank and suit
    rank = str(card.rank).upper()
    suit = suit_map.get(card.suit.lower(), card.suit.upper())

    # Handle numeric ranks
    if rank in ('10', '11', '12', '13'):
        rank = rank_map.get(rank, rank)
    elif rank == '1':  # Ace
        rank = 'A'

    filename = f"{rank}{suit}.png"
    cards_dir = os.path.join(os.path.dirname(__file__), "cards", "Rust")
    path = os.path.join(cards_dir, filename)

    # Load pixmap with fallback
    pixmap = QPixmap(path)
    if pixmap.isNull():
        # Create blank card as fallback
        pixmap = QPixmap(140, 200)
        pixmap.fill(Qt.transparent)
    else:
        pixmap = pixmap.scaled(
            140, 200,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
    return pixmap


class PokerGameGUI(QMainWindow):
    SHIFT_DISTANCE = 50
    CLICK_COOLDOWN = 0.3
    ANIM_DURATION = 200

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker")
        self.resize(1100, 600)

        # Game setup
        self.deck = Deck()
        self.players = [
            Player(1000, "You", True),
            Player(1000, "Bot 1", False),
            Player(1000, "Bot 2", False)
        ]
        self.engine = GuiGameEngine(
            self.players, self.deck, 25, 50, gui_handler=self
        )

        # UI state
        self.selected_cards = []
        self.card_items = []
        self.last_click_time = 0
        self.exchange_phase = False  # Track if we're in exchange phase

        self._createMenuBar()
        self._createMainLayout()

        # Start game after GUI shows
        QTimer.singleShot(100, self.play_round)

    def _createMenuBar(self):
        mb = self.menuBar()
        gm = mb.addMenu("Game")
        gm.addAction(QAction("New Game", self, triggered=self.new_game))
        gm.addAction(QAction("Exit", self, triggered=self.close))

    def _createMainLayout(self):
        cw = QWidget(self)
        self.setCentralWidget(cw)

        main_layout = QHBoxLayout(cw)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Left panel - player info
        self.player_list = QListWidget(self)
        self.player_list.setFixedWidth(220)
        main_layout.addWidget(self.player_list, stretch=1)

        # Center area - game display
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(5)

        # Game info labels
        info_layout = QHBoxLayout()
        self.pot_label = QLabel("Pot: 0")
        self.stack_label = QLabel("Your Stack: 1000 | Current Bet: 0")
        info_layout.addWidget(self.pot_label)
        info_layout.addWidget(self.stack_label)
        center_layout.addLayout(info_layout)

        # Card display
        self.card_container = QHBoxLayout()
        self.card_container.setContentsMargins(0, 0, 0, 0)
        self.card_container.setSpacing(0)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(QRectF(0, 0, 900, 400))
        self.scene.setBackgroundBrush(QBrush(QColor(0, 128, 0)))  # Green poker table

        self.view = QGraphicsView(self.scene, self)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setMinimumSize(900, 400)
        self.view.setFrameStyle(QFrame.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        self.card_container.addWidget(self.view)
        center_layout.addLayout(self.card_container, stretch=5)

        # Game messages
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setMaximumHeight(100)
        center_layout.addWidget(self.message_display)

        # Action buttons container
        self.actions_container = QHBoxLayout()
        self.actions_container.setContentsMargins(5, 0, 5, 5)
        self.actions_container.setSpacing(10)

        # Create all buttons but only show relevant ones
        self.btn_check_call = QPushButton("Check / Call", self)
        self.btn_raise = QPushButton("Raise", self)
        self.btn_fold = QPushButton("Fold", self)
        self.btn_exchange = QPushButton("Exchange Selected Cards", self)
        self.btn_play_again = QPushButton("Play Again", self)
        self.btn_confirm = QPushButton("Confirm Exchange", self)

        # Set button sizes
        for btn in [self.btn_check_call, self.btn_raise, self.btn_fold,
                    self.btn_exchange, self.btn_play_again, self.btn_confirm]:
            btn.setFixedHeight(40)
            btn.setMinimumWidth(120)

        # Connect signals
        self.btn_raise.clicked.connect(self.raise_clicked)
        self.btn_fold.clicked.connect(lambda: self.set_player_action("fold"))
        self.btn_exchange.clicked.connect(self.start_card_exchange)
        self.btn_play_again.clicked.connect(self.play_round)
        self.btn_check_call.clicked.connect(self.check_or_call)
        self.btn_confirm.clicked.connect(self.confirm_exchange)

        # Add buttons to container but hide most initially
        self.actions_container.addWidget(self.btn_check_call)
        self.actions_container.addWidget(self.btn_raise)
        self.actions_container.addWidget(self.btn_fold)
        self.actions_container.addWidget(self.btn_exchange)
        self.actions_container.addWidget(self.btn_confirm)
        self.actions_container.addWidget(self.btn_play_again)

        # Initial visibility
        self.btn_exchange.setVisible(False)
        self.btn_confirm.setVisible(False)
        self.btn_play_again.setVisible(False)

        center_layout.addLayout(self.actions_container, stretch=0)
        main_layout.addLayout(center_layout, stretch=5)

    class CardItem(QGraphicsObject):
        def __init__(self, pixmap, orig_pos, z, index, parent_ref):
            super().__init__()
            self.pixmap = pixmap
            self.setTransformOriginPoint(pixmap.width() / 2, pixmap.height() / 2)
            self.original_pos = orig_pos
            self.shifted = False
            self.setZValue(z)
            self.index = index
            self.parent_ref = parent_ref  # Weak reference to avoid circular references

            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(PokerGameGUI.ANIM_DURATION)
            self.setPos(orig_pos)

        def boundingRect(self):
            return QRectF(0, 0, self.pixmap.width(), self.pixmap.height())

        def paint(self, painter, option, widget):
            painter.drawPixmap(0, 0, self.pixmap)

        def mousePressEvent(self, event):
            parent = self.parent_ref()
            if not parent or not parent.exchange_phase:
                return

            now = time.time()
            if now - parent.last_click_time < PokerGameGUI.CLICK_COOLDOWN:
                return
            parent.last_click_time = now

            angle = math.radians(self.rotation())
            dx = PokerGameGUI.SHIFT_DISTANCE * math.sin(angle)
            dy = -PokerGameGUI.SHIFT_DISTANCE * math.cos(angle)

            start = self.pos()
            if not self.shifted:
                end = QPointF(self.original_pos.x() + dx, self.original_pos.y() + dy)
                parent.selected_cards.append(self.index)
            else:
                end = self.original_pos
                if self.index in parent.selected_cards:
                    parent.selected_cards.remove(self.index)

            self.anim.stop()
            self.anim.setStartValue(start)
            self.anim.setEndValue(end)
            self.anim.start()

            self.shifted = not self.shifted
            super().mousePressEvent(event)

    # === Game Engine Methods ===
    def play_round(self):
        """Start a new round of poker"""
        self.btn_play_again.setVisible(False)
        self.enable_betting_controls()
        self.message_display.clear()
        self.add_message("New round started!")

        # Reset game state
        self.selected_cards = []
        self.exchange_phase = False
        self.card_items = []

        # Start round
        self.engine.play_round()
        self.last_click_time = 0

    def request_player_action(self, player, current_bet):
        """Request action from the player during betting phase"""
        self.add_message(f"{player.get_name()}, your move! Bet to call: {current_bet}")
        self.update_player_list()
        self.show_cards(player)
        self.set_betting_controls_visible(True)
        self.exchange_phase = False

    def request_raise_amount(self, current_bet):
        """Show dialog to get raise amount from player"""
        amount, ok = QInputDialog.getInt(
            self, "Raise", f"Enter raise amount (minimum {current_bet + 50}):",
            current_bet + 50, current_bet + 50, 10000
        )
        if ok:
            self.engine.set_raise_amount(amount)
            self.set_player_action("raise")
        else:
            self.add_message("Raise canceled. Please choose another action.")
            self.enable_betting_controls()  # Re-enable controls

    def request_card_exchange(self, player):
        """Handle card exchange phase"""
        self.add_message(f"{player.get_name()}, select cards to exchange (click to select)")
        self.show_cards(player)
        self.set_exchange_controls_visible(True)
        self.selected_cards = []  # Reset selected cards
        self.exchange_phase = True  # Enable card selection

    def start_card_exchange(self):
        """Initiate card exchange when button is clicked"""
        self.engine.request_card_exchange(next(p for p in self.players if p.is_human()))

    def confirm_exchange(self):
        """Confirm card exchange and send to game engine"""
        if not self.selected_cards:
            self.add_message("No cards selected! Please select cards to exchange.")
            return

        self.set_exchange_controls_visible(False)
        player = next(p for p in self.players if p.is_human())
        self.engine.set_exchange_indices(self.selected_cards)
        self.selected_cards = []
        self.exchange_phase = False
        self.add_message("Cards exchanged successfully!")
        self.show_cards(player)

    def set_betting_controls_visible(self, visible):
        """Show/hide betting controls"""
        self.btn_check_call.setVisible(visible)
        self.btn_raise.setVisible(visible)
        self.btn_fold.setVisible(visible)
        self.btn_exchange.setVisible(False)
        self.btn_confirm.setVisible(False)

    def set_exchange_controls_visible(self, visible):
        """Show/hide exchange controls"""
        self.btn_check_call.setVisible(False)
        self.btn_raise.setVisible(False)
        self.btn_fold.setVisible(False)
        self.btn_exchange.setVisible(False)  # Hide "Exchange" button
        self.btn_confirm.setVisible(visible)  # Show "Confirm Exchange"

    def show_cards(self, player):
        """Display player's cards"""
        # Clear existing cards safely
        self.safe_clear_scene()

        if not player.get_hand():
            return

        cards = player.get_hand()
        num_cards = len(cards)

        # Adjust parameters based on number of cards
        if num_cards == 5:
            params = [
                {'angle': -45, 'x': -182, 'y': -77},
                {'angle': -22, 'x': -100, 'y': -140},
                {'angle': 0, 'x': 0, 'y': -165},
                {'angle': 22, 'x': 100, 'y': -140},
                {'angle': 45, 'x': 182, 'y': -77},
            ]
        else:  # For other hand sizes (like after exchange)
            params = []
            card_spacing = 180
            start_x = -(num_cards - 1) * card_spacing / 2
            for i in range(num_cards):
                params.append({'angle': 0, 'x': start_x + i * card_spacing, 'y': 0})

        w = self.scene.sceneRect().width()
        h = self.scene.sceneRect().height()
        bx, by = w / 2, h - 60

        for i, card in enumerate(cards):
            pm = _load_card_pixmap(card)
            p = params[i] if i < len(params) else {'angle': 0, 'x': 0, 'y': 0}
            x = bx + p['x'] - pm.width() / 2
            y = by + p['y'] - pm.height() / 2

            # Use weakref to avoid circular references
            item = self.CardItem(pm, QPointF(x, y), z=i, index=i,
                                 parent_ref=weakref.ref(self))
            item.setRotation(p['angle'])
            self.scene.addItem(item)
            self.card_items.append(item)

    def safe_clear_scene(self):
        """Safely clear the scene without causing crashes"""
        # Stop all animations first
        for item in self.card_items:
            if hasattr(item, 'anim') and item.anim:
                try:
                    item.anim.stop()
                    item.anim.deleteLater()
                except RuntimeError:
                    pass  # Item might already be deleted

        # Clear scene and reset card items list
        self.scene.clear()
        self.card_items = []

    def show_showdown_results(self, results_text):
        """Display showdown results and winner information"""
        self.add_message("\n--- SHOWDOWN ---")
        self.add_message(results_text)
        self.btn_play_again.setVisible(True)
        self.set_betting_controls_visible(False)
        self.exchange_phase = False

    def update_stats(self):
        """Update displayed game statistics"""
        try:
            pot = self.engine.pot
            player = next(p for p in self.players if p.is_human())
            stack = player.get_stack_amount()
            current_bet = player.current_bet
            self.pot_label.setText(f"Pot: {pot}")
            self.stack_label.setText(f"Your Stack: {stack} | Current Bet: {current_bet}")
        except Exception as e:
            print(f"Error updating stats: {e}")

    def update_player_list(self):
        """Update player list with current status"""
        try:
            self.player_list.clear()
            for player in self.players:
                status = " (Human)" if player.is_human() else " (Bot)"
                status += " - Folded" if player.has_folded else ""
                status += f" - ${player.get_stack_amount()}"
                if player == self.engine.current_player:
                    status += " [ACTIVE]"
                self.player_list.addItem(f"{player.get_name()}{status}")
        except Exception as e:
            print(f"Error updating player list: {e}")

    def add_message(self, text):
        """Add message to game log"""
        try:
            self.message_display.append(text)
            self.message_display.verticalScrollBar().setValue(
                self.message_display.verticalScrollBar().maximum()
            )
        except Exception as e:
            print(f"Error adding message: {e}")

    def process_events(self):
        QApplication.processEvents()

    def set_player_action(self, action):
        """Set player action and disable controls during processing"""
        try:
            self.disable_betting_controls()
            self.engine.set_player_action(action)
            self.add_message(f"You chose: {action}")
            self.update_stats()
        except Exception as e:
            print(f"Error setting player action: {e}")

    def raise_clicked(self):
        """Handle raise button click"""
        try:
            self.disable_betting_controls()
            player = next(p for p in self.players if p.is_human())
            to_call = self.engine.current_bet - player.current_bet
            if to_call > 0:
                self.set_player_action("call")
            else:
                self.request_raise_amount(self.engine.current_bet)
        except Exception as e:
            print(f"Error in raise_clicked: {e}")

    def check_or_call(self):
        """Handle check/call button click"""
        try:
            self.disable_betting_controls()
            player = next(p for p in self.players if p.is_human())
            to_call = self.engine.current_bet - player.current_bet
            if to_call <= 0:
                self.set_player_action("check")
            else:
                self.set_player_action("call")
        except Exception as e:
            print(f"Error in check_or_call: {e}")

    def disable_betting_controls(self):
        """Disable betting buttons during processing"""
        try:
            self.btn_check_call.setEnabled(False)
            self.btn_raise.setEnabled(False)
            self.btn_fold.setEnabled(False)
        except Exception as e:
            print(f"Error disabling controls: {e}")

    def enable_betting_controls(self):
        """Enable betting buttons for player action"""
        try:
            self.btn_check_call.setEnabled(True)
            self.btn_raise.setEnabled(True)
            self.btn_fold.setEnabled(True)
        except Exception as e:
            print(f"Error enabling controls: {e}")

    def new_game(self):
        """Start a new game"""
        try:
            self.deck = Deck()
            for player in self.players:
                player.stack = 1000
                player.current_bet = 0
                player.hand = []
                player.has_folded = False
            self.engine = GuiGameEngine(
                self.players, self.deck, 25, 50, gui_handler=self
            )
            self.play_round()
        except Exception as e:
            print(f"Error starting new game: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = PokerGameGUI()
    w.show()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)