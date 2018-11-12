from app.device import SystemDevice
from app.rc433 import RC433Factory, RC433Switch


def test_rc433_factory():
    device = SystemDevice(
        device_name='test', system_code='00001', device_code='A'
    )
    svc = RC433Factory.service(device)
    assert isinstance(svc, RC433Switch.__class__)


def test_rc44_factory_stateful_device():
    pass
