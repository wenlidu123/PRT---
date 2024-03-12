import numpy as np
from PIL import Image
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter,QIcon
from PyQt5.QtWidgets import QMessageBox
import sys
import os
import time
import shutil
from app_icon_py import *
import base64
import atexit
temp_image_path = "temp_image.tif"
with open(r'D:/app_icon.png', 'wb') as w:
    # test_mp3变量是把 .改为_ 的文件名
    w.write(base64.b64decode(app_icon_png))
class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super(CustomGraphicsView, self).__init__(scene)

    def wheelEvent(self, event):
        factor = 1.1
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1.0 / factor, 1.0 / factor)
class windows(QWidget):
    def __init__(self):
        super(windows, self).__init__()
        self.setWindowTitle('PRT转半色调tif  --Lydon')
        self.resize(800, 600)
        # 设置窗口图标
        self.setWindowIcon(QIcon('D:/app_icon.png'))
        self.bt1 = QPushButton("选择PRT文件")
        self.btDownload = QPushButton("下载图片")
        self.btDownload.setEnabled(False)

        self.scene = QGraphicsScene(self)
        self.view = CustomGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        # 使用布局管理器
        layout = QVBoxLayout()
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.bt1)
        buttonsLayout.addWidget(self.btDownload)
        layout.addWidget(self.view)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)

        self.bt1.clicked.connect(self.click_location)
        self.btDownload.clicked.connect(self.download_image)
        self.current_image_path = None

    def show_image(self, img_path):
        self.scene.clear()
        pixmap = QPixmap(img_path)
        item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(item)
        self.current_image_path = img_path
        self.btDownload.setEnabled(True)

    # 重写resizeEvent来调整view的大小
    def resizeEvent(self, event):
        super(windows, self).resizeEvent(event)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    def download_image(self):
        if self.current_image_path:
            save_path, _ = QFileDialog.getSaveFileName(self, "保存处理后的文件", "D:/",
                                                       "*.tif;;*.jpg;;*.png;;All Files(*)")
            if save_path:
                shutil.copy(self.current_image_path, save_path)  # 使用shutil复制文件

    def click_location(self):
        PRTpath, _ = QFileDialog.getOpenFileName(self, "分析色阶扫描图", "D:/",
                                                         "*.prt;;All Files(*)")
        if PRTpath:
            global time_start
            time_start = time.time()
            process(PRTpath, self)  # 修改process函数调用
class UnsupportedColorError(Exception):
    """Exception raised for unsupported number of colors in PRT file."""
    pass
def read_prt(path):
    """读取prt文件解析出cmyk四个通道，如果有则包括w通道"""
    with open(path, 'rb') as f:
        data = np.frombuffer(f.read(), dtype=np.uint8)
    # 读取PRT头部信息
    uXResolution, uYResolution, uImageWidth, uImageHeight, uGrayBits, uColors, *uReserved = data[:280].view(np.uint32)
    if uColors not in [4, 5]:
        return None, None, None, None, None, None, None,1  # 返回多个None以匹配返回值的数量



    # 确定图片每行要存储的字节数
    linebt = (uImageWidth * uGrayBits + 7) // 8
    # 建立一个全为0的跟图像像素点个数一致的一维数组
    c_channel = np.zeros((uImageWidth * uImageHeight * uGrayBits,), dtype=np.uint8)
    m_channel = np.zeros((uImageWidth * uImageHeight * uGrayBits,), dtype=np.uint8)
    y_channel = np.zeros((uImageWidth * uImageHeight * uGrayBits,), dtype=np.uint8)
    k_channel = np.zeros((uImageWidth * uImageHeight * uGrayBits,), dtype=np.uint8)
    if uColors == 5:
        w_channel = np.zeros((uImageWidth * uImageHeight * uGrayBits,), dtype=np.uint8)
    else:
        w_channel = None  # 如果uColors不是5，不处理w通道

    # 开始循环读取
    for hang in range(uImageHeight):
        # 忽略前280字节的头部信息
        start = 280 + hang * uColors * linebt
        end = start + uColors * linebt
        a = np.unpackbits(data[start:end])
        # 以流的形式读取
        c_channel[hang * uImageWidth * uGrayBits: (hang + 1) * uImageWidth * uGrayBits] = a[:uImageWidth * uGrayBits].astype(np.uint8)
        m_channel[hang * uImageWidth * uGrayBits: (hang + 1) * uImageWidth * uGrayBits] = a[uImageWidth * uGrayBits:2 * uImageWidth * uGrayBits].astype(np.uint8)
        y_channel[hang * uImageWidth * uGrayBits: (hang + 1) * uImageWidth * uGrayBits] = a[2 * uImageWidth * uGrayBits:3 * uImageWidth * uGrayBits].astype(np.uint8)
        k_channel[hang * uImageWidth * uGrayBits: (hang + 1) * uImageWidth * uGrayBits] = a[3 * uImageWidth * uGrayBits:4 * uImageWidth * uGrayBits].astype(np.uint8)
        if uColors == 5:
            w_channel[hang * uImageWidth * uGrayBits: (hang + 1) * uImageWidth * uGrayBits] = a[4 * uImageWidth * uGrayBits:5 * uImageWidth * uGrayBits].astype(np.uint8)

    # 还原成二维数组
    c_channel = c_channel.reshape((uImageHeight, uImageWidth * uGrayBits))
    m_channel = m_channel.reshape((uImageHeight, uImageWidth * uGrayBits))
    y_channel = y_channel.reshape((uImageHeight, uImageWidth * uGrayBits))
    k_channel = k_channel.reshape((uImageHeight, uImageWidth * uGrayBits))
    if uColors == 5:
        w_channel = w_channel.reshape((uImageHeight, uImageWidth * uGrayBits))
    else:
        w_channel = None

    if uGrayBits == 2:
        c_channel = c_channel[:, 1::2]
        m_channel = m_channel[:, 1::2]
        y_channel = y_channel[:, 1::2]
        k_channel = k_channel[:, 1::2]
        if w_channel is not None:
            w_channel = w_channel[:, 1::2]

    return c_channel, m_channel, y_channel, k_channel, w_channel, uXResolution, uYResolution,0
