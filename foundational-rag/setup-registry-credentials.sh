#!/bin/bash
# setup-registry-credentials.sh - Configure NVIDIA NGC Registry credentials for Kubernetes

# Set default namespace
NAMESPACE=${1:-nvidia-rag}

# Prompt for NVIDIA API key if not provided
if [ -z "$NVIDIA_API_KEY" ]; then
  read -sp "Enter your NVIDIA API key: " NVIDIA_API_KEY
  echo ""
fi

# Validate input
if [ -z "$NVIDIA_API_KEY" ]; then
  echo "Error: NVIDIA API key is required"
  exit 1
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
  echo "Creating namespace: $NAMESPACE"
  kubectl create namespace "$NAMESPACE"
fi

# Create the Docker registry secret
echo "Creating registry secret in namespace $NAMESPACE..."
kubectl create secret docker-registry nvidia-registry-secret \
  --namespace "$NAMESPACE" \
  --docker-server=nvcr.io \
  --docker-username='$oauthtoken' \
  --docker-password="$NVIDIA_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

# Update the default service account to use this secret
echo "Configuring service account to use registry secret..."
kubectl patch serviceaccount default -n "$NAMESPACE" -p '{"imagePullSecrets": [{"name": "nvidia-registry-secret"}]}'

echo "NVIDIA NGC Registry credentials configured successfully in namespace $NAMESPACE"