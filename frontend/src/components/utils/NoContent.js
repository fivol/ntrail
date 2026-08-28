import React from 'react';
import QuestionPopup from "./QuestionPopup";


const NoContent = (props) => {
    let minHeight = 300;
    if (props.height)
        minHeight = props.height;
    const noContentCss = {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: minHeight + "px",
        width: '100%'
    };
    return (
        <div style={noContentCss}>
            <div style={{float: "left"}}>{props.text}</div>
            &nbsp;&nbsp;
            <QuestionPopup
                text={props.popup}
            />
        </div>
    );
}

export default NoContent;
