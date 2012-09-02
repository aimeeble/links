import bs4
import errno
import hashlib
import os
from PIL import Image
import urllib2
import uuid


class UploadedFile(object):
    '''Handles saving an uploaded file.

    With this class, the file is hashed, and this value is used to create a
    directory name to store the file in. The file is saved simply as file.dat.
    A symlink is created using the original filename which points at file.dat.

    If an identical file is uploaded later, it'll hash to the same value and a
    new symlink (with a potentially different name) is created for the
    subsequent upload.

    '''
    def __init__(self, req, formfile=None, stream=None, mimetype=None,
                 filename=None):
        self.real_filename = None
        self.link_filename = None

        if formfile:
            reqfile = req.files[formfile]
            self.stream = reqfile.stream
            self.remote_filename = reqfile.filename
            self.mimetype = reqfile.mimetype
        elif stream:
            self.stream = stream
            self.remote_filename = filename if filename else 'unknown'
            self.mimetype = mimetype if mimetype else 'text/plain'
        else:
            raise ValueError('invalid params')

    @classmethod
    def _create_paths(cls, fullpath):
        '''Creates all the directories, handling existing ones.

        '''
        try:
            os.makedirs(os.path.dirname(fullpath))
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                pass
            else:
                raise

    def _get_hash(self):
        '''Digests the file contents, then resets the file stream

        '''
        sha1 = hashlib.sha1()
        data = self.stream.read()
        sha1.update(data)

        # be sure to reset the stream so we can save it later.
        self.stream.seek(0)

        return sha1.hexdigest()

    def _update_filenames(self):
        ''' Recalculates the filenames to save and link to.

        '''
        dirname = self._get_hash()
        subpath = os.path.join('static', dirname)
        self.real_filename = os.path.join(subpath, 'file.dat')
        self.link_filename = os.path.join(subpath, self.remote_filename)

        extension = os.path.splitext(self.link_filename)[1]
        path = os.path.dirname(self.link_filename)
        self.thumb_filename = os.path.join(path, 'thumb%s' % extension)

    def _create_thumbnail(self):
        '''Creates a thumbnail.

        If the mimetype is that of an image, creates a thumbnail called
        thumb.jpg. Also avoids making thumbs for animated gifs, or small
        images.

        '''
        if self.mimetype.find('image') == -1:
            return

        img = Image.open(self.real_filename)
        if img.size[0] < 640 or img.size[1] < 480:
            return

        # GIFs might be animated and we don't want a static thumb for those.
        if img.format == 'GIF':
            try:
                img.seek(img.tell() + 1)
            except EOFError:
                # seek fails => single-frame => thumb okay!
                img.seek(0)
                pass
            else:
                # successful seek => animated => no thumb.
                return

        img.thumbnail((640, 480), Image.ANTIALIAS)
        img.save(self.thumb_filename)

    def get_mimetype(self):
        return self.mimetype

    def get_remote_filename(self):
        return self.remote_filename

    def get_real_filename(self):
        return self.real_filename

    def get_filename(self):
        return self.link_filename

    def save(self):
        if not self.real_filename or not self.link_filename:
            self._update_filenames()

        # Save the actual data
        UploadedFile._create_paths(self.real_filename)

        print 'saving to %s' % self.real_filename
        with open(self.real_filename, 'w') as real_fh:
            real_fh.write(self.stream.read())

        # Symlink it up
        print 'linking to %s' % self.link_filename
        if os.path.islink(self.link_filename):
            print 'unlinking %s' % self.link_filename
            os.unlink(self.link_filename)
        real_basename = os.path.basename(self.real_filename)
        os.symlink(real_basename, self.link_filename)

        # Thumbnail!
        self._create_thumbnail()


class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"


def get_page_info(url):
    info = {}

    # Start by getting head.  We only do fancy stuff when it's the right type.
    have_body = False
    try:
        res = urllib2.urlopen(HeadRequest(url))
    except urllib2.HTTPError, e:
        if e.code == 405:
            # Requesting head is invalid.  Just get it all then...
            have_body = True
            res = urllib2.urlopen(url)
        else:
            # On any other HTTP error, just abort
            print "Got HTTPError.code = %d on HEAD." % (e.code)
            raise e

    if res.headers.gettype() != "text/html":
        info["mimetype"] = res.headers.gettype()
        length = res.headers.get("Content-length")
        if length:
            info["length"] = length
        return info

    # This makes the assumption that HTML files are small, so we fetch it all.
    if not have_body:
        res = urllib2.urlopen(url)
    html = res.read()
    soup = bs4.BeautifulSoup(html, "lxml")

    if soup.title:
        info["title"] = soup.title.get_text(strip=True)

    info["meta"] = {}
    for meta in soup.find_all("meta"):
        key = meta.get("name")
        val = meta.get("content")
        if key and val:
            key = key.replace(".", "_")
            info["meta"][key] = val

    info["mimetype"] = res.headers.gettype()
    length = res.headers.get("Content-length")
    if length:
        info["length"] = length

    return info
