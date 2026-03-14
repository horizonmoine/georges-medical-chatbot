from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def get_limiter(app):
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[app.config.get('RATELIMIT_DEFAULT', '100 per hour')],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://'),
        strategy="fixed-window"
    )
    return limiter
