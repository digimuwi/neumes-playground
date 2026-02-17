import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Typography,
  Box,
} from '@mui/material';
import { CantusChant } from '../services/cantusIndex';

interface CantusSelectionDialogProps {
  open: boolean;
  chants: CantusChant[];
  onSelect: (chant: CantusChant) => void;
  onCancel: () => void;
}

export function CantusSelectionDialog({
  open,
  chants,
  onSelect,
  onCancel,
}: CantusSelectionDialogProps) {
  const [selectedCid, setSelectedCid] = useState<string | null>(
    chants.length > 0 ? chants[0].cid : null
  );

  const handleConfirm = () => {
    const selected = chants.find((c) => c.cid === selectedCid);
    if (selected) {
      onSelect(selected);
    }
  };

  const truncateText = (text: string, maxLength: number = 80): string => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  return (
    <Dialog open={open} onClose={onCancel} maxWidth="sm" fullWidth>
      <DialogTitle>Select Cantus Chant</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Multiple chants match the annotated text. Please select the correct one:
        </Typography>
        <RadioGroup
          value={selectedCid}
          onChange={(e) => setSelectedCid(e.target.value)}
        >
          {chants.map((chant) => (
            <FormControlLabel
              key={chant.cid}
              value={chant.cid}
              control={<Radio />}
              label={
                <Box sx={{ py: 1 }}>
                  <Typography variant="body1" component="span" fontWeight="medium">
                    {chant.cid}
                  </Typography>
                  <Typography
                    variant="body2"
                    component="span"
                    color="text.secondary"
                    sx={{ ml: 1 }}
                  >
                    ({chant.genre})
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ display: 'block', mt: 0.5, fontStyle: 'italic' }}
                  >
                    {truncateText(chant.fulltext)}
                  </Typography>
                </Box>
              }
              sx={{
                alignItems: 'flex-start',
                borderBottom: '1px solid',
                borderColor: 'divider',
                mx: 0,
                '&:last-child': { borderBottom: 'none' },
              }}
            />
          ))}
        </RadioGroup>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={handleConfirm} variant="contained" disabled={!selectedCid}>
          Select
        </Button>
      </DialogActions>
    </Dialog>
  );
}
