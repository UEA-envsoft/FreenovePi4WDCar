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
from datetime import datetime, timedelta

class localKeyboard:
    def __init__(self):
        self.headUpDownAngle = 90
        self.headLeftRightAngle = 90
        self.PWM = Motor()
        self.servo = Servo()
        self.horn = Buzzer()
        self.speed = 1000
        # corrected servo positions
        # adjust these to suit your car
        # so head is front and centre at start
        self.headLRcorrect = -3
        self.headUDcorrect = 4
        self.reset_head()
        self.selector = DefaultSelector()
        # set true for mecanum wheels
        self.mecanum = False
        self.useLights = True
        self.led = Led()
        self.mouse = evdev.InputDevice('/dev/input/event1')
        self.keybd = evdev.InputDevice('/dev/input/event0')
        self.readingKeys = False
        self.led.colorWipe(self.led.strip, Color(0,0,0),0)
        self.brake = False
        self.reverse = False
        self.indicating = False
        self.leftTurn = False
        self.rightTurn = False
        self.moving = False
        self.indi_time = datetime.now()
        self.indi_off = True
        self.brake_time = datetime.now()
        self.brake_off = True
        atexit.register(self.keybd.ungrab)  # Don't forget to ungrab the keyboard on exit!
        atexit.register(self.mouse.ungrab)
        self.keybd.grab()  # Grab, i.e. prevent the keyboard from emitting original events.#
        self.mouse.grab()
        # This works because InputDevice has a `fileno()` method.
        self.selector.register(self.mouse, EVENT_READ)
        self.selector.register(self.keybd, EVENT_READ)

    def read_keys_loop(self):
        self.readingKeys = True
        while self.readingKeys:
            self.read_keys()
            # only manage lights after a key press so brake lights, if on,
            # will stay on until next key event
            if self.useLights: self.manage_lights()

    def manage_lights(self):
        # indicators
        if not self.indicating and not self.reverse:
            self.led.colorWipe(self.led.strip, Color(0,0,0),0)
        else:
            if self.indicating:
                if (datetime.now() - self.indi_time).microseconds > 250000:
                    self.indi_off = not self.indi_off
                    self.indi_time = datetime.now()
                if self.indi_off:
                    if self.leftTurn:
                        self.led.strip.setPixelColor(2, Color(125,85,0) )
                        self.led.strip.setPixelColor(5, Color(125,85,0) )
                    if self.rightTurn:
                        self.led.strip.setPixelColor(1, Color(125,85,0) )
                        self.led.strip.setPixelColor(6, Color(125,85,0) )
                    self.led.strip.show()
                else:
                    self.led.colorWipe(self.led.strip, Color(0,0,0),0)
            if self.reverse:
                self.led.strip.setPixelColor(1, Color(255,255,255) )
                self.led.strip.setPixelColor(2, Color(255,255,255) )
                self.led.strip.show()

        if self.brake:
            self.brake = False
            if self.brake_off:
                self.brake_off = False
                self.brake_time = datetime.now()
                self.led.strip.setPixelColor(1, Color(255,0,0) )
                self.led.strip.setPixelColor(2, Color(255,0,0) )
                self.led.strip.show()
                
        if not self.brake_off:
            #this is a minimum time on, they stay on until next key press
            if (datetime.now() - self.brake_time).microseconds > 250000:
                self.led.colorWipe(self.led.strip, Color(0,0,0),0)
                self.brake = False
                self.brake_off = True

    def read_keys(self):
        for key, mask in self.selector.select():
            device =key.fileobj
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
            if (ev.value == 1 or ev.value == 2): # 1 PRESS or 2 HOLD
                # EVENTS CALLED ON PRESS AND ON HOLD
                # HEAD POSITION
                if ev.code == evdev.ecodes.KEY_Z: self.head_down()
                elif ev.code == evdev.ecodes.KEY_A: self.head_left()
                elif ev.code == evdev.ecodes.KEY_S: self.head_right()
                elif ev.code == evdev.ecodes.KEY_W: self.head_up()
                # HORN
                elif ev.code == evdev.ecodes.KEY_T: self.toot()
                # not interested in any other held keys
                elif ev.value == 2: pass

                #EVENTS THAT SHOULD ONLY BE CALLED ON PRESS AND NOT HOLD
                # SPEED SETTING
                elif ev.code == evdev.ecodes.KEY_1: self.speed = 1000
                elif ev.code == evdev.ecodes.KEY_2: self.speed = 1200
                elif ev.code == evdev.ecodes.KEY_3: self.speed = 1400
                elif ev.code == evdev.ecodes.KEY_4: self.speed = 1700
                elif ev.code == evdev.ecodes.KEY_5: self.speed = 2000
                elif ev.code == evdev.ecodes.KEY_6: self.speed = 2400
                elif ev.code == evdev.ecodes.KEY_7: self.speed = 2800
                elif ev.code == evdev.ecodes.KEY_8: self.speed = 3200
                elif ev.code == evdev.ecodes.KEY_9: self.speed = 3600
                elif ev.code == evdev.ecodes.KEY_0: self.speed = 4000

                # DRIVE FUNCTIONS
                elif ev.code == evdev.ecodes.KEY_UP: self.drive_forward()
                elif ev.code == evdev.ecodes.KEY_DOWN: self.drive_backward()
                elif ev.code == evdev.ecodes.KEY_LEFT: self.turn_left()
                elif ev.code == evdev.ecodes.KEY_RIGHT: self.turn_right()
                elif ev.code == evdev.ecodes.KEY_COMMA: self.crab_left()
                elif ev.code == evdev.ecodes.KEY_DOT: self.crab_right()
                elif ev.code == evdev.ecodes.KEY_SEMICOLON: self.diag_right()
                elif ev.code == evdev.ecodes.KEY_K: self.diag_left()
                elif ev.code == evdev.ecodes.KEY_SLASH: self.diag_rev_right()
                elif ev.code == evdev.ecodes.KEY_M: self.diag_rev_left()
                elif ev.code == evdev.ecodes.KEY_U: self.curve_right()
                elif ev.code == evdev.ecodes.KEY_Y: self.curve_left()
                elif ev.code == evdev.ecodes.KEY_J: self.curve_rev_right()
                elif ev.code == evdev.ecodes.KEY_H: self.curve_rev_left()

                # USE OR DONT USE LIGHTS
                elif ev.code == evdev.ecodes.KEY_L:
                    self.useLights = not self.useLights
                    if not self.useLights: self.led.colorWipe(self.led.strip, Color(0,0,0),0)

                # RESET TO START STATE
                elif ev.code == evdev.ecodes.KEY_HOME: #RESET TO START STATE
                    self.drive_stop()
                    self.servo.setServoPwm('0', int(self.headLeftRightAngle))
                    self.servo.setServoPwm('1', int(self.headUpDownAngle))
                    self.speed = 1000
                    self.led.colorWipe(self.led.strip, Color(0,0,0),0)

                # PROG FUNCTIONS
                elif ev.code == evdev.ecodes.KEY_LEFTMETA: self.close()
                elif ev.code == evdev.ecodes.KEY_END: self.shutdown_pi()
                elif ev.code == evdev.ecodes.KEY_SYSRQ: self.reboot_pi()

                else:
                    print("UNUSED KEY CODE")
                    print(evdev.ecodes.bytype[evdev.ecodes.EV_KEY][ev.code])        
            if ev.value == 0:
                self.drive_stop()
            # flush backed up key presses
            while kbd.read_one() is not None:
                if ev.value == 0 :
                    self.drive_stop()


    def close(self):
        self.readingKeys = False
        self.selector.unregister(self.mouse)
        self.selector.unregister(self.keybd)
        self.led.colorWipe(self.led.strip, Color(0,0,0),0)
        # kbd should be ungrabbed by atexit
        # but belt and braces
        try:
            self.keybd.ungrab
            self.mouse.ungrab
        except:
            pass
        sys.exit()

    def shutdown_pi(self):
        self.readingKeys = False
        self.toot()
        time.sleep(0.2)
        self.toot()
        call("sudo nohup shutdown -h now", shell=True)

    def reboot_pi(self):
        self.readingKeys = False
        self.toot()
        call("sudo nohup reboot", shell=True)

    def toot(self):
        self.horn.run('1')
        time.sleep(0.2)
        self.horn.run('0')

    def drive_forward(self):
        self.moving = True
        PWM.setMotorModel(self.speed, self.speed, self.speed, self.speed)

    def turn_left(self):
        self.moving = True
        self.indicating = True
        self.leftTurn = True
        self.rightTurn = False
        PWM.setMotorModel(-self.speed, -self.speed, self.speed, self.speed)

    def drive_backward(self):
        self.moving = True
        self.reverse = True
        PWM.setMotorModel(-self.speed, -self.speed, -self.speed, -self.speed)

    def turn_right(self):
        self.moving = True
        self.indicating = True
        self.leftTurn = False
        self.rightTurn = True
        PWM.setMotorModel(self.speed, self.speed, -self.speed, -self.speed)

    def curve_left(self, biasPcent=20):
        self.moving = True
        PWM.setMotorModel(int(self.speed * (100 - biasPcent) / 100), int(self.speed * (100 - biasPcent) / 100),
                          int(self.speed * (100 + biasPcent) / 100), int(self.speed * (100 + biasPcent) / 100))

    def curve_right(self, biasPcent=20):
        self.moving = True
        PWM.setMotorModel(int(self.speed * (100 + biasPcent) / 100), int(self.speed * (100 + biasPcent) / 100),
                          int(self.speed * (100 - biasPcent) / 100), int(self.speed * (100 - biasPcent) / 100))

    def curve_rev_left(self, biasPcent=20):
        self.moving = True
        self.reverse = True
        PWM.setMotorModel(-int(self.speed * (100 - biasPcent) / 100), -int(self.speed * (100 - biasPcent) / 100),
                          -int(self.speed * (100 + biasPcent) / 100), -int(self.speed * (100 + biasPcent) / 100))

    def curve_rev_right(self, biasPcent=20):
        self.moving = True
        self.reverse = True
        PWM.setMotorModel(-int(self.speed * (100 + biasPcent) / 100), -int(self.speed * (100 + biasPcent) / 100),
                          -int(self.speed * (100 - biasPcent) / 100), -int(self.speed * (100 - biasPcent) / 100))

    def crab_left(self): #REQUIRES MECANUM WHEELS
        if self.mecanum:
            self.moving = True
            self.indicating = True
            self.leftTurn = True
            self.rightTurn = False
            PWM.setMotorModel(-self.speed, self.speed, self.speed, -self.speed)

    def crab_right(self): #REQUIRES MECANUM WHEELS
        if self.mecanum:
            self.moving = True
            self.indicating = True
            self.leftTurn = False
            self.rightTurn = True
            PWM.setMotorModel(self.speed, -self.speed, -self.speed, self.speed)

    def diag_right(self): #REQUIRES MECANUM WHEELS
        if self.mecanum: 
            self.moving = True
            PWM.setMotorModel(self.speed, 0, 0, self.speed)

    def diag_left(self): #REQUIRES MECANUM WHEELS
        if self.mecanum: 
            self.moving = True
            PWM.setMotorModel(0, self.speed, self.speed, 0)

    def diag_rev_left(self): #REQUIRES MECANUM WHEELS
        if self.mecanum: 
            self.moving = True
            self.reverse = True
            PWM.setMotorModel(-self.speed, 0, 0, -self.speed)

    def diag_rev_right(self): #REQUIRES MECANUM WHEELS
        if self.mecanum: 
            self.moving = True
            self.reverse = True
            PWM.setMotorModel(0, -self.speed, -self.speed, 0)

    def drive_stop(self):
        if self.moving:
            self.brake = True
            self.moving = False
            PWM.setMotorModel(0, 0, 0, 0)
            self.reverse = False
            self.indicating = False
            self.leftTurn = False
            self.rightTurn = False

    def head_up(self):
        self.headUpDownAngle += 1
        if self.headUpDownAngle > 180 + self.headUDcorrect:
            self.headUpDownAngle = 180 + self.headUDcorrect
        self.servo.setServoPwm('1', self.headUpDownAngle)
        # print("Up/down " + str(self.headUpDownAngle))

    def head_down(self):
        self.headUpDownAngle -= 1
        if self.headUpDownAngle < 80 + self.headUDcorrect:
            self.headUpDownAngle = 80 + self.headUDcorrect
        self.servo.setServoPwm('1', self.headUpDownAngle)
        # print("Up/down " + str(self.headUpDownAngle))

    def head_left(self):
        self.headLeftRightAngle -= 1
        if self.headLeftRightAngle < 10 + self.headLRcorrect:
            self.headLeftRightAngle = 10 + self.headLRcorrect
        self.servo.setServoPwm('0', self.headLeftRightAngle)
        # print("Left/Right " + str(self.headLeftRightAngle))

    def head_LRpos(self, angle):
        # print("Move head to " + str(self.headLeftRightAngle))
        self.headLeftRightAngle = angle + self.headLRcorrect
        self.servo.setServoPwm('0', self.headLeftRightAngle)

    def head_right(self):
        self.headLeftRightAngle += 1
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
