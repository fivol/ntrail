import {Icon} from "semantic-ui-react";
import React from "react";

const SearchIcon = ({isInputStringEmpty, onClose, onSearch}) => {
    if (onClose === undefined) onClose = () => {
    };
    if (onSearch === undefined) onSearch = () => {
    };
    return <Icon
        name={isInputStringEmpty ? 'search' : 'close'}
        onClick={
            () => {
                isInputStringEmpty ? onSearch() : onClose()
            }
        }
        link
    />
};

export default SearchIcon;