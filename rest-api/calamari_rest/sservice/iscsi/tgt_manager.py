#!/usr/bin/env python
#coding=utf-8

import os
import random
import logging

# import rbd
# import rados

from calamari_rest.sservice.lib.config import Config, TGT_CONF_TEMPLATE_DIR, \
    TGT_CONF_TEMPLATE, TGT_ETC_CONF_DIR, TGT_ETC_EX_FILE, TGTADMIN_CMD, CEPH_CONFIG, \
    SALT_CONFIG_PATH
from calamari_rest.sservice.lib.utils import filter_dict, check_output, run_by_all_minion, \
    send_file_by_salt, run_by_one_minion
from calamari_rest.sservice.lib.schema import Schema, Use, Optional, \
    Default, BoolVal, IntVal, AutoDel
from calamari_rest.sservice.lib.lock import lock
from calamari_rest.sservice.lib import logger
from calamari_rest.sservice.iscsi.target import Target


LUN_CONF_SCHEMA = Schema({
    Optional('lun'): Default(IntVal(1, 255), default=1),
    'size': IntVal(1, 4096),
    'iqn': Use(str),
    'pool': Use(str),
    'image': Use(str),
    'name': Use(str),
    Optional('device_type'): Default(Use(str), default='disk'),
    Optional('bs_type'): Default(Use(str), default='rbd'),
    Optional('write_cache'): Default(BoolVal(), default=True),
    AutoDel(str): object
})


TARGET_CONF_SCHEMA = Schema({
    Optional('id'): Default(IntVal(1, 255), default=1),
    'iqn': Use(str),
    Optional('initiator_addr_list'): Default([Use(str)], default=[]),
    Optional('initiator_name_list'): Default([Use(str)], default=[]),
    Optional('incominguser_list'): Default([Use(str)], default=[]),
    Optional('outgoinguser_list'): Default([Use(str)], default=[]),
    Optional('lun_list'): Default([LUN_CONF_SCHEMA], default=[]),
    AutoDel(str): object
})


TGT_CONF_SCHEMA = Schema({
    Optional('incomingdiscoveryuser'): Default(Use(str), default=''),
    Optional('outgoingdiscoveryuser'): Default(Use(str), default=''),
    Optional('target_list'):  Default([TARGET_CONF_SCHEMA], default=[]),
    AutoDel(str): object
})


