#!/usr/bin/env python
# encoding: utf-8
"""
hosts.py

Created by Wuvist on 2010-06-27.
Copyright (c) 2010 . All rights reserved.
"""

server_types = {"win": 1, "linux": 2}

logins = {
    "mac" : {"host": "127.0.0.1", "type": "linux", "username": r"Wuvist", "password" : ""},
    "moserver" : {"host": "192.168.1.12", "type": "linux", "username": "mozat", "password" : ""},
    "moserverwin" : {"host": "192.168.1.13", "type": "windows", "username": "administrator", "password" : ""}
 }