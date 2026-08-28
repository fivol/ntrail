import React from 'react';
import Cluster from "./Cluster";
import Arrow from "./Arrow";


const ClustersGraph = (props) => {
    const {sizes: {width, height}, graph} = props;
    if (!graph)
        return null;
    return (
        <div
            onMouseMove={(e) => {
                e.preventDefault();
                props.dragCluster(e.movementX, e.movementY)
            }}
            onMouseUp={() => props.stopDrag()}
            onMouseLeave={() => {
                props.stopDrag()
            }}
            className={'clustersAnimationsContainer'}>
            <div className="clustersField" style={{height: height, width: width}}>
                {graph.nodes.map(node => (
                    <Cluster
                        chooseCluster={() => props.selectCluster(node.id)}
                        selected={props.selectedClusterID === node.id}
                        highlighted={props.highlightedClusters.includes(node.id)}
                        x={node.pos.x}
                        y={node.pos.y}
                        key={node.id}
                        clusterData={node.data}
                        isOverlay={node.id === props.overlayClusterID}
                        toggleClusterHighlight={props.toggleClusterHighlight}
                        showCheckbox={props.highlightedClusters.length > 0}
                    />
                ))}
            </div>
            <svg width={width} height={height}>
                {
                    graph.edges.map(item => {
                            let x1, x2, y1, y2;
                            x1 = item.from.pos.x;
                            y1 = item.from.pos.y;
                            x2 = item.to.pos.x;
                            y2 = item.to.pos.y;

                            return (
                                <Arrow
                                    key={item.from.id + '__' + item.to.id}
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
};


export default ClustersGraph;

