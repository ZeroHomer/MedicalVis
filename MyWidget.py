import traceback
import typing

from Manager import DataManager
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QLineEdit, QHBoxLayout, QGridLayout, QFileDialog
from matplotlib.figure import Figure
from pyvistaqt import QtInteractor, MainWindow
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, window, dataManager):
        super().__init__(window)
        self.window = window
        self.dataManager = dataManager
        self.menuNameDict = {'File': ['Open', 'Save'],
                             'Edit': ['Undo'],
                             'Process': [
                                 {'Blur': ['Average', 'Median', 'Gussian']},
                                 'Sharpen',
                                 {'FFT': ['FFT', 'Inverse FFT']}
                             ]
                             }

        self.actionTriggerDict = {'File': [self.open, self.save],
                                  'Edit': [self.undo],

                                  'Process': [
                                      {'Blur': [self.average_blur,
                                                self.median_blur,
                                                self.gussian_blur]},
                                      self.sharpen,
                                      {'FFT': [self.fft, self.inverse_fft]}]
                                  }

        for key in self.menuNameDict:
            menu = self.addMenu(key)
            items = self.menuNameDict[key]
            triggers = self.actionTriggerDict[key]
            self.__addItems(items, triggers, menu)

    def __addItems(self, items, triggers, menu: QtWidgets.QMenu):
        '''
        :param items: A list (may contains sub menu)
        :param triggers: A list contains the trigger functions
        :param menu: the menu where the items added into
        :return: None
        '''
        for item, trigger in zip(items, triggers):
            if type(item) == type({}):
                for key in item:
                    submenu = QtWidgets.QMenu(key, menu)
                    self.__addItems(item[key], trigger[key], submenu)
                    menu.addAction(submenu.menuAction())

            else:
                action = QtWidgets.QAction(item, menu)
                action.triggered.connect(trigger)
                menu.addAction(action)

    # 处理函数
    def open(self):
        if self.window == None:
            return

        filePath = QFileDialog.getOpenFileName(caption="open file dialog")[0]
        if len(filePath) == 0:
            return
        try:
            self.dataManager.read_data(filePath)
            self.window.display()
        except Exception as e:
            print(e)
            traceback.print_exc()

    def save(self):
        pass

    def undo(self):
        pass

    def average_blur(self):
        """均值过滤"""
        newDataManager = self.dataManager.average_blur()
        self.displayInOtherWindow(dataManager=newDataManager)

    def median_blur(self):
        """中值过滤"""
        pass

    def gussian_blur(self):
        pass

    def sharpen(self):
        pass

    def fft(self):
        pass

    def inverse_fft(self):
        pass

    def displayInOtherWindow(self, dataManager):
        try:
            subWindow = self.window.createSubWindow(title=self.window.windowTitle() + 'sub', dataManager=dataManager)
            subWindow.show()
            subWindow.display()
        except Exception as e:
            print(e)
            traceback.print_exc()


class ConfigWidget(QtWidgets.QWidget):

    def __init__(self, window) -> None:
        super().__init__(window)
        self.window = window
        colorMapLabel = QLabel(self)
        colorMapLabel.setText('color map')
        opacityLabel = QLabel(self)
        opacityLabel.setText('opacity')

        colorMapItem = ['gray', 'cool', 'viridis']
        self.colorMapComboBox = QComboBox(self)
        for item in colorMapItem:
            self.colorMapComboBox.addItem(item)
        opacityItem = ['linear', 'linear_r', 'geom', 'geom_r']
        self.opacityComboBox = QComboBox(self)
        for item in opacityItem:
            self.opacityComboBox.addItem(item)

        self.colorMapComboBox.currentIndexChanged.connect(self.update)
        self.opacityComboBox.currentIndexChanged.connect(self.update)

        # 创建水平布局
        # layout = QGridLayout()
        # layout.addWidget(opacityLabel,0,0)
        # layout.addWidget(opacityComboBox,0,1)
        layout = QHBoxLayout()
        layout.addWidget(colorMapLabel)
        layout.addWidget(self.colorMapComboBox)
        layout.addWidget(opacityLabel)
        layout.addWidget(self.opacityComboBox)
        self.setLayout(layout)

    def update(self):
        opacity = self.opacityComboBox.currentText()
        colorMap = self.colorMapComboBox.currentText()
        self.window.display(cmap=colorMap, opacity=opacity)


