#!/bin/bash
# Background Discovery Service
# Runs autonomous discovery daemon as a background process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/autonomous_discovery.pid"
LOG_FILE="$SCRIPT_DIR/autonomous_discovery.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "✅ Discovery daemon already running (PID: $PID)"
                exit 0
            else
                rm "$PID_FILE"
            fi
        fi
        
        echo "🚀 Starting autonomous discovery daemon..."
        nohup python3 "$SCRIPT_DIR/autonomous_discovery_daemon.py" \
            --mode continuous \
            --delay 3600 \
            --output "$SCRIPT_DIR/autonomous_discoveries" \
            >> "$LOG_FILE" 2>&1 &
        
        echo $! > "$PID_FILE"
        echo "✅ Discovery daemon started (PID: $!)"
        echo "📋 Log file: $LOG_FILE"
        echo "📁 Output: $SCRIPT_DIR/autonomous_discoveries/"
        ;;
    
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ No PID file found. Daemon not running?"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        echo "🛑 Stopping discovery daemon (PID: $PID)..."
        kill $PID 2>/dev/null
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                rm "$PID_FILE"
                echo "✅ Discovery daemon stopped"
                exit 0
            fi
            sleep 1
        done
        
        # Force kill if necessary
        kill -9 $PID 2>/dev/null
        rm "$PID_FILE"
        echo "⚠️  Discovery daemon force-stopped"
        ;;
    
    status)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ Discovery daemon is NOT running"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Discovery daemon is RUNNING (PID: $PID)"
            
            # Show recent discoveries
            DISC_DIR="$SCRIPT_DIR/autonomous_discoveries"
            if [ -d "$DISC_DIR" ]; then
                COUNT=$(find "$DISC_DIR" -name "*.json" | wc -l)
                echo "📊 Total discoveries: $COUNT"
                echo "📁 Output directory: $DISC_DIR"
                
                # Show latest 5 files
                echo ""
                echo "📄 Recent discoveries:"
                ls -lt "$DISC_DIR"/*.json 2>/dev/null | head -5 | awk '{print "   " $9 " (" $6 " " $7 " " $8 ")"}'
            fi
        else
            echo "❌ PID file exists but daemon not running"
            rm "$PID_FILE"
            exit 1
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    single)
        echo "🔬 Running single discovery cycle..."
        python3 "$SCRIPT_DIR/autonomous_discovery_daemon.py" \
            --mode single \
            --output "$SCRIPT_DIR/autonomous_discoveries"
        ;;
    
    logs)
        if [ ! -f "$LOG_FILE" ]; then
            echo "❌ No log file found"
            exit 1
        fi
        
        tail -f "$LOG_FILE"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|status|restart|single|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start autonomous discovery daemon (continuous mode)"
        echo "  stop     - Stop the daemon"
        echo "  status   - Check daemon status and show discoveries"
        echo "  restart  - Restart the daemon"
        echo "  single   - Run one discovery cycle and exit"
        echo "  logs     - Tail the log file"
        exit 1
        ;;
esac

exit 0
