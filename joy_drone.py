import pygame
from pygame.locals import *
import tellopy
import time

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

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

pygame.joystick.init()
try:
    joy = pygame.joystick.Joystick(0) # create a joystick instance
    joy.init() # init instance
    print('Joystickの名称: ' + joy.get_name()) 
    print('ボタン数 : ' + str(joy.get_numbuttons()))
except pygame.error:
    print('Joystickが見つかりませんでした。')

drone = tellopy.Tello()
try:
    drone.connect()
    drone.wait_for_connection(20.0)#初期値は60
except Exception as ex:
    print(ex)

def main():
    pygame.init()
    screen = pygame.display.set_mode( (SCREEN_WIDTH, SCREEN_HEIGHT) ) # 画面を作る
    pygame.display.set_caption('Joystick') # タイトル
    pygame.display.flip() # 画面を反映
    fly_sw = False#takeoffとlandの切り替え
    move_sw = False#left_xとright_xとの切り替え
    scale = 6#適時変更
    while 1:
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
                    drone.left_x = x
                    drone.left_y = y
                if move_sw == True:
                    drone.right_x = x
                    drone.right_y = y
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
                    fly_sw = False

                if int(e.button) == 4:
                    move_sw = False
                if int(e.button) == 5:
                    move_sw = True
            elif e.type == pygame.locals.JOYBUTTONUP: 
                print(str(e.button)+'番目のボタンが離された')

if __name__ == '__main__': main()
#end of file