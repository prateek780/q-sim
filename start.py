def start_server():
    # Import and use eventlet for better performance
    import eventlet
    eventlet.monkey_patch()
    from server.app import get_app
    app, socketio = get_app()
    
    # Run the app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5174, debug=True)

if __name__ == '__main__':
    start_server()