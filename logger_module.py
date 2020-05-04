#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: logger_module.py

Created on Mon Sep 23 21:18:37 2019

@author: qjfoidnh
"""

import logging


LOG_FORMAT = "%(asctime)s - %(filename)s -Line: %(lineno)d - %(levelname)s: %(message)s"
logging.basicConfig(filename='downloadsys.log', level=logging.INFO, format=LOG_FORMAT, filemode='a')

logger = logging.getLogger(__name__)