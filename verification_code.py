# -*- coding = utf-8 -*-
# @Time : 2020/8/30 14:22
# @Author : luohx
# @File : verification_code.py
# @Software: PyCharm


import time
import re
import pytesseract
from PIL import Image  # 用于打开图片和对图片处理


def str_split(image):
    inletter = False  # 找出每个字母开始位置
    foundletter = False  # 找出每个字母结束位置
    start = 0
    letters = []  # 存储坐标
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            pix = image.getpixel((x, y))
            if pix != 255:
                inletter = True
        if foundletter == False and inletter == True:
            foundletter = True
            start = x
        if foundletter == True and inletter == False:
            foundletter = False
            end = x
            letters.append((start, end))
        inletter = False

    # 因为切割出来的图像有可能是噪声点
    # 筛选可能切割出来的噪声点,只保留开始结束位置差值最大的位置信息
    subtract_array = []  # 存储 结束-开始 值
    for each in letters:
        subtract_array.append(each[1] - each[0])
    reSet = sorted(subtract_array, key=lambda x: x, reverse=True)[0:4]
    letter_choice = []  # 存储 最终选择的点坐标
    for each in letters:
        if int(each[1] - each[0]) in reSet:
            letter_choice.append(each)

    image_split_array = []  # 存储切割后的图像
    for letter in letter_choice:
        im_split = image.crop((letter[0], 0, letter[1], image.size[1]))  # (切割的起始横坐标，起始纵坐标，切割的宽度，切割的高度)
        im_split = im_split.resize((13, 42))  # 转换格式
        image_split_array.append(im_split)

    return image_split_array[0:4]


class VerificationCode:
    def __init__(self, picture_name, ver_code_pos=None):
        if ver_code_pos is None:
            ver_code_pos = (0, 0, 0, 0)
        self.picture_name = picture_name
        self.ver_code_pos = ver_code_pos

    def get_pictures(self):
        page_snap_obj = Image.open(self.picture_name)
        time.sleep(1)

        image_obj = page_snap_obj.crop(self.ver_code_pos)
        return image_obj

    def process_pictures(self):
        image_obj = self.get_pictures()
        img = image_obj.convert("L")  # 转灰度

        pixdata = img.load()
        w, h = img.size
        threshold = 60
        # 遍历所有像素，大于阈值的为黑色
        for y in range(h):
            for x in range(w):
                if pixdata[x, y] < threshold:
                    pixdata[x, y] = 255  # 黑
                else:
                    pixdata[x, y] = 0
        return img  # 返回一个二值灰度图像

    def delete_spot(self):
        images = self.process_pictures()
        data = images.getdata()
        w, h = images.size
        black_point = 0
        for x in range(1, w - 1):
            for y in range(1, h - 1):
                mid_pixel = data[w * y + x]  # 中央像素点像素值
                if mid_pixel < 50:  # 找出上下左右四个方向像素点像素值
                    top_pixel = data[w * (y - 1) + x]
                    left_pixel = data[w * y + (x - 1)]
                    down_pixel = data[w * (y + 1) + x]
                    right_pixel = data[w * y + (x + 1)]
                    # 判断上下左右的黑色像素点总个数
                    if top_pixel < 10:
                        black_point += 1
                    if left_pixel < 10:
                        black_point += 1
                    if down_pixel < 10:
                        black_point += 1
                    if right_pixel < 10:
                        black_point += 1
                    if black_point < 1:
                        images.putpixel((x, y), 255)
                    black_point = 0
        return images

    def image_str(self):
        image = self.delete_spot()
        result_array = []
        image_split_array = str_split(image)
        pytesseract.pytesseract.tesseract_cmd = r"E:\tesseract\Tesseract-OCR\tesseract.exe"  # 更换成自己的tesseract安装位置
        for each in image_split_array:
            result = pytesseract.image_to_string(each, config="-psm 10")  # 图片转文字
            result = re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", result)  # 去除识别出来的特殊字符
            result_array.append(result)
        for each in result_array:
            if each == "":
                return None
        return ''.join(result_array)
