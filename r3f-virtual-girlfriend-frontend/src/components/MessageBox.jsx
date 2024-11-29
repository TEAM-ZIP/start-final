const MessageBox = ({ type, text }) => {
  let boxClass = "flex p-3 bg-[#E9F9EC] rounded-xl max-w-md h-auto";

  switch (type) {
    case "user":
      boxClass =
        "flex p-3 bg-[#A1ACA4] rounded-xl max-w-md h-auto bg-opacity-50 self-end";
      break;
    case "system":
      boxClass = "flex p-3 bg-[#E9F9EC] rounded-xl max-w-md h-auto self-start";
  }

  return <div className={boxClass}>{text}</div>;
};

export default MessageBox;
