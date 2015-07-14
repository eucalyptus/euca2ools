# Copyright 2013-2015 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import multiprocessing
import os.path
import tarfile

from requestbuilder import Arg
from requestbuilder.mixins import FileTransferProgressBarMixin

from euca2ools.bundle.pipes.core import create_bundle_pipeline
from euca2ools.bundle.pipes.fittings import (create_bundle_part_deleter,
                                             create_bundle_part_writer,
                                             create_mpconn_aggregator)
import euca2ools.bundle.manifest
import euca2ools.bundle.util
from euca2ools.commands.bundle.mixins import (BundleCreatingMixin,
                                              BundleUploadingMixin)
from euca2ools.commands.empyrean import EmpyreanRequest
from euca2ools.commands.s3 import S3Request
from euca2ools.util import mkdtemp_for_large_files


class BundleAndUploadImage(S3Request, BundleCreatingMixin,
                           BundleUploadingMixin,
                           FileTransferProgressBarMixin):
    DESCRIPTION = 'Prepare and upload an image for use in the cloud'
    ARGS = [Arg('--preserve-bundle', action='store_true',
                help='do not delete the bundle as it is being uploaded'),
            Arg('--max-pending-parts', type=int, default=2,
                help='''pause the bundling process when more than this number
                of parts are waiting to be uploaded (default: 2)'''),
            Arg('--iam-url', route_to=None,
                help='identity service endpoint URL'),
            Arg('--iam-service', route_to=None, help=argparse.SUPPRESS),
            Arg('--iam-auth', route_to=None, help=argparse.SUPPRESS)]

    # noinspection PyExceptionInherit
    def configure(self):
        S3Request.configure(self)

        # Set up access to empyrean in case we need auto cert fetching.
        try:
            self.args['empyrean_service'] = \
                EmpyreanRequest.SERVICE_CLASS.from_other(
                    self.service, url=self.args.get('empyrean_url'))
            self.args['empyrean_auth'] = EmpyreanRequest.AUTH_CLASS.from_other(
                self.auth)
        except:
            self.log.debug('empyrean setup failed; auto cert fetching '
                           'will be unavailable', exc_info=True)

        self.configure_bundle_upload_auth()
        self.configure_bundle_creds()
        self.configure_bundle_properties()
        self.configure_bundle_output()
        self.generate_encryption_keys()

    def main(self):
        if self.args.get('destination'):
            path_prefix = os.path.join(self.args['destination'],
                                       self.args['prefix'])
            if not os.path.exists(self.args['destination']):
                os.mkdir(self.args['destination'])
        else:
            tempdir = mkdtemp_for_large_files(prefix='bundle-')
            path_prefix = os.path.join(tempdir, self.args['prefix'])
        self.log.debug('bundle path prefix: %s', path_prefix)

        key_prefix = self.get_bundle_key_prefix()
        self.ensure_dest_bucket_exists()

        # First create the bundle and upload it to the server
        digest, partinfo = self.create_and_upload_bundle(path_prefix,
                                                         key_prefix)

        # All done; now build the manifest, write it to disk, and upload it.
        manifest = self.build_manifest(digest, partinfo)
        manifest_filename = '{0}.manifest.xml'.format(path_prefix)
        with open(manifest_filename, 'w') as manifest_file:
            manifest.dump_to_file(manifest_file, self.args['privatekey'],
                                  self.args['cert'], self.args['ec2cert'])
        manifest_dest = key_prefix + os.path.basename(manifest_filename)
        self.upload_bundle_file(manifest_filename, manifest_dest,
                                show_progress=self.args.get('show_progress'))
        if not self.args.get('preserve_bundle', False):
            os.remove(manifest_filename)

        # Then we just inform the caller of all the files we wrote.
        # Manifests are returned in a tuple for future expansion, where we
        # bundle for more than one region at a time.
        return {'parts': tuple({'filename': part.filename,
                                'key': (key_prefix +
                                        os.path.basename(part.filename))}
                               for part in manifest.image_parts),
                'manifests': ({'filename': manifest_filename,
                               'key': manifest_dest},)}

    def print_result(self, result):
        if self.debug:
            for part in result['parts']:
                print 'Uploaded', part['key']
        if result['manifests'][0]['key'] is not None:
            print 'Uploaded', result['manifests'][0]['key']

    def create_and_upload_bundle(self, path_prefix, key_prefix):
        part_write_sem = multiprocessing.Semaphore(
            max(1, self.args['max_pending_parts']))

        # Fill out all the relevant info needed for a tarball
        tarinfo = tarfile.TarInfo(self.args['prefix'])
        tarinfo.size = self.args['image_size']

        # disk --(bytes)-> bundler
        partwriter_in_r, partwriter_in_w = \
            euca2ools.bundle.util.open_pipe_fileobjs()
        digest_result_mpconn = create_bundle_pipeline(
            self.args['image'], partwriter_in_w, self.args['enc_key'],
            self.args['enc_iv'], tarinfo, debug=self.debug)
        partwriter_in_w.close()

        # bundler --(bytes)-> part writer
        bundle_partinfo_mpconn = create_bundle_part_writer(
            partwriter_in_r, path_prefix, self.args['part_size'],
            part_write_sem=part_write_sem, debug=self.debug)
        partwriter_in_r.close()

        # part writer --(part info)-> part uploader
        # This must be driven on the main thread since it has a progress bar,
        # so for now we'll just set up its output pipe so we can attach it to
        # the remainder of the pipeline.
        uploaded_partinfo_mpconn_r, uploaded_partinfo_mpconn_w = \
            multiprocessing.Pipe(duplex=False)

        # part uploader --(part info)-> part deleter
        if not self.args.get('preserve_bundle', False):
            deleted_partinfo_mpconn_r, deleted_partinfo_mpconn_w = \
                multiprocessing.Pipe(duplex=False)
            create_bundle_part_deleter(uploaded_partinfo_mpconn_r,
                                       out_mpconn=deleted_partinfo_mpconn_w)
            uploaded_partinfo_mpconn_r.close()
            deleted_partinfo_mpconn_w.close()
        else:
            # Bypass this stage
            deleted_partinfo_mpconn_r = uploaded_partinfo_mpconn_r

        # part deleter --(part info)-> part info aggregator
        # (needed for building the manifest)
        bundle_partinfo_aggregate_mpconn = create_mpconn_aggregator(
            deleted_partinfo_mpconn_r, debug=self.debug)
        deleted_partinfo_mpconn_r.close()

        # Now drive the pipeline by uploading parts.
        try:
            self.upload_bundle_parts(
                bundle_partinfo_mpconn, key_prefix,
                partinfo_out_mpconn=uploaded_partinfo_mpconn_w,
                part_write_sem=part_write_sem,
                show_progress=self.args.get('show_progress'))
        finally:
            # Make sure the writer gets a chance to exit
            part_write_sem.release()

        # All done; now grab info about the bundle we just created
        try:
            digest = digest_result_mpconn.recv()
            partinfo = bundle_partinfo_aggregate_mpconn.recv()
        except EOFError:
            self.log.debug('EOFError from reading bundle info', exc_info=True)
            raise RuntimeError(
                'corrupt bundle: bundle process was interrupted')
        finally:
            digest_result_mpconn.close()
            bundle_partinfo_aggregate_mpconn.close()
        self.log.info('%i bundle parts uploaded to %s', len(partinfo),
                      self.args['bucket'])
        self.log.debug('bundle digest: %s', digest)
        return digest, partinfo
