#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIND_CLUSTER_NAME="my-app-cluster"
NAMESPACE="my-app"

teardown_helm() {
    helm uninstall my-app -n "${NAMESPACE}" || true
    kubectl delete namespace "${NAMESPACE}" --ignore-not-found=true || true
}

teardown_kind() {
    kind delete cluster --name "${KIND_CLUSTER_NAME}"
}

teardown_terraform() {
    cd "${PROJECT_ROOT}/terraform"
    aws s3 rm s3://my-app-bucket --endpoint-url http://localhost:4566 --recursive || true
    terraform destroy -auto-approve || true
    rm -rf .terraform terraform.tfstate* .terraform.lock.hcl || true
    cd "${PROJECT_ROOT}"
}

teardown_localstack() {
    localstack stop
}

main() {
    teardown_helm
    teardown_kind
    teardown_terraform
    teardown_localstack
    echo "Teardown Complete!"
}

main
