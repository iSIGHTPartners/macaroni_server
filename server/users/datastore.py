import logging

from uuid import uuid4

# internal imports
from config import ConfigClass
from model import User, Role

logger = logging.getLogger()

class UsersHelper(object):
    
    def __init__(self, db_adapter, user_manager):
        self.db_adapter = db_adapter
        self.user_manager = user_manager

    def add_user(self, username, role, password):
        info = "query failed"
        logger.debug("Add user: {} ({})".format(username, role))
        try:
            if role in ConfigClass.roles:
                if not User.query.filter(User.username == username).first():
                    user = User(username=username, is_enabled=True,
                            password=self.user_manager.hash_password(password),
                            apikey=uuid4().get_hex())
                    user_role = Role.query.filter(Role.name==role).first()
                    user.roles.append(user_role)
                    self.db_adapter.db.session.add(user)
                    self.db_adapter.db.session.commit()
                    info = "added user {} successfully".format(username)
                else:
                    info = "user exists: {}".format(username)
            else:
                info = "invalid role: '{}' doesn't exist".format(role)
        except Exception as e:
            logging.warning(e)
            info = "add user failed"
        return info

    def del_user(self, username):
        info = "query failed"
        try:
            user_object = User.query.filter(User.username == username).first()
            if user_object is not None:
                self.db_adapter.delete_object(user_object)
                self.db_adapter.db.session.commit()              
                info = "user deleted: {}".format(username)
            else:
                info = "user not found: {}".format(username)
        except Exception as e:
            logger.warning(e)
            info = "delete user failed"
        return info

    def toggle_active(self, username):
        info = "query failed"
        try:
            user_object = User.query.filter(User.username == username).first()
            if user_object is not None:
                if user_object.is_active():
                    user_object.set_active(False)
                    self.db_adapter.db.session.commit()
                    info = "user deactivated: {}".format(username)
                else:
                    user_object.set_active(True)
                    self.db_adapter.db.session.commit()
                    info = "user activated: {}".format(username)
            else:
                info = "user not found: {}".format(username)
        except Exception as e:
            logger.warning(e)
            info = "delete user failed"
        return info
        

    def get_user_by_apikey(self, apikey):
        return self.db_adapter.find_first_object(User, apikey=apikey)

    def get_user_list(self):
        return self.db_adapter.find_all_objects(User)