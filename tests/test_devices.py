import pytest

from app.device import CodeDevice, SystemDevice


def test_systemdevice():
    d = SystemDevice(device_name='test', system_code='00001', device_code='A')
    assert d.props()['device_name'] == str
    assert d.props()['system_code'] == str
    assert d.props()['device_code'] == str


def test_systemdevice_with_invalid_device_code():
    with pytest.raises(ValueError):
        SystemDevice(
            device_name='test',
            system_code='00001',
            device_code='AB'
        )


def test_codedevice():
    d = CodeDevice(device_name='test', code_on='123', code_off='321')
    assert d.props()['device_name'] == str
    assert d.props()['code_on'] == int
    assert d.props()['code_off'] == int
