#!/usr/bin/env python
#coding=utf-8

from calamari_rest.sservice.lib.utils import check_output
from calamari_rest.sservice.iscsi.tgt_manager import TGTADMIN_CMD


class ParseObject(dict):
    def __init__(self,*args, **kwargs):
        super(ParseObject, self).__init__(*args, **kwargs)
        self.value = ''


def leading_space_num(line):
    no_space_line = line.lstrip()
    return line.index(no_space_line)


def parse_lines(lines=[], value=''):
    obj = ParseObject()
    obj.value = value

    leading = leading_space_num(lines[0]) if len(lines) > 0 else 0
    line_index = 0
    line_num = len(lines)
    while line_index < line_num:
        if leading_space_num(lines[line_index]) < leading:
            break
        key, sep, value = lines[line_index].partition(':')
        key = key.strip()
        value = value.strip()
        line_index += 1
        if sep == '':
            continue
        if line_index < line_num and (leading_space_num(lines[line_index]) > leading):
            # print line_index, line_num, leading_space_num(lines[line_index]), leading
            print value
            parsed_num, tmpObj = parse_lines(lines[line_index:], value)
            line_index += parsed_num
        else:
            tmpObj = ParseObject()
            tmpObj.value = value
        if key in obj:
            if not isinstance(obj[key], list):
                obj[key] = [obj[key]]
            obj[key].append(tmpObj)
        else:
            obj[key] = tmpObj

    return line_index, obj


class TgtStatus(object):

    def __init__(self):
        pass

    def _get_target_info(self, iqn):
        output_lines = check_output([TGTADMIN_CMD, '-s']).split('\n')
        line_num, root = parse_lines(output_lines)
        for k,v in root.items():
            if v.value == iqn:
                return v
        raise Exception('The target (%s) Not Found' % (iqn), 404)

    def get_target_state(self, iqn):
        try:
            target = self._get_target_info(iqn)
        except Exception:
            return 'error'
        return target['System information']['State'].value

    def get_target_sessions(self, iqn):
        sessions = []
        try:
            target = self._get_target_info(iqn)
        except Exception:
            return sessions

        nexus_info = target['I_T nexus information']
        if 'I_T nexus' not in nexus_info:
            return sessions

        if not isinstance(nexus_info['I_T nexus'], list):
            nexus_info['I_T nexus'] = [nexus_info['I_T nexus']]

        for nexus in nexus_info['I_T nexus']:
            if 'Connection' in nexus and isinstance(nexus['Connection'], list):
                addr = nexus['Connection'][0]['IP Address'].value
            elif  'Connection' in nexus:
                addr = nexus['Connection']['IP Address'].value
            else:
                addr = ''

            sessions.append({
                'initiator':nexus['Initiator'].value,
                'addr': addr
            })

        return sessions


TgtStatus = TgtStatus()


def tgt_status():
    return TgtStatus


if __name__ == '__main__':
    tgt = TgtStatus
    print tgt.get_target_state('iqn:2011-07.com.baidu:test')
    # print tgt.get_target_sessions('iqn:2011-07.com.baidu:test')
