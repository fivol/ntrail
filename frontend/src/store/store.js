import {applyMiddleware, combineReducers, createStore} from "redux";
import thunk from 'redux-thunk';
import {loadState, saveState} from "./localStorage";
import {workSpace} from "./workSpaceReducer";
import { reducer as formReducer } from 'redux-form'

const reducers = combineReducers({
    workSpace,
    form: formReducer
});

const persistedState = loadState();
console.log('STATE LOADED FROM LOCAL STORAGE', persistedState);

export const store = createStore(
    reducers,
    persistedState,
    applyMiddleware(thunk)
);

store.subscribe(() => {
    saveState(store.getState());
});

window.store = store;

// const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

// export const store = createStore(reducers, composeEnhancers(
//     applyMiddleware(thunk)
// ));



