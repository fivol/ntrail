import {produceActionCreator} from "./utils";
import {addClusters, startLoadingCluster} from "./clustersReducer";

export const selectEntities = produceActionCreator('SELECT_ENTITIES');
export const toggleEntitySelection = produceActionCreator('TOGGLE_ENTITY_SELECTION');
export const setEntities = produceActionCreator('setEntities');
export const removeEntitiesLoader = produceActionCreator('removeLoader');
export const setEntitiesSearchValue = produceActionCreator('setSearchValue');
export const setEntitiesItemsList = produceActionCreator('setEntitiesItemsList');

const initialData = {
    isLoading: false,
    selectedItems: [],
    items: [],
    connections: {},
    searchValue: ''
};

export function entities(state = initialData, action) {
    switch (action.type) {
        case setEntitiesItemsList.type:
            return {
                ...state,
                searchValue: action.payload.join(', ')
            };
        case setEntitiesSearchValue.type:
            return {
                ...state,
                searchValue: action.payload
            };
        case removeEntitiesLoader.type:
            return {
                ...state,
                isLoading: false
            };
        case addClusters.type:
            return {
                ...state,
                isLoading: false,
            };
        case startLoadingCluster.type:
            return {
                ...state,
                isLoading: true
            };
        case selectEntities.type:
            return {
                ...state,
                selectedItems: action.payload
            };
        case toggleEntitySelection.type:
            const itemID = action.payload;
            if(state.selectedItems.includes(itemID))
                return {
                ...state,
                    selectedItems: state.selectedItems.filter(item=>item !== itemID)
                };
            else
                return {
                ...state,
                    selectedItems: [...state.selectedItems, itemID]
                };
        case setEntities.type:
            return {
                ...state,
                items: action.payload.items,
                connections: action.payload.connections,
                selectedItems: [],
                searchValue: ''
            };
        default:
            return state
    }
}


