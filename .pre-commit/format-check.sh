#!/bin/sh

set -e

cd python-spec
black .
isort .
