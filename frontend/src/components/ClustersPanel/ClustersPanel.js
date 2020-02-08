import React from "react";
import {Button, Segment} from "semantic-ui-react";
import {connect} from "react-redux";
import NoContent from "../utils/NoContent";
import {deleteCluster, reloadCluster, selectCluster, setHighlightedClusters} from "../../store/clustersReducer";
import {clearAll} from "../../store/workSpaceReducer";
import ClustersAnimate from "./ClustersAnimate";
import {shuffle} from "../../utils";
import {getObj} from "../../store/utils";

const ClustersPanel = (props) => {
    console.log('Clusters connections', props.connections)
    const noContent = <NoContent
        popup={"Создайте объект в рабочем поле (центральное), чтобы добавить кластер"}
        text={'Кластеров пока нет'}
    />;

    return (
        <Segment className={'clustersPanel'}>{
            props.haveControlButtons &&
            (<Button.Group compact size={'tiny'} widths='3'>
                <Button onClick={props.clearAll} basic color={'red'} icon={'delete'} content={'Очистить'}/>
                <Button onClick={props.deleteCluster} basic color={'orange'} icon={'trash alternate outline'}
                        content={'Удалить'}/>
                <Button onClick={props.reloadCluster} basic color={'blue'} icon={'sync alternate'}
                        content={'Обновить'}/>
            </Button.Group>)
        }

            {props.clusters.length === 0
                ? noContent
                : <ClustersAnimate {...props}/>
            }
            {
                props.haveSelectionActions &&
                (<Button.Group compact size={'tiny'} widths='2' style={{marginBottom: '0.2rem'}}>
                    <Button onClick={() => props.setHighlightedClusters([])} color={'grey'} basic
                            icon={'circle outline'}
                            content={'Снять выделение'}/>
                    <Button onClick={() => props.setHighlightedClusters(props.clustersID)} color={'grey'} basic
                            icon={'circle'}
                            content={'Выделить все'}/>
                </Button.Group>)
            }
        </Segment>
    );
};

const mapStateToProps = (state) => {
    const clustersID = state.workSpace.clusters.items;
    const clustersData = clustersID.map(id => {
        const data = getObj(state, 'clusters', id);
        const entitiesID = data.entities.items;
        let randomIDS = [...entitiesID];
        shuffle(randomIDS);
        const photos = randomIDS.slice(0, 3).map(id => getObj(state, 'entities', id).img);
        return {
            ...data.params,
            photos: photos
        }
    });

    return {
        clusters: clustersData,
        clustersID: clustersID,
        connections: state.workSpace.clusters.connections,
        selectedClusterID: state.workSpace.clusters.selectedClusterID,
        haveControlButtons: state.workSpace.clusters.items.length > 0,
        highlightedClusters: state.workSpace.clusters.highlightedClusters,
        haveSelectionActions: state.workSpace.clusters.highlightedClusters.length > 0
    }
};

const mapDispatchToProps = {
    selectCluster,
    deleteCluster,
    reloadCluster,
    clearAll,
    setHighlightedClusters
};

export default connect(mapStateToProps, mapDispatchToProps)(ClustersPanel)