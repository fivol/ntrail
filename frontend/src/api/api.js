import axios from "axios";
import {apiHost} from "../config";
import {normalize, schema} from "normalizr";

const server = axios.create(
    {
        baseURL: apiHost,
        // withCredentials: true,
    }
);

const normalizeSelectiveQuery = (responseJson) => {
    const entity = new schema.Entity('entities');
    const cluster = new schema.Entity('clusters', {
        'entities': {
            'items': [entity]
        }
    });
    const mySchema = {
        'clusters': {
            'items': [cluster]
        }
    };
    return normalize(responseJson, mySchema)
};

export const executeSelectiveQuery = (queryString) => (
    server.get(`/query/?q=${queryString}`).then(
        response => normalizeSelectiveQuery(response.data.data)
    )
);




