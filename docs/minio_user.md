# File: /minio/docs/minio_user.md

# MinIO User Module Documentation

## Overview

The `minio_user` module is designed to manage users in a MinIO server. It allows for the creation, updating, and deletion of users, as well as the management of their access keys and secret keys.

## Parameters

- **state**:
  - Type: `str`
  - Required: `true`
  - Choices: `present`, `absent`
  - Description: Defines whether to ensure the user is present or absent.

- **access_key**:
  - Type: `str`
  - Required: `true`
  - Description: The access key for the MinIO user.

- **secret_key**:
  - Type: `str`
  - Required: `true`
  - Description: The secret key for the MinIO user.

- **endpoint_url**:
  - Type: `str`
  - Required: `true`
  - Description: The MinIO endpoint including the scheme (http/https).

- **user_access_key**:
  - Type: `str`
  - Required: `true`
  - Description: The access key of the user to be managed.

- **user_secret_key**:
  - Type: `str`
  - Required: `true`
  - Description: The secret key of the user to be managed.

## Examples

### Create a User

```yaml
- name: Create a MinIO user
  minio_user:
    state: present
    access_key: minio
    secret_key: minio123
    endpoint_url: "https://play.min.io:9000"
    user_access_key: newuser
    user_secret_key: newpassword
```

### Delete a User

```yaml
- name: Delete a MinIO user
  minio_user:
    state: absent
    access_key: minio
    secret_key: minio123
    endpoint_url: "https://play.min.io:9000"
    user_access_key: olduser
```

## Return Values

- **changed**: Indicates if any changes were made.
- **message**: A message describing the result of the operation.
- **diff**: Shows the before and after states of the user configuration.