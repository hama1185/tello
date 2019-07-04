import sys
import traceback
import tellopy
import av
import cv2.cv2 as cv2  # for avoidance of pylint error
import numpy
import time
import os
import re
import pygame
from pygame.locals import *

#left_x は回転
#right_xは左右の平行移動
#left_y は上昇下降
#right_yは前進移動

#button number
#0...A
#1...B
#2...X
#3...Y
#4...L
#5...R
#6...back
#7...start
#8...L3
#9...R3

def pixel_art(img, s, c):
    h, w, ch = img.shape
    img = cv2.resize(img, (int(w / s), int(h / s)))
    img = cv2.resize(img, (w, h), interpolation = cv2.INTER_NEAREST)

    return sub_color(img, c)

def sub_color(img, c):
    z = img.reshape((-1, 3))
    z = numpy.float32(z)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(z, c, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = numpy.uint8(center)
    res = center[label.flatten()]

    return res.reshape((img.shape))

def dir_write(dir_name, file_name, img):
    file_path = os.path.join(dir_name, file_name)
    cv2.imwrite(file_path, img)


def main():
    drone = tellopy.Tello()
    os.makedirs('raw_data', exist_ok=True)#生データの保存するディレクトリの作成
    os.makedirs('take_picture', exist_ok=True)#撮影時のディレクトリ
    os.makedirs('process_picture', exist_ok=True)#撮影時の加工画像を入れるディレクトリ
    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 480

    pygame.joystick.init()
    try:
        joy = pygame.joystick.Joystick(0) # create a joystick instance
        joy.init() # init instance
        print('Joystickの名称: ' + joy.get_name())
        print('ボタン数 : ' + str(joy.get_numbuttons()))
        pygame.init()
        screen = pygame.display.set_mode( (SCREEN_WIDTH, SCREEN_HEIGHT) ) # 画面を作る
        pygame.display.set_caption('Joystick') # タイトル
        pygame.display.flip() # 画面を反映
    except pygame.error:
        print('Joystickが見つかりませんでした。')

    try:
        drone.connect()
        drone.wait_for_connection(20.0)

        retry = 3
        container = None
        while container is None and 0 < retry:
            retry -= 1
            try:
                container = av.open(drone.get_video_stream())
            except av.AVError as ave:
                print(ave)
                print('retry...')

        fly_sw = False#takeoffとlandの切り替え
        scale = 4#適時変更
        # skip first 300 frames
        frame_skip = 300

        raw_count = 0#rawfile_no
        picture_count = 0#picturefile_no

        while True:

            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                cv2.imshow('Original', image)
                cv2.waitKey(1)
                if frame.time_base < 1.0 / 60:
                    time_base = 1.0 / 60
                else:
                    time_base = frame.time_base
                frame_skip = int((time.time() - start_time) / time_base)
                dir_write('raw_data', 'frame_{:04d}.png'.format(raw_count), image)
                raw_count += 1

                for e in pygame.event.get(): # イベントチェック
                    if e.type == QUIT: # 終了が押された？
                        drone.quit()
                        return
                    if e.type == KEYDOWN and e.key  == K_ESCAPE: # ESCが押された？
                        drone.quit()
                        return

                    # Joystick関連のイベントチェック
                    if e.type == pygame.locals.JOYAXISMOTION:
                        x1 , y1 = joy.get_axis(0), joy.get_axis(1)#左スティックのx,yに値の格納
                        x2 , y2 = joy.get_axis(4), joy.get_axis(3)#右スティックのx,yに値の格納
                        #print('x and y : ' + str(x) +' , '+ str(y))

                        drone.left_x = -x1
                        drone.left_y = -y1

                        drone.right_x = x2 / scale
                        drone.right_y = -y2 / scale
                    elif e.type == pygame.locals.JOYBALLMOTION:
                        print('ball motion')
                    elif e.type == pygame.locals.JOYHATMOTION:
                        print('hat motion')
                    elif e.type == pygame.locals.JOYBUTTONDOWN:
                        print(str(e.button)+'番目のボタンが押された')
                        if int(e.button) == 7 and fly_sw == False:#start
                            drone.takeoff()
                            fly_sw = True

                        elif int(e.button) == 7 and fly_sw == True:#start
                            drone.land()
                            drone.quit()
                            cv2.destroyAllWindows()
                            filepath = os.path.join('raw_data')

                            files = os.listdir(filepath)
                            raw_count = 0

                            for file in files:
                                index = re.search('.png', file)
                                if index:
                                    raw_count += 1

                            print(raw_count)
                            #ビデオとして結合
                            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                            video = cv2.VideoWriter('replay.mp4', fourcc, 20.0, (640, 480))

                            for i in range(0, raw_count):
                                filepath = os.path.join('raw_data', 'frame_{:04d}.png'.format(i))
                                img = cv2.imread(filepath)
                                img = cv2.resize(img, (640, 480))
                                video.write(img)

                            video.release()

                            for i in range(0, picture_count):
                                filepath = os.path.join('take_picture', 'picture_{:04d}.png'.format(i))
                                img = cv2.imread(filepath)
                                print(cv2.Laplacian(img, cv2.CV_64F).var())#ラプラシアン微分
                                img = pixel_art(img, 4, 32)
                                dir_write('process_picture', 'dot_{:04d}.png'.format(i), img)

                            fly_sw = False

                        if int(e.button) == 3:#Y
                            dir_write('take_picture', 'picture_{:04d}.png'.format(picture_count), image)
                            picture_count += 1


                    elif e.type == pygame.locals.JOYBUTTONUP:
                        print(str(e.button)+'番目のボタンが離された')

    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        drone.quit()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