class TgtManager(object):

    def __init__(self):
        self.lock = lock()
        self.conf_file = os.path.join(TGT_CONF_TEMPLATE_DIR, TGT_CONF_TEMPLATE)
        self.lun_conf_schema = LUN_CONF_SCHEMA
        self.target_conf_schema = TARGET_CONF_SCHEMA
        self.tgt_conf_schema = TGT_CONF_SCHEMA

    def _load_conf(self):
        tgt_conf = {}
        #check_conf_dir()
        if os.path.exists(self.conf_file):
            tgt_conf = Config.from_file(self.conf_file, self.tgt_conf_schema).conf
        else:
            tgt_conf = self.tgt_conf_schema.validate(tgt_conf)
        return tgt_conf

    def _save_conf(self, tgt_conf):
        #check_conf_dir()
        Config.to_file(self.conf_file, tgt_conf)

    def _get_target_conf(self, iqn):
        tgt_conf = self._load_conf()
        for target_conf in tgt_conf['target_list']:
            if target_conf['iqn'] == iqn:
                return target_conf
        raise Exception('Target (iqn:%s) Not Found' % iqn)

    def _set_target_conf(self, iqn, new_target_conf):
        tgt_conf = self._load_conf()
        for i, target_conf in enumerate(tgt_conf['target_list']):
            if target_conf['iqn'] == iqn:
                tgt_conf['target_list'][i] = new_target_conf
                self._save_conf(tgt_conf)
                self._sync_to_system_conf(tgt_conf)
                return
        raise Exception('Target (iqn:%s) Not Found' % iqn)

    def _get_salt_fileserver_base_path(self):
        find = False
        with open(SALT_CONFIG_PATH) as f:
            for i in f:
                if i.startswith('file_roots:'):
                    find = True
                if find:
                    if '-' in i:
                        _,  path = i.split('-')
                        break
        return path.strip()

    def _lun_conf_to_line(self, lun_conf):
        return 'backing-store %s/%s\n' % (lun_conf['pool'], lun_conf['image'])

    def _target_conf_to_line(self, target_conf):
        line = '<target %s>\n' % target_conf['iqn']

        for initiator_addr in target_conf['initiator_addr_list']:
            line += 'initiator-address %s\n' % initiator_addr

        for initiator_name in target_conf['initiator_name_list']:
            line += 'initiator-name %s\n' % initiator_name

        for incominguser in target_conf['incominguser_list']:
            line += 'incominguser %s\n' % incominguser.replace(':', ' ')

        for outgoinguser in target_conf['outgoinguser_list']:
            line += 'outgoinguser %s\n' % outgoinguser.replace(':', ' ')

        write_cache = None
        for lun_conf in target_conf['lun_list']:
            line += self._lun_conf_to_line(lun_conf)
            if lun_conf and not write_cache:
                write_cache = 'write-cache on\n' if lun_conf['write_cache'] else 'write-cache off\n'
        if target_conf['lun_list']:
            line += 'device-type disk\nbs-type rbd\n%s' % write_cache

        line += '</target>\n\n'

        return line

    def _sync_to_system_conf(self, tgt_conf):
        if not os.path.exists(TGT_ETC_CONF_DIR):
            os.makedirs(TGT_ETC_CONF_DIR)

        file_base_path = self._get_salt_fileserver_base_path()
        ex_file_name = os.path.join(file_base_path, TGT_ETC_EX_FILE)
        with open(ex_file_name, 'w') as f:
            if tgt_conf['incomingdiscoveryuser'] != '':
                f.write('incomingdiscoveryuser %s\n' %
                        tgt_conf['incomingdiscoveryuser'].replace(':', ' '))

            if tgt_conf['outgoingdiscoveryuser'] != '':
                f.write('outgoingdiscoveryuser %s\n' %
                        tgt_conf['outgoingdiscoveryuser'].replace(':', ' '))
            f.write('# target list\n')
            for target_conf in tgt_conf['target_list']:
                f.write(self._target_conf_to_line(target_conf))
            f.write('\n\n')
        send_file_by_salt(TGT_ETC_EX_FILE, '/etc/tgt/conf.d/%s' % TGT_ETC_EX_FILE)

    def sync_to_system_conf(self):
        if not os.path.exists(self.conf_file):
            return

        with self.lock:
            tgt_conf = self._load_conf()
            self._sync_to_system_conf(tgt_conf)

    def system_restore_cb(self):
        if not os.path.exists(self.conf_file):
            return

        os.remove(self.conf_file)

        with self.lock:
            tgt_conf = self._load_conf()
            self._sync_to_system_conf(tgt_conf)

    def get_tgt_conf(self):
        with self.lock:
            tgt_conf = self._load_conf()

        not_allowed_keys = (
            'target_list',
        )
        tgt_conf = filter_dict(tgt_conf, not_allowed_keys, True)

        if tgt_conf['incomingdiscoveryuser'] != '':
            name, sep, password = tgt_conf['incomingdiscoveryuser'].partition(':')
            tgt_conf['incomingdiscoveryuser'] = name.strip() + ':' + '*'
        if tgt_conf['outgoingdiscoveryuser'] != '':
            name, sep, password = tgt_conf['outgoingdiscoveryuser'].partition(':')
            tgt_conf['outgoingdiscoveryuser'] = name.strip() + ':' + '*'

        return tgt_conf

    def get_target_iqn_list(self):
        with self.lock:
            tgt_conf = self._load_conf()

        iqn_list = []
        for target_conf in tgt_conf['target_list']:
            iqn_list.append(target_conf['iqn'])

        return tgt_conf

    def get_target_by_iqn(self, iqn):
        with self.lock:
            tgt_conf = self._load_conf()

        for target_conf in tgt_conf['target_list']:
            if target_conf['iqn'] == iqn:
                return Target(iqn, target_conf, self)

        raise Exception('tgt target (iqn:%s) Not Found' % iqn)

    def get_target_by_id(self, id):
        with self.lock:
            tgt_conf = self._load_conf()

        for target_conf in tgt_conf['target_list']:
            if target_conf['id'] == id:
                return Target(target_conf['iqn'], target_conf, self)

        raise Exception('tgt target (id:%s) Not Found' % id)

    def generate_id(self, existing_ids, max_id):
        max_id = max(existing_ids)+1 if existing_ids else 1
        if max_id > max:
            if len(existing_ids) < max:
                while 1:
                    random_int = random.randint(1, max)
                    if random_int not in existing_ids:
                        max_id = random_int
                        break
            else:
                raise Exception('Id too manay, > %s' % max_id)
        return max_id

    def create_target(self, iqn):

        target_conf ={
            'iqn': iqn,
            'initiator_addr_list': [],
            'initiator_name_list': [],
            'incominguser_list': [],
            'outgoinguser_list': [],
        }
        target_conf = self.target_conf_schema.validate(target_conf)
        with self.lock:
            tgt_conf = self._load_conf()
            target_ids = []
            for conf in tgt_conf['target_list']:
                if conf['iqn'] == iqn:
                    raise Exception('Target (iqn:%s) Already exist' % iqn)
                target_ids.append(conf['id'])

            id = self.generate_id(target_ids, 255)
            target_conf['id'] = id

            tgt_conf['target_list'].append(target_conf)

            self._save_conf(tgt_conf)
            self._sync_to_system_conf(tgt_conf)

        try:
            run_by_all_minion('%s --execute' % TGTADMIN_CMD)
        except Exception as e:
            print e
            pass

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) config is added by operator(%s)' %
        #            (iqn, operator))

    def remove_target_by_iqn(self, iqn):
        with self.lock:
            tgt_conf = self._load_conf()
            delete_conf = None
            for target_conf in tgt_conf['target_list']:
                if target_conf['iqn'] == iqn:
                    delete_conf = target_conf
                    break

            if delete_conf is None:
                raise Exception('Target (iqn:%s) Not Found' % iqn)
            elif delete_conf['lun_list']:
                raise Exception('Target (iqn:%s) has lun' % iqn)
            else:
                tgt_conf['target_list'].remove(delete_conf)

            self._save_conf(tgt_conf)
            self._sync_to_system_conf(tgt_conf)

        try:
            run_by_all_minion('%s -f --delete %s' % (TGTADMIN_CMD, iqn))
        except Exception:
            pass

    def remove_target_by_id(self, id):
        with self.lock:
            tgt_conf = self._load_conf()
            delete_conf = None
            for target_conf in tgt_conf['target_list']:
                if target_conf['id'] == id:
                    delete_conf = target_conf
                    iqn = target_conf['iqn']
                    break

            if delete_conf is None:
                raise Exception('Target (id:%s) Not Found' % id)
            elif delete_conf['lun_list']:
                raise Exception('Target (iqn:%s) has lun' % iqn)
            else:
                tgt_conf['target_list'].remove(delete_conf)

            self._save_conf(tgt_conf)
            self._sync_to_system_conf(tgt_conf)

        try:
            run_by_all_minion('%s -f --delete %s' % (TGTADMIN_CMD, iqn))
        except Exception:
            pass

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) is deleted by operator(%s)' %
        #            (iqn, operator))

    def is_pool_exists(self, pool_name):
        cluster = rados.Rados(conffile=CEPH_CONFIG)
        cluster.connect()
        try:
            return cluster.pool_exists(pool_name)
        finally:
            cluster.shutdown()

    def create_rbd_image(self, pool, image, size):
        run_by_one_minion('rbd create %s/%s -s %d' % (pool, image, size*1024))
        # cluster = rados.Rados(conffile=CEPH_CONFIG)
        # cluster.connect()
        # try:
        #     ioctx = cluster.open_ioctx(pool)
        #     try:
        #         rbd_inst = rbd.RBD()
        #         size = size * 1024**3
        #         rbd_inst.create(ioctx, image, size)
        #     finally:
        #         ioctx.close()
        # finally:
        #     cluster.shutdown()

    def del_rbd_image(self, pool, image):
        run_by_one_minion('rbd rm %s/%s' % (pool, image))
        # cluster = rados.Rados(conffile=CEPH_CONFIG)
        # cluster.connect()
        # try:
        #     ioctx = cluster.open_ioctx(pool)
        #     try:
        #         rbd_inst = rbd.RBD()
        #         rbd_inst.remove(ioctx, image)
        #     finally:
        #         ioctx.close()
        # finally:
        #     cluster.shutdown()