#将位图乘255
def qufan (chanel):
    final=chanel*255
    return final
def cleanup_temp_file(path=temp_image_path):
    os.remove(path)
def cleanup_icon_file(path='D:/app_icon.png'):
    os.remove(path)
#处理过程
def process (PRTpath,  window_instance):
    # 显示进度条对话框
    progressDialog = QProgressDialog("图片正在加载中...", "取消", 0, 100, window_instance)
    progressDialog.setWindowModality(Qt.WindowModal)  # 设置为模态窗口，阻塞其他窗口操作
    progressDialog.setMinimumDuration(0)  # 立即显示进度条，不延迟
    progressDialog.setValue(0)  # 设置初始进度为0
    c ,m,y,k,w, uXResolution, uYResolution,error= read_prt(PRTpath)
    if error == 1:
        progressDialog.close()  # 关闭进度条对话框
        QMessageBox.critical(window_instance, "错误", "读取PRT文件时发生错误，PRT文件不是四色或五色。")  # 显示错误消息
        # 这里可以添加任何需要的代码来返回到开始界面或重置界面状态
        return  # 退出函数

    progressDialog.setValue(20)  # 更新进度条值
    c=qufan(c)
    m=qufan(m)
    y=qufan(y)
    k=qufan(k)
    progressDialog.setValue(40)  # 继续更新进度条值
    # 将各通道图像转为PIL格式
    c_image = Image.fromarray(c, mode='L')
    m_image = Image.fromarray(m, mode='L')
    y_image = Image.fromarray(y, mode='L')
    k_image = Image.fromarray(k, mode='L')


    if w is not None:
        w = qufan(w)
        w_image = Image.fromarray(w, mode='L')
        cmyk_image = Image.merge("CMYK", (c_image, m_image, y_image, k_image, w_image))
    else:
        cmyk_image = Image.merge("CMYK", (c_image, m_image, y_image, k_image))
    progressDialog.setValue(60)  # 继续更新进度条值
    out = cmyk_image.transpose(Image.FLIP_TOP_BOTTOM)

    temp_image_path = "temp_image.tif"  # 临时保存路径
    out.save(temp_image_path, dpi=(uXResolution, uYResolution))
    progressDialog.setValue(80)  # 继续更新进度条值
    window_instance.show_image(temp_image_path)  # 显示图像而不是直接保存

    # time_end = time.time()
    progressDialog.setValue(100)  # 完成，关闭进度条对话框
    # time_sum = time_end - time_start
    # QMessageBox.information(window_instance, "gooooooood", "执行完毕，用时" + str(round(time_sum, 4)) + '秒')
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = windows()
    window.show()
    atexit.register(cleanup_temp_file)
    atexit.register(cleanup_icon_file)
    sys.exit(app.exec_())

