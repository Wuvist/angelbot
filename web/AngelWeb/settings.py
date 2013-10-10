# Django settings for AngelWeb project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('Wuvist', 'wuvist@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

CACHE_BACKEND = 'memcached://192.168.0.186:11211'
CACHE_TIME = 65

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*pjvh9#lm#$!-c2=eugwhoas9z_kqhazyn!zz=(*3&^r$bj+fk'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'AngelWeb.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "template"
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'AngelWeb.servers',
    'AngelWeb.cmdb',
)

BOT_URL = 'http://localhost:8080/foo?'
RRD_PATH = '/Users/Wuvist/source/angelbot/rrds/'
LOGIN_REDIRECT_URL = '/'
LOGPATH = '/home/user/backuplog/'
SMS_API = ''
CALL_API = ''
RING_PHONE_NUMBER = ''
RING_IP = ''
RING_PORT = ''
RING_USERNAME = ''
RING_PASSWORD = ''
RING_PATH = ''
IDC_API = ''

#please use 1~24
DEPLOYMENT_CONSUMPTION_START = 3
DEPLOYMENT_CONSUMPTION_END = 6

SERVER_PERFMON_CATEGORY_TITLE = ''

#ping server
ERROR_MIN=100
ERROR_AVG=100
ERROR_MAX=100
ERROR_LOSS=1
EXCLUDE_IPS=[]

#angel detector
DETECTOR_CREATE_PROJECT_ID=1
DETECTOR_CREATE_DASHBOARD_ID=10

#cmdb show widget in dashboard
CMDB_SHOW_WIDGET_DASHBOARD_ID=[]

#DB INFO
DB_RECEIVER="xx@xx.com;zz@zz.com"
DB_ERROR_TIME=30
DB_MYSQL_INFO_LOG=""
DB_MYSQL_DETAIL_LOG=""
DB_SQLSERVER_INFO_LOG=""
DB_SQLSERVER_DETAIL_LOG=""
DB_REMOTE_BACKUP=""

#diff network devices config
TICKET_API=""
SVN_NETWORK_CONFIG=""
SVN_USERNAME=""
SVN_PASSWORD=""
SVN_DIFF_NUMBER=10
