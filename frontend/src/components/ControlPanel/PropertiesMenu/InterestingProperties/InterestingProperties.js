import React from "react";
import {Table} from "semantic-ui-react";
import "./style.less";

import InterestingProperty from "./InterestingProperty";
import {connect} from "react-redux";
import SingleProperty from "../SingleProperty";


const InterestingProperties = (props) => {
    return (
        <div  style={{maxHeight: '65vh', overflow: 'auto', scrollbarWidth: 'none'}}>
            <Table columns={props.importantProperties.length}>
                <Table.Header>
                    <Table.Row>
                        {props.importantProperties.map(item => (
                            <Table.HeaderCell
                                key={item.name}
                                className="propertyTableHeader"
                            >
                                {item.name}
                            </Table.HeaderCell>
                        ))}
                    </Table.Row>
                </Table.Header>
                <Table.Body>
                    <Table.Row>
                        {props.importantProperties.map(item => (
                            <Table.Cell key={item.id}>{item.value}</Table.Cell>
                        ))}
                    </Table.Row>
                </Table.Body>
            </Table>
            <Table selectable fixed >
                <Table.Header>
                    <Table.Row>
                        <Table.HeaderCell className="propertyTableHeader" width={10}>
                            Название
                        </Table.HeaderCell>
                        <Table.HeaderCell className="propertyTableHeader" width={5}>
                            Значение
                        </Table.HeaderCell>
                        <Table.HeaderCell width={2}/>
                    </Table.Row>
                </Table.Header>
                <Table.Body>
                    {props.interestingProperties.map((propertyItem) => (
                        <SingleProperty propertyDict={propertyItem} onClick={props.moveToAll}/>
                    ))}
                </Table.Body>
            </Table>
        </div>
    )
};

const mapStateToProps = (state) => ({
        importantProperties: state.workSpace.controls.properties.important,
        interestingProperties: state.workSpace.controls.properties.interesting
    }
);

export default connect(mapStateToProps)(InterestingProperties)
