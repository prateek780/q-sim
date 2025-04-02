from flask_socketio import SocketIO


class SocketServer:
    _instance = None
    _socketio = None
    
    @classmethod
    def get_instance(cls, app=None):
        if cls._instance is None:
            cls._instance = cls()
            # Create the SocketIO instance with CORS enabled
            cls._socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
            
            if app:
                # Register event handlers
                cls._register_handlers()
        elif app and cls._socketio.server is None:
            # If we have a new app and need to initialize
            cls._socketio.init_app(app)
            # Register event handlers
            cls._register_handlers()
            
        return cls._instance
    
    @classmethod
    def _register_handlers(cls):
        """Register all event handlers"""
        @cls._socketio.on('connect')
        def handle_connect():
            print('Client connected')
            
        @cls._socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected')
            
        # Add your custom event handlers here
        @cls._socketio.on('client_message')
        def handle_message(data):
            print(f'Received message: {data}')
            # Echo back to the client
            cls._socketio.emit('server_response', {'status': 'received', 'data': data})
    
    def emit(self, event, data, room=None):
        """
        Emit an event to connected clients
        
        Args:
            event (str): Event name
            data (dict): Event data
            room (str, optional): Specific room to emit to
        """
        if room:
            self._socketio.emit(event, data, room=room)
        else:
            self._socketio.emit(event, data)
    
    def get_socketio(self):
        """Get the SocketIO instance"""
        return self._socketio

# Convenience function to get the socket server
def get_socket_server(app=None):
    return SocketServer.get_instance(app)