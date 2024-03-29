"""Config related settings, follows 12factor.net
"""
import logging
import os
import platform
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    'Setting',
    'expandabspath',
    # global settings
    'tmpdir',
    'vendor',
    'local',
    'output',
    'syslog',
    'tlssyslog',
    'mail',
    'mandrill',
    'log',
    'gpg',
    # global vars
    'CHECKTTY',
    'PLATFORM',
    'RELEASE',
    'ENVIRONMENT',
    # global vars (legacy)
    'WIN',
    'WSL',
    'NIX',
    'WEBAPP',
    'checktty',
    'webapp',
    ]


class Setting(dict):
    """Dict where d['foo'] can also be accessed as d.foo
    but also automatically creates new sub-attributes of
    type Setting. This behavior can be locked to turn off
    later. WARNING: not copy safe

    >>> cfg = Setting()
    >>> cfg.unlock() # locked after config.py load

    >>> cfg.foo.bar = 1
    >>> hasattr(cfg.foo, 'bar')
    True
    >>> cfg.foo.bar
    1
    >>> cfg.lock()
    >>> cfg.foo.bar = 2
    Traceback (most recent call last):
     ...
    ValueError: This Setting object is locked from editing
    >>> cfg.foo.baz = 3
    Traceback (most recent call last):
     ...
    ValueError: This Setting object is locked from editing
    >>> cfg.unlock()
    >>> cfg.foo.baz = 3
    >>> cfg.foo.baz
    3
    """

    _locked = False

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getattr__(self, name):
        """Create sub-setting fields on the fly"""
        if name not in self:
            if self._locked:
                raise ValueError('This Setting object is locked from editing')
            self[name] = Setting()
        return self[name]

    def __setattr__(self, name, val):
        if self._locked:
            raise ValueError('This Setting object is locked from editing')
        if name not in self:
            self[name] = Setting()
        self[name] = val

    @staticmethod
    def lock():
        Setting._locked = True

    @staticmethod
    def unlock():
        Setting._locked = False


# Environment
HERE = os.path.abspath(os.path.dirname(__file__))
CHECKTTY = 'CONFIG_CHECKTTY' in os.environ
PLATFORM = platform.system()
RELEASE = platform.release()
ENVIRONMENT = None
if 'CONFIG_PROD' in os.environ:
    ENVIRONMENT = 'prod'
if 'CONFIG_UAT' in os.environ:
    ENVIRONMENT = 'uat'
if 'CONFIG_QA' in os.environ:
    ENVIRONMENT = 'qa'
if 'CONFIG_DEV' in os.environ:
    ENVIRONMENT = 'dev'
if ENVIRONMENT is None:
    import getpass
    logger.error(f'User "{getpass.getuser()}" missing environment type, set in environment variables')

# Environment (Legacy)
WIN = 'Windows' in PLATFORM
WSL = 'Microsoft' in RELEASE
NIX = 'Linux' in PLATFORM and not WSL
WEBAPP = 'CONFIG_WEBAPP' in os.environ
checktty = CHECKTTY
webapp = WEBAPP


def expandabspath(p: str) -> str:
    """Expand path to absolute path

    >>> import os
    >>> os.environ['SPAM'] = 'eggs'
    >>> assert expandabspath('~/$SPAM') == os.path.expanduser('~/eggs')
    >>> assert expandabspath('/foo') == '/foo'
    """
    a = os.path.abspath
    u = os.path.expanduser
    v = os.path.expandvars

    def r(x):
        try:
            return os.path.relpath(x)
        except ValueError:
            return os.path.abspath(x)

    return a(u(r(v(p))))


# Tmpdir
tmpdir = Setting()
if os.getenv('CONFIG_TMPDIR_DIR'):
    tmpdir.dir = expandabspath(os.getenv('CONFIG_TMPDIR_DIR'))
else:
    tmpdir.dir = tempfile.gettempdir()
Path(tmpdir.dir).mkdir(parents=True, exist_ok=True)

# Vendor Dir
vendor = Setting()
if os.getenv('CONFIG_VENDOR_DIR'):
    vendor.dir = expandabspath(os.getenv('CONFIG_VENDOR_DIR'))
else:
    vendor.dir = tempfile.gettempdir()
Path(vendor.dir).mkdir(parents=True, exist_ok=True)

# Local Dir
local = Setting()
local.dir = Path(expandabspath(r'%APPDATA%')
                 if 'Win' in PLATFORM
                 else expandabspath('~/.local/share/')) / 'libb'
local.dir = local.dir.as_posix()
Path(local.dir).mkdir(parents=True, exist_ok=True)

# Output Dir
output = Setting()
if os.getenv('CONFIG_OUTPUT_DIR'):
    output.dir = expandabspath(os.getenv('CONFIG_OUTPUT_DIR'))
else:
    output.dir = tempfile.gettempdir()
Path(output.dir).mkdir(parents=True, exist_ok=True)

# Syslog
syslog = Setting()
syslog.host = os.getenv('CONFIG_SYSLOG_HOST')
syslog.port = os.getenv('CONFIG_SYSLOG_PORT')

# TLS Syslog
tlssyslog = Setting()
tlssyslog.host = os.getenv('CONFIG_TLSSYSLOG_HOST')
tlssyslog.port = os.getenv('CONFIG_TLSSYSLOG_PORT')
tlssyslog.dir = None
if os.getenv('CONFIG_TLSSYSLOG_DIR'):
    tlssyslog.dir = expandabspath(os.getenv('CONFIG_TLSSYSLOG_DIR'))

# Intermedia Email
mail = Setting()
mail.domain = os.getenv('CONFIG_MAIL_DOMAIN')
mail.server = os.getenv('CONFIG_MAIL_SERVER')
mail.fromemail = os.getenv('CONFIG_MAIL_FROMEMAIL')
mail.toemail = os.getenv('CONFIG_MAIL_TOEMAIL')
mail.adminemail = os.getenv('CONFIG_MAIL_ADMINEMAIL')

# Mandrill API integration
mandrill = Setting()
mandrill.apikey = os.getenv('CONFIG_MANDRILL_APIKEY')
mandrill.smtp = os.getenv('CONFIG_MANDRILL_SMTP','smtp.mandrillapp.com')
mandrill.url = os.getenv('CONFIG_MANDRILL_URL', 'https://mandrillapp.com/api/1.0/')

# Log additional settings (comma separated)
log = Setting()
log.modules.extra = os.getenv('CONFIG_LOG_MODULES_EXTRA', '')
log.modules.ignore = os.getenv('CONFIG_LOG_MODULES_IGNORE', '')

# GnuPG encryption
gpg = Setting()
gpg.dir = os.path.abspath(os.getenv('CONFIG_GPG_DIR') or tmpdir.dir)
gpg.exe = os.path.join(gpg.dir, 'gpg.exe' if 'Win' in PLATFORM else 'gpg')


Setting.lock()


if __name__ == '__main__':
    __import__('doctest').testmod(optionflags=4 | 8 | 32)
    print('tmpdir: '+tmpdir.dir)
    print('vendor: '+vendor.dir)
    print('local:  '+local.dir)
    print('output: '+output.dir)
