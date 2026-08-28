import React, { Component } from "react";
import { Button, Header, Menu } from "semantic-ui-react";
import Authorizing from "./Authorizing/Authorizing";

export default class PageHeader extends Component {
  state = {
    status: "base"
  };
  render() {
    return (
      <div>
        <Menu secondary>
          <Menu.Item style={{ padding: 0 }}>
            <Header as="h1">NTrail</Header>
          </Menu.Item>

          <Menu.Item position="right" style={{ padding: 0 }}>
            <Button secondary style={{ marginRight: "0.5em" }}>
              Как пользоваться?
            </Button>
            <Button primary onClick={() => this.setState({ status: "auth" })}>
              Войти
            </Button>
            {this.state.status === "auth" && (
              <Authorizing
                handleClose={() => {
                  this.setState({ status: "base" });
                }}
              />
            )}
          </Menu.Item>
        </Menu>
        <p style={{ fontSize: "1.23em" }}>Ваш проводник по миру соцсетей</p>
      </div>
    );
  }
}
