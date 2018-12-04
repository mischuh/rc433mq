import json
import os
from abc import abstractmethod
from typing import Any, Callable

import attr
import paho.mqtt.client as mqtt
from schema import And, Optional, Schema, SchemaMissingKeyError, Use

from .util import LogMixin


class InvalidClientConfigException(Exception):
    pass


class SubscriptionException(Exception):
    pass


@attr.s
class GenericClient(LogMixin):

    client_conf = attr.ib(validator=attr.validators.instance_of(dict))
    client = attr.ib(default=None, init=False)

    @classmethod
    def from_config(cls, file_name: str) -> 'GenericClient':
        """
        Instead from dictionary loads the devices from a config json file.
        Args:
            file_name (str): Path of the file to load the devices from.
        Returns:
            Returns a `Conusmer` that is initialized from the given json.
        """
        with open(file_name, 'r') as fp:
            jsonf = json.load(fp)

        return cls.from_json(jsonf)

    @classmethod
    def from_json(cls, config: dict) -> 'GenericClient':
        """
        Instead from dictionary loads the devices from a config
        Args:
            config (dict): dictionary with valid config
        Returns:
            Returns a `Conusmer` that is initialized from the given json.
        """
        try:
            clz = cls(client_conf=config)
            clz.validate_config()
            return clz
        except (SchemaMissingKeyError, ValueError):
            raise InvalidClientConfigException(
                "Given consumer config is not valid: {config}".
                format(**locals())
            )

    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup connection to a Message Broker
        Concrete class must implement details
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validates json config for a specific Message Broker
        Concrete class must implement details
        """
        pass

    @abstractmethod
    def connect(self, func: Callable = None, *args) -> Any:
        pass


class MQTTClient(GenericClient):

    SCHEMA = Schema({
            Optional('host'): str,
            'port': And(Use(int), lambda n: 0 <= n <= 65535),
            Optional('username'): str,
            Optional('password'): str,
            'topics': dict
        })

    def validate_config(self) -> bool:
        success = MQTTClient.SCHEMA.validate(self.client_conf) \
            and os.environ.get(
                'MQTT_HOST',
                self.client_conf.get('host')
            )
        if not success:
            raise ValueError(
                "Check your consumer configuration. "
                "Something is wrong with it. "
                "Hint: `host`: '{}".format(os.environ.get(
                        'MQTT_HOST',
                        self.client_conf.get('host')
                    )
                )
            )
        return success

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """
        Fallback method in case no callback function is passed into
        `MQTTConsumer.consume(on_connect)` function
        """
        pass

    def _on_message(self, client, userdata, message) -> None:
        """
        Fallback method in case no callback function is passed into
        `MQTTConsumer.consume(on_message)` function
        """
        self.logger.info(
            "Default callback: Received message '{}' on topic '{}'".format(
                message.payload.decode('utf-8'),
                message.topic
            )
        )

    def connect(self,
                on_connect: Callable = None,
                on_message: Callable = None,
                *args) -> Any:
        """
        """
        self.client = mqtt.Client()
        self.client.on_connect = on_connect or self._on_connect
        self.client.on_message = on_message or self._on_message
        username = os.environ.get(
            'MQTT_USERNAME',
            self.client_conf.get('username', None)
        )
        if username:
            self.client.username_pw_set(
                username=username,
                password=os.environ.get(
                    'MQTT_PASSWORD',
                    self.client_conf.get('password', None)
                )
            )
        self.client.connect(
            host=os.environ.get(
                'MQTT_HOST',
                self.client_conf.get('host', None)
            ),
            port=self.client_conf['port'],
            keepalive=60
        )

    def cleanup(self) -> None:
        self.logger.info("Disconnecting...")
        self.client.disconnect()


class GenericPublisher:

    @abstractmethod
    def publish(self, message):
        pass


class MQTTPublisher(MQTTClient, GenericPublisher):

    def publish(self, topic, payload=None, qos=0, retain=False) -> None:
        self.connect()
        self.client.publish(topic, payload, qos, retain)


class GenericSubscriber:

    @abstractmethod
    def consume(self, *args, **kwargs) -> None:
        pass


class MQTTSubscriber(MQTTClient, GenericSubscriber):

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """
        The callback for when the client receives a CONNACK
        response from the server. In this case the client subscribes
        to a list of topics.
        Args:
            client: mqtt.Client()
            userdata: the private user data as set in
                Client() or user_data_set()
            flags: response flags sent by the broker
            rc (int): the connection result
                The value of rc indicates success or not:
                0: Connection successful
                1: Connection refused - incorrect protocol version
                2: Connection refused - invalid client identifier
                3: Connection refused - server unavailable
                4: Connection refused - bad username or password
                5: Connection refused - not authorised
                6-255: Currently unused.
        """
        self.logger.debug(
            "Connection returned result: {}".format(mqtt.connack_string(rc))
        )
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        res = self.client.subscribe(list(self.client_conf['topics'].items()))
        if res[0] == mqtt.MQTT_ERR_SUCCESS:
            self.logger.debug(
                "Succesfully connected on topics: {}".
                format(list(self.client_conf['topics'].items()))
            )
        else:
            raise SubscriptionException(
                "Could not connect on topics: {}".
                format(list(self.client_conf['topics'].items()))
            )

    def consume(self, on_message_call: Callable, **kwargs) -> None:
        try:
            self.connect(on_message=on_message_call)
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.cleanup()
