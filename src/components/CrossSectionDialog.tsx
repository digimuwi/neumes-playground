import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Autocomplete,
  Box,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Menu,
  MenuItem,
  Popover,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { listNeumes, relabelNeume, NeumeCrop } from '../services/htrService';
import { neumeTypes, NeumeTypeInfo } from '../data/neumeTypes';
import { computeOtsuThreshold, binarizeRegion } from '../utils/imageProcessing';

interface CrossSectionDialogProps {
  open: boolean;
  onClose: () => void;
}

interface BinarizedNeume {
  /** Stable identity key for animation tracking */
  key: string;
  crop: NeumeCrop;
  binarizedDataUrl: string;
}

/**
 * Binarize a crop data URL: load image, compute Otsu threshold, binarize,
 * and return a black-on-white data URL.
 */
function binarizeCropDataUrl(dataUrl: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Could not get canvas context'));
        return;
      }

      ctx.drawImage(img, 0, 0);
      const imageData = ctx.getImageData(0, 0, img.width, img.height);
      const threshold = computeOtsuThreshold(imageData);
      const binary = binarizeRegion(imageData, { x: 0, y: 0, width: 1, height: 1 }, threshold);

      const outData = ctx.createImageData(binary.width, binary.height);
      for (let i = 0; i < binary.data.length; i++) {
        const val = binary.data[i] === 1 ? 0 : 255;
        outData.data[i * 4] = val;
        outData.data[i * 4 + 1] = val;
        outData.data[i * 4 + 2] = val;
        outData.data[i * 4 + 3] = 255;
      }

      const outCanvas = document.createElement('canvas');
      outCanvas.width = binary.width;
      outCanvas.height = binary.height;
      const outCtx = outCanvas.getContext('2d');
      if (!outCtx) {
        reject(new Error('Could not get output canvas context'));
        return;
      }
      outCtx.putImageData(outData, 0, 0);
      resolve(outCanvas.toDataURL('image/png'));
    };
    img.onerror = () => reject(new Error('Failed to load crop image'));
    img.src = dataUrl;
  });
}

/** Build a stable key for a neume based on contribution + bbox */
function neumeKey(crop: NeumeCrop): string {
  return `${crop.contribution_id}:${crop.bbox.x},${crop.bbox.y},${crop.bbox.width},${crop.bbox.height}`;
}

const CROP_HEIGHT = 48;

const filterNeumeOptions = (
  options: NeumeTypeInfo[],
  { inputValue }: { inputValue: string },
) =>
  options.filter((opt) =>
    opt.name.toLowerCase().startsWith(inputValue.toLowerCase()),
  );

