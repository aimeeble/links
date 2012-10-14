import pygeoip


geo = pygeoip.GeoIP('data/GeoIP.dat')
gic = pygeoip.GeoIP('data/GeoLiteCity.dat')


class Classifier(object):
    def __init__(self, sdb, surl, hit):
        self.sdb = sdb
        self.surl = surl
        self.hit = hit

        self.info = surl.get_info()
        if not self.info:
            self.info = {}

        self.meta = self.info.get("meta")
        self.social = surl.get_social()

    def is_bot(self):
        '''Returns a score on if we think this is a bot.

        Scores range from 0 to 100, with 0 being definitely not, and 100 being
        definitely bot.
        '''
        pass

    def get_country_code(self, default=None):
        '''Returns the two-letter country code for the hit.

        '''
        ip = self.hit["remote_addr"]
        cc = geo.country_code_by_addr(ip)
        if cc:
            return cc
        return default

    def get_region(self, default=None):
        '''Returns a city/region/county/etc for the hit.

        '''
        ip = self.hit["remote_addr"]
        area = gic.record_by_addr(ip)
        if area:
            return area
        return default

    def get_browser_name_and_version(self):
        '''Returns a tuple of ('common browser name', int(version)).

        '''
        pass

    def get_full_agent_string(self):
        pass
