# File: /minio/docs/minio_policy.md

# MinIO Policy Module Documentation

## Overview

The `minio_policy` module allows you to manage policies in MinIO. You can create, update, and delete policies, as well as assign them to users and groups.

## Parameters

- **endpoint_url**:
  - Type: `str`
  - Required: `true`
  - Description: The URL of the MinIO server.

- **access_key**:
  - Type: `str`
  - Required: `true`
  - Description: Access key for MinIO.

- **secret_key**:
  - Type: `str`
  - Required: `true`
  - Description: Secret key for MinIO.

- **policy_name**:
  - Type: `str`
  - Required: `true`
  - Description: Name of the policy to manage.

- **statements**:
  - Type: `list`
  - Required: `false`
  - Elements: `dict`
  - Default: `None`
  - Description: List of policy statements in dictionary format.

- **state**:
  - Type: `str`
  - Required: `false`
  - Choices: `present`, `absent`
  - Default: `present`
  - Description: Desired state of the policy.

- **users**:
  - Type: `list`
  - Required: `false`
  - Elements: `str`
  - Description: List of users to associate with this policy.

- **groups**:
  - Type: `list`
  - Required: `false`
  - Elements: `str`
  - Description: List of groups to associate with this policy.

## Examples

```yaml
- name: Add or remove a policy
  minio_policy:
    endpoint_url: "https://minio.example.com:9000"
    access_key: "ACCESS_KEY"
    secret_key: "SECRET_KEY"
    policy_name: "my_policy"
    statements:
      - Effect: Allow
        Action:
          - "s3:GetBucketLocation"
          - "s3:GetObject"
        Resource:
          - "arn:aws:s3:::mybucket/*"
    state: present
    users:
      - "test-user"
    groups:
      - "test-group"
```