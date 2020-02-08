import React from "react";
import {Dropdown} from "semantic-ui-react";
import {connect} from "react-redux";
import StringSearch from "./StringSearch";
import {changeFilterMode} from "../../../store/controlsReducer";
import ServerSearch from "./ServerSearch";


const PageSearch = props => {
    return (
        <></>
    )
};


const FilterPanel = ({searchMode, ...props}) => {
    const searchModeOptions = [
        {key: 'net', text: 'Из интернета (обращаться к API различных сервисов)', value: 'net'},
        {key: 'cache', text: 'Из баз данных NTrail (закешированные запросы)', value: 'cache'},
        {key: 'page', text: 'С данной страницы (уже полученное с сервера)', value: 'page'},
        {key: 'text', text: 'Извлечь данные из строки', value: 'text'},
    ];
    return (
        <div
            style={{marginTop: '1rem'}}>
            <b>Откуда брать информацию</b>
            <Dropdown
                value={searchMode}
                onChange={(e, data) => props.changeFilterMode(data.value)}
                fluid selection
                options={searchModeOptions}
                style={{marginBottom: '1rem'}}
            />
            {
                searchMode === 'text' &&
                <StringSearch/>
            }
            {
                (searchMode === 'net' || searchMode === 'cache') &&
                <ServerSearch/>
            }
            {
                (searchMode === 'page') &&
                <PageSearch/>
            }
        </div>
    );
};

const mapStateToProps = state => {
    return {
        searchMode: state.workSpace.controls.filterMode
    }
};
const mapDispatchToProps = ({
    changeFilterMode
});


export default connect(mapStateToProps, mapDispatchToProps)(FilterPanel)
