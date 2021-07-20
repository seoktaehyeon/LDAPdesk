#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, render_template
import os
# import yaml
# import json
import logging

logging.basicConfig(level=logging.INFO, format='[ %(asctime)s ] %(levelname)s %(message)s')


app = Flask(__name__)


@app.route('/')
def index():
    return render_template(
        template_name_or_list='index.html',
        body_data={
            'domain': os.getenv('LDAP_SERVER_DOMAIN'),
        }
    )


@app.route('/login')
def login():
    return render_template(
        template_name_or_list='login.html',
        body_data={
            'domain': os.getenv('LDAP_SERVER_DOMAIN'),
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
