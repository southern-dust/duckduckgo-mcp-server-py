#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a port is already in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log "Port $port is already in use"
        return 1
    fi
    return 0
}

# Default values
TRANSPORT_MODE=${TRANSPORT_MODE:-"auto"}
LOG_LEVEL=${LOG_LEVEL:-"INFO"}
HTTP_HOST=${HTTP_HOST:-"0.0.0.0"}
HTTP_PORT=${HTTP_PORT:-8080}
SSE_HOST=${SSE_HOST:-"0.0.0.0"}
SSE_PORT=${SSE_PORT:-8081}

# Log startup information
log "Starting DuckDuckGo MCP Server"
log "Transport mode: $TRANSPORT_MODE"
log "Log level: $LOG_LEVEL"

# Set Python environment
export PYTHONPATH=/app/src
export LOG_LEVEL=$LOG_LEVEL

# Handle different transport modes
case "$TRANSPORT_MODE" in
    "stdio")
        log "Starting with STDIO transport"
        exec python -m duckduckgo_mcp_server.server --transport stdio
        ;;

    "http")
        log "Starting with HTTP transport on $HTTP_HOST:$HTTP_PORT"
        exec python -m duckduckgo_mcp_server.server --transport http --host "$HTTP_HOST" --port "$HTTP_PORT"
        ;;

    "sse")
        log "Starting with SSE transport on $SSE_HOST:$SSE_PORT"
        exec python -m duckduckgo_mcp_server.server --transport sse --host "$SSE_HOST" --port "$SSE_PORT"
        ;;

    "hybrid")
        log "Starting with HYBRID transport (HTTP on $HTTP_PORT, SSE on $SSE_PORT)"
        exec python -m duckduckgo_mcp_server.server --transport hybrid --http-port "$HTTP_PORT" --sse-port "$SSE_PORT"
        ;;

    "auto")
        log "Auto-detecting transport mode based on environment..."

        # Check for specific environment indicators
        if [[ -n "$MCP_CLIENT_ID" ]] || [[ -t 0 ]]; then
            log "Detected STDIO environment, starting with STDIO transport"
            exec python -m duckduckgo_mcp_server.server --transport stdio
        elif [[ -n "$HTTP_ONLY" ]] || [[ "$HTTP_PORT" != "8080" ]]; then
            log "Detected HTTP-only configuration, starting with HTTP transport"
            exec python -m duckduckgo_mcp_server.server --transport http --host "$HTTP_HOST" --port "$HTTP_PORT"
        elif [[ -n "$SSE_ONLY" ]] || [[ "$SSE_PORT" != "8081" ]]; then
            log "Detected SSE-only configuration, starting with SSE transport"
            exec python -m duckduckgo_mcp_server.server --transport sse --host "$SSE_HOST" --port "$SSE_PORT"
        else
            log "No specific transport detected, defaulting to HYBRID mode"
            exec python -m duckduckgo_mcp_server.server --transport hybrid --http-port "$HTTP_PORT" --sse-port "$SSE_PORT"
        fi
        ;;

    "multi")
        log "Starting MULTI-PROCESS mode with all transports"

        # Create background processes for each transport
        python -m duckduckgo_mcp_server.server --transport http --host "$HTTP_HOST" --port "$HTTP_PORT" &
        HTTP_PID=$!
        log "Started HTTP transport (PID: $HTTP_PID)"

        python -m duckduckgo_mcp_server.server --transport sse --host "$SSE_HOST" --port "$SSE_PORT" &
        SSE_PID=$!
        log "Started SSE transport (PID: $SSE_PID)"

        # Wait for services to start
        sleep 2

        # Function to cleanup background processes
        cleanup() {
            log "Shutting down background processes..."
            kill $HTTP_PID $SSE_PID 2>/dev/null || true
            wait $HTTP_PID $SSE_PID 2>/dev/null || true
            log "All processes terminated"
        }

        # Set trap for cleanup on exit
        trap cleanup TERM INT EXIT

        # Health check loop
        log "Health monitoring started"
        while true; do
            # Check if processes are still running
            if ! kill -0 $HTTP_PID 2>/dev/null; then
                log "HTTP transport died, restarting..."
                python -m duckduckgo_mcp_server.server --transport http --host "$HTTP_HOST" --port "$HTTP_PORT" &
                HTTP_PID=$!
            fi

            if ! kill -0 $SSE_PID 2>/dev/null; then
                log "SSE transport died, restarting..."
                python -m duckduckgo_mcp_server.server --transport sse --host "$SSE_HOST" --port "$SSE_PORT" &
                SSE_PID=$!
            fi

            sleep 5
        done
        ;;

    *)
        log "Unknown transport mode: $TRANSPORT_MODE"
        log "Available modes: stdio, http, sse, hybrid, auto, multi"
        exit 1
        ;;
esac