import { createInstance } from 'localforage';

export enum StorageKeys {
    NETWORK,
    LAST_OPENED_TOPOLOGY_ID,
}

class NetworkStorage {
    storageCache = new Map<string, any>();
    storageDriver;

    constructor() {
        this.storageDriver = createInstance({
            description: 'Simulation Network storage',
            name: 'SimStore',
        })
    }

    async getNetwork(networkName = 'default') {
        const key = StorageKeys.NETWORK.toString()+' __||__' + networkName;
        if(this.storageCache.has(key)) return this.storageCache.get(key);

        return await this.storageDriver.getItem(key);
    }

    async setNetwork(networkName = 'default', data: Object) {
        const key = StorageKeys.NETWORK.toString()+' __||__' + networkName;

        this.storageCache.set(key, data);
        this.storageDriver.setItem(key, data);
    }

    async getLastOpenedTopologyID() {
        const key = StorageKeys.LAST_OPENED_TOPOLOGY_ID.toString();
        if(this.storageCache.has(key)) return this.storageCache.get(key);

        return await this.storageDriver.getItem(key);
    }

    async setLastOpenedTopologyID(id: string) {
        const key = StorageKeys.LAST_OPENED_TOPOLOGY_ID.toString();

        this.storageCache.set(key, id);
        this.storageDriver.setItem(key, id);
    }
}

export const networkStorage = new NetworkStorage();