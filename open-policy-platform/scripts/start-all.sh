#!/bin/bash
echo "Starting all Open Policy services..."
echo "This will start backend and web application"

# Start backend in background
./start-backend.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start web application in background
./start-web.sh &
WEB_PID=$!

echo "All services started!"
echo "Backend PID: $BACKEND_PID"
echo "Web PID: $WEB_PID"
echo ""
echo "To stop all services, run: kill $BACKEND_PID $WEB_PID"
echo ""
echo "Access the applications:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Web Interface: http://localhost:5173"
echo "  - Admin Interface: http://localhost:5173/admin"

# Wait for user to stop
wait
