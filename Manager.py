import SimpleITK as sitk
import numpy as np
import cv2
import pyvista
from pyvista.utilities import wrap

class DataManager:
    def __init__(self, numpy_data=None) -> None:
        self.numpy_data = numpy_data
        self.read_func_dict = {'DCM': self.read_dcm, 'dcm': self.read_dcm, 'nii': self.read_nii, 'gz': self.read_nii,
                               'jpg': self.read_normal_type, 'png': self.read_normal_type}
        if(self.numpy_data and self.is3D(self.numpy_data)):
            self.ugrid_data = wrap(self.numpy_data) # UniformGrid类，使用该类做三维数据处理
        # self.operateHistory = []

    def read_data(self, file_path):
        file_type = file_path[file_path.rfind('.') + 1:]
        read_func = self.read_func_dict[file_type]
        self.numpy_data = read_func(file_path)
        if (self.is3D(self.numpy_data)):
            self.ugrid_data = wrap(self.numpy_data)  # UniformGrid类，使用该类做三维数据处理

        else:
            self.upgrid_data = None
        return self.numpy_data

    def read_dcm(self, file_path):
        simpleITK_data = sitk.ReadImage(file_path)
        numpy_data = sitk.GetArrayFromImage(simpleITK_data)  # (Depth, Height, Width)
        numpy_data = numpy_data.transpose(2, 1, 0)
        return numpy_data

    def read_nii(self, file_path):
        '''nii 文件为3d数据'''
        simpleITK_data = sitk.ReadImage(file_path)
        numpy_data = sitk.GetArrayFromImage(simpleITK_data)  # (Depth, Height, Width)
        return numpy_data

    def read_normal_type(self, file_path):
        simpleITK_data = sitk.ReadImage(file_path)
        numpy_data = sitk.GetArrayFromImage(simpleITK_data)

        return self.modify_demension(numpy_data)

    def read_slc(self, file_path):
        # cleanup artifact
        dataset = pyvista.read(file_path)
        mask = dataset['SLCImage'] == 255
        dataset['SLCImage'][mask] = 0

        return dataset

    def average_blur(self, kernel_size=(3, 3)):
        """均值滤波"""
        blurred_img = cv2.blur(self.numpy_data, ksize=kernel_size)
        blurred_img = self.modify_demension(blurred_img)
        return DataManager(blurred_img)


    def is3D(self,data):
        if len(data.shape[-1]==1 or data.shape[-1]==3):
            return False
        return True

    def modify_demension(self, numpy_data):
        '''修改numpy数据维度，灰度二维图像数据读入或修改时没有通道维度'''
        if (len(numpy_data.shape) == 2):
            numpy_data = numpy_data[:, :, np.newaxis]
        return numpy_data


if __name__ == '__main__':
    dm = DataManager()
    # dm.read_slc('E:\Study\Visualization\Assignment\MedicalVis\data\embryo.slc')
    p = pyvista.Plotter()
    data = dm.read_nii('E:\Study\Visualization\Assignment\MedicalVis\data\T1_preprocessed.nii.gz')
    data = wrap(data)

    p.add_volume(data)
    p.show()