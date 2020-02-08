import {selectEntities} from "./entitiesReducer";
import {produceActionCreator} from "./utils";
import {setHighlightedClusters} from "./clustersReducer";

const SELECT_MENU = 'SELECT_MENU';

const initialData = {
    properties: {
        important: [],
        interesting: [],
        all: []
    },
    activeItem: 'filter',
    filterMode: 'net'
};

export const setProperties = produceActionCreator('setProperties');
export const changeFilterMode = produceActionCreator('changeFilterMode');

const autoChangeMenu = (state, newMenu) => {
    if (state.activeItem === 'params')
        return state;
    return {
        ...state,
        activeItem: newMenu
    }
};

export function controls(state = initialData, action) {
    switch (action.type) {
        case SELECT_MENU:
            return {
                ...state,
                activeItem: action.name
            };
        case selectEntities.type:
            const entitiesSize = action.payload.length;
            if (state.activeItem === 'params')
                return state;
            if (entitiesSize > 0)
                return autoChangeMenu(state, 'actions');
            return autoChangeMenu(state, 'properties');
        case setProperties.type:
            return {
                ...autoChangeMenu(state, 'properties'),
                properties: action.payload,
            };
        case setHighlightedClusters.type:
            let menu = action.payload.length ? 'actions' : 'properties';
            return autoChangeMenu(state, menu);
        case changeFilterMode.type:
            return {
                ...state,
                filterMode: action.payload
            };
        default:
            return state
    }
}

export const selectMenu = (menuName) => ({type: SELECT_MENU, name: menuName});

