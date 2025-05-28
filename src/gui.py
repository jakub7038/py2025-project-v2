import sys
import os
import math
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QAction,
    QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QDialog, QGraphicsView, QGraphicsScene, QGraphicsObject,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor

from card import Card


def _load_card_pixmap(card):
    rank = card.rank.upper()
    suit = card.suit.upper()
    filename = f"{rank}{suit}.png"
    cards_dir = os.path.join(os.path.dirname(__file__), "cards", "Rust")
    path = os.path.join(cards_dir, filename)
    pixmap = QPixmap(path)
    if pixmap.isNull():
        pixmap = QPixmap(140, 200)
        pixmap.fill(Qt.transparent)
    else:
        pixmap = pixmap.scaled(
            140, 200,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
    return pixmap


class RaiseDialog(QDialog):
    pass


class PokerGUI(QMainWindow):
    SHIFT_DISTANCE = 50
    CLICK_COOLDOWN = 0.3
    ANIM_DURATION = 200

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker")
        self.resize(1100, 600)

        self._createMenuBar()
        self._createMainLayout()

    def _createMenuBar(self):
        mb = self.menuBar()
        gm = mb.addMenu("Gra")
        gm.addAction(QAction("Nowa Gra", self))
        gm.addAction(QAction("Zapisz Grę", self))
        gm.addAction(QAction("Wczytaj Grę", self))
        gm.addAction(QAction("Wyjście", self))

    def _createMainLayout(self):
        cw = QWidget(self)
        self.setCentralWidget(cw)

        main_layout = QHBoxLayout(cw)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(5)

        self._createCardDisplay(center_layout)

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(5, 0, 5, 5)
        actions_layout.setSpacing(10)
        btns = []
        for text in ("Raise", "Check/Call", "Fold", "Wymień zaznaczone"):
            b = QPushButton(text, self)
            b.setFixedHeight(40)
            b.setMinimumWidth(100)
            btns.append(b)
        btns[0].clicked.connect(self.showRaiseDialog)
        for b in btns:
            actions_layout.addWidget(b)

        center_layout.addLayout(self.card_container, stretch=5)
        center_layout.addLayout(actions_layout, stretch=0)

        player_list = QListWidget(self)
        player_list.addItems(["Bot 1 - 500", "Bot 2 - 520", "Ty - 480"])
        player_list.setFixedWidth(220)

        main_layout.addLayout(center_layout, stretch=5)
        main_layout.addWidget(player_list, stretch=1)

    def _createCardDisplay(self, layout):
        self.card_container = QHBoxLayout()
        self.card_container.setContentsMargins(0, 0, 0, 0)
        self.card_container.setSpacing(0)

        class CardItem(QGraphicsObject):
            _last_click_time = 0
            def __init__(self, pixmap, orig_pos, z):
                super().__init__()
                self.pixmap = pixmap
                self.setTransformOriginPoint(
                    pixmap.width()/2, pixmap.height()/2
                )
                self.original_pos = orig_pos
                self.shifted = False
                self.setZValue(z)
                self.anim = QPropertyAnimation(self, b"pos")
                self.anim.setDuration(PokerGUI.ANIM_DURATION)
                self.setPos(orig_pos)

            def boundingRect(self):
                return QRectF(0, 0, self.pixmap.width(), self.pixmap.height())

            def paint(self, painter, option, widget):
                painter.drawPixmap(0, 0, self.pixmap)

            def mousePressEvent(self, event):
                now = time.time()
                if now - CardItem._last_click_time < PokerGUI.CLICK_COOLDOWN:
                    return
                CardItem._last_click_time = now

                angle = math.radians(self.rotation())
                dx = PokerGUI.SHIFT_DISTANCE * math.sin(angle)
                dy = -PokerGUI.SHIFT_DISTANCE * math.cos(angle)

                start = self.pos()
                end = (QPointF(self.original_pos.x() + dx,
                               self.original_pos.y() + dy)
                       if not self.shifted else self.original_pos)

                self.anim.stop()
                self.anim.setStartValue(start)
                self.anim.setEndValue(end)
                self.anim.start()

                self.shifted = not self.shifted
                super().mousePressEvent(event)

        scene = QGraphicsScene(self)
        scene.setSceneRect(QRectF(0, 0, 900, 400))

        cards = [Card(r, s) for r, s in
                 [('A','s'),('K','h'),('Q','d'),('J','c'),('10','s')]]
        params = [
            {'angle': -45, 'x': -182, 'y': -77},
            {'angle': -22, 'x': -100, 'y': -140},
            {'angle':   0, 'x':    0, 'y': -165},
            {'angle':  22, 'x':  100, 'y': -140},
            {'angle':  45, 'x':  182, 'y': -77},
        ]
        w = scene.sceneRect().width()
        h = scene.sceneRect().height()
        bx, by = w/2, h-60

        for i, c in enumerate(cards):
            pm = _load_card_pixmap(c)
            p = params[i]
            x = bx + p['x'] - pm.width()/2
            y = by + p['y'] - pm.height()/2
            item = CardItem(pm, QPointF(x, y), z=i)
            item.setRotation(p['angle'])
            scene.addItem(item)

        items_rect = scene.itemsBoundingRect()
        scene.setSceneRect(items_rect)
        scene.setBackgroundBrush(QBrush(QColor(0, 128, 0)))

        view = QGraphicsView(scene, self)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        view.setMinimumSize(int(items_rect.width()), int(items_rect.height()))
        view.setFrameStyle(QFrame.NoFrame)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform
        )

        self.card_container.addWidget(view)
        layout.addLayout(self.card_container)

    def showRaiseDialog(self):
        dlg = RaiseDialog(self)
        if dlg.exec_():
            amt = dlg.raise_input.text()
            print(f"Raise amount: {amt}")


def newgame():
    # TODO: rename main and reuse its contents to actually start a game
    pass

def savegame():
    # TODO: link to session_manager; disable if not between rounds
    pass

def loadgame():
    # TODO: link to session_manager; warn if loading during play
    pass

def exitgame():
    # TODO: confirm exit before saving and then close
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = PokerGUI()
    w.show()
    sys.exit(app.exec_())