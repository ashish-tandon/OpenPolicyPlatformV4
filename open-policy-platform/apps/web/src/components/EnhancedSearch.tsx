import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Typography,
  Chip,
  CircularProgress,
  Divider,
  Button,
  Stack,
  Collapse,
  alpha,
  useTheme,
  Fade,
  Popper,
  ClickAwayListener,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear,
  History,
  TrendingUp,
  Policy,
  Person,
  Gavel,
  Article,
  FilterList,
  Close,
  ArrowForward,
  Schedule,
  Category,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { debounce } from 'lodash';

const MotionPaper = motion(Paper);
const MotionBox = motion(Box);

interface SearchResult {
  id: string;
  type: 'policy' | 'bill' | 'representative' | 'committee' | 'debate';
  title: string;
  description: string;
  date?: string;
  category?: string;
  relevance: number;
}

interface SearchFilters {
  type: string[];
  dateRange: string;
  category: string[];
}

const EnhancedSearch: React.FC = () => {
  const theme = useTheme();
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState<SearchFilters>({
    type: [],
    dateRange: 'all',
    category: [],
  });
  
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Mock search function - replace with actual API call
  const performSearch = async (searchQuery: string) => {
    setIsSearching(true);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock results
    const mockResults: SearchResult[] = [
      {
        id: '1',
        type: 'policy',
        title: 'Healthcare Reform Act 2024',
        description: 'Comprehensive healthcare policy reform addressing accessibility and affordability',
        date: '2024-01-15',
        category: 'Healthcare',
        relevance: 0.95,
      },
      {
        id: '2',
        type: 'bill',
        title: 'Bill C-45: Digital Privacy Protection',
        description: 'Enhanced privacy protections for digital services and online platforms',
        date: '2024-01-10',
        category: 'Technology',
        relevance: 0.88,
      },
      {
        id: '3',
        type: 'representative',
        title: 'Hon. Jane Smith',
        description: 'Minister of Health - Leading healthcare reform initiatives',
        category: 'Government',
        relevance: 0.82,
      },
      {
        id: '4',
        type: 'debate',
        title: 'Parliamentary Debate on Healthcare Funding',
        description: 'Full transcript and voting records from the healthcare funding debate',
        date: '2024-01-08',
        category: 'Parliament',
        relevance: 0.75,
      },
    ];
    
    setResults(mockResults);
    setIsSearching(false);
    
    // Add to recent searches
    if (searchQuery && !recentSearches.includes(searchQuery)) {
      setRecentSearches(prev => [searchQuery, ...prev.slice(0, 4)]);
    }
  };

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((searchQuery: string) => {
      if (searchQuery.trim()) {
        performSearch(searchQuery);
      } else {
        setResults([]);
      }
    }, 300),
    []
  );

  useEffect(() => {
    if (query) {
      debouncedSearch(query);
      setShowResults(true);
    } else {
      setResults([]);
      setShowResults(false);
    }
  }, [query, debouncedSearch]);

  const handleClearSearch = () => {
    setQuery('');
    setResults([]);
    setShowResults(false);
    inputRef.current?.focus();
  };

  const handleResultClick = (result: SearchResult) => {
    // Navigate to result detail page
    console.log('Navigate to:', result);
    setShowResults(false);
  };

  const getIconForType = (type: string) => {
    switch (type) {
      case 'policy':
        return <Policy />;
      case 'bill':
        return <Gavel />;
      case 'representative':
        return <Person />;
      case 'committee':
        return <Category />;
      case 'debate':
        return <Article />;
      default:
        return <Article />;
    }
  };

  const getColorForType = (type: string) => {
    switch (type) {
      case 'policy':
        return 'primary';
      case 'bill':
        return 'secondary';
      case 'representative':
        return 'success';
      case 'committee':
        return 'warning';
      case 'debate':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <ClickAwayListener onClickAway={() => setShowResults(false)}>
      <Box sx={{ position: 'relative', width: '100%', maxWidth: 800, mx: 'auto' }}>
        <MotionBox
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <TextField
            ref={inputRef}
            fullWidth
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setShowResults(true)}
            placeholder="Search policies, bills, representatives, committees..."
            variant="outlined"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <Stack direction="row" spacing={1}>
                    {query && (
                      <IconButton size="small" onClick={handleClearSearch}>
                        <Clear />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => setShowFilters(!showFilters)}
                      color={showFilters ? 'primary' : 'default'}
                    >
                      <FilterList />
                    </IconButton>
                  </Stack>
                </InputAdornment>
              ),
              sx: {
                borderRadius: 3,
                backgroundColor: theme.palette.background.paper,
                boxShadow: `0 4px 20px ${alpha(theme.palette.common.black, 0.08)}`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: `0 8px 30px ${alpha(theme.palette.common.black, 0.12)}`,
                },
                '&.Mui-focused': {
                  boxShadow: `0 8px 30px ${alpha(theme.palette.primary.main, 0.2)}`,
                },
              },
            }}
          />
        </MotionBox>

        {/* Filters */}
        <Collapse in={showFilters}>
          <Paper
            sx={{
              mt: 2,
              p: 2,
              borderRadius: 2,
              boxShadow: `0 4px 20px ${alpha(theme.palette.common.black, 0.08)}`,
            }}
          >
            <Stack spacing={2}>
              <Typography variant="subtitle2" fontWeight="bold">
                Filter Results
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {['Policy', 'Bill', 'Representative', 'Committee', 'Debate'].map((type) => (
                  <Chip
                    key={type}
                    label={type}
                    onClick={() => {
                      setSelectedFilters(prev => ({
                        ...prev,
                        type: prev.type.includes(type)
                          ? prev.type.filter(t => t !== type)
                          : [...prev.type, type],
                      }));
                    }}
                    color={selectedFilters.type.includes(type) ? 'primary' : 'default'}
                    sx={{ mb: 1 }}
                  />
                ))}
              </Stack>
            </Stack>
          </Paper>
        </Collapse>

        {/* Search Results Dropdown */}
        <AnimatePresence>
          {showResults && (query || recentSearches.length > 0) && (
            <MotionPaper
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              sx={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                mt: 1,
                maxHeight: 600,
                overflow: 'auto',
                borderRadius: 2,
                boxShadow: `0 8px 40px ${alpha(theme.palette.common.black, 0.15)}`,
                zIndex: 1000,
              }}
            >
              {/* Recent Searches */}
              {!query && recentSearches.length > 0 && (
                <>
                  <Box sx={{ p: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Recent Searches
                    </Typography>
                    <List dense>
                      {recentSearches.map((search, index) => (
                        <ListItem
                          key={index}
                          button
                          onClick={() => setQuery(search)}
                          sx={{
                            borderRadius: 1,
                            '&:hover': {
                              bgcolor: alpha(theme.palette.primary.main, 0.08),
                            },
                          }}
                        >
                          <ListItemIcon>
                            <History fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={search} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                  <Divider />
                </>
              )}

              {/* Trending Searches */}
              {!query && (
                <Box sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Trending Searches
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {['Healthcare Reform', 'Climate Policy', 'Budget 2024', 'Digital Privacy'].map((trend) => (
                      <Chip
                        key={trend}
                        label={trend}
                        size="small"
                        icon={<TrendingUp fontSize="small" />}
                        onClick={() => setQuery(trend)}
                        sx={{
                          mb: 1,
                          '&:hover': {
                            bgcolor: alpha(theme.palette.primary.main, 0.08),
                          },
                        }}
                      />
                    ))}
                  </Stack>
                </Box>
              )}

              {/* Loading State */}
              {isSearching && (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <CircularProgress size={40} />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Searching...
                  </Typography>
                </Box>
              )}

              {/* Search Results */}
              {!isSearching && results.length > 0 && (
                <>
                  {query && <Divider />}
                  <List>
                    {results.map((result, index) => (
                      <MotionBox
                        key={result.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <ListItem
                          button
                          onClick={() => handleResultClick(result)}
                          sx={{
                            py: 2,
                            '&:hover': {
                              bgcolor: alpha(theme.palette.primary.main, 0.04),
                            },
                          }}
                        >
                          <ListItemIcon>
                            <Box
                              sx={{
                                p: 1,
                                borderRadius: 1,
                                bgcolor: alpha(theme.palette[getColorForType(result.type)].main, 0.1),
                                color: theme.palette[getColorForType(result.type)].main,
                              }}
                            >
                              {getIconForType(result.type)}
                            </Box>
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Typography variant="subtitle1" fontWeight="medium">
                                {result.title}
                              </Typography>
                            }
                            secondary={
                              <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                                <Typography variant="body2" color="text.secondary">
                                  {result.description}
                                </Typography>
                                <Stack direction="row" spacing={1} alignItems="center">
                                  {result.date && (
                                    <Chip
                                      icon={<Schedule fontSize="small" />}
                                      label={new Date(result.date).toLocaleDateString()}
                                      size="small"
                                      variant="outlined"
                                    />
                                  )}
                                  {result.category && (
                                    <Chip
                                      label={result.category}
                                      size="small"
                                      color={getColorForType(result.type)}
                                    />
                                  )}
                                  <Typography variant="caption" color="text.secondary">
                                    {Math.round(result.relevance * 100)}% match
                                  </Typography>
                                </Stack>
                              </Stack>
                            }
                          />
                          <ListItemSecondaryAction>
                            <IconButton edge="end" size="small">
                              <ArrowForward />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                        {index < results.length - 1 && <Divider variant="inset" component="li" />}
                      </MotionBox>
                    ))}
                  </List>
                  <Divider />
                  <Box sx={{ p: 2, textAlign: 'center' }}>
                    <Button
                      fullWidth
                      variant="text"
                      endIcon={<ArrowForward />}
                      onClick={() => console.log('View all results')}
                    >
                      View all {results.length}+ results
                    </Button>
                  </Box>
                </>
              )}

              {/* No Results */}
              {!isSearching && query && results.length === 0 && (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography variant="body1" color="text.secondary">
                    No results found for "{query}"
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Try adjusting your search terms or filters
                  </Typography>
                </Box>
              )}
            </MotionPaper>
          )}
        </AnimatePresence>
      </Box>
    </ClickAwayListener>
  );
};

export default EnhancedSearch;