export function CrossSectionDialog({ open, onClose }: CrossSectionDialogProps) {
  const [binarizedNeumes, setBinarizedNeumes] = useState<BinarizedNeume[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef(false);

  // Context menu state
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);
  const [menuTarget, setMenuTarget] = useState<BinarizedNeume | null>(null);

  // Relabel autocomplete popover state
  const [relabelAnchor, setRelabelAnchor] = useState<HTMLElement | null>(null);
  const [relabelTarget, setRelabelTarget] = useState<BinarizedNeume | null>(null);

  // Set of neume keys currently being relabeled (show spinner)
  const [relabelingKeys, setRelabelingKeys] = useState<Set<string>>(new Set());

  // Set of neume keys recently moved (for entrance animation)
  const [animatingKeys, setAnimatingKeys] = useState<Set<string>>(new Set());

  const loadNeumes = useCallback(async () => {
    setLoading(true);
    setError(null);
    setBinarizedNeumes([]);
    abortRef.current = false;

    try {
      const crops = await listNeumes();

      const results = await Promise.all(
        crops.map(async (crop) => {
          if (abortRef.current) return null;
          try {
            const binarizedDataUrl = await binarizeCropDataUrl(crop.crop_data_url);
            return { key: neumeKey(crop), crop, binarizedDataUrl };
          } catch {
            return null;
          }
        }),
      );

      if (!abortRef.current) {
        setBinarizedNeumes(results.filter((r): r is BinarizedNeume => r !== null));
      }
    } catch (err) {
      if (!abortRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to load neumes');
      }
    } finally {
      if (!abortRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (!open) {
      abortRef.current = true;
      return;
    }
    loadNeumes();
  }, [open, loadNeumes]);

  // Handle click (left or right) on a crop image
  const handleCropClick = (
    event: React.MouseEvent<HTMLElement>,
    bn: BinarizedNeume,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setMenuTarget(bn);
  };

  const closeMenu = () => {
    setMenuAnchor(null);
    setMenuTarget(null);
  };

  const handleRelabelClick = () => {
    // Transfer anchor from menu to popover
    const anchor = menuAnchor;
    const target = menuTarget;
    closeMenu();
    if (anchor && target) {
      setRelabelAnchor(anchor);
      setRelabelTarget(target);
    }
  };

  const closeRelabel = () => {
    setRelabelAnchor(null);
    setRelabelTarget(null);
  };

  const handleRelabelSelect = async (
    _event: React.SyntheticEvent,
    value: NeumeTypeInfo | null,
  ) => {
    if (!value || !relabelTarget) return;

    const target = relabelTarget;
    const key = target.key;
    const newType = value.type;
    closeRelabel();

    // Show spinner
    setRelabelingKeys((prev) => new Set(prev).add(key));

    try {
      await relabelNeume(target.crop.contribution_id, target.crop.bbox, newType);

      // Update the neume's type in state → it moves to the new row
      setBinarizedNeumes((prev) =>
        prev.map((bn) =>
          bn.key === key
            ? { ...bn, crop: { ...bn.crop, type: newType } }
            : bn,
        ),
      );

      // Trigger entrance animation on the moved item
      setAnimatingKeys((prev) => new Set(prev).add(key));
      setTimeout(() => {
        setAnimatingKeys((prev) => {
          const next = new Set(prev);
          next.delete(key);
          return next;
        });
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Relabel failed');
    } finally {
      setRelabelingKeys((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  // Group binarized neumes by type
  const neumesByType = new Map<string, BinarizedNeume[]>();
  for (const bn of binarizedNeumes) {
    const list = neumesByType.get(bn.crop.type) || [];
    list.push(bn);
    neumesByType.set(bn.crop.type, list);
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>Cross Section</DialogTitle>
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
        {!loading && !error && (
          <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {neumeTypes.map((info) => {
                const instances = neumesByType.get(info.type) || [];
                return (
                  <Box
                    component="tr"
                    key={info.type}
                    sx={{
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      '&:hover': { bgcolor: 'action.hover' },
                    }}
                  >
                    <Box
                      component="td"
                      sx={{
                        py: 1,
                        pr: 2,
                        whiteSpace: 'nowrap',
                        verticalAlign: 'middle',
                        width: 180,
                        minWidth: 180,
                        color: instances.length === 0 ? 'text.disabled' : 'text.primary',
                      }}
                    >
                      <Typography variant="body2" component="span">
                        {info.name}
                      </Typography>
                      <Typography
                        variant="caption"
                        component="span"
                        sx={{ ml: 1, color: 'text.secondary' }}
                      >
                        ({instances.length})
                      </Typography>
                    </Box>
                    <Box
                      component="td"
                      sx={{
                        py: 1,
                        verticalAlign: 'middle',
                        overflowX: 'auto',
                      }}
                    >
                      <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                        {instances.map((bn) => {
                          const isRelabeling = relabelingKeys.has(bn.key);
                          const isAnimating = animatingKeys.has(bn.key);

                          return (
                            <Tooltip
                              key={bn.key}
                              title={`${info.name} — ${bn.crop.contribution_id.slice(0, 8)}`}
                            >
                              <Box
                                onClick={(e) => handleCropClick(e, bn)}
                                onContextMenu={(e) => handleCropClick(e, bn)}
                                sx={{
                                  height: CROP_HEIGHT,
                                  border: '1px solid',
                                  borderColor: 'divider',
                                  borderRadius: 0.5,
                                  flexShrink: 0,
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  '&:hover': { borderColor: 'primary.main' },
                                  ...(isAnimating && {
                                    animation: 'crossSectionFadeIn 0.5s ease-out',
                                    '@keyframes crossSectionFadeIn': {
                                      '0%': {
                                        opacity: 0,
                                        transform: 'scale(0.7)',
                                        bgcolor: 'primary.light',
                                      },
                                      '50%': {
                                        opacity: 1,
                                        transform: 'scale(1.1)',
                                      },
                                      '100%': {
                                        opacity: 1,
                                        transform: 'scale(1)',
                                      },
                                    },
                                  }),
                                }}
                              >
                                {isRelabeling ? (
                                  <CircularProgress size={20} sx={{ mx: 1 }} />
                                ) : (
                                  <Box
                                    component="img"
                                    src={bn.binarizedDataUrl}
                                    sx={{ height: '100%', display: 'block' }}
                                  />
                                )}
                              </Box>
                            </Tooltip>
                          );
                        })}
                      </Box>
                    </Box>
                  </Box>
                );
              })}
            </tbody>
          </Box>
        )}
      </DialogContent>

      {/* Context menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={closeMenu}
      >
        <MenuItem onClick={handleRelabelClick}>Relabel...</MenuItem>
      </Menu>

      {/* Relabel autocomplete popover */}
      <Popover
        open={Boolean(relabelAnchor)}
        anchorEl={relabelAnchor}
        onClose={closeRelabel}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{ paper: { sx: { p: 1, width: 280 } } }}
      >
        <Autocomplete
          size="small"
          options={neumeTypes}
          getOptionLabel={(option) => option.name}
          filterOptions={filterNeumeOptions}
          openOnFocus
          autoHighlight
          onChange={handleRelabelSelect}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Neume type"
              autoFocus
              variant="outlined"
              size="small"
            />
          )}
          renderOption={(props, option) => (
            <li {...props} key={option.type}>
              <Box>
                <Typography variant="body2">{option.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {option.description}
                </Typography>
              </Box>
            </li>
          )}
        />
      </Popover>
    </Dialog>
  );
}
