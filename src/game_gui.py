import sys
import os
import math
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget, QHBoxLayout, QListWidget,
    QGraphicsView, QGraphicsScene, QGraphicsObject,
    QTextEdit, QInputDialog, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QPropertyAnimation, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor

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
        pixmap.fill(Qt.transparent)
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
            self.parent.selected_cards.append(self.index)
        else:
            end = self.original_pos
            if self.index in self.parent.selected_cards:
                self.parent.selected_cards.remove(self.index)
        self.anim.stop()
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()
        self.shifted = not self.shifted
        super().mousePressEvent(event)


class PokerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker")
        self.resize(1000, 700)
        self.deck = Deck()
        self.players = [Player(1000, "You", True), Player(1000, "Bot", False)]
        self.engine = GuiGameEngine(self.players, self.deck, 25, 50, gui_handler=self)
        self.selected_cards = []
        self.card_items = []
        self.last_click_time = 0
        self.exchange_phase = False
        self.awaiting_raise_input = False
        self._createMainLayout()
        self._createGameControls()
        QTimer.singleShot(100, self.play_round)

    def _createMainLayout(self):
        cw = QWidget(self)
        self.setCentralWidget(cw)
        main_layout = QVBoxLayout(cw)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        game_area = QHBoxLayout()
        game_area.setSpacing(10)
        self.player_list = QListWidget()
        self.player_list.setFixedWidth(200)
        game_area.addWidget(self.player_list, stretch=1)
        center_layout = QVBoxLayout()
        center_layout.setSpacing(10)
        info_layout = QHBoxLayout()
        self.pot_label = QLabel("Pot: 0")
        self.stack_label = QLabel("Your Stack: 1000 | Current Bet: 0")
        info_layout.addWidget(self.pot_label)
        info_layout.addStretch()
        info_layout.addWidget(self.stack_label)
        center_layout.addLayout(info_layout)
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(QRectF(0, 0, 700, 400))
        self.scene.setBackgroundBrush(QBrush(QColor(0, 100, 0)))
        self.view = QGraphicsView(self.scene, self)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setMinimumSize(700, 400)
        self.view.setFrameStyle(QFrame.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        center_layout.addWidget(self.view, stretch=2)
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setMaximumHeight(100)
        center_layout.addWidget(self.message_display, stretch=1)
        game_area.addLayout(center_layout, stretch=4)
        main_layout.addLayout(game_area, stretch=1)
        self.button_container = QHBoxLayout()
        self.button_container.setContentsMargins(0, 10, 0, 0)
        main_layout.addLayout(self.button_container, stretch=0)

    def _createGameControls(self):
        self.btn_check_call = QPushButton("Check / Call")
        self.btn_raise = QPushButton("Raise")
        self.btn_fold = QPushButton("Fold")
        self.btn_exchange = QPushButton("Exchange Cards")
        self.btn_play_again = QPushButton("Play Again")
        for btn in [self.btn_check_call, self.btn_raise, self.btn_fold,
                    self.btn_exchange, self.btn_play_again]:
            btn.setFixedHeight(40)
            btn.setMinimumWidth(120)
        self.btn_raise.clicked.connect(self.raise_clicked)
        self.btn_fold.clicked.connect(lambda: self.set_player_action("fold"))
        self.btn_exchange.clicked.connect(self.confirm_exchange)
        self.btn_play_again.clicked.connect(self.play_round)
        self.btn_check_call.clicked.connect(self.check_or_call)
        self.button_container.addWidget(self.btn_check_call)
        self.button_container.addWidget(self.btn_raise)
        self.button_container.addWidget(self.btn_fold)
        self.button_container.addWidget(self.btn_exchange)
        self.button_container.addWidget(self.btn_play_again)
        self.btn_exchange.setVisible(False)
        self.btn_play_again.setVisible(False)

    def play_round(self):
        self.btn_play_again.setVisible(False)
        self.enable_betting_controls()
        self.message_display.clear()
        self.add_message("New round started!")
        self.selected_cards = []
        self.exchange_phase = False
        self.awaiting_raise_input = False
        self.clear_card_scene()
        self.engine.play_round()
        self.last_click_time = 0

    def request_player_action(self, player, current_bet):
        self.awaiting_raise_input = False
        self.add_message(f"{player.get_name()}, your move! Bet to call: {current_bet}")
        self.update_player_list()
        self.show_cards(player)
        self.set_betting_controls_visible(True)
        self.exchange_phase = False

    def request_raise_amount(self, current_bet):
        if not self.awaiting_raise_input:
            self.awaiting_raise_input = True

            # Get human player and calculate amount needed to call
            player = next(p for p in self.players if p.is_human())
            to_call = current_bet - player.current_bet

            # Calculate minimum raise amount (additional chips above call)
            min_raise = max(self.engine.big_blind, to_call + self.engine.big_blind)

            amount, ok = QInputDialog.getInt(
                self, "Raise",
                f"Additional raise (minimum {min_raise}):",
                min_raise, min_raise, 10000
            )

            if ok:
                # Set the additional raise amount
                self.engine.set_raise_amount(amount)
                self.set_player_action("raise")
            else:
                self.add_message("Raise canceled. Please choose another action.")
                self.enable_betting_controls()

            self.awaiting_raise_input = False

    def request_card_exchange(self, player):
        self.add_message(f"{player.get_name()}, select cards to exchange (click to select)")
        self.show_cards(player)
        self.btn_exchange.setVisible(True)
        self.selected_cards = []
        self.exchange_phase = True

    def confirm_exchange(self):
        self.btn_exchange.setVisible(False)
        player = next(p for p in self.players if p.is_human())
        self.engine.set_exchange_indices(self.selected_cards)
        self.selected_cards = []
        self.exchange_phase = False
        self.add_message("Cards exchanged successfully!")
        self.show_cards(player)

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
        w = self.scene.sceneRect().width()
        h = self.scene.sceneRect().height()
        bx, by = w / 2, h - 100
        for i, card in enumerate(cards):
            pm = load_card_pixmap(card)
            p = params[i] if i < len(params) else {'angle': 0, 'x': 0, 'y': 0}
            x = bx + p['x'] - pm.width() / 2
            y = by + p['y'] - pm.height() / 2
            item = CardItem(pm, QPointF(x, y), z=i, index=i, parent=self)
            item.setRotation(p['angle'])
            self.scene.addItem(item)
            self.card_items.append(item)

    def clear_card_scene(self):
        for item in self.card_items:
            if hasattr(item, 'anim'):
                item.anim.stop()
        self.scene.clear()
        self.card_items = []

    def show_showdown_results(self, results_text):
        self.add_message("\n--- SHOWDOWN ---")
        self.add_message(results_text)
        self.btn_play_again.setVisible(True)
        self.set_betting_controls_visible(False)
        self.exchange_phase = False

        self.update_stats()
        self.update_player_list()

    def update_stats(self):
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
        try:
            self.player_list.clear()
            for player in self.players:
                status = " (Human)" if player.is_human() else " (Bot)"
                status += " - Folded" if player.folded else ""
                status += f" - ${player.get_stack_amount()}"
                if player == self.engine.current_player:
                    status += " [ACTIVE]"
                self.player_list.addItem(f"{player.get_name()}{status}")
        except Exception as e:
            print(f"Error updating player list: {e}")

    def add_message(self, text):
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
        self.engine.set_player_action(action)
        self.add_message(f"You chose: {action}")
        self.update_stats()

    def raise_clicked(self):
        if not self.awaiting_raise_input:
            self.awaiting_raise_input = True
            min_raise = max(self.engine.big_blind, self.engine.current_bet + self.engine.big_blind)
            amount, ok = QInputDialog.getInt(
                self, "Raise", f"Enter raise amount (minimum {min_raise}):",
                min_raise, min_raise, 10000
            )
            if ok:
                self.engine.set_raise_amount(amount)
                self.set_player_action("raise")
            else:
                self.add_message("Raise canceled. Please choose another action.")
                self.enable_betting_controls()
            self.awaiting_raise_input = False

    def check_or_call(self):
        player = next(p for p in self.players if p.is_human())
        to_call = self.engine.current_bet - player.current_bet
        if to_call <= 0:
            self.set_player_action("check")
        else:
            self.set_player_action("call")

    def set_betting_controls_visible(self, visible):
        self.btn_check_call.setVisible(visible)
        self.btn_raise.setVisible(visible)
        self.btn_fold.setVisible(visible)

    def disable_betting_controls(self):
        self.btn_check_call.setEnabled(False)
        self.btn_raise.setEnabled(False)
        self.btn_fold.setEnabled(False)

    def enable_betting_controls(self):
        self.btn_check_call.setEnabled(True)
        self.btn_raise.setEnabled(True)
        self.btn_fold.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PokerGUI()
    window.show()
    sys.exit(app.exec_())
