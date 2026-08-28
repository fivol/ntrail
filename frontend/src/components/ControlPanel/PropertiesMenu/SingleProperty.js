import React from 'react';
import {Icon, Table} from "semantic-ui-react";
import {round} from "../../../utils";
import {setEntitiesItemsList} from "../../../store/entitiesReducer";
import {connect} from "react-redux";


const SingleProperty = (props) => {
    const {id, value, name, ids} = props.propertyDict;
    return (
        <Table.Row
            onClick={() => props.onClick ? props.onClick(id) : null}
            key={id}>
            <Table.Cell width="10">{name}</Table.Cell>
            <Table.Cell width="5">{round(value, 2)}</Table.Cell>
            <Table.Cell width="2">
                {
                    ids &&
                    <Icon link
                          name="eye"
                          color="grey"
                          onClick={
                              (e) => {
                                  e.stopPropagation();
                                  props.setEntitiesItemsList(ids)
                              }
                          }
                    />
                }
            </Table.Cell>
        </Table.Row>
    )
};

const mapDispatchToState = ({
    setEntitiesItemsList
})

export default connect(undefined, mapDispatchToState)(SingleProperty);
