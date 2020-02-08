import React from 'react';
import {Field, reduxForm} from "redux-form";
import {Accordion, Form, Icon} from "semantic-ui-react";
import FormComponentWrapper from "../../utils/ReduxFormComponentWrapper";


const SocialNetworksAccordion = props => {
    return (
        <Accordion>
            <Accordion.Accordion>
                <Accordion.Title active>
                    <Icon name="dropdown"/>
                    ВК
                </Accordion.Title>
                <Accordion.Content active>
                    <Field component={Form.Input}
                           name={'vkSearchQuery'}
                           label={'Поиск в социальной сети ВКонтакте'}
                           placeholder={'Иван Иванов, мемы каждый день'}/>
                    <Form.Group>
                        <Field component={FormComponentWrapper(Form.Checkbox, 'checked')} name={'usersInclude'}
                               label={'Люди'}/>
                        <Field component={FormComponentWrapper(Form.Checkbox, 'checked')} name={'groupsInclude'}
                               label={'Группы'}/>
                        <Field component={FormComponentWrapper(Form.Checkbox, 'checked')} name={'postsInclude'}
                               label={'Посты'}/>
                    </Form.Group>
                    <Form.Input label={'По ключевым словам'} placeholder={'Москва, школа, рисование, футбол'}/>
                </Accordion.Content>
            </Accordion.Accordion>
        </Accordion>
    )
};

const maxAmount1000Validation = (value) => Number(value) > 1000 ? 'Максимальное значение: 1000' : undefined;

const ServerSearch = props => {
    return (
        <Form autoComplete={'off'}>
            <Field
                name={'limit'}
                normalize={(value, previousValue) => {
                    if (Number(value) || value === '')
                        return value;
                    return previousValue;
                }}
                component={FormComponentWrapper(Form.Input)}
                validate={maxAmount1000Validation}
                label={'Максимальное количество объектов'}
            />
            <Field component={Form.Input}
                   name={'commonQueryString'}
                   label={'Универсальная поисковая строка'}
                   placeholder={'nagibator666'}/>
            <SocialNetworksAccordion/>
        </Form>
    )
};

export default reduxForm(
    {
        form: 'StringSearch',
        onSubmit: ()=>console.log('submit'),
    }
)(ServerSearch);
