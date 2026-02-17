import { useEffect, useState } from 'react';
import {
  Box,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemText,
  Typography,
} from '@mui/material';
import { listContributions, ContributionSummary } from '../services/htrService';

interface ContributionsDialogProps {
  open: boolean;
  onSelect: (id: string) => void;
  onClose: () => void;
}

export function ContributionsDialog({ open, onSelect, onClose }: ContributionsDialogProps) {
  const [contributions, setContributions] = useState<ContributionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    listContributions()
      .then(setContributions)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load contributions'))
      .finally(() => setLoading(false));
  }, [open]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Contributions</DialogTitle>
      <DialogContent>
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}
        {error && (
          <Typography color="error" sx={{ py: 2 }}>
            {error}
          </Typography>
        )}
        {!loading && !error && contributions.length === 0 && (
          <Typography color="text.secondary" sx={{ py: 2 }}>
            No contributions available.
          </Typography>
        )}
        {!loading && !error && contributions.length > 0 && (
          <List>
            {contributions.map((c) => (
              <ListItemButton key={c.id} onClick={() => onSelect(c.id)}>
                <ListItemText
                  primary={c.image.filename}
                  secondary={`${c.image.width}×${c.image.height} · ${c.line_count} lines · ${c.syllable_count} syllables · ${c.neume_count} neumes`}
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </DialogContent>
    </Dialog>
  );
}
