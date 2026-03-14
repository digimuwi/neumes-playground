import React, { useState, useEffect, useCallback } from 'react';
import {
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Typography,
  Box,
} from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import CloseIcon from '@mui/icons-material/Close';

// Platform detection for modifier key display
const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);
const modKey = isMac ? '⌘' : 'Ctrl';

interface ShortcutRowProps {
  keys: string;
  description: string;
}

function ShortcutRow({ keys, description }: ShortcutRowProps) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.5 }}>
      <Typography
        component="span"
        sx={{
          fontFamily: 'monospace',
          fontSize: '0.8rem',
          backgroundColor: 'grey.100',
          px: 1,
          py: 0.25,
          borderRadius: 1,
          border: '1px solid',
          borderColor: 'grey.300',
          whiteSpace: 'nowrap',
        }}
      >
        {keys}
      </Typography>
      <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary', textAlign: 'right' }}>
        {description}
      </Typography>
    </Box>
  );
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

function Section({ title, children }: SectionProps) {
  return (
    <Box sx={{ mb: 2 }}>
      <Typography
        variant="overline"
        sx={{ color: 'text.secondary', fontWeight: 600, display: 'block', mb: 0.5 }}
      >
        {title}
      </Typography>
      {children}
    </Box>
  );
}

interface HelpButtonProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function HelpButton({ open: controlledOpen, onOpenChange }: HelpButtonProps) {
  const [internalOpen, setInternalOpen] = useState(false);

  // Support both controlled and uncontrolled modes
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;

  const setOpen = useCallback((value: boolean) => {
    if (isControlled) {
      onOpenChange?.(value);
    } else {
      setInternalOpen(value);
    }
  }, [isControlled, onOpenChange]);

  const handleOpen = useCallback(() => setOpen(true), [setOpen]);
  const handleClose = useCallback(() => setOpen(false), [setOpen]);

  // Handle ? key to open dialog (only in uncontrolled mode, parent handles in controlled)
  useEffect(() => {
    if (isControlled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

      if (e.key === '?' && !isInInput) {
        e.preventDefault();
        setInternalOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isControlled]);

  return (
    <>
      <Fab
        size="small"
        color="default"
        onClick={handleOpen}
        aria-label="Help"
        sx={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          backgroundColor: 'white',
          '&:hover': {
            backgroundColor: 'grey.100',
          },
        }}
      >
        <HelpOutlineIcon />
      </Fab>

      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="sm"
        PaperProps={{
          sx: { maxHeight: '80vh' },
        }}
      >
        <DialogTitle sx={{ m: 0, p: 2, pr: 6 }}>
          Keyboard Shortcuts & Tips
          <IconButton
            aria-label="close"
            onClick={handleClose}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: 'grey.500',
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent dividers sx={{ p: 2 }}>
          <Section title="Navigate the Image">
            <ShortcutRow keys={`${modKey} + Scroll`} description="Zoom in/out" />
            <ShortcutRow keys="Space + Drag" description="Pan around" />
            <ShortcutRow keys="Double-click" description="Reset view" />
          </Section>

          <Section title="Cycle Through Annotations">
            <ShortcutRow keys="Tab" description="Next annotation" />
            <ShortcutRow keys="Shift + Tab" description="Previous annotation" />
            <ShortcutRow keys={`${modKey} + A`} description="Select all" />
            <ShortcutRow keys="Escape" description="Deselect all" />
            <ShortcutRow keys="Delete" description="Delete selected" />
          </Section>

          <Section title="Drawing & OCR">
            <ShortcutRow keys="Click + Drag" description="Draw annotation" />
            <ShortcutRow keys="Shift + Drag" description="OCR region" />
          </Section>

          <Section title="Undo / Redo">
            <ShortcutRow keys={`${modKey} + Z`} description="Undo" />
            <ShortcutRow keys={`${modKey} + Shift + Z`} description="Redo" />
          </Section>

          <Section title="Tips">
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
              <strong>Assignment curves:</strong> Neumes are automatically linked to their nearest syllable. Curves show these connections when you select or hover over annotations.
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
              <strong>Auto-tightening:</strong> When you draw a bounding box, it automatically shrinks to fit the ink content.
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>Suggestions:</strong> The editor offers neume type suggestions based on image classification.
            </Typography>
          </Section>
        </DialogContent>
      </Dialog>
    </>
  );
}
