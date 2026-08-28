import React, {useEffect, useState} from "react";
import {Checkbox, Dimmer, Input, Loader, Radio, Segment} from "semantic-ui-react";

import {connect} from "react-redux";
import './style.less'
import NoContent from "../utils/NoContent";
import {selectEntities, setEntitiesSearchValue, toggleEntitySelection} from "../../store/entitiesReducer";
import {getObjects} from "../../store/utils";
import SearchIcon from "../utils/SearchIcon";
import EntitiesGraph from "./EntitiesGraph";
import EntitiesList from "./EntitiesList";


const EntitiesPanel = ({searchValue, selectEntities, entitiesIDS, entities, isLoading, setSearchValue, ...props}) => {
    const noContent = <NoContent height={500} text={'Тут будут пользователи, группы, посты или прочая медиа информация'}
                                 popup={'Введите запрос в поисковую строку сверху'}/>;
    const selectedEntities = props.selectedEntities;
    const [isNotValidHidden, changeNotValidHiddenMode] = useState(true);
    const [isGraphView, setGraphView] = useState(false);


    const isEntityVisible = (entity) => {
        const fitToSearch = (search, value) => {
            if (!search)
                return true;
            if (!value)
                return false;
            return String(value).toLowerCase().includes(search.toLowerCase());
        };
        const ids = searchValue.split(', ');
        if (ids.length > 1) {
            return (!isNotValidHidden || entity.valid) && ids.includes(entity.id);
        }
        return (!isNotValidHidden || entity.valid) && (
            fitToSearch(searchValue, entity.name) ||
            fitToSearch(searchValue, entity.username) ||
            fitToSearch(searchValue, entity.id)
        );
    };


    const visibleEntities = entities.filter(item => isEntityVisible(item));

    // if (!visibleEntities.length && isNotValidHidden)
    //     changeNotValidHiddenMode(false);

    const menuItemStyle = {display: 'flex', alignItems: 'center'};
    return (
        <Dimmer.Dimmable blurring as={Segment} clearing dimmed={false}
                         style={{display: 'flex', flexDirection: 'column', maxHeight: '100%'}}>
            {
                entities.length > 0 ?
                    <>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            marginBottom: '1rem',
                            marginLeft: '0.5rem',
                            marginRight: '0.5rem',
                            justifyContent: 'space-between'
                        }}>
                            <Input value={searchValue}
                                   onChange={(e, data) => setSearchValue(data.value)}
                                   size={'mini'}
                                   icon={<SearchIcon isInputStringEmpty={!searchValue.length}
                                                     onClose={() => setSearchValue('')}/>}
                            />
                            <div style={menuItemStyle}>
                                <div style={{paddingRight: '0.5rem'}}>{'Выделить'}</div>
                                <Checkbox
                                    indeterminate={
                                        selectedEntities.length > 0 && (visibleEntities.length !== selectedEntities.length)
                                    }
                                    checked={visibleEntities.length === selectedEntities.length}
                                    onChange={(e, data) => {
                                        const selected = data.checked;
                                        if (selected)
                                            selectEntities(visibleEntities.map(item => item.id));
                                        else
                                            selectEntities([]);
                                    }}
                                />
                            </div>
                            <div style={menuItemStyle}>
                                <div style={{paddingRight: '0.5rem'}}>Скрыть невалид</div>
                                <Checkbox onClick={((e, data) => changeNotValidHiddenMode(data.checked))}
                                          checked={isNotValidHidden}
                                />
                            </div>
                            <div style={menuItemStyle}>

                                <div style={{marginRight: '1rem'}}>Список</div>
                                <Radio checked={isGraphView}
                                       onChange={(e, data) => setGraphView(data.checked)} toggle/>
                                <div style={{marginLeft: '1rem'}}>Граф</div>
                            </div>
                            <Dimmer inverted active={isLoading}>
                                <Loader style={{top: '150px'}} active/>
                            </Dimmer>

                        </div>
                        {isGraphView ?
                            <EntitiesGraph
                                visibleEntities={visibleEntities} toggleItemSelection={props.toggleEntitySelection}
                                selectedEntities={[...selectedEntities]}
                            /> :
                            <EntitiesList visibleEntities={visibleEntities}
                                          toggleItemSelection={props.toggleEntitySelection}
                                          selectedEntities={selectedEntities}/>
                        }
                    </> : noContent
            }

        </Dimmer.Dimmable>
    )

};

const mapStateToProps = (state) => {
    const entitiesIDS = state.workSpace.entities.items;
    const entities = getObjects(state, 'entities', entitiesIDS);
    return {
        entitiesIDS: entitiesIDS,
        entities: entities,
        isLoading: state.workSpace.entities.isLoading,
        selectedEntities: state.workSpace.entities.selectedItems,
        searchValue: state.workSpace.entities.searchValue
    }
};

const mapDispatchToProps = {
    selectEntities,
    toggleEntitySelection,
    setSearchValue: setEntitiesSearchValue
};

export default connect(mapStateToProps, mapDispatchToProps)(EntitiesPanel);
