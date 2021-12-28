import SimpleITK as sitk
import numpy as np
import cv2
import pyvista
from pyvista.utilities import wrap


class DataManager:
    def __init__(self, numpy_data=None) -> None:
        self.numpy_data = numpy_data
        self.read_func_dict = {'DCM': self.read_dcm, 'dcm': self.read_dcm, 'nii': self.read_nii, 'gz': self.read_nii,
                               'slc': self.read_slc, 'vtk':self.read_3d_normal_type,'pvtk':self.read_3d_normal_type,
                               'vti': self.read_3d_normal_type,'pvti':self.read_3d_normal_type,'vtr':self.read_3d_normal_type,
                               'pvtr': self.read_3d_normal_type,'vtu':self.read_3d_normal_type,'pvtu':self.read_3d_normal_type,
                               'obj': self.read_3d_normal_type,'vtp':self.read_3d_normal_type,'ply':self.read_3d_normal_type,
                               'jpg': self.read_normal_type, 'png': self.read_normal_type,'tif':self.read_normal_type,
                               'jpeg':self.read_normal_type,'bmp':self.read_normal_type}
        self.ugrid_data = None
        if type(numpy_data)!=type(None) and not (numpy_data.shape[-1] == 1 or numpy_data.shape[-1] == 3):
            self.ugrid_data = wrap(numpy_data)  # UniformGrid类，使用该类做三维数据处理

    def read_data(self, file_path):
        file_type = file_path[file_path.rfind('.') + 1:]
        read_func = self.read_func_dict[file_type]
        data = read_func(file_path)
        if (data.__class__.__name__=='tuple'):
            # 3D体数据
            self.numpy_data, self.ugrid_data = data[0], data[1]  # UniformGrid类，使用该类做三维数据处理
        else:
            self.numpy_data, self.ugrid_data = data, None

        # return self.numpy_data

    def save_data(self,file_path):
        file_type = file_path[file_path.rfind('.') + 1:]

        if(self.ugrid_data!=None and file_type!='nii'):
            self.ugrid_data.save(file_path)
        else:
            image = sitk.GetImageFromArray(self.numpy_data)
            sitk.WriteImage(image, file_path)

    def read_dcm(self, file_path):
        simpleITK_data = sitk.ReadImage(file_path)
        numpy_data = sitk.GetArrayFromImage(simpleITK_data)  # (Depth, Height, Width)
        numpy_data = numpy_data.transpose(2, 1, 0)
        return numpy_data

    def read_nii(self, file_path):
        '''nii 文件为3d数据'''
        simpleITK_data = sitk.ReadImage(file_path)
        numpy_data = sitk.GetArrayFromImage(simpleITK_data)  # (Depth, Height, Width)
        grid_data = self.convert_numpy_to_grid(numpy_data)
        return numpy_data, grid_data

    def read_normal_type(self, file_path):
        simpleITK_data = sitk.ReadImage(file_path)
        numpy_data = sitk.GetArrayFromImage(simpleITK_data)

        return self.modify_demension(numpy_data)

    def read_slc(self, file_path):
        # cleanup artifact
        grid_data = pyvista.read(file_path)
        mask = grid_data['SLCImage'] == 255
        grid_data['SLCImage'][mask] = 0
        numpy_data = self.convert_grid_to_numpy(grid_data)
        return numpy_data, grid_data

    def read_3d_normal_type(self,file_path):
        grid_data = pyvista.read(file_path)
        numpy_data = self.convert_grid_to_numpy(grid_data)
        return numpy_data, grid_data

    def convert_numpy_to_grid(self, numpy_data):
        """numpy_data要为3D体数据"""
        return wrap(numpy_data)

    def convert_grid_to_numpy(self, grid_data):
        numpy_data = grid_data[grid_data.array_names[0]]
        numpy_data = numpy_data.reshape(grid_data.dimensions)
        return numpy_data

    def average_blur(self, kernel_size=(3, 3)):
        """均值滤波"""
        blurred_img = cv2.blur(self.numpy_data, ksize=kernel_size)
        blurred_img = self.modify_demension(blurred_img)
        return DataManager(blurred_img)

    def modify_demension(self, numpy_data):
        '''修改numpy数据维度，灰度二维图像数据读入或修改时没有通道维度'''
        if (len(numpy_data.shape) == 2):
            numpy_data = numpy_data[:, :, np.newaxis]
        return numpy_data


