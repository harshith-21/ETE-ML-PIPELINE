#!/bin/bash

# =============================================================================
# ETE-ML-PIPELINE Infrastructure Management Script
# Usage: ./main.sh <action> <service>
# =============================================================================

set -e

# Configuration
# export KUBECONFIG=adminkubeconfig.yaml
NAMESPACE="harshith"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

print_success() {
    echo "✅ $1"
}

print_info() {
    echo "ℹ️  $1"
}

print_error() {
    echo "❌ $1"
}

# =============================================================================
# Service Definitions
# =============================================================================

get_service_files() {
    local service=$1
    case $service in
        postgres)
            echo "infra-k8s/1.postgres.yaml"
            ;;
        minio)
            echo "infra-k8s/2b.Minio.yaml"
            ;;
        airflow)
            echo "infra-k8s/2a.airflowconfigmaps.yaml infra-k8s/2.airflow.yaml"
            ;;
        mlflow)
            echo "infra-k8s/3.mlflow.yaml"
            ;;
        bento)
            echo "infra-k8s/4.bento.yaml"
            ;;
        frontend)
            echo "infra-k8s/5.frontend.yaml"
            ;;
        namespace)
            echo "infra-k8s/0.namespace.yaml"
            ;;
        all)
            # Skip namespace creation - create manually if needed: kubectl create namespace harshith
            echo "infra-k8s/1.postgres.yaml infra-k8s/2b.Minio.yaml infra-k8s/2a.airflowconfigmaps.yaml infra-k8s/2.airflow.yaml infra-k8s/3.mlflow.yaml infra-k8s/4.bento.yaml infra-k8s/5.frontend.yaml"
            ;;
        *)
            return 1
            ;;
    esac
}

get_service_deployments() {
    local service=$1
    case $service in
        postgres)
            echo "postgres-airflow postgres-mlflow"
            ;;
        minio)
            echo "minio"
            ;;
        airflow)
            echo "airflow-scheduler airflow-web"
            ;;
        mlflow)
            echo "mlflow"
            ;;
        bento)
            echo "bento-svc"
            ;;
        frontend)
            echo "frontend"
            ;;
        *)
            return 1
            ;;
    esac
}

# =============================================================================
# Action Functions
# =============================================================================

start_service() {
    local service=$1
    print_header "Starting $service"
    
    files=$(get_service_files "$service")
    if [ $? -ne 0 ]; then
        print_error "Unknown service: $service"
        return 1
    fi
    
    for file in $files; do
        if [ -f "$file" ]; then
            print_info "Applying $file..."
            kubectl apply -f "$file"
        fi
    done
    
    print_success "$service started successfully"
}

stop_service() {
    local service=$1
    print_header "Stopping $service"
    
    deployments=$(get_service_deployments "$service")
    if [ $? -ne 0 ]; then
        print_error "Unknown service: $service"
        return 1
    fi
    
    for deployment in $deployments; do
        print_info "Scaling down $deployment..."
        kubectl scale deployment "$deployment" --replicas=0 -n "$NAMESPACE" --ignore-not-found=true
    done
    
    print_success "$service stopped successfully"
}

restart_service() {
    local service=$1
    print_header "Restarting $service"
    
    deployments=$(get_service_deployments "$service")
    if [ $? -ne 0 ]; then
        print_error "Unknown service: $service"
        return 1
    fi
    
    for deployment in $deployments; do
        print_info "Restarting $deployment..."
        kubectl rollout restart deployment "$deployment" -n "$NAMESPACE" 2>/dev/null || print_info "Deployment $deployment not found, skipping..."
    done
    
    print_success "$service restarted successfully"
}

cleanup_service() {
    local service=$1
    print_header "Cleaning up $service"
    
    files=$(get_service_files "$service")
    if [ $? -ne 0 ]; then
        print_error "Unknown service: $service"
        return 1
    fi
    
    for file in $files; do
        if [ -f "$file" ]; then
            print_info "Deleting resources from $file..."
            kubectl delete -f "$file" --ignore-not-found=true
        fi
    done
    
    print_success "$service cleaned up successfully"
}

