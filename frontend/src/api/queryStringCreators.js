const queryTypeCreator = (queryType, queryString) => {
    return `${queryType} ${queryString}`
};

const extractGetQueryAction = (queryString) => {
    return queryString.slice(4)
};

export const queryGET = (queryString) => {
    return queryTypeCreator('GET', queryString);
};


export const queryLOAD = (queryString) => {
    return queryTypeCreator('LOAD', queryString);
};


export const queryReplaceGetWithLoad = (queryString) => {
    console.assert(queryString.toLowerCase().startsWith('get '));
    return queryLOAD(extractGetQueryAction(queryString))
};

export const queryList = (items) => {
    return `(${items.join(', ')})`
};

export const queryGenerateParams = (params) => {
    return `[${params.join(' ')}]`
};

const queryGenerateAttrs = (attrs) => {
    if (!attrs)
        return '';
    if (typeof attrs === 'object')
        return attrs.join(' ');
    return attrs;
};

export const queryCreator = (actionName, args, attrs = null, queryType = 'GET') => {
    if (typeof args === 'object')
        args = queryList(args);

    if(!args.match(/[a-zA-Zа-яА-Я]+/))
        args = `"${args}"`;

    return `${queryType} ${actionName} ${args} ${queryGenerateAttrs(attrs)}`;
};