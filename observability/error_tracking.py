import os
import sentry_sdk
from dotenv import load_dotenv

load_dotenv()


def init_sentry():
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        print("⚠️  SENTRY_DSN not set — error tracking disabled")
        return

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    print("✅ Sentry initialized")


def capture_exception(error: Exception, context: dict = None):
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)