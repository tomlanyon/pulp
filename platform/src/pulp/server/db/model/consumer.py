# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import datetime

from pulp.server.db.model.base import Model
from pulp.common import dateutils

# -- classes -----------------------------------------------------------------

class Consumer(Model):
    """
    Represents a consumer of the content on Pulp server.

    @ivar consumer_id: uniquely identifies the consumer
    @type consumer_id: str

    @ivar display_name: user-friendly name of the consumer
    @type display_name: str

    @ivar description: user-friendly description of the consumer
    @type description: str

    @ivar notes: arbitrary key-value pairs programmatically describing the consumer
    @type notes: dict

    @param capabilities: operations permitted on the consumer
    @type capabilities: dict

    @param certificate: x509 certificate for the consumer
    @type certificate: str
    """

    collection_name = 'consumers'
    unique_indices = ('id',)
    search_indices = ('notes',)

    def __init__(self, consumer_id, display_name, description=None, notes=None, capabilities=None, certificate=None):
        super(Consumer, self).__init__()

        self.id = consumer_id
        self.display_name = display_name
        self.description = description
        self.notes = notes or {}

        self.capabilities = capabilities or {}
        self.certificate = certificate or None


class Bind(Model):
    """
    Represents consumer binding to a repo/distributor.

    Each consumer action entry will be of the format: {id:<str>, action:<str>, status:<str>}
    * Status: (pending|succeeded|failed)
    * Action: (bind|unbind)

    :ivar consumer_id: uniquely identifies the consumer.
    :type consumer_id: str
    :ivar repo_id: uniquely identifies the repository
    :type repo_id: str
    :ivar distributor_id: uniquely identifies a distributor
    :type distributor_id: str
    :ivar notify_agent: indicates if the agent should be sent a message informing it of the binding
    :type notify_agent: bool
    :ivar binding_config: value only applicable to this particular binding
    :type binding_config: object
    :ivar consumer_actions: tracks consumer bind/unbind actions; see above for format
    :ivar deleted: indicates the bind has been deleted
    :type deleted: bool
    """
    collection_name = 'consumer_bindings'
    unique_indices = (
        ('repo_id', 'distributor_id', 'consumer_id'),
    )
    search_indices = (
        ('consumer_id',),
    )

    class Action:
        # enumerated actions
        BIND = 'bind'
        UNBIND = 'unbind'

    class Status:
        # enumerated status
        PENDING = 'pending'
        SUCCEEDED = 'succeeded'
        FAILED = 'failed'

    def __init__(self, consumer_id, repo_id, distributor_id, notify_agent, binding_config):
        """
        :param consumer_id: uniquely identifies the consumer.
        :type consumer_id: str
        :param repo_id: uniquely identifies the repository.
        :type repo_id: str
        :param distributor_id: uniquely identifies a distributor.
        :type distributor_id: str
        :ivar notify_agent: controls whether or not the consumer agent will be sent a message
                            about the binding
        ;type notify_agent: bool
        :ivar binding_config: configuration to pass the distributor during payload creation for this
                              binding
        :type binding_config: object
        """
        super(Bind, self).__init__()

        # Required, Unique
        self.consumer_id = consumer_id
        self.repo_id = repo_id
        self.distributor_id = distributor_id

        # Configuration
        self.notify_agent = notify_agent
        self.binding_config = binding_config

        # State
        self.consumer_actions = []
        self.deleted = False


class UnitProfile(Model):
    """
    Represents an install content unit profile.
    @ivar consumer_id: A consumer ID.
    @type consumer_id: str
    @ivar content_type: The profile (unit) type ID.
    @type content_type: str
    @ivar profile: The stored profile.
    @type profile: dict
    """

    collection_name = 'consumer_unit_profiles'
    unique_indices = (
        ('consumer_id', 'content_type'),
    )

    def __init__(self, consumer_id, content_type, profile):
        """
        @param consumer_id: A consumer ID.
        @type consumer_id: str
        @param content_type: The profile (unit) type ID.
        @type content_type: str
        @param profile: The stored profile.
        @type profile: dict
        """
        super(UnitProfile, self).__init__()
        self.consumer_id = consumer_id
        self.content_type = content_type
        self.profile = profile


class ConsumerHistoryEvent(Model):
    """
    Represents a consumer history event.

    @ivar consumer_id: identifies the consumer
    @type consumer_id: str

    @ivar originator: consumer or username of the admin who initiated the event
    @type originator: str

    @param type: event type
                 current supported event types: 'consumer_registered', 'consumer_unregistered', 'repo_bound', 'repo_unbound',
                 'content_unit_installed', 'content_unit_uninstalled', 'unit_profile_changed', 'added_to_group', 'removed_from_group'
    @type  type: str

    @param details: event details
    @type details: dict
    """
    collection_name = 'consumer_history'
    search_indices = ('consumer_id', 'originator', 'type', )

    def __init__(self, consumer_id, originator, event_type, details):
        super(ConsumerHistoryEvent, self).__init__()

        self.consumer_id = consumer_id
        self.originator = originator
        self.type = event_type
        self.details = details
        now = datetime.datetime.now(dateutils.utc_tz())
        self.timestamp = dateutils.format_iso8601_datetime(now)

class ConsumerGroup(Model):
    """
    Represents a group of consumers.
    """
    collection_name = 'consumer_groups'
    search_indices = ('display_name', 'consumer_ids')

    def __init__(self, consumer_group_id, display_name=None, description=None, 
            consumer_ids=None, notes=None):
        super(ConsumerGroup, self).__init__()

        self.id = consumer_group_id
        self.display_name = display_name
        self.description = description
        self.consumer_ids = consumer_ids or []
        self.notes = notes or {}

        self.scratchpad = None
