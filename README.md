# RC433MQ: Switch state of 433Mhz devices via messages

Paste some intelligent text...

## For local testing

Start local MQTT broker

    docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto

## Supported broker

At the moment only MQTT brokers are supported. Feel free to implement a new one.

Define a _config file_ for a broker in _conf_ folder:
I think this is straight forward. You can define more than one topic.
Each topic can have its own QoS.

```json
   {
        "host": "localhost",
        "port": 1883,
        "username": "admin",
        "password": "admin",
        "topics": {
            "rc433/device1": 0,
            "rc433/device2": 0,
            "rc433/device3": 0,
            "rc433/device4": 0
        }
    }
```

If you donnot want to store `host`, `username` and `passwort` within a config file
you also have the option to expose environment variables `MQTT_HOST`, `MQTT_USERNAME` and `MQTT_PASSWORD`
(in case of a MQTT broker. Other brokers may have other variables).