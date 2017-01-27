# config.py

# Configuration definitions
# Simply "import config" and use definitions 

# Define Raspberry Pi IP Address
#ip_address = "192.168.1.1"
ip_address = "pi7"

# Define i2c addresses
gpio = 0x70     # gpio chip
fanout = 0x72   # fanout board
ccm = 0x74      # ngccm emulator

# Define fanout channel values
# For bits 0,1,2,3 use values 1,2,4,8
# For bits 4,5,6,7 use values 0x10, 0x20, 0x40, 0x80                        
channels = [1,2]        

