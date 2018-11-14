import logging
import os
import random
import time

import paho.mqtt.client as mqtt

from app.device import DeviceDict, DeviceRegistry, MemoryState

level = logging.DEBUG
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=level
)
logger = logging.getLogger("RC433MQ")


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

    client = mqtt.Client()
    client.username_pw_set(
        username="admin",
        password="admin"
    )
    client.connect("localhost", 1883, 60)
    client.loop_start()

    while True:
        time.sleep(2)
        id = random.randrange(len(device_names))
        device = device_names[id]
        state = "on" if id % 2 == 0 else "off"
        # message = str(dict(
        #         device=device,
        #         state=state,
        #         uuid=str(uuid.uuid4()),
        #         ts=int(time.time())
        #     )
        # )
        # logger.info("Send message {} to topic 'rc433'".format(message))
        if device[:2] == 'gf':
            floor = 'groundfloor'
        elif device[:2] == 'ff':
            floor = 'firstfloor'
        elif device[:2] == 'sf':
            floor = 'secondfloor'

        logger.info(
            "rc433/{}/{}/switch: {}".format(floor, device, state.upper())
        )
        client.publish(
            "rc433/{}/{}/switch".format(floor, device), state.upper()
        )
