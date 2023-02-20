from PyQt5.QtCore import QEasingCurve, Qt, QPropertyAnimation, QPoint, QRect, pyqtProperty
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import QCheckBox

class ToggleButton(QCheckBox):
    def __init__(
        self,
        parent = None,
        width = 50,
        hight = 28,
        bg_color = "#777", 
        circle_color = "#DDD",
        active_color = "#00BCFF",
        animation_curve = QEasingCurve.OutQuad
    ):
        QCheckBox.__init__(self, parent=parent)
        self.setFixedSize(width, hight)
        self.setCursor(Qt.PointingHandCursor)

        # COLORS
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        self._position = 3
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(200)
        self.stateChanged.connect(self.setup_animation)
        self.show()

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = int(pos)
        self.update()

    # START STOP ANIMATION
    def setup_animation(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(self.width() - (self.height() - 2)) # kenet 26
        else:
            self.animation.setEndValue(4)
        self.animation.start()
    
    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setFont(QFont("Segoe UI", 9))

        # SET PEN
        p.setPen(Qt.NoPen)

        # DRAW RECT
        rect = QRect(0, 0, self.width(), self.height())        
    
        if not self.isChecked():
            p.setBrush(QColor(self._bg_color))
            p.drawRoundedRect(0,0,rect.width(), rect.height(), rect.height()/2, rect.height()/2)
            p.setBrush(QColor(self._circle_color))
            # 3 is initioal self._position of the circle
            p.drawEllipse(self._position, 3, rect.height()-2*3, rect.height()-2*3)
        else:
            p.setBrush(QColor(self._active_color))
            p.drawRoundedRect(0,0,rect.width(), rect.height(), rect.height()/2, rect.height()/2)
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._position, 3, rect.height()-2*3, rect.height()-2*3)

        p.end()