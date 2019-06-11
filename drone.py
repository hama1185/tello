import sys
import traceback
import tellopy
import av
import cv2.cv2 as cv2  # for avoidance of pylint error
import numpy
import time
import os

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
        #flag = False
        drone.takeoff()#離陸
        fly_begin_time = time.time()#飛び始めの時間
        #drone.clockwise(10)#10%の速度で旋回?
        count = 0#file_no
        while True:
            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                cv2.imshow('Original', image)
                cv2.imshow('Canny', cv2.Canny(image, 100, 200))
                cv2.waitKey(1)
                if frame.time_base < 1.0/60:
                    time_base = 1.0/60
                else:
                    time_base = frame.time_base
                procedure_time = time.time() - fly_begin_time#経過時間
                frame_skip = int((time.time() - start_time) / time_base)
                if procedure_time >= 30:
                    drone.land()#着陸
                count = count + 1
                file_path = os.path.join('output_pictures', 'frame_{:04d}.png'.format(count))
                cv2.imwrite(file_path, image)
            


    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        drone.quit()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()