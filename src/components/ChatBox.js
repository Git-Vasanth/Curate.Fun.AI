import React, { useState, useEffect, useRef } from "react";
import { Container, Box, TextField, Paper, Typography, IconButton } from "@mui/material";
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import io from "socket.io-client";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { solarizedlight, dark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import FavoriteBorderOutlinedIcon from '@mui/icons-material/FavoriteBorderOutlined';
import ThumbUpOutlinedIcon from '@mui/icons-material/ThumbUpOutlined';
import ThumbDownOutlinedIcon from '@mui/icons-material/ThumbDownOutlined';
import SentimentDissatisfiedOutlinedIcon from '@mui/icons-material/SentimentDissatisfiedOutlined';


const socket = io("http://localhost:5000");

const ChatBox = ({ isDarkMode }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const messagesEndRef = useRef(null); // Ref for auto-scrolling

  // Effect for auto-scrolling to the latest message (existing)
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Socket.IO message listener (existing)
  useEffect(() => {
    socket.on("message", (msg) => {
      setMessages((prevMessages) => [...prevMessages, msg]);
    });

    return () => {
      socket.off("message");
    };
  }, []);

  const handleSendMessage = () => {
    if (newMessage.trim() !== "") {
      socket.emit("chatMessage", { text: newMessage, sender: "user" });
      setNewMessage(""); // This clears the input field
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // --- NEW: Handler for reaction buttons ---
  const handleReaction = (messageIndex, reactionType) => {
    console.log(`Message Index: ${messageIndex}, Reaction: ${reactionType}`);
    // You would typically send this to the backend
    socket.emit('ai_reaction', { messageIndex: messageIndex, reaction: reactionType });

    // Optional: You could update the UI here to show the reaction (e.g., change icon color)
    // For simplicity, we'll just log and send to backend for now.
  };
  // --- END NEW Handler ---


  const MarkdownComponents = {
    p: ({ node, ...props }) => <Typography variant="body1" sx={{ mb: 1, whiteSpace: 'pre-wrap', wordBreak: 'break-word', textAlign: 'left' }} {...props} />,
    h1: ({ node, ...props }) => <Typography variant="h5" sx={{ mt: 2, mb: 1.5, fontWeight: 'bold', textAlign: 'left' }} {...props} />,
    h2: ({ node, ...props }) => <Typography variant="h6" sx={{ mt: 2, mb: 1.5, fontWeight: 'bold', textAlign: 'left' }} {...props} />,
    h3: ({ node, ...props }) => <Typography variant="subtitle1" sx={{ mt: 1.5, mb: 1, fontWeight: 'bold', textAlign: 'left' }} {...props} />,
    code: ({ node, inline, className, children, ...props }) => {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={isDarkMode ? dark : solarizedlight}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code style={{
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
          padding: '2px 4px',
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontSize: '0.9em',
          color: isDarkMode ? '#90CAF9' : '#C2185B'
        }} {...props}>
          {children}
        </code>
      );
    },
    ul: ({ node, ...props }) => <Typography component="ul" sx={{ ml: 2, mb: 1, textAlign: 'left' }} {...props} />,
    ol: ({ node, ...props }) => <Typography component="ol" sx={{ ml: 2, mb: 1, textAlign: 'left' }} {...props} />,
    li: ({ node, ...props }) => <Typography component="li" variant="body2" sx={{ mb: 0.5, textAlign: 'left' }} {...props} />,
    blockquote: ({ node, ...props }) => (
      <Box
        component="blockquote"
        sx={{
          borderLeft: `4px solid ${isDarkMode ? '#61dafb' : '#2196f3'}`,
          pl: 2,
          py: 0.5,
          my: 1,
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
          borderRadius: 1,
          fontStyle: 'italic',
          color: isDarkMode ? '#ccc' : '#555',
          textAlign: 'left' // Ensuring blockquotes are also left-aligned
        }}
        {...props}
      />
    ),
    a: ({ node, ...props }) => (
      <a style={{ color: isDarkMode ? '#90CAF9' : '#1976D2', textDecoration: 'underline' }} {...props} />
    ),
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 0 }}>
      <Box
        sx={{
          height: "68vh",
          display: "flex",
          flexDirection: "column",
          border: isDarkMode ? "1.5px solid #33c9dc" : "1.5px solid #834bff",
          borderRadius: "8px",
          p: 5,
          backgroundColor: isDarkMode ? "#555" : "#cfd8dc",
          boxShadow: 5,
        }}
      >
        {/* Messages Section */}
        <Box
          sx={{
            flex: 1,
            overflowY: "auto",
            maxHeight: "60vh",
            mb: 2,
            paddingRight: "8px",
          }}
        >
          {messages.map((message, index) => (
            <Box
              key={index} // Using index as a temporary ID for reaction
              sx={{
                mb: 1,
                display: "flex",
                justifyContent: message.sender === "user" ? "flex-end" : "flex-start"
              }}
            >
              <Paper
                sx={{
                  p: 1.5,
                  maxWidth: "70%",
                  backgroundColor:
                    message.sender === "user"
                      ? isDarkMode ? "#3f51b5" : "#d1e7fd"
                      : isDarkMode ? "#444" : "#f0f0f0",
                  color: isDarkMode ? "#fff" : "#000",
                  borderRadius: 2,
                  textAlign: message.sender === "ai" ? 'left' : 'inherit', // AI message content is left-aligned
                  '& pre': {
                      maxHeight: '200px',
                      overflowY: 'auto',
                      borderRadius: '4px',
                      p: 1,
                      fontSize: '0.85em',
                      lineHeight: 1.4,
                      backgroundColor: isDarkMode ? '#222' : '#eee',
                      color: isDarkMode ? '#fff' : '#333'
                  },
                  '& p': {
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }
                }}
              >
                {message.sender === "ai" ? (
                  <>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={MarkdownComponents}
                    >
                      {message.text}
                    </ReactMarkdown>
                    <Box sx={{
                      display: 'flex',
                      gap: 0.5,
                      mt: 1,
                      justifyContent: 'flex-end',
                      pr: 0.5
                    }}>
                      {/* --- MODIFIED: Added onClick handlers to IconButtons --- */}
                      <IconButton size="small" sx={{ color: isDarkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)' }}
                        onClick={() => handleReaction(index, 'love')}>
                        <FavoriteBorderOutlinedIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" sx={{ color: isDarkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)' }}
                        onClick={() => handleReaction(index, 'like')}>
                        <ThumbUpOutlinedIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" sx={{ color: isDarkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)' }}
                        onClick={() => handleReaction(index, 'dislike')}>
                        <ThumbDownOutlinedIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" sx={{ color: isDarkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)' }}
                        onClick={() => handleReaction(index, 'disappointed')}>
                        <SentimentDissatisfiedOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </>
                ) : (
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {message.text}
                  </Typography>
                )}
              </Paper>
            </Box>
          ))}
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Section */}
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <TextField
            fullWidth
            variant="standard"
            label="Type a message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            multiline
            maxRows={4}
            sx={{
              mr: 1,
              "& .MuiInputBase-root": {
                color: isDarkMode ? "#fff" : "#000",
              },
              "& .MuiInputLabel-root": {
                color: isDarkMode ? "#bbb" : "#666",
                "&.Mui-focused": {
                  color: isDarkMode ? "#90CAF9" : "#3e2723",
                },
              },
              "& .MuiInput-underline:after": {
                borderBottomColor: isDarkMode ? "#90CAF9" : "#3e2723",
              },
              "& .MuiInputBase-input": {
                color: isDarkMode ? "#fff" : "#000",
              },
            }}
            InputLabelProps={{
              shrink: true,
            }}
          />

          {/* Send Icon in a square box */}
          <Box
            sx={{
              width: 50,
              height: 50,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              borderRadius: "12px",
              backgroundColor: isDarkMode ? "#b388ff" : "#ba68c8",
              cursor: "pointer",
              "&:hover": {
                backgroundColor: isDarkMode ? "#2c387e" : "#a3c7f7",
              },
            }}
            onClick={handleSendMessage}
            tabIndex={0}
          >
            <SendRoundedIcon sx={{ color: isDarkMode ? "#fff" : "#000" }} />
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default ChatBox;