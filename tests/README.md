# This file provides documentation for the tests directory, explaining how to run the tests and their purpose.

## Tests Directory Overview

The `tests` directory contains integration tests for the Ansible collection managing MinIO resources. These tests ensure that the modules function as expected in various scenarios.

### Running Tests

To run the integration tests, you can use the following command:

```bash
ansible-playbook tests/integration/test_minio_user.yml
ansible-playbook tests/integration/test_minio_retention.yml
ansible-playbook tests/integration/test_minio_policy.yml
ansible-playbook tests/integration/test_minio_group.yml
```

Make sure you have the necessary environment set up and that MinIO is accessible with the correct credentials.

### Purpose of Tests

- **User Management Tests**: Validate the functionality of the `minio_user` module, including user creation, updating, and deletion.
- **Retention Policy Tests**: Ensure that the `minio_retention` module correctly sets and removes retention policies on MinIO buckets.
- **Policy Management Tests**: Check that the `minio_policy` module can create, update, and delete policies, as well as assign them to users and groups.
- **Group Management Tests**: Verify the functionality of the `minio_group` module, including group creation, updating, and membership management.

These tests are crucial for maintaining the reliability and correctness of the modules as changes are made to the codebase.