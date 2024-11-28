import { createContext, useContext, useEffect, useState } from "react";
import instance from "../api/instance";

const backendUrl = "http://localhost:3000";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const chat = async (message) => {
    try {
      setLoading(true);
      const response = await instance.post(`${backendUrl}/chat`, { message });

      if (response.status === 200) {
        console.log("메시지 전송 성공:", response.data.messages[0].text);
        const { messages: resp } = response.data;
        setMessages((prevMessages) => [...prevMessages, ...resp]);
      } else {
        console.error(
          "메시지 전송 실패: ",
          response.status,
          response.statusText
        );
      }
    } catch (error) {
      console.error("메시지 전송 중 오류 발생:", error);
    } finally {
      setLoading(false);
    }
  };
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};
