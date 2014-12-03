import logging
import json

from flask import Blueprint, render_template, request, make_response
from flask_user import roles_required

# internal imports
from app_and_db import app, db_adapter, user_manager
from config import ConfigClass

from datastore import UsersHelper

logger = logging.getLogger()

users_helper = UsersHelper(db_adapter, user_manager)

users_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

def api_response(obj):
    """ Helper method to facilitate JSON API responses """
    response = make_response(json.dumps(obj))
    response.headers['Content-Type'] = 'application/json; charset=UTF-8'
    return response

##########################################################################
#--- UI Routes
##########################################################################

@users_blueprint.route('/', methods=['POST', 'GET'])
@roles_required('admin')
def manage():
    return render_template('user_management.html', users=users_helper.get_user_list())

@users_blueprint.route('/adduser', methods=['POST'])
@roles_required('admin')
def adduser():
    info = {'status': 'fail', 'message': 'invalid params'}
    username = request.form.get('email', None, type=str)
    role = ConfigClass.default_role
    if username:
        result = users_helper.add_user(username, role, 'Password123')
        info['status'] = 'success'
        info['message'] = result

    return api_response(info)

@users_blueprint.route('/deluser', methods=['POST'])
@roles_required('admin')
def deluser():
    info = {'status': 'fail', 'message': 'invalid params'}
    username = request.form.get('email', None, type=str)
    if username:
        result = users_helper.del_user(username)
        info['status'] = 'success'
        info['message'] = result

    return api_response(info)
    

@users_blueprint.route('/toggle_active', methods=['POST'])
@roles_required('admin')
def user_toggle_active():
    info = {'status': 'fail', 'message': 'invalid params'}
    username = request.form.get('email', None, type=str)
    if username:
        result = users_helper.toggle_active(username)
        info['status'] = 'success'
        info['message'] = result

    return api_response(info)


