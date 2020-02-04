import logging


def lite_logging(logging_data: dict = None, keys_to_exclude: list = []):
    data = {"message": "liteolog hmrc"}
    for key in logging_data:
        if key not in keys_to_exclude:
            value = logging_data[key]
            if len(value) > 100:
                value = value[0:100]
            data[key] = value
    logging.info(data)


def lite_logging_decorator(func):
    def wrapper(*args, **kwargs):
        lite_logging(
            {
                "function_name": func.__name__,
                "function_qualified_name": func.__qualname__,
                "function_position": "start",
            }
        )
        try:
            func(*args, **kwargs)
            lite_logging(
                {
                    "function_end": func.__name__,
                    "function_qualified_name": func.__qualname__,
                    "function_position": "end",
                }
            )
        except Exception as e:
            lite_logging(
                {
                    "function_end": func.__name__,
                    "function_qualified_name": func.__qualname__,
                    "function_position": "exception thrown",
                    "exception": e,
                }
            )

    return wrapper
