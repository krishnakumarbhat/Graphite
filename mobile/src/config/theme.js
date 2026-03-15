export const lightTheme = {
  mode: 'light',
  colors: {
    background: '#FAF7F2',
    canvas: '#F6F2EA',
    surface: '#FFFFFF',
    surfaceMuted: '#F8F4ED',
    text: '#111418',
    textSoft: '#2A3138',
    textMuted: '#6B7280',
    border: '#E7E1D8',
    primary: '#2CB1A1',
    primaryDeep: '#0E776B',
    primarySoft: '#DDF5F1',
    sand: '#E7DCCB',
    apricot: '#F4B08A',
    success: '#1F9D7A',
    warning: '#C58B2C',
    danger: '#D1493F',
    overlay: 'rgba(17, 20, 24, 0.08)',
  },
};

export const darkTheme = {
  mode: 'dark',
  colors: {
    background: '#10161A',
    canvas: '#141C21',
    surface: '#182228',
    surfaceMuted: '#1C272E',
    text: '#F5F7F8',
    textSoft: '#D8E0E5',
    textMuted: '#9BA8B1',
    border: '#25323A',
    primary: '#3DC9B7',
    primaryDeep: '#8BE2D7',
    primarySoft: '#183833',
    sand: '#3A332B',
    apricot: '#B97752',
    success: '#3AC198',
    warning: '#E2B050',
    danger: '#E26F65',
    overlay: 'rgba(0, 0, 0, 0.2)',
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const radius = {
  pill: 999,
  control: 12,
  card: 16,
  frame: 28,
};

export const getThemeTokens = (mode = 'light') => ({
  ...(mode === 'dark' ? darkTheme : lightTheme),
  spacing,
  radius,
});
