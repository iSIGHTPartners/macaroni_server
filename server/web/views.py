import logging
import json

from flask import Blueprint, render_template, redirect

# internal imports
from config import ConfigClass

logger = logging.getLogger()

site_blueprint = Blueprint('site', __name__, url_prefix='/')

##########################################################################
#--- UI Routes
##########################################################################

@site_blueprint.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@site_blueprint.route('install', methods=['GET'])
def install():
    return render_template('install.html')

@site_blueprint.route('about', methods=['GET'])
def about():
    return render_template('about.html')

@site_blueprint.route('download', methods=['GET'])
def download():
    return redirect(ConfigClass.extension_download_url, 303)

@site_blueprint.route('update.xml', methods=['GET'])
def extension_update_url():
    #TODO: https://developer.chrome.com/extensions/autoupdate
    pass
    