status_service() {
    local service=$1
    print_header "Status of $service"
    
    deployments=$(get_service_deployments "$service")
    if [ $? -ne 0 ]; then
        print_error "Unknown service: $service"
        return 1
    fi
    
    for deployment in $deployments; do
        echo "─────────────────────────────────────────────────────────────────────"
        echo "Deployment: $deployment"
        echo "─────────────────────────────────────────────────────────────────────"
        kubectl get deployment "$deployment" -n "$NAMESPACE" 2>/dev/null || print_info "Not found"
        echo ""
        kubectl get pods -n "$NAMESPACE" -l app="$deployment" 2>/dev/null || true
        echo ""
    done
}

# =============================================================================
# Bulk Operations
# =============================================================================

start_all() {
    print_header "Starting ALL services"
    
    # Note: Namespace should be created manually: kubectl create namespace harshith
    print_info "Ensure namespace '$NAMESPACE' exists before continuing..."
    sleep 1
    
    start_service "postgres"
    sleep 3
    start_service "minio"
    sleep 3
    start_service "airflow"
    sleep 2
    start_service "mlflow"
    sleep 2
    start_service "bento"
    sleep 2
    start_service "frontend"
    
    print_success "All services started successfully"
}

stop_all() {
    print_header "Stopping ALL services"
    
    stop_service "frontend"
    stop_service "bento"
    stop_service "mlflow"
    stop_service "airflow"
    stop_service "minio"
    stop_service "postgres"
    
    print_success "All services stopped successfully"
}

cleanup_all() {
    print_header "Cleaning up ALL services"
    
    cleanup_service "frontend"
    cleanup_service "bento"
    cleanup_service "mlflow"
    cleanup_service "airflow"
    cleanup_service "minio"
    cleanup_service "postgres"
    
    print_success "All services cleaned up successfully"
}

status_all() {
    print_header "Status of ALL services"
    
    echo ""
    kubectl get all -n "$NAMESPACE"
    echo ""
}

# =============================================================================
# Usage Information
# =============================================================================

show_usage() {
    cat << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ETE-ML-PIPELINE Infrastructure Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage: $0 <action> <service>

Actions:
  start       Deploy and start a service
  stop        Stop a service (scale to 0 replicas)
  restart     Restart a service
  cleanup     Remove a service completely
  status      Show service status

Services:
  postgres    PostgreSQL databases (Airflow + MLflow)
  minio       MinIO object storage
  airflow     Airflow orchestration (scheduler + web)
  mlflow      MLflow experiment tracking
  bento       BentoML model serving
  frontend    FastAPI frontend
  all         All services

Examples:
  $0 start postgres       Start PostgreSQL
  $0 stop airflow         Stop Airflow
  $0 restart minio        Restart MinIO
  $0 cleanup frontend     Remove frontend completely
  $0 status all           Show status of all services
  
  $0 start all            Start all services
  $0 cleanup all          Remove all services

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
    exit 1
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    local action=$1
    local service=$2
    
    # Check if arguments provided
    if [ -z "$action" ] || [ -z "$service" ]; then
        show_usage
    fi
    
    # Handle special case for "all"
    if [ "$service" = "all" ]; then
        case $action in
            start)
                start_all
                ;;
            stop)
                stop_all
                ;;
            restart)
                stop_all
                sleep 2
                start_all
                ;;
            cleanup)
                cleanup_all
                ;;
            status)
                status_all
                ;;
            *)
                print_error "Unknown action: $action"
                show_usage
                ;;
        esac
    else
        case $action in
            start)
                start_service "$service"
                ;;
            stop)
                stop_service "$service"
                ;;
            restart)
                restart_service "$service"
                ;;
            cleanup)
                cleanup_service "$service"
                ;;
            status)
                status_service "$service"
                ;;
            *)
                print_error "Unknown action: $action"
                show_usage
                ;;
        esac
    fi
}

# Run main function
main "$@"
