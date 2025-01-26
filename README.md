# Ansible Collection for Managing MinIO Resources

This Ansible collection provides modules for managing various resources in MinIO, including users, retention policies, policies, and groups. Each module is designed to facilitate the management of MinIO resources in an automated and efficient manner.

## Modules

### minio_user
- **Description**: Manage MinIO users, including creating, updating, and deleting users, as well as managing their access keys and secret keys.
- **File**: `plugins/modules/minio_user.py`

### minio_retention
- **Description**: Manage retention policies on MinIO buckets. Allows users to set or remove object lock configurations for specified buckets.
- **File**: `plugins/modules/minio_retention.py`

### minio_policy
- **Description**: Manage policies in MinIO. Provides functionality to create, update, and delete policies, as well as assign them to users and groups.
- **File**: `plugins/modules/minio_policy.py`

### minio_group
- **Description**: Manage groups in MinIO. Allows for the creation, updating, and deletion of groups, as well as managing group memberships.
- **File**: `plugins/modules/minio_group.py`

## Documentation

Detailed documentation for each module can be found in the `docs` directory:
- [minio_user](docs/minio_user.md)
- [minio_retention](docs/minio_retention.md)
- [minio_policy](docs/minio_policy.md)
- [minio_group](docs/minio_group.md)

## Testing

Integration tests for each module are located in the `tests/integration` directory. These tests ensure that the modules behave as expected in various scenarios:
- `tests/integration/test_minio_user.yml`
- `tests/integration/test_minio_retention.yml`
- `tests/integration/test_minio_policy.yml`
- `tests/integration/test_minio_group.yml`

## Installation

To install this collection, use the following command:
```
ansible-galaxy collection install <collection_name>
```

Replace `<collection_name>` with the name of the collection.

## Usage

Examples of how to use each module can be found in their respective documentation files.