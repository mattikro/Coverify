import storage
import board
import digitalio

switch = digitalio.DigitalInOut(board.BUTTON_UP)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

storage.remount("/", not switch.value)