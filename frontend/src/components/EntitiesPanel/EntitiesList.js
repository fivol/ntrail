import React, {useEffect, useState} from 'react';
import UserAvatar from "./UserAvatar/User";


const EntitiesList = ({visibleEntities, toggleItemSelection, ...props}) => {
    const [visibleItemsCount, setVisibleItemsCount] = useState(60);

    const onScroll = (percents) => {
        if (percents > 0.7) {
            if (visibleEntities.length > visibleItemsCount) {
                console.log(percents);
                setVisibleItemsCount(Math.max(visibleItemsCount + 20, parseInt(visibleItemsCount * 1.2)))
            }
        }
    };
    useEffect(() => {
        setVisibleItemsCount(60);
    }, [visibleEntities]);

    const entitiesToShow = visibleEntities.slice(0, visibleItemsCount);
    return (
        <div className="entitiesContainer" style={{maxHeight: '70vh', overflow: 'auto'}}
             onScroll={(e) => onScroll(e.target.scrollTop / (e.target.scrollHeight - e.target.clientHeight))}>


            {entitiesToShow.map((obj) => (
                <UserAvatar
                    entity={obj}
                    key={obj.id}
                    selected={props.selectedEntities.includes(obj.id)}
                    toggleSelection={() => toggleItemSelection(obj.id)}
                />
            ))}
        </div>
    )
};

export default EntitiesList;
