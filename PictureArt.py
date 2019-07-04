# coding : utf-8

import cv2.cv2 as cv2
import numpy as np
import os
from PIL import Image

def main() :
    filename = 'girl.png'
    image = cv2.imread(filename)
    file, ext = os.path.splitext(filename)

    pixelArtImage = pixelArt(image)
    digitalArtImage = digitalArt(image)
    waterColorImage = waterColor(image, file, ext)
    oilPaintImage = oilPaint(image)

    cv2.imwrite(file + "_PixelArt" + ext, pixelArtImage)
    cv2.imwrite(file + "_DigitalArt" + ext, digitalArtImage)
    cv2.imwrite(file + "_WaterColor" + ext, waterColorImage)
    cv2.imwrite(file + "_OilPaint" + ext, oilPaintImage)



# ドット絵
def pixelArt(image, scale = 4.0, tone = 32, saturation = 1.2, brightness = 1.1) :
    image = mosaic(image, scale)
    image = subtractiveColor(image, tone)

    image = modulateSV(image, saturation, brightness)

    return image

# デジタル絵
def digitalArt(image, scale = 2.0, tone = 64, saturation = 1.1, brightness = 0.95) :
    image = mosaic(image, scale)
    image = subtractiveColor(image, tone)

    image = modulateSV(image, saturation, brightness)

    return image

# 水彩画
def waterColor(image, file, ext, saturation = 1.15, brightness = 0.9) :
    image_paint = paint(image)
    cv2.imwrite(file + "_paint" + ext, image_paint)
    image_line = line(image)
    cv2.imwrite(file + "_line" + ext, image_line)

    image1 = Image.open(file + "_paint" + ext).convert("RGB")
    image2 = Image.open(file + "_line" + ext).convert("RGB")

    multi = multiple(image1, image2)
    multi.save(file+"_multi"+ext)

    image_multi = cv2.imread(file+"_multi"+ext)
    image_water = dodge(image_multi, image_paint)
    
    os.remove(file + "_paint" + ext)
    os.remove(file + "_line" + ext)
    os.remove(file + "_multi" + ext)

    image_water = modulateSV(image_water, saturation, brightness)

    return image_water

# 油絵
def oilPaint(image, saturation = 1.1, brightness = 1.05) :
    laplacianFilter = np.array([[-1,-1,-1,-1,-1,-1,-1],
                                [-1, 0, 0, 0, 0, 0,-1],
                                [-1, 0, 0, 0, 0, 0,-1],
                                [-1, 0, 0,26, 0, 0,-1],
                                [-1, 0, 0, 0, 0, 0,-1],
                                [-1, 0, 0, 0, 0, 0,-1],
                                [-1,-1,-1,-1,-1,-1,-1]], np.float32) / 2.0
    image_median = cv2.medianBlur(image, 7)
    image_oil = cv2.filter2D(image_median, -1, laplacianFilter)
    for i in range(2) :
        image_oil = cv2.medianBlur(image_oil, 3)
    image_oil = modulateSV(image_oil, saturation, brightness)

    return image_oil
    



# 彩度・輝度調節
# 4 referenced in
#   pixelArt
#   digitalArt
#   waterColor
#   oilPaint
def modulateSV (image, saturation, brightness) :
    image_HSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    for j in range(len(image_HSV)) :
        for i in range(len(image_HSV[j])) :
            if image_HSV[j][i][1] * saturation <= 255 :
                image_HSV[j][i][1] *= saturation
            if image_HSV[j][i][2] * brightness <= 255 :
                image_HSV[j][i][2] *= brightness
    image = cv2.cvtColor(image_HSV, cv2.COLOR_HSV2BGR)

    return image

# 2 referenced in
#   pixelArt
#   digitalArt
def mosaic(image, scale) :
    h, w, ch = image.shape

    image = cv2.resize(image, (int(w / scale), int(h / scale)))
    image = cv2.resize(image, (w, h), interpolation = cv2.INTER_NEAREST)

    return image

# 2 referenced in
#   pixelArt
#   digitalArt
def subtractiveColor(image, tone):
    z = image.reshape((-1, 3))
    z = np.float32(z)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(z, tone, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    res = center[label.flatten()]

    return res.reshape((image.shape))

# 1 referenced in
#   waterColor
def paint(image, average_square = (5, 5), sigma_x = 0, reshape_size = (-1, 3), criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0), k = 128) :
    image_blurring = cv2.GaussianBlur(image, average_square, sigma_x)
    z = image_blurring.reshape(reshape_size)
    z= np.float32(z)
    ret,label,center=cv2.kmeans(z, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    res = center[label.flatten()]
    image_reshape = res.reshape((image_blurring.shape))

    return cv2.GaussianBlur(image_reshape, average_square, sigma_x)

# 1 referenced in
#   waterColor
def line(image, line_average = (9, 9), line_sigma_x = 0, threshold1 = 50, threshold2 = 55, edges_average = (1, 1), edges_sigma_x = 0, thresh = 90, max_pixel = 255) :
    image_preprocessed  = cv2.cvtColor(cv2.GaussianBlur(image, line_average, line_sigma_x), cv2.COLOR_BGR2GRAY)
    image_edges = cv2.Canny(image_preprocessed, threshold1 = threshold1, threshold2 = threshold2)    
    image_h = cv2.GaussianBlur(image_edges, edges_average, edges_sigma_x)
    _, image_binary = cv2.threshold(image_h, thresh, max_pixel, cv2.THRESH_BINARY)
    image_binary = cv2.bitwise_not(image_binary)
    return image_binary

# 1 referenced in
#   waterColor
def multiple(image1, image2) :
    pixelSizeTuple = image1.size
    image3 = Image.new('RGB', image1.size)
    for i in range(pixelSizeTuple[0]):
        for j in range(pixelSizeTuple[1]):
            r,g,b = image1.getpixel((i,j))
            r2,g2,b2 = image2.getpixel((i,j))
            img_r = mul(r,r2)
            img_g = mul(g,g2)
            img_b = mul(b,b2)
            image3.putpixel((i,j),(img_r,img_g,img_b))  
    return image3

# 1 referenced in
#   multiple
def mul(input_color,mul_color) :
    return int(round(((input_color*mul_color)/255),0))
# 1 referenced in
#   waterColor
def dodge(multi, image_paint, gamma = 1.5, multi_w = 0.5, paint_w = 0.9) :
    d = cv2.addWeighted(multi, multi_w, image_paint, paint_w, gamma)
    return d

if __name__ == '__main__' :
    main()