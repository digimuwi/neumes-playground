import React, { useEffect, useRef, useState } from 'react';
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Checkbox, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Divider, FormControlLabel, IconButton, Menu, MenuItem, Snackbar, TextField, ToggleButton, ToggleButtonGroup, Tooltip, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import UndoIcon from '@mui/icons-material/Undo';
import RedoIcon from '@mui/icons-material/Redo';
import DocumentScannerIcon from '@mui/icons-material/DocumentScanner';
import VolunteerActivismIcon from '@mui/icons-material/VolunteerActivism';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import SearchIcon from '@mui/icons-material/Search';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import TableChartIcon from '@mui/icons-material/TableChart';
import { useAppContext } from '../state/context';
import { undo, redo, setImage, setOcrDialog, setError, setMetadata, loadState, setContributionId } from '../state/actions';
import { exportMEI } from '../utils/meiExport';
import { exportAnnotationsJSON, AnnotationsFile } from '../utils/jsonExport';
import { parseAnnotationsJSON } from '../utils/jsonImport';
import { contributeTrainingData, getContribution, updateContribution, TrainingType } from '../services/htrService';
import { CantusSelectionDialog } from './CantusSelectionDialog';
import { ContributionsDialog } from './ContributionsDialog';
import { CrossSectionDialog } from './CrossSectionDialog';
import { useCantusLookup } from '../hooks/useCantusLookup';
import { useTrainingStatus } from '../hooks/useTrainingStatus';
import { CantusChant } from '../services/cantusIndex';

