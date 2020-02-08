import React, {useEffect, useState} from "react";
import {Accordion, Icon, Input, Table} from "semantic-ui-react";
import {connect} from "react-redux";
import SearchIcon from "../../../utils/SearchIcon";
import {PlotPopup} from "../../../Plot/Plot";
import {setEntitiesItemsList} from "../../../../store/entitiesReducer";
import {getObj} from "../../../../store/utils";
import {round} from "../../../../utils";
import SingleProperty from "../SingleProperty";

const AllProperties = (props) => {
    const [searchValue, setInputValue] = useState('');
    const [activeIDS, setActiveIDS] = useState([]);
    const [properties, setProperties] = useState(props.allProperties);

    const toggleProperty = (e, titleProps) => {
        const itemId = titleProps.index;

        if (activeIDS.includes(itemId))
            setActiveIDS(activeIDS.filter(item => item !== itemId));
        else
            setActiveIDS([...activeIDS, itemId])
    };

    const searchStringChange = (value) => {
        const newProperties = [];
        for (let property of properties) {
            const {name} = property;
            if (name.toLowerCase().indexOf(value.toLowerCase()) !== -1) {
                newProperties.push(property);
            }
        }
        setInputValue(value);
        if (!value) {
            setProperties(props.allProperties);
            setActiveIDS([]);
        } else {
            setProperties(newProperties);
            if (newProperties.length)
                setActiveIDS([newProperties[0].id]);
        }
    };
    useEffect(() => {
        if (props.allProperties !== properties) {
            setProperties(props.allProperties);
            setActiveIDS([]);
        }
        if (props.openedPropID) {
            const openedID = props.openedPropID;
            setActiveIDS([props.openedPropID]);
            const newProps = [...props.allProperties];
            newProps.sort((a, b) => (b.id === openedID ? 1 : -1));
            setProperties(newProps);
        }
    }, [props.allProperties, props.openedPropID]);
    return (
        <>
            <Input fluid
                   icon={<SearchIcon isInputStringEmpty={!searchValue.length} onClose={() => searchStringChange('')}/>}
                   value={searchValue}
                   placeholder={'Грамотность, 12, школа, общественные статус'}
                   onChange={(e, data) => {
                       searchStringChange(data.value)
                   }}
            />
            <Accordion style={{maxHeight: '61.5vh', overflow: 'auto', scrollbarWidth: 'none'}}>
                {properties.map((property) => {
                    return (
                        <Accordion.Accordion key={property.id}>
                            <Accordion.Title
                                index={property.id}
                                active={activeIDS.includes(property.id)}
                                onClick={toggleProperty}
                            >
                                <Icon name="dropdown"/>
                                {props.activePropertyId === property.id ? <b>{property.name}</b> : property.name}
                                {
                                    property.plot &&
                                    <PlotPopup data={property.plot.data}
                                               type={property.plot.type}
                                               onSelectNode={(node) => props.setEntitiesItemsList(node.ids)}
                                               header={property.name}
                                               trigger={<Icon
                                                   link
                                                   onClick={e => e.stopPropagation()}
                                                   circular
                                                   style={{float: "right"}}
                                                   name="chart line"
                                               />}/>
                                }
                            </Accordion.Title>
                            <Accordion.Content active={activeIDS.includes(property.id)}>
                                <Table selectable>
                                    <Table.Body>
                                        {property.values.map(subProperty => (
                                            <SingleProperty key={subProperty.id} propertyDict={subProperty}/>
                                        ))}
                                    </Table.Body>
                                </Table>
                            </Accordion.Content>
                        </Accordion.Accordion>
                    )
                })}
            </Accordion>
        </>
    );
};

const mapStateToProps = (state) => ({
    allProperties: state.workSpace.controls.properties.all,
    mainID: getObj(state, 'clusters', state.workSpace.clusters.selectedClusterID)
});

const mapDispatchToProps = ({
    setEntitiesItemsList
});

export default connect(mapStateToProps, mapDispatchToProps)(AllProperties)
