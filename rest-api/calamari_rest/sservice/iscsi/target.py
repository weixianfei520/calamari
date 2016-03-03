#!/usr/bin/env python
#coding=utf-8

from calamari_rest.sservice.lib.config import TGTADMIN_CMD
from calamari_rest.sservice.lib.utils import check_output, run_by_all_minion, run_by_one_minion


class Target(object):

    def __init__(self, iqn, conf, manager):
        self.iqn = iqn
        self.conf = conf
        self.manager = manager

    def _update_target(self):
        try:
            run_by_all_minion('%s -f --update %s' % (TGTADMIN_CMD, self.iqn))
        except Exception:
            pass

    def get_initiator_addr_list(self):
        return self.conf['initiator_addr_list']

    def set_initiator_addr_list(self, initiator_addr_list=[]):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            conf['initiator_addr_list'] = initiator_addr_list
            self.manager._set_target_conf(self.iqn, conf)

            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) initiator_addr_list is updated by operator(%s)' %
        #            (self.iqn, operator))

    def del_initiator_addr(self, ip):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            found = None
            for i in conf['initiator_addr_list']:
                if i == ip:
                    found = i

            if found is None:
                raise Exception('Target (iqn:%s) initiator addr (%s) Not Found' % (self.iqn, ip))
            else:
                conf['initiator_addr_list'].remove(found)

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

    def get_initiator_name_list(self):
        return self.conf['initiator_name_list']

    def set_initiator_name_list(self, initiator_name_list=[]):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            conf['initiator_name_list'] = initiator_name_list
            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) initiator_name_list is updated by operator(%s)' %
        #            (self.iqn, operator))

    def del_initiator_name(self, name):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            found = None
            for i in conf['initiator_name_list']:
                if i == name:
                    found = i

            if found is None:
                raise Exception('Target (iqn:%s) initiator name (%s) Not Found' % (self.iqn, name))
            else:
                conf['initiator_name_list'].remove(found)

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

    def get_incominguser_list(self):
        user_list = []
        for user in self.conf['incominguser_list']:
            name, sep, password = user.partition(':')
            user_list.append( name.strip())
        return user_list

    def set_incominguser(self, name, passwd):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            found = False
            for index, user in enumerate(conf['incominguser_list']):
                user_name, sep, password = user.partition(':')
                if user_name == name:
                    conf['incominguser_list'][index] = name.strip() + ':' + passwd.strip()
                    found = True

            if not found:
                conf['incominguser_list'].append(name.strip() + ':' + passwd.strip())

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) incominguser (%s) is set by operator(%s)' %
        #            (self.iqn, name, operator))

    def del_incominguser(self, name):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            found = None
            for user in conf['incominguser_list']:
                user_name, sep, password = user.partition(':')
                if user_name == name:
                    found = user

            if found is None:
                raise Exception('tgt target (iqn:%s) incominguser (%s) Not Found' % (self.iqn, name))
            else:
                conf['incominguser_list'].remove(found)

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) incominguser (%s) is deleted by operator(%s)' %
        #            (self.iqn, name, operator))

    def get_outgoinguser_list(self):
        user_list = []
        for user in self.conf['outgoinguser_list']:
            name, sep, password = user.partition(':')
            user_list.append( name.strip())
        return user_list

    def set_outgoinguser(self, name, passwd):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            found = False
            for index, user in enumerate(conf['outgoinguser_list']):
                user_name, sep, password = user.partition(':')
                if user_name == name:
                    conf['outgoinguser_list'][index] = name.strip() + ':' + passwd.strip()
                    found = True

            if not found:
                conf['outgoinguser_list'].append(name.strip() + ':' + passwd.strip())

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) outgoinguser (%s) is set by operator(%s)' %
        #            (self.iqn, name, operator))

    def del_outgoinguser(self, name):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            found = None
            for user in conf['outgoinguser_list']:
                user_name, sep, password = user.partition(':')
                if user_name == name:
                    found = user

            if found is None:
                raise Exception('tgt target (iqn:%s) outgoinguser (%s) Not Found' %
                                     (self.iqn, name))
            else:
                conf['outgoinguser_list'].remove(found)

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) outgoinguser (%s) is deleted by operator(%s)' %
        #            (self.iqn, name, operator))

    def get_lun_list(self):
        return self.conf['lun_list']

    def get_lun_by_num(self, lun_num):
        for lun in self.conf['lun_list']:
            if lun['lun'] == lun_num:
                return lun

        raise Exception('Target (iqn:%s) Lun (%d)Not Found' % (self.iqn, lun_num))

    def add_lun(self, pool, image, size, name, device_type='disk', bs_type='rbd', write_cache=True):
        lun_conf = {
            'iqn': self.iqn,
            'size': size,
            'pool': pool,
            'image': image,
            'name': name,
            'device_type': device_type,
            'bs_type': bs_type,
            'write_cache': write_cache,
        }
        lun_conf = self.manager.lun_conf_schema.validate(lun_conf)

        if bs_type != 'rbd':
            raise Exception("device 's bs_type must be rbd")

        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            tgt_conf = self.manager._load_conf()

            for i in conf['lun_list']:
                if i['name'] == name:
                    raise Exception('Target (iqn:%s) Lun name(%s) already exists' %
                                    (self.iqn, name))

            for i in conf['lun_list']:
                if i['pool'] == pool:
                    for j in conf['lun_list']:
                        if j['image'] == image:
                            raise Exception('Target (iqn:%s) Lun Path (%s/%s) already exists' %
                                            (self.iqn, pool, image))

            try:
                self.manager.create_rbd_image(pool, image, size)
            except Exception, e:
                raise(e)

            lun_ids = []
            for i in  tgt_conf['target_list']:
                for j in i['lun_list']:
                    lun_ids.append(j['lun'])
            id = self.manager.generate_id(lun_ids, 255)
            lun_conf['lun'] = id
            conf['lun_list'].append(lun_conf)

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) Lun (%d) is added by operator(%s)' %
        #            (self.iqn, lun, operator))


    def set_lun(self, lun, data):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            found = None
            for l in conf['lun_list']:
                if l['lun'] == lun:
                    found = l
                    conf['lun_list'].remove(l)
                    break

            if not found:
                raise Exception('Target (iqn:%s) Lun (%d)Not Found' % (self.iqn, lun))

            if 'size' in data:
                run_by_one_minion('rbd resize %s/%s -s %d' % (found['pool'], found['image'], data['size']*1024))

            if 'name' in data:
                for i in conf['lun_list']:
                    if i['name'] == data['name']:
                        raise Exception('Target (iqn:%s) Lun (name:%s) duplicate' % (self.iqn, data['name']))

            found.update(data)
            lun_conf = self.manager.lun_conf_schema.validate(found)
            conf['lun_list'].append(lun_conf)
            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) Lun (%d) is updated by operator(%s)' %
        #            (self.iqn, lun, operator))

    def del_lun(self, lun):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            tgt_conf = self.manager._load_conf()

            found = None
            for l in conf['lun_list']:
                if l['lun'] == lun:
                    found = l

            if found is None:
                raise Exception('Target (iqn:%s) Lun (%d) Not Found' % (self.iqn, lun))
            else:
                conf['lun_list'].remove(found)

            is_relation = False
            for i in tgt_conf['target_list']:
                for j in i['lun_list']:
                    if j['pool'] == found['pool'] and j['image'] == found['image'] and \
                                    j['lun'] != found['lun']:
                        is_relation = True
                        break

            self.manager._set_target_conf(self.iqn, conf)
            self.conf = conf

        self._update_target()

        try:
            if not is_relation:
                self.manager.del_rbd_image(found['pool'], found['image'])
        except Exception, e:
            raise e

        # logger.log(logging.INFO, logger.LOG_TYPE_CONFIG,
        #            'tgt target (iqn:%s) Lun (%d) is deleted by operator(%s)' %
        #            (self.iqn, lun, operator))

    # def get_state(self):
    #     return TgtStatus.get_target_state(self.iqn)

    def set_state(self, state):
        if state == 'offline':
            check_output([TGTADMIN_CMD, '--offline', self.iqn])
        elif state == 'ready':
            check_output([TGTADMIN_CMD, '--ready', self.iqn])
        else:
            raise Exception('state (%s) is  not supported' % state)

    # def get_session_list(self):
    #     return TgtStatus.get_target_sessions(self.iqn)

    def update_target_iqn(self, new_iqn):
        with self.manager.lock:
            conf = self.manager._get_target_conf(self.iqn)
            tgt_conf = self.manager._load_conf()
            for i in tgt_conf['target_list']:
                if i['iqn'] == new_iqn:
                    raise Exception('Target (iqn:%s) Already exist' % new_iqn)

            new_iqn_lun_list = []
            for i in conf['lun_list']:
                i['iqn'] = new_iqn
                new_iqn_lun_list.append(i)
            conf['iqn'] = new_iqn
            conf['lun_list'] = new_iqn_lun_list

            self.manager._set_target_conf(self.iqn, conf)

            run_by_all_minion('%s -f --delete %s' % (TGTADMIN_CMD, self.iqn))

            self.iqn = new_iqn
            self.conf = conf

        self._update_target()
