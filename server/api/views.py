import json
import redis
import logging

from functools import wraps

from flask import Blueprint, render_template, request, abort, make_response
from flask_user import roles_required

# internal imports
from app_and_db import es, db_adapter, user_manager
from config import ConfigClass

from users.datastore import UsersHelper
from datastore import ElasticsearchHelper

logger = logging.getLogger()

api_blueprint = Blueprint('api', __name__, url_prefix='/api')

# initialize redis db connector
red = redis.StrictRedis(host=ConfigClass.redis_host, port=ConfigClass.redis_port)

api_backend = ElasticsearchHelper(es)

users_helper = UsersHelper(db_adapter, user_manager)

def api_response(obj):
    """ Helper method to facilitate JSON API responses """
    response = make_response(json.dumps(obj))
    response.headers['Content-Type'] = 'application/json; charset=UTF-8'
    return response

##########################################################################
#--- Auth Functions
##########################################################################

def is_authorized(apikey):
    """ Checks that an API key is authorized
        @param: apikey, str
        @return: authorized, boolean
    """
    authorized = 0
    cached_answer = red.get(apikey)
    if cached_answer is None:
        #check database for apikey
        result = users_helper.get_user_by_apikey(apikey)
        if result and result.is_active():
            answer = 1
        else:
            answer = 0

        # store result in redis cache with TTL of N
        red.setex(apikey, ConfigClass.apikey_cache_ttl, answer)
        authorized = answer
    else:
        authorized = int(cached_answer)
    return authorized

def auth_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        apikey = request.args.get('apikey', None, type=str)
        if apikey and is_authorized(apikey):
            return func(*args, **kwargs)
        else:
            return abort(401)
    return decorated_view

##########################################################################
#--- API Routes
##########################################################################

@api_blueprint.route('/tag_list/', methods=['POST'])
@auth_required
def get_tags():
    info = {'status': 'fail', 'message': 'invalid params'}    
    client_input = request.get_data()
    hashlist = []
    if client_input:
        try:
            hashlist = json.loads(client_input)
        except Exception as e:
            raise e
        else:
            result = api_backend.get_tags_by_hash(hashlist)
            info['status'] = 'success'
            info['message'] = 'query completed'
            info['data'] = result
    return api_response(info)

@api_blueprint.route('/search/', methods=['GET'])
@auth_required
def api_search_tags():
    info = {'status': 'fail', 'message': 'invalid params'}
    query = request.args.get('query', None, type=str)
    size = request.args.get('size', 100, type=int)
    keys = request.args.get('keys', None, type=int)

    if query:
        result = api_backend.search_tags(query, size=size, keys=keys)
        info['status'] = 'success'
        info['message'] = 'query completed'
        info['data'] = result    
    return api_response(info)

@api_blueprint.route('/file/', defaults={'filehash': None}, methods=['PUT'])
@api_blueprint.route('/api/file/<filehash>/', methods=['POST', 'GET', 'DELETE'])
@auth_required
def api_file(filehash):
    info = {'status': 'fail', 
        'message': 'invalid parameters', 
    }
    if request.method == 'GET':
        info = api_backend.get_file(filehash)
    elif request.method == 'DELETE':
        info = api_backend.delete_file(filehash)
    else:
        try:
            client_input = json.loads(request.get_data())
        except Exception as e:
            logger.warning("Unable to parse user input: {}".format(e))
            info['message'] = 'invalid input, must be JSON'
        else:
            if client_input.get("tags") and isinstance(client_input.get("tags"), list):
                if request.method == 'POST':
                    info = api_backend.update_file(filehash, client_input.get("tags"))
                elif request.method == 'PUT':
                    if client_input.get("filehash"):
                        info = api_backend.insert_file(client_input.get("filehash"), client_input.get("tags"))
                    else:
                        info['message'] = '"filehash" parameter must be a string'
            else: 
                info['message'] = '"tags" parameter must be JSON list'

    return api_response(info)
