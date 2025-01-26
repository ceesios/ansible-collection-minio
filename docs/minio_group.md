# minio_group
Manage MinIO groups.

## Description
This document describes how to use the **minio_group** Ansible module to create, update, or remove MinIO groups. It can also optionally disable a group.

## Parameters

- **endpoint_url**:
  - Type: `str`
  - Required: `true`
  - Description: The URL of the MinIO server (e.g., `https://play.min.io:9000`).

- **access_key**:
  - Type: `str`
  - Required: `true`
  - Description: Access key for MinIO.

- **secret_key**:
  - Type: `str`
  - Required: `false`
  - Description: Secret key for MinIO.

- **group_name**:
  - Type: `str`
  - Required: `true`
  - Description: Name of the group to manage.

- **users**:
  - Type: `list`
  - Required: `false`
  - Elements: `str`
  - Default: `None`
  - Description: List of users to manage within the group.

- **state**:
  - Type: `str`
  - Required: `true`
  - Choices: `present`, `absent`, `disabled`
  - Default: `present`
  - Description: Desired state of the group.

- **cert_check**:
  - Type: `bool`
  - Default: `true`
  - Description: Whether to verify server certificate.

## Examples

### Create a Group with Users
```yaml
- name: Create a group with users
  minio_group:
    state: present
    group_name: my-group
    users:
      - user1
      - user2
    access_key: minio
    secret_key: minio123
    endpoint_url: "https://play.min.io:9000"
```

### Update Group Membership

```yaml
- name: Update group membership
  minio_group:
    state: present
    group_name: my-group
    users:
      - user1
      - user3
    access_key: minio
    secret_key: minio123
    endpoint_url: "https://play.min.io:9000"
```

### Remove a Group

```yaml
- name: Remove a group
  minio_group:
    state: absent
    group_name: my-group
    access_key: minio
    secret_key: minio123
    endpoint_url: "http://play.min.io:9000"
```

### Disable a Group

```yaml
- name: Disable a group
  minio_group:
    state: disabled
    group_name: my-group
    access_key: minio
    secret_key: minio123
    endpoint_url: "http://play.min.io:9000"
```

## Return Values

- **changed**: Indicates if any changes were made.
- **message**: Result message detailing the outcome of the operation.
- **diff**: Shows before and after states of the group configuration.