Macaroni REST Server
==========================

Installation
---------------------

The easiest way to get a development version of the service up and running is to use Vagrant and Ansible. This will create a virtual machine using VirtualBox as a provider. To begin, you'll need to install Vagrant, Ansible. and VirtualBox:

* https://www.vagrantup.com/downloads.html
* Install Ansible with 'sudo pip install ansible' (you need Ansible 1.8 or higher)
* https://www.virtualbox.org/wiki/Downloads


Now that you have Vagrant and VirtualBox installed, you need to clone this repo and make a few small changes custom to your environment:

1. Go to deploy/vars/ and make a copy the private_vars.yml.example:

        cd deploy/ansible/vars/
        cp private_vars.yml.example private_vars.yml

2. Edit the private variables (enter your own):

        admin_user: admin@example.org
        admin_pw: Password1
        
        vt_api_keys:
           - apikey1
           - apikey2

3. Move your terminal to the deploy directory and run Vagrant
        
        vagrant up

4. Vagrant will create a virtual machine and then use Ansible to install all dependencies and start the server. You can log in to the server (from the deploy directory) using vagrant ssh:

        vagrant ssh

5. Once Ansible has run through the playbook completely, you will see something like the following in your terminal:

        PLAY RECAP ********************************************************************
		172.28.128.50              : ok=59   changed=16   unreachable=0    failed=0


6. You can verify that the install worked completely by visiting the following URL (if you changed the VM IP in the Vagrantfile, then update this URL accordingly):

		https://172.28.128.50/admin/

Enter the password you configured and you should see a user management page.

7. You can test the REST API by making an HTTP request to the API endpoints:

		https://172.28.128.50/api/search?query=*&apikey=<YOUR_KEY>

**Gotcha! Since ES is running in a single instance, it sometimes takes a few minutes to get ready!**

Troubleshooting the Install
---------------------
Check the Vagrantfile and be sure the settings in it are suitable for your environment. Sometimes turning the VM GUI on is useful. 

Nginx logs are in:

    /var/log/nginx

Gunicorn logs are in:

    /var/log/macaroni/gunicorn.log

Flask logs are in:

    /var/log/macaroni/flask.log


Development Workflow
---------------------

Vagrant makes development easy by syncing the git working copy (sans .git folder) to it's corresponding place on the VM dev server (/home/macaroni/macaroni_server/). This allows you to make changes to the source code on your host machine (in your favorite text editor or IDE) and easily sync these changes with the development server when you're ready. To push changes, from the 'deploy' directory, you can use the following commands:

    vagrant rsync

    vagrant rsync-auto

'rsync-auto' will constantly be checking for changes, whereas 'rsync' will only run once. 

Contact
---------------------
nick@sinkhole.me
