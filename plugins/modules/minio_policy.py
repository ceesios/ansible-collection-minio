#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from minio import Minio
from minio.error import S3Error, MinioAdminException
from minio import MinioAdmin
from minio.credentials import StaticProvider
import json
import re
import tempfile
import yaml

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: minio_policy
short_description: Manage MinIO policies
description:
    - This module allows you to create, update, and delete policies in MinIO.
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
    policy_name:
        description:
            - Name of the policy to manage.
        required: true
        type: str
    statements:
        description:
            - List of policy statements in dictionary format.
        required: false
        type: list
        elements: dict
    state:
        description:
            - The desired state of the policy.
        choices: ['present', 'absent']
        default: 'present'
        type: str
    users:
        description:
            - List of users to be associated with the policy.
        required: false
        type: list
        elements: str
    groups:
        description:
            - List of groups to be associated with the policy.
        required: false
        type: list
        elements: str
author:
    - Cees Moerkerken (@ceesios)
'''

EXAMPLES = r'''
- name: Add or remove a policy
  minio_policy:
    endpoint_url: 'https://minio.example.com:9000'
    secret_key: "SECRET_KEY"
    access_key: "ACCESS_KEY"
    policy_name: "my_policy"
    statements:
      - Effect: Allow
        Action:
          - 's3:GetBucketLocation'
          - 's3:GetObject'
          - 's3:ListAllMyBuckets'
          - 's3:ListBucket'
        Resource:
          - "arn:aws:s3:::mybucket/*"
    state: present
    users:
      - "test-user"
    groups:
      - "test-group"
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

def sort_yaml(yaml_str):
    # Sort the keys in the YAML representation and sort actions and resources lists.
    data = yaml.safe_load(yaml_str)

    def sort_lists(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k.lower() in ['action', 'resource'] and isinstance(v, list):
                    d[k] = sorted(v)
                else:
                    d[k] = sort_lists(v)
        elif isinstance(d, list):
            return [sort_lists(i) for i in d]
        return d

    sorted_data = sort_lists(data)
    return yaml.dump(sorted_data, default_flow_style=False, sort_keys=True)

def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        policy_name=dict(type='str', required=True),
        statements=dict(type='list', required=False, elements='dict'),
        access_key=dict(type='str', required=True, no_log=True),
        secret_key=dict(type='str', required=True, no_log=True),
        endpoint_url=dict(type='str', required=True),
        users=dict(type='list', required=False, elements='str'),
        groups=dict(type='list', required=False, elements='str')
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
            ('state', 'present', ('statements', 'policy_name'), True),
       ],
    )

    state = module.params['state']
    policy_name = module.params['policy_name']
    statements = module.params['statements']
    access_key = module.params['access_key']
    secret_key = module.params['secret_key']
    endpoint_url = module.params['endpoint_url']
    users = module.params['users']
    groups = module.params['groups']
    use_ssl = derive_use_ssl(endpoint_url)
    endpoint_url = strip_scheme(endpoint_url)

    try:
        validate_endpoint_url(endpoint_url)
    except ValueError as e:
        module.fail_json(msg=str(e), **result)

    credentials = StaticProvider(access_key, secret_key)
    client = MinioAdmin(endpoint_url, credentials=credentials, secure=use_ssl)

    policy_document_json = json.dumps({"Version": "2012-10-17", "Statement": statements})
    desired_policy = json.loads(policy_document_json)
    desired_policy_yaml = sort_yaml(yaml.dump(desired_policy, default_flow_style=False))
    current_policy_yaml = None

    try:
        try:
            current_policy_json = client.policy_info(policy_name)
            current_policy = json.loads(current_policy_json)
            current_policy_yaml = sort_yaml(yaml.dump(current_policy, default_flow_style=False))

        except MinioAdminException as e:
            if "XMinioAdminNoSuchPolicy" not in e._body:
                raise

        result['diff']['before'] = current_policy_yaml
        result['diff']['after'] = desired_policy_yaml

        if state == 'present':
            if current_policy_yaml != desired_policy_yaml:
                result['changed'] = True
                if not module.check_mode:
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_policy_file:
                        tmp_policy_file.write(policy_document_json.encode())
                        tmp_policy_file.flush()
                        client.policy_add(policy_name, tmp_policy_file.name)
                    result['message'] = f'Policy {policy_name} created'
            else:
                result['message'] = f'Policy {policy_name} is already up to date'

            if users:
                for user in users:
                    client.policy_set(policy_name, user=user)
                result['message'] += f' and users {users} added'

            if groups:
                for group in groups:
                    client.policy_set(policy_name, group=group)
                result['message'] += f' and groups {groups} added'

        elif state == 'absent':
            result['diff']['after'] = ''
            if current_policy_yaml is not None:
                result['changed'] = True
                if not module.check_mode:
                    client.policy_remove(policy_name)
                    result['message'] = f'Policy {policy_name} deleted'

            if users:
                for user in users:
                    client.policy_unset(policy_name, user=user)
                result['message'] += f' and users {users} removed'

            if groups:
                for group in groups:
                    client.policy_unset(policy_name, group=group)
                result['message'] += f' and groups {groups} removed'

    except MinioAdminException as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()