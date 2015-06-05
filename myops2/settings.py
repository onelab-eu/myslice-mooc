import ConfigParser
import os.path

config = ConfigParser.ConfigParser()
try:
    config.read('/etc/myops2.cfg')
except Exception as e:
    print e
    exit(1)


def get(section, key, default = None):
    try :
        value = config.get(section, key)
    except ConfigParser.NoSectionError:
        value = default
    except ConfigParser.NoOptionError:
        value = default
    except ConfigParser.Error:
        value = default

    return value

