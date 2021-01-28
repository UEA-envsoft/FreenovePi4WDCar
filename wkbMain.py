import io
import os
import socket
import struct
import time
import picamera
import sys, getopt
from Thread import *
from threading import Thread
from server import Server
from server_ui import Ui_server_ui
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from Motor import *
from servo import *
from pynput import mouse, keyboard
from Buzzer import *

class mywindow(QMainWindow, Ui_server_ui):

    def __init__(self):
        self.user_ui = True
        self.start_tcp = False
        self.TCP_Server = Server()

        self.PWM = Motor()
        self.servo = Servo()
        self.horn = Buzzer()
        self.headLeftRightAngle = 90
        self.headUpDownAngle = 90
        self.mouseX = -1000
        self.mouseY = -1000
        self.servo.setServoPwm('0', int(self.headLeftRightAngle))
        self.servo.setServoPwm('1', int(self.headUpDownAngle))
        self.parseOpt()

        if self.user_ui:
            self.app = QApplication(sys.argv)
            super(mywindow, self).__init__()
            self.setupUi(self)
            self.m_DragPosition = self.pos()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setMouseTracking(True)
            self.Button_Server.setText("On")
            self.on_pushButton()
            self.Button_Server.clicked.connect(self.on_pushButton)
            self.pushButton_Close.clicked.connect(self.close)
            self.pushButton_Min.clicked.connect(self.windowMinimumed)
            self.setFocusPolicy(Qt.StrongFocus)

        if self.start_tcp:
            self.TCP_Server.StartTcpServer()
            self.ReadData = Thread(target=self.TCP_Server.readdata)
            self.SendVideo = Thread(target=self.TCP_Server.sendvideo)
            self.power = Thread(target=self.TCP_Server.Power)
            self.SendVideo.start()
            self.ReadData.start()
            self.power.start()
            if self.user_ui:
                self.label.setText("Server On")
                self.Button_Server.setText("Off")

        # keep an eye on the mouse in a non-blocking fashion:
        mlistener = mouse.Listener(
            on_move=self.on_move)
        kblistener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        mlistener.start()
        kblistener.start()
        self.toot()
        # mlistener.join()
        # kblistener.join()

    def on_press(self, key):
        try:
            if key.char == 'w':
                self.head_up()
            elif key.char == 'z':
                self.head_down()
            elif key.char  == 'a':
                self.head_left()
            elif key.char == 's':
                self.head_right()
            elif key.char == 't':
                self.toot()
            else:
                print('alphanumeric key {0} pressed'.format(key.char))
        except AttributeError:
            if key == keyboard.Key.up:
                self.drive_forward()
            elif key == keyboard.Key.down:
                self.drive_backward()
            elif key == keyboard.Key.left:
                self.turn_left()
            elif key == keyboard.Key.right:
                self.turn_right()
            elif key == keyboard.Key.cmd:
                self.close()
            elif key == keyboard.Key.home:
                self.drive_stop()
                self.headLeftRightAngle = 90
                self.headUpDownAngle = 90
                self.servo.setServoPwm('0', int(self.headLeftRightAngle))
                self.servo.setServoPwm('1', int(self.headUpDownAngle))
            elif key == keyboard.Key.end:
                self.shutdown_pi()
            elif key == keyboard.Key.print_screen:
                self.reboot_pi()
            else:
                pass
                # print('special key {0} pressed'.format(key))

    def on_release(self, key):
        if (key == keyboard.Key.up or
                key == keyboard.Key.left or
                key == keyboard.Key.down or
                key == keyboard.Key.right):
            self.drive_stop()
        elif key == keyboard.Key.esc:
            # Stop listener
            return False
        else:
            pass
            # print('{0} released'.format(key))

    def on_move(self, x, y):
        # print('Pointer moved to {0}'.format((x, y)))
        if self.mouseX == -1000:
            self.mouseX = x
        if self.mouseY == -1000:
            self.mouseY = y
        if x > self.mouseX:
            self.head_right()
        if x < self.mouseX:
            self.head_left()
        self.mouseX = x
        if y > self.mouseY:
            self.head_down()
        if y < self.mouseY:
            self.head_up()
        self.mouseY = y

    def shutdown_pi(self):
        self.toot()
        self.toot()
        from subprocess import call
        call("sudo nohup shutdown -h now", shell=True)

    def reboot_pi(self):
        self.toot()
        from subprocess import call
        call("sudo nohup reboot", shell=True)

    def toot(self):
        self.horn.run('1')
        time.sleep(0.2)
        self.horn.run('0')

    def drive_forward(self):
        PWM.setMotorModel(1500, 1500, 1500, 1500)

    def turn_left(self):
        PWM.setMotorModel(-1500, -1500, 1500, 1500)

    def drive_backward(self):
        PWM.setMotorModel(-1500, -1500, -1500, -1500)

    def turn_right(self):
        PWM.setMotorModel(1500, 1500, -1500, -1500)

    def drive_stop(self):
        PWM.setMotorModel(0, 0, 0, 0)

    def head_up(self):
        self.headUpDownAngle = self.headUpDownAngle + 1
        if self.headUpDownAngle > 180:
            self.headUpDownAngle = 180;
        self.servo.setServoPwm('1', self.headUpDownAngle)

    def head_down(self):
        self.headUpDownAngle = self.headUpDownAngle - 1
        if self.headUpDownAngle < 80:
            self.headUpDownAngle = 80
        self.servo.setServoPwm('1', self.headUpDownAngle)

    def head_left(self):
        self.headLeftRightAngle = self.headLeftRightAngle - 1
        if self.headLeftRightAngle < 10:
            self.headLeftRightAngle = 10
        self.servo.setServoPwm('0', self.headLeftRightAngle)

    def head_right(self):
        self.headLeftRightAngle = self.headLeftRightAngle + 1
        if self.headLeftRightAngle > 170:
            self.headLeftRightAngle = 170
        self.servo.setServoPwm('0', self.headLeftRightAngle)

    def windowMinimumed(self):
        self.showMinimized()

    def parseOpt(self):
        self.opts, self.args = getopt.getopt(sys.argv[1:], "tn")
        for o, a in self.opts:
            if o in ('-t'):
                print("Open TCP")
                self.start_tcp = True
            elif o in ('-n'):
                self.user_ui = False

    def close(self):
        try:
            stop_thread(self.SendVideo)
            stop_thread(self.ReadData)
            stop_thread(self.power)
        except:
            pass
        try:
            self.TCP_Server.server_socket.shutdown(2)
            self.TCP_Server.server_socket1.shutdown(2)
            self.TCP_Server.StopTcpServer()
        except:
            pass
        print("Close TCP")
        if self.user_ui:
            QCoreApplication.instance().quit()
        os._exit(0)

    def on_pushButton(self):
        if self.label.text() == "Server Off":
            self.label.setText("Server On")
            self.Button_Server.setText("Off")
            self.TCP_Server.tcp_Flag = True
            print("Open TCP")
            self.TCP_Server.StartTcpServer()
            self.SendVideo = Thread(target=self.TCP_Server.sendvideo)
            self.ReadData = Thread(target=self.TCP_Server.readdata)
            self.power = Thread(target=self.TCP_Server.Power)
            self.SendVideo.start()
            self.ReadData.start()
            self.power.start()

        elif self.label.text() == 'Server On':
            self.label.setText("Server Off")
            self.Button_Server.setText("On")
            self.TCP_Server.tcp_Flag = False
            try:
                stop_thread(self.ReadData)
                stop_thread(self.power)
                stop_thread(self.SendVideo)
            except:
                pass
            self.TCP_Server.StopTcpServer()
            print("Close TCP")


if __name__ == '__main__':
    myshow = mywindow()
    if myshow.user_ui == True:
        myshow.show();
        sys.exit(myshow.app.exec_())
    else:
        try:
            pass
        except KeyboardInterrupt:
            myshow.close()
