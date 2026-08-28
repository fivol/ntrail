import React from 'react';
import {Button, Header, Icon} from "semantic-ui-react";
import iconCircleSum from '../../../media/SVG/circles black and grey/SVG/2.svg'
import iconCircleDiff from '../../../media/SVG/circles black and grey/SVG/4.svg'
import iconCircleSymDiff from '../../../media/SVG/circles black and grey/SVG/3.svg'
import iconCircleUnion from '../../../media/SVG/circles black and grey/SVG/1.svg'
import {connect} from "react-redux";
import {
    deleteFromCluster,
    deleteSelectedClusters,
    downloadWorkSpace, getFriendsAction,
    intersectClusters, pickOutToCluster,
    subtractClusters, symDiffClusters,
    unionClusters,
    uploadWorkSpace
} from "../../../store/actions";


const ActionPanelButton = (props) => {
    const style = {
        display: 'flex',
        alignItems: 'center',
    };
    const imgSize = '1.5rem';
    const iconStyle = {
        display: 'inline-block',
        marginRight: '5px',
        width: imgSize,
        height: 'auto'
    };
    const icon = typeof props.icon === 'object' ? props.icon : <img src={props.icon} alt={'afs'} style={iconStyle}/>;
    return (
        <Button basic onClick={props.onClick}>
            <div style={style}>
                <div style={{width: '1rem'}}>{icon}</div>
                <div style={{margin: 'auto'}}>{props.text}</div>
            </div>
        </Button>
    )
};

const ActionsPanel = (props) => {
    const headerMargin = '0.2rem';
    return <div>
        <Header size={'small'} style={{marginLeft: headerMargin, marginTop: '1rem'}}>Холст</Header>
        <Button.Group vertical basic style={{width: '100%'}}>
            {
                props.haveClusters &&
                <ActionPanelButton onClick={props.downloadWorkSpace} text={'Сохранить рабочее пространсто'}
                                   icon={<Icon name={'download'}/>}/>
            }
            <ActionPanelButton onClick={props.uploadWorkSpace} text={'Загрузить рабочее пространство'}
                               icon={<Icon name={'upload'}/>}/>

        </Button.Group>
        {
            props.selectedEntitiesCount > 0 &&
            <>
                <Header size={'small'} style={{marginLeft: headerMargin}}>Выделенные профили</Header>
                <Button.Group vertical basic style={{width: '100%'}}>
                    <ActionPanelButton onClick={props.pickOutToCluster} text={'Выделить в отдельный кластер'}
                                       icon={<Icon name={'dot circle outline'}/>}/>
                    <ActionPanelButton onClick={props.deleteFromCluster} text={'Удалить из кластера'} icon={<Icon name={'remove circle'}/>}/>
                    {
                        props.selectedEntitiesCount === 1 &&
                        <ActionPanelButton text={'Запустить полный анализ'} icon={<Icon name={'shekel'}/>}/>
                    }
                    <ActionPanelButton onClick={props.getFriendsAction} text={'Получить друзей'}
                                       icon={<Icon name={'user circle'}/>}/>
                    <ActionPanelButton text={'Получить подписки'} icon={<Icon name={'address book outline'}/>}/>
                    <ActionPanelButton text={'Получить подписчиков'} icon={<Icon name={'comment alternate'}/>}/>
                </Button.Group>
            </>
        }
        {
            props.selectedClustersCount > 0 &&
            <>
                <Header size={'small'} style={{marginLeft: headerMargin}}>Выделенные кластеры</Header>
                <Button.Group basic compact vertical style={{width: '100%'}}>
                    {
                        props.selectedClustersCount === 2 &&
                        <ActionPanelButton text={'Сравнить'} icon={<Icon name={'sun outline'}/>}/>
                    }
                    {
                        props.selectedClustersCount >= 2 &&
                        <>
                            <ActionPanelButton onClick={props.intersectClusters} text={'Пересечение'}
                                               icon={iconCircleUnion}/>
                            <ActionPanelButton onClick={props.unionClusters} text={'Объединение'} icon={iconCircleSum}/>
                            <ActionPanelButton onClick={props.subtractClusters} text={'Разность'}
                                               icon={iconCircleDiff}/>
                            <ActionPanelButton onClick={props.symDiffClusters} text={'Симметрическая разность'}
                                               icon={iconCircleSymDiff}/>
                        </>
                    }
                    <ActionPanelButton onClick={props.deleteSelectedClusters} text={'Удалить выделенные'}
                                       icon={<Icon name={'trash alternate outline'}/>}/>
                </Button.Group>
            </>
        }


    </div>
};

const mapStateToProps = state => {
    return {
        selectedClustersCount: state.workSpace.clusters.highlightedClusters.length,
        selectedEntitiesCount: state.workSpace.entities.selectedItems.length,
        haveClusters: state.workSpace.clusters.items.length > 0
    }
};
const mapDispatchToProps = {
    downloadWorkSpace,
    uploadWorkSpace,
    intersectClusters,
    unionClusters,
    subtractClusters,
    symDiffClusters,
    pickOutToCluster,
    deleteSelectedClusters,
    getFriendsAction,
    deleteFromCluster
};

export default connect(mapStateToProps, mapDispatchToProps)(ActionsPanel)