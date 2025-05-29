import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QDialog,
    QFormLayout, QSpinBox, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from game_gui import PokerGUI
from src.player import Player
from src.deck import Deck
from src.game_engine import GameEngine

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'num_bots': 1,
        'small_blind': 25,
        'big_blind': 50,
        'starting_stack': 100
    }


def save_config(cfg):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        QMessageBox.warning(None, 'Error', f'Could not save config: {e}')


class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Ustawienia Gry')
        layout = QFormLayout(self)
        self.cfg = cfg

        self.bot_spin = QSpinBox(self)
        self.bot_spin.setRange(1, 3)
        self.bot_spin.setValue(cfg.get('num_bots', 1))
        layout.addRow('Liczba botów (min 1):', self.bot_spin)

        self.sb_spin = QSpinBox(self)
        self.sb_spin.setRange(1, 1000000)
        self.sb_spin.setValue(cfg.get('small_blind', 25))
        layout.addRow('Small Blind:', self.sb_spin)

        self.bb_spin = QSpinBox(self)
        self.bb_spin.setRange(1, 1000000)
        self.bb_spin.setValue(cfg.get('big_blind', 50))
        layout.addRow('Big Blind:', self.bb_spin)

        self.st_spin = QSpinBox(self)
        self.st_spin.setRange(1, 1000000)
        self.st_spin.setValue(cfg.get('starting_stack', 100))
        layout.addRow('Początkowy stack:', self.st_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def validate(self):
        sb = self.sb_spin.value()
        bb = self.bb_spin.value()
        if bb <= sb:
            QMessageBox.warning(self, 'Błąd', 'Big Blind musi być większy od Small Blind!')
            return

        self.cfg['num_bots'] = self.bot_spin.value()
        self.cfg['small_blind'] = sb
        self.cfg['big_blind'] = bb
        self.cfg['starting_stack'] = self.st_spin.value()
        save_config(self.cfg)
        self.accept()


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Poker - Main Menu')
        self.resize(500, 400)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('#228B22'))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        self.config = load_config()

        btn_new = QPushButton('Nowa Gra', self)
        btn_new.setFixedHeight(60)
        btn_new.setMinimumWidth(200)
        btn_new.clicked.connect(self.start_game)
        layout.addWidget(btn_new, alignment=Qt.AlignCenter)

        btn_load = QPushButton('Wczytaj Grę', self)
        btn_load.setFixedHeight(60)
        btn_load.setMinimumWidth(200)
        btn_load.clicked.connect(self.load_game)
        layout.addWidget(btn_load, alignment=Qt.AlignCenter)

        btn_settings = QPushButton('Ustawienia', self)
        btn_settings.setFixedHeight(60)
        btn_settings.setMinimumWidth(200)
        btn_settings.clicked.connect(self.open_settings)
        layout.addWidget(btn_settings, alignment=Qt.AlignCenter)

        btn_exit = QPushButton('Wyjście', self)
        btn_exit.setFixedHeight(60)
        btn_exit.setMinimumWidth(200)
        btn_exit.clicked.connect(QApplication.quit)
        layout.addWidget(btn_exit, alignment=Qt.AlignCenter)

    def open_settings(self):
        dlg = SettingsDialog(self.config, self)
        dlg.exec_()

    def start_game(self):
        bots = self.config.get('num_bots', 1)
        starting = self.config.get('starting_stack', 100)

        players = [Player(starting, 'Gracz 1', True)]

        for i in range(bots):
            players.append(Player(starting, f'Bot {i+1}', False))
        deck = Deck()
        engine = GameEngine(players, deck,
                            self.config.get('small_blind', 25),
                            self.config.get('big_blind', 50))
        self.poker = PokerGUI(engine)
        self.poker.show()
        self.hide()

    def load_game(self):
        QMessageBox.information(self, 'Wczytaj Grę', 'Funkcja w przygotowaniu.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec_())
