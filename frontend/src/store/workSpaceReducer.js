import {addClusters, clusters, makeClusterSelected, processServerResponse, selectCluster} from "./clustersReducer";
import {entities, selectEntities, setEntities, toggleEntitySelection} from "./entitiesReducer";
import {mergeObjectsDepth2, produceActionCreator} from "./utils";
import {controls, setProperties} from "./controlsReducer";
import {makeInputPlaceholder, search} from "./searchReducer";

export const clearAll = produceActionCreator('CLEAR_ALL');


const initData = {
    clusters: undefined,
    entities: undefined,
    controls: undefined,
    search: undefined,
    objects: {}
};

export const workSpace = (state = initData, action) => {
    console.log('ACTION', action);
    switch (action.type) {
        case clearAll.type:
            return {
                clusters: clusters(undefined, action),
                entities: entities(undefined, action),
                controls: controls(undefined, action),
                search: search(undefined, action),
                objects: {}
            };
        case processServerResponse.type:
            return {
                ...state,
                clusters: clusters(state.clusters, addClusters({
                    ...action.payload.response.result.clusters,
                    source: action.payload.source
                })),
                objects: mergeObjectsDepth2(state.objects, action.payload.response.entities),
            };
        case selectCluster.type:
            const clusterID = action.payload;
            const clusterData = state.objects.clusters[clusterID];
            return {
                ...state,
                search: search(state.search, makeInputPlaceholder(clusterData.params.query)),
                clusters: clusters(state.clusters, makeClusterSelected(clusterID)),
                entities: entities(state.entities, setEntities(clusterData.entities)),
                controls: controls(state.controls, setProperties(clusterData.properties))
            };
        case toggleEntitySelection.type:
            const itemID = action.payload;
            let newSelectedItems = [];
            const selectedItems = state.entities.selectedItems;
            if(selectedItems.includes(itemID))
                newSelectedItems =  selectedItems.filter(item=>item !== itemID);
            else
                newSelectedItems = [...selectedItems, itemID];
            const newAction = selectEntities(newSelectedItems);
            return {
                ...state,
                entities: entities(state.entities, newAction),
                controls: controls(state.controls, newAction)
            };
        default:
            return {
                ...state,
                clusters: clusters(state.clusters, action),
                entities: entities(state.entities, action),
                controls: controls(state.controls, action),
                search: search(state.search, action)
            }

    }
};

