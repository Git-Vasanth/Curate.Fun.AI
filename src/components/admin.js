import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, LinearProgress, CircularProgress } from '@mui/material';
import { styled } from '@mui/system';

const AdminContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  backgroundColor: '#f0f2f5', // Light background
  padding: '1rem',
  boxSizing: 'border-box',
}));

const AdminCard = styled(Box)(({ theme }) => ({
  backgroundColor: '#ffffff',
  borderRadius: '1.5rem',
  boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
  width: '90%',
  maxWidth: '700px',
  padding: '2rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '1.5rem',
}));

const AdminHeader = styled(Typography)(({ theme }) => ({
  backgroundColor: '#4f46e5', // Primary purple
  color: 'white',
  padding: '1.5rem 2rem',
  borderTopLeftRadius: '1rem',
  borderTopRightRadius: '1rem',
  fontWeight: 700,
  fontSize: '1.75rem',
  textAlign: 'center',
  // Adjust margin to extend to edges of the card
  margin: '-2rem -2rem 1.5rem -2rem',
}));

const StatusBox = styled(Box)(({ theme }) => ({
  backgroundColor: '#f3f4f6', // Light gray background for status
  borderRadius: '0.75rem',
  padding: '1.5rem',
  border: '1px solid #e5e7eb',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
}));

const StatusItem = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  fontSize: '1rem',
  color: '#374151',
}));

const StatusLabel = styled(Typography)(({ theme }) => ({
  fontWeight: 600,
}));

const StatusValue = styled(Typography)(({ theme }) => ({
  color: '#4b5563',
}));

const StyledLinearProgress = styled(LinearProgress)(({ theme }) => ({
  height: '1.5rem', // Slightly taller progress bar
  borderRadius: '0.5rem',
  backgroundColor: '#e5e7eb', // Background for the progress bar track
  '& .MuiLinearProgress-bar': {
    backgroundColor: '#22c55e', // Green for progress
    borderRadius: '0.5rem',
    transition: 'width 0.5s ease-in-out',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontWeight: 600,
    fontSize: '0.875rem',
    textShadow: '1px 1px 2px rgba(0,0,0,0.2)', // Add text shadow for readability
  },
}));

const ActionButton = styled(Button)(({ theme }) => ({
  backgroundColor: '#4f46e5',
  color: 'white',
  padding: '1rem 2rem',
  borderRadius: '1.25rem',
  cursor: 'pointer',
  transition: 'background-color 0.3s ease, box-shadow 0.3s ease',
  fontWeight: 700,
  fontSize: '1.125rem',
  boxShadow: '0 4px 10px rgba(79, 70, 229, 0.2)',
  width: 'fit-content',
  alignSelf: 'center', // Center the button
  border: 'none', // Remove default button border
  '&:hover': {
    backgroundColor: '#4338ca',
    boxShadow: '0 6px 15px rgba(79, 70, 229, 0.3)',
  },
  '&:disabled': {
    backgroundColor: '#9ca3af',
    cursor: 'not-allowed',
    boxShadow: 'none',
    color: '#e0e0e0', // Lighter text for disabled state
  },
}));

const MessageBox = styled(Box)(({ type }) => ({
  backgroundColor: '#fff',
  border: '1px solid #ccc',
  borderRadius: '8px',
  padding: '15px',
  marginBottom: '15px',
  display: 'none', // Hidden by default
  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  color: '#333',
  fontSize: '0.95rem',
  // Conditional display based on 'type' prop
  ...(type === 'show' && { display: 'block' }),
  ...(type === 'success' && {
    backgroundColor: '#d4edda',
    borderColor: '#28a745',
    color: '#155724',
  }),
  ...(type === 'error' && {
    backgroundColor: '#f8d7da',
    borderColor: '#dc3545',
    color: '#721c24',
  }),
  ...(type === 'info' && {
    backgroundColor: '#d1ecf1',
    borderColor: '#17a2b8',
    color: '#0c5460',
  }),
}));

