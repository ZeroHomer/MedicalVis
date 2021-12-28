import traceback


from PyQt5.QtCore import Qt
import time
from Manager import DataManager
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QLineEdit, QHBoxLayout, QGridLayout, QFileDialog, QPushButton, \
    QMessageBox, QTextEdit
from matplotlib.figure import Figure
from pyvistaqt import QtInteractor, MainWindow
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

colormaps3d = plt.colormaps()
colormaps2d = plt.colormaps()
colormaps2d[0], colormaps2d[57] = colormaps2d[57], colormaps2d[0]
saveFileType3DStr = "(*.vtk);;(*.pvtk);;(*.vti);;(*.pvti);;(*.vtr);;(*.pvtr);;(*.vtu);;(*.pvtu);;(*.obj);;(*.vtp);;(*.slc);;"
saveFileType2DStr = "(*.jpeg);;(*.jpg);;(*.png);;(*.bmp)"


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, window, dataManager):
        super().__init__(window)
        self.window = window
        self.dataManager = dataManager

        self.menuNameDict = {'File': ['Open', {'Save': ['Save File', 'Save screenshots']}],
                             'View': ['Iso-surface', 'Slice', '3D-config', '2D-config', 'DCM-info'],
                             'Process': [
                                 {'Filter': ['Uniform', 'Median', 'Gaussian', 'Maximum', 'Minimum']},
                                 {'FFT': ['FFT', 'FFT shift']},
                                 {'Gray': ['High', 'Low']},
                                 {'Noise': ['Salt', 'Gaussian']},
                                 {'Sharpen': ['Sobel', 'Prewitt', 'Laplace']},
                                 'Counter',
                                 'Emboss',
                                 'Historgram'
                             ]
                             }

        self.actionTriggerDict = {'File': [self.open, {'Save': [self.save_file, self.save_screenshots]}],
                                  'View': [self.iso_surface, self.slice, self.display3DConfig, self.display2DConfig,self.dcm_info],
                                  'Process': [
                                      {'Filter': [
                                          self.uniform_filter,
                                          self.median_blur,
                                          self.gaussian_blur,
                                          self.maximum_filter,
                                          self.minimum_filter
                                      ]},

                                      {'FFT': [self.fft, self.shift_fft]},
                                      {'Gray': [self.highGray, self.lowGray]},
                                      {'Noise': [self.Salt_noice, self.Gaussian_noice]},
                                      {
                                          'Sharpen': [
                                              self.sobel,
                                              self.prewitt,
                                              self.laplace
                                          ]
                                      },
                                      self.counter,
                                      self.emboss,
                                      self.his
                                  ]
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

        file_path = QFileDialog.getOpenFileName(caption="open file dialog")[0]
        if len(file_path) == 0:
            return
        try:
            self.dataManager.read_data(file_path)
            self.window.display()
        except Exception as e:
            print(e)
            traceback.print_exc()

    def save_file(self):
        try:
            file_path = None
            if self.dataManager.ugrid_data != None:
                # 保存三维数据
                file_path = QFileDialog.getSaveFileName(caption='Save file', filter=saveFileType3DStr)[0]
            else:
                file_path = QFileDialog.getSaveFileName(caption='Save file', filter=saveFileType2DStr)[0]
            if (file_path != ''):
                self.dataManager.save_data(file_path)
        except Exception as e:
            traceback.print_exc()

    def save_screenshots(self):
        if (self.dataManager.ugrid_data == None):
            QMessageBox.critical(self, '错误', '只有导入三维体数据才能截图', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return
        filePath = QFileDialog.getExistingDirectory(caption='Save file dialog')
        name = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())
        filePath = filePath + '/' + name + '.png'

        try:
            self.window.plotter.screenshot(filePath)
        except:
            traceback.print_exc()

    def maximum_filter(self):
        newDataManager = self.dataManager.maximum_filter()
        self.displayInOtherWindow(dataManager=newDataManager)

    def minimum_filter(self):
        newDataManager = self.dataManager.minimum_filter()
        self.displayInOtherWindow(dataManager=newDataManager)

    def uniform_filter(self):
        """"""
        newDataManager = self.dataManager.uniform_filter()
        self.displayInOtherWindow(dataManager=newDataManager)

    def median_blur(self):
        """中值过滤"""
        newDataManager = self.dataManager.median_blur()
        self.displayInOtherWindow(dataManager=newDataManager)

    def gaussian_blur(self):
        newDataManager = self.dataManager.gaussian_blur()
        self.displayInOtherWindow(dataManager=newDataManager)

    def sharpen(self):
        pass

    def fft(self):
        newDataManager = self.dataManager.fft()
        self.displayInOtherWindow(dataManager=newDataManager)

    def shift_fft(self):
        newDataManager = self.dataManager.shift_fft()
        self.displayInOtherWindow(dataManager=newDataManager)

    def displayInOtherWindow(self, dataManager):
        try:
            subWindow = self.window.createSubWindow(title=self.window.windowTitle() + 'sub', dataManager=dataManager)
            subWindow.show()
            subWindow.display()
        except Exception as e:
            print(e)
            traceback.print_exc()

    def iso_surface(self):
        if (self.dataManager.ugrid_data != None):
            self.window.isoSurfaceWidget = IsoSurfaceWidget(self.dataManager.ugrid_data)
            self.window.isoSurfaceWidget.show()

    def slice(self):
        if (self.dataManager.ugrid_data != None):
            self.window.sliceWidget = SliceWidget(self.dataManager.ugrid_data)
            self.window.sliceWidget.show()

    def dcm_info(self):
        if (self.dataManager.dcm_data != None):
            try:
                self.window.dcmInfoWidget = DCMInfoWidget(self.dataManager.dcm_data)
                self.window.dcmInfoWidget.show()
            except :
                traceback.print_exc()
    def highGray(self):
        try:
            newDataManager = self.dataManager.gray(1)
            self.displayInOtherWindow(newDataManager)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def lowGray(self):
        try:
            newDataManager = self.dataManager.gray(0)
            self.displayInOtherWindow(newDataManager)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def Salt_noice(self):
        try:
            newDataManager = self.dataManager.Salt_noice()
            self.displayInOtherWindow(newDataManager)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def Gaussian_noice(self):
        try:
            newDataManager = self.dataManager.Gaussian_noice()
            self.displayInOtherWindow(newDataManager)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def counter(self):
        """轮廓"""
        newDataManager = self.dataManager.counterDetail()
        self.displayInOtherWindow(dataManager=newDataManager)

    def his(self):
        self.dataManager.Historn()

    def emboss(self):
        """浮雕"""
        newDataManager = self.dataManager.embossFilter()
        self.displayInOtherWindow(dataManager=newDataManager)

    def sobel(self):
        """sobel算子"""
        newDataManager = self.dataManager.sharpenSobel()
        self.displayInOtherWindow(dataManager=newDataManager)

    def prewitt(self):
        """prewitt算子"""
        newDataManager = self.dataManager.sharpenPrewitt()
        self.displayInOtherWindow(dataManager=newDataManager)

    def laplace(self):
        """拉普拉斯算子"""
        newDataManager = self.dataManager.sharpenLaplace()
        self.displayInOtherWindow(dataManager=newDataManager)

    def sharpen(self):
        """锐化 2d"""
        try:
            newDataManager = self.dataManager.sharpen2D()
            self.displayInOtherWindow(dataManager=newDataManager)
        except:
            traceback.print_exc()

    def display3DConfig(self):
        if (self.dataManager.ugrid_data == None):
            QMessageBox.critical(self, '错误', '请先导入体数据', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return
        self.window.display3DC()

    def display2DConfig(self):
        if (self.dataManager.ugrid_data != None or type(self.dataManager.numpy_data) == type(None)):
            QMessageBox.critical(self, '错误', '请先导入二维图像数据', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return
        try:
            self.window.display2DC()
        except:
            traceback.print_exc()


class DCMInfoWidget(QWidget):
    def __init__(self, dcm):
        super().__init__()
        info = {}

        info["PatientID"] = dcm.PatientID  # 患者ID
        info["PatientName"] = dcm.PatientName  # 患者姓名
        info["PatientBirthData"] = dcm.PatientBirthDate  # 患者出生日期
        info["PatientAge"] = dcm.PatientAge  # 患者年龄
        info['PatientSex'] = dcm.PatientSex  # 患者性别
        info['StudyID'] = dcm.StudyID  # 检查ID
        info['StudyDate'] = dcm.StudyDate  # 检查日期
        info['StudyTime'] = dcm.StudyTime  # 检查时间
        info['InstitutionName'] = dcm.InstitutionName  # 机构名称
        info['Manufacturer'] = dcm.Manufacturer  # 设备制造商
        info['StudyDescription'] = dcm.StudyDescription  # 检查项目描述

        self.infoText = QTextEdit()
        self.vlayout = QtWidgets.QVBoxLayout()
        self.vlayout.addWidget(self.infoText)
        for key in info:
            self.infoText.insertPlainText(key + ':\t' + str(info[key])+'\n')

        self.infoText.setReadOnly(True)
        self.setLayout(self.vlayout)
        self.setWindowTitle('DCM Info')

class IsoSurfaceWidget(QtWidgets.QWidget):
    def __init__(self, volumeData):
        super().__init__()
        self.volumeData = volumeData
        rangeLabel = QLabel(self)
        rangeLabel.setText('Range: ')
        noteLabel = QLabel(self)
        noteLabel.setText("to")
        numLabel = QLabel(self)
        numLabel.setText("Number:")
        opacityLabel = QLabel(self)
        opacityLabel.setText("Opacity(0~1):")

        self.leftRangeLineEdit = QLineEdit()
        self.rightRangeLineEdit = QLineEdit()
        self.numLineEdit = QLineEdit()
        self.opacityLineEdit = QLineEdit()

        # 添加按钮
        self.drawBtn = QPushButton('Draw', self)
        self.screenshotBtn = QPushButton('Screenshot', self)
        # 添加显示组件
        self.frame = QtWidgets.QFrame()
        self.plotter = QtInteractor(self.frame)
        self.display3DWidget = self.plotter.interactor

        gridLayout = QGridLayout()
        gridLayout.addWidget(self.display3DWidget, 0, 0, 85, 1)
        gridLayout.addWidget(rangeLabel, 0, 1)

        gridLayout.addWidget(self.leftRangeLineEdit, 0, 2)
        gridLayout.addWidget(noteLabel, 0, 3)
        gridLayout.addWidget(self.rightRangeLineEdit, 0, 4)

        gridLayout.addWidget(numLabel, 1, 1)
        gridLayout.addWidget(self.numLineEdit, 1, 2)

        gridLayout.addWidget(opacityLabel, 2, 1)
        gridLayout.addWidget(self.opacityLineEdit, 2, 2)

        gridLayout.addWidget(self.drawBtn, 3, 1)
        gridLayout.addWidget(self.screenshotBtn, 3, 2)

        gridLayout.setColumnStretch(0, 7)
        gridLayout.setColumnStretch(2, 1)
        gridLayout.setColumnStretch(4, 1)

        # 绑定事件
        self.drawBtn.clicked.connect(self.draw)
        self.screenshotBtn.clicked.connect(self.screenshot)

        self.setLayout(gridLayout)
        self.setWindowTitle('Iso-surface')

    def draw(self):
        try:
            start = int(self.leftRangeLineEdit.text())
            stop = int(self.rightRangeLineEdit.text())
            num = int(self.numLineEdit.text())
            opacity = float(self.opacityLineEdit.text())
            if (start > stop):
                QMessageBox.critical(self, '错误', '起始范围不能大于结束范围', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            if (opacity < 0 or opacity > 1):
                QMessageBox.critical(self, '错误', '透明度范围为0-1', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            contours = self.volumeData.contour(np.linspace(start, stop, num))
            self.plotter.clear()
            self.plotter.add_mesh(contours, opacity=opacity)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def screenshot(self):
        filePath = QFileDialog.getExistingDirectory(caption='Save file dialog')
        name = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())
        filePath = filePath + '/' + name + '.png'
        self.plotter.screenshot(filePath)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        super().closeEvent(a0)
        self.display3DWidget.close()


class SliceWidget(QtWidgets.QWidget):
    def __init__(self, volumeData):
        super().__init__()
        self.volumeData = volumeData
        # 标签
        normalVectorLabel = QLabel("Normal Vector: ")
        originPointLabel = QLabel("Origin Point: ")
        xLabel = QLabel("x")
        xLabel.setAlignment(Qt.AlignCenter)
        yLabel = QLabel("y")
        yLabel.setAlignment(Qt.AlignCenter)
        zLabel = QLabel("z")
        zLabel.setAlignment(Qt.AlignCenter)
        # 输入框
        self.normalXLineEdit = QLineEdit()
        self.normalYLineEdit = QLineEdit()
        self.normalZLineEdit = QLineEdit()
        self.originXLineEdit = QLineEdit()
        self.originYLineEdit = QLineEdit()
        self.originZLineEdit = QLineEdit()

        # 按钮
        self.sliceBtn = QPushButton("slice")
        self.screenshotBtn = QPushButton('Screenshot', self)

        # 显示组件
        self.frame = QtWidgets.QFrame()

        self.plotter = QtInteractor(self.frame)
        self.display3DWidget = self.plotter.interactor
        # self.display3DWidget.setBaseSize(500,900)
        # 布局
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.display3DWidget, 0, 0, 85, 1)

        gridLayout.addWidget(xLabel, 0, 2)
        gridLayout.addWidget(yLabel, 0, 3)
        gridLayout.addWidget(zLabel, 0, 4)

        gridLayout.addWidget(normalVectorLabel, 1, 1)
        gridLayout.addWidget(self.normalXLineEdit, 1, 2)
        gridLayout.addWidget(self.normalYLineEdit, 1, 3)
        gridLayout.addWidget(self.normalZLineEdit, 1, 4)

        gridLayout.addWidget(originPointLabel, 2, 1)
        gridLayout.addWidget(self.originXLineEdit, 2, 2)
        gridLayout.addWidget(self.originYLineEdit, 2, 3)
        gridLayout.addWidget(self.originZLineEdit, 2, 4)

        gridLayout.addWidget(self.sliceBtn, 3, 1)
        gridLayout.addWidget(self.screenshotBtn, 3, 2)

        gridLayout.setColumnStretch(0, 6)
        gridLayout.setColumnStretch(2, 1)
        gridLayout.setColumnStretch(3, 1)
        gridLayout.setColumnStretch(4, 1)

        self.sliceBtn.clicked.connect(self.slice)
        self.screenshotBtn.clicked.connect(self.screenshot)

        self.setLayout(gridLayout)
        self.setWindowTitle('Slice')

    def slice(self):
        normal = (
            float(self.normalXLineEdit.text()), float(self.normalYLineEdit.text()), float(self.normalZLineEdit.text()))
        origin = (
            float(self.originXLineEdit.text()), float(self.originYLineEdit.text()), float(self.originZLineEdit.text()))
        # normal = np.array(normal)
        # normal = normal/np.linalg.norm(normal) #向量正交
        slices = self.volumeData.slice(normal=normal, origin=origin)

        self.display3DWidget.clear()
        self.display3DWidget.add_mesh(self.volumeData.outline())
        self.display3DWidget.add_mesh(slices)

    def screenshot(self):
        filePath = QFileDialog.getExistingDirectory(caption='Save file dialog')
        name = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())
        filePath = filePath + '/' + name + '.png'
        self.plotter.screenshot(filePath)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        super().closeEvent(a0)
        self.display3DWidget.close()


class Config2DWidget(QtWidgets.QWidget):
    def __init__(self, window) -> None:
        super().__init__(window)
        self.window = window
        colorMapLabel = QLabel(self)
        colorMapLabel.setText('color map')
        colorMapItem = colormaps2d
        self.colorMapComboBox = QComboBox(self)
        for item in colorMapItem:
            self.colorMapComboBox.addItem(item)
        self.colorMapComboBox.currentIndexChanged.connect(self.update)
        layout = QHBoxLayout()
        layout.addWidget(colorMapLabel)
        layout.addWidget(self.colorMapComboBox)

        self.setLayout(layout)

    def update(self):
        colorMap = self.colorMapComboBox.currentText()
        try:
            self.window.updateImageRender(self.window.dataManager.numpy_data, colorMap)
        except:
            traceback.print_exc()


class Config3DWidget(QtWidgets.QWidget):

    def __init__(self, window) -> None:
        super().__init__(window)
        self.window = window
        colorMapLabel = QLabel(self)
        colorMapLabel.setText('color map')
        opacityLabel = QLabel(self)
        opacityLabel.setText('opacity')

        colorMapItem = colormaps3d
        self.colorMapComboBox = QComboBox(self)
        for item in colorMapItem:
            self.colorMapComboBox.addItem(item)
        opacityItem = ['linear', 'linear_r', 'geom', 'geom_r', 'sigmoid', 'sigmoid_r']
        self.opacityComboBox = QComboBox(self)
        for item in opacityItem:
            self.opacityComboBox.addItem(item)

        self.colorMapComboBox.currentIndexChanged.connect(self.update)
        self.opacityComboBox.currentIndexChanged.connect(self.update)

        # 创建水平布局

        layout = QHBoxLayout()
        layout.addWidget(colorMapLabel)
        layout.addWidget(self.colorMapComboBox)
        layout.addWidget(opacityLabel)
        layout.addWidget(self.opacityComboBox)
        self.setLayout(layout)

    def update(self):
        opacity = self.opacityComboBox.currentText()
        colorMap = self.colorMapComboBox.currentText()
        try:
            self.window.updateVolumeRender(self.window.dataManager.ugrid_data, colorMap, opacity)
        except:
            traceback.print_exc()


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

        # 设置Iso-surface组件为空
        self.isoSurfaceWidget = None
        # 设置切片组件为空
        self.sliceWidget = None
        # 设置DCM信息组件为kong
        self.dcmInfoWidget = None

        # 添加Config组件
        self.config3DWidget = Config3DWidget(self)
        self.vlayout.addWidget(self.config3DWidget)
        self.conin3d = False
        self.config3DWidget.setVisible(self.conin3d)
        self.config2DWidget = Config2DWidget(self)
        self.vlayout.addWidget(self.config2DWidget)
        self.conin2d = False
        self.config2DWidget.setVisible(self.conin2d)
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

        # 设置背景颜色
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(255, 255, 255))

        self.setPalette(palette)
        self.setWindowTitle('MedicalVis')
    def createSubWindow(self, title='', isVolumeData=False, dataManager=None):
        subWindow = MyWindow(title=title, isVolumeData=isVolumeData, dataManager=dataManager)
        self.subWindows.append(subWindow)

        return self.subWindows[-1]

    def display(self, cmap=None, opacity='linear'):
        data = self.dataManager.ugrid_data
        if (data == None):
            # 2维灰度图像或RGB图像
            if (cmap == None):
                self.display2d(cmap=colormaps2d[0])
        else:
            if (cmap == None):
                self.display3d(cmap=colormaps3d[0], opacity=opacity)

    def display3d(self, cmap=None, opacity=None):
        data = self.dataManager.ugrid_data
        if (self.isVolumeData):
            # 正在显示的是体数据，组件不改变
            self.plotter.clear()
            self.plotter.update()
            self.plotter.add_volume(data, cmap=cmap, opacity=opacity)
        else:
            # 正在显示的是灰度图像数据或RGB图像数据，改变组件
            self.displayWidget.setVisible(False)
            self.vlayout.removeWidget(self.displayWidget)
            self.displayWidget = self.display3DWidget
            self.vlayout.addWidget(self.displayWidget)
            self.displayWidget.setVisible(True)
            self.plotter.clear()
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

    def display3DC(self):
        if self.conin == False:
            self.conin = True
            self.config3DWidget.setVisible(True)

        elif self.conin == True:
            self.conin = False
            self.config3DWidget.hide()

    def display2DC(self):
        try:
            self.conin2d = not self.conin2d
            self.config2DWidget.setVisible(self.conin2d)
        except:
            traceback.print_exc()

    def updateVolumeRender(self, data, cmap, opacity):
        self.plotter.clear()
        self.plotter.add_volume(data, cmap=cmap, opacity=opacity)

    def updateImageRender(self, data, cmap):
        self.ax.imshow(data, cmap=cmap)
        self.displayWidget.draw()

    def closeEvent(self, event: QtCore.QEvent) -> None:
        super().closeEvent(event)

        self.display2DWidget.close()
        self.display3DWidget.close()
