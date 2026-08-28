import React from "react";
import {Segment, Menu} from "semantic-ui-react";
import './style.less'

import PropertiesMenu from "./PropertiesMenu/PropertiesMenu";
import FilterPanel from "./FilterPanel/FilterPanel";
import ActionsPanel from "./ActionsPanel/ActionsPanel";
import {connect} from "react-redux";
import {selectMenu} from "../../store/controlsReducer";
import ParamsPanel from "./ParamsPanel/ParamsPanel";

const ControlPanel = (props) => {
    const {activeItem} = props;
    let menu = <PropertiesMenu/>;
    if (activeItem === 'actions')
        menu = <ActionsPanel/>;
    else if (activeItem === 'filter')
        menu = <FilterPanel/>;
    else if (activeItem === 'params')
        menu = <ParamsPanel/>;
    return (
        <Segment>
            <Menu secondary
                  widths={props.haveClusters ? 4 : 2}
                  style={{marginBottom: "0.2rem"}}
            >
                {
                    props.haveClusters &&
                    <Menu.Item
                        active={activeItem === "properties"}
                        name="properties"
                        content='Свойства'
                        onClick={() => props.selectMenu('properties')}
                    />
                }
                <Menu.Item
                    onClick={() => props.selectMenu('filter')}
                    active={activeItem === "filter"}
                    name="filter"
                    className={'controlMenu'}
                    content="Фильтр"
                />
                <Menu.Item
                    onClick={() => props.selectMenu('actions')}
                    active={activeItem === "actions"}
                    name="actions"
                    content="Действия"
                />
                {
                    props.haveClusters &&
                    <Menu.Item
                        onClick={() => props.selectMenu('params')}
                        active={activeItem === "params"}
                        name="params"
                        content="Параметры"
                    />
                }

            </Menu>
            {menu}
        </Segment>
    );
};

const mapStateToProps = (state) => ({
    activeItem: state.workSpace.controls.activeItem,
    haveClusters: state.workSpace.clusters.items.length > 0
});
const mapDispatchToProps = {
    selectMenu
};

export default connect(mapStateToProps, mapDispatchToProps)(ControlPanel)
