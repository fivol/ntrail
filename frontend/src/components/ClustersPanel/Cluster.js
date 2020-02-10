import React, {useLayoutEffect, useRef, useState} from "react";
import "./style.less";
import {Checkbox} from "semantic-ui-react";

function ClusterImages(props) {
    const photos = props.photos;
    const calculatePhotoCSS = (size, idx) => {
        const css = {
            zIndex: -idx + 100
        };
        if (size === 1)
            return css;
        if (size === 2)
            return {...css, left: 2 + 80 / size * idx + '%'};
        return {...css, left: 75 / size * idx + '%'};
    };


    return (
        <div className="imagesContainer">
            {photos.map((url, idx) => (
                <img
                    key={idx}
                    style={calculatePhotoCSS(photos.length, idx)}
                    className="previewClusterImage"
                    src={url}
                    alt=""
                />
            ))}
        </div>
    );
}

const Cluster = ({clusterData, chooseCluster, selected, x, y, dragCluster, ...props}) => {
    const {photos} = clusterData;
    const [dimensions, setDimensions] = useState({width: 0, height: 0});

    const clusterCss = {
        zIndex: selected ? 100 : 0,
        left: x - dimensions['width'] / 2 + 'px',
        top: y - dimensions['height'] / 2 + 'px',
        width: clusterData.size + "rem",
    };
    const targetRef = useRef();

    useLayoutEffect(() => {
        if (targetRef.current) {
            setDimensions({
                width: targetRef.current.offsetWidth,
                height: targetRef.current.offsetHeight
            });
        }
    }, []);

    const clusterContainerClasses = [
        'clusterObject',
        selected && 'selectedCluster',
        props.isOverlay && 'overlayCluster'
    ];
    return (
        <div
            ref={targetRef}
            onMouseDown={(e) => {
                e.preventDefault();
                chooseCluster(clusterData.id)
            }}
            style={clusterCss} className={clusterContainerClasses.join(' ')}>
            {(selected || props.showCheckbox) &&
            <Checkbox checked={props.highlighted}
                      onMouseDown={e => e.stopPropagation()}
                      onClick={e => e.stopPropagation()}
                      onChange={(e) => {
                          props.toggleClusterHighlight(clusterData.id)
                      }}
                      style={{zIndex: '103', position: 'absolute', right: '0.5rem', top: '0.5rem'}}/>}
            <ClusterImages
                photos={photos}/>

            <div style={{display: 'flex', justifyContent: 'center', textAlign: 'center', alignItems: 'center'}}>
                <div>{clusterData.name} </div>

            </div>

        </div>
    );

}
export default Cluster
