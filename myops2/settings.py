from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError, Error
import os


class Config:


    def __init__(self):
        self.system = os.path.abspath("/etc/myops2")
        self.user = os.path.expanduser("~/.myops2")
        self.files = [ self.general + "/settings.ini", self.local + "/settings.ini" ]

        if not os.path.exists(self.general):
            pass

        if not os.path.exists(self.local):
            os.mkdir(self.local)

        self.parser = SafeConfigParser()
        s = self.parser.read(self.files)

        print s
        #print config.sections()

    def get(self, section, key, default = None):
        try :
            value = self.parser.get(section, key)
        except NoSectionError:
            value = default
        except NoOptionError:
            value = default
        except Error:
            value = default

        return value

