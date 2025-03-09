from machine import Pin, Timer
from utime import sleep_ms

OFF = 0
ON = 1

SHORT_SLEEP_MS = 100
LONG_SLEEP_MS = 500

#setup
led_pin_numbers = 18
pin  = Pin(led_pin_numbers, Pin.OUT)

def turn_off_leds():
    pin.value(OFF)

def turn_on_leds():
    pin.value(ON)

def setup_pins():
    COUNT = 0
    while COUNT < 10:
        turn_on_leds()
        sleep_ms(SHORT_SLEEP_MS)
        turn_off_leds()
        sleep_ms(SHORT_SLEEP_MS)
        COUNT += 1

def main():
    setup_pins()
    led_timer = Timer(-1)
    led_timer.init(period=LONG_SLEEP_MS, mode=Timer.PERIODIC, callback=lambda t: turn_on_leds())


if __name__ == '__main__':
    main()