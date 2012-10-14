import time


class ShortURL(object):
    REDIR = 1
    IMG = 2
    TEXT = 3

    def __init__(self, short_code, short_url, long_url=None, info={}):
        self.short_code = short_code
        self.short_url = short_url
        self.long_url = long_url
        self.info = info
        self.latest_short = time.time()

        self.link_type = ShortURL.REDIR
        self.mime_type = None
        self.qs = None
        self.social = {}

    def get_link_type(self):
        return self.link_type

    def get_link_type_text(self):
        LINK_TYPES = {}
        LINK_TYPES[1] = "REDIR"
        LINK_TYPES[2] = "IMG"
        LINK_TYPES[3] = "TEXT"
        return LINK_TYPES[self.link_type]

    def is_redir(self):
        return self.link_type == ShortURL.REDIR

    def is_img(self):
        return self.link_type == ShortURL.IMG

    def is_text(self):
        return self.link_type == ShortURL.TEXT

    def get_mime_type(self):
        return self.mime_type

    def get_short_code(self):
        return self.short_code

    def get_short_url(self):
        return self.short_url

    def get_long_url(self):
        return self.long_url

    def get_info(self):
        return self.info

    def get_social(self):
        return self.social

    def get_title(self):
        title = self.info.get('title')
        if not title:
            title = 'Unknown'
        return title

    def get_description(self):
        meta = self.info.get('meta')
        if not meta:
            return 'None'
        desc = meta.get('description')
        if not desc:
            return 'None'
        return desc

    def get_content_length(self):
        length = self.info.get('length', '0')
        return int(length)

    def get_social(self):
        return {}

    def __str__(self):
        return "(URL %s = %s)" % (self.short_code, self.long_url)

    def serialize(self, update_time=True):
        new_time = self.latest_short
        if update_time:
            new_time = time.time()

        return {
            "short_code": self.short_code,
            "long_url": self.long_url,
            "link_type": self.link_type,
            "mime_type": self.mime_type,
            "info": self.info,
            "latest_short": new_time,
            "social": self.social,
        }

    def deserialize(self, data):
        self.short_code = data.get("short_code")
        self.long_url = data.get("long_url")
        self.link_type = data.get("link_type")
        self.mime_type = data.get("mime_type")
        self.info = data.get("info")
        self.latest_short = data.get("latest_short")
        self.social = data.get("social", {})
