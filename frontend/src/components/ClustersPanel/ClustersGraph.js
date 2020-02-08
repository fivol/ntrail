import React, {useEffect, useState} from 'react';
import {
    Sigma,
    RandomizeNodePositions,
    ForceAtlas2, SigmaEnableWebGL
} from 'react-sigma';
import {listHash} from "../../utils";
import EntitiesGraph from "../EntitiesPanel/EntitiesGraph";
import ClustersAnimate from "./ClustersAnimate";

class ClustersGraphChecker extends React.Component {

    componentWillMount(...props) {
        console.log('mount', props)
    }

    componentWillReceiveProps({sigma, selectedEntities, visibleEntities}) {
        // console.log('sigma', sigma.graph.nodes())
        if (sigma.graph.nodes() && sigma.graph.nodes()[0].firstMount) {
            sigma.graph.nodes().forEach(n => {
                Object.assign(n, {firstMount: false})
            });
            return;
        }
        console.log('done adjust', sigma.graph.nodes(), this.props);
        const {width, height} = this.props;
        const coordinates = sigma.graph.nodes().map(node => {
            return {
                x: node.x,
                y: node.y
            }
        });
        const minX = Math.min(...coordinates.map(item => item.x));
        const minY = Math.min(...coordinates.map(item => item.y));
        const maxX = Math.max(...coordinates.map(item => item.x));
        const maxY = Math.max(...coordinates.map(item => item.y));

        // this.props.setCoordinates(
        //     coordinates.map(pos => ({
        //         x: (pos.x - minX) / (maxX - minX) * width,
        //         y: (pos.y - minY) / (maxY - minY) * height,
        //     }))
        // );
    }

    render = () => null;
}


const ClustersGraph = (props) => {

    const {clusters, connections} = props;

    const [needDrawGraph, setNeedDrawGraph] = useState(false);
    const [sizes, setSizes] = useState({});
    const [setCoordinates, setSetCoordinatesFunc] = useState(null);

    const graph = {
        nodes: clusters.map(cluster => ({id: cluster.id, firstMount: true, size: 5})),
        edges: connections.map(edge => ({id: edge.from + edge.to, source: edge.from, target: edge.to}))
    };

    const graphSettings = {
        defaultNodeColor: '#ec5148',
        defaultEdgeColor: '#333',
        edgeColor: 'default',
        drawEdges: true,
        labelThreshold: 100,
        minNodeSize: 0,
        maxNodeSize: 0
    };

    const graphStyle = {
        width: sizes.width + 'px',
        height: sizes.height + 'px',
    };
    const startGenerateCoordinates = (setCoordinates, width, height) => {
        console.log('in startGenerateCoordinates', setCoordinates, width, height)
        setNeedDrawGraph(true);
        setSizes({
            width,
            height
        });
        setSetCoordinatesFunc(setCoordinates)
    };
    console.log('setCoordinates', setCoordinates)
    return (
        <>
            <ClustersAnimate {...props} startGenerateCoordinates={startGenerateCoordinates}/>
            {
                needDrawGraph &&
                <div
                    key={listHash(clusters)}
                >
                    <Sigma
                        renderer="webgl"
                        graph={graph}
                        settings={graphSettings}
                        style={graphStyle}
                    >
                        <SigmaEnableWebGL/>
                        <RandomizeNodePositions>
                            <ForceAtlas2 worker
                                         scalingRatio={1}
                                         slowDown={10}
                                         linLogMode={false}
                                         iterationsPerRender={50}
                                         timeout={2000}
                            >
                                <ClustersGraphChecker setCoordinates={setCoordinates}
                                                      width={sizes.width}
                                                      height={sizes.height}/>

                            </ForceAtlas2>
                        </RandomizeNodePositions>
                    </Sigma>

                </div>
            }
        </>
    )
};


export default ClustersGraph;

