import {
  AppBar,
  Toolbar as MuiToolbar,
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import { AppProvider } from './state/context';
import { AnnotationCanvas } from './components/AnnotationCanvas';
import { Toolbar } from './components/Toolbar';
import { ErrorSnackbar } from './components/ErrorSnackbar';

const theme = createTheme();

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
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
    </ThemeProvider>
  );
}

export default App;
