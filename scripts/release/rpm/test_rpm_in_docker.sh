#!/usr/bin/env bash

# This script should be run in a centos7 docker.
set -exv

export USERNAME=azureuser

yum --nogpgcheck localinstall /mnt/rpm/$RPM_NAME -y

yum install git gcc python3-devel findutils -y

ln -s -f /usr/bin/python3 /usr/bin/python
ln -s -f /usr/bin/pip3 /usr/bin/pip
time az self-test
time az --version

cd /azure-cli/
pip3 install wheel
./scripts/ci/build.sh
pip3 install pytest --prefix /usr/lib64/az
pip3 install pytest-xdist --prefix /usr/lib64/az

# From Fedora36, when using `pip install --prefix`with root, the package is installed into `{prefix}/local/lib`.
# Making a copy of the modules to make sure tests can be added later.
# Ref https://docs.fedoraproject.org/en-US/fedora/latest/release-notes/developers/Development_Python/
cp -r /usr/lib64/az/lib /usr/lib64/az/local/lib/

find /azure-cli/artifacts/build -name "azure_cli_testsdk*" | xargs pip3 install --prefix /usr/lib64/az --upgrade --ignore-installed
find /azure-cli/artifacts/build -name "azure_cli_fulltest*" | xargs pip3 install --prefix /usr/lib64/az --upgrade --ignore-installed --no-deps

python3 /azure-cli/scripts/release/rpm/test_rpm_package.py
