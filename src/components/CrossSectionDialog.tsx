import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Box,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Tooltip,
  Typography,
} from '@mui/material';
import { listNeumes, NeumeCrop } from '../services/htrService';
import { neumeTypes } from '../data/neumeTypes';
import { computeOtsuThreshold, binarizeRegion } from '../utils/imageProcessing';

interface CrossSectionDialogProps {
  open: boolean;
  onClose: () => void;
}

interface BinarizedNeume {
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

      // Convert BinaryImage to black-on-white ImageData
      const outData = ctx.createImageData(binary.width, binary.height);
      for (let i = 0; i < binary.data.length; i++) {
        const val = binary.data[i] === 1 ? 0 : 255; // foreground=black, background=white
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

const CROP_HEIGHT = 48;

export function CrossSectionDialog({ open, onClose }: CrossSectionDialogProps) {
  const [binarizedNeumes, setBinarizedNeumes] = useState<BinarizedNeume[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef(false);

  const loadNeumes = useCallback(async () => {
    setLoading(true);
    setError(null);
    setBinarizedNeumes([]);
    abortRef.current = false;

    try {
      const crops = await listNeumes();

      // Binarize all crops in parallel (they're small images)
      const results = await Promise.all(
        crops.map(async (crop) => {
          if (abortRef.current) return null;
          try {
            const binarizedDataUrl = await binarizeCropDataUrl(crop.crop_data_url);
            return { crop, binarizedDataUrl };
          } catch {
            // Skip crops that fail to binarize
            return null;
          }
        })
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
                        {instances.map((bn, idx) => (
                          <Tooltip
                            key={idx}
                            title={`${info.name} — ${bn.crop.contribution_id.slice(0, 8)}`}
                          >
                            <Box
                              component="img"
                              src={bn.binarizedDataUrl}
                              sx={{
                                height: CROP_HEIGHT,
                                border: '1px solid',
                                borderColor: 'divider',
                                borderRadius: 0.5,
                                flexShrink: 0,
                              }}
                            />
                          </Tooltip>
                        ))}
                      </Box>
                    </Box>
                  </Box>
                );
              })}
            </tbody>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}