function AdminPanel() {
  const [status, setStatus] = useState({
    status: 'Loading...',
    message: 'Fetching initial status...',
    progress: 0,
    total: 0,
    last_update: null,
  });
  const [messageBoxContent, setMessageBoxContent] = useState('');
  const [messageBoxType, setMessageBoxType] = useState('info');
  const [messageBoxShow, setMessageBoxShow] = useState(false);
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);

  const showMessageBox = (message, type = 'info') => {
    setMessageBoxContent(message);
    setMessageBoxType(type);
    setMessageBoxShow(true);
    setTimeout(() => {
      setMessageBoxShow(false);
      setMessageBoxContent('');
    }, 5000); // Hide after 5 seconds
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/update-status');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStatus(data);

      if (data.status === 'Running') {
        setIsButtonDisabled(true);
      } else {
        setIsButtonDisabled(false);
        // If update completed or failed, show final message and stop polling
        if (data.status === 'Complete') {
          showMessageBox('RAG update completed successfully!', 'success');
        } else if (data.status === 'Failed') {
          showMessageBox(`RAG update failed: ${data.message}`, 'error');
        }
      }
    } catch (error) {
      console.error('Error fetching status:', error);
      setStatus(prev => ({ ...prev, status: 'Error', message: 'Could not fetch status.' }));
      setIsButtonDisabled(false);
      showMessageBox('Failed to connect to backend for status updates.', 'error');
    }
  };

  useEffect(() => {
    fetchStatus(); // Fetch initial status on component mount
    const pollingInterval = setInterval(fetchStatus, 3000); // Poll every 3 seconds

    // Cleanup interval on component unmount
    return () => clearInterval(pollingInterval);
  }, []); // Empty dependency array means this runs once on mount and cleans up on unmount

  const handleStartUpdate = async () => {
    setIsButtonDisabled(true);
    showMessageBox('Initiating update...', 'info');

    try {
      const response = await fetch('http://127.0.0.1:5000/api/trigger-full-update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      if (response.ok) {
        showMessageBox(data.message, 'success');
        fetchStatus(); // Fetch status immediately after triggering
      } else {
        showMessageBox(`Error: ${data.message || 'Failed to trigger update.'}`, 'error');
        setIsButtonDisabled(false);
      }
    } catch (error) {
      console.error('Error triggering update:', error);
      showMessageBox('Network error: Could not trigger update.', 'error');
      setIsButtonDisabled(false);
    }
  };

  const progressPercentage = status.total > 0 ? (status.progress / status.total) * 100 : 0;

  return (
    <AdminContainer>
      <AdminCard>
        <AdminHeader variant="h1">
          RAG Update Admin Panel
        </AdminHeader>

        <MessageBox type={messageBoxShow ? 'show' : ''}>
          {messageBoxContent}
        </MessageBox>

        <StatusBox>
          <StatusItem>
            <StatusLabel>Current Status:</StatusLabel>
            <StatusValue>{status.status}</StatusValue>
          </StatusItem>
          <StatusItem>
            <StatusLabel>Message:</StatusLabel>
            <StatusValue>{status.message}</StatusValue>
          </StatusItem>
          <StatusItem>
            <StatusLabel>Progress:</StatusLabel>
            <StatusValue>{status.progress}/{status.total}</StatusValue>
          </StatusItem>
          <Box sx={{ width: '100%', mt: '0.5rem' }}>
            <StyledLinearProgress variant="determinate" value={progressPercentage}>
              {/* This span ensures the percentage text is displayed inside the bar */}
              <span style={{ position: 'absolute', width: '100%', textAlign: 'center' }}>
                {`${Math.round(progressPercentage)}%`}
              </span>
            </StyledLinearProgress>
          </Box>
          <StatusItem>
            <StatusLabel>Last Updated:</StatusLabel>
            <StatusValue>{status.last_update ? new Date(status.last_update).toLocaleString() : 'N/A'}</StatusValue>
          </StatusItem>
        </StatusBox>

        <ActionButton
          onClick={handleStartUpdate}
          disabled={isButtonDisabled}
        >
          {isButtonDisabled ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={20} color="inherit" /> Update In Progress...
            </Box>
          ) : (
            'Start Full RAG Update'
          )}
        </ActionButton>
      </AdminCard>
    </AdminContainer>
  );
}

export default AdminPanel;
