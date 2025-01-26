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
module: minio_group
short_description: Manage MinIO groups
description:
    - This module allows you to create, update, and delete groups in MinIO.
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
    group_name:
        description:
            - Name of the group to manage.
        required: true
        type: str
    users:
        description:
            - List of users to be added to the group.
        required: false
        type: list
        elements: str
    state:
        description:
            - The desired state of the group.
        choices: ['present', 'absent']
        default: 'present'
        type: str
author:
    - Cees Moerkerken (@ceesios)
'''

EXAMPLES = r'''
- name: Create a group with users
  minio_group:
    endpoint_url: "http://minio.example.com"
    access_key: "your_access_key"
    secret_key: "your_secret_key"
    group_name: "example_group"
    users:
      - user1
      - user2
    state: "present"

- name: Delete a group
  minio_group:
    endpoint_url: "http://minio.example.com"
    access_key: "your_access_key"
    secret_key: "your_secret_key"
    group_name: "example_group"
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
    if re.search(r'\/', endpoint_url.split('://')[-1]):
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
        secret_key=dict(type='str', required=False, no_log=True),
        endpoint_url=dict(type='str', required=True),
        cert_check=dict(type='bool', default=True),
        group_name=dict(type='str', required=True),
        users=dict(type='list', required=False, elements='str', default=None)
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
        required_if=[],
    )

    state = module.params['state']
    access_key = module.params['access_key']
    secret_key = module.params['secret_key']
    endpoint_url = module.params['endpoint_url']
    cert_check = module.params['cert_check']
    group_name = module.params['group_name']
    users = module.params['users']
    use_ssl = derive_use_ssl(endpoint_url)
    endpoint_url = strip_scheme(endpoint_url)

    try:
        validate_endpoint_url(endpoint_url)
    except ValueError as e:
        module.fail_json(msg=str(e), **result)

    credentials = StaticProvider(access_key, secret_key)
    client = MinioAdmin(endpoint_url, credentials=credentials, secure=use_ssl, cert_check=cert_check)

    try:
        group_info = None
        group_exists = False
        try:
            group_info = client.group_info(group_name)
            group_info = json.loads(group_info)  # Ensure group_info is a dictionary
            group_info.pop("updatedAt")  # Remove updatedAt from current
            group_info.pop("policy")  # Remove policy from current
            if users is None:
                group_info.pop("members") # Ignore members if users is None
            group_info_sorted = dict(sorted(group_info.items()))
            group_exists = True
        except MinioAdminException as e:
            if "XMinioAdminNoSuchGroup" not in e._body:
                raise
        current = group_info_sorted if group_exists else None

        desired_unsorted = {
            "name": group_name,
            "members": users,
            "status": "enabled" if state == "present" else "disabled"
        }
        desired = dict(sorted(desired_unsorted.items()))

        if users is None:
            desired.pop("members")

        if state == 'present':
            if not group_exists:
                set_diff(result, current, desired)
                if not module.check_mode:
                    try:
                        client.group_add(group_name,users)
                        result['message'] = f'Group {group_name} created and users added'
                    except MinioAdminException as e:
                        module.fail_json(msg=f"Failed to add group {group_name}: with users: {users} {str(e)}", **result)
            else:
                if group_info["status"] == 'disabled':
                    set_diff(result, current, desired)
                    if not module.check_mode:
                        try:
                            client.group_enable(group_name)
                            result['message'] = f'Group {group_name} enabled'
                        except MinioAdminException as e:
                            module.fail_json(msg=f"Failed to enable group {group_name}: {str(e)}", **result)
                elif users is not None:
                    if current["members"] is None:
                        current_members = set([])
                    else:
                        current_members = set(current["members"])
                    desired_members = set(users)
                    if current_members != desired_members:
                        set_diff(result, current, desired)
                        if not module.check_mode:
                            try:
                                members_to_add = desired_members - current_members
                                members_to_remove = current_members - desired_members
                                if members_to_add:
                                    client.group_add(group_name,list(members_to_add))
                                if members_to_remove:
                                    client.group_remove(group_name,list(members_to_remove))
                                result['message'] = f'Group {group_name} members updated'
                            except MinioAdminException as e:
                                module.fail_json(msg=f"Failed to update members of group {group_name}: {str(e)}", **result)
                    else:
                        result['message'] = f'Group {group_name} already exists and members are up to date'
        elif state == 'absent':
            if group_exists:
                set_diff(result, current, "")
                if not module.check_mode:
                    try:
                        client.group_remove(group_name)
                        result['message'] = f'Group {group_name} removed'
                    except MinioAdminException as e:
                        module.fail_json(msg=f"Failed to remove group {group_name}: {str(e)}", **result)
            else:
                result['message'] = f'Group {group_name} does not exist. Group info: {group_info}'
    except MinioAdminException as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()