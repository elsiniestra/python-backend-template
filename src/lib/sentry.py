import sentry_sdk


def init_sentry_sdk(dsn: str, traces_sample_rate: float) -> None:
    sentry_sdk.init(
        dsn=dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=traces_sample_rate,
    )
