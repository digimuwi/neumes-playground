import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import ArchiveOutlinedIcon from '@mui/icons-material/ArchiveOutlined';
import CheckIcon from '@mui/icons-material/Check';
import { useAppContext } from '../state/context';
import { setError } from '../state/actions';

interface NeumeClassesDialogProps {
  open: boolean;
  onClose: () => void;
}

interface EditDraft {
  name: string;
  description: string;
}

export function NeumeClassesDialog({ open, onClose }: NeumeClassesDialogProps) {
  const {
    neumeClasses,
    neumeClassesLoading,
    createNeumeClass,
    updateNeumeClass,
    dispatch,
  } = useAppContext();

  const [newKey, setNewKey] = useState('');
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [savingNew, setSavingNew] = useState(false);
  const [savingIds, setSavingIds] = useState<Set<number>>(new Set());
  const [drafts, setDrafts] = useState<Record<number, EditDraft>>({});

  useEffect(() => {
    if (!open) return;
    setDrafts(
      Object.fromEntries(
        neumeClasses.map((entry) => [entry.id, {
          name: entry.name,
          description: entry.description,
        }])
      )
    );
  }, [neumeClasses, open]);

  const sortedClasses = useMemo(
    () => [...neumeClasses].sort((a, b) => a.id - b.id),
    [neumeClasses]
  );

  const handleDraftChange = (
    id: number,
    updates: Partial<EditDraft>
  ) => {
    setDrafts((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        ...updates,
      },
    }));
  };

  const handleCreate = async () => {
    setSavingNew(true);
    try {
      await createNeumeClass({
        key: newKey,
        name: newName,
        description: newDescription,
      });
      setNewKey('');
      setNewName('');
      setNewDescription('');
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to create neume class'));
    } finally {
      setSavingNew(false);
    }
  };

  const setActive = async (id: number, active: boolean) => {
    setSavingIds((prev) => new Set(prev).add(id));
    try {
      await updateNeumeClass(id, { active });
    } catch (error) {
      const fallback = active ? 'Failed to reactivate neume class' : 'Failed to deactivate neume class';
      dispatch(setError(error instanceof Error ? error.message : fallback));
    } finally {
      setSavingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleSave = async (id: number) => {
    const draft = drafts[id];
    if (!draft) return;

    setSavingIds((prev) => new Set(prev).add(id));
    try {
      await updateNeumeClass(id, draft);
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to update neume class'));
    } finally {
      setSavingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Neume Classes</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Add new canonical classes here. Removing a class deactivates it so existing IDs stay stable for training and exports.
        </Typography>

        <Box sx={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 2, mb: 2 }}>
          <TextField
            label="Key"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            placeholder="virga strata"
            size="small"
          />
          <TextField
            label="Display Name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Virga Strata"
            size="small"
          />
        </Box>
        <TextField
          label="Description"
          value={newDescription}
          onChange={(e) => setNewDescription(e.target.value)}
          placeholder="Optional help text for annotators"
          size="small"
          fullWidth
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          onClick={handleCreate}
          disabled={savingNew || newKey.trim() === '' || newName.trim() === ''}
        >
          Add Class
        </Button>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {neumeClassesLoading && sortedClasses.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              Loading classes...
            </Typography>
          )}
          {sortedClasses.map((entry) => {
            const draft = drafts[entry.id] || {
              name: entry.name,
              description: entry.description,
            };
            const isDirty =
              draft.name !== entry.name
              || draft.description !== entry.description;
            const isSaving = savingIds.has(entry.id);

            if (!entry.active) {
              return (
                <Box
                  key={entry.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 2,
                    border: '1px dashed',
                    borderColor: 'divider',
                    borderRadius: 1,
                    px: 1.5,
                    py: 0.5,
                    opacity: 0.7,
                  }}
                >
                  <Typography variant="body2" color="text.disabled" sx={{ fontSize: 13 }}>
                    <Box component="span" sx={{ color: 'text.secondary' }}>
                      ID {entry.id} · {entry.key}
                    </Box>
                    {' — '}
                    {entry.name}
                  </Typography>
                  <Button
                    size="small"
                    onClick={() => setActive(entry.id, true)}
                    disabled={isSaving}
                  >
                    Reactivate
                  </Button>
                </Box>
              );
            }

            return (
              <Box
                key={entry.id}
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  p: 2,
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  ID {entry.id} · {entry.key}
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr auto', gap: 2, mt: 1 }}>
                  <TextField
                    label="Display Name"
                    size="small"
                    value={draft.name}
                    onChange={(e) => handleDraftChange(entry.id, { name: e.target.value })}
                  />
                  <TextField
                    label="Description"
                    size="small"
                    value={draft.description}
                    onChange={(e) => handleDraftChange(entry.id, { description: e.target.value })}
                  />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Tooltip title="Save changes">
                      <span>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleSave(entry.id)}
                          disabled={!isDirty || isSaving || draft.name.trim() === ''}
                        >
                          <CheckIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title="Deactivate (preserves ID)">
                      <span>
                        <IconButton
                          size="small"
                          onClick={() => setActive(entry.id, false)}
                          disabled={isSaving}
                        >
                          <ArchiveOutlinedIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </Box>
                </Box>
              </Box>
            );
          })}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
