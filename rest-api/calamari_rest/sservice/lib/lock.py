#!/usr/bin/env python
#coding=utf-8


from threading import Lock as threading_Lock


ss_lock_factory = threading_Lock


def set_lock_factory(lock_factory):
    global ss_lock_factory
    ss_lock_factory = lock_factory


def set_lock_factory_from_name(module_path_name, factory_func_name):
    global ss_lock_factory
    ss_lock_factory = getattr(__import__(module_path_name, fromlist=[factory_func_name]),
                              factory_func_name)


def lock():
    return ss_lock_factory()