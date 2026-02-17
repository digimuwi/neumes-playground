import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  CircularProgress,
  LinearProgress,
  Box,
  Typography,
} from '@mui/material';
import { OcrDialogState, OcrStage } from '../../state/types';

function getStageMessage(stage: OcrStage): string {
  switch (stage) {
    case 'loading':
      return 'Loading model...';
    case 'segmenting':
      return 'Detecting text regions...';
    case 'recognizing':
      return 'Recognizing text...';
    case 'syllabifying':
      return 'Processing syllables...';
  }
}

interface OcrDialogProps {
  state: OcrDialogState;
  onClose: () => void;
  onAcceptUploadPrompt: () => void;
  onKeepAndAdd: () => void;
  onReplace: () => void;
}

export function OcrDialog({
  state,
  onClose,
  onAcceptUploadPrompt,
  onKeepAndAdd,
  onReplace,
}: OcrDialogProps) {
  if (state.mode === 'closed') {
    return null;
  }

  if (state.mode === 'loading') {
    const isRecognizing = state.stage === 'recognizing';
    const progress = isRecognizing && state.current && state.total
      ? Math.round((state.current / state.total) * 100)
      : 0;

    return (
      <Dialog open disableEscapeKeyDown>
        <DialogContent>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              py: 3,
              px: 4,
              minWidth: 300,
            }}
          >
            {isRecognizing ? (
              <Box sx={{ width: '100%', mb: 3 }}>
                <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
            ) : (
              <CircularProgress size={48} sx={{ mb: 3 }} />
            )}
            <Typography variant="h6" gutterBottom>
              {getStageMessage(state.stage)}
            </Typography>
            {isRecognizing && state.current && state.total ? (
              <Typography variant="body2" color="text.secondary" textAlign="center">
                Line {state.current} of {state.total}
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary" textAlign="center">
                This may take a minute for large manuscripts.
              </Typography>
            )}
          </Box>
        </DialogContent>
      </Dialog>
    );
  }

  if (state.mode === 'error') {
    return (
      <Dialog open onClose={onClose}>
        <DialogTitle>Recognition Failed</DialogTitle>
        <DialogContent>
          <DialogContentText>{state.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  if (state.mode === 'uploadPrompt') {
    return (
      <Dialog open onClose={onClose}>
        <DialogTitle>Run Text Recognition?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Would you like to run text recognition on this page? This will
            detect and label all syllables automatically.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>No</Button>
          <Button onClick={onAcceptUploadPrompt} variant="contained" autoFocus>
            Yes, recognize
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  if (state.mode === 'existingAnnotationsPrompt') {
    return (
      <Dialog open onClose={onClose}>
        <DialogTitle>Existing Annotations</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This page has existing annotations. What would you like to do with
            them?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button onClick={onKeepAndAdd}>Keep & Add</Button>
          <Button onClick={onReplace} variant="contained" autoFocus>
            Replace
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  return null;
}
