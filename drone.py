import sys
import traceback
import tellopy
import av
import cv2.cv2 as cv2  # for avoidance of pylint error
import numpy
import time
import os
import re
#left_x は回転
#right_xは左右の平行移動
#left_y は上昇下降
#right_yは前進移動

#ドローンを停止させる
def stop(self):
    self.left_x = 0
    self.left_y = 0
    self.right_y = 0
    self.right_x = 0


def main():
    drone = tellopy.Tello()
    os.makedirs('output_pictures', exist_ok=True)#ディレクトリの作成
    try:
        drone.connect()
        drone.wait_for_connection(60.0)

        retry = 3
        container = None
        while container is None and 0 < retry:
            retry -= 1
            try:
                container = av.open(drone.get_video_stream())
            except av.AVError as ave:
                print(ave)
                print('retry...')

        # skip first 300 frames
        frame_skip = 300
        flag = False
        drone.takeoff()#離陸
        fly_begin_time = time.time()#飛び始めの時間
        drone.left_x = 0.5
        
        count = 0#file_no
        while True:
            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                cv2.imshow('Original', image)
                #cv2.imshow('Canny', cv2.Canny(image, 100, 200))
                cv2.waitKey(1)
                if frame.time_base < 1.0/60:
                    time_base = 1.0/60
                else:
                    time_base = frame.time_base
                procedure_time = time.time() - fly_begin_time#経過時間
                frame_skip = int((time.time() - start_time) / time_base)
                count = count + 1
                file_path = os.path.join('output_pictures', 'frame_{:04d}.png'.format(count))
                cv2.imwrite(file_path, image)

                if procedure_time >= 15 and flag == False:
                    stop(drone)
                    flag = True

                if procedure_time >= 30:#終了条件
                    drone.land()#着陸
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
            


    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        drone.quit()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
