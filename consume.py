import json
import logging
import os
from logging.config import dictConfig

import yaml
from schema import And, Optional, Schema, Use

from app.broker import MQTTPublisher, MQTTSubscriber
from app.device import DeviceDict, DeviceRegistry, MemoryState
from app.rc433 import RC433Factory

base_path = os.path.abspath(os.path.dirname(__file__))

global_config = yaml.load(open(os.path.join(base_path, 'conf/logging.yaml')))
dictConfig(global_config['logging'])
logger = logging.getLogger("RC433MQ")


MSG_SCHEMA = Schema({
    'topic': str,
    'command': And(str, lambda s: s in ['switch', 'state']),
    'device': str,
    'state': And(str, Use(str.lower), lambda s: s in ('on', 'off')),
    Optional('floor'): str,
    Optional('uuid'): str,
    Optional('ts'): int
})


def get_devices():
    config_file = os.path.join(base_path, 'conf/devices.json')
    logger.info("Loading devices...")
    try:
        device_store = DeviceDict.from_json(config_file)
        device_state = MemoryState()
        return DeviceRegistry(device_store, device_state)
    except Exception as why:
        logger.error(str(why))


if __name__ == '__main__':

    def handle_state(client, userdata, message):
        """
        Callback function if a message appears on subscribed topi
        """
        try:
            msg = json.loads(message.payload.decode("utf-8").replace("'", '"'))
            MSG_SCHEMA.validate(msg)
            logger.info(
                "Topic '{topic}' received state {state} for device '{device}'"
                .format(**msg)
            )
            device = device_db.lookup(msg['device'])
            svc = RC433Factory.service(device)()
            svc.switch(device=device, state=msg['state'])
            # return result
            msg['command'] = 'state'
            topic = "{topic}/state".format(**msg)
            mqp.publish(topic=topic, payload=str(msg), retain=True)
        except Exception:
            import traceback
            logger.error(traceback.print_exc())

    device_db = get_devices()
    device_names = [dev.device.device_name for dev in device_db.list()]
    logger.info(
        "Loaded {} devices {}".
        format(str(len(device_names)), device_names)
    )

    config_file = os.path.join(base_path, 'conf/consumer.json')
    mqs = MQTTSubscriber.from_config(config_file)
    mqp = MQTTPublisher.from_config(config_file)
    mqs.consume(handle_state)
