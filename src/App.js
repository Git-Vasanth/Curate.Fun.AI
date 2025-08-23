import React, { useState } from "react";
import { Box, Typography, IconButton, Dialog, DialogTitle, DialogContent, TextField, DialogActions, Button } from "@mui/material";
import ChatBox from './components/ChatBox';
import yourLogo from './logo.png'; // Adjust as necessary

// Material-UI Icons
import PermIdentityIcon from '@mui/icons-material/PermIdentity';
import InfoIcon from '@mui/icons-material/Info';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import { X as CloseIcon } from 'lucide-react'; // For the close icon in the dialog

// Import your existing AdminPage component
// Make sure this path is correct based on your file structure (e.g., './admin' or './pages/AdminPage')
import AdminPanel from './components/admin';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false); // State for dark mode

  // --- NEW STATE FOR ADMIN LOGIN ---
  const [openAdminDialog, setOpenAdminDialog] = useState(false); // Controls visibility of password dialog
  const [adminPasswordInput, setAdminPasswordInput] = useState(''); // Stores password input
  const [adminPasswordError, setAdminPasswordError] = useState(''); // Stores password error message
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false); // Tracks if admin is logged in

  // --- IMPORTANT: Define your static 10-digit password here ---
  const STATIC_ADMIN_PASSWORD = '1111111111'; // <<< REPLACE THIS!

  // Function to toggle dark and light theme
  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Function to navigate to the website
  const handleNavigate = () => {
    window.open("https://www.curate.fun/", "_blank"); // Navigate to the website
  };

  // Function for PermIdentity (placeholder for now)
  const handlePermIdentityClick = () => {
    window.open("https://www.linkedin.com/in/vasanth-shastri", "_blank")
  };

  // Function for InfoIcon click
  const handleInfoClick = () => {
    console.log("Info button clicked!");
  };

  // --- NEW ADMIN DIALOG HANDLERS ---
  const handleAdminClick = () => {
    setOpenAdminDialog(true); // Open the password dialog
    setAdminPasswordInput(''); // Clear any previous input
    setAdminPasswordError(''); // Clear any previous error
  };

  const handleCloseAdminDialog = () => {
    setOpenAdminDialog(false); // Close the password dialog
    setAdminPasswordError(''); // Clear error on close
  };

  const handleAdminPasswordChange = (event) => {
    setAdminPasswordInput(event.target.value);
    // Clear error as user types
    if (adminPasswordError) {
      setAdminPasswordError('');
    }
  };

  const handleAdminPasswordSubmit = () => {
    if (adminPasswordInput.length !== 10) {
      setAdminPasswordError('Password must be 10 digits long.');
      return;
    }
    if (adminPasswordInput === STATIC_ADMIN_PASSWORD) {
      setIsAdminLoggedIn(true); // Set admin logged in state to true
      setOpenAdminDialog(false); // Close the dialog
      setAdminPasswordError(''); // Clear any error
    } else {
      setAdminPasswordError('Incorrect password. Please try again.');
    }
  };

  // Function to handle logout from admin page
  // This function will be passed to your AdminPage component
  const handleAdminLogout = () => {
    setIsAdminLoggedIn(false);
    setAdminPasswordInput(''); // Clear password state on logout
  };

  // Conditional rendering: If admin is logged in, show AdminPage, otherwise show main App content
  if (isAdminLoggedIn) {
    // Pass the logout function to your AdminPage component
    return <AdminPanel onLogout={handleAdminLogout} />;
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        backgroundColor: isDarkMode ? "#333" : "#f4f4f4",
        color: isDarkMode ? "#fff" : "#000",
        textAlign: "center",
        p: 0,
        position: "relative", // Ensure this is relative for absolute positioning of children
        boxSizing: "border-box",
      }}
    >
      {/* Inject the font using <style> tag */}
      <style>
        {`
          @import url('https://fonts.googleapis.com/css2?family=Londrina+Solid:wght@100;300;400;900&display=swap');
        `}
      </style>

      {/* Left-aligned Icons */}
      <Box
        sx={{
          position: "absolute",
          top: 20,
          left: 20,
          display: "flex",
          alignItems: "center",
          gap: 2,
        }}
      >
        {/* Globe Icon Button */}
        <IconButton onClick={handleNavigate} sx={{ color: isDarkMode ? "#fff" : "#000" }}>
          🌐
        </IconButton>

        {/* Info Icon Button */}
        <IconButton onClick={handleInfoClick} sx={{ color: isDarkMode ? "#fff" : "#000" }}>
          <InfoIcon sx={{ fontSize: '2rem' }} />
        </IconButton>
      </Box>

      {/* Container for Logo and Heading (remains centered) */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          mb: 2,
        }}
      >
        {/* Logo */}
        <img
          src={yourLogo}
          alt="Curate.Fun Logo"
          style={{
            maxWidth: "75px",
            height: "auto",
          }}
        />

        {/* Heading with Londrina Solid Font */}
        <Typography
          variant="h1"
          sx={{
            fontFamily: '"Londrina Solid", sans-serif',
            fontWeight: 400,
            fontSize: "4rem",
            color: isDarkMode ? "#fff" : "#333",
            letterSpacing: "5px",
          }}
        >
          Curate.Fun
        </Typography>
      </Box>

      {/* Right-aligned Icons */}
      <Box
        sx={{
          position: "absolute",
          top: 20,
          right: 20,
          display: "flex",
          alignItems: "center",
          gap: 2,
        }}
      >
        {/* PermIdentity Icon Button */}
        <IconButton onClick={handlePermIdentityClick} sx={{ color: isDarkMode ? "#fff" : "#000" }}>
          <PermIdentityIcon sx={{ fontSize: '2rem' }} />
        </IconButton>

        {/* Admin Panel Settings Icon Button (Now opens modal) */}
        <IconButton onClick={handleAdminClick} sx={{ color: isDarkMode ? "#fff" : "#000" }}>
          <AdminPanelSettingsIcon sx={{ fontSize: '2rem' }} />
        </IconButton>

        {/* Dark Mode Toggle Button */}
        <IconButton onClick={toggleDarkMode} sx={{ color: isDarkMode ? "#fff" : "#000" }}>
          {isDarkMode ? "🌙" : "☀️"}
        </IconButton>
      </Box>

      {/* Chat Box */}
      <ChatBox isDarkMode={isDarkMode} />

      {/* Admin Password Verification Dialog */}
      <Dialog open={openAdminDialog} onClose={handleCloseAdminDialog} aria-labelledby="admin-password-dialog-title">
        <DialogTitle id="admin-password-dialog-title" sx={{ position: 'relative', pr: 6 }}>
          Admin Access Required
          <IconButton
            aria-label="close"
            onClick={handleCloseAdminDialog}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <CloseIcon size={20} />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <TextField
            autoFocus
            margin="dense"
            id="admin-password"
            label="Enter 10-Digit Password"
            type="password"
            fullWidth
            variant="outlined"
            value={adminPasswordInput}
            onChange={handleAdminPasswordChange}
            error={!!adminPasswordError}
            helperText={adminPasswordError}
            inputProps={{ maxLength: 10 }} // Enforce 10 digits
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAdminPasswordSubmit();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAdminDialog} color="secondary">
            Cancel
          </Button>
          <Button onClick={handleAdminPasswordSubmit} variant="contained" color="primary">
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default App;
