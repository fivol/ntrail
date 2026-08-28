import React, { Component } from "react";
import { Button, Dimmer, Form, Header, Grid, Segment } from "semantic-ui-react";

export default class Authorizing extends Component {
  render() {
    return (
      <Dimmer active={true} onClickOutside={this.props.handleClose} page>
        <Grid textAlign="center" verticalAlign="middle">
          <Grid.Column style={{ maxWidth: 450, minWidth: 360 }}>
            <Header as="h2" color="teal" textAlign="center">
              Войти в аккаунт
            </Header>
            <Form size="large">
              <Segment stacked>
                <Form.Input
                  fluid
                  icon="user"
                  iconPosition="left"
                  placeholder="Логин или почта"
                />
                <Form.Input
                  fluid
                  icon="lock"
                  iconPosition="left"
                  placeholder="Пароль"
                  type="password"
                />

                <Button color="teal" fluid size="large">
                  Войти
                </Button>
              </Segment>
            </Form>
            <Button
              style={{ marginTop: "15px" }}
              inverted
              color="teal"
              fluid
              size="large"
            >
              Зарегистрироваться
            </Button>
          </Grid.Column>
        </Grid>
      </Dimmer>
    );
  }
}
