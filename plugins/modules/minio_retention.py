#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from minio import Minio
from minio.error import S3Error, MinioAdminException
from minio.credentials import StaticProvider
from minio.objectlockconfig import ObjectLockConfig, DAYS, YEARS
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
module: minio_retention
short_description: Manage object retention in MinIO
description:
    - This module sets, updates, or removes retention policies for objects in MinIO.
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
    bucket_name:
        description:
            - The name of the bucket for which to set retention.
        required: true
        type: str
    retention_mode:
        description:
            - The retention mode (e.g., GOVERNANCE or COMPLIANCE).
        required: true
        type: str
    retention_days:
        description:
            - The number of days to retain objects.
        required: true
        type: int
author:
    - Cees Moerkerken (@ceesios)
'''

EXAMPLES = r'''
- name: Set retention on a bucket
  minio_retention:
    endpoint_url: "http://play.min.io:9000"
    access_key: "minio"
    secret_key: "minio123"
    bucket_name: "example-bucket"
    retention_mode: "GOVERNANCE"
    retention_days: 30
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
    """Raise ValueError if endpoint contains a path component."""
    if re.search(r'/', endpoint_url.split('://')[-1]):
        raise ValueError("path in endpoint is not allowed")

def strip_scheme(endpoint_url):
    """Remove scheme (http:// or https://) from endpoint URL."""
    return re.sub(r'^https?://', '', endpoint_url)

def derive_use_ssl(endpoint_url):
    """Return True if endpoint_url starts with https."""
    return endpoint_url.startswith('https://')

def set_retention(client, bucket_name, retention_mode, retention_days):
    """
    Call 'set_object_lock_config' instead of 'set_object_lock_configuration'
    to avoid the AttributeError.
    """
    lock_config = ObjectLockConfig(
        retention_mode.upper(),
        retention_days,
        DAYS
    )
    # Use the correct method name here:
    client.set_object_lock_config(bucket_name, lock_config)

def remove_retention(client, bucket_name):
    """
    Remove object lock configuration by setting an empty ObjectLockConfig.
    """
    lock_config = ObjectLockConfig(None, None, None)
    client.set_object_lock_config(bucket_name, lock_config)

def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        bucket_name=dict(type='str', required=True),
        retention_mode=dict(type='str', required=False),
        retention_days=dict(type='int', required=False),
        access_key=dict(type='str', required=True, no_log=True),
        secret_key=dict(type='str', required=True, no_log=True),
        endpoint_url=dict(type='str', required=True)
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
            ('state', 'present', ('retention_mode', 'retention_days'), True),
       ],
    )

    state = module.params['state']
    bucket_name = module.params['bucket_name']
    retention_mode = module.params['retention_mode']
    retention_days = module.params['retention_days']
    access_key = module.params['access_key']
    secret_key = module.params['secret_key']
    endpoint_url = module.params['endpoint_url']

    try:
        validate_endpoint_url(endpoint_url)
    except ValueError as e:
        module.fail_json(msg=str(e), **result)

    use_ssl = derive_use_ssl(endpoint_url)
    endpoint_clean = strip_scheme(endpoint_url)

    client = Minio(
        endpoint_clean,
        access_key=access_key,
        secret_key=secret_key,
        secure=use_ssl
    )

    # For diff support, attempt to retrieve or note existing config (not always possible).
    current_config_json = ""
    desired_config_json = ""

    if state == 'present':
        if retention_mode and retention_days is not None:
            desired_config_data = {
                "Mode": retention_mode.upper(),
                "Duration": retention_days,
                "Unit": DAYS
            }
            desired_config_json = json.dumps(desired_config_data, sort_keys=True)

            result['diff']['before'] = current_config_json
            result['diff']['after'] = desired_config_json
            result['changed'] = True

            if not module.check_mode:
                try:
                    set_retention(client, bucket_name, retention_mode, retention_days)
                except (S3Error, MinioAdminException) as e:
                    module.fail_json(msg=str(e), **result)
            result['message'] = f"Retention set for bucket {bucket_name}"
        else:
            result['message'] = "No retention_mode or retention_days provided; nothing changed."
    else:  # absent
        desired_config_json = json.dumps({}, sort_keys=True)

        result['diff']['before'] = current_config_json
        result['diff']['after'] = desired_config_json
        result['changed'] = True

        if not module.check_mode:
            try:
                remove_retention(client, bucket_name)
            except (S3Error, MinioAdminException) as e:
                module.fail_json(msg=str(e), **result)
        result['message'] = f"Retention removed for bucket {bucket_name}"

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()