export function Toolbar() {
  const { state, dispatch, canUndo, canRedo, recognitionMode, setRecognitionMode } = useAppContext();
  const [isContributing, setIsContributing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectionDialogChants, setSelectionDialogChants] = useState<CantusChant[]>([]);
  const [pendingImport, setPendingImport] = useState<AnnotationsFile | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const [importAnchorEl, setImportAnchorEl] = useState<null | HTMLElement>(null);
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);
  const cantusLookup = useCantusLookup();
  const training = useTrainingStatus();
  const [contributionsDialogOpen, setContributionsDialogOpen] = useState(false);
  const [crossSectionOpen, setCrossSectionOpen] = useState(false);
  const [trainingDialogOpen, setTrainingDialogOpen] = useState(false);
  const [trainingType, setTrainingType] = useState<TrainingType>('both');
  const [trainingEpochs, setTrainingEpochs] = useState('');
  const [trainingImgsz, setTrainingImgsz] = useState(640);
  const [trainingSegEpochs, setTrainingSegEpochs] = useState(50);
  const [trainingFromScratch, setTrainingFromScratch] = useState(false);
  const prevTrainingState = useRef(training.status?.state);

  // React to training state transitions for snackbar feedback
  useEffect(() => {
    const prev = prevTrainingState.current;
    const curr = training.status?.state;
    prevTrainingState.current = curr;

    if (prev && prev !== curr) {
      if (curr === 'complete') {
        setSuccessMessage('Training complete!');
      } else if (curr === 'failed') {
        dispatch(setError(training.status?.error || 'Training failed'));
      }
    }
  }, [training.status?.state]);

  const handleTrainingClick = () => {
    setTrainingDialogOpen(true);
  };

  const handleTrainingStart = async () => {
    setTrainingDialogOpen(false);
    try {
      const options: Record<string, unknown> = {};
      if (trainingType !== 'both') options.training_type = trainingType;
      const parsedEpochs = parseInt(trainingEpochs);
      if (!isNaN(parsedEpochs) && parsedEpochs >= 1) options.epochs = parsedEpochs;
      if (trainingImgsz !== 640) options.imgsz = trainingImgsz;
      if (trainingSegEpochs !== 50) options.seg_epochs = trainingSegEpochs;
      if (trainingFromScratch) options.from_scratch = true;
      await training.start(Object.keys(options).length > 0 ? options : undefined);
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to start training'));
    }
  };

  const handleTrainingDialogClose = () => {
    setTrainingDialogOpen(false);
  };

  const handleUndo = () => {
    dispatch(undo());
  };

  const handleRedo = () => {
    dispatch(redo());
  };

  const handleExport = async () => {
    if (state.imageDataUrl) {
      await exportMEI(state.annotations, state.imageDataUrl, state.metadata);
    }
  };

  const handleExportJSON = () => {
    if (state.imageDataUrl) {
      exportAnnotationsJSON(state.imageDataUrl, state.annotations, state.metadata);
    }
  };

  const handleImportImageFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      dispatch(setImage(dataUrl));
      dispatch(setOcrDialog({ mode: 'uploadPrompt' }));
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleImportJSONFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    try {
      const data = await parseAnnotationsJSON(file);
      if (state.annotations.length > 0) {
        setPendingImport(data);
      } else {
        applyImport(data);
      }
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to import JSON'));
    }
  };

  const applyImport = (data: AnnotationsFile) => {
    dispatch(loadState({
      imageDataUrl: data.imageDataUrl,
      annotations: data.annotations,
      selectedAnnotationIds: new Set<string>(),
      isNewlyCreated: false,
      ocrDialogState: { mode: 'closed' },
      errorMessage: null,
      metadata: data.metadata,
      lineBoundaries: [],
      contributionId: null,
    }));
  };

  const handleConfirmImport = () => {
    if (pendingImport) {
      applyImport(pendingImport);
      setPendingImport(null);
    }
  };

  const handleCancelImport = () => {
    setPendingImport(null);
  };

  const canExport = state.imageDataUrl !== null;
  const canRecognize = state.imageDataUrl !== null;

  // Can lookup Cantus ID only when there are syllables with text
  const syllablesWithText = state.annotations.filter(
    (a) => a.type === 'syllable' && a.text?.trim()
  );
  const canLookupCantus = syllablesWithText.length > 0 && cantusLookup.state.status !== 'loading';

  const handleCantusLookup = async () => {
    const results = await cantusLookup.lookup(state.annotations);
    if (results.length === 0) {
      dispatch(setError('No matching chant found'));
    } else if (results.length === 1) {
      // Auto-select single result
      const chant = results[0];
      dispatch(setMetadata({ cantusId: chant.cid, genre: chant.genre }));
      setSuccessMessage(`Found: ${chant.cid} (${chant.genre})`);
    } else {
      // Multiple results - show selection dialog
      setSelectionDialogChants(results);
    }
  };

  const handleCantusSelect = (chant: CantusChant) => {
    dispatch(setMetadata({ cantusId: chant.cid, genre: chant.genre }));
    setSelectionDialogChants([]);
    setSuccessMessage(`Selected: ${chant.cid} (${chant.genre})`);
  };

  const handleCantusCancel = () => {
    setSelectionDialogChants([]);
    cantusLookup.reset();
  };

  // Can contribute only when there's an image AND both syllables AND neumes
  const hasSyllables = state.annotations.some(a => a.type === 'syllable');
  const hasNeumes = state.annotations.some(a => a.type === 'neume');
  const canContribute = state.imageDataUrl !== null && hasSyllables && hasNeumes && !isContributing;

  const handleContribute = async () => {
    if (!state.imageDataUrl || isContributing) return;

    setIsContributing(true);
    try {
      if (state.contributionId) {
        await updateContribution(state.contributionId, state.imageDataUrl, state.annotations, state.lineBoundaries);
        setSuccessMessage('Contribution updated successfully');
      } else {
        const response = await contributeTrainingData(state.imageDataUrl, state.annotations, state.lineBoundaries);
        dispatch(setContributionId(response.id));
        setSuccessMessage('Contribution submitted successfully');
      }
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Contribution failed'));
    } finally {
      setIsContributing(false);
    }
  };

  const handleContributionSelect = async (id: string) => {
    setContributionsDialogOpen(false);
    setIsContributing(true);
    try {
      const data = await getContribution(id);
      dispatch(loadState({
        imageDataUrl: data.imageDataUrl,
        annotations: data.annotations,
        selectedAnnotationIds: new Set<string>(),
        isNewlyCreated: false,
        ocrDialogState: { mode: 'closed' },
        errorMessage: null,
        lineBoundaries: data.lineBoundaries,
        contributionId: id,
      }));
      setSuccessMessage('Contribution loaded');
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to load contribution'));
    } finally {
      setIsContributing(false);
    }
  };

  const handleRecognizePage = () => {
    if (state.annotations.length > 0) {
      dispatch(setOcrDialog({ mode: 'existingAnnotationsPrompt' }));
    } else {
      // No existing annotations - show upload prompt style dialog
      // which will trigger OCR when user confirms
      dispatch(setOcrDialog({ mode: 'uploadPrompt' }));
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        if (e.shiftKey) {
          e.preventDefault();
          if (canRedo) handleRedo();
        } else {
          e.preventDefault();
          if (canUndo) handleUndo();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canUndo, canRedo]);

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      {/* Hidden file inputs */}
      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        onChange={handleImportImageFile}
        style={{ display: 'none' }}
      />
      <input
        ref={jsonInputRef}
        type="file"
        accept=".json"
        onChange={handleImportJSONFile}
        style={{ display: 'none' }}
      />

      {/* Import / Export dropdown group */}
      <Tooltip title="Import">
        <IconButton
          color="inherit"
          onClick={(e) => setImportAnchorEl(e.currentTarget)}
        >
          <FileUploadIcon />
          <ArrowDropDownIcon sx={{ fontSize: 16, ml: -0.5 }} />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={importAnchorEl}
        open={Boolean(importAnchorEl)}
        onClose={() => setImportAnchorEl(null)}
      >
        <MenuItem onClick={() => { imageInputRef.current?.click(); setImportAnchorEl(null); }}>
          Image
        </MenuItem>
        <MenuItem onClick={() => { jsonInputRef.current?.click(); setImportAnchorEl(null); }}>
          JSON
        </MenuItem>
      </Menu>

      <Tooltip title="Export">
        <IconButton
          color="inherit"
          onClick={(e) => setExportAnchorEl(e.currentTarget)}
        >
          <FileDownloadIcon />
          <ArrowDropDownIcon sx={{ fontSize: 16, ml: -0.5 }} />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={exportAnchorEl}
        open={Boolean(exportAnchorEl)}
        onClose={() => setExportAnchorEl(null)}
      >
        <MenuItem disabled={!canExport} onClick={() => { handleExport(); setExportAnchorEl(null); }}>
          MEI
        </MenuItem>
        <MenuItem disabled={!canExport} onClick={() => { handleExportJSON(); setExportAnchorEl(null); }}>
          JSON
        </MenuItem>
      </Menu>

      <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

      {/* Contributions group */}
      <Tooltip title="Browse Contributions">
        <IconButton onClick={() => setContributionsDialogOpen(true)} color="inherit">
          <FolderOpenIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title={state.contributionId ? 'Update Contribution' : 'Contribute Training Data'}>
        <span>
          <IconButton onClick={handleContribute} disabled={!canContribute} color="inherit">
            {isContributing ? <CircularProgress size={24} color="inherit" /> : <VolunteerActivismIcon />}
          </IconButton>
        </span>
      </Tooltip>
      {state.contributionId && (
        <Tooltip title={`Contribution: ${state.contributionId}`}>
          <Chip
            label={state.contributionId.slice(0, 8)}
            size="small"
            color="secondary"
            variant="outlined"
            sx={{ ml: 0.5 }}
          />
        </Tooltip>
      )}
      <Tooltip title="Cross Section">
        <IconButton onClick={() => setCrossSectionOpen(true)} color="inherit">
          <TableChartIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Start Training">
        <span>
          <IconButton onClick={handleTrainingClick} disabled={training.isActive} color="inherit">
            {training.isActive ? <CircularProgress size={24} color="inherit" /> : <FitnessCenterIcon />}
          </IconButton>
        </span>
      </Tooltip>
      {training.isActive && training.status && (
        <Chip
          label={
            training.status.state === 'training' && training.status.current_epoch != null && training.status.total_epochs != null
              ? `Training${training.status.mode ? ` (${training.status.mode})` : ''} ${training.status.current_epoch}/${training.status.total_epochs}`
              : training.status.state === 'exporting'
                ? 'Exporting...'
                : training.status.state === 'deploying'
                  ? 'Deploying...'
                  : 'Training...'
          }
          size="small"
          color="primary"
          variant="outlined"
          sx={{ ml: 0.5 }}
        />
      )}

      <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

      {/* OCR group */}
      <Tooltip title="Recognize Page">
        <span>
          <IconButton onClick={handleRecognizePage} disabled={!canRecognize} color="inherit">
            <DocumentScannerIcon />
          </IconButton>
        </span>
      </Tooltip>
      <ToggleButtonGroup
        value={recognitionMode}
        exclusive
        onChange={(_e, value) => { if (value !== null) setRecognitionMode(value); }}
        size="small"
        sx={{ ml: 0.5 }}
      >
        <ToggleButton value="neume">Neume (n)</ToggleButton>
        <ToggleButton value="text">Text (t)</ToggleButton>
        <ToggleButton value="manual">Manual (m)</ToggleButton>
      </ToggleButtonGroup>
      <Tooltip title="Find Cantus ID">
        <span>
          <IconButton onClick={handleCantusLookup} disabled={!canLookupCantus} color="inherit">
            {cantusLookup.state.status === 'loading' ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              <SearchIcon />
            )}
          </IconButton>
        </span>
      </Tooltip>
      {state.metadata?.cantusId ? (
        <Tooltip title={`Genre: ${state.metadata.genre || 'Unknown'}`}>
          <Chip
            label={state.metadata.cantusId}
            size="small"
            color="primary"
            variant="outlined"
            sx={{ ml: 0.5 }}
          />
        </Tooltip>
      ) : (
        <Tooltip title="No Cantus ID set">
          <Chip
            label="No ID"
            size="small"
            variant="outlined"
            sx={{ ml: 0.5, opacity: 0.5 }}
          />
        </Tooltip>
      )}

      <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

      {/* Undo / Redo group */}
      <Tooltip title="Undo (Ctrl+Z)">
        <span>
          <IconButton onClick={handleUndo} disabled={!canUndo} color="inherit">
            <UndoIcon />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title="Redo (Ctrl+Shift+Z)">
        <span>
          <IconButton onClick={handleRedo} disabled={!canRedo} color="inherit">
            <RedoIcon />
          </IconButton>
        </span>
      </Tooltip>

      {/* Success snackbar */}
      <Snackbar
        open={successMessage !== null}
        autoHideDuration={6000}
        onClose={() => setSuccessMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccessMessage(null)} severity="success" variant="filled">
          {successMessage}
        </Alert>
      </Snackbar>

      {/* Import confirmation dialog */}
      <Dialog open={pendingImport !== null} onClose={handleCancelImport}>
        <DialogTitle>Existing Annotations</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Importing will replace all current annotations. Do you want to continue?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelImport}>Cancel</Button>
          <Button onClick={handleConfirmImport} variant="contained">Replace</Button>
        </DialogActions>
      </Dialog>

      {/* Cantus selection dialog */}
      <CantusSelectionDialog
        open={selectionDialogChants.length > 0}
        chants={selectionDialogChants}
        onSelect={handleCantusSelect}
        onCancel={handleCantusCancel}
      />

      {/* Contributions dialog */}
      <ContributionsDialog
        open={contributionsDialogOpen}
        onSelect={handleContributionSelect}
        onClose={() => setContributionsDialogOpen(false)}
      />

      {/* Cross section dialog */}
      <CrossSectionDialog
        open={crossSectionOpen}
        onClose={() => setCrossSectionOpen(false)}
      />

      {/* Training configuration dialog */}
      <Dialog open={trainingDialogOpen} onClose={handleTrainingDialogClose}>
        <DialogTitle>Start Training</DialogTitle>
        <DialogContent>
          <ToggleButtonGroup
            value={trainingType}
            exclusive
            onChange={(_e, value) => { if (value !== null) setTrainingType(value); }}
            size="small"
            fullWidth
            sx={{ mb: 2 }}
          >
            <ToggleButton value="neumes">Neumes</ToggleButton>
            <ToggleButton value="segmentation">Segmentation</ToggleButton>
            <ToggleButton value="both">Both</ToggleButton>
          </ToggleButtonGroup>
          <DialogContentText sx={{ mb: 1 }}>
            {trainingType === 'both'
              ? 'Train neume detection and line segmentation models from current contributions.'
              : trainingType === 'neumes'
                ? 'Train the neume detection model from current contributions.'
                : 'Train the line segmentation model from current contributions.'}
          </DialogContentText>
          <Accordion disableGutters elevation={0} sx={{ '&:before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ px: 0 }}>
              <Typography variant="body2">Advanced Settings</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ px: 0 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {(trainingType === 'neumes' || trainingType === 'both') && (
                  <>
                    <TextField
                      label="YOLO Epochs"
                      type="number"
                      value={trainingEpochs}
                      onChange={(e) => setTrainingEpochs(e.target.value)}
                      placeholder="Auto (100 fresh / 30 incr.)"
                      inputProps={{ min: 1 }}
                      size="small"
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="Image Size"
                      type="number"
                      value={trainingImgsz}
                      onChange={(e) => setTrainingImgsz(Math.max(32, parseInt(e.target.value) || 32))}
                      inputProps={{ min: 32 }}
                      size="small"
                    />
                  </>
                )}
                {(trainingType === 'segmentation' || trainingType === 'both') && (
                  <TextField
                    label="Segmentation Epochs"
                    type="number"
                    value={trainingSegEpochs}
                    onChange={(e) => setTrainingSegEpochs(Math.max(1, parseInt(e.target.value) || 1))}
                    inputProps={{ min: 1 }}
                    size="small"
                  />
                )}
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={trainingFromScratch}
                      onChange={(e) => setTrainingFromScratch(e.target.checked)}
                      size="small"
                    />
                  }
                  label="Train from scratch"
                />
              </Box>
            </AccordionDetails>
          </Accordion>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleTrainingDialogClose}>Cancel</Button>
          <Button onClick={handleTrainingStart} variant="contained">Start</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
