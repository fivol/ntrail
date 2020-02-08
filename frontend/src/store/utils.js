import makeActionCreator from 'make-action-creator';


export function produceActionCreator(type, ...keys) {
    return makeActionCreator(type)
}

export const mergeObjectsDepth2 = (obj1, obj2) => {
    const obj = {...obj1};
    for (let [key, value] of Object.entries(obj2)) {
        if (key in obj)
            obj[key] = {...obj[key], ...value};
        else
            obj[key] = value
    }
    return obj
};

export const getObj = (state, objType, idx) => {
    return state.workSpace.objects[objType][idx]
};

export const getObjects = (state, objType, indexes)=>{
    return indexes.map(id=>getObj(state, objType, id))
};

export const getSelectedClusterID = (state)=>{
    return state.workSpace.clusters.selectedClusterID;
};


export const reducerWrapper = (reducerFunc) => {
    return (state, action) => {
        const obj = reducerFunc(state, action);
        if ('force' in obj)
            return obj;
        return {
            ...state,
            ...obj
        }
    }
}

export function download(data, filename, type) {
    let file = new Blob([data], {type: type});
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        let a = document.createElement("a"),
            url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function() {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 0);
    }
}