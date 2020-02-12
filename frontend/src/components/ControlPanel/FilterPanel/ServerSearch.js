import React, {useState} from 'react';
import {Field, reduxForm} from "redux-form";
import {Accordion, Form, Icon} from "semantic-ui-react";
import formComponentGenerator, {formInputComponent} from "../../utils/ReduxFormComponentWrapper";
import {connect} from "react-redux";
import {submitFilterSearch} from "../../../store/controlsReducer";


const maxAmount1000Validation = (value) => Number(value) > 1000 ? 'Максимальное значение: 1000' : undefined;

const ServerSearch = ({handleSubmit, ...props}) => {
    handleSubmit = handleSubmit(props.submitFilterSearch);
    const [activeItem, setActiveItem] = useState('vk');
    const toggleActiveItem = (value) => {
        setActiveItem(activeItem === value ? '' : value)
    };
    console.log('ServerSearch form props', props);
    return (
        <Form autoComplete={'off'}>
            <Field
                name={'limit'}
                normalize={(value, previousValue) => {
                    if (Number(value))
                        return Number(value).toString();
                    if(!value)
                        return '0';
                    return previousValue;
                }}
                component={formComponentGenerator(Form.Input)}
                validate={maxAmount1000Validation}
                label={'Максимальное количество объектов'}
            />
            <Field component={formComponentGenerator(Form.Input, handleSubmit)}
                   name={'commonQueryString'}
                   label={'Универсальная поисковая строка'}
                   placeholder={'nagibator666'}/>

            <Accordion>
                <Accordion.Accordion>
                    <Accordion.Title onClick={() => toggleActiveItem('vk')} active={activeItem === 'vk'}>
                        <Icon name="dropdown"/>
                        ВК
                    </Accordion.Title>
                    <Accordion.Content active={activeItem === 'vk'}>
                        <Field component={formInputComponent}
                               submit={handleSubmit}
                               name={'vkSearchQuery'}
                               label={'Поиск в социальной сети ВКонтакте'}
                               placeholder={'Иван Иванов, artur97, мемы'}/>
                        <Form.Group>
                            <Field component={formComponentGenerator(Form.Checkbox)}
                                   name={'vkUsersInclude'}
                                   label={'Люди'}/>
                            <Field component={formComponentGenerator(Form.Checkbox)}
                                   name={'vkGroupsInclude'}
                                   label={'Группы'}/>
                            <Field component={formComponentGenerator(Form.Checkbox)}
                                   name={'vkPostsInclude'}
                                   label={'Посты'}/>
                        </Form.Group>
                    </Accordion.Content>
                </Accordion.Accordion>
            </Accordion>
        </Form>
    )
};

const mapDispatchToProps = ({
    submitFilterSearch
});

export default connect(null, mapDispatchToProps)(
    reduxForm(
        {
            form: 'ServerSearch',
            initialValues: {
                limit: 1000,
                vkUsersInclude: true,
                vkGroupsInclude: false,
                vkPostsInclude: false
            },
        }
    )(ServerSearch));
