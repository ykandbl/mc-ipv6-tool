"""无需外部资源的点对点联机图标。"""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF


def create_app_icon() -> QIcon:
    """绘制两个设备之间双向通信的抽象标识。"""
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#1C2921"))
    painter.drawRoundedRect(QRectF(8, 8, 240, 240), 54, 54)

    lime = QColor("#C7E36C")
    painter.setBrush(lime)
    painter.drawEllipse(QRectF(38, 101, 54, 54))
    painter.drawEllipse(QRectF(164, 101, 54, 54))

    painter.setPen(QPen(lime, 13, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(98, 105), QPointF(151, 105))
    painter.drawLine(QPointF(158, 151), QPointF(105, 151))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(QPolygonF([QPointF(159, 105), QPointF(140, 91), QPointF(140, 119)]))
    painter.drawPolygon(QPolygonF([QPointF(97, 151), QPointF(116, 137), QPointF(116, 165)]))
    painter.end()
    return QIcon(pixmap)
