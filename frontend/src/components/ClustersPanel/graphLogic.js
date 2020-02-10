const repulsionForce = [-2.4, 1, 10, 20, 10];
const attractionForce = [2, 0, 4, 2, 2];
const borderRepulsionForce = [-1, 0.5, 10, 20, 0.1];
const centralAttractionForce = [1, 1, 2, 2, 0.01 * 0];

const moveStrength = 50;

const width_ = 400;
const height_ = 700;


class Vector {
    constructor(x, y) {
        this.x = x;
        this.y = y;
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
}

const createVector = (x, y) => {
    return new Vector(x, y);
};

const min = (...values) => Math.min(...values);
const max = (...values) => Math.max(...values);

const map = (value, currLower, currUpper, targetLower, targetUpper, needBound = false) => {
    if (needBound)
        value = min(max(value, currLower), currUpper);
    value -= currLower;
    value /= (currUpper - currLower);
    value *= (targetUpper - targetLower);
    value += targetLower;
    return value;
};

const maxSize = max(width_, height_);

const toForceVector = (distVector, parameters, direction = 1) => {
    let [pow, lowerBorder, upperBorder, minValue, coef] = parameters;

    let dist = distVector.mag();
    distVector.div(dist);

    dist = map(dist, minValue, maxSize, lowerBorder, upperBorder, true);

    let forceFactor = Math.pow(dist, pow);
    return distVector.mult(forceFactor * coef * direction)
}

const Node = class {
    constructor(id, x, y) {
        this.id = id;
        this.pos = createVector(x, y);
        this.velocity = createVector(0, 0);
        this.lastShift = createVector(0, 0);
        this.lockedPosition = false
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
        let bottom = createVector(0, min(-1, this.pos.y - height_));
        let right = createVector(min(-1, this.pos.x - width_), 0);

        let center = createVector(width_ / 2 - this.pos.x, height_ / 2 - this.pos.y);

        let sum = toForceVector(center, centralAttractionForce);
        sum.add(toForceVector(top, borderRepulsionForce));
        sum.add(toForceVector(left, borderRepulsionForce));
        sum.add(toForceVector(bottom, borderRepulsionForce));
        sum.add(toForceVector(right, borderRepulsionForce));
        return sum;
    }

    normalizePosition() {
        const normalizeCoordinate = (value, maxValue) => {
            return max(min(value, maxValue), 0)
        };

        this.pos = createVector(
            normalizeCoordinate(this.pos.x, width_),
            normalizeCoordinate(this.pos.y, height_)
        );
    }

    applyForce(forceVector) {

        forceVector.mult(moveStrength);

        return forceVector;
    }
};

export const Graph = class {
    constructor(nodes, edgesDict) {
        this.nodes = nodes;
        this.edgesDict = edgesDict;
    }

    getNearestNode(x, y) {
        let minDist = 9999999;
        let bestNode = this.nodes[0]
        for (let node of this.nodes) {
            let dist = node.getDistanceWith(x, y);
            if (dist < minDist) {
                minDist = dist;
                bestNode = node;
            }
        }
        return bestNode
    }

    getCompletePercents() {
        let res = 0;
        for (let node of this.nodes)
            res += node.lastShift.mag();
        res /= this.nodes.length;
        res = Math.pow(res, 0.5);
        return 100 - map(res, 0, 3, 0, 100, true)
    }

    calculateForces(nodes, edgesDict) {
        let forces = {};
        for (let node1 of nodes) {
            let id1 = node1.id;
            let nodeBorderForce = Node.calculateForceWithBorders();

            forces[id1] = createVector(0, 0);

            for (let node2 of nodes) {
                let id2 = node2.id;s
                if (id1 === id2)
                    continue;

                let connected = false;

                if (edgesDict[id1].includes(id2))
                    connected = true;

                forces[id1].add(node1.calculateForceWith(node2, connected));
            }

            forces[id1].div(nodes.length).add(nodeBorderForce)
        }
        return forces;
    }

    updatePositionsForces(nodes, edgesDict) {
        let forces = this.calculateForces(nodes, edgesDict);
        for (let node of this.nodes) {
            Node.applyForce(forces[node.id])
        }
    }
};