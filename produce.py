"""
    Example Producer setup
"""

import logging
import os
import random
import time
import uuid

from app.broker import MQTTPublisher
from app.device import DeviceDict, DeviceRegistry, MemoryState

level = logging.DEBUG
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=level
)
logger = logging.getLogger("RC433MQ")

base_path = os.path.abspath(os.path.dirname(__file__))


def get_devices():
    base_path = os.path.abspath(os.path.dirname(__file__))
    config_file = os.path.join(base_path, 'conf/devices.json')
    logger.info("Loading devices...")
    try:
        device_store = DeviceDict.from_json(config_file)
        device_state = MemoryState()
        return DeviceRegistry(device_store, device_state)
    except Exception as why:
        logger.error(str(why))


if __name__ == '__main__':

    devices = get_devices()
    device_names = [dev.device.device_name for dev in devices.list()]
    logger.info(
        "Loaded {} devices which are: {}".
        format(str(len(device_names)), device_names)
    )

    config_file = os.path.join(base_path, 'conf/consumer.json')
    client = MQTTPublisher.from_config(config_file)

    while True:
        time.sleep(2)
        id = random.randrange(len(device_names))
        device = device_names[id]
        state = "on" if id % 2 == 0 else "off"
        message = dict(
            topic='rc433',
            device=device,
            state=state.upper(),
            command='switch',
            uuid=str(uuid.uuid4()),
            ts=int(time.time())
        )
        logger.info("Send message {}".format(message))
        client.publish(topic=message['topic'], payload=str(message))
