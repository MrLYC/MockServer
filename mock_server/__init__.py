# coding: utf-8

import importlib
import argparse

from tornado import ioloop


class SETTINGS(object):
    ADDRESS = "0.0.0.0"
    PORT = 8080


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
    arguments = parser.parse_args()
    SETTINGS.ADDRESS = arguments.address
    SETTINGS.PORT = arguments.port

    module = importlib.import_module(
        "mock_server.servers.%s" % arguments.server,
    )
    module.init()

    instance = ioloop.IOLoop.instance()
    instance.start()
