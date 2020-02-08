import React, {createRef} from 'react';
import Cluster from "./Cluster";
import Arrow from "./Arrow";
import {rand} from '../../utils'

const generatePositions = (objectsID, connections, width) => {
    rand.initState();
    // TODO Посчитать нормально положение объекта на холсте. Сейчас стоит простоя метрика, чтоб объекты были как можно дальше
    const connectionsDict = {};
    for (const nodeID of objectsID)
        connectionsDict[nodeID] = [];
    for (const item of connections) {
        connectionsDict[item.from].push(item.to);
        connectionsDict[item.to].push(item.from);
    }
    const nodeDist = (node1, node2) => {
        return Math.sqrt(Math.pow(node1.x - node2.x, 2) + Math.pow(node1.y - node2.y, 2));
    };
    const nodeConnected = (node1ID, node2ID) => {
        return connectionsDict[node1ID].includes(node2ID)
    };
    const metric = (nodesPositions) => {
        let sum = 0;
        for (const node1 of nodesPositions) {
            for (const node2 of nodesPositions) {
                if (node1 !== node2) {
                    const dist = nodeDist(node1, node2);
                    if (dist < 100)
                        sum -= 5000;
                    else if (nodeConnected(node1.id, node2.id)) {
                        sum -= dist;
                    } else {
                        sum += dist;
                    }
                }
            }
        }
        return sum;
    };
    const height = Math.max(objectsID.length * 70, 250);
    let positions = {};
    const margin = 50;
    const clearHeight = height - 2 * margin;
    const clearWidth = width - 2 * margin;
    let maxMetric = -1000000000;
    let bestPositions;
    for (let i = 0; i < 10 * objectsID.length; i++) {
        const nodesPositions = [];
        for (const nodeID of objectsID) {
            nodesPositions.push(
                {
                    id: nodeID,
                    x: rand(1000) / 1000 * clearWidth,
                    y: rand(1000) / 1000 * clearHeight,
                }
            )
        }
        const metricValue = metric(nodesPositions);
        if (metricValue > maxMetric) {
            bestPositions = nodesPositions;
            maxMetric = metricValue;
        }
    }
    for (let node of bestPositions) {
        positions[node.id] = {
            x: margin + node.x,
            y: margin + node.y
        }
    }
    return {
        positions,
        height
    }
};


class ClustersAnimate extends React.Component {
    state = {
        positions: {},
        width: 0,
        height: 0,
        clusters: [],
        connections: [],
        overlayClusterID: null,
        selectedCluster: null,
        mousePressed: false
    };

    updateState(width) {
        const {positions, height} = generatePositions(this.props.clustersID, this.props.connections, width);
        this.setState({
            width, positions, height,
            clusters: this.props.clusters,
            connections: this.props.connections,
        });
    }

    componentDidMount() {
        const width = this.containerRef.current.offsetWidth;
        this.updateState(width);
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (this.props.clustersID !== prevProps.clustersID) {
            this.updateState(this.state.width);
        }
    }

    getNearestCluster(clusterID) {
        const positions = this.state.positions;
        const {x, y} = positions[clusterID];
        let minDist = 9999999;
        let nearestItemKey = -1;
        for (let [key, item] of Object.entries(positions)) {
            if (key !== clusterID) {
                const elemX = item.x;
                const elemY = item.y;
                const dist = Math.sqrt(Math.pow(x - elemX, 2) + Math.pow(y - elemY, 2));
                if (dist < minDist) {
                    minDist = dist;
                    nearestItemKey = key;
                }
            }
        }
        return {
            nearestClusterID: nearestItemKey,
            dist: minDist
        }
    }

    dragCluster = (x, y) => {
        if (!this.state.mousePressed)
            return;
        const {positions, selectedCluster} = this.state;
        const clusterID = selectedCluster;
        const newX = positions[clusterID].x + x;
        const newY = positions[clusterID].y + y;
        const border = 50;

        const {nearestClusterID, dist} = this.getNearestCluster(clusterID);
        if (this.movedDist !== undefined)
            this.movedDist += dist;
        this.setState(
            {
                overlayClusterID: dist < 30 ? nearestClusterID : null
            }
        );

        const checkBorder = (value, maxValue) => (value > border && value < maxValue - border);
        if (checkBorder(newX, this.state.width) && checkBorder(newY, this.state.height))
            this.setState(
                {
                    positions:
                        {
                            ...positions,
                            [clusterID]: {
                                x: newX,
                                y: newY
                            }
                        }
                }
            )
    };

    toggleClusterHighlight(id) {
        if (!this.props.highlightedClusters.includes(id))
            this.props.setHighlightedClusters([
                ...this.props.highlightedClusters,
                id
            ]);
        else
            this.props.setHighlightedClusters([
                ...this.props.highlightedClusters.filter(item => item !== id)
            ]);
    }

    checkOverlay() {
        if (this.state.overlayClusterID && this.props.selectedClusterID) {
            this.props.setHighlightedClusters([this.state.overlayClusterID, this.props.selectedClusterID])
        }
        this.setState({overlayClusterID: null});
        if (this.movedDist && this.movedDist > 3)
            this.updateState(this.state.width);
    }

    selectCluster(id) {
        this.movedDist = 0;
        this.setState({
            selectedCluster: id,
            mousePressed: true
        });
        this.props.selectCluster(id)
    }

    stopDrag() {
        this.setState({
            mousePressed: false
        })
        this.checkOverlay();
    }

    render() {
        const connections = this.state.connections;
        this.containerRef = createRef();
        const {width, height, positions} = this.state;
        return (
            <div
                onMouseMove={(e) => this.dragCluster(e.movementX, e.movementY)}
                onMouseUp={this.stopDrag.bind(this)}
                onMouseLeave={this.stopDrag.bind(this)}
                className={'clustersAnimationsContainer'} ref={this.containerRef}>
                <div className="clustersField" style={{height: this.state.height}}>
                    {this.state.clusters.map(clusterData => (
                        <Cluster chooseCluster={this.selectCluster.bind(this)}
                                 selected={this.props.selectedClusterID === clusterData.id}
                                 highlighted={this.props.highlightedClusters.includes(clusterData.id)}
                                 pos={this.state.positions[clusterData.id]}
                                 key={clusterData.id}
                                 clusterData={clusterData}
                                 isOverlay={clusterData.id === this.state.overlayClusterID}
                                 toggleClusterHighlight={this.toggleClusterHighlight.bind(this)}
                                 showCheckbox={this.props.highlightedClusters.length > 0}
                        />
                    ))}
                </div>
                <svg width={width} height={height}>
                    {
                        connections.map((item, index) => {
                                let x1, x2, y1, y2;
                                x1 = positions[item.from].x;
                                y1 = positions[item.from].y;
                                x2 = positions[item.to].x;
                                y2 = positions[item.to].y;

                                return (
                                    <Arrow
                                        key={index}
                                        x1={x1}
                                        y1={y1}
                                        x2={x2}
                                        y2={y2}
                                        shorten={50}
                                    />
                                )
                            }
                        )
                    }
                </svg>
            </div>
        )
    }
}

export default ClustersAnimate;
