import React from "react";
import {Accordion, Form, Icon} from "semantic-ui-react";


export const formInputComponent = (props) => {
    const submit = props.submit;
    const canSubmit = (props.input.value && submit);
    const searchIcon = {
        name: 'search', link: true, onClick: e => {
            e.preventDefault();
            submit()
        }
    };
    return (
        <Form.Input
            onKeyDown={e => {
                if (e.keyCode === 13) {
                    submit()
                }
            }}
            icon={canSubmit ? searchIcon : undefined}

            {...{
                ...props,
                ...props.input,
                error: props.meta.error,
                onChange: (e, data) => {
                    if (!data)
                        return props.input.onChange(e);
                    return props.input.onChange(data.value)
                }
            }}
        />
    )
};

const formComponentGenerator = (TargetComponent, submit) => {
    return (
        props => {
            console.log('Form Wrapper props', props);
            let valueName = 'value';
            if (typeof props.input.value === 'boolean')
                valueName = 'checked';
            const canSubmit = (props.input.value && submit);
            const searchIcon = {
                name: 'search', link: true, onClick: e => {
                    e.preventDefault();
                    submit()
                }
            };
            return (
                <TargetComponent
                    onKeyDown={e => {
                        if (e.keyCode === 13) {
                            submit()
                        }
                    }}
                    icon={canSubmit ? searchIcon : undefined}

                    {...{
                        ...props,
                        ...props.input,
                        value: undefined,
                        [valueName]: props.input.value,
                        error: props.meta.error,
                        onChange: (e, data) => {
                            if (!data)
                                return props.input.onChange(e);
                            return props.input.onChange(data[valueName])
                        }
                    }}
                />
            )
        }
    )
};

export default formComponentGenerator;