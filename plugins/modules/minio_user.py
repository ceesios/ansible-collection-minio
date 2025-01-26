#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from minio import Minio
from minio.error import MinioAdminException
from minio import MinioAdmin
from minio.credentials import StaticProvider
import json
import re

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: minio_user
short_description: Manage MinIO users
description:
    - This module allows you to create, update, and delete users in MinIO.
options:
    endpoint_url:
        description:
            - The URL of the MinIO server.
        required: true
        type: str
    access_key:
        description:
            - Access key for MinIO.
        required: true
        type: str
    secret_key:
        description:
            - Secret key for MinIO.
        required: true
        type: str
    user_name:
        description:
            - Name of the user to manage.
        required: true
        type: str
    password:
        description:
            - Password for the user.
        required: false
        type: str
    state:
        description:
            - The desired state of the user.
        choices: ['present', 'absent']
        default: 'present'
        type: str
author:
    - Cees Moerkerken (@ceesios)
'''

EXAMPLES = r'''
- name: Create a user
  minio_user:
    endpoint_url: "http://minio.example.com"
    access_key: "admin_access_key"
    secret_key: "admin_secret_key"
    user_name: "test_user"
    password: "test_password"
    state: "present"

- name: Delete a user
  minio_user:
    endpoint_url: "http://minio.example.com"
    access_key: "admin_access_key"
    secret_key: "admin_secret_key"
    user_name: "test_user"
    state: "absent"
'''

RETURN = r'''
changed:
  description: If any changes were made
  returned: always
  type: bool
message:
  description: Result message
  returned: always
  type: str
diff:
  description: Shows before and after states
  returned: always
  type: dict
'''

def validate_endpoint_url(endpoint_url):
    # Ensure the endpoint URL does not contain a path
    if re.search(r'/', endpoint_url.split('://')[-1]):
        raise ValueError("path in endpoint is not allowed")

def strip_scheme(endpoint_url):
    # Strip https:// or http:// from the endpoint_url
    return re.sub(r'^https?://|^http://', '', endpoint_url)

def derive_use_ssl(endpoint_url):
    # Determine if SSL should be used based on the scheme
    return endpoint_url.startswith('https://')

def set_diff(result, current, desired):
    result['changed'] = True
    result['diff']['before'] = current
    result['diff']['after'] = desired

def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present', 'absent', 'disabled']),
        access_key=dict(type='str', required=True),
        secret_key=dict(type='str', required=True, no_log=True),
        endpoint_url=dict(type='str', required=True),
        user_access_key=dict(type='str', required=True),
        user_secret_key=dict(type='str', required=False, no_log=True)
    )

    result = dict(
        changed=False,
        original_message='',
        message='',
        diff=dict(before='', after='')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ('user_access_key', 'user_secret_key'), True),
       ],
    )

    state = module.params['state']
    access_key = module.params['access_key']
    secret_key = module.params['secret_key']
    endpoint_url = module.params['endpoint_url']
    user_access_key = module.params['user_access_key']
    user_secret_key = module.params['user_secret_key']
    use_ssl = derive_use_ssl(endpoint_url)
    endpoint_url = strip_scheme(endpoint_url)

    try:
        validate_endpoint_url(endpoint_url)
    except ValueError as e:
        module.fail_json(msg=str(e), **result)

    credentials = StaticProvider(access_key, secret_key)
    client = MinioAdmin(endpoint_url, credentials=credentials, secure=use_ssl)

    try:
        user_info = None
        user_exists = False
        try:
            user_info = client.user_info(user_access_key)
            user_exists = True
        except MinioAdminException as e:
            if "XMinioAdminNoSuchUser" not in e._body:
                raise

        current = user_info if user_exists else None
        desired = {
            "access_key": user_access_key,
            "secret_key": user_secret_key,
            "status": "enabled" if state == "present" else "disabled"
        }

        if state == 'present':
            if not user_exists:
                set_diff(result, current, desired)
                if not module.check_mode:
                    try:
                        client.user_add(user_access_key, user_secret_key)
                        result['message'] = f'User {user_access_key} added'
                    except MinioAdminException as e:
                        module.fail_json(msg=f"Failed to add user {user_access_key}: {str(e)}", **result)
            else:
                result['message'] = f'User {user_access_key} already exists'
        elif state == 'disabled':
            if user_exists and user_info.get('status') == 'enabled':
                current_status = current.get('status')
                desired_status = 'disabled'
                if current_status != desired_status:
                    current['status'] = desired_status
                    set_diff(result, user_info, current)
                    if not module.check_mode:
                        try:
                            client.user_disable(user_access_key)
                            result['message'] = f'User {user_access_key} disabled'
                        except MinioAdminException as e:
                            module.fail_json(msg=f"Failed to disable user {user_access_key}: {str(e)}", **result)
            else:
                result['message'] = f'User {user_access_key} is already disabled or does not exist. User info: {user_info}'
        elif state == 'absent':
            if user_exists:
                set_diff(result, current, None)
                if not module.check_mode:
                    try:
                        client.user_remove(user_access_key)
                        result['message'] = f'User {user_access_key} removed'
                    except MinioAdminException as e:
                        module.fail_json(msg=f"Failed to remove user {user_access_key}: {str(e)}", **result)
            else:
                result['message'] = f'User {user_access_key} does not exist. User info: {user_info}'
    except MinioAdminException as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()