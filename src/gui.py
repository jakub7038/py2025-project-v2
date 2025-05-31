import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget, QHBoxLayout, QCheckBox, QTextEdit
)
from PyQt5.QtCore import QTimer

from src.deck import Deck
from src.player import Player
from src.game_engine_controls import GuiGameEngine


class PokerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker GUI")
        self.setGeometry(100, 100, 800, 500)

        # Game setup
        self.deck = Deck()
        self.players = [
            Player(1000, "You", True),
            Player(1000, "Bot", False)
        ]
        self.engine = GuiGameEngine(
            self.players, self.deck, 25, 50, gui_handler=self
        )

        # UI Elements
        self.label = QLabel("Welcome! Game will begin shortly...", self)
        self.pot_label = QLabel("Pot: 0")
        self.stack_label = QLabel("")
        self.cards_display = QTextEdit()
        self.cards_display.setReadOnly(True)

        # Card checkboxes
        self.card_boxes = [QCheckBox(f"Card {i}") for i in range(5)]
        for cb in self.card_boxes:
            cb.setVisible(False)

        self.btn_check_call = QPushButton("Check / Call")
        self.btn_raise = QPushButton("Raise")
        self.btn_fold = QPushButton("Fold")
        self.btn_exchange = QPushButton("Exchange Selected Cards")
        self.btn_exchange.setVisible(False)
        self.btn_play_again = QPushButton("Play Again")
        self.btn_play_again.setVisible(False)

        # Button actions
        self.btn_raise.clicked.connect(self.raise_clicked)
        self.btn_fold.clicked.connect(lambda: self.set_player_action("fold"))
        self.btn_exchange.clicked.connect(self.confirm_exchange)
        self.btn_play_again.clicked.connect(self.play_round)
        self.btn_check_call.clicked.connect(self.check_or_call)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.pot_label)
        main_layout.addWidget(self.stack_label)
        main_layout.addWidget(self.cards_display)

        card_layout = QHBoxLayout()
        for cb in self.card_boxes:
            card_layout.addWidget(cb)
        main_layout.addLayout(card_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_check_call)
        btn_layout.addWidget(self.btn_raise)
        btn_layout.addWidget(self.btn_fold)
        main_layout.addLayout(btn_layout)

        main_layout.addWidget(self.btn_exchange)
        main_layout.addWidget(self.btn_play_again)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Start game after GUI shows
        QTimer.singleShot(100, self.play_round)

    def play_round(self):
        self.btn_play_again.setVisible(False)
        self.enable_betting_controls()
        self.label.setText("New round started!")
        self.cards_display.clear()
        self.engine.play_round()

    # === GuiGameEngine Hooks ===

    def request_player_action(self, player, current_bet):
        self.label.setText(f"{player.get_name()}, your move! Bet to call: {current_bet}")
        self.update_stats()
        self.show_cards(player)
        self.show_card_controls(False)

    def request_raise_amount(self, current_bet):
        self.label.setText(f"Raise above {current_bet} (simulated)")
        self.engine.set_raise_amount(current_bet + 50)

    def request_card_exchange(self, player):
        self.label.setText(f"{player.get_name()}, select cards to exchange")
        self.show_cards(player)
        self.show_card_controls(True)

    def confirm_exchange(self):
        selected_indices = [i for i, cb in enumerate(self.card_boxes) if cb.isChecked()]
        self.show_card_controls(False)
        player = next(p for p in self.players if p.is_human())
        self.show_cards(player)
        self.engine.set_exchange_indices(selected_indices)

    def show_card_controls(self, show):
        for cb in self.card_boxes:
            cb.setVisible(show)
            cb.setChecked(False)
        self.btn_exchange.setVisible(show)

    def show_cards(self, player):
        cards = player.get_hand()
        text = "\n".join(f"{i}: {str(card)}" for i, card in enumerate(cards))
        self.cards_display.setText(text)

    def show_showdown_results(self, results_text):
        self.cards_display.append("\n--- SHOWDOWN ---")
        self.cards_display.append(results_text)
        self.btn_play_again.setVisible(True)

    def update_stats(self):
        pot = self.engine.pot
        player = next(p for p in self.players if p.is_human())
        stack = player.get_stack_amount()
        current_bet = player.current_bet
        self.pot_label.setText(f"Pot: {pot}")
        self.stack_label.setText(f"Your Stack: {stack} | Current Bet: {current_bet}")

    def process_events(self):
        QApplication.processEvents()

    def set_player_action(self, action):
        self.engine.set_player_action(action)
        self.label.setText(f"You chose: {action}")
        self.update_stats()

    def raise_clicked(self):
        self.request_raise_amount(self.engine.current_bet)
        self.set_player_action("raise")

    def check_or_call(self):
        player = next(p for p in self.players if p.is_human())
        to_call = self.engine.current_bet - player.current_bet
        if to_call <= 0:
            self.set_player_action("check")
        else:
            self.set_player_action("call")

    def disable_betting_controls(self):
        self.btn_check_call.setEnabled(False)
        self.btn_raise.setEnabled(False)
        self.btn_fold.setEnabled(False)

    def enable_betting_controls(self):
        self.btn_check_call.setEnabled(True)
        self.btn_raise.setEnabled(True)
        self.btn_fold.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PokerGUI()
    window.show()
    sys.exit(app.exec_())
