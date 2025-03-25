#!/bin/bash
# NVIDIA RAG Application - Enterprise Helm Chart Installation Script

set -e

# Default values
NAMESPACE="nvidia-rag"
RELEASE_NAME="nvidia-rag"
ENTERPRISE_MODE="true"
HIGH_AVAILABILITY="true"
MONITORING="true"
CHART_PATH="./nvidia-rag"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --release-name)
      RELEASE_NAME="$2"
      shift 2
      ;;
    --api-key)
      NVIDIA_API_KEY="$2"
      shift 2
      ;;
    --disable-enterprise)
      ENTERPRISE_MODE="false"
      shift
      ;;
    --disable-ha)
      HIGH_AVAILABILITY="false"
      shift
      ;;
    --disable-monitoring)
      MONITORING="false"
      shift
      ;;
    --chart-path)
      CHART_PATH="$2"
      shift 2
      ;;
    --help)
      echo "NVIDIA RAG Application - Enterprise Helm Chart Installation"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --namespace NAME         Kubernetes namespace to deploy to (default: nvidia-rag)"
      echo "  --release-name NAME      Helm release name (default: nvidia-rag)"
      echo "  --api-key KEY            NVIDIA API key (required)"
      echo "  --disable-enterprise     Disable enterprise features"
      echo "  --disable-ha             Disable high availability features"
      echo "  --disable-monitoring     Disable monitoring"
      echo "  --chart-path PATH        Path to Helm chart (default: ./nvidia-rag)"
      echo "  --help                   Display this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check for required API key
if [ -z "$NVIDIA_API_KEY" ]; then
  echo "Error: NVIDIA API key is required. Use --api-key to provide it."
  exit 1
fi

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
  echo "Creating namespace: $NAMESPACE"
  kubectl create namespace "$NAMESPACE"
fi

# Set up NVIDIA Registry credentials if needed
if [ -f "./setup-registry-credentials.sh" ]; then
  echo "Setting up NVIDIA NGC Registry credentials..."
  chmod +x ./setup-registry-credentials.sh
  ./setup-registry-credentials.sh "$NAMESPACE"
fi
# Add Helm repositories
echo "Adding required Helm repositories..."
helm repo add milvus https://milvus-io.github.io/milvus-helm/
helm repo update

# Update dependencies
echo "Updating Helm dependencies..."
helm dependency update "$CHART_PATH"

# Install or upgrade the Helm chart
echo "Deploying NVIDIA RAG application to namespace: $NAMESPACE"
helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
  --namespace "$NAMESPACE" \
  --set secrets.nvidiaapikey.data.NVIDIA_API_KEY="$NVIDIA_API_KEY" \
  --set global.enterprise.enabled="$ENTERPRISE_MODE" \
  --set global.enterprise.highAvailability="$HIGH_AVAILABILITY" \
  --set global.enterprise.monitoring.enabled="$MONITORING" \
  --wait

echo ""
echo "NVIDIA RAG application has been deployed successfully."
echo "To access the application, run the following commands:"
echo ""
echo "  # Access the RAG Server API:"
echo "  kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-rag-server 8081:8081"
echo ""
echo "  # Access the RAG Playground:"
echo "  kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-rag-playground 8090:8090"
echo ""
echo "Then open http://localhost:8090 in your browser."