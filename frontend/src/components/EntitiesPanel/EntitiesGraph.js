import React, {useEffect, useState} from 'react';
import {
    Sigma,
    RandomizeNodePositions,
    ForceAtlas2, SigmaEnableWebGL
} from 'react-sigma';
import {connect} from "react-redux";
import {getObjects} from "../../store/utils";
import {listHash} from "../../utils";
import User from "./UserAvatar/User";

const getNodeColorAndSize = (entity, selectedEntities, visibleEntities) => {
    let size = 5;
    let color = entity.properties.sex === 1 ? '#ff5555' : '#5555ff';
    if (!entity.valid)
        color = '#aaa';
    if (!visibleEntities.includes(entity.id)) {
        // color = LightenDarkenColor(color, -40);
        color = '#777';
        size = 4
    }
    if (selectedEntities.includes(entity.id)) {
        color = '#0a0';
    }

    return {
        color: color,
        size: size
    };
};

class UpdateNodeProps extends React.Component {

    componentWillReceiveProps({sigma, selectedEntities, visibleEntities}) {
        console.log('graphUpdateComponent, ReceiveProps');

        sigma.graph.nodes().forEach(n => {
            const updateNode = {
                ...getNodeColorAndSize(n.entity, selectedEntities, visibleEntities),
            };
            Object.assign(n, updateNode)
        });
        sigma.refresh();

    }

    render = () => null
}


const EntitiesGraph = (props) => {
    const {selectedEntities, connections, toggleItemSelection, entities} = props;
    const visibleEntitiesIDS = props.visibleEntities.map(item => item.id);
    const [selectedEntity, setSelectedEntity] = useState(null);
    useEffect(() => {
        setSelectedEntity(null);
    }, [listHash(entities)]);

    const generateGraph = () => {
        return {
            nodes: entities.map(entity => ({
                id: entity.id,
                label: entity.name,
                ...getNodeColorAndSize(entity, selectedEntities, visibleEntitiesIDS),
                entity: entity
            }))
            ,
            edges: Object.entries(connections).map(([firstID, connectedIDS]) =>
                connectedIDS.map(secondID => ({
                    id: firstID + secondID,
                    source: firstID,
                    target: secondID,
                }))).flat()
        }
    };

    const graphSettings = {
        defaultNodeColor: '#ec5148',
        defaultEdgeColor: '#ccc',
        edgeColor: 'default',
        drawEdges: true,
        labelThreshold: 100,
        minNodeSize: 0,
        maxNodeSize: 0
    };

    const graphStyle = {
        height: '700px'
    };
    const onClickNode = (id, selectedEntities) => {
        toggleItemSelection(id, selectedEntities);
    };

    const onOverNode = (node) => {
        setSelectedEntity(node.entity)
    };
    const onOutNode = (node) => {
        // setSelectedEntity(null);
    };
    const graphID = entities.reduce((acc, val) => acc + val.id, '').hashCode()
    return (
        <div
            key={graphID}
        >
            <Sigma
                renderer="webgl"
                graph={generateGraph()}
                settings={graphSettings}
                style={graphStyle}
                onClickNode={(e) => onClickNode(e.data.node.id, selectedEntities)}
                onOverNode={(e) => onOverNode(e.data.node)}
                onOutNode={(e) => onOutNode(e.data.node)}
            >
                <SigmaEnableWebGL/>
                <RandomizeNodePositions>
                    <ForceAtlas2 worker
                                 scalingRatio={1}
                                 slowDown={10}
                                 linLogMode={false}
                                 iterationsPerRender={1}
                                 timeout={entities.length / 100 * 1000}
                    />

                    <UpdateNodeProps visibleEntities={visibleEntitiesIDS} selectedEntities={selectedEntities}/>
                </RandomizeNodePositions>
            </Sigma>
            {
                selectedEntity &&
                <div id={'entityPreView'}>
                    <User key={selectedEntity.id} entity={selectedEntity}/>
                </div>
            }
        </div>
    )
};


const mapStateToProps = (state) => {
    return {
        connections: state.workSpace.entities.connections,
        entities: getObjects(state, 'entities', state.workSpace.entities.items)
    }
};

const mapDispatchToProps = ({});

export default connect(mapStateToProps, mapDispatchToProps)(EntitiesGraph);
