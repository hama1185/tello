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




def main():
    drone = tellopy.Tello()
    os.makedirs('output_pictures', exist_ok=True)#ディレクトリの作成
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
        move_sw = False#left_xとright_xとの切り替え
        scale = 4#適時変更
        # skip first 300 frames
        frame_skip = 300
        
        count = 0#file_no
        while True:
            
            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                cv2.imshow('Original', image)
                cv2.waitKey(1)
                if frame.time_base < 1.0/60:
                    time_base = 1.0/60
                else:
                    time_base = frame.time_base
                frame_skip = int((time.time() - start_time) / time_base)
                count = count + 1
                file_path = os.path.join('output_pictures', 'frame_{:04d}.png'.format(count))
                cv2.imwrite(file_path, image)

                for e in pygame.event.get(): # イベントチェック
                    if e.type == QUIT: # 終了が押された？
                        drone.quit()
                        return
                    if e.type == KEYDOWN and e.key  == K_ESCAPE: # ESCが押された？
                        drone.quit()
                        return
                    
                    # Joystick関連のイベントチェック
                    if e.type == pygame.locals.JOYAXISMOTION:
                        x , y = joy.get_axis(0), joy.get_axis(1)#x,yに値の格納
                        #print('x and y : ' + str(x) +' , '+ str(y))
                        if move_sw == False:
                            drone.left_x = -x
                            drone.left_y = -y
                        if move_sw == True:
                            drone.right_x = -x / scale
                            drone.right_y = -y / scale
                    elif e.type == pygame.locals.JOYBALLMOTION:
                        print('ball motion')
                    elif e.type == pygame.locals.JOYHATMOTION:
                        print('hat motion')
                    elif e.type == pygame.locals.JOYBUTTONDOWN:
                        print(str(e.button)+'番目のボタンが押された')
                        if int(e.button) == 1 and fly_sw == False:#B
                            drone.takeoff()
                            fly_sw = True
                        
                        elif int(e.button) == 1 and fly_sw == True:#B
                            drone.land()
                            drone.quit()
                            cv2.destroyAllWindows()
                            filepath = os.path.join('output_pictures')

                            files = os.listdir(filepath)
                            count = 0

                            for file in files:
                                index = re.search('.png', file)
                                if index:
                                    count = count + 1

                            print(count)

                            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                            video = cv2.VideoWriter('replay.mp4', fourcc, 20.0, (640, 480))

                            for i in range(1, count):
                                filepath = os.path.join('output_pictures', 'frame_{:04d}.png'.format(i))
                                img = cv2.imread(filepath)
                                img = cv2.resize(img, (640, 480))
                                video.write(img)

                            video.release()
                
                            fly_sw = False

                        if int(e.button) == 4:#L
                            move_sw = False

                        if int(e.button) == 5:#R
                            move_sw = True

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