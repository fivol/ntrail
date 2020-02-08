import React from "react";

const FormComponentWrapper = (TargetComponent, valueName) => {
    if (!valueName)
        valueName = 'value';
    return (
        props => {
            console.log('Form Wrapper props', props);
            return (
                <TargetComponent
                    {...props}
                    {...{
                        ...props.input,
                        value: undefined,
                        [valueName]: props.input.value
                    }}
                    error={props.meta.error}
                    onChange={(e, data) => {
                        if (!data)
                            return props.input.onChange(e);
                        return props.input.onChange(data[valueName].trim())
                    }}/>
            )
        }
    )
};

export default FormComponentWrapper;