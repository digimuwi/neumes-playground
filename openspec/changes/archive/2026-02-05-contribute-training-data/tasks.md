## 1. Service Layer

- [x] 1.1 Add `contributeTrainingData()` function to htrService.ts that accepts imageDataUrl and annotations
- [x] 1.2 Implement coordinate conversion from normalized (0-1) to pixel coordinates using image dimensions
- [x] 1.3 Implement data transformation: group syllables into lines using computeTextLines(), format neumes
- [x] 1.4 Send POST request to `/contribute` endpoint with FormData (image blob + annotations JSON)

## 2. Toolbar UI

- [x] 2.1 Add VolunteerActivism icon import to Toolbar.tsx
- [x] 2.2 Add Contribute button after Export MEI button with tooltip "Contribute Training Data"
- [x] 2.3 Implement `canContribute` check: imageDataUrl !== null AND has syllables AND has neumes
- [x] 2.4 Add loading state (`isContributing`) and disable button while submitting

## 3. User Feedback

- [x] 3.1 Add success snackbar display on successful contribution (may need to extend existing snackbar or add success variant)
- [x] 3.2 Use existing ErrorSnackbar/setError for error handling on submission failure
- [x] 3.3 Wire up click handler to call service function and handle success/error responses
