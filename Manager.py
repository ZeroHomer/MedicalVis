import random

import SimpleITK as sitk
import pydicom
import imageio
import numpy as np
from PIL import Image, ImageFilter
import pyvista
from matplotlib import pyplot as plt
from pyvista.utilities import wrap
from scipy import ndimage
from skimage import exposure, img_as_float

from skimage import filters
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
        self.dcm_data=None
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

        if not (file_type=='DCM' or file_type=='dcm'):
            self.dcm_data = None


    def save_data(self,file_path):
        file_type = file_path[file_path.rfind('.') + 1:]

        if(file_type=='nii'):
            image = sitk.GetImageFromArray(self.numpy_data)
            sitk.WriteImage(image, file_path)
            return

        if(self.ugrid_data!=None):
            self.ugrid_data.save(file_path)
        else:
            imageio.imsave(file_path,self.numpy_data)


    def read_dcm(self, file_path):
        self.dcm_data = pydicom.read_file(file_path,force=True)
        numpy_data = self.dcm_data.pixel_array
        numpy_data = self.modify_demension(numpy_data)
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

    def fft(self):
        if self.ugrid_data != None:
            result = np.fft.fftn(self.numpy_data)
            result = np.abs(result)
            result = result.astype(np.uint8)
            return DataManager(result)
        else:
            result = np.fft.fft2(self.numpy_data)
            result = np.abs(result)
            result = result.astype(np.uint8)
            return DataManager(result)

    def shift_fft(self):
        if self.ugrid_data != None:
            result = np.fft.fftshift(self.numpy_data)
            return DataManager(result)
        else:
            result = np.fft.fftshift(self.numpy_data)
            return DataManager(result)

    def maximum_filter(self):
        result = ndimage.maximum_filter(self.numpy_data, size=20)
        return DataManager(result)

    def minimum_filter(self):
        result = ndimage.minimum_filter(self.numpy_data, size=20)
        return DataManager(result)

    def uniform_filter(self):
        """"""
        if self.ugrid_data == None:
            blurred_img = ndimage.uniform_filter(self.numpy_data, size=20)
            return DataManager(blurred_img)
        else:
            blurred_img = ndimage.uniform_filter(self.numpy_data, size=20)
            return DataManager(blurred_img)

    def median_blur(self):
        """中值过滤"""
        result = ndimage.median_filter(self.numpy_data, size=3)
        return DataManager(result)

    def gaussian_blur(self):
        '''高斯过滤'''
        result = ndimage.gaussian_filter(self.numpy_data, sigma=5)
        return DataManager(result)

    def gray(self, n):
        try:
            # 把图像的像素值转换为浮点数
            img = img_as_float(self.numpy_data)
            # 使用伽马调整
            # 第二个参数控制亮度，大于1增强亮度，小于1降低。
            if n:
                data = exposure.adjust_gamma(img, 1.5)
            else:
                data = exposure.adjust_gamma(img, 0.8)
                # data = exposure.adjust_log(img, 0.8)
        except Exception as e:
            img = img_as_float(self.numpy_data)
            minImg = np.min(img)
            maxImg = np.max(img)
            img = (img-minImg)/(maxImg-minImg)
            if n:
                data = exposure.adjust_gamma(img, 5)
            else:
                data = exposure.adjust_gamma(img, 0.5)
        return DataManager(data)



    def Salt_noice(self):
        if len(self.numpy_data.shape) == 3:
            rows, cols, dims = self.numpy_data.shape
            if dims == 3:
                Grey_sp = self.numpy_data
                snr = 0.9
                noise_num = int((1 - snr) * rows * cols)

                for i in range(noise_num):
                    rand_x = random.randint(0, rows - 1)
                    rand_y = random.randint(0, cols - 1)
                    if random.randint(0, 1) == 0:
                        Grey_sp[rand_x, rand_y, 0] = 0
                        Grey_sp[rand_x, rand_y, 1] = 0
                        Grey_sp[rand_x, rand_y, 2] = 0
                    else:
                        Grey_sp[rand_x, rand_y, :] = 255
                        Grey_sp[rand_x, rand_y, 1] = 255
                        Grey_sp[rand_x, rand_y, 2] = 255

            elif dims == 1:
                Grey_sp = self.numpy_data
                snr = 0.9
                noise_num = int((1 - snr) * rows * cols)

                for i in range(noise_num):
                    rand_x = random.randint(0, rows - 1)
                    rand_y = random.randint(0, cols - 1)
                    if random.randint(0, 1) == 0:
                        Grey_sp[rand_x, rand_y, 0] = 0
                    else:
                        Grey_sp[rand_x, rand_y, 0] = 255

            elif dims > 3:
                Grey_sp = self.numpy_data
                snr = 0.9
                noise_num = int((1 - snr) * rows * cols)

                for i in range(noise_num):
                    rand_x = random.randint(0, rows - 1)
                    rand_y = random.randint(0, cols - 1)
                    rand_z = random.randint(0, dims - 1)
                    if random.randint(0, 1) == 0:
                        Grey_sp[rand_x, rand_y, rand_z] = 0
                    else:
                        Grey_sp[rand_x, rand_y, rand_z] = 255
        else:
            rows, cols = self.numpy_data.shape
            R = np.mat(self.numpy_data[:, :])
            G = np.mat(self.numpy_data[:, :])
            B = np.mat(self.numpy_data[:, :])
            Grey_sp = R * 0.299 + G * 0.587 + B * 0.114
            snr = 0.9
            noise_num = int((1 - snr) * rows * cols)

            for i in range(noise_num):
                rand_x = random.randint(0, rows - 1)
                rand_y = random.randint(0, cols - 1)
                if random.randint(0, 1) == 0:
                    Grey_sp[rand_x, rand_y] = 0
                else:
                    Grey_sp[rand_x, rand_y] = 255

        return DataManager(Grey_sp)

    def Gaussian_noice(self):
        if len(self.numpy_data.shape) == 3:
            rows, cols, dims = self.numpy_data.shape
            if dims == 3:
                Grey_gs = self.numpy_data
            elif dims == 1:
                Grey_gs = self.numpy_data
            elif dims > 3:
                pass
        else:
            Grey_gs = self.numpy_date

        # 给图像加入高斯噪声
        Grey_gs = Grey_gs + np.random.normal(0, 48, Grey_gs.shape)
        Grey_gs = Grey_gs - np.full(Grey_gs.shape, np.min(Grey_gs))
        Grey_gs = Grey_gs * 255 / np.max(Grey_gs)
        Grey_gs = Grey_gs.astype(np.uint8)

        return DataManager(Grey_gs)

    def drawHistorgram(self, npdata, bins=15):
        bin = []
        max = np.max(npdata)
        min = np.min(npdata)
        temp = (max - min) / bins
        for level in range(0, bins + 1):
            bin.append(min + level * temp)
        c = np.reshape(npdata, (-1))
        print(bin)
        plt.hist(c, bins=bin)
        plt.title('Historgram')
        plt.show()
        return

    def Historn(self):
        self.drawHistorgram(npdata=self.numpy_data, bins=256)

    def counterDetail(self):
        """轮廓"""
        im = self.numpy_data
        if im.shape[2] == 1:
            im = im.squeeze(-1)
        im = Image.fromarray(im.astype('uint8'))
        imq2 = im.filter(ImageFilter.CONTOUR)
        imq2 = np.array(imq2)
        if len(imq2.shape) == 2:
            imq2 = np.expand_dims(imq2, axis=2)
        return DataManager(imq2)

    def embossFilter(self):
        """浮雕"""
        im = self.numpy_data
        if im.shape[2] == 1:
            im = im.squeeze(-1)
        im = Image.fromarray(im.astype('uint8'))
        imq1 = im.filter(ImageFilter.EMBOSS)
        imq1 = np.array(imq1)
        if len(imq1.shape) == 2:
            imq1 = np.expand_dims(imq1, axis=2)
        return DataManager(imq1)

    def sharpenSobel(self):
        img = self.numpy_data
        edges = filters.sobel(img)
        return DataManager(edges)

    def sharpenPrewitt(self):
        img = self.numpy_data
        edges = filters.prewitt(img)
        return DataManager(edges)

    def sharpenLaplace(self):
        img = self.numpy_data
        edges = filters.laplace(img)
        return DataManager(edges)

    def sharpen2D(self):
        """锐化操作 对2d图像"""
        s = self.numpy_data
        if s.shape[2] == 1:
            s = s.squeeze(-1)
        im = Image.fromarray(s.astype('uint8'))
        s = im.filter(ImageFilter.SHARPEN)
        s = s.filter(ImageFilter.SHARPEN)
        s = s.filter(ImageFilter.SHARPEN)
        s = np.array(s)
        if len(s.shape) == 2:
            s = np.expand_dims(s, axis=2)
        return DataManager(s)

    def modify_demension(self, numpy_data):
        '''修改numpy数据维度，灰度二维图像数据读入或修改时没有通道维度'''
        if (len(numpy_data.shape) == 2):
            numpy_data = numpy_data[:, :, np.newaxis]
        return numpy_data


