#!/usr/bin/python
#
# Copyright (c) 2012 Red Hat, Inc.
#
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import glob
import mock
import os
import shutil
import sys
import tempfile
import time
import unittest
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../../src/")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../../plugins/importers/yum_importer/")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../../plugins/distributors/yum_distributor/")
from distributor import YumDistributor, YUM_DISTRIBUTOR_TYPE_ID, \
        REQUIRED_CONFIG_KEYS, OPTIONAL_CONFIG_KEYS, RPM_TYPE_ID, SRPM_TYPE_ID

from pulp.server.content.plugins.model import RelatedRepository, Repository, Unit
from pulp.server.content.plugins.config import PluginCallConfiguration

import distributor_mocks

class TestDistributor(unittest.TestCase):

    def setUp(self):
        super(TestDistributor, self).setUp()
        self.init()

    def tearDown(self):
        super(TestDistributor, self).tearDown()
        self.clean()

    def init(self):
        self.temp_dir = tempfile.mkdtemp()
        #pkg_dir is where we simulate units actually residing
        self.pkg_dir = os.path.join(self.temp_dir, "packages")
        os.makedirs(self.pkg_dir)
        #publish_dir simulates /var/lib/pulp/published
        self.publish_dir = os.path.join(self.temp_dir, "publish")
        os.makedirs(self.publish_dir)
        self.repo_working_dir = os.path.join(self.temp_dir, "repo_working_dir")
        os.makedirs(self.repo_working_dir)
        self.data_dir = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data"))

    def clean(self):
        shutil.rmtree(self.temp_dir)

    def get_units(self, count=5):
        units = []
        for index in range(0, count):
            u = self.get_unit()
            units.append(u)
        return units

    def get_unit(self, type_id="rpm"):
        uniq_id = uuid4()
        filename = "test_unit-%s" % (uniq_id)
        storage_path = os.path.join(self.pkg_dir, filename)
        metadata = {}
        metadata["relativepath"] = os.path.join("a/b/c", filename)
        metadata["filename"] = filename
        unit_key = uniq_id
        # Create empty file to represent the unit
        open(storage_path, "a+")
        u = Unit(type_id, unit_key, metadata, storage_path)
        return u

    def test_metadata(self):
        metadata = YumDistributor.metadata()
        self.assertEquals(metadata["id"], YUM_DISTRIBUTOR_TYPE_ID)
        self.assertTrue(RPM_TYPE_ID in metadata["types"])
        self.assertTrue(SRPM_TYPE_ID in metadata["types"])

    def test_validate_config(self):
        repo = mock.Mock(spec=Repository)
        distributor = YumDistributor()
        # Confirm that required keys are successful
        req_kwargs = {}
        req_kwargs['http'] = True
        req_kwargs['https'] = False
        req_kwargs['relative_url'] = "sample_value"
        config = distributor_mocks.get_basic_config(**req_kwargs)
        state, msg = distributor.validate_config(repo, config, [])
        self.assertTrue(state)
        # Confirm required and optional are successful
        optional_kwargs = dict(req_kwargs)
        optional_kwargs['auth_ca'] = open(os.path.join(self.data_dir, "valid_ca.crt")).read()
        optional_kwargs['https_ca'] = open(os.path.join(self.data_dir, "valid_ca.crt")).read()
        optional_kwargs['protected'] = True
        optional_kwargs['generate_metadata'] = True
        optional_kwargs['checksum_type'] = "sha"
        optional_kwargs['metadata_types'] = {}
        optional_kwargs['auth_cert'] = open(os.path.join(self.data_dir, "cert.crt")).read()
        config = distributor_mocks.get_basic_config(**optional_kwargs)
        state, msg = distributor.validate_config(repo, config, [])
        self.assertTrue(state)
        # Test that config fails when a bad value for non_existing_dir is used
        optional_kwargs["https_publish_dir"] = "non_existing_dir"
        config = distributor_mocks.get_basic_config(**optional_kwargs)
        state, msg = distributor.validate_config(repo, config, [])
        self.assertFalse(state)
        # Test config succeeds with a good value of https_publish_dir
        optional_kwargs["https_publish_dir"] = self.temp_dir
        config = distributor_mocks.get_basic_config(**optional_kwargs)
        state, msg = distributor.validate_config(repo, config, [])
        self.assertTrue(state)
        del optional_kwargs["https_publish_dir"]

        # Confirm an extra key fails
        optional_kwargs["extra_arg_not_used"] = "sample_value"
        config = distributor_mocks.get_basic_config(**optional_kwargs)
        state, msg = distributor.validate_config(repo, config, [])
        self.assertFalse(state)
        self.assertTrue("extra_arg_not_used" in msg)

        # Confirm missing a required fails
        del optional_kwargs["extra_arg_not_used"]
        config = distributor_mocks.get_basic_config(**optional_kwargs)
        state, msg = distributor.validate_config(repo, config, [])
        self.assertTrue(state)

        del optional_kwargs["relative_url"]
        config = distributor_mocks.get_basic_config(**optional_kwargs)
        state, msg = distributor.validate_config(repo, config, [])
        self.assertFalse(state)
        self.assertTrue("relative_url" in msg)

    def test_handle_symlinks(self):
        distributor = YumDistributor()
        units = []
        symlink_dir = os.path.join(self.temp_dir, "symlinks")
        num_links = 5
        for index in range(0,num_links):
            relpath = "file_%s.rpm" % (index)
            sp = os.path.join(self.pkg_dir, relpath)
            open(sp, "a") # Create an empty file
            if index % 2 == 0:
                # Ensure we can support symlinks in subdirs
                relpath = os.path.join("a", "b", "c", relpath)
            u = Unit("rpm", "unit_key_%s" % (index), {"relativepath":relpath}, sp)
            units.append(u)

        status, errors = distributor.handle_symlinks(units, symlink_dir)
        self.assertTrue(status)
        self.assertEqual(len(errors), 0)
        for u in units:
            symlink_path = os.path.join(symlink_dir, u.metadata["relativepath"])
            self.assertTrue(os.path.exists(symlink_path))
            self.assertTrue(os.path.islink(symlink_path))
            target = os.readlink(symlink_path)
            self.assertEqual(target, u.storage_path)
        # Test republish is successful
        status, errors = distributor.handle_symlinks(units, symlink_dir)
        self.assertTrue(status)
        self.assertEqual(len(errors), 0)
        for u in units:
            symlink_path = os.path.join(symlink_dir, u.metadata["relativepath"])
            self.assertTrue(os.path.exists(symlink_path))
            self.assertTrue(os.path.islink(symlink_path))
            target = os.readlink(symlink_path)
            self.assertEqual(target, u.storage_path)
        # Simulate a package is deleted
        os.unlink(units[0].storage_path)
        status, errors = distributor.handle_symlinks(units, symlink_dir)
        self.assertFalse(status)
        self.assertEqual(len(errors), 1)


    def test_get_relpath_from_unit(self):
        distributor = YumDistributor()
        test_unit = Unit("rpm", "unit_key", {}, "")

        test_unit.unit_key = {"fileName" : "test_1"}
        rel_path = distributor.get_relpath_from_unit(test_unit)
        self.assertEqual(rel_path, "test_1")

        test_unit.unit_key = {}
        test_unit.storage_path = "test_0"
        rel_path = distributor.get_relpath_from_unit(test_unit)
        self.assertEqual(rel_path, "test_0")

        test_unit.metadata["filename"] = "test_2"
        rel_path = distributor.get_relpath_from_unit(test_unit)
        self.assertEqual(rel_path, "test_2")

        test_unit.metadata["relativepath"] = "test_3"
        rel_path = distributor.get_relpath_from_unit(test_unit)
        self.assertEqual(rel_path, "test_3")


    def test_create_symlink(self):
        target_dir = os.path.join(self.temp_dir, "a", "b", "c", "d", "e")
        distributor = YumDistributor()
        # Create an empty file to serve as the source_path
        source_path = os.path.join(self.temp_dir, "some_test_file.txt")
        open(source_path, "a")
        symlink_path = os.path.join(self.temp_dir, "symlink_dir", "a", "b", "file_path.lnk")
        # Confirm subdir of symlink_path doesn't exist
        self.assertFalse(os.path.isdir(os.path.dirname(symlink_path)))
        self.assertTrue(distributor.create_symlink(source_path, symlink_path))
        # Confirm we created the subdir
        self.assertTrue(os.path.isdir(os.path.dirname(symlink_path)))
        self.assertTrue(os.path.exists(symlink_path))
        self.assertTrue(os.path.islink(symlink_path))
        # Verify the symlink points to the source_path
        a = os.readlink(symlink_path)
        self.assertEqual(a, source_path)

    def test_create_dirs(self):
        target_dir = os.path.join(self.temp_dir, "a", "b", "c", "d", "e")
        distributor = YumDistributor()
        self.assertFalse(os.path.exists(target_dir))
        self.assertTrue(distributor.create_dirs(target_dir))
        self.assertTrue(os.path.exists(target_dir))
        self.assertTrue(os.path.isdir(target_dir))
        # Test we can call it twice with no errors
        self.assertTrue(distributor.create_dirs(target_dir))
        # Remove permissions to directory and force an error
        orig_stat = os.stat(target_dir)
        try:
            os.chmod(target_dir, 0000)
            self.assertFalse(os.access(target_dir, os.R_OK))
            target_dir_b = os.path.join(target_dir, "f")
            self.assertFalse(distributor.create_dirs(target_dir_b))
        finally:
            os.chmod(target_dir, orig_stat.st_mode)

    def test_empty_publish(self):
        repo = mock.Mock(spec=Repository)
        repo.working_dir = self.repo_working_dir
        repo.id = "test_empty_publish"
        existing_units = []
        publish_conduit = distributor_mocks.get_publish_conduit(existing_units=existing_units, pkg_dir=self.pkg_dir)
        config = distributor_mocks.get_basic_config(https_publish_dir=self.publish_dir)
        distributor = YumDistributor()
        report = distributor.publish_repo(repo, publish_conduit, config)
        self.assertTrue(report.success_flag)
        summary = report.summary
        self.assertEqual(summary["num_units_attempted"], 0)
        self.assertEqual(summary["num_units_published"], 0)
        self.assertEqual(summary["num_units_errors"], 0)
        expected_repo_publish_dir = os.path.join(self.publish_dir, "repos", repo.id)
        self.assertEqual(summary["repo_publish_dir"], expected_repo_publish_dir)
        details = report.details
        self.assertEqual(len(details["errors"]), 0)


    def test_publish(self):
        repo = mock.Mock(spec=Repository)
        repo.working_dir = self.repo_working_dir
        repo.id = "test_publish"
        num_units = 10
        relative_url = "rel_a/rel_b/rel_c/"
        existing_units = self.get_units(count=num_units)
        publish_conduit = distributor_mocks.get_publish_conduit(existing_units=existing_units, pkg_dir=self.pkg_dir)
        config = distributor_mocks.get_basic_config(https_publish_dir=self.publish_dir, relative_url=relative_url)
        distributor = YumDistributor()
        report = distributor.publish_repo(repo, publish_conduit, config)
        self.assertTrue(report.success_flag)
        summary = report.summary
        self.assertEqual(summary["num_units_attempted"], num_units)
        self.assertEqual(summary["num_units_published"], num_units)
        self.assertEqual(summary["num_units_errors"], 0)
        expected_repo_publish_dir = os.path.join(self.publish_dir, "repos", relative_url)
        self.assertEqual(summary["repo_publish_dir"], expected_repo_publish_dir)
        details = report.details
        self.assertEqual(len(details["errors"]), 0)
        #
        # Add a verification of the publish directory
        #
        self.assertTrue(os.path.exists(summary["repo_publish_dir"]))
        self.assertTrue(os.path.islink(summary["repo_publish_dir"].rstrip("/")))
        source_of_link = os.readlink(expected_repo_publish_dir.rstrip("/"))
        self.assertEquals(source_of_link, repo.working_dir)
        #
        # Verify the expected units
        #
        for u in existing_units:
            expected_link = os.path.join(expected_repo_publish_dir, u.metadata["relativepath"])
            self.assertTrue(os.path.exists(expected_link))
            actual_target = os.readlink(expected_link)
            expected_target = u.storage_path
            self.assertEqual(actual_target, expected_target)

    def test_split_path(self):
        distributor = YumDistributor()
        test_path = "/a"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 1)
        self.assertTrue(pieces[0], test_path)

        test_path = "/a/"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 1)
        self.assertTrue(pieces[0], test_path)

        test_path = "/a"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 1)
        self.assertTrue(pieces[0], test_path)

        test_path = "a/"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 1)
        self.assertTrue(pieces[0], test_path)

        test_path = "/a/bcde/f/ghi/j"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 5)
        self.assertTrue(os.path.join(*pieces), test_path)

        test_path = "a/bcde/f/ghi/j"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 5)
        self.assertTrue(os.path.join(*pieces), test_path)

        test_path = "a/bcde/f/ghi/j/"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 5)
        self.assertTrue(os.path.join(*pieces), test_path)

        test_path = "/a/bcde/f/ghi/j/"
        pieces = distributor.split_path(test_path)
        self.assertEqual(len(pieces), 5)
        self.assertTrue(os.path.join(*pieces), test_path)

    def test_form_rel_url_lookup_table(self):
        distributor = YumDistributor()
        existing_urls = distributor.form_rel_url_lookup_table(None)
        self.assertEqual(existing_urls, {})

        url_a = "/abc/de/fg/"
        config_a = PluginCallConfiguration({"relative_url":url_a}, {})
        repo_a = RelatedRepository("repo_a_id", [config_a])

        conflict_url_a = "/abc/de/"
        conflict_config_a = PluginCallConfiguration({"relative_url":conflict_url_a}, {})
        conflict_repo_a = RelatedRepository("conflict_repo_id_a", [conflict_config_a])

        url_b = "/abc/de/kj/"
        config_b = PluginCallConfiguration({"relative_url":url_b}, {})
        repo_b = RelatedRepository("repo_b_id", [config_b])
        repo_b_dup = RelatedRepository("repo_b_dup_id", [config_b])

        url_c = "/abc/jk/fg/gfgf/gfgf/gfre/"
        config_c = PluginCallConfiguration({"relative_url":url_c}, {})
        repo_c = RelatedRepository("repo_c_id", [config_c])

        url_d = "simple"
        config_d = PluginCallConfiguration({"relative_url":url_d}, {})
        repo_d = RelatedRepository("repo_d_id", [config_d])

        url_e = ""
        config_e = PluginCallConfiguration({"relative_url":url_e}, {})
        repo_e = RelatedRepository("repo_e_id", [config_e])

        url_f = "/foo"
        config_f = PluginCallConfiguration({"relative_url":url_f}, {})
        repo_f = RelatedRepository("repo_f_id", [config_f])

        conflict_url_f = "foo/"
        conflict_config_f = PluginCallConfiguration({"relative_url":conflict_url_f}, {})
        conflict_repo_f = RelatedRepository("conflict_repo_f_id", [conflict_config_f])

        url_g = "bar/"
        config_g = PluginCallConfiguration({"relative_url":url_g}, {})
        repo_g = RelatedRepository("repo_g_id", [config_g])

        # Try with url set to None
        url_h = None
        config_h = PluginCallConfiguration({"relative_url":url_h}, {})
        repo_h = RelatedRepository("repo_h_id", [config_h])

        # Try with relative_url not existing
        config_i = PluginCallConfiguration({}, {})
        repo_i = RelatedRepository("repo_i_id", [config_i])

        existing_urls = distributor.form_rel_url_lookup_table([repo_a, repo_d, repo_e, repo_f, repo_g, repo_h])
        self.assertEqual(existing_urls, {'simple': {'repo_id': repo_d.id, 'url': url_d}, 
            'abc': {'de': {'fg': {'repo_id': repo_a.id, 'url': url_a}}}, 
            repo_e.id : {'repo_id': repo_e.id, 'url': repo_e.id}, # url_e is empty so we default to use repo id
            repo_h.id : {'repo_id': repo_h.id, 'url': repo_h.id}, # urk_h is None so we default to use repo id
            'bar': {'repo_id': repo_g.id, 'url':url_g}, 'foo': {'repo_id': repo_f.id, 'url': url_f}})

        existing_urls = distributor.form_rel_url_lookup_table([repo_a])
        self.assertEqual(existing_urls, {'abc': {'de': {'fg': {'repo_id': repo_a.id, 'url': url_a}}}})

        existing_urls = distributor.form_rel_url_lookup_table([repo_a, repo_b])
        self.assertEqual(existing_urls, {'abc': {'de': {'kj': {'repo_id': repo_b.id, 'url': url_b}, 'fg': {'repo_id': repo_a.id, 'url': url_a}}}})

        existing_urls = distributor.form_rel_url_lookup_table([repo_a, repo_b, repo_c])
        self.assertEqual(existing_urls, {'abc': {'de': {'kj': {'repo_id': repo_b.id, 'url':url_b}, 
            'fg': {'repo_id': repo_a.id, 'url':url_a}}, 'jk': {'fg': {'gfgf': {'gfgf': {'gfre': {'repo_id': repo_c.id, 'url':url_c}}}}}}})

        # Add test for exception on duplicate with repos passed in
        caught = False
        try:
            existing_urls = distributor.form_rel_url_lookup_table([repo_a, repo_b, repo_b_dup, repo_c])
        except Exception, e:
            caught = True
        self.assertTrue(caught)

        caught = False
        try:
            existing_urls = distributor.form_rel_url_lookup_table([repo_f, conflict_repo_f])
        except Exception, e:
            caught = True
        self.assertTrue(caught)

        # Add test for exception on conflict with a subdir from an existing repo
        caught = False
        try:
            existing_urls = distributor.form_rel_url_lookup_table([repo_a, conflict_repo_a]) 
        except Exception, e:
            caught = True
        self.assertTrue(caught)


    def test_basic_repo_publish_rel_path_conflict(self):
        repo = mock.Mock(spec=Repository)
        repo.working_dir = self.repo_working_dir
        repo.id = "test_basic_repo_publish_rel_path_conflict"
        num_units = 10
        relative_url = "rel_a/rel_b/rel_a/"
        config = distributor_mocks.get_basic_config(https_publish_dir=self.publish_dir, 
                relative_url=relative_url, http=False, https=True)

        url_a = relative_url
        config_a = PluginCallConfiguration({"relative_url":url_a}, {})
        repo_a = RelatedRepository("repo_a_id", [config_a])

        # Simple check of direct conflict of a duplicate
        related_repos = [repo_a]
        distributor = YumDistributor()
        status, msg = distributor.validate_config(repo, config, related_repos)
        self.assertFalse(status)
        expected_msg = "Relative url '%s' conflicts with existing relative_url of '%s' from repo '%s'" % (relative_url, url_a, repo_a.id)
        self.assertEqual(expected_msg, msg)

        # Check conflict with a subdir
        url_b = "rel_a/rel_b/"
        config_b = PluginCallConfiguration({"relative_url":url_b}, {})
        repo_b = RelatedRepository("repo_b_id", [config_b])
        related_repos = [repo_b]
        distributor = YumDistributor()
        status, msg = distributor.validate_config(repo, config, related_repos)
        self.assertFalse(status)
        expected_msg = "Relative url '%s' conflicts with existing relative_url of '%s' from repo '%s'" % (relative_url, url_b, repo_b.id)
        self.assertEqual(expected_msg, msg)

        # Check no conflict with a pieces of a common subdir
        url_c = "rel_a/rel_b/rel_c"
        config_c = PluginCallConfiguration({"relative_url":url_c}, {})
        repo_c = RelatedRepository("repo_c_id", [config_c])

        url_d = "rel_a/rel_b/rel_d"
        config_d = PluginCallConfiguration({"relative_url":url_d}, {})
        repo_d = RelatedRepository("repo_d_id", [config_d])

        url_e = "rel_a/rel_b/rel_e/rel_e"
        config_e = PluginCallConfiguration({"relative_url":url_e}, {})
        repo_e = RelatedRepository("repo_e_id", [config_e])

        # Add a repo with no relative_url
        config_f = PluginCallConfiguration({"relative_url":None}, {})
        repo_f = RelatedRepository("repo_f_id", [config_f])

        related_repos = [repo_c, repo_d, repo_e, repo_f]
        distributor = YumDistributor()
        status, msg = distributor.validate_config(repo, config, related_repos)
        self.assertTrue(status)
        self.assertEqual(msg, None)

        # Test with 2 repos and no relative_url
        config_h = PluginCallConfiguration({}, {})
        repo_h = RelatedRepository("repo_h_id", [config_h])

        config_i = PluginCallConfiguration({}, {})
        repo_i = RelatedRepository("repo_i_id", [config_i])

        status, msg = distributor.validate_config(repo_i, config, [repo_h])
        self.assertTrue(status)
        self.assertEqual(msg, None)

        # TODO:  Test, repo_1 has no rel url, so repo_1_id is used
        # Then 2nd repo is configured with rel_url of repo_1_id
        #  should result in a conflict



        # Ensure this test can handle a large number of repos
        test_repos = []
        for index in range(0,10000):
            test_url = "rel_a/rel_b/rel_e/repo_%s" % (index)
            test_config = PluginCallConfiguration({"relative_url":test_url}, {})
            r = RelatedRepository("repo_%s_id" % (index), [test_config])
            test_repos.append(r)
        related_repos = test_repos
        distributor = YumDistributor()
        status, msg = distributor.validate_config(repo, config, related_repos)
        self.assertTrue(status)
        self.assertEqual(msg, None)