import { Snackbar, Alert } from '@mui/material';
import { useAppContext } from '../state/context';
import { setError } from '../state/actions';

const AUTO_HIDE_DURATION = 6000;

export function ErrorSnackbar() {
  const { state, dispatch } = useAppContext();

  const handleClose = () => {
    dispatch(setError(null));
  };

  return (
    <Snackbar
      open={state.errorMessage !== null}
      autoHideDuration={AUTO_HIDE_DURATION}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert onClose={handleClose} severity="error" variant="filled">
        {state.errorMessage}
      </Alert>
    </Snackbar>
  );
}
