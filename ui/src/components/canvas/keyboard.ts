import { Canvas } from "fabric";
import * as fabric from 'fabric';
import { ConnectionManager } from "../node/connections/connectionManager";
import { SimulatorNode } from "../node/base/baseNode";
import { getLogger } from "../../helpers/simLogger";
import { ClassicalNetwork } from "../node/network/classicalNetwork";
import { NetworkManager } from "../node/network/networkManager";
import { manager } from "../node/nodeManager";

export class KeyboardListener {
    static #instance: KeyboardListener;
    canvas;
    logger = getLogger("KeyboardListener");

    constructor(canvas: Canvas) {
        this.canvas = canvas;
        this.listenEvents();
    }

    public static getInstance(canvas?: Canvas): KeyboardListener {
        if (!KeyboardListener.#instance && canvas) {
            console.info("Initialized keyboard listener!");
            KeyboardListener.#instance = new KeyboardListener(canvas);
        }

        return KeyboardListener.#instance;
    }

    listenEvents() {
        document.addEventListener("keydown", (event) => {
            if (event.key === "Delete") {
                this.onDelete(event);
            } else if (event.ctrlKey && event.key === "a") {
                event.preventDefault();
                this.selectAllObjects(event);
            }
        });
    }

    selectAllObjects(_: KeyboardEvent) {
        this.canvas.discardActiveObject();
        const selection = new fabric.ActiveSelection(this.canvas.getObjects(), {
            canvas: this.canvas,
        });
        this.canvas.setActiveObject(selection);
        this.canvas.requestRenderAll();
    }

    onDelete(_: KeyboardEvent) {
        const activeObjects = this.canvas.getActiveObjects();
        activeObjects.forEach((activeObject) => {
            if (activeObject) {
                if (activeObject instanceof SimulatorNode) {
                    this.logger.info("Deleting object", (activeObject as any)?.name);
                    this.canvas.remove(activeObject);
                    ConnectionManager.getInstance(this.canvas).removeAllConnectionsIfExists(activeObject as SimulatorNode);
                    manager.removeNode(activeObject.name);
                } else if (activeObject instanceof ClassicalNetwork) {
                    NetworkManager.getInstance().deleteNetwork(activeObject);
                }
            }
        });
        if (activeObjects.length > 0) {
            this.canvas.discardActiveObject();
            this.canvas.requestRenderAll();
        }
    }
}