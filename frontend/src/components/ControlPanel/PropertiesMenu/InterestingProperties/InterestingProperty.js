import React, { Component } from "react";
import { Table, Icon, Popup } from "semantic-ui-react";
import "./style.less";

function Confidence({ level }) {
  const maxFilled = 5;
  const filled = level * maxFilled;
  const items = Array(maxFilled)
    .fill()
    .map((_, i) => (
      <div
        key={i}
        className={
          "confidenceLevel " + (maxFilled - i <= filled ? "levelFilled" : "")
        }
      />
    ));

  return <div>{items}</div>;
}

const actionButtonsData = {
  doNotHaveProperty: {
    popupText: "Показать людей, не обладающих этим свойством",
    iconName: "arrow alternate circle left outline"
  },
  haveProperty: {
    popupText: "Показать только людей с данным свойством",
    iconName: "arrow alternate circle right outline"
  },
  decreaseOrder: {
    popupText: "Отсортировать в порядке убывания",
    iconName: "angle double right"
  },
  increaseOrder: {
    popupText: "Отсортировать в порядке возрастания",
    iconName: "angle double left"
  }
};

export default class InterestingProperty extends Component {
  state = {
    active: false
  };
  render() {
    const propertyItem = this.props.propertyItem;
    let actionNames = [];
    if (propertyItem.type === "show")
      actionNames = ["haveProperty", "doNotHaveProperty"];
    else if (propertyItem.type === "order")
      actionNames = ["decreaseOrder", "increaseOrder"];
    const actionButtons = actionNames.map(actionName => (
      <Popup
        key={actionName}
        mouseEnterDelay={500}
        position="top right"
        content={actionButtonsData[actionName].popupText}
        trigger={
          <Icon
            color="grey"
            className="actionButton"
            name={actionButtonsData[actionName].iconName}
          />
        }
      />
    ));
    const moveToAllProperties = (allPropID) => {
      this.props.moveToAll(allPropID);
    };
    return (
      <Table.Row
        onMouseOver={() => this.setState({ active: true })}
        onMouseLeave={() => this.setState({ active: false })}
        onClick={()=>moveToAllProperties(propertyItem.id.split('.')[0])}
        className="property"
      >
        <Table.Cell width="10">{propertyItem.name}</Table.Cell>
        <Table.Cell width="5" style={{ wordWrap: "break-word" }}>
          {propertyItem.value}
        </Table.Cell>
        <Table.Cell width="2" className="confidenceCell">
          {this.state.active
            ? actionButtons
            : "confidence" in propertyItem && (
                <Confidence level={propertyItem.confidence} />
              )}
        </Table.Cell>
      </Table.Row>
    );
  }
}
