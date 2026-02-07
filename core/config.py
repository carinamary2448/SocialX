# COMPRESS APP --------------------------------------------------------------------------------------------------
COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']
COMPRESS_LEVEL = 6
COMPRESS_MIN_SIZE = 500
# ---------------------------------------------------------------------------------------------------------------
# LOCAL CONFIGS--------------------------------------------------------------------------------------------------
DATABASE = "./database.db"
url = 'https://github.com/UndeadSec/SocialFish'
red = 'https://github.com/UndeadSec/SocialFish'
sta = 'x'
# SECURITY WARNING: Set a strong secret key in production. Use environment variable or secure config file.
# For development, generating a random key. In production, use: os.environ.get('SECRET_KEY', 'your-secure-key')
import os
import secrets
APP_SECRET_KEY = os.environ.get('SOCIALFISH_SECRET_KEY') or secrets.token_urlsafe(32)
# ---------------------------------------------------------------------------------------------------------------