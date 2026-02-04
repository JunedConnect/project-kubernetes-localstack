#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIND_CLUSTER_NAME="my-app-cluster"
NAMESPACE="my-app"

start_localstack() {
    localstack start -d
    sleep 30
}

deploy_terraform() {
    cd "${PROJECT_ROOT}/terraform"
    terraform init -upgrade
    terraform apply -auto-approve
    cd "${PROJECT_ROOT}"
}

create_kind_cluster() {
    kind create cluster --name "${KIND_CLUSTER_NAME}" --config "${PROJECT_ROOT}/kind-config.yaml"
    kubectl wait --for=condition=ready nodes --all --timeout=60s
}

build_and_load_image() {
    docker build -t my-app:latest "${PROJECT_ROOT}/app"
    kind load docker-image my-app:latest --name "${KIND_CLUSTER_NAME}"
}

deploy_helm() {
    kubectl create namespace "${NAMESPACE}" || true
    helm upgrade --install my-app "${PROJECT_ROOT}/helm-chart/my-app" \
        --namespace "${NAMESPACE}" \
        --wait --timeout 60s
}

verify_deployment() {
    kubectl wait --for=condition=ready pod -l app=my-app -n "${NAMESPACE}" --timeout=60s
    kubectl get pods -n "${NAMESPACE}"
}

main() {
    start_localstack
    deploy_terraform
    create_kind_cluster
    build_and_load_image
    deploy_helm
    verify_deployment
    echo "Setup Complete!"
}

main
