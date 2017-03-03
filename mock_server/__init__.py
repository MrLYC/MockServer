# coding: utf-8

import importlib
import argparse
import logging
import logging.config

from tornado import ioloop

logger = logging.getLogger(__name__)


class SETTINGS(object):
    DEBUG = False
    ADDRESS = "0.0.0.0"
    PORT = 8080

    CACHE_ADDRESS = "127.0.0.1"
    CACHE_PORT = 6379
    CACHE_DB = 0
    CACHE_STRICT_MODE = False


def config_logger(loggers, level="INFO"):
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "long": {
                "format": (
                    r"%(asctime)s %(name)s %(module)s %(process)d "
                    r"%(levelname)-8s %(message)s"
                ),
            },
        },
        "handlers": {
            "console": {
                "level": level,
                "class": "logging.StreamHandler",
                "formatter": "long",
            },
        },
        "loggers": {
            i: {
                "handlers": ["console"],
                "level": level,
            }
            for i in loggers
        }
    })


def start_server():
    parser = argparse.ArgumentParser()
    parser.add_argument("server", help="server name")
    parser.add_argument(
        "-a", "--address", default=SETTINGS.ADDRESS,
        help="server listen address",
    )
    parser.add_argument(
        "-p", "--port", default=SETTINGS.PORT,
        help="server listen port",
    )
    parser.add_argument(
        "-A", "--databse_address", default=SETTINGS.CACHE_ADDRESS,
        help="cache databse address",
    )
    parser.add_argument(
        "-P", "--databse_port", default=SETTINGS.CACHE_PORT,
        help="cache databse port",
    )
    parser.add_argument(
        "-d", "--database", default=SETTINGS.CACHE_DB,
        help="database name",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="debug mode",
    )
    arguments = parser.parse_args()
    SETTINGS.ADDRESS = arguments.address
    SETTINGS.PORT = arguments.port
    SETTINGS.DEBUG = arguments.debug
    SETTINGS.CACHE_ADDRESS = arguments.databse_address
    SETTINGS.CACHE_PORT = arguments.databse_port
    SETTINGS.CACHE_DB = arguments.database

    config_logger(
        ["tornado", "mock_server"],
        "DEBUG" if SETTINGS.DEBUG else "INFO"
    )

    module = importlib.import_module(
        "mock_server.servers.%s" % arguments.server,
    )
    module.init()

    instance = ioloop.IOLoop.instance()
    try:
        logger.info("start server on %s:%s", SETTINGS.ADDRESS, SETTINGS.PORT)
        instance.start()
    except KeyboardInterrupt:
        logger.info("bye")
