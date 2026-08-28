import React from 'react';
import {Field, reduxForm} from "redux-form";
import {Button, Form} from "semantic-ui-react";
import formComponentGenerator from "../../utils/ReduxFormComponentWrapper";
import {connect} from "react-redux";
import {extractFromString} from "../../../store/actions";


const StringSearch = props => {
    return (
        <Form onSubmit={props.handleSubmit(props.extractFromString)}>
            <p>Можете сделать <b>поиск</b> с помощью вк, нажать правой кнопкой мыши на странице, затем <b>Page
                source</b>, скопировать весь текст и вставить сюда (или просто ctrl + U)</p>
            <Field name={'text'}
                   component={formComponentGenerator(Form.TextArea)}
            />
            <Button type={'submit'} content={'Извлечь'}
                    style={{marginTop: '0.2rem'}} fluid basic/>
        </Form>
    )
};

const mapDispatchToProps = ({
    extractFromString
});
export default connect(() => ({}), mapDispatchToProps)(reduxForm(
    {
        form: 'StringSearch',
    }
)(StringSearch));
