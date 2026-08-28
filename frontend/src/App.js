import React from "react";
import "./_variables.less";
import "semantic-ui-less/semantic.less";
import './utils'

import {Container, Grid} from "semantic-ui-react";

import PageHeader from "./components/PageHeader/PageHeader";
import ControlPanel from "./components/ControlPanel/ControlPanel";
import ClustersPanel from "./components/ClustersPanel/ClustersPanel";
import EntitiesPanel from "./components/EntitiesPanel/EntitiesPanel";
import SearchPanel from "./components/SearchPanel/SearchPanel";

function App() {
    return (
        <Container style={{padding: "3rem", width: '90vw', height: '100vh', display: 'flex', flexDirection: 'column'}}>
            <PageHeader/>
            <SearchPanel/>

            <Grid columns="equal" style={{flexGrow: '1'}}>
                <Grid.Column width={4}>
                    <ClustersPanel/>
                </Grid.Column>

                <Grid.Column width={7}>
                    <EntitiesPanel/>
                </Grid.Column>

                <Grid.Column width={5}>
                    <ControlPanel/>
                </Grid.Column>
            </Grid>
        </Container>
    );
}

export default App;
