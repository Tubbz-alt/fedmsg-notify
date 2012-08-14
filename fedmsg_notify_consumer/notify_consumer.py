from paste.deploy.converters import asbool
from fedmsg.consumers import FedmsgConsumer
import fedmsg.text
import logging
import pynotify
import json

log = logging.getLogger("moksha.hub")


class NotifyConsumer(FedmsgConsumer):
    topic = 'org.fedoraproject.*'
    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None

        ENABLED = 'fedmsg.consumers.notifyconsumer.enabled'
        if not asbool(hub.config.get(ENABLED, False)):
            log.info(
                'fedmsg.consumers.notifyconsumer disbaled')
        pynotify.init("Fedmsg")
        return super(NotifyConsumer, self).__init__(hub)

    def consume(self, msg):
        if type(msg['body']) == type(""):
            msg['body'] = json.loads(msg['body'])
        if msg['topic'] != 'org.fedoraproject._heartbeat':
            pretty_text = fedmsg.text.msg2repr(msg)
            print pretty_text
            note = pynotify.Notification("Fedmsg", pretty_text)
            note.show()
