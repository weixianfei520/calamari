#!/usr/bin/env python
#coding=utf-8

import os
import json
import subprocess

from calamari_common.salt_wrapper import LocalClient
from calamari_rest.sservice.lib.config import SALT_CONFIG_PATH


def filter_dict(d, keys, invert=False):
    key_set = set(d.keys()) - set(keys) if invert else set(keys) & set(d.keys())
    return dict([(k, d[k]) for k in key_set])


class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs.pop('default', None)
        super(CustomJSONEncoder, self).__init__(*args, **kwargs)

    def default(self, o):
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            if isinstance(o, set):
                return list(o)
            elif hasattr(o, '__json__'):
                return o.__json__()
            elif hasattr(o, '__dict__'):
                obj_dict = {}
                for k, v in o.__dict__.iteritems():
                    if not k.startswith('_'):
                        obj_dict[k] = v
                return obj_dict


def encode_json(o):
    return json.dumps(o, check_circular=True, cls=CustomJSONEncoder)


def check_conf_dir(path):
    if not os.path.isdir(path):
        if os.path.exists(path):
            raise Exception("conf path(%s) is not a directory" % path)
        else:
            os.makedirs(path)


def check_output(cmd, shell=False, input_ret=[]):
    try:
        return subprocess.check_output(cmd,
                                       stderr=subprocess.STDOUT,
                                       shell=shell)
    except subprocess.CalledProcessError as e:
        returncode = e.returncode
        if returncode in input_ret:
            http_status = 400
        else:
            http_status = 500
        info = e.output
        print info, returncode
    except Exception as e:
        raise(e)


def _run_by_salt(tgt, fun, cmd):
    client = LocalClient(SALT_CONFIG_PATH)
    return client.cmd(tgt, fun, cmd, timeout=5)


def run_by_all_minion(cmd):
    return _run_by_salt('*', 'cmd.run', [cmd])


def run_by_one_minion(cmd):
    data = _run_by_salt('*', 'test.ping', [])
    active_minion = None
    for k, v in data.items():
        if v:
            active_minion = k
            break

    if not active_minion:
        return False

    return _run_by_salt(active_minion, 'cmd.run', [cmd])


def send_file_by_salt(sour, dest):
    return _run_by_salt('*', 'cp.get_file', ['salt://%s' % sour, dest])


if __name__ == '__main__':
    # print check_output(['lsss'])
    print check_output('exit 10', True)


