import React from "react";
import { Popup, Icon } from "semantic-ui-react";

export default ({ text, position }) => {
  return (
    <Popup
      position={position}
      content={text}
      trigger={<Icon color="grey" name="question circle" />}
    />
  );
};