class MyWindow(MainWindow):

    def __init__(self, parent=None, title='', isVolumeData=False, dataManager=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.dataManager = dataManager
        self.subWindows = []
        if dataManager == None:
            self.dataManager = DataManager()

        self.setWindowTitle(title)
        # create the frame
        self.frame = QtWidgets.QFrame()
        self.vlayout = QtWidgets.QVBoxLayout()

        self.isVolumeData = isVolumeData
        menubar = None
        # 添加菜单
        menubar = MenuBar(self, self.dataManager)
        self.vlayout.addWidget(menubar)

        # 添加Config组件
        configWidget = ConfigWidget(self)
        self.vlayout.addWidget(configWidget)
        self.frame.setLayout(self.vlayout)
        self.setCentralWidget(self.frame)

        # 添加显示组件
        self.displayWidget = None
        # plotter 显示3D数据
        self.plotter = QtInteractor(self.frame)
        self.display3DWidget = self.plotter.interactor
        # matplotlib 显示2D数据
        figure = Figure()
        self.ax = figure.add_subplot(111)
        self.display2DWidget = FigureCanvas(figure)

        if (self.isVolumeData):
            self.displayWidget = self.display3DWidget
            self.display2DWidget.setVisible(False)
        else:
            self.displayWidget = self.display2DWidget
            self.display3DWidget.setVisible(False)

        self.vlayout.addWidget(self.displayWidget)  # 默认展示界面为matplotlib
        # self.signal_close.connect(self.plotter.close)

        # 设置背景颜色
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(255, 255, 255))

        self.setPalette(palette)

    def createSubWindow(self, title='', isVolumeData=False, dataManager=None):
        subWindow = MyWindow(title=title, isVolumeData=isVolumeData, dataManager=dataManager)
        self.subWindows.append(subWindow)

        return self.subWindows[-1]

    # def display(self, data, cmap=None):
    #     if (data.shape[-1] == 1 or data.shape[-1] == 3):
    #         # 2维灰度图像或RGB图像
    #         self.display2d(data, cmap)
    #     else:
    #
    #         self.display3d(data, cmap)

    def display(self, cmap='gray', opacity='linear'):
        data = self.dataManager.ugrid_data
        if (data == None):
            self.display3d(cmap, opacity)
        else:
            # 2维灰度图像或RGB图像
            self.display2d(cmap)


    def display3d(self, cmap=None, opacity=None):
        data = self.dataManager.ugrid_data
        if (self.isVolumeData):
            # 正在显示的是体数据，组件不改变
            self.plotter.update()
            self.plotter.add_volume(data, cmap=cmap, opacity=opacity)
        else:
            # 正在显示的是灰度图像数据或RGB图像数据，改变组件
            self.displayWidget.setVisible(False)
            self.vlayout.removeWidget(self.displayWidget)
            self.displayWidget = self.display3DWidget
            self.vlayout.addWidget(self.displayWidget)
            self.displayWidget.setVisible(True)

            self.plotter.update()
            self.plotter.add_volume(data, cmap=cmap, opacity=opacity)
            self.isVolumeData = True

    def display2d(self, cmap='gray'):
        data = self.dataManager.numpy_data
        if (not self.isVolumeData):
            # 正在显示的是灰度图像数据或RGB图像数据，组件不变
            # self.ax.redraw_in_frame()
            self.ax.imshow(data, cmap=cmap)
            self.displayWidget.draw()
        else:
            # 正在显示的是体数据，组件改变
            self.displayWidget.setVisible(False)
            self.vlayout.removeWidget(self.displayWidget)
            self.displayWidget = self.display2DWidget
            self.vlayout.addWidget(self.displayWidget)
            self.displayWidget.setVisible(True)

            self.ax.imshow(data, cmap=cmap)
            self.displayWidget.draw()
            self.isVolumeData = False

    def closeEvent(self, event: QtCore.QEvent) -> None:
        super().closeEvent(event)
        self.display2DWidget.close()
        self.display3DWidget.close()
