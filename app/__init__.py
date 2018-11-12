try:
    import rpi_rf
    RFDevice = rpi_rf.RFDevice
except ImportError:
    # Mock it on non-rpi machines
    class RFDevice(object):
        def __init__(self, *args, **kwargs):
            pass

        def enable_tx(self):
            pass

        def cleanup(self):
            pass

        def tx_code(self, code, **kwargs):
            return True

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock it on non-rpi machines
    class GPIO:
        BOARD = 1
        OUT = 1
        IN = 1
        BCM = 1
        HIGH = 1
        LOW = 0

        @staticmethod
        def setmode(a):
            pass

        @staticmethod
        def setup(a, b):
            pass

        @staticmethod
        def output(a, b):
            pass

        @staticmethod
        def cleanup():
            pass

        @staticmethod
        def setwarnings(flag):
            pass
