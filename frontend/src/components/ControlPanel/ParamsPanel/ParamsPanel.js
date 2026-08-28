import React from 'react';
import {Form} from "semantic-ui-react";
import {connect} from "react-redux";
import {getObjects} from "../../../store/utils";

const CopyPasteInput = ({value, label, component, condition}) => {
    if (condition === undefined)
        condition = true;
    if (!value || !condition)
        return <></>;
    let Component = Form.Input;
    if (component)
        Component = component;

    return <Component value={value} label={label}/>;
};


const ParamsPanel = (props) => {
    console.log(props);
    return (
        <Form style={{marginTop: '1rem'}}>
            <CopyPasteInput label={'ID текущего кластера'} value={props.clusterID}/>
            <CopyPasteInput component={Form.TextArea} label={'ID выделенных кластеров'}
                            value={props.selectedClustersID.join('\n')}/>

            <Form.Group widths={'2'}>
                <CopyPasteInput label={'Количество Кластеров'} value={props.clustersCount}/>
                <CopyPasteInput label={'Размер текущего кластера'} value={props.entitiesCount}/>
            </Form.Group>
            <Form.Group widths={'2'}>
                <CopyPasteInput label={'ID выбранных сущностей'} value={props.selectedEntitiesID.join(', ')}/>
                <CopyPasteInput label={'К-во выбранных сущностей'} value={props.selectedEntitiesID.length}/>
            </Form.Group>


            <CopyPasteInput component={Form.TextArea}
                            label={'Ссылки на выбранные сущности'}
                            value={props.selectedEntitiesURLS.join('\n')}/>
        </Form>
    )
};

const mapStateToProps = state => {
    return {
        clusterID: state.workSpace.clusters.selectedClusterID,
        selectedEntitiesID: state.workSpace.entities.selectedItems,
        selectedEntitiesURLS: getObjects(state, 'entities', state.workSpace.entities.selectedItems).map(item => item.url),
        clustersCount: state.workSpace.clusters.items.length,
        entitiesCount: state.workSpace.entities.items.length,
        selectedClustersID: state.workSpace.clusters.highlightedClusters
    }
};

export default connect(mapStateToProps)(ParamsPanel);