class PoolManager(TgtManager):

    def __init__(self, pool_name):
        super(PoolManager, self).__init__()
        self.pool = pool_name

    def get_lun_by_pool(self):
        with self.lock:
            tgt_conf = self._load_conf()

        luns = []
        for i in  (i['lun_list'] for i in tgt_conf['target_list']):
            for j in i:
                if j['pool'] == self.pool:
                    luns.append(j)

        if not luns:
            raise Exception('Pool (name: %s) No lun' % self.pool)

        return luns

    def get_lun_by_pool_and_num(self, lun_num):
        by_pool_luns = self.get_lun_by_pool()
        lun = [i for i in by_pool_luns if i['lun']==lun_num]

        if len(lun) != 1:
            raise Exception('Pool (name: %s) Lun (lun: %s) No Found' % (self.pool, lun_num))

        return lun[0]


TgtMgr = TgtManager()


def tgt_mgr():
    return TgtMgr


def pool_mgr(pool_name):
    return PoolManager(pool_name)


if __name__ == '__main__':
    tmg = tgt_mgr()
    # print run_by_all_minion('hostname')
    print run_by_one_minion('rbd list liupeng -l')
    # print tmg.conf_file
    # if '2015-08.com.futong:yyy' in tmg.get_target_iqn_list():
    #     print 'i am in'
    #     tmg.remove_target_by_iqn('2015-08.com.futong:yyy')
    #     print 'than del it'
    # tmg.create_target('2015-08.com.futong:yyy')
    # print 'create iqn '
    # print tmg.get_tgt_conf()
    # print tmg.get_target_iqn_list()
    # tgt = tmg.get_target_by_iqn('2015-08.com.futong:yyy')

    # tgt.set_initiator_addr_list(['192.168.8.88'])
    # tgt.del_initiator_addr('192.168.8.88')

    # tgt.set_initiator_name_list(['iqn.1993-08.org.debian:01:e59ff3ea9a54'])
    # tgt.del_initiator_name('iqn.1993-08.org.debian:01:e59ff3ea9a54')

    # tgt.set_incominguser('liu', 'liu')
    # tgt.del_incominguser('liu')

    # tgt.add_lun('1', 'weixianfei/liu3', 1*1024**3)
    # tgt.del_lun(1)

    # print tgt.get_lun_list()
    # print tgt.get_lun_by_num(3)
    # client = LocalClient(config.get('cthulhu', 'salt_config_path'))
    # # pub_data = client.cmd('*', 'cmd.run', ['/usr/sbin/tgt-admin -s'])
    # pub_data = client.cmd('*', 'cp.get_file', ['salt://targets.futong.conf', '/etc/tgt/conf.d/xxx'])
    # print pub_data
    #
    # if not pub_data:
    #     raise Exception("Failed to publish job")
    # def get_file(path, dest, env='base'):
    #     '''
    #     Used to get a single file from the Salt master
    #     '''
    #     # Get the configuration data
    #     opts = salt.config.minion_config(config.get('cthulhu', 'salt_config_path'))
    #     # Create the FileClient object
    #     client = salt.minion.FileClient(opts)
    #     # Call get_file
    #     ex_file_name = os.path.join(TGT_ETC_CONF_DIR, TGT_ETC_EX_FILE)
    #     print ex_file_name
    #     return client.get_file(path, dest, False, env)






