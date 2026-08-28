import React, {createRef} from 'react';
import Cluster from "./Cluster";
import Arrow from "./Arrow";
import {rand} from '../../utils'
import ClustersGraph from "./ClustersGraph";
import {getDist, Graph} from "./graphLogic";


const makeGraphIteration = (graph) => {
    if (!graph)
        return;
    graph.applyForces();
    return graph
};

const updateGraphWith = (graph, clusters, connections, sizes) => {
    let existingNodesDict = {};
    if (graph)
        existingNodesDict = graph.nodesDict;

    const newClustersIDS = clusters.map(item => item.id);

    const newNodes = clusters.map(
        cluster => (cluster.id in existingNodesDict) ? existingNodesDict[cluster.id].getData() : cluster
    ).filter(node => newClustersIDS.includes(node.id));
    return new Graph(newNodes, connections, sizes)
};


const updateClustersPositionsTimeout = 25;
const stopUpdateGraphCutoff = 90;

class ClustersAnimate extends React.Component {
    state = {
        graph: null,
        sizes: {
            width: 0,
            height: 0
        },
        overlayClusterID: null,
        selectedCluster: null,
        mousePressed: false,
        liveUpdate: false,
        selectedClusterObject: null,
        trajectory: 0
    };

    updateGraphFrame() {
        this.setState({
            graph: makeGraphIteration(this.state.graph)
        });
    }

    calculateHeight(){
        return (this.props.clusters.length - this.props.connections.length / 2 + 5) * 40;
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps.clustersID !== this.props.clustersID) {
            const width = this.containerRef.current.offsetWidth;
            const height = this.calculateHeight();
            this.setState({
                    sizes: {
                        width, height
                    },
                    liveUpdate: true,
                    mousePressed: false,
                    overlayClusterID: false,
                    selectedCluster: this.props.selectedClusterID,
                    graph: updateGraphWith(this.state.graph, this.props.clusters, this.props.connections, {width, height})
                }
            )
        } else if (this.state.liveUpdate) {
            if (this.state.graph.getCompletePercents() >= stopUpdateGraphCutoff)
                this.setState({liveUpdate: false});
            else
                setTimeout(this.updateGraphFrame.bind(this), updateClustersPositionsTimeout);
        }
    }

    componentDidMount() {
        const width = this.containerRef.current.offsetWidth;
        const height = this.calculateHeight();
        this.setState({
            sizes: {width, height},
            graph: updateGraphWith(this.state.graph, this.props.clusters, this.props.connections, {width, height}),
            liveUpdate: true
        });
    }

    selectCluster(id) {
        let nearestNode = this.state.graph.nodesDict[id];
        nearestNode.lockMovement();
        this.state.graph.wornToChange();
        this.setState({
            mousePressed: true,
            selectedCluster: id,
            selectedClusterObject: nearestNode,
            trajectory: 0
        });
    }

    stopDrag() {
        if(this.state.selectedClusterObject){
            if(this.state.trajectory < 5){
                this.props.selectCluster(this.state.selectedCluster)
            }
            this.state.selectedClusterObject.unlockMovement();
            this.setState({
                mousePressed: false,
                selectedClusterObject: null,
                liveUpdate: true
            });
        }
    }

    dragCluster(x, y){
        if (this.state.selectedClusterObject) {
            this.state.selectedClusterObject.shiftBy(x, y);
            this.setState({
                graph: this.state.graph,
                trajectory: this.state.trajectory + getDist(x, y)
            })
        }
    }

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

    render() {
        this.containerRef = createRef();
        return (
            <div ref={this.containerRef} style={{margin: '35px'}}>
                <ClustersGraph
                    graph={this.state.graph}
                    sizes={this.state.sizes}
                    dragCluster={this.dragCluster.bind(this)}
                    stopDrag={this.stopDrag.bind(this)}
                    selectCluster={this.selectCluster.bind(this)}
                    selectedClusterID={this.props.selectedClusterID}
                    highlightedClusters={this.props.highlightedClusters}
                    toggleClusterHighlight={this.toggleClusterHighlight.bind(this)}
                />
            </div>
        )
    }
}

export default ClustersAnimate;
