#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Created on Thu Dec 09 2021 09:56:30 by codeskyblue
"""

import json
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlparse

from wda.usbmux.exceptions import HTTPError, MuxConnectError, MuxError
from wda.usbmux.pyusbmux import select_device


def http_create(url: str) -> HTTPConnection:
    u = urlparse(url)
    if u.scheme == "http+usbmux":
        udid, device_wda_port = u.netloc.split(":")
        device = select_device(udid)
        return device.make_http_connection(int(device_wda_port))
    elif u.scheme == "http":
        return HTTPConnection(u.netloc)
    elif u.scheme == "https":
        return HTTPSConnection(u.netloc)
    else:
        raise ValueError(f"unknown scheme: {u.scheme}")


class HTTPResponseWrapper:
    def __init__(self, content: bytes, status_code: int):
        self.content = content
        self.status_code = status_code
    
    def json(self):
        return json.loads(self.content)

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")

    def getcode(self) -> int:
        return self.status_code
    

def fetch(url: str, method="GET", data=None, timeout=None) -> HTTPResponseWrapper:
    """
    thread safe http request

    Raises:
        HTTPError
    """
    try:
        method = method.upper()
        conn = http_create(url)
        conn.timeout = timeout
        u = urlparse(url)
        urlpath = url[len(u.scheme) + len(u.netloc) + 3:]

        if not data:
            conn.request(method, urlpath, headers={"Connection": "close", "User-Agent": "python-requests/2.31.0"})
        else:
            conn.request(method, urlpath, json.dumps(data), headers={"Content-Type": "application/json", "Connection": "close", "User-Agent": "python-requests/2.31.0"})
        response = conn.getresponse()
        content = bytearray()
        while chunk := response.read(4096):
            content.extend(chunk)
        resp = HTTPResponseWrapper(content, response.status)
        return resp
    except Exception as e:
        raise HTTPError(e)
