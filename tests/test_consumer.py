import os

import pytest

from app.broker import InvalidClientConfigException, MQTTSubscriber


def test_mqtt_from_config():
    base_path = os.path.abspath(os.path.dirname(__file__))
    config = os.path.join(base_path, './conf/consumer_test.json')
    mqtt = MQTTSubscriber.from_config(config)
    assert mqtt.client_conf['host'] == 'localhost'
    assert mqtt.client_conf['port'] == 1883


def test_from_config_with_empty_yaml():
    base_path = os.path.abspath(os.path.dirname(__file__))
    empty_config = os.path.join(base_path, './conf/empty.json')
    from json.decoder import JSONDecodeError
    with pytest.raises(JSONDecodeError):
        MQTTSubscriber.from_config(empty_config)


def test_invalid_mqtt_from_config():
    base_path = os.path.abspath(os.path.dirname(__file__))
    config = os.path.join(base_path, './conf/invalid_consumer_test.json')
    with pytest.raises(InvalidClientConfigException) as why:
        MQTTSubscriber.from_config(config)
    assert "Given consumer config is not valid:" in str(why)


# def test_mqtt_with_env_vars():
#     given_config = {'port': 1234, 'topics': {'topic_name': 0}}
#     expected_config = {** given_config, **{
#         'host': 'mqtthost',
#         'username': 'minime',
#         'password': '123admin'
#     }}
#     mq = MQTTConsumer.from_json(given_config)
#     assert list(mq.consumer_conf.keys()).sort() \
#         == list(expected_config.keys()).sort()
