import React from "react";
import {Segment, Input, Message, Icon} from "semantic-ui-react";
import "./style.less";
import {connect} from "react-redux";
import {closeMessage, executeQuery, removeHints, selectHint, typeSymbol} from "../../store/searchReducer";
import Hints from "./SearchHints";

const SearchPanel = (props) => {
    const [focused, setFocus] = React.useState(false);
    const value = (focused && !props.placeholder.startsWith('Введите') && !props.value.length) ?
        props.placeholder :
        props.value;
    const beginExecuteQueryString = (query) => {
        if(!props.error){
            props.executeQuery(query);
        }
    };
    return (
        <Segment basic style={{marginBottom: "1rem", padding: 0}}>
            {
                props.message.draw &&
                <Message
                    error={props.message.error}
                    warning={props.message.warning}
                >
                    <Icon onClick={props.closeMessage} name='close'/>
                    <Message.Header>{props.message.header}</Message.Header>
                    <p>
                        {props.message.body}
                    </p>
                </Message>
            }
            <Input
                onChange={(e, data) => props.typeSymbol(data.value)}
                fluid
                onFocus={(e) => {
                    setFocus(true)
                }}
                onBlur={() => {
                    props.removeHints();
                    setFocus(false);
                }}
                loading={props.loading}
                error={props.error}
                value={value}
                icon={{
                    name: "search",
                    circular: false,
                    link: true,
                    onClick: e => beginExecuteQueryString(props.value)
                }}
                placeholder={props.placeholder}
                onKeyDown={e => {
                    if (e.keyCode === 13 && !props.hints.length) {
                        beginExecuteQueryString(value)
                    }
                }}
            />
            {props.hints.length > 0 && (
                <Hints
                    marginLeftSymbols={props.value.length}
                    chooseElement={props.selectHint}
                    unmountHints={props.removeHints}
                    values={props.hints}
                />
            )}
        </Segment>
    )
};

const mapStateToProps = (state) => ({
    hints: state.workSpace.search.currentHints,
    value: state.workSpace.search.queryString,
    loading: state.workSpace.search.isLoading,
    placeholder: state.workSpace.search.placeholder,
    error: state.workSpace.search.isError,
    warning: state.workSpace.search.isWarning,
    message: state.workSpace.search.message,
});
const mapDispatchToProps = {
    executeQuery,
    typeSymbol,
    selectHint,
    removeHints,
    closeMessage
};

export default connect(mapStateToProps, mapDispatchToProps)(SearchPanel)
