import sys
import configparser
import traceback
import logging
import logging.config
from cadre.controllers import Controller, load_controllers
from cadre.framework import Framework, DumpRoutes
from cadre.framework import framework_from_config, validate

logger = logging.getLogger(__name__)


class NotReady:
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic

    def __getattr__(self, attribute):
        raise AttributeError("Cannot access %r: %s" %
                             (attribute, self.diagnostic))

    def __getitem__(self, item):
        raise AttributeError("Cannot find %r: %s" % (item, self.diagnostic))

    def __bool__(self):
        return False


request = cookies = NotReady("Cadre is not setup yet.")


class Cadre():

    config = {}

    def __init__(self, config_filename):
        self.application = getattr(self, 'application',
                                   self.__class__.__name__.lower())
        logger.debug("Starting cadre application '%s'." % self.application)
        self.config_filename = config_filename
        if self.config_filename:
            self.config.update(self.read_config(self.config_filename))
            try:
                logging.config.fileConfig(self.config_filename)
            except Exception:
                print("You'd better configure logging in '%s':\n%s" %
                      (self.config_filename, traceback.format_exc()))
        setattr(sys.modules['cadre'], 'config', self.config)

    def read_config(self, filename):
        config = {self.__class__.__name__.lower(): {}}
        p = configparser.ConfigParser()
        p.read(filename)
        for n, s in p.items():
            if s:
                config[n] = dict(s)
        return config

    def serve(self):
        assert self.config, "Missing config."
        f = framework_from_config(self.__class__.__name__.lower(), self.config)
        f.setup_application(self)
        load_controllers(f, self.application)
        f.serve()

    def dump_routes(self):
        assert self.config, "Missing config."
        f = DumpRoutes(self.__class__.__name__.lower(), self.config)
        load_controllers(f, self.application)
        print(f)

    def get_wsgi_app(self):
        config = self.read_config(self.config_filename)
        assert config, "Missing config."
        f = framework_from_config(self.__class__.__name__.lower(), config)
        f.setup_application(self)
        load_controllers(f, self.application)
        return f.get_wsgi_app()


__all__ = ['Cadre', 'Framework', 'Controller', 'validate']
