import {executeQuery, showMessage} from "./searchReducer";
import {executeSelectiveQuery} from "../api/api";
import {getObj, produceActionCreator} from "./utils";
import {clearAll} from "./workSpaceReducer";
import {removeEntitiesLoader} from "./entitiesReducer";
import {queryReplaceGetWithLoad} from "../api/queryStringCreators";

export const addClusters = produceActionCreator('ADD_CLUSTERS');
export const processServerResponse = produceActionCreator('processServerResponse');
export const selectCluster = produceActionCreator('SELECT_CLUSTER');
export const removeClusters = produceActionCreator('REMOVE_CLUSTERS_FROM_PANEL');
export const startLoadingCluster = produceActionCreator('START_LOADING_CLUSTER');
export const makeClusterSelected = produceActionCreator('make_cluster_selected');
export const setHighlightedClusters = produceActionCreator('setHighlightedClusters');

const initialData = {
    items: [],
    connections: [],
    selectedClusterID: null,
    highlightedClusters: []
};

export function clusters(state = initialData, action) {
    switch (action.type) {
        case setHighlightedClusters.type:
            return {
                ...state,
                highlightedClusters: action.payload
            };
        case addClusters.type:
            let newClustersIDS = action.payload.items;
            let newClustersConnections = action.payload.connections;
            let sourceID = action.payload.source;
            let newClustersMainID = action.payload.mainID;

            const getConnID = (connection) => {
                return connection.from + '_' + connection.to;
            };

            if (!newClustersMainID && newClustersIDS.length === 1)
                newClustersMainID = newClustersIDS[0];

            if (sourceID && newClustersMainID) {
                newClustersConnections.push(
                    {
                        'from': sourceID,
                        'to': newClustersMainID
                    }
                )
            }
            newClustersConnections = newClustersConnections.map(item => ({...item, id: getConnID(item)}));
            const existConnectionsIDS = state.connections.map(item => item.id);
            newClustersConnections = newClustersConnections.filter(item => !(existConnectionsIDS.includes(item.id)));

            return {
                ...state,
                items: [
                    ...new Set([...state.items, ...newClustersIDS])
                ],
                connections: [
                    ...state.connections,
                    ...newClustersConnections,
                ]
            };
        case makeClusterSelected.type:
            const clusterID = action.payload;
            return {
                ...state,
                selectedClusterID: clusterID,
            };
        case removeClusters.type:
            const removeClustersIds = action.payload;
            const selectedCluster = state.selectedClusterID;
            const remainingClusters = state.items.filter(id => !removeClustersIds.includes(id));
            return {
                ...state,
                connections: state.connections.filter(
                    conn => !removeClustersIds.includes(conn.from) && !removeClustersIds.includes(conn.to)
                ),
                items: remainingClusters,
                selectedClusterID: removeClustersIds.includes(selectedCluster) ? -1 : selectedCluster,
                highlightedClusters: state.highlightedClusters.filter(id => !removeClustersIds.includes(id))
            };
        default:
            return state
    }
}


export const reloadCluster = () => (dispatch, getState) => {
    const state = getState();
    const id = state.workSpace.clusters.selectedClusterID;
    const clusterQuery = queryReplaceGetWithLoad(getObj(state, 'clusters', id).params.query);
    dispatch(executeQuery(clusterQuery));
    return;
    dispatch(startLoadingCluster());
    executeSelectiveQuery(clusterQuery).then(
        response => {
            dispatch(addClusters(response));
            dispatch(removeEntitiesLoader())
        }
    ).catch(
        response => {
            dispatch(removeEntitiesLoader());
            dispatch(showMessage('Ошибка сети', 'Проверьте подключение к интернету', false, true))
        }
    )
};

export const deleteCluster = () =>
    (dispatch, getState) => {
        const state = getState();
        const clusterID = state.workSpace.clusters.selectedClusterID;
        const remainingClusters = state.workSpace.clusters.items.filter(id => id !== clusterID);
        if (!remainingClusters.length)
            dispatch(clearAll());
        else {
            dispatch(selectCluster(remainingClusters[0]));
            dispatch(removeClusters([clusterID]))
        }
    };