#!/bin/bash
# NVIDIA RAG Application - Installation Validation Script

set -e

# Default values
NAMESPACE="nvidia-rag"
RELEASE_NAME="nvidia-rag"

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
    --help)
      echo "NVIDIA RAG Application - Installation Validation"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --namespace NAME     Kubernetes namespace to check (default: nvidia-rag)"
      echo "  --release-name NAME  Helm release name (default: nvidia-rag)"
      echo "  --help               Display this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Validating NVIDIA RAG installation in namespace: $NAMESPACE"
echo ""

# Check if namespace exists
echo "Checking namespace..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
  echo "✅ Namespace $NAMESPACE exists"
else
  echo "❌ Namespace $NAMESPACE does not exist"
  exit 1
fi

# Check Helm release
echo ""
echo "Checking Helm release..."
if helm status "$RELEASE_NAME" -n "$NAMESPACE" &> /dev/null; then
  echo "✅ Helm release $RELEASE_NAME exists"
else
  echo "❌ Helm release $RELEASE_NAME does not exist in namespace $NAMESPACE"
  exit 1
fi

# Check pods
echo ""
echo "Checking pods..."
PODS_RUNNING=true
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME" -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}' | while read -r pod status; do
  if [[ "$status" != "Running" && "$status" != "Completed" ]]; then
    echo "❌ Pod $pod is in $status state"
    PODS_RUNNING=false
  else
    echo "✅ Pod $pod is $status"
  fi
done

if [[ "$PODS_RUNNING" == "false" ]]; then
  echo ""
  echo "Some pods are not running. Check the logs for more details:"
  echo "kubectl logs -n $NAMESPACE <pod-name>"
  exit 1
fi

# Check services
echo ""
echo "Checking services..."
RAG_SERVER_SVC="${RELEASE_NAME}-rag-server"
RAG_PLAYGROUND_SVC="${RELEASE_NAME}-rag-playground"

if kubectl get svc -n "$NAMESPACE" "$RAG_SERVER_SVC" &> /dev/null; then
  echo "✅ Service $RAG_SERVER_SVC exists"
else
  echo "❌ Service $RAG_SERVER_SVC does not exist"
  exit 1
fi

if kubectl get svc -n "$NAMESPACE" "$RAG_PLAYGROUND_SVC" &> /dev/null; then
  echo "✅ Service $RAG_PLAYGROUND_SVC exists"
else
  echo "❌ Service $RAG_PLAYGROUND_SVC does not exist"
  exit 1
fi

# Set up port-forwarding and check health endpoint
echo ""
echo "Checking RAG server health endpoint..."

# Start port-forwarding in the background
kubectl port-forward -n "$NAMESPACE" "svc/$RAG_SERVER_SVC" 8081:8081 &> /dev/null &
PF_PID=$!

# Wait for port-forwarding to start
sleep 3

# Check health endpoint
if curl -s http://localhost:8081/api/v1/health &> /dev/null; then
  echo "✅ RAG server health endpoint is accessible"
else
  echo "❌ RAG server health endpoint is not accessible"
  kill $PF_PID
  exit 1
fi

# Kill port-forwarding process
kill $PF_PID

echo ""
echo "✅ Validation completed successfully"
echo ""
echo "To access the application, run the following commands:"
echo ""
echo "  # Access the RAG Server API:"
echo "