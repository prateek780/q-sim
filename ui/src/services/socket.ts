import { io, Socket, ManagerOptions, SocketOptions } from 'socket.io-client';

type MessageHandler = (data: any) => void;
type ErrorHandler = (error: any) => void;
type ConnectHandler = () => void;
type DisconnectHandler = (reason: string) => void;


export enum SocketEvents {
    SimulationEvent = 'simulation_event'
}

/**
 * Singleton SocketIO client
 */
export class SocketIOClient {
    private static instance: SocketIOClient;
    private socket: Socket | null = null;
    private messageHandlers: Map<string, MessageHandler[]> = new Map();
    private connectHandlers: ConnectHandler[] = [];
    private disconnectHandlers: DisconnectHandler[] = [];
    private errorHandlers: ErrorHandler[] = [];
    private url: string | undefined = '';
    private options: Partial<ManagerOptions & SocketOptions> = {};
    private _connecting = false;
    simulationEventLogs: any[] = [];

    /**
     * Private constructor to prevent direct instantiation
     */
    private constructor() {
        // Store Messages in Memory
        this.onMessage(SocketEvents.SimulationEvent, (data) => {
            this.simulationEventLogs.push(data);
        })
    }

    /**
     * Get singleton instance
     */
    public static getInstance(): SocketIOClient {
        if (!SocketIOClient.instance) {
            SocketIOClient.instance = new SocketIOClient();
        }
        return SocketIOClient.instance;
    }

    /**
     * Connect to Socket.IO server
     * 
     * @param url Server URL
     * @param options Connection options
     * @returns Promise that resolves when connected
     */
    public connect(
        url: string | undefined,
        options: Partial<ManagerOptions & SocketOptions> = {}
    ): Promise<void> {
        return new Promise((resolve, reject) => {
            if (this.socket?.connected || this._connecting) {
                return resolve();
            }
            this._connecting = true;

            this.url = url;
            this.options = options;

            try {
                this.socket = io(url, options);

                this.socket.on('connect', () => {
                    console.log('Socket connected');
                    this.connectHandlers.forEach(handler => handler());
                    this._connecting = false;
                    resolve();
                });

                this.socket.on('disconnect', (reason) => {
                    console.log(`Socket disconnected: ${reason}`);
                    this.disconnectHandlers.forEach(handler => handler(reason));
                    this._connecting = false;
                });

                this.socket.on('connect_error', (error) => {
                    console.error('Connection error:', error);
                    this.errorHandlers.forEach(handler => handler(error));
                    this._connecting = false;
                    reject(error);
                });

                // Set up message handlers from the map
                this.messageHandlers.forEach((handlers, event) => {
                    this.socket?.on(event, (data) => {
                        handlers.forEach(handler => handler(data));
                    });
                });
            } catch (error) {
                console.error('Failed to create socket:', error);
                reject(error);
            }
        });
    }

    /**
     * Reconnect to the server using the same URL and options
     */
    public reconnect(): Promise<void> {
        if (this.socket) {
            this.socket.disconnect();
        }
        return this.connect(this.url, this.options);
    }

    /**
     * Disconnect from the server
     */
    public disconnect(): void {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }

    /**
     * Send a message to the server
     * 
     * @param event Event name
     * @param data Data to send
     * @returns Promise that resolves when the message is acknowledged, or void if no ack
     */
    public send<T = any>(
        event: string,
        data?: any
    ): Promise<T | void> {
        return new Promise((resolve, reject) => {
            if (!this.socket || !this.socket.connected) {
                reject(new Error('Socket not connected'));
                return;
            }

            this.socket.emit(event, data, (response: T) => {
                resolve(response);
            });
        });
    }

    /**
     * Register a handler for a specific message event
     * 
     * @param event Event name
     * @param handler Handler function
     */
    public onMessage(event: SocketEvents | string, handler: MessageHandler): void {
        if (!this.messageHandlers.has(event)) {
            this.messageHandlers.set(event, []);

            // If socket exists, add the event listener
            if (this.socket) {
                this.socket.on(event, (data) => {
                    const handlers = this.messageHandlers.get(event) || [];
                    handlers.forEach(h => h(data));
                });
            }
        }

        const handlers = this.messageHandlers.get(event) || [];
        handlers.push(handler);
        this.messageHandlers.set(event, handlers);
    }

    /**
     * Remove a specific handler for a message event
     * 
     * @param event Event name
     * @param handler Handler to remove
     */
    public offMessage(event: string, handler: MessageHandler): void {
        if (!this.messageHandlers.has(event)) return;

        const handlers = this.messageHandlers.get(event) || [];
        const index = handlers.indexOf(handler);

        if (index !== -1) {
            handlers.splice(index, 1);
            this.messageHandlers.set(event, handlers);
        }
    }

    /**
     * Register a connection handler
     * 
     * @param handler Handler function
     */
    public onConnect(handler: ConnectHandler): void {
        this.connectHandlers.push(handler);
    }

    /**
     * Register a disconnect handler
     * 
     * @param handler Handler function
     */
    public onDisconnect(handler: DisconnectHandler): void {
        this.disconnectHandlers.push(handler);
    }

    /**
     * Register an error handler
     * 
     * @param handler Handler function
     */
    public onError(handler: ErrorHandler): void {
        this.errorHandlers.push(handler);
    }

    /**
     * Check if socket is connected
     */
    public isConnected(): boolean {
        return !!(this.socket && this.socket.connected);
    }
}

// Export a default instance
export default SocketIOClient.getInstance();