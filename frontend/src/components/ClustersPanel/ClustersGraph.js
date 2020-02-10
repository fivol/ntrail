import React from 'react';
import Cluster from "./Cluster";
import Arrow from "./Arrow";


const ClustersGraph = (props) => {
    const {sizes: {width, height}, graph: {nodes, edges}} = props;
    if(!width)
        return null;
    console.log('Clusters graph', props);
    return (
        <div
            // onMouseMove={(e) => props.dragCluster(e.movementX, e.movementY)}
            // onMouseUp={() => props.stopDrag()}
            // onMouseLeave={() => props.stopDrag()}
            className={'clustersAnimationsContainer'}>
            <div className="clustersField" style={{height: height, width: width}}>
                {nodes.map(node => (
                    <Cluster
                        chooseCluster={() => props.selectCluster(node.id)}
                        selected={props.selectedClusterID === node.id}
                        highlighted={props.highlightedClusters.includes(node.id)}
                        x={node.x}
                        y={node.y}
                        key={node.id}
                        clusterData={node}
                        isOverlay={node.id === props.overlayClusterID}
                        toggleClusterHighlight={props.toggleClusterHighlight}
                        showCheckbox={props.highlightedClusters.length > 0}
                    />
                ))}
            </div>
            <svg width={width} height={height}>
                {
                    edges.map((item, index) => {
                            let x1, x2, y1, y2;
                            x1 = item.from.x;
                            y1 = item.from.y;
                            x2 = item.to.x;
                            y2 = item.to.y;

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
};


export default ClustersGraph;

