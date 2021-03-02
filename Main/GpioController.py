# -*- coding: utf-8 -*-
#Deque system for fast-serialized GPIO PWM control

from collections import deque
import threading
import pigpio

gpioDeque = deque(maxlen=2048) #[pinnumber, pwm] double info, 1024byte

class GpioController():
    pi = pigpio.pi()
    
    # gpioDeque

    def getMainGpioDeque(self):
        return gpioDeque

    def gpio_PIN_PWM(self, pin,pwm):
        gpioDeque.append(pin)
        gpioDeque.append(pwm)
        #print("pin:"+str(pin)+"  pwm:"+str(pwm))

    def dequedQuantity(self):
        return len(gpioDeque)/2 #our deque is doubled.

    def popDequePeriodically(self):
        if(len(gpioDeque)>0):
            pin = gpioDeque.popleft()
            pwm = gpioDeque.popleft()
            print("deque gpio command!"+" pin:"+str(pin)+"  pwm: "+str(pwm))
            self.pi.set_servo_pulsewidth(pin,pwm)
        threading.Timer(0.02, self.popDequePeriodically).start() #10ms per command. 100command / 1second