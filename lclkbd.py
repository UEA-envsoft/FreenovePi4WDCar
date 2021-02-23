import evdev 
from selectors import DefaultSelector, EVENT_READ
from Motor import *
from servo import *
from Buzzer import *
from subprocess import call
import atexit
from Led import *
import time
import sys
# from selfDrive import *

class localKeyboard:
    def __init__(self):
        self.headUpDownAngle = 90
        self.headLeftRightAngle = 90
        self.PWM = Motor()
        self.servo = Servo()
        self.horn = Buzzer()
        self.speed = 1000
        # corrected servo positions
        self.headLRcorrect = -3
        self.headUDcorrect = 4
        # self.auton = selfDrive(self)
        # self.selfDriving = False
        self.reset_head()
        self.selector = DefaultSelector()
        self.mecanum = False

        self.mouse = evdev.InputDevice('/dev/input/event1')
        self.keybd = evdev.InputDevice('/dev/input/event0')
        
        atexit.register(self.keybd.ungrab)  # Don't forget to ungrab the keyboard on exit!
        atexit.register(self.mouse.ungrab)
        self.keybd.grab()  # Grab, i.e. prevent the keyboard from emitting original events.#
        self.mouse.grab()

        # This works because InputDevice has a `fileno()` method.
        self.selector.register(self.mouse, EVENT_READ)
        self.selector.register(self.keybd, EVENT_READ)

    def read_keys_loop(self):
        while True:
            self.read_keys()

    def read_keys(self):
        for key, mask in self.selector.select():
            device = key.fileobj
            for event in device.read():
                if event.type == evdev.ecodes.EV_KEY:
                    # print("key press")
                    # print(evdev.ecodes.bytype[evdev.ecodes.EV_KEY][event.code])
                    if event.value == 1 or event.value == 2: 
                        self.key_press(event, self.keybd)
                    elif event.value == 0:
                        self.drive_stop()
                elif event.type == evdev.ecodes.EV_REL:
                    if event.code == evdev.ecodes.REL_X:
                        if event.value < 0:
                            self.head_left()
                        else:
                            self.head_right()
                    if event.code == evdev.ecodes.REL_Y:
                        if event.value < 0:
                            self.head_down()
                        else:
                            self.head_up()
                else:
                    pass
                    #print(event)

    def key_press(self, ev, kbd):
            unknownKey = True
            #EVENTS THAT SHOULD ONLY BE CALLED ON PRESS AND NOT HOLD
            if ev.value == 1:
                unknownKey = False
                # SPEED SETTING
                if ev.code == evdev.ecodes.KEY_1:
                    self.speed = 900
                elif ev.code == evdev.ecodes.KEY_2:
                    self.speed = 1000
                elif ev.code == evdev.ecodes.KEY_3:
                    self.speed = 1100
                elif ev.code == evdev.ecodes.KEY_4:
                    self.speed = 1200
                elif ev.code == evdev.ecodes.KEY_5:
                    self.speed = 1300
                elif ev.code == evdev.ecodes.KEY_6:
                    self.speed = 1400
                elif ev.code == evdev.ecodes.KEY_7:
                    self.speed = 1500
                elif ev.code == evdev.ecodes.KEY_8:
                    self.speed = 1600
                elif ev.code == evdev.ecodes.KEY_9:
                    self.speed = 1800
                elif ev.code == evdev.ecodes.KEY_0:
                    self.speed = 2000
                # DRIVE FUNCTIONS
                # elif ev.code == evdev.ecodes.KEY_TAB:
                #     self.selfDriving = not self.selfDriving
                #     if self.selfDriving:
                #         print("self drive start")
                #     # call self driving from here so that key presses are still monitored
                #     # flush backed up key presses
                #     while kbd.read_one() != None:
                #         pass
                #     while self.selfDriving:
                #         self.auton.drive()
                #         time.sleep(0.5)
                #         # any interaction will stop
                #         ev = kbd.read_one()
                #         try:
                #             if ev.value == 1:
                #                 # print(evdev.ecodes.bytype[evdev.ecodes.EV_KEY][ev.code])
                #                 self.selfDriving = False
                #         except:
                #             pass
                #     self.drive_stop()
                #     print("self drive stop")
                elif ev.code == evdev.ecodes.KEY_UP:
                    self.drive_forward()
                elif ev.code == evdev.ecodes.KEY_DOWN:
                    self.drive_backward()
                elif ev.code == evdev.ecodes.KEY_LEFT:
                    self.turn_left()
                elif ev.code == evdev.ecodes.KEY_RIGHT:
                    self.turn_right()
                elif ev.code == evdev.ecodes.KEY_COMMA:
                    self.crab_left()
                elif ev.code == evdev.ecodes.KEY_DOT:
                    self.crab_right()
                elif ev.code == evdev.ecodes.KEY_SEMICOLON:
                    self.diag_right()
                elif ev.code == evdev.ecodes.KEY_K:
                    self.diag_left()
                elif ev.code == evdev.ecodes.KEY_SLASH:
                    self.diag_rev_right()
                elif ev.code == evdev.ecodes.KEY_M:
                    self.diag_rev_left()
                elif ev.code == evdev.ecodes.KEY_U:
                    self.curve_right()
                elif ev.code == evdev.ecodes.KEY_Y:
                    self.curve_left()
                elif ev.code == evdev.ecodes.KEY_J:
                    self.curve_rev_right()
                elif ev.code == evdev.ecodes.KEY_H:
                    self.curve_rev_left()
                elif ev.code == evdev.ecodes.KEY_HOME:
                    self.drive_stop()
                    self.servo.setServoPwm('0', int(self.headLeftRightAngle))
                    self.servo.setServoPwm('1', int(self.headUpDownAngle))
                    self.speed = 1000
                #PROG FUNCTIONS
                elif ev.code == evdev.ecodes.KEY_LEFTMETA:
                    self.close()
                elif ev.code == evdev.ecodes.KEY_END:
                    self.shutdown_pi()
                elif ev.code == evdev.ecodes.KEY_SYSRQ:
                    self.reboot_pi()
                else:
                    unknownKey = True
            #EVENTS CALLED ON PRESS AND ON HOLD
            #HEAD POSITION
            if ev.code == evdev.ecodes.KEY_Z:
                self.head_down()
            elif ev.code == evdev.ecodes.KEY_A:
                self.head_left()
            elif ev.code == evdev.ecodes.KEY_S:
                self.head_right()
            elif ev.code == evdev.ecodes.KEY_W:
                self.head_up()
            #HORN
            elif ev.code == evdev.ecodes.KEY_T:
                self.toot()
            elif unknownKey:
                print("UNUSED KEY CODE")
                print(evdev.ecodes.bytype[evdev.ecodes.EV_KEY][ev.code])

            # flush backed up key presses
            while kbd.read_one() is not None:
                if ev.value == 0:
                    self.drive_stop()


    def close(self):
        # kbd should be ungrabbed by atexit
        sys.exit()

    def shutdown_pi(self):
        self.toot()
        time.sleep(0.2)
        self.toot()
        call("sudo nohup shutdown -h now", shell=True)

    def reboot_pi(self):
        self.toot()
        call("sudo nohup reboot", shell=True)

    def toot(self):
        self.horn.run('1')
        time.sleep(0.2)
        self.horn.run('0')

    def drive_forward(self):
        PWM.setMotorModel(self.speed, self.speed, self.speed, self.speed)

    def turn_left(self):
        PWM.setMotorModel(-self.speed, -self.speed, self.speed, self.speed)

    def drive_backward(self):
        PWM.setMotorModel(-self.speed, -self.speed, -self.speed, -self.speed)

    def turn_right(self):
        PWM.setMotorModel(self.speed, self.speed, -self.speed, -self.speed)

    def crab_left(self):
        if self.mecanum: PWM.setMotorModel(-self.speed, self.speed, self.speed, -self.speed)

    def crab_right(self):
        if self.mecanum: PWM.setMotorModel(self.speed, -self.speed, -self.speed, self.speed)

    def curve_left(self, biasPcent=20):
        PWM.setMotorModel(int(self.speed * (100 - biasPcent) / 100), int(self.speed * (100 - biasPcent) / 100),
                          int(self.speed * (100 + biasPcent) / 100), int(self.speed * (100 + biasPcent) / 100))

    def curve_right(self, biasPcent=20):
        PWM.setMotorModel(int(self.speed * (100 + biasPcent) / 100), int(self.speed * (100 + biasPcent) / 100),
                          int(self.speed * (100 - biasPcent) / 100), int(self.speed * (100 - biasPcent) / 100))

    def curve_rev_left(self, biasPcent=20):
        PWM.setMotorModel(-int(self.speed * (100 - biasPcent) / 100), -int(self.speed * (100 - biasPcent) / 100),
                          -int(self.speed * (100 + biasPcent) / 100), -int(self.speed * (100 + biasPcent) / 100))

    def curve_rev_right(self, biasPcent=20):
        PWM.setMotorModel(-int(self.speed * (100 + biasPcent) / 100), -int(self.speed * (100 + biasPcent) / 100),
                          -int(self.speed * (100 - biasPcent) / 100), -int(self.speed * (100 - biasPcent) / 100))

    def diag_right(self):
        PWM.setMotorModel(self.speed, 0, 0, self.speed)

    def diag_left(self):
        PWM.setMotorModel(0, self.speed, self.speed, 0)

    def diag_rev_left(self):
        PWM.setMotorModel(-self.speed, 0, 0, -self.speed)

    def diag_rev_right(self):
        PWM.setMotorModel(0, -self.speed, -self.speed, 0)

    def drive_stop(self):
        PWM.setMotorModel(0, 0, 0, 0)

    def head_up(self):
        self.headUpDownAngle = self.headUpDownAngle + 1
        if self.headUpDownAngle > 180 + self.headUDcorrect:
            self.headUpDownAngle = 180 + self.headUDcorrect;
        self.servo.setServoPwm('1', self.headUpDownAngle)
        # print("Up/down " + str(self.headUpDownAngle))

    def head_down(self):
        self.headUpDownAngle = self.headUpDownAngle - 1
        if self.headUpDownAngle < 80 + self.headUDcorrect:
            self.headUpDownAngle = 80 + self.headUDcorrect
        self.servo.setServoPwm('1', self.headUpDownAngle)
        # print("Up/down " + str(self.headUpDownAngle))

    def head_left(self):
        self.headLeftRightAngle = self.headLeftRightAngle - 1
        if self.headLeftRightAngle < 10 + self.headLRcorrect:
            self.headLeftRightAngle = 10 + self.headLRcorrect
        self.servo.setServoPwm('0', self.headLeftRightAngle)
        # print("Left/Right " + str(self.headLeftRightAngle))

    def head_LRpos(self, angle):
        print("Move head to " + str(self.headLeftRightAngle))
        self.headLeftRightAngle = angle + self.headLRcorrect
        self.servo.setServoPwm('0', self.headLeftRightAngle)

    def head_right(self):
        self.headLeftRightAngle = self.headLeftRightAngle + 1
        if self.headLeftRightAngle > 170 + self.headLRcorrect:
            self.headLeftRightAngle = 170 + self.headLRcorrect
        self.servo.setServoPwm('0', self.headLeftRightAngle)
        # print("Left/Right " + str(self.headLeftRightAngle))

    def reset_head(self):
        self.headLeftRightAngle = 90 + self.headLRcorrect
        self.headUpDownAngle = 90 + self.headUDcorrect
        self.servo.setServoPwm('0', int(self.headLeftRightAngle))
        self.servo.setServoPwm('1', int(self.headUpDownAngle))

if __name__ == '__main__':
    kb = localKeyboard()
    try:
        kb.read_keys_loop()
    except KeyboardInterrupt:
        print("calling close")
        kb.close()
