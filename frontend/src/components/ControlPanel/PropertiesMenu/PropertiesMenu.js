import React, {Component} from "react";
import {Menu} from "semantic-ui-react";

import InterestingProperties from "./InterestingProperties/InterestingProperties";
import AllProperties from "./AllProperties/AllProperties";

export default class PropertiesPanel extends Component {
    state = {
        activeItem: "all",
        openedPropID: null
    };
    clickMenu = (e, {name}) => {
        this.setState({activeItem: name});
    };

    openAllMenuWithProp = (propID) => {
        console.log(propID);
        this.setState({
            activeItem: 'all',
            openedPropID: propID.split('.')[0]
        })
    };

    render() {
        const {activeItem} = this.state;
        return (
            <div>
                <Menu secondary size="tiny">
                    <Menu.Item
                        onClick={this.clickMenu}
                        active={activeItem === "interesting"}
                        name="interesting"
                        content="Интересные"
                    />
                    <Menu.Item
                        onClick={this.clickMenu}
                        active={activeItem === "all"}
                        name="all"
                        content="Все"
                    />
                </Menu>
                {activeItem === "interesting" ? (
                    <InterestingProperties moveToAll={this.openAllMenuWithProp}/>
                ) : (
                    <AllProperties openedPropID={this.state.openedPropID}/>
                )}
            </div>
        );
    }
}
