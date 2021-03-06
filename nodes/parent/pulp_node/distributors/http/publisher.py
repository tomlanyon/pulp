# Copyright (c) 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


from pulp_node.distributors.publisher import join, FilePublisher
from pulp_node.manifest import MANIFEST_FILE_NAME


class HttpPublisher(FilePublisher):
    """
    An HTTP publisher.
    :ivar repo_id: A repository ID.
    :type repo_id: str
    :ivar alias: The httpd alias (base_url, directory)
    :type alias: tuple(2)
    """

    def __init__(self, base_url, alias, repo_id):
        """
        :param base_url: The base URL.
        :type base_url: str
        :param alias: The httpd alias (base_url, publish_dir)
        :type alias: tuple(2)
        :param repo_id: A repository ID.
        :type repo_id: str
        """
        self.base_url = base_url
        self.alias = alias
        FilePublisher.__init__(self, alias[1], repo_id)

    def link_unit(self, units):
        # Add the URL to each unit.
        unit, relative_path = FilePublisher.link_unit(self, units)
        if relative_path:
            url = join(self.base_url, self.alias[0], relative_path)
            unit['_download'] = dict(url=url)
        return unit, relative_path

    def manifest_path(self):
        """
        Get the relative URL path to the manifest.
        :return: The path component of the URL.
        :rtype: str
        """
        return join(self.alias[0], self.repo_id, MANIFEST_FILE_NAME)