import { useState } from "react";
import "./App.css";

type Message = {
  role: "user" | "assistant";
  content: string;
};


const API_URL = import.meta.env.VITE_API_URL;

const getToken = async (): Promise<string> => {
  const tokenData = sessionStorage.getItem("access_token");

  if (tokenData){
    const data = JSON.parse(tokenData)
    if (Date.now() >= data.expiresAt) {
      // Token expired
      sessionStorage.removeItem("access_token");
    }else{
      console.log("Access token from sesson storage : ", data.access_token)
      return data.access_token
    }
  }


  const response = await fetch(`${API_URL}/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: "Vijay"
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to generate token");
  }

  const data = await response.json();
  console.log("Access token : ", data.access_token)

  sessionStorage.setItem("access_token", JSON.stringify({
                                        "access_token": data.access_token, 
                                        expiresAt: Date.now() + 30 * 60 * 1000,    // Expire time 30 mins
                                        }));

  return data.access_token;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    const message = input.trim();

    if (!message || loading) {
      return;
    }

    // Add user's message to UI immediately
    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: message,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const token = await getToken();

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/conversations/6ec70578-5ed2-43c1-9eff-1abb75a87183/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: message,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to get response from server");
      }

      if (!response.body) {
        throw new Error("Response body is empty");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Add empty assistant message first
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: "",
        },
      ]);

      let assistantMessage = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        const chunk = decoder.decode(value, {
          stream: true,
        });

        assistantMessage += chunk;

        // Update the LAST assistant message
        setMessages((previous) => {
          const updated = [...previous];

          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: assistantMessage,
          };

          return updated;
        });
      }

    } catch (error) {
      console.error(error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: "Sorry, something went wrong.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>My Chatbot</h1>
      </header>

      <main className="messages">
        {messages.length === 0 && (
          <div className="welcome">
            <h2>Hello 👋</h2>
            <p>How can I help you today?</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role}`}
          >
            <div className="message-content">
              {message.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-content">
              Thinking...
            </div>
          </div>
        )}
      </main>

      <footer className="input-area">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          rows={1}
          disabled={loading}
        />

        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </footer>
    </div>
  );
}

export default App;