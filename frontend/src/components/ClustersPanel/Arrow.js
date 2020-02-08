import React from 'react';


const Arrow = ({x1, x2, y1, y2, shorten}) => {
    // shorten - значение, на которое надо сократить срелку с обеих сторон
    const shiftX = x2 - x1;
    const shiftY = y2 - y1;
    if (!shorten) shorten = 0;
    const lineLength = Math.sqrt(shiftX*shiftX + shiftY*shiftY);
    const newLength = lineLength - shorten * 2;
    const minLength = 20;
    if(shorten && (lineLength < minLength || newLength < minLength)){
        return <line/>
    }
    const lengthFraction = newLength / lineLength;
    const newShiftX = shiftX * lengthFraction;
    const newShiftY = shiftY * lengthFraction;
    x1 += (shiftX - newShiftX) / 2;
    y1 += (shiftY - newShiftY) / 2;
    x2 = x1 + newShiftX;
    y2 = y1 + newShiftY;

    // debugger
    return (
        <line x1={x1 + 'px'} y1={y1 + 'px'} x2={x2 + 'px'} y2={y2 + 'px'} stroke="black"/>
    )
}

export default Arrow;
