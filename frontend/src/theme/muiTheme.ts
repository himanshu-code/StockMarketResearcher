import { createTheme } from '@mui/material/styles'

export const muiTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#0B0E14',
      paper: '#151921',
    },
    primary: {
      main: '#00C805',
      contrastText: '#0B0E14',
    },
    secondary: {
      main: '#3D8BFF',
      contrastText: '#ffffff',
    },
    error: {
      main: '#FF3B30',
    },
    warning: {
      main: '#F59E0B',
    },
    text: {
      primary: '#E1E2EB',
      secondary: '#BBCBB2',
      disabled: '#4B5563',
    },
    divider: '#2D343F',
  },
  typography: {
    fontFamily: "'Inter', 'Geist', ui-sans-serif, system-ui, sans-serif",
    h1: { fontWeight: 700, letterSpacing: '-0.02em' },
    h2: { fontWeight: 600, letterSpacing: '-0.01em' },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    body1: { fontSize: '0.9375rem', lineHeight: 1.6 },
    body2: { fontSize: '0.875rem', lineHeight: 1.5, color: '#BBCBB2' },
    caption: { fontSize: '0.75rem', letterSpacing: '0.02em' },
  },
  shape: {
    borderRadius: 6,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#0B0E14',
          color: '#E1E2EB',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#0B0E14',
          borderBottom: '1px solid #2D343F',
          boxShadow: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#151921',
          border: '1px solid #2D343F',
          boxShadow: 'none',
          backgroundImage: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#151921',
          border: '1px solid #2D343F',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: '6px',
          variants: [
            {
              props: { variant: 'contained', color: 'primary' },
              style: {
                backgroundColor: '#00C805',
                color: '#0B0E14',
                '&:hover': {
                  backgroundColor: '#00a804',
                  boxShadow: '0 0 18px rgba(0,200,5,0.35)',
                },
              },
            },
          ],
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: '#0B0E14',
            '& fieldset': { borderColor: '#2D343F' },
            '&:hover fieldset': { borderColor: '#4B5A6B' },
            '&.Mui-focused fieldset': {
              borderColor: '#3D8BFF',
              boxShadow: '0 0 0 3px rgba(61,139,255,0.1)',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: '999px',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#272A31',
            color: '#BBCBB2',
            fontWeight: 600,
            fontSize: '0.75rem',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(255,255,255,0.03)',
          },
          '& .MuiTableCell-root': {
            borderColor: '#2D343F',
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: '#2D343F',
          borderRadius: '4px',
          height: '4px',
        },
        bar: {
          backgroundColor: '#00C805',
          borderRadius: '4px',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          color: '#BBCBB2',
          '&.Mui-selected': { color: '#E1E2EB' },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: { backgroundColor: '#00C805' },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#272A31',
          border: '1px solid #2D343F',
          color: '#E1E2EB',
          fontSize: '0.75rem',
        },
      },
    },
  },
})
