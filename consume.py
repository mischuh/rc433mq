import logging
import os

from schema import And, Optional, Schema, Use

from app.consumer import MQTTConsumer
from app.device import DeviceDict, DeviceRegistry, MemoryState
from app.rc433 import RC433Factory

level = logging.DEBUG
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=level
)
logger = logging.getLogger("RC433MQ")

base_path = os.path.abspath(os.path.dirname(__file__))

STATE_SCHEMA = Schema(And(str, Use(str.lower), lambda s: s in ('on', 'off')))
TOPIC_SCHEMA = Schema({
    'topic': And(str, lambda s: s == 'rc433'),
    'floor': And(
        str,
        lambda s: s in ['groundfloor', 'firstfloor', 'secondfloor']
    ),
    'device': And(str, lambda s: s[:2] in ['gf', 'ff', 'sf']),
    Optional('command'): str
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
        try:
            TOPICS = ['topic', 'floor', 'device', 'command']
            topic_dict = dict(zip(TOPICS, message.topic.split("/")))
            TOPIC_SCHEMA.validate(topic_dict)

            state = message.payload.decode("utf-8")
            STATE_SCHEMA.validate(state)

            logger.debug(
                "Topic {topic_dict} received state {state}".format(**locals())
            )
            device = device_db.lookup(topic_dict['device'])
            svc = RC433Factory.service(device)()
            success = svc.switch(device=device, state=state)
            # TODO: publish success code to loopback topic
            logger.info("Succes: {success}".format(**locals()))
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
    mq = MQTTConsumer.from_config(config_file)
    mq.consume(handle_state)
