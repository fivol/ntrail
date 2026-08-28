import randGen from 'random-seed';

export const rand = randGen.create();

Set.prototype.difference = function (otherSet) {
    const differenceSet = new Set();

    for (let elem of this) {
        if (!otherSet.has(elem))
            differenceSet.add(elem);
    }

    return differenceSet;
};

Set.prototype.intersect = function (otherSet) {
    return new Set([...this].filter(x => otherSet.has(x)));
};

Set.prototype.union = function (otherSet) {
    return new Set([...this, ...otherSet]);
};

Set.prototype.symmetricDifference = function (otherSet) {
    return this.union(otherSet).difference(this.intersect(otherSet));
};

export function shuffle(array) {
    rand.initState();
    array.sort(() => (rand(1000) / 1000) - 0.5);
}

export const round = (value, digits = 2) => {
    if (!Number(value))
        return value;
    const pow = Math.pow(10, digits);
    return Math.round(Number(value) * pow) / pow;
};

String.prototype.hashCode = function() {
    var hash = 0, i, chr;
    if (this.length === 0) return hash;
    for (i = 0; i < this.length; i++) {
        chr   = this.charCodeAt(i);
        hash  = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

export const listHash = (list)=>{
    if(!list)
        return -1
    if(typeof list[0] === typeof ''){
        return list.join('').hashCode()
    }
    return list.reduce((s, curr)=>s + curr.id, '').hashCode()
}

export function LightenDarkenColor(col,amt) {
    var usePound = false;
    if ( col[0] == "#" ) {
        col = col.slice(1);
        usePound = true;
    }

    var num = parseInt(col,16);

    var r = (num >> 16) + amt;

    if ( r > 255 ) r = 255;
    else if  (r < 0) r = 0;

    var b = ((num >> 8) & 0x00FF) + amt;

    if ( b > 255 ) b = 255;
    else if  (b < 0) b = 0;

    var g = (num & 0x0000FF) + amt;

    if ( g > 255 ) g = 255;
    else if  ( g < 0 ) g = 0;

    return (usePound?"#":"") + (g | (b << 8) | (r << 16)).toString(16);
}