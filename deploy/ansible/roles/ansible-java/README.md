# Java role for Ansible

Installs Java from the webupd8 PPA and applies the specified configuration.

## Requirements

Tested on Ubuntu 12.04 Server.

## Role Variables

	jdk_version: '8'	# Which version of Java to install

## Example Playbook

    - hosts: 'servers'
      roles:
        - role: 'ssilab.java'
          jdk_version: '7'

# License

This playbook is provided 'as-is' under the conditions of the BSD license. No fitness for purpose is guaranteed or implied.