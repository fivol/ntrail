import React from "react";
import "./style.less";
import lockImg from "./lock.png";
import verifyImg from "../../../media/vkverified.svg";
import LazyImage from "../../utils/LazyImage";

export default function UserAvatar(props) {
    const entity = props.entity;
    let baseClasses = ["userContainer "];
    if (props.selected) baseClasses.push("choosed");
    const borderColor = entity.properties.sex === 2 ? "blue" : "red";
    const lockIcon = <img src={lockImg} className="lock" alt="lock"/>;
    const verifyIcon = <img src={verifyImg} className="verified" alt="verified"/>;

    return (
        <div
            onClick={props.toggleSelection}
            onContextMenu={
                e => {
                    e.preventDefault();
                    props.toggleSelection();
                }
            }
            className={baseClasses.join(" ")}>
            <LazyImage
                onMouseMove={e => e.preventDefault()}
                onMouseDown={e => e.preventDefault()}
                style={{borderColor: borderColor}}
                size={'tiny'}
                circular
                bordered={false}
                centered
                className="avatar"
                title={entity.id}
                src={entity.img}
                alt=""
            />
            {entity.private === 1 && lockIcon}
            {entity.verified === 1 && verifyIcon}
            <a
                onMouseDown={e=>e.stopPropagation()}
                onClick={e=>e.stopPropagation()}
                className="userName"
                href={entity.url}
                target="_blank"
                rel="noopener noreferrer"
            >
                <div>{entity.name}</div>

                {
                    entity.secondName &&
                    <div>{entity.secondName}</div>
                }
            </a>
        </div>
    );
}
