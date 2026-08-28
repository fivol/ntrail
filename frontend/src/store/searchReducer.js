import {textConstants} from "../constants";
import {executeSelectiveQuery} from "../api/api";
import {addClusters, processServerResponse, selectCluster} from "./clustersReducer";
import {produceActionCreator} from "./utils";

const initialData = {
    queryString: '',
    allHints: ["https://",
        "vk.com/",
        "instagram.com/",
        "me",
        'GET',
        'LOAD',
        'vk.user',
        'vk.users',
        'ig.user',
        'ig.users',
        "age",
        "school",
        "sex",
        "city",
        "search",
        "net",
        "internet",
        "page",
        "cache",
        "followers",
        "follows",
        "friends",
    ],
    currentHints: [],
    isLoading: false,
    placeholder: 'Введите запрос',
    isError: false,
    errorText: '',
    message: {
        draw: false,
        header: '',
        body: '',
        warning: false,
        error: false
    }
};

const TYPE_SYMBOL = 'TYPE_SYMBOL';
const SELECT_HINT = 'SELECT_HINT';
const CLEAR_INPUT = 'CLEAR_INPUT';
const REMOVE_HINTS = 'REMOVE_HINTS';
const CHANGE_MESSAGE = 'CHANGE_MESSAGE';
const CLOSE_MESSAGE = 'CLOSE_MESSAGE';
const ACTIVATE_LOADER = 'ACTIVATE_LOADER';
const REMOVE_LOADER = 'REMOVE_LOADER';

export const makeInputPlaceholder = produceActionCreator('make_input_placeholder')

function isQueryStringCorrect(queryString) {
    return !queryString.includes("#");

}

function getStringLastToken(str) {
    return str.split(/[\s, /()[\]]+/).slice(-1)[0];
}

export function search(state = initialData, action) {
    switch (action.type) {
        case TYPE_SYMBOL:
            const value = action.value;
            const lastToken = getStringLastToken(value);
            let newHints = [];
            if (lastToken.length)
                newHints = state.allHints.filter(
                    item => item.toLowerCase().startsWith(lastToken.toLowerCase()) && !(lastToken === item)
                );
            return {
                ...state,
                currentHints: newHints,
                queryString: value,
                isError: !isQueryStringCorrect(value),
                placeholder: initialData.placeholder
            };
        case SELECT_HINT:
            const newValue =
                state.queryString.slice(0, -getStringLastToken(state.queryString).length) + action.value;
            return {
                ...state,
                currentHints: [],
                queryString: newValue
            };
        case REMOVE_HINTS:
            return {
                ...state,
                currentHints: []
            };
        case CLEAR_INPUT:
            return {
                ...state,
                queryString: '',
                placeholder: action.placeholder
            };
        case CHANGE_MESSAGE:
            return {
                ...state,
                message: {
                    ...state.message,
                    header: action.header,
                    draw: true,
                    body: action.body,
                    error: action.error,
                    warning: action.warning
                },
            };
        case CLOSE_MESSAGE:
            return {
                ...state,
                message: {
                    ...state.message,
                    draw: false
                }
            };
        case ACTIVATE_LOADER:
            return {
                ...state,
                isLoading: true,
                message: {
                    ...state.message,
                    draw: false
                }
            };
        case REMOVE_LOADER:
            return {
                ...state,
                isLoading: false
            };
        case makeInputPlaceholder.type:
            return {
                ...state,
                placeholder: action.payload,
                queryString: ''
            };
        default:
            return state
    }
}

export const typeSymbol = (value) => ({'type': TYPE_SYMBOL, 'value': value});
export const selectHint = (value) => ({'type': SELECT_HINT, 'value': value});
export const removeHints = () => ({'type': REMOVE_HINTS});
export const showMessage = (header, body, error = false, warning = false) => ({
    type: CHANGE_MESSAGE,
    header, body, error, warning
});
export const closeMessage = () => ({type: CLOSE_MESSAGE});
export const activateLoader = () => ({type: ACTIVATE_LOADER});
export const removeLoader = () => ({type: REMOVE_LOADER});

export const executeQuery = (queryString, source=undefined) => (
    (dispatch, getState) => {
        dispatch(makeInputPlaceholder(queryString));
        if (queryString.length === 0) {
            let messageBody;
            if (queryString.length === 0) {
                messageBody = 'Введите запрос в строку. Пока она пустая';
                dispatch(showMessage('Пустая строка', messageBody, false, true));
            } else {
                messageBody = 'Тут должно быть описание конкретной ошибки, но я пока не сделал разбор';
                dispatch(showMessage(textConstants.messageWrongSyntax, messageBody, true));
            }

        } else {
            dispatch(activateLoader());
            executeSelectiveQuery(queryString).then(
                response => {
                    dispatch(removeLoader());
                    response.result.clusters.items = response.result.clusters.items.filter(
                        id => response.entities.clusters[id].entities.items.length > 0);
                    if (response.result.clusters.items.length === 0) {
                        dispatch(showMessage('Ответ сервера', 'Получен пустой кластер (он не отображается)', false, true));
                    } else {
                        console.log('Good clusters', response);
                        dispatch(processServerResponse({response: response, source: source}));
                        dispatch(selectCluster(response.result.clusters.items[0]))
                    }
                }
            ).catch(
                query => {
                    dispatch(removeLoader());
                    const response = query.response;
                    if (!response) {
                        console.log(query);
                        dispatch(showMessage(`Ошибка сети`, 'Либо у вас нету интернета, либо сервер упал, также возможно просто разраб криворукий', true))
                    } else {
                        dispatch(showMessage(`Ошибка выполнения зарпоса (${response.status})`, response.data.error, true))
                    }
                }
            )
        }
    }
);


