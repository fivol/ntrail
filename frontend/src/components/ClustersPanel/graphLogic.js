const repulsionForce = [-2.4, 1, 10, 80, 25];
const attractionForce = [2, 0, 4, 2, 2];
const borderRepulsionForce = [-1, 0.5, 10, 20, 0.1];
const centralAttractionForce = [1, 1, 2, 2, 0.01 * 0];

const moveStrength = 5;

class Vector {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }

    copy() {
        return new Vector(this.x, this.y);
    }

    add(other) {
        this.x += other.x;
        this.y += other.y;
        return this;
    }

    mult(value) {
        this.x *= value;
        this.y *= value;
        return this;
    }

    div(value) {
        return this.mult(1 / value);
    }

    sub(other) {
        this.x -= other.x;
        this.y -= other.y;
        return this
    }

    mag() {
        return Math.sqrt(this.x * this.x + this.y * this.y);
    }
}

const createVector = (x, y) => {
    return new Vector(x, y);
};

const min = (...values) => Math.min(...values);
const max = (...values) => Math.max(...values);

export const getDist = (x, y) => {
    return Math.sqrt(x*x + y*y);
};

const map = (value, currLower, currUpper, targetLower, targetUpper, needBound = false) => {
    if (needBound)
        value = min(max(value, currLower), currUpper);
    value -= currLower;
    value /= (currUpper - currLower);
    value *= (targetUpper - targetLower);
    value += targetLower;
    return value;
};


class Node {
    constructor(node, sizes) {
        this.id = node.id;
        this.data = node;
        this.sizes = sizes;
        this.maxSize = max(sizes.width, sizes.height);
        let x, y;
        if (node['__exist']) {
            x = node.pos.x;
            y = node.pos.y;
        } else {
            x = Math.random() * sizes.width;
            y = Math.random() * sizes.height;
        }
        this.pos = createVector(x, y);
        this.velocity = createVector(0, 0);
        this.lastShift = null;
        this.lockedPosition = false
    }

    getData() {
        return {
            ...this.data,
            __exist: true,
            pos: {
                x: this.pos.x,
                y: this.pos.y
            }
        }
    }

    getDistanceWith(x, y) {
        return createVector(x - this.pos.x, y - this.pos.y).mag()
    }

    shiftBy(x, y) {
        this.pos.add(createVector(x, y))
    }

    moveTo(x, y) {
        this.pos = createVector(x, y)
    }

    lockMovement() {
        this.lockedPosition = true
    }

    unlockMovement() {
        this.lockedPosition = false
    }

    toForceVector(distVector, parameters, direction = 1) {
        let [pow, lowerBorder, upperBorder, minValue, coef] = parameters;

        let dist = distVector.mag();
        distVector.div(dist);

        dist = map(dist, minValue, this.maxSize, lowerBorder, upperBorder, true);

        let forceFactor = Math.pow(dist, pow);
        return distVector.mult(forceFactor * coef * direction)
    }

    calculateForceWith(other, connected) {
        let dir = other.pos.copy().sub(this.pos);

        let move = this.toForceVector(dir.copy(), repulsionForce, -1);
        if (connected)
            return this.toForceVector(dir, attractionForce).add(move);

        return move
    }

    calculateForceWithBorders() {
        let top = createVector(0, max(1, this.pos.y));
        let left = createVector(max(1, this.pos.x), 0);
        let bottom = createVector(0, min(-1, this.pos.y - this.sizes.height));
        let right = createVector(min(-1, this.pos.x - this.sizes.width), 0);

        let center = createVector(this.sizes.width / 2 - this.pos.x, this.sizes.height / 2 - this.pos.y);

        let sum = this.toForceVector(center, centralAttractionForce);
        sum.add(this.toForceVector(top, borderRepulsionForce));
        sum.add(this.toForceVector(left, borderRepulsionForce));
        sum.add(this.toForceVector(bottom, borderRepulsionForce));
        sum.add(this.toForceVector(right, borderRepulsionForce));
        return sum;
    }

    normalizePosition() {
        const normalizeCoordinate = (value, maxValue) => {
            return max(min(value, maxValue), 0)
        };

        this.pos = createVector(
            normalizeCoordinate(this.pos.x, this.sizes.width),
            normalizeCoordinate(this.pos.y, this.sizes.height)
        );
    }

    applyForce(forceVector) {
        if (this.lockedPosition)
            return;

        forceVector.mult(moveStrength);

        this.lastShift = forceVector;
        this.pos.add(forceVector);

        this.normalizePosition()
    }
}


export class Graph {
    constructor(nodes, edges, sizes) {
        this.nodes = nodes.map(node => new Node(node, sizes));
        const nodesDict = {};
        for (const node of this.nodes)
            nodesDict[node.id] = node;

        this.nodesDict = nodesDict;
        this.edges = edges.map(edge => ({from: nodesDict[edge.from], to: nodesDict[edge.to]}));
        this.sizes = sizes;
        const edgesDict = {};
        for (let node of this.nodes)
            edgesDict[node.id] = [];

        for (let edge of this.edges) {
            let id1 = edge.from.id;
            let id2 = edge.to.id;
            edgesDict[id1].push(id2);
            edgesDict[id2].push(id1);
        }
        this.edgesDict = edgesDict;
        this.wasUpdated = false;
    }

    getNearestNode(x, y) {
        let minDist = 9999999;
        let bestNode = this.nodes[0];
        for (let node of this.nodes) {
            let dist = node.getDistanceWith(x, y);
            if (dist < minDist) {
                minDist = dist;
                bestNode = node;
            }
        }
        return bestNode
    }

    wornToChange(){
        this.wasUpdated = false
    }

    getCompletePercents() {
        if (!this.wasUpdated){
            return 0;
        }
        let res = 0;
        for (let node of this.nodes) {
            res += node.lastShift.mag();
        }
        res /= this.nodes.length;
        res = Math.pow(res, 0.5);
        return 100 - map(res, 0, 3, 0, 100, true)
    }

    calculateForces() {
        let forces = {};
        for (let node1 of this.nodes) {
            let id1 = node1.id;
            let nodeBorderForce = node1.calculateForceWithBorders();

            forces[id1] = createVector(0, 0);

            for (let node2 of this.nodes) {
                let id2 = node2.id;
                if (id1 === id2)
                    continue;

                let connected = false;

                if (this.edgesDict[id1].includes(id2))
                    connected = true;

                forces[id1].add(node1.calculateForceWith(node2, connected));
            }

            forces[id1].div(this.nodes.length).add(nodeBorderForce)
        }
        return forces;
    }

    applyForces() {
        let forces = this.calculateForces();
        for (let node of this.nodes) {
            node.applyForce(forces[node.id])
        }
        this.wasUpdated = true;
    }
}