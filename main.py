from PyQt5 import QtWidgets
import sys
from MyWidget import MyWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())