import React, {createRef} from 'react';
import Cluster from "./Cluster";
import Arrow from "./Arrow";
import {rand} from '../../utils'
import ClustersGraph from "./ClustersGraph";
import {Graph} from "./graphLogic";

// getNearestCluster(clusterID) {
//     const positions = this.state.positions;
//     const {x, y} = positions[clusterID];
//     let minDist = 9999999;
//     let nearestItemKey = -1;
//     for (let [key, item] of Object.entries(positions)) {
//         if (key !== clusterID) {
//             const elemX = item.x;
//             const elemY = item.y;
//             const dist = Math.sqrt(Math.pow(x - elemX, 2) + Math.pow(y - elemY, 2));
//             if (dist < minDist) {
//                 minDist = dist;
//                 nearestItemKey = key;
//             }
//         }
//     }
//     return {
//         nearestClusterID: nearestItemKey,
//         dist: minDist
//     }
// }

// dragCluster = (x, y) => {
//     if (!this.state.mousePressed)
//         return;
//     const {positions, selectedCluster} = this.state;
//     const clusterID = selectedCluster;
//     const newX = positions[clusterID].x + x;
//     const newY = positions[clusterID].y + y;
//     const border = 50;
//
//     const {nearestClusterID, dist} = this.getNearestCluster(clusterID);
//     if (this.movedDist !== undefined)
//         this.movedDist += dist;
//     this.setState(
//         {
//             overlayClusterID: dist < 30 ? nearestClusterID : null
//         }
//     );
//
//     const checkBorder = (value, maxValue) => (value > border && value < maxValue - border);
//     if (checkBorder(newX, this.state.width) && checkBorder(newY, this.state.height))
//         this.setState(
//             {
//                 positions:
//                     {
//                         ...positions,
//                         [clusterID]: {
//                             x: newX,
//                             y: newY
//                         }
//                     }
//             }
//         )
// };

// toggleClusterHighlight(id) {
//     if (!this.props.highlightedClusters.includes(id))
//         this.props.setHighlightedClusters([
//             ...this.props.highlightedClusters,
//             id
//         ]);
//     else
//         this.props.setHighlightedClusters([
//             ...this.props.highlightedClusters.filter(item => item !== id)
//         ]);
// }

// stopDrag() {
//     this.setState({
//         mousePressed: false
//     });
//     this.checkOverlay();
// }

// checkOverlay() {
//     if (this.state.overlayClusterID && this.props.selectedClusterID) {
//         this.props.setHighlightedClusters([this.state.overlayClusterID, this.props.selectedClusterID])
//     }
//     this.setState({overlayClusterID: null});
//     if (this.movedDist && this.movedDist > 3)
//         this.updateState(this.state.width);
// }


const makeGraphIteration = (graph, sizes,) => {
    const {nodes, edgesDict} = graph;
    const positionGenerator
    return {...graph, nodes: [...nodes]}
};

const updateGraphWith = (graph, clusters, connections, sizes) => {
    const generateRandomPosition = (width, height) => ({
        x: Math.random() * width,
        y: Math.random() * height
    });

    const newGraph = {
        nodes: [
            ...graph.nodes,
            ...clusters.map(cluster => ({...cluster, ...generateRandomPosition(sizes.width, sizes.height)}))
        ],
        edges: [
            ...graph.edges
        ]
    };

    const edgesDict = {};
    for (let node of newGraph.nodes)
        edgesDict[node.id] = [];

    for (let edge of newGraph.edges) {
        let id1 = edge.from.id;
        let id2 = edge.to.id;
        edgesDict[id1].push(id2);
        edgesDict[id2].push(id1);
    }

    return {
        ...newGraph,
        edgesDict
    }
};


class ClustersAnimate extends React.Component {
    state = {
        graph: {
            nodes: [],
            edges: []
        },
        sizes: {
            width: 0,
            height: 0
        },
        overlayClusterID: null,
        selectedCluster: null,
        mousePressed: false
    };

    updateGraphFrame() {
        this.setState({
            graph: makeGraphIteration(this.state.graph, this.state.sizes)
        });
    }

    componentDidMount() {
        const width = this.containerRef.current.offsetWidth;
        const height = this.props.clusters.length * 100;
        this.setState({
            sizes: {width, height},
            graph: updateGraphWith(this.state.graph, this.props.clusters, this.props.connections, {width, height})
        })
    }

    selectCluster(id) {
        // this.movedDist = 0;
        this.setState({
            selectedCluster: id,
            // mousePressed: true
        });
        this.props.selectCluster(id)
    }

    render() {
        this.containerRef = createRef();
        return (
            <div ref={this.containerRef} style={{margin: '25px'}}>
                <ClustersGraph
                    graph={this.state.graph.}
                    sizes={this.state.sizes}
                    selectCluster={this.selectCluster.bind(this)}
                    selectedClusterID={this.props.selectedClusterID}
                    highlightedClusters={this.props.highlightedClusters}
                />
            </div>
        )
    }
}

export default ClustersAnimate;
