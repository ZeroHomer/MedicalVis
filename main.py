from PyQt5 import QtWidgets
import sys

from PyQt5.QtGui import QFont
from MyWidget import MyWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    font = QFont("Consolas", 10)
    app.setFont(font)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())