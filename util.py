import os
import time
import urllib

import flask

class Forwarder(object):
    def __init__(self, sdb, surl, path=None):
        self.sdb = sdb
        self.surl = surl
        self.path = path

        self.hit_code = self.record_hit()

        # override of surl.get_long_url()
        self.url = None

    @classmethod
    def args2qs(cls, args):
        '''converts the args dict into a normal query string.

        Note: might not be the same order as originally specified

        '''
        if not args:
            return None
        r = ''
        for key, vals in args.iterlists():
            for val in vals:
                r += '&%s=%s' % (urllib.quote_plus(key), urllib.quote_plus(val))
        return '?' + r[1:]


    @classmethod
    def _thumbify(cls, url, tiny=False):
        '''Given a URL, modifies the file portion to be thumb.jpg

        '''
        parts = os.path.split(url)

        original_path = parts[0]
        original_filename = parts[1]

        extension = os.path.splitext(original_filename)[1]
        if tiny:
            thumb_path = os.path.join(original_path, 'tiny%s' % extension)
        else:
            thumb_path = os.path.join(original_path, 'thumb%s' % extension)

        # only return a relative URL to thumbnail if one actually exists :-)
        if os.path.exists(thumb_path):
            return thumb_path
        return url

    @classmethod
    def _friendly_to_seconds(cls, t):
        '''Converts a friendly "5m30s" style time into just an integer number of
        seconds.

        '''
        mins = 0
        secs = 0

        m = t.find('m')
        if m != -1:
            mins = int(t[:m])

        s = t.find('s')
        if s != -1:
            secs = int(t[m+1:s])

        return mins * 60 + secs

    def _is_youtube(self):
        url = self.surl.get_long_url()
        if url.find('www.youtube.com') == -1:
            return False
        return True

    def _get_youtube_url(self):
        url = self.surl.get_long_url()
        # split 'http://www.youtube.com/v=VIDEOID#tag' -> 'v=VIDEOID#tag'
        query = urllib.splitquery(os.path.split(url)[1])[1]
        # split 'v=VIDEOID#tag' -> 'VIDEOID#tag'
        value = urllib.splitvalue(query)[1]
        # split 'VIDEOID#tag' -> ('VIDEOID', 'tag')
        vid, tag = urllib.splittag(value)

        if tag:
            # split 't=5m2s' -> ('t', '5m2s')
            tag = urllib.splitvalue(tag)[1]
            # convert '5m2s' -> int(302)
            time_offset = Forwarder._friendly_to_seconds(tag)
        else:
            time_offset = 0

        if time_offset > 0:
            return 'http://www.youtube.com/v/%s?start=%s' % (vid, time_offset)
        else:
            return 'http://www.youtube.com/v/%s' % (vid)

    def _display_redirect(self):
        if self.path:
            dest_url = "%s/%s" % (self.surl.get_long_url(), self.path)
        else:
            dest_url = self.surl.get_long_url()
        return flask.make_response("Moved", 302, {"Location": dest_url})

    def _display_local_image(self):
        thumb_url = Forwarder._thumbify(self.surl.get_long_url())
        data = {
            "img_filename": self.surl.get_info().get("title"),
            "img_thumb_url": urllib.quote(thumb_url),
            "img_url": self.surl.get_long_url(),
            "hit_code": self.hit_code,
            "file_size": 0,
            "media_type": None,
        }
        return flask.render_template("media.html", data=data)

    def _display_binary(self):
        length = self.surl.get_info().get("length")
        if not length:
            length = 0
        data = {
            "img_filename": self.surl.get_info().get("title"),
            "img_url": self.surl.get_long_url(),
            "hit_code": self.hit_code,
            "file_size": length,
            "media_type": 'BINARY',
        }
        return flask.render_template("media.html", data=data)

    def _display_hosted_image(self):
        raise NotImplemented()

    def _display_audio(self):
        raise NotImplemented()

    def _display_youtube(self):
        if not self.url:
            raise ValueError('url must be set')
        print 'URL = "%s"' % (self.url)
        data = {
            "img_filename": self.surl.get_info().get("title"),
            "img_url": self.url,
            "original_url": self.surl.get_long_url(),
            "hit_code": self.hit_code,
            "media_type": 'YOUTUBE',
        }
        return flask.render_template("media.html", data=data)

    def _display_text(self):
        lang = ""
        if "lang" in self.surl.get_info() and self.surl.get_info()["lang"]:
            lang = " data-language=\"%s\"" % self.surl.get_info()["lang"]
        if "lang" in flask.request.args:
            lang = " data-language=\"%s\"" % flask.request.args["lang"]
        with open(self.surl.get_long_url(), "r") as f:
            data = {
                "text": f.read(),
                "lang": lang,
                "hit_code": self.hit_code,
            }
            return flask.render_template("text.html", data=data)

    def _get_display_function(self):
        '''Tests what type of display page is required and returns a display
        function.

        '''
        if self.surl.is_img():
            template = 'IMG'
            if self.surl.get_mime_type().find('image') == -1:
                return self._display_binary
            return self._display_local_image

        if self.surl.is_redir():
            if self._is_youtube():
                self.url = self._get_youtube_url()
                return self._display_youtube
            return self._display_redirect

        if self.surl.is_text():
            return self._display_text

        return None

    def handle_request(self):
        '''Either forwards with a 302 or displays a media page. The behaviour
        is definied by the type of the shortcode requested.

        Returns: flask response object.

        '''
        display_fun = self._get_display_function()
        if display_fun:
            return display_fun()
        else:
            return flask.make_response("invalid type", 500)

    def record_hit(self):
        # Update stats
        remote = flask.request.remote_addr
        referrer = "direct"
        if "referer" in flask.request.headers:
            referrer = flask.request.headers["referer"]
        hit_data = {
            "remote_addr": flask.request.remote_addr,
            "referrer": referrer,
            "time": time.time(),
            "agent": flask.request.headers.get("user-agent"),
            "method": flask.request.method,
            "qs": Forwarder.args2qs(flask.request.args),
            "path": self.path,
        }
        hit_id = self.sdb.record_hit(self.surl.get_short_code(), hit_data)
        self.hit_code = str(hit_id)
