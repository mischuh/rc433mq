import time
from abc import abstractmethod

import attr

from . import GPIO, RFDevice
from .device import CodeDevice, StatefulDevice, SystemDevice
from .util import LogMixin


class UnsupportedDeviceError(Exception):
    """Raised when a device is unsupported."""
    pass


@attr.s
class RC433Service(LogMixin):

    pin = attr.ib(
        default=17,
        converter=int,
        validator=attr.validators.instance_of(int)
    )

    @abstractmethod
    def applicable(self, device):
        res = self._applicable(device)
        if not res:
            raise UnsupportedDeviceError(
                "The device type '{}' is not supported".format(
                    str(type(device))))
        return res

    @abstractmethod
    def switch(self, device, state):
        if isinstance(device, StatefulDevice):
            # Unpack the actual device from the Stateful device wrapper
            device = device.device
        self.logger.info(
            "Device switch for '{device}' to '{state}' requested".format(
                **locals()
            )
        )
        assert state.lower() in ['on', 'off']
        assert self.applicable(device)
        return self._switch(device, state)


@attr.s
class RC433Switch(RC433Service):
    # Number of transmissions
    REPEAT = 10
    # microseconds
    PULSE_LENGTH = 300
    GPIOMode = GPIO.BCM
    DEVICE_LETTER = {"A": 1, "B": 2, "C": 4, "D": 8, "E": 16, "F": 32, "G": 64}

    def _initialize(self):
        GPIO.setmode(RC433Switch.GPIOMode)
        GPIO.setup(self.pin, GPIO.OUT)

    def __del__(self):
        GPIO.cleanup()

    def _applicable(self, device):
        return isinstance(device, SystemDevice)

    def _switch(self, device, state):
        key = [
            int(device.system_code[0]),
            int(device.system_code[1]),
            int(device.system_code[2]),
            int(device.system_code[3]),
            int(device.system_code[4])
        ]
        device_letter = RC433Switch.DEVICE_LETTER[device.device_code]
        self._initialize()
        self.logger.debug(
            "Toggle device (bit:{}, name:{}, state: {})"
            .format(device_letter, device.device_name, state)
        )
        return self._toggle(
            GPIO.HIGH if state.lower() == 'on' else GPIO.LOW,
            key,
            device_letter
        )

    def _toggle(self, switch, key, device_letter):
        bit = [
            142, 142, 142, 142, 142, 142, 142, 142,
            142, 142, 142, 136, 128, 0, 0, 0
        ]

        for t in range(5):
            if key[t]:
                bit[t] = 136
        x = 1
        for i in range(1, 6):
            if device_letter & x > 0:
                bit[4 + i] = 136
            x = x << 1

        if switch == GPIO.HIGH:
            bit[10] = 136
            bit[11] = 142

        bangs = []
        for y in range(16):
            x = 128
            for i in range(1, 9):
                b = (bit[y] & x > 0) and GPIO.HIGH or GPIO.LOW
                bangs.append(b)
                x = x >> 1

        GPIO.output(self.pin, GPIO.LOW)
        for z in range(RC433Switch.REPEAT):
            for b in bangs:
                GPIO.output(self.pin, b)
                time.sleep(RC433Switch.PULSE_LENGTH / 1000000.)

        return True


@attr.s
class RC433Code(RC433Service):
    """
    Remote control 433mhz devices.
    """
    rf_device = attr.ib(default=None, init=False)

    def _initialize(self):
        """Sets the RFDevice to transmit state if necessary"""
        if self.rf_device is None:
            self.rf_device = RFDevice(self.pin)
            self.rf_device.enable_tx()

    def __del__(self):
        """Stops transmitting."""
        if self.rf_device is not None:
            self.rf_device.cleanup()
            self.rf_device = None

    def _applicable(self, device):
        return isinstance(device, CodeDevice)

    def _switch(self, device, state):
        if isinstance(device, StatefulDevice):
            # Unpack the actual device from the Stateful device wrapper
            device = device.device
        return self._send_code(device.code_on if state else device.code_off)

    def _send_code(self, code):
        """
        Sends a decimal code via 433mhz. This implementation will actually
        send the code five times to make sure that any disturbance
        in the force has less impact.
        Args:
            code (int): Code to send
        Returns:
            Returns True if the underlying RFDevice acknowledged;
            otherwise False.
        """
        if not isinstance(code, int):
            raise TypeError(
                "Argument code is expected to be an int, but given is '{}'".
                format(type(code)))

        self._initialize()
        self.logger.debug("Sending code '{}'".format(code))
        return any([self.rf_device.tx_code(code) for _ in range(5)])


class RC433Factory:
    """
    Factory to serve the right `RC433Service` for a given `Device`
    """

    MAPPING = {
        'CodeDevice': RC433Code,
        'SystemDevice': RC433Switch
    }

    @staticmethod
    def service(device):
        if isinstance(device, StatefulDevice):
            # Unpack the actual device from the Stateful device wrapper
            device = device.device
        svc = RC433Factory.MAPPING.get(device.__class__.__name__, None)
        if svc is None:
            raise UnsupportedDeviceError(
                "The device type '{}' is not supported".format(
                    str(type(device)))
            )
        return svc
