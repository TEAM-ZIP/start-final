import { useRef, useState, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import MessageBox from "./MessageBox";

export const UI = ({ hidden, ...props }) => {
  const endOfMessages = useRef();
  const { chat, loading, message, setSystemRes, systemRes } = useChat();
  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (!loading && !message && input.trim() !== "") {
      const userMessage = { text: input, type: "user" };
      setSystemRes((prevMessages) => [...prevMessages, userMessage]);

      chat(input);
      setInput("");
    }
  };

  useEffect(() => {
    if (endOfMessages.current) {
      endOfMessages.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [systemRes]);

  if (hidden) return null;

  return (
    <>
      <div className="fixed top-0 left-0 right-0 bottom-0 z-10 flex justify-between p-4 flex-col">
        <div className="self-start backdrop-blur-md bg-white bg-opacity-50 p-4 rounded-lg pointer-events-auto">
          <h1 className="font-black text-xl">척척박사 쏙쏙이</h1>
          <p>궁금한 사항이 있으면 언제든지 물어보세요!</p>
        </div>
        <div
          className="flex gap-3 mx-[100px] w-3/6 my-10 self-end flex-col max-h-[80%] overflow-y-auto z-10 pointer-events-auto scrollbar-thin scrollbar-thumb-[#9ABFA2] scrollbar-track-transparent "
          onWheel={(e) => e.stopPropagation()} // 휠 이벤트 차단
        >
          {systemRes.map((msg, index) => (
            <MessageBox key={index} text={msg.text} type={msg.type} />
          ))}
          <div ref={endOfMessages}></div>
        </div>
        <div className="flex items-center gap-2 max-w-screen-md w-full mx-auto pointer-events-auto">
          <input
            className="w-full placeholder:text-gray-600 placeholder:italic p-4 rounded-md bg-opacity-50 bg-white backdrop-blur-md"
            placeholder="자립 준비 청년 관련해서 궁금한 주거, 취업, 금융 정보를 물어보세요!"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();
              }
            }}
          />
          <button
            disabled={loading || message}
            onClick={sendMessage}
            className={`bg-[#9ABFA2] hover:bg-[#64926E] text-white p-4 px-10 font-semibold uppercase rounded-md whitespace-nowrap ${
              loading || message ? "cursor-not-allowed opacity-30" : ""
            }`}
          >
            전송
          </button>
        </div>
      </div>
    </>
  );
};
