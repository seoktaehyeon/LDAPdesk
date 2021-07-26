#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ldap3
from ldap3 import Server, Connection, MODIFY_REPLACE
import json
import logging


class LdapCtl(object):
    def __init__(self, ldap_domain, ldap_user, ldap_pass, ldap_host='127.0.0.1', ldap_port=389):
        self.ldap_host = ldap_host
        self.ldap_port = ldap_port
        self.ldap_domain = ldap_domain
        self.ldap_base = 'dc=%s' % ',dc='.join(
            self.ldap_domain.split('.')
        )
        self.ldap_user = ldap_user
        self.ldap_user_dn = ','.join([
            'cn=%s' % self.ldap_user,
            self.ldap_base
        ])
        self.ldap_pass = ldap_pass
        self.ldap_server = Server(host=ldap_host, port=ldap_port)
        self.ldap_conn = Connection(
            server=self.ldap_server,
            user=self.ldap_user_dn,
            password=self.ldap_pass,
            auto_bind=True
        )
        self.whoami = self.ldap_conn.extend.standard.who_am_i()
        self.ldap_entries = list()
        self.ldap_tree = dict()
        # self.ldap_conn.extend.microsoft.add_members_to_groups()
        # self.ldap_conn.extend.microsoft.remove_members_from_groups()

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def login(self):
        """
        Login LDAP
        :return:
        """
        logging.debug('%s login' % self.whoami)
        assert self.whoami == 'dn:%s' % self.ldap_user_dn, '%s != dn:%s' % (self.whoami, self.ldap_user_dn)
        return True

    def logout(self):
        """
        Logout LDAP
        :return:
        """
        logging.debug('%s logout' % self.whoami)
        self.ldap_conn.unbind()
        return True

    def list_object(self, ldap_filter='(objectClass=*)'):
        """
        List all objects
        :param ldap_filter:
        :return:
        """
        logging.debug('Start to list LDAP entries : %s %s' % (self.ldap_base, ldap_filter))
        self.ldap_entries = []
        self.ldap_conn.search(
            search_base=self.ldap_base,
            search_filter=ldap_filter
        )
        assert self.ldap_conn.result.get('result') == 0, '%s' % self.ldap_conn.result.get('description')
        logging.debug('Complete to list entries')
        for ldap_entry in self.ldap_conn.entries:
            self.ldap_entries.append(json.loads(ldap_entry.entry_to_json()))
        logging.debug('LDAP entries : %s' % self.ldap_entries)
        return True

    def tree_object(self, node_parent_dn=None, node_parent_path=None):
        # node_parent_dn and node_parent_path is required
        # if empty will be defined as root level
        if node_parent_dn is None:
            logging.debug('Start to tree LDAP object: %s' % self.ldap_base)
            node_parent_dn = self.ldap_base
        if node_parent_path is None:
            self.ldap_tree[node_parent_dn] = dict()
            node_parent_path = self.ldap_tree[node_parent_dn]
        # Start to parse entries, the first one should be domain, skip it
        for node in self.ldap_entries[1:]:
            node_dn = node['dn']
            # Check node dn if it ends with parent node dn, this node will be parsed
            if node_dn not in node_parent_dn and node_dn.endswith(node_parent_dn):
                logging.debug('%s ends with %s' % (node_dn, node_parent_dn))
                node_dn_prefix = node_dn.replace(',%s' % node_parent_dn, '').split(',')
                logging.debug('Node DN prefix : %s' % node_dn_prefix)
                if len(node_dn_prefix) == 1:
                    node_parent_path[node_dn] = {}
                    logging.debug('Success to add %s into tree' % node_dn)
                elif len(node_dn_prefix) > 1:
                    _node_parent_dn = '%s,%s' % (node_dn_prefix[-1], node_parent_dn)
                    if _node_parent_dn not in node_parent_path.keys():
                        node_parent_path[_node_parent_dn] = {}
                    self.tree_object(_node_parent_dn, node_parent_path[_node_parent_dn])
        logging.debug('Complete to tree object')
        logging.debug('LDAP tree: %s' % self.ldap_tree)
        return True

    def get_object(self, search_base, search_filter='(objectClass=*)'):
        logging.debug('Get object: %s %s' % (search_base, search_filter))
        self.ldap_conn.search(
            search_base=search_base,
            search_filter=search_filter,
            attributes=[ldap3.ALL_ATTRIBUTES]
        )
        assert self.ldap_conn.result.get('result') == 0, '%s' % self.ldap_conn.result.get('description')
        logging.debug('Complete to get object')
        object_detail = json.loads(self.ldap_conn.entries[0].entry_to_json())
        logging.debug('Object detail : %s' % object_detail)
        return object_detail

    def update_object(self, dn, attributes):
        attributes_change = dict()
        for attr_key, attr_value in attributes.items():
            attributes_change[attr_key] = [(
                MODIFY_REPLACE, [attr_value]
            )]
        self.ldap_conn.modify(
            dn=dn,
            changes=attributes_change
        )
        assert self.ldap_conn.result.get('result') == 0, '%s' % self.ldap_conn.result.get('description')
        return True

    def rename_object(self, dn, relative_dn):
        logging.debug('Rename %s to %s' % (dn, relative_dn))
        self.ldap_conn.modify_dn(dn=dn, relative_dn=relative_dn, delete_old_dn=True, new_superior=None)
        assert self.ldap_conn.result.get('result') == 0, '%s' % self.ldap_conn.result.get('description')
        return True

    def add_object(self, dn, object_class, attributes):
        logging.debug('Add new object: %s' % dn)
        self.ldap_conn.add(
            dn=dn,
            object_class=object_class,
            attributes=attributes
        )
        assert self.ldap_conn.result.get('result') == 0, '%s' % self.ldap_conn.result.get('description')
        return True

    def delete_object(self, dn):
        logging.debug('Delete new user: %s' % dn)
        self.ldap_conn.delete(dn=dn)
        assert self.ldap_conn.result.get('result') == 0, '%s' % self.ldap_conn.result.get('description')
        return True

    def add_user(self, obj_dn, obj_class=None, obj_attr=None):
        logging.debug('Add new user: %s' % obj_dn)
        obj_cn = obj_dn.split(',')[0].split('=')[1]
        obj_class = obj_class if obj_class else [
            'top',
            'inetOrgPerson'
        ]
        obj_attr = obj_attr if obj_attr else {
            'sn': obj_cn,
            'uid': obj_cn
        }
        return self.add_object(dn=obj_dn, object_class=obj_class, attributes=obj_attr)

    def add_group(self, obj_dn, obj_class=None, obj_attr=None):
        logging.debug('Add new group : %s' % obj_dn)
        obj_class = obj_class if obj_class else [
            'top',
            'groupOfUniqueNames'
        ]
        obj_attr = obj_attr if obj_attr else {
            'uniqueMember': [],
        }
        return self.add_object(dn=obj_dn, object_class=obj_class, attributes=obj_attr)

    def move_object(self, obj_dn, target_parent_obj_dn):
        logging.debug('Move %s to %s' % (obj_dn, target_parent_obj_dn))
        obj_info = self.get_object(search_base=obj_dn)
        self.add_object(
            dn='%s,%s' % (obj_dn.split(',')[0], target_parent_obj_dn),
            object_class=obj_info['attributes'].get('objectClass'),
            attributes=obj_info['attributes']
        )
        self.delete_object(dn=obj_dn)
        return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='[ %(asctime)s ] %(levelname)s %(message)s')
    print('This is LDAP ctl scripts')
