from PyQt5 import QtWidgets
import sys

from YKWMyWidget import MyWindow
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())