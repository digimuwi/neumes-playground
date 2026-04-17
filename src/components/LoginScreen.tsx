import { Box, Button, Paper, Typography } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import { loginUrl } from '../services/authService';

export function LoginScreen() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
      }}
    >
      <Paper
        elevation={2}
        sx={{ p: 4, maxWidth: 420, width: '100%', textAlign: 'center' }}
      >
        <Typography variant="h5" gutterBottom>
          Neumes Playground
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Sign in with a GitHub account that belongs to the digimuwi organization to
          continue.
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<GitHubIcon />}
          onClick={() => {
            window.location.href = loginUrl();
          }}
        >
          Sign in with GitHub
        </Button>
      </Paper>
    </Box>
  );
}
