import RPi.GPIO as io 

io.setmode(io.BCM) 
doorPin1 = 17
doorPin2 = 18
io.setup(doorPin1, io.IN, pull_up_down=io.PUD_UP)
io.setup(doorPin2, io.IN, pull_up_down=io.PUD_UP)

door1StatusPrev = -1
door2StatusPrev = -1

## Event loop
while True:
    door1Status = io.input(doorPin1)
    door2Status = io.input(doorPin2)
    if door1Status != door1StatusPrev:
        if door1Status:
            print("Door 1: Open")
        else:
            print("Door 1: Closed")
    if door2Status != door2StatusPrev:
        if door2Status:
            print("Door 2: Open")
        else:
            print("Door 2: Closed")
    door1StatusPrev = door1Status
    door2StatusPrev = door2Status

