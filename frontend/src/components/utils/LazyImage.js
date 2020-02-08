import {Visibility, Image, Placeholder} from 'semantic-ui-react'
import React from 'react';
import defaultImg from '../../media/defaultAvatar.png'

export default class LazyImage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            show: false,
            src: defaultImg
        };
        this.ref = React.createRef();
    }

    showImage = () => {
        this.setState({
            show: true,
        })
    };

    // checkImageOnScreen() {
    //     const inRange = (value, min, max) => {
    //         return (value >= min) && (value <= max);
    //     };
    //     const {x, y} = this.ref.current.getBoundingClientRect();
    //     if (inRange(x, 0, window.screen.width) && inRange(y, 0, window.screen.height)) {
    //         console.log('show avatar');
    //
    //         this.setState({show: true})
    //     }
    // }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (this.ref.current)
            this.ref.current.update()
    }

    render() {
        const {src} = this.props;
        if (!this.state.show) {
            return (
                <div>
                    <Visibility ref={this.ref} fireOnMount onOnScreen={this.showImage}>
                        <Placeholder style={{height: 100, width: 90}}>
                            <Placeholder.Image/>
                        </Placeholder>
                    </Visibility>
                </div>
            )
        }
        return <Image {...this.props} src={this.state.src} onLoad={() => this.setState({src})}/>
    }
}