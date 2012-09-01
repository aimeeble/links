#!/usr/bin/python

import os

import pymongo

from linklib.util import UploadedFile


class ConvertBase(object):
    def __init__(self):
        self.con = pymongo.Connection('localhost')
        self.db = pymongo.database.Database(self.con, 'links')

    def convert(self):
        raise RuntimeError('must override convert')


class ConvertSaveFileFormat(ConvertBase):
    '''Converts from the static/IP/GUID filename convention to the
    static/content_hash/file.dat with symlink convention.

    '''
    def __init__(self):
        super(ConvertSaveFileFormat, self).__init__()
        self.files_to_delete = []

    def convert(self):
        cur = self.db.urls.find({"link_type": 2, "info.title": {"$exists": 1}})
        for row in cur:

            if not os.path.exists(row["long_url"]):
                continue

            filename = os.path.basename(row["info"]["title"])

            print "%s: %s -> %s" % (row["short_code"], row["long_url"], filename)

            with open(row["long_url"], "r") as fh:
                uf = UploadedFile(
                        None,
                        stream=fh,
                        mimetype=row["mime_type"],
                        filename=filename)
                uf._update_filenames()
                if uf.get_filename() == row["long_url"]:
                    print "\tskipping new format"
                    continue
                uf.save()

                row["long_url"] = uf.get_filename()
                self.db.urls.update({"short_code": row["short_code"]}, row)


class CreateThumbnails(ConvertBase):
    '''Creates thumbnails for any files which are missing it.

    '''
    def __init__(self):
        super(CreateThumbnails, self).__init__()

    def convert(self):
        cur = self.db.urls.find({'link_type': 2})
        for row in cur:

            if not os.path.exists(row['long_url']):
                continue

            filename = os.path.basename(row["info"]["title"])

            print '%s: thumbnailing %s' % (row['short_code'], filename)

            with open(row["long_url"], "r") as fh:
                uf = UploadedFile(
                        None,
                        stream=fh,
                        mimetype=row["mime_type"],
                        filename=filename)
                uf._update_filenames()

                if os.path.exists(uf.thumb_filename):
                    print '\tskipping existing thumb'
                    continue
                uf._create_thumbnail()


if __name__ == '__main__':
    c = ConvertSaveFileFormat()
    c.convert()
    c = CreateThumbnails()
    c.convert()
