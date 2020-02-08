import {SubmissionError} from "redux-form";
import {executeQuery, showMessage} from "./searchReducer";
import {download, getSelectedClusterID} from "./utils";
import {saveState} from "./localStorage";
import {removeClusters} from "./clustersReducer";
import {queryCreator} from "../api/queryStringCreators";

const keyWords = new Set(['group', 'feed', 'news', 'music', 'edit', 'settings', 'im', 'friends', 'groups', 'video', 'apps', 'vkpay', 'market', 'docs', 'blog', 'dev', "biz", "about", "jobs", "legal", "data_protection", "safety", "exilemusic", "exilemusic", "verify", "exile_music"]);

export const extractFromString = (values) => {
    return (dispatch, getState) => {
        const text = values.text;
        if (!text) {
            throw new SubmissionError({text: 'Пустое поле'});
        }
        const regex = /href="\/(\w+)"/g;
        let match = regex.exec(text);
        if (!match) {
            throw new SubmissionError({text: 'Не найдено полезных данных'});
        }
        let matches = new Set();
        while (match) {
            matches.add(match[1]);
            match = regex.exec(text);
        }
        matches = [...matches.difference(keyWords)];
        const queryString = queryCreator('vk.users', matches);
        dispatch(executeQuery(queryString));
    }
};

export const downloadWorkSpace = () => {
    return (dispatch, getState) => {
        const filename = `NTrail workspace (${getState().workSpace.clusters.items.length} clusters)`;
        download(JSON.stringify(getState()), filename, '')
    }
};

export const uploadWorkSpace = () => {
    return (dispatch, getState) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.onchange = e => {
            const file = e.target.files[0];

            const reader = new FileReader();
            reader.readAsText(file, 'UTF-8');

            reader.onload = readerEvent => {
                const content = readerEvent.target.result;
                console.log('File loaded');
                try {
                    const state = JSON.parse(content);
                    if (!('form' in state))
                        throw Error('ошибка');
                    saveState(state);
                } catch (e) {
                    alert('Не корректный файл данных NTrail пространства! (Загружать можно только файлы, ранее сохраненные с помощью опции "Сохранить рабочее пространство") Попробуйте выбрать другой файл')
                }
                window.location.reload(true);
            }
        };
        input.click();
    }
};

const transformEntities = (dispatch, getState, setTransformFunc) => {
    const state = getState();
    const selectedClusters = state.workSpace.clusters.highlightedClusters;
    if (selectedClusters.length >= 2) {
        const selectedClustersEntities = selectedClusters.map(
            id => state.workSpace.objects.clusters[id].entities
        );
        let resultEntities = new Set(selectedClustersEntities[0]);
        for (let entities of selectedClustersEntities.slice(1)) {
            resultEntities = resultEntities[setTransformFunc](new Set(entities));
        }
        const entitiesID = [...resultEntities];
        if (entitiesID.length === 0) {
            dispatch(showMessage('Результат операции', 'Получен пустой кластер', false, true))
        } else {
            const queryString = queryCreator('vk.users', entitiesID);
            dispatch(executeQuery(queryString));
        }
    }
};

export const intersectClusters = () => {
    return (dispatch, getState) => {
        transformEntities(dispatch, getState, 'intersect')
    }
};

export const unionClusters = () => {
    return (dispatch, getState) => {
        transformEntities(dispatch, getState, 'union')
    }
};

export const subtractClusters = () => {
    return (dispatch, getState) => {
        transformEntities(dispatch, getState, 'difference')
    }
};

export const symDiffClusters = () => {
    return (dispatch, getState) => {
        transformEntities(dispatch, getState, 'symmetricDifference')
    }
};

export const pickOutToCluster = () => {
    return (dispatch, getState) => {
        const state = getState();
        const selectedEntities = state.workSpace.entities.selectedItems;
        if (selectedEntities.length > 0) {
            const queryString = queryCreator('vk.users', selectedEntities);
            dispatch(executeQuery(queryString, getSelectedClusterID(state)));
        }
    }
};

export const deleteFromCluster = () => (dispatch, getState) => {
    const state = getState();
    const selectedEntities = state.workSpace.entities.selectedItems;
    const allEntities = state.workSpace.entities.items;
    const subtractedEntities = [...new Set(allEntities).difference(new Set(selectedEntities))];
    if (selectedEntities.length > 0) {
        const queryString = queryCreator('vk.users', subtractedEntities);
        dispatch(executeQuery(queryString));
    }
};
export const deleteSelectedClusters = () => {
    return (dispatch, getState) => {
        const state = getState();
        const selectedClusters = state.workSpace.clusters.highlightedClusters;
        dispatch(removeClusters(selectedClusters));
    }
};

export const getFriendsAction = () => {
    return (dispatch, getState) => {
        const state = getState();
        const selectedEntities = state.workSpace.entities.selectedItems;
        if (selectedEntities.length >= 1) {
            let queryString;
            if (selectedEntities.length > 1) {
                queryString = queryCreator('vk.users', selectedEntities, 'friends');
            } else {
                queryString = queryCreator('vk.user', selectedEntities[0], 'friends');
            }
            dispatch(executeQuery(queryString, getSelectedClusterID(state)));
        }
    }
};