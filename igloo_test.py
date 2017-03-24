from client import webBus
from operator import add
#b = webBus("pi7",0)

# Read from Igloo
def readIgloo(b, slot, address, num_bytes=1):
    b.write(0x00,[0x06])
    b.write(slot,[0x11,0x03,0,0,0])
    b.write(0x09,[address])
    b.read(0x09, num_bytes)
    message = b.sendBatch()[-1]
    if message[0] != '0':
        print 'Igloo i2c error, mein freund'
    return message
