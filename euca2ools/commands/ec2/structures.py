# Copyright 2014 Eucalyptus Systems, Inc.
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

import logging

import lxml.etree
import lxml.objectify

import euca2ools


class ImportManifest(object):
    def __init__(self, loglevel=None):
        self.log = logging.getLogger(self.__class__.__name__)
        if loglevel is not None:
            self.log.level = loglevel
        self.file_format = None
        self.self_destruct_url = None
        self.image_size = None
        self.volume_size = None
        self.image_parts = []

    @classmethod
    def read_from_file(cls, manifest_filename):
        with open(manifest_filename) as manifest_fileobj:
            return cls.read_from_fileobj(manifest_fileobj)

    @classmethod
    def read_from_fileobj(cls, manifest_fileobj):
        xml = lxml.objectify.parse(manifest_fileobj).getroot()
        manifest = cls()

        manifest.file_format = xml['file-format'].text
        manifest.self_destruct_url = xml['self-destruct-url'].text
        manifest.image_size = int(xml['import'].size)
        manifest.volume_size = int(xml['import']['volume-size'])
        manifest.image_parts = [None] * int(xml['import']['parts']
                                            .get('count'))
        for part in xml['import']['parts']['part']:
            part_index = int(part.get('index'))
            part_obj = ImportImagePart()
            part_obj.index = part_index
            part_obj.start = int(part['byte-range'].get('start'))
            part_obj.end = int(part['byte-range'].get('end'))
            part_obj.key = part['key'].text
            part_obj.head_url = part['head-url'].text
            part_obj.get_url = part['get-url'].text
            part_obj.delete_url = part['delete-url'].text
            manifest.image_parts[part_index] = part_obj
        assert None not in manifest.image_parts, 'part missing from manifest'
        return manifest

    def dump_to_str(self, pretty_print=False):
        xml = lxml.objectify.Element('manifest')

        # Manifest version
        xml.version = '2010-11-15'

        # File format
        xml['file-format'] = self.file_format

        # Our version
        xml.importer = None
        xml.importer.name = 'euca2ools'
        xml.importer.version = euca2ools.__version__
        xml.importer.release = 0

        # Import and image part info
        xml['self-destruct-url'] = self.self_destruct_url
        xml['import'] = None
        xml['import']['size'] = self.image_size
        xml['import']['volume-size'] = self.volume_size
        xml['import']['parts'] = None
        xml['import']['parts'].set('count', str(len(self.image_parts)))
        for part in self.image_parts:
            xml['import']['parts'].append(part.dump_to_xml())

        # Cleanup
        lxml.objectify.deannotate(xml, xsi_nil=True)
        lxml.etree.cleanup_namespaces(xml)
        self.log.debug('-- manifest content --\n', extra={'append': True})
        pretty_manifest = lxml.etree.tostring(xml, pretty_print=True).strip()
        self.log.debug('%s', pretty_manifest, extra={'append': True})
        self.log.debug('-- end of manifest content --')
        return lxml.etree.tostring(xml, pretty_print=pretty_print,
                                   encoding='UTF-8', standalone=True,
                                   xml_declaration=True).strip()

    def dump_to_fileobj(self, fileobj, pretty_print=False):
        fileobj.write(self.dump_to_str(pretty_print=pretty_print))


class ImportImagePart(object):
    def __init__(self):
        self.index = None
        self.start = None
        self.end = None
        self.key = None
        self.head_url = None
        self.get_url = None
        self.delete_url = None

    def dump_to_xml(self):
        xml = lxml.objectify.Element('part', index=str(self.index))
        xml['byte-range'] = None
        xml['byte-range'].set('start', str(self.start))
        xml['byte-range'].set('end', str(self.end))
        xml['key'] = self.key
        xml['head-url'] = self.head_url
        xml['get-url'] = self.get_url
        xml['delete-url'] = self.delete_url
        return xml
