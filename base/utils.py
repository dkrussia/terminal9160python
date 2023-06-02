import functools
import logging

logger = logging.getLogger('catch_exception')
logger.setLevel(logging.INFO)


def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception as e:
                import traceback
                logger.error(str(e), exc_info=True)

        return wrapper

    return catch_exceptions_decorator
