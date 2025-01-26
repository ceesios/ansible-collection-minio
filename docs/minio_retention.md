# File: /minio/docs/minio_retention.md

# MinIO Retention Module Documentation

## Overview

The `minio_retention` module allows you to manage retention policies on MinIO buckets. It enables you to set or remove object lock configurations for specified buckets, ensuring that objects are retained for a defined period.

## Description
This document describes how to use the **minio_retention** Ansible module to set, update, or remove retention policies for objects in MinIO.

## Parameters

- **state**:
  - Type: `str`
  - Required: `true`
  - Choices: `present`, `absent`
  - Description: Define whether to ensure the retention is present or absent.

- **bucket_name**:
  - Type: `str`
  - Required: `true`
  - Description: Name of the bucket to manage.

- **retention_mode**:
  - Type: `str`
  - Required: `true`
  - Description: Retention mode, e.g., `GOVERNANCE` or `COMPLIANCE`.

- **retention_days**:
  - Type: `int`
  - Required: `true`
  - Description: Retention period in days.

- **access_key**:
  - Type: `str`
  - Required: `true`
  - Description: MinIO access key.

- **secret_key**:
  - Type: `str`
  - Required: `true`
  - Description: MinIO secret key.

- **endpoint_url**:
  - Type: `str`
  - Required: `true`
  - Description: MinIO endpoint including the scheme (http/https).

## Examples

### Set Retention in GOVERNANCE Mode

```yaml
- name: Set retention in GOVERNANCE mode
  minio_retention:
    state: present
    bucket_name: my-bucket
    retention_mode: GOVERNANCE
    retention_days: 30
    access_key: minio
    secret_key: minio123
    endpoint_url: "https://play.min.io:9000"
```

### Remove Retention

```yaml
- name: Remove retention
  minio_retention:
    state: absent
    bucket_name: my-bucket
    access_key: minio
    secret_key: minio123
    endpoint_url: "http://play.min.io:9000"
```

### Set Retention on a Bucket

```yaml
- name: Set retention on a bucket
  minio_retention:
    endpoint_url: "https://minio.example.com:9000"
    access_key: "ACCESS_KEY"
    secret_key: "SECRET_KEY"
    bucket_name: "example-bucket"
    retention_mode: "GOVERNANCE"
    retention_days: 30
    # Additional tasks...
```

## Return Values

- **changed**: Indicates if any changes were made.
- **message**: Result message.
- **diff**: Shows before and after states.