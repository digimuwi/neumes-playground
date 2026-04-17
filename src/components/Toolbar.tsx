import React, { useEffect, useRef, useState } from 'react';
import { Alert, Avatar, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Divider, IconButton, Menu, MenuItem, Snackbar, ToggleButton, ToggleButtonGroup, Tooltip } from '@mui/material';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import UndoIcon from '@mui/icons-material/Undo';
import RedoIcon from '@mui/icons-material/Redo';
import DocumentScannerIcon from '@mui/icons-material/DocumentScanner';
import VolunteerActivismIcon from '@mui/icons-material/VolunteerActivism';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import TableChartIcon from '@mui/icons-material/TableChart';
import LabelIcon from '@mui/icons-material/Label';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAppContext } from '../state/context';
import { useAuth } from '../state/auth';
import { undo, redo, setImage, setOcrDialog, setError, loadState, setContributionId, selectAnnotation } from '../state/actions';
import { exportMEI, getImageDimensions } from '../utils/meiExport';
import { exportAnnotationsJSON, AnnotationsFile } from '../utils/jsonExport';
import { parseAnnotationsJSON } from '../utils/jsonImport';
import { contributeTrainingData, getContribution, updateContribution, NeumeCrop } from '../services/htrService';
import { findNeumeAnnotation } from '../utils/findNeumeAnnotation';
import { ContributionsDialog } from './ContributionsDialog';
import { CrossSectionDialog } from './CrossSectionDialog';
import { NeumeClassesDialog } from './NeumeClassesDialog';

export function Toolbar() {
  const { state, dispatch, canUndo, canRedo, recognitionMode, setRecognitionMode, requestFocus } = useAppContext();
  const auth = useAuth();
  const [isContributing, setIsContributing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [pendingImport, setPendingImport] = useState<AnnotationsFile | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const [importAnchorEl, setImportAnchorEl] = useState<null | HTMLElement>(null);
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);
  const [contributionsDialogOpen, setContributionsDialogOpen] = useState(false);
  const [crossSectionOpen, setCrossSectionOpen] = useState(false);
  const [neumeClassesOpen, setNeumeClassesOpen] = useState(false);

  const handleUndo = () => {
    dispatch(undo());
  };

  const handleRedo = () => {
    dispatch(redo());
  };

  const handleExport = async () => {
    if (state.imageDataUrl) {
      await exportMEI(state.annotations, state.imageDataUrl);
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
      lineBoundaries: [],
      contributionId: null,
      metadata: data.metadata,
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

  const handleNavigateToNeume = async (crop: NeumeCrop) => {
    setCrossSectionOpen(false);
    try {
      if (state.contributionId === crop.contribution_id && state.imageDataUrl) {
        const dims = await getImageDimensions(state.imageDataUrl);
        const match = findNeumeAnnotation(state.annotations, crop.type, crop.bbox, dims.width, dims.height);
        if (match) {
          dispatch(selectAnnotation(match.id));
          requestFocus(match.id);
        }
        return;
      }

      const data = await getContribution(crop.contribution_id);
      const match = findNeumeAnnotation(data.annotations, crop.type, crop.bbox, data.imageWidth, data.imageHeight);
      dispatch(loadState({
        imageDataUrl: data.imageDataUrl,
        annotations: data.annotations,
        selectedAnnotationIds: match ? new Set<string>([match.id]) : new Set<string>(),
        isNewlyCreated: false,
        ocrDialogState: { mode: 'closed' },
        errorMessage: null,
        lineBoundaries: data.lineBoundaries,
        contributionId: crop.contribution_id,
      }));
      if (match) requestFocus(match.id);
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to open instance'));
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
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, width: '100%' }}>
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
      <Tooltip title="Manage Neume Classes">
        <IconButton onClick={() => setNeumeClassesOpen(true)} color="inherit">
          <LabelIcon />
        </IconButton>
      </Tooltip>

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

      {auth.user && (
        <>
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title={auth.user.name ? `${auth.user.name} (${auth.user.login})` : auth.user.login}>
            <Chip
              avatar={
                auth.user.avatar_url ? (
                  <Avatar src={auth.user.avatar_url} alt={auth.user.login} />
                ) : undefined
              }
              label={auth.user.login}
              size="small"
              variant="outlined"
              sx={{ ml: 1 }}
            />
          </Tooltip>
          {auth.authEnabled && (
            <Tooltip title="Sign out">
              <IconButton onClick={() => { void auth.logout(); }} color="inherit" size="small">
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </>
      )}

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
        onNavigateToNeume={handleNavigateToNeume}
      />

      <NeumeClassesDialog
        open={neumeClassesOpen}
        onClose={() => setNeumeClassesOpen(false)}
      />
    </Box>
  );
}
