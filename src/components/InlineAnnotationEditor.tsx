import React, { useRef, useEffect } from 'react';
import {
  Paper,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Autocomplete,
  IconButton,
  Box,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { Annotation, NeumeType } from '../state/types';
import { neumeTypes, NeumeTypeInfo } from '../data/neumeTypes';

interface InlineAnnotationEditorProps {
  annotation: Annotation;
  position: { x: number; y: number };
  isNewlyCreated: boolean;
  neumeSuggestion: string | null;
  onTypeChange: (type: 'syllable' | 'neume') => void;
  onTextChange: (text: string) => void;
  onNeumeTypeChange: (neumeType: NeumeType) => void;
  onClose: () => void;
  onClearNewFlag: () => void;
  onDelete: () => void;
}

export function InlineAnnotationEditor({
  annotation,
  position,
  isNewlyCreated,
  neumeSuggestion,
  onTypeChange,
  onTextChange,
  onNeumeTypeChange,
  onClose,
  onClearNewFlag,
  onDelete,
}: InlineAnnotationEditorProps) {
  const textInputRef = useRef<HTMLInputElement>(null);
  const selectRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isNewlyCreated) {
      setTimeout(() => {
        if (annotation.type === 'syllable' && textInputRef.current) {
          textInputRef.current.focus();
        } else if (annotation.type === 'neume' && selectRef.current) {
          selectRef.current.focus();
        }
        onClearNewFlag();
      }, 0);
    }
  }, [isNewlyCreated, annotation.type, onClearNewFlag]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleTypeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onTypeChange(e.target.value as 'syllable' | 'neume');
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onTextChange(e.target.value);
  };

  const handleTextKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onClose();
    }
  };

  // For newly created neumes without a type set, return null to show placeholder
  // Otherwise find the matching type info
  const currentNeumeTypeInfo = annotation.neumeType
    ? neumeTypes.find((n) => n.type === annotation.neumeType) || null
    : null;

  const handleNeumeAutocompleteChange = (
    _event: React.SyntheticEvent,
    value: NeumeTypeInfo | null
  ) => {
    if (value) {
      onNeumeTypeChange(value.type);
      onClose();
    }
  };

  const filterNeumeOptions = (
    options: NeumeTypeInfo[],
    { inputValue }: { inputValue: string }
  ) =>
    options.filter((opt) =>
      opt.name.toLowerCase().startsWith(inputValue.toLowerCase())
    );

  // Find the suggested neume type info
  const suggestedNeumeTypeInfo = neumeSuggestion
    ? neumeTypes.find((n) => n.name.toLowerCase() === neumeSuggestion.toLowerCase())
    : null;

  // Show neume ghost text when no neume type selected yet and suggestion exists
  const showNeumeGhostText =
    annotation.type === 'neume' &&
    !annotation.neumeType &&
    neumeSuggestion &&
    suggestedNeumeTypeInfo;

  // Track if user has typed in neume autocomplete
  const [neumeInputValue, setNeumeInputValue] = React.useState('');

  const handleNeumeInputChange = (
    _event: React.SyntheticEvent,
    value: string
  ) => {
    setNeumeInputValue(value);
  };

  const handleNeumeKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    // Accept suggestion with Tab or Enter when no type selected and suggestion exists
    if (
      (e.key === 'Tab' || e.key === 'Enter') &&
      !annotation.neumeType &&
      suggestedNeumeTypeInfo &&
      neumeInputValue === ''
    ) {
      e.preventDefault();
      onNeumeTypeChange(suggestedNeumeTypeInfo.type);
      onClose();
    }
  };

  return (
    <Paper
      ref={containerRef}
      elevation={8}
      sx={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        width: 280,
        p: 1.5,
        zIndex: 1000,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <RadioGroup
          row
          value={annotation.type}
          onChange={handleTypeChange}
          sx={{ flex: 1 }}
        >
          <FormControlLabel
            value="syllable"
            control={<Radio size="small" />}
            label="Syllable"
          />
          <FormControlLabel
            value="neume"
            control={<Radio size="small" />}
            label="Neume"
          />
        </RadioGroup>
        <IconButton size="small" onClick={onDelete} color="error">
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Box>

      {annotation.type === 'syllable' && (
        <TextField
          fullWidth
          size="small"
          label="Syllable Text"
          value={annotation.text || ''}
          onChange={handleTextChange}
          onKeyDown={handleTextKeyDown}
          inputRef={textInputRef}
          autoComplete="off"
        />
      )}

      {annotation.type === 'neume' && (
        <Autocomplete
          size="small"
          options={neumeTypes}
          value={currentNeumeTypeInfo}
          getOptionLabel={(option) => option.name}
          filterOptions={filterNeumeOptions}
          openOnFocus
          onChange={handleNeumeAutocompleteChange}
          inputValue={neumeInputValue}
          onInputChange={handleNeumeInputChange}
          onKeyDown={handleNeumeKeyDown}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Neume Type"
              inputRef={selectRef}
              placeholder={showNeumeGhostText ? neumeSuggestion ?? undefined : undefined}
              InputProps={{
                ...params.InputProps,
                sx: showNeumeGhostText
                  ? {
                      '& input::placeholder': {
                        color: 'text.secondary',
                        opacity: 0.7,
                      },
                    }
                  : undefined,
              }}
              helperText={showNeumeGhostText ? 'Tab/Enter to accept' : undefined}
            />
          )}
        />
      )}
    </Paper>
  );
}
