import sys
import os
import math
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget, QHBoxLayout, QTextEdit,
    QInputDialog, QFrame, QSizePolicy, QGridLayout,
    QMessageBox, QProgressBar, QGraphicsView, QGraphicsScene, QGraphicsObject
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QPropertyAnimation, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QFont

from src.deck import Deck
from src.player import Player
from src.game_engine_controls import GuiGameEngine


def load_card_pixmap(card):
    suit_map = {'s': 'S', 'h': 'H', 'd': 'D', 'c': 'C'}
    rank_map = {'10': '10', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}

    rank = str(card.rank).upper()
    suit = suit_map.get(card.suit.lower(), card.suit.upper())

    if rank in ('10', '11', '12', '13'):
        rank = rank_map.get(rank, rank)
    elif rank == '1':
        rank = 'A'

    filename = f"{rank}{suit}.png"
    cards_dir = os.path.join(os.path.dirname(__file__), "cards", "Rust")
    path = os.path.join(cards_dir, filename)

    pixmap = QPixmap(path)
    if pixmap.isNull():
        pixmap = QPixmap(100, 150)
        pixmap.fill(QColor(255, 255, 255))
        painter = QPainter(pixmap)
        painter.setPen(Qt.black)
        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)

        rank_text = str(card.rank)
        if rank_text == '1':
            rank_text = 'A'
        elif rank_text == '11':
            rank_text = 'J'
        elif rank_text == '12':
            rank_text = 'Q'
        elif rank_text == '13':
            rank_text = 'K'

        suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
        suit_symbol = suit_symbols.get(card.suit.lower(), card.suit)

        if card.suit.lower() in ['h', 'd']:
            painter.setPen(Qt.red)
        else:
            painter.setPen(Qt.black)

        text = f"{rank_text}\n{suit_symbol}"
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
    else:
        pixmap = pixmap.scaled(100, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return pixmap


class CardItem(QGraphicsObject):
    SHIFT_DISTANCE = 30
    ANIM_DURATION = 200

    def __init__(self, pixmap, orig_pos, z, index, parent):
        super().__init__()
        self.pixmap = pixmap
        self.setTransformOriginPoint(pixmap.width() / 2, pixmap.height() / 2)
        self.original_pos = orig_pos
        self.shifted = False
        self.setZValue(z)
        self.index = index
        self.parent = parent
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(self.ANIM_DURATION)
        self.setPos(orig_pos)

    def boundingRect(self):
        return QRectF(0, 0, self.pixmap.width(), self.pixmap.height())

    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        if not self.parent.exchange_phase:
            return

        now = time.time()
        if now - self.parent.last_click_time < 0.3:
            return
        self.parent.last_click_time = now

        angle = math.radians(self.rotation())
        dx = self.SHIFT_DISTANCE * math.sin(angle)
        dy = -self.SHIFT_DISTANCE * math.cos(angle)

        start = self.pos()

        if not self.shifted:
            end = QPointF(self.original_pos.x() + dx, self.original_pos.y() + dy)
            if len(self.parent.selected_cards) < 3:  # Max 3 cards
                self.parent.selected_cards.append(self.index)
            else:
                self.parent.add_message("You can only exchange up to 3 cards!")
                return
        else:
            end = self.original_pos
            if self.index in self.parent.selected_cards:
                self.parent.selected_cards.remove(self.index)

        self.anim.stop()
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

        self.shifted = not self.shifted

        self.parent.update_exchange_button_text()

        super().mousePressEvent(event)


class PokerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Five Card Draw Poker")
        self.setGeometry(100, 100, 1200, 800)

        self.deck = Deck()
        self.players = [
            Player(1000, "You", True),
            Player(1000, "Bot 1", False),
            Player(1000, "Bot 2", False),
            Player(1000, "Bot 3", False)  # Added another bot for testing
        ]
        self.engine = GuiGameEngine(self.players, self.deck, 25, 50, gui_handler=self)

        self.selected_cards = []
        self.card_items = []
        self.last_click_time = 0
        self.exchange_phase = False
        self.game_over = False

        self.setup_ui()
        self.update_all_displays()

        QTimer.singleShot(500, self.start_new_round)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.create_game_info_section(main_layout)

        player_info_layout = QHBoxLayout()

        self.create_human_player_info(player_info_layout)

        self.create_bot_players_info(player_info_layout)

        main_layout.addLayout(player_info_layout)

        self.create_card_scene(main_layout)

        self.create_game_controls(main_layout)

        self.create_messages_area(main_layout)

    def create_game_info_section(self, parent_layout):
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Box)
        info_frame.setStyleSheet("QFrame { background-color: #f0f0f0; padding: 10px; }")

        info_layout = QHBoxLayout(info_frame)

        self.pot_label = QLabel("Pot: $0")
        self.pot_label.setFont(QFont("Arial", 14, QFont.Bold))

        self.stage_label = QLabel("Stage: Pre-flop")
        self.stage_label.setFont(QFont("Arial", 12))

        self.current_bet_label = QLabel("Current Bet: $0")
        self.current_bet_label.setFont(QFont("Arial", 12))

        info_layout.addWidget(self.pot_label)
        info_layout.addStretch()
        info_layout.addWidget(self.stage_label)
        info_layout.addStretch()
        info_layout.addWidget(self.current_bet_label)

        parent_layout.addWidget(info_frame)

    def create_human_player_info(self, parent_layout):
        player_frame = QFrame()
        player_frame.setFrameStyle(QFrame.Box)
        player_frame.setStyleSheet("QFrame { background-color: #e8f4f8; padding: 15px; }")
        player_frame.setMinimumWidth(300)

        player_layout = QVBoxLayout(player_frame)

        human_player = next(p for p in self.players if p.is_human())

        title_label = QLabel("YOUR STATUS")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        self.human_player_label = QLabel(f"{human_player.get_name()}: ${human_player.get_stack_amount()}")
        self.human_player_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.human_player_label.setStyleSheet("QLabel { color: blue; }")
        self.human_player_label.setAlignment(Qt.AlignCenter)

        player_layout.addWidget(title_label)
        player_layout.addWidget(self.human_player_label)
        player_layout.addStretch()

        parent_layout.addWidget(player_frame)

    def create_bot_players_info(self, parent_layout):
        bot_frame = QFrame()
        bot_frame.setFrameStyle(QFrame.Box)
        bot_frame.setStyleSheet("QFrame { background-color: #f8e8e8; padding: 15px; }")

        bot_layout = QVBoxLayout(bot_frame)

        title_label = QLabel("OPPONENTS")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        bot_layout.addWidget(title_label)

        self.bot_labels = []
        for player in self.players:
            if not player.is_human():
                label = QLabel(f"{player.get_name()}: ${player.get_stack_amount()}")
                label.setFont(QFont("Arial", 11))
                label.setStyleSheet("QLabel { margin: 5px; }")
                self.bot_labels.append(label)
                bot_layout.addWidget(label)

        bot_layout.addStretch()
        parent_layout.addWidget(bot_frame)

    def create_card_scene(self, parent_layout):
        card_frame = QFrame()
        card_frame.setFrameStyle(QFrame.Box)
        card_frame.setMinimumHeight(300)

        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(5, 5, 5, 5)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(QRectF(0, 0, 800, 250))
        self.scene.setBackgroundBrush(QBrush(QColor(0, 100, 0)))  # Green felt background

        self.view = QGraphicsView(self.scene, self)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setMinimumSize(800, 250)
        self.view.setFrameStyle(QFrame.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        card_layout.addWidget(self.view)
        parent_layout.addWidget(card_frame)

    def create_game_controls(self, parent_layout):
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        self.btn_fold = QPushButton("Fold")
        self.btn_check_call = QPushButton("Check/Call")
        self.btn_raise = QPushButton("Raise")

        self.btn_exchange = QPushButton("Exchange Selected Cards (0)")
        self.btn_keep_all = QPushButton("Keep All Cards")

        self.btn_new_round = QPushButton("Start New Round")

        button_style = """
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: 2px solid #333;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """

        for btn in [self.btn_fold, self.btn_check_call, self.btn_raise,
                    self.btn_exchange, self.btn_keep_all, self.btn_new_round]:
            btn.setStyleSheet(button_style)
            btn.setMinimumWidth(120)

        self.btn_fold.clicked.connect(lambda: self.set_player_action("fold"))
        self.btn_check_call.clicked.connect(self.handle_check_call)
        self.btn_raise.clicked.connect(self.handle_raise)
        self.btn_exchange.clicked.connect(self.handle_exchange)
        self.btn_keep_all.clicked.connect(lambda: self.handle_exchange(keep_all=True))
        self.btn_new_round.clicked.connect(self.start_new_round)

        controls_layout.addWidget(self.btn_fold)
        controls_layout.addWidget(self.btn_check_call)
        controls_layout.addWidget(self.btn_raise)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_exchange)
        controls_layout.addWidget(self.btn_keep_all)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_new_round)

        parent_layout.addWidget(controls_frame)

        self.btn_exchange.setVisible(False)
        self.btn_keep_all.setVisible(False)

    def create_messages_area(self, parent_layout):
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        self.messages.setMaximumHeight(150)
        self.messages.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
                font-family: monospace;
                font-size: 11px;
            }
        """)

        parent_layout.addWidget(self.messages)

    def show_cards(self, player):
        self.clear_card_scene()

        if not player.get_hand():
            return

        cards = player.get_hand()
        num_cards = len(cards)

        if num_cards == 5:
            params = [
                {'angle': -45, 'x': -182, 'y': -77},
                {'angle': -22, 'x': -100, 'y': -140},
                {'angle': 0, 'x': 0, 'y': -165},
                {'angle': 22, 'x': 100, 'y': -140},
                {'angle': 45, 'x': 182, 'y': -77},
            ]
        else:
            params = []
            card_spacing = 140
            start_x = -(num_cards - 1) * card_spacing / 2
            for i in range(num_cards):
                params.append({'angle': 0, 'x': start_x + i * card_spacing, 'y': 0})

        scene_rect = self.scene.sceneRect()
        center_x = scene_rect.width() / 2
        center_y = scene_rect.height()

        for i, card in enumerate(cards):
            pixmap = load_card_pixmap(card)

            if i < len(params):
                p = params[i]
            else:
                p = {'angle': 0, 'x': 0, 'y': 0}

            x = center_x + p['x'] - pixmap.width() / 2
            y = center_y + p['y'] - pixmap.height() / 2

            card_item = CardItem(pixmap, QPointF(x, y), z=i, index=i, parent=self)
            card_item.setRotation(p['angle'])

            self.scene.addItem(card_item)
            self.card_items.append(card_item)

    def clear_card_scene(self):
        for item in self.card_items:
            if hasattr(item, 'anim'):
                item.anim.stop()
        self.scene.clear()
        self.card_items = []

    def update_all_displays(self):
        self.pot_label.setText(f"Pot: ${self.engine.pot}")
        self.stage_label.setText(f"Stage: {self.engine.current_stage.title()}")
        self.current_bet_label.setText(f"Current Bet: ${self.engine.current_bet}")

        human_player = next(p for p in self.players if p.is_human())
        status = f"{human_player.get_name()}: ${human_player.get_stack_amount()}"
        if human_player.folded:
            status += " (Folded)"
        if human_player == self.engine.current_player:
            self.human_player_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        else:
            self.human_player_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

        self.human_player_label.setText(status)

        bot_index = 0
        for player in self.players:
            if not player.is_human() and bot_index < len(self.bot_labels):
                label = self.bot_labels[bot_index]
                status = f"{player.get_name()}: ${player.get_stack_amount()}"
                if player.folded:
                    status += " (Folded)"
                if player == self.engine.current_player:
                    label.setStyleSheet("QLabel { color: red; font-weight: bold; margin: 5px; }")
                else:
                    label.setStyleSheet("QLabel { color: black; margin: 5px; }")

                label.setText(status)
                bot_index += 1

    def update_exchange_button_text(self):
        count = len(self.selected_cards)
        self.btn_exchange.setText(f"Exchange Selected Cards ({count})")

    def add_message(self, message):
        self.messages.append(message)
        scrollbar = self.messages.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def process_events(self):
        QApplication.processEvents()

    def request_player_action(self, player, current_bet):
        self.exchange_phase = False
        self.show_betting_controls(True)
        self.show_exchange_controls(False)

        to_call = current_bet
        if to_call > 0:
            self.btn_check_call.setText(f"Call ${to_call}")
        else:
            self.btn_check_call.setText("Check")

        self.add_message(f"{player.get_name()}'s turn. Bet to call: ${current_bet}")
        self.update_all_displays()

    def request_raise_amount(self, current_bet):
        player = next(p for p in self.players if p.is_human())
        min_raise = max(self.engine.big_blind, current_bet + self.engine.big_blind)
        max_raise = player.get_stack_amount()

        amount, ok = QInputDialog.getInt(
            self,
            "Raise Amount",
            f"Enter raise amount (min: ${min_raise}, max: ${max_raise}):",
            min_raise, min_raise, max_raise
        )

        if ok:
            self.engine.set_raise_amount(amount)
        else:
            self.add_message("Raise cancelled - please choose another action")

    def request_card_exchange(self, player):
        self.exchange_phase = True
        self.selected_cards = []
        self.last_click_time = 0

        self.show_betting_controls(False)
        self.show_exchange_controls(True)

        self.add_message("Select up to 3 cards to exchange (click on cards)")
        self.show_cards(player)

        for card_item in self.card_items:
            card_item.shifted = False

        self.update_exchange_button_text()

    def show_showdown_results(self, results_text):
        self.add_message(results_text)
        self.show_betting_controls(False)
        self.show_exchange_controls(False)
        self.update_all_displays()

        active_players = [p for p in self.players if p.get_stack_amount() > 0]
        if len(active_players) <= 1:
            self.show_game_over()
        else:
            QTimer.singleShot(3000, self.enable_new_round)

    def show_game_over(self):
        winner = max(self.players, key=lambda p: p.get_stack_amount())
        QMessageBox.information(
            self,
            "Game Over",
            f"Game Over!\n{winner.get_name()} wins with ${winner.get_stack_amount()}!"
        )
        self.game_over = True

    # Button handlers
    def handle_check_call(self):
        player = next(p for p in self.players if p.is_human())
        to_call = self.engine.current_bet - player.current_bet

        if to_call > 0:
            self.set_player_action("call")
        else:
            self.set_player_action("check")

    def handle_raise(self):
        self.set_player_action("raise")

    def handle_exchange(self, keep_all=False):
        if keep_all:
            indices = []
        else:
            indices = self.selected_cards.copy()

        self.engine.set_exchange_indices(indices)
        self.add_message(f"Exchanged {len(indices)} cards")

        self.show_exchange_controls(False)
        self.exchange_phase = False

        self.selected_cards = []

    def start_new_round(self):
        if self.game_over:
            # Reset game
            for player in self.players:
                player.set_stack_amount(1000)
            self.game_over = False

        self.messages.clear()
        self.add_message("Starting new round...")
        self.selected_cards = []
        self.exchange_phase = False
        self.last_click_time = 0

        self.clear_card_scene()

        QTimer.singleShot(100, self.engine.play_round)

    def enable_new_round(self):
        self.btn_new_round.setEnabled(True)

    # Engine interface methods
    def set_player_action(self, action):
        self.engine.set_player_action(action)
        self.add_message(f"You chose: {action}")
        self.show_betting_controls(False)

    # UI helper methods
    def show_betting_controls(self, visible):
        self.btn_fold.setVisible(visible)
        self.btn_check_call.setVisible(visible)
        self.btn_raise.setVisible(visible)

    def show_exchange_controls(self, visible):
        self.btn_exchange.setVisible(visible)
        self.btn_keep_all.setVisible(visible)


def main():
    app = QApplication(sys.argv)
    window = PokerGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()