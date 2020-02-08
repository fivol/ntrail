import React, {useState} from 'react';
import {
    CartesianGrid,
    Cell,
    Line,
    LineChart,
    Pie,
    PieChart,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import './style.less';
import {Checkbox, Popup} from "semantic-ui-react";

function getBaseLog(x, y) {
    return Math.log(y) / Math.log(x);
}

const CircularPlot = ({onSelectItem, width, height, data}) => {
    return (
        <PieChart width={width} height={height}>
            <Pie onClick={onSelectItem} data={data} fill="#8884d8" label={entry => entry.name}>
                {
                    data.map((entry, index) => <Cell key={`cell-${index}`}
                                                     fill={entry.color ? entry.color : '#000000'}/>)
                }
            </Pie>
            <Tooltip/>
        </PieChart>
    )
};

const LinePlot = ({width, height, data, onSelectItem}) => {

    const [isLogMode, setLogMode] = useState(false);

    const logModeChange = (e, data) => {
        setLogMode(data.checked)
    };

    if (isLogMode) {
        data = data.map(item => ({...item, value: getBaseLog(1.1,item.value + 1)}))
    }

    return (
        <>
            <LineChart
                onClick={onSelectItem}
                width={width}
                height={height}
                data={data}
                margin={{
                    top: 5, right: 30, left: 0, bottom: 5,
                }}
            >
                <CartesianGrid strokeDasharray="3 3"/>
                <YAxis/>
                <XAxis hide dataKey={'name'}/>
                <Tooltip/>
                <Line type="monotone" dataKey="value" stroke="#8884d8" activeDot={{r: 8}}/>
            </LineChart>
            <Checkbox onChange={logModeChange} checked={isLogMode} label={'Логорифмический режим'}/>
        </>
    )
};

const Plot = ({type, data, onSelectNode}) => {

    const onSelectItem = (event) => {
        console.log(event);
        if (event && event.activePayload)
            onSelectNode(event.activePayload[0].payload);
        else if (event && event.payload && event.payload.payload)
            onSelectNode(event.payload.payload);

    };

    const width = 500;
    const height = 300;
    const plotProps = {
        width,
        height,
        data,
        onSelectItem
    };
    return (
        <div className={'plotWidget'} onClick={e => e.stopPropagation()}>
            {
                type === 'line' &&
                <LinePlot {...plotProps}/>
            }
            {
                type === 'circular' &&
                <CircularPlot {...plotProps}/>
            }
        </div>
    );
};


export const PlotPopup = (props) => {

    return (
        <Popup pinned
               basic
               trigger={props.trigger} on={'click'}
               flowing
               position={'top right'}>
            <div style={{textAlign: 'center', marginBottom: '0.5rem'}}>{props.header}</div>
            <Plot {...props}/>
        </Popup>
    )
};

export default Plot;