#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random

from flask import Flask, jsonify, render_template, request, session, redirect
from utils.ldapctl import LdapCtl
import os
# import yaml
# import json
import logging
import random

logging.basicConfig(level=logging.INFO, format='[ %(asctime)s ] %(levelname)s %(message)s')
# logging.basicConfig(level=logging.DEBUG, format='[ %(asctime)s ] %(levelname)s %(message)s')

app = Flask(__name__)


def isLdapAattribute(attr_name):
    attr_list = [
        "objectClass",
        "gidNumber",
        "cn",
        "sn",
        "uid",
        "displayName",
        "email",
        "userPassword",
        "ou",
        "description",
        "uniqueMember",
    ]
    return True if attr_name in attr_list else False


def formatLdapAttributes(attr_dict):
    formatted_attrs = dict()
    for attr_k, attr_v in attr_dict.items():
        if isLdapAattribute(attr_k):
            logging.debug('Found attribute %s in form' % attr_k)
            formatted_attrs[attr_k] = attr_v.split(',')
    logging.debug('Formatted attributes: %s' % formatted_attrs)
    return formatted_attrs



@app.route('/', methods=["GET"])
def index():
    logging.debug('%s : /' % request.method)
    if session.get('ldap_username') is None or session.get('ldap_password') is None:
        logging.debug('No ldap_username or ldap_password in session')
        return redirect(location='/login')
    return render_template(
        template_name_or_list='index.html',
        rsp_data={
            'ldap_domain': os.getenv('LDAP_SERVER_DOMAIN'),
            'ldap_username': session.get('ldap_username'),
        }
    )


@app.route('/login', methods=["GET", "POST"])
def login():
    logging.debug('%s : /login' % request.method)
    _data = {
        "ldap_host": os.getenv('LDAP_SERVER_HOST'),
        "ldap_port": int(os.getenv('LDAP_SERVER_PORT')),
        "ldap_domain": os.getenv('LDAP_SERVER_DOMAIN'),
    }
    if request.method == "POST":
        _data["ldap_username"] = request.form.get('ldap_username')
        _data["ldap_password"] = request.form.get('ldap_password')
    logging.debug('Request data : %s' % _data)
    try:
        with LdapCtl(
                ldap_host=_data['ldap_host'],
                ldap_port=_data['ldap_port'],
                ldap_domain=_data['ldap_domain'],
                ldap_user=_data['ldap_username'],
                ldap_pass=_data['ldap_password']
        ) as ldap_ctl:
            print(ldap_ctl.whoami)
        session['ldap_username'] = _data['ldap_username']
        session['ldap_password'] = _data['ldap_password']
        logging.debug('Login success and redirect to /')
        return redirect(location='/')
    except Exception as e:
        logging.error('Login failed : %s' % e)
    return render_template(
        template_name_or_list='login.html',
        rsp_data={
            'ldap_domain': os.getenv('LDAP_SERVER_DOMAIN'),
        }
    )


@app.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return render_template(
        template_name_or_list='login.html',
        rsp_data={
            'ldap_domain': os.getenv('LDAP_SERVER_DOMAIN'),
        }
    )


@app.route('/api/list', methods=["GET"])
def api_list_object():
    _entries = list()
    try:
        with LdapCtl(
                ldap_host=os.getenv('LDAP_SERVER_HOST'),
                ldap_port=int(os.getenv('LDAP_SERVER_PORT')),
                ldap_domain=os.getenv('LDAP_SERVER_DOMAIN'),
                ldap_user=session.get('ldap_username'),
                ldap_pass=session.get('ldap_password')
        ) as ldap_ctl:
            ldap_ctl.list_object()
            _entries = ldap_ctl.ldap_entries
            logging.debug('LDAP entries: %s' % _entries)
    except Exception as e:
        logging.error(e)
    return jsonify(_entries)


@app.route('/api/tree', methods=["GET"])
def api_list_tree():
    node_tree = list()
    try:
        with LdapCtl(
                ldap_host=os.getenv('LDAP_SERVER_HOST'),
                ldap_port=int(os.getenv('LDAP_SERVER_PORT')),
                ldap_domain=os.getenv('LDAP_SERVER_DOMAIN'),
                ldap_user=session.get('ldap_username'),
                ldap_pass=session.get('ldap_password')
        ) as ldap_ctl:
            ldap_ctl.list_object()
            ldap_ctl.tree_object()
            ldap_tree = ldap_ctl.ldap_tree
            logging.debug('LDAP tree: %s' % ldap_tree)
    except Exception as e:
        logging.error(e)
        return jsonify(node_tree)

    # Internal function
    def _ldap_tree_to_node_tree(_node_tree, _ldap_tree):
        _node_level = 0
        for key, value in _ldap_tree.items():
            logging.debug('Append %s' % key)
            _node_tree.append({
                'text': key.split(',')[0],
                'href': 'javascript:getObject("%s")' % key,
            })
            value_len = len(value)
            logging.debug('Value length is %s : %s' % (value_len, value))
            if value:
                _node_tree[_node_level]['nodes'] = list()
                _node_tree[_node_level]['tags'] = [str(value_len)]
                _ldap_tree_to_node_tree(
                    _node_tree=_node_tree[_node_level]['nodes'],
                    _ldap_tree=value
                )
            _node_level += 1

    _ldap_tree_to_node_tree(_node_tree=node_tree, _ldap_tree=ldap_tree)
    logging.debug('Node tree : %s' % node_tree)
    return jsonify(node_tree)


@app.route('/api/get', methods=["GET"])
def api_get_object():
    """

    :return:
    """
    obj_detail = dict()
    obj_dn = request.args.get('dn')
    logging.info('%s get object %s' % (session.get('ldap_username'), obj_dn))
    try:
        with LdapCtl(
                ldap_host=os.getenv('LDAP_SERVER_HOST'),
                ldap_port=int(os.getenv('LDAP_SERVER_PORT')),
                ldap_domain=os.getenv('LDAP_SERVER_DOMAIN'),
                ldap_user=session.get('ldap_username'),
                ldap_pass=session.get('ldap_password')
        ) as ldap_ctl:
            obj_detail = ldap_ctl.get_object(search_base=obj_dn)
            session['ldap_current_dn'] = obj_dn
    except Exception as e:
        logging.error(e)
    return jsonify(obj_detail)


@app.route('/api/add', methods=["POST"])
def api_add_object():
    obj_dn = '%s=%s,%s' % (request.form.get('rdnKey'), request.form.get('rdnValue'), request.form.get('baseDn'))
    obj_class = request.form.get('objectClass')
    obj_attr = formatLdapAttributes(request.form)
    obj_detail = dict()
    logging.info('%s add new object %s' % (session.get('ldap_username'), obj_dn))
    try:
        with LdapCtl(
                ldap_host=os.getenv('LDAP_SERVER_HOST'),
                ldap_port=int(os.getenv('LDAP_SERVER_PORT')),
                ldap_domain=os.getenv('LDAP_SERVER_DOMAIN'),
                ldap_user=session.get('ldap_username'),
                ldap_pass=session.get('ldap_password')
        ) as ldap_ctl:
            ldap_ctl.add_object(
                dn=obj_dn,
                object_class=obj_class,
                attributes=obj_attr
            )
            # obj_detail = ldap_ctl.get_object(search_base=obj_dn)
            session['ldap_current_dn'] = obj_dn
    except Exception as e:
        logging.error(e)
    # return jsonify(obj_detail)
    return redirect(location='/')


@app.route('/api/update', methods=["POST"])
def api_update_object():
    logging.debug('Form: %s' % request.form)
    obj_dn = request.form.get('dn')
    obj_attr = formatLdapAttributes(request.form)
    # for attrKey, attrValue in request.form.items():
    #     if isLdapAattribute(attrKey):
    #         logging.debug('Found attribute %s in form' % attrKey)
    #         obj_attr[attrKey] = attrValue.split(',')
    # obj_detail = dict()
    logging.info('%s update object %s' % (session.get('ldap_username'), obj_dn))
    logging.debug('%s' % obj_attr)
    try:
        with LdapCtl(
                ldap_host=os.getenv('LDAP_SERVER_HOST'),
                ldap_port=int(os.getenv('LDAP_SERVER_PORT')),
                ldap_domain=os.getenv('LDAP_SERVER_DOMAIN'),
                ldap_user=session.get('ldap_username'),
                ldap_pass=session.get('ldap_password')
        ) as ldap_ctl:
            ldap_ctl.update_object(
                dn=obj_dn,
                attributes=obj_attr
            )
            session['ldap_current_dn'] = obj_dn
    except Exception as e:
        logging.error(e)
    return redirect(location='/')


@app.route('/delete', methods=["POST"])
def delete_object():
    obj_dn = request.values.get("dn")
    logging.info('%s delete object %s' % (session.get('ldap_username'), obj_dn))
    try:
        with LdapCtl(
                ldap_host=os.getenv('LDAP_SERVER_HOST'),
                ldap_port=int(os.getenv('LDAP_SERVER_PORT')),
                ldap_domain=os.getenv('LDAP_SERVER_DOMAIN'),
                ldap_user=session.get('ldap_username'),
                ldap_pass=session.get('ldap_password')
        ) as ldap_ctl:
            ldap_ctl.delete_object(dn=obj_dn)
    except Exception as e:
        logging.error(e)
        return False
    return redirect(location='/')


@app.route('/api/move', methods=["POST"])
def api_move_object():
    obj_dn = request.form.get('dn')
    obj_cn = obj_dn.split(',')[0]
    target_parent_dn = request.form.get('target_parent_dn')
    obj_detail = dict()
    logging.info('%s move object %s to %s' % (session.get('ldap_username'), obj_dn, target_parent_dn))
    try:
        with LdapCtl(
                ldap_host=os.getenv('LDAP_SERVER_HOST'),
                ldap_port=int(os.getenv('LDAP_SERVER_PORT')),
                ldap_domain=os.getenv('LDAP_SERVER_DOMAIN'),
                ldap_user=session.get('ldap_username'),
                ldap_pass=session.get('ldap_password')
        ) as ldap_ctl:
            ldap_ctl.move_object(
                obj_dn=obj_dn,
                target_parent_obj_dn=target_parent_dn
            )
            obj_detail = ldap_ctl.get_object(search_base='%s,%s' % (obj_cn, target_parent_dn))
    except Exception as e:
        logging.error(e)
    # return jsonify(obj_detail)
    return redirect(location='/')


if __name__ == '__main__':
    print('LDAP_SERVER_HOST: %s' % os.getenv('LDAP_SERVER_HOST'))
    print('LDAP_SERVER_PORT: %s' % os.getenv('LDAP_SERVER_PORT'))
    print('LDAP_SERVER_DOMAIN: %s' % os.getenv('LDAP_SERVER_DOMAIN'))
    app.secret_key = random.random().hex().replace('.', '').replace('-', '')
    app.run(host='0.0.0.0', port=80, debug=True)
