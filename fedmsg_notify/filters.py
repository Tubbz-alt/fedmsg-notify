# This file is a part of fedmsg-notify.
#
# fedmsg-notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fedmsg-notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fedmsg-notify.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2012, 2013 Red Hat, Inc.
# Authors: Luke Macken <lmacken@redhat.com>

import json
import logging

from twisted.internet import reactor

from .distro_specific import (get_installed_packages,
                              get_reported_bugs,
                              get_user_packages)

log = logging.getLogger('moksha.hub')


class Filter(object):
    __description__ = None
    __user_entry__ = None

    def __init__(self, settings):
        self.settings = settings

    def match(self, msg, processor):
        raise NotImplementedError

    @classmethod
    def is_available(self):
        return True

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


class ReportedBugsFilter(Filter):
    """ Matches messages that reference bugs that abrt has encountered """
    __description__ = 'Bugs that you have encountered'

    def __init__(self, settings):
        """ Pull bug numbers out of local reports """
        self.bugs = get_reported_bugs()

    def match(self, msg, processor):
        """ Check if this update fixes and of our bugs """
        if processor.__name__ == 'Bodhi':
            update = msg['msg'].get('update')
            if update:
                bugs = [bug['bug_id'] for bug in update['bugs']]
                for bug in self.bugs:
                    if bug in bugs:
                        log.info("Message contains bug that user filed!")
                        return True

    @classmethod
    def is_available(self):
        return not getattr(get_reported_bugs, 'disabled', False)


class MyPackageFilter(Filter):
    """ Matches messages regarding packages that a given user has ACLs on """
    __description__ = 'Packages that these users maintain'
    __user_entry__ = 'Usernames'

    def __init__(self, settings):
        self.usernames = settings.replace(',', ' ').split()
        self.packages = set()
        reactor.callInThread(self._query_maintained_packages)

    def _query_maintained_packages(self):
        self.packages = get_user_packages(self.usernames)

    def match(self, msg, processor):
        packages = processor.packages(msg)
        for package in self.packages:
            if package in packages:
                return True


class UsernameFilter(Filter):
    """ Matches messages that contain specific usernames """
    __description__ = 'Messages that reference specific users'
    __user_entry__ = 'Usernames'

    def __init__(self, settings):
        self.usernames = settings.replace(',', ' ').split()

    def match(self, msg, processor):
        for username in processor.usernames(msg):
            if username in self.usernames:
                return True


class PackageFilter(Filter):
    """ Matches messages referencing packages that are specified by the user """
    __description__ = 'Messages that reference specific packages'
    __user_entry__ = 'Packages'

    def __init__(self, settings):
        self.packages = settings.replace(',', ' ').split()

    def match(self, msg, processor):
        for package in processor.packages(msg):
            if package in self.packages:
                return True


class InstalledPackageFilter(Filter):
    """ Matches messages referencing packages that are installed locally """
    __description__ = 'Packages that you have installed'

    def __init__(self, settings):
        self.packages = []
        reactor.callInThread(self._query_local_packages)

    def _query_local_packages(self):
        self.packages = list(get_installed_packages())

    def match(self, msg, processor):
        for package in processor.packages(msg):
            if package in self.packages:
                return True


def get_enabled_filters(settings, key='enabled-filters'):
    try:
        return json.loads(settings.get_string(key))
    except ValueError:
        return settings.get_string(key).split()


filters = [
    ReportedBugsFilter,
    InstalledPackageFilter,
    PackageFilter,
    MyPackageFilter,
    UsernameFilter,
]
