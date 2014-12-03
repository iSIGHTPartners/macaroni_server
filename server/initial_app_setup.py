
from config import ConfigClass

from app_and_db import db, db_adapter, user_manager

from users.datastore import UsersHelper

from users.model import Role

def setup():
    # Create all database tables
    db.create_all()

    users_helper = UsersHelper(db_adapter, user_manager)

    # create roles
    for role in ConfigClass.roles:
        if not Role.query.filter(Role.name==role).first():
            db.session.add(Role(name=role))
    db.session.commit()

    # create admin account
    users_helper.add_user(ConfigClass.admin_email, 
                            ConfigClass.admin_role, 
                            ConfigClass.admin_password)

if __name__ == "__main__":
    setup()

