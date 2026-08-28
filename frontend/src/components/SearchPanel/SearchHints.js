import React, {Component} from "react";
import "./style.less";


export default class Hints extends Component {
    constructor(props) {
        super(props);
        this.state = {
            activeIndex: 0
        };
        document.onkeydown = e => {
            switch (e.keyCode) {
                case 13:
                    this.props.chooseElement(this.props.values[this.state.activeIndex]);
                    break;
                case 27:
                    this.props.unmountHints();
                    break;
                case 38:
                    e.preventDefault();
                    this.setState({
                        activeIndex: Math.max(this.state.activeIndex - 1, 0)
                    });
                    break;
                case 40:
                    e.preventDefault();
                    this.setState({
                        activeIndex: Math.min(
                            this.state.activeIndex + 1,
                            this.props.values.length - 1
                        )
                    });
                    break;
                default:
                    break;
            }
        };
    }

    componentWillUnmount() {
        document.onkeydown = undefined;
    }

    render() {
        const {values} = this.props;
        return (
            <div
                style={{marginLeft: this.props.marginLeftSymbols * 7 + "px"}}
                id="hintsList"
            >
                {values.map((name, idx) => (
                    <div
                        onMouseDown={e => {
                            this.props.chooseElement(
                                this.props.values[Number(e.target.getAttribute("index"))]
                            );
                        }}
                        key={name}
                        index={idx}
                        className={
                            "hintsListItem " +
                            (this.state.activeIndex === idx && "activeHint")
                        }
                    >
                        {name}
                    </div>
                ))}
            </div>
        );
    }
}
