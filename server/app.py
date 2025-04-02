import os
from flask import Flask
from flask_cors import CORS

from server.socket_server.socket_server import SocketServer

REACT_BUILD_FOLDER = "../ui/dist"

# Create a new app factory function
def get_app():
    app = Flask(__name__, static_folder=REACT_BUILD_FOLDER)
    CORS(app, origins='*')
    
    # Register routes
    from server.routes import register_routes
    register_routes(app)
    
    # Initialize SocketIO with the app
    socket_server = SocketServer.get_instance(app)
    
    return app, socket_server.get_socketio()

# Convenience function to get the socket server
def get_socket_server(app=None):
    return SocketServer.get_instance(app)
