import {
  AppBar,
  Toolbar as MuiToolbar,
  Box,
  CircularProgress,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import { AppProvider } from './state/context';
import { AuthProvider, useAuth } from './state/auth';
import { AnnotationCanvas } from './components/AnnotationCanvas';
import { Toolbar } from './components/Toolbar';
import { ErrorSnackbar } from './components/ErrorSnackbar';
import { LoginScreen } from './components/LoginScreen';

const theme = createTheme();

function AuthedApp() {
  const { status, authEnabled } = useAuth();

  if (status === 'loading') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (status === 'unauthenticated' && authEnabled) {
    return <LoginScreen />;
  }

  return (
    <AppProvider>
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <AppBar position="static" color="default" elevation={1}>
          <MuiToolbar>
            <Toolbar />
          </MuiToolbar>
        </AppBar>

        <Box
          sx={{
            flex: 1,
            display: 'flex',
            overflow: 'hidden',
            p: 2,
          }}
        >
          <AnnotationCanvas />
        </Box>
        <ErrorSnackbar />
      </Box>
    </AppProvider>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AuthedApp />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
