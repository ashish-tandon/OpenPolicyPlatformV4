import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Paper,
  Checkbox,
  IconButton,
  Toolbar,
  Typography,
  Tooltip,
  TextField,
  InputAdornment,
  Menu,
  MenuItem,
  Chip,
  Stack,
  Button,
  Collapse,
  Avatar,
  LinearProgress,
  useTheme,
  useMediaQuery,
  alpha,
  Card,
  CardContent,
} from '@mui/material';
import {
  Delete,
  FilterList,
  Search,
  Download,
  Print,
  ViewColumn,
  MoreVert,
  Edit,
  KeyboardArrowDown,
  KeyboardArrowRight,
  Star,
  StarBorder,
} from '@mui/icons-material';
import { visuallyHidden } from '@mui/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface Data {
  id: string;
  title: string;
  type: string;
  status: string;
  category: string;
  date: string;
  author: string;
  priority: 'high' | 'medium' | 'low';
  starred: boolean;
  [key: string]: any;
}

interface HeadCell {
  id: keyof Data;
  numeric: boolean;
  disablePadding: boolean;
  label: string;
  width?: string | number;
}

interface AdvancedDataTableProps {
  data: Data[];
  title?: string;
  onRowClick?: (row: Data) => void;
  onEdit?: (row: Data) => void;
  onDelete?: (selected: string[]) => void;
  loading?: boolean;
}

const headCells: HeadCell[] = [
  { id: 'title', numeric: false, disablePadding: true, label: 'Title', width: '30%' },
  { id: 'type', numeric: false, disablePadding: false, label: 'Type' },
  { id: 'status', numeric: false, disablePadding: false, label: 'Status' },
  { id: 'category', numeric: false, disablePadding: false, label: 'Category' },
  { id: 'author', numeric: false, disablePadding: false, label: 'Author' },
  { id: 'date', numeric: false, disablePadding: false, label: 'Date' },
  { id: 'priority', numeric: false, disablePadding: false, label: 'Priority' },
];

type Order = 'asc' | 'desc';

const AdvancedDataTable: React.FC<AdvancedDataTableProps> = ({
  data,
  title = 'Data Table',
  onRowClick,
  onEdit,
  onDelete,
  loading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  
  const [order, setOrder] = useState<Order>('asc');
  const [orderBy, setOrderBy] = useState<keyof Data>('date');
  const [selected, setSelected] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, string[]>>({});
  const [visibleColumns, setVisibleColumns] = useState<string[]>(
    headCells.map(cell => cell.id as string)
  );
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [columnAnchorEl, setColumnAnchorEl] = useState<null | HTMLElement>(null);

  // Filter and search data
  const filteredData = useMemo(() => {
    let filtered = [...data];
    
    // Apply search
    if (searchQuery) {
      filtered = filtered.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    }
    
    // Apply filters
    Object.entries(filters).forEach(([key, values]) => {
      if (values.length > 0) {
        filtered = filtered.filter(row => values.includes(String(row[key])));
      }
    });
    
    return filtered;
  }, [data, searchQuery, filters]);

  // Sort data
  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => {
      const aVal = a[orderBy];
      const bVal = b[orderBy];
      
      if (aVal < bVal) return order === 'asc' ? -1 : 1;
      if (aVal > bVal) return order === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, order, orderBy]);

  // Paginate data
  const paginatedData = useMemo(() => {
    return sortedData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [sortedData, page, rowsPerPage]);

  const handleRequestSort = (property: keyof Data) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = paginatedData.map((n) => n.id);
      setSelected(newSelected);
      return;
    }
    setSelected([]);
  };

  const handleClick = (event: React.MouseEvent<unknown>, id: string) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected: string[] = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      );
    }

    setSelected(newSelected);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleToggleRow = (id: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleToggleStar = (event: React.MouseEvent, id: string) => {
    event.stopPropagation();
    // Handle star toggle logic
    console.log('Toggle star for:', id);
  };

  const isSelected = (id: string) => selected.indexOf(id) !== -1;

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success';
      case 'pending':
        return 'warning';
      case 'completed':
        return 'info';
      case 'rejected':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return theme.palette.error.main;
      case 'medium':
        return theme.palette.warning.main;
      case 'low':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const exportData = (format: 'csv' | 'json') => {
    if (format === 'csv') {
      // CSV export logic
      const headers = headCells.map(cell => cell.label).join(',');
      const rows = filteredData.map(row =>
        headCells.map(cell => row[cell.id]).join(',')
      ).join('\n');
      const csv = `${headers}\n${rows}`;
      
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.toLowerCase().replace(/\s+/g, '-')}-${new Date().toISOString()}.csv`;
      a.click();
    } else {
      // JSON export
      const json = JSON.stringify(filteredData, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.toLowerCase().replace(/\s+/g, '-')}-${new Date().toISOString()}.json`;
      a.click();
    }
  };

  // Mobile card view
  const MobileCard = ({ row }: { row: Data }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <Card
        sx={{
          mb: 2,
          cursor: onRowClick ? 'pointer' : 'default',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: theme.shadows[4],
          },
        }}
        onClick={() => onRowClick?.(row)}
      >
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
            <Typography variant="h6" component="div" sx={{ fontSize: '1.1rem' }}>
              {row.title}
            </Typography>
            <IconButton
              size="small"
              onClick={(e) => handleToggleStar(e, row.id)}
            >
              {row.starred ? <Star color="warning" /> : <StarBorder />}
            </IconButton>
          </Stack>
          
          <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
            <Chip
              label={row.type}
              size="small"
              sx={{ mb: 1 }}
            />
            <Chip
              label={row.status}
              size="small"
              color={getStatusColor(row.status) as any}
              sx={{ mb: 1 }}
            />
            <Chip
              label={row.category}
              size="small"
              variant="outlined"
              sx={{ mb: 1 }}
            />
          </Stack>
          
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              <strong>Author:</strong> {row.author}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Date:</strong> {new Date(row.date).toLocaleDateString()}
            </Typography>
            <Box>
              <Typography variant="body2" color="text.secondary" component="span">
                <strong>Priority:</strong>
              </Typography>
              <Box
                component="span"
                sx={{
                  display: 'inline-block',
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: getPriorityColor(row.priority),
                  ml: 1,
                  mr: 0.5,
                }}
              />
              <Typography variant="body2" component="span">
                {row.priority}
              </Typography>
            </Box>
          </Stack>
          
          {onEdit && (
            <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
              <Button
                size="small"
                startIcon={<Edit />}
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(row);
                }}
              >
                Edit
              </Button>
              <Checkbox
                checked={isSelected(row.id)}
                onChange={(e) => handleClick(e, row.id)}
                onClick={(e) => e.stopPropagation()}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Toolbar
          sx={{
            pl: { sm: 2 },
            pr: { xs: 1, sm: 1 },
            ...(selected.length > 0 && {
              bgcolor: (theme) =>
                alpha(theme.palette.primary.main, theme.palette.action.activatedOpacity),
            }),
          }}
        >
          {selected.length > 0 ? (
            <Typography
              sx={{ flex: '1 1 100%' }}
              color="inherit"
              variant="subtitle1"
              component="div"
            >
              {selected.length} selected
            </Typography>
          ) : (
            <Typography
              sx={{ flex: '1 1 100%' }}
              variant="h6"
              id="tableTitle"
              component="div"
            >
              {title}
            </Typography>
          )}

          {selected.length > 0 ? (
            <Tooltip title="Delete">
              <IconButton onClick={() => onDelete?.(selected)}>
                <Delete />
              </IconButton>
            </Tooltip>
          ) : (
            <Stack direction="row" spacing={1}>
              <TextField
                size="small"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                sx={{ width: 200, display: { xs: 'none', sm: 'block' } }}
              />
              <Tooltip title="Filter list">
                <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
                  <FilterList />
                </IconButton>
              </Tooltip>
              <Tooltip title="Columns">
                <IconButton onClick={(e) => setColumnAnchorEl(e.currentTarget)}>
                  <ViewColumn />
                </IconButton>
              </Tooltip>
              <Tooltip title="Export">
                <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
                  <Download />
                </IconButton>
              </Tooltip>
            </Stack>
          )}
        </Toolbar>

        {loading && <LinearProgress />}

        {isMobile ? (
          // Mobile view
          <Box sx={{ p: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search fontSize="small" />
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />
            <AnimatePresence>
              {paginatedData.map((row) => (
                <MobileCard key={row.id} row={row} />
              ))}
            </AnimatePresence>
          </Box>
        ) : (
          // Desktop view
          <TableContainer>
            <Table sx={{ minWidth: 750 }} aria-labelledby="tableTitle" size="medium">
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      indeterminate={selected.length > 0 && selected.length < paginatedData.length}
                      checked={paginatedData.length > 0 && selected.length === paginatedData.length}
                      onChange={handleSelectAllClick}
                    />
                  </TableCell>
                  <TableCell />
                  {headCells
                    .filter(headCell => visibleColumns.includes(headCell.id as string))
                    .map((headCell) => (
                      <TableCell
                        key={headCell.id}
                        align={headCell.numeric ? 'right' : 'left'}
                        padding={headCell.disablePadding ? 'none' : 'normal'}
                        sortDirection={orderBy === headCell.id ? order : false}
                        sx={{ width: headCell.width }}
                      >
                        <TableSortLabel
                          active={orderBy === headCell.id}
                          direction={orderBy === headCell.id ? order : 'asc'}
                          onClick={() => handleRequestSort(headCell.id)}
                        >
                          {headCell.label}
                          {orderBy === headCell.id ? (
                            <Box component="span" sx={visuallyHidden}>
                              {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                            </Box>
                          ) : null}
                        </TableSortLabel>
                      </TableCell>
                    ))}
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedData.map((row, index) => {
                  const isItemSelected = isSelected(row.id);
                  const labelId = `enhanced-table-checkbox-${index}`;
                  const isExpanded = expandedRows.has(row.id);

                  return (
                    <React.Fragment key={row.id}>
                      <TableRow
                        hover
                        role="checkbox"
                        aria-checked={isItemSelected}
                        tabIndex={-1}
                        selected={isItemSelected}
                        sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                      >
                        <TableCell padding="checkbox">
                          <Checkbox
                            color="primary"
                            checked={isItemSelected}
                            onChange={(event) => handleClick(event, row.id)}
                            inputProps={{ 'aria-labelledby': labelId }}
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => handleToggleRow(row.id)}
                          >
                            {isExpanded ? <KeyboardArrowDown /> : <KeyboardArrowRight />}
                          </IconButton>
                        </TableCell>
                        {visibleColumns.includes('title') && (
                          <TableCell
                            component="th"
                            id={labelId}
                            scope="row"
                            padding="none"
                            onClick={() => onRowClick?.(row)}
                          >
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <Typography variant="body2" fontWeight="medium">
                                {row.title}
                              </Typography>
                              <IconButton
                                size="small"
                                onClick={(e) => handleToggleStar(e, row.id)}
                              >
                                {row.starred ? <Star color="warning" fontSize="small" /> : <StarBorder fontSize="small" />}
                              </IconButton>
                            </Stack>
                          </TableCell>
                        )}
                        {visibleColumns.includes('type') && (
                          <TableCell>{row.type}</TableCell>
                        )}
                        {visibleColumns.includes('status') && (
                          <TableCell>
                            <Chip
                              label={row.status}
                              size="small"
                              color={getStatusColor(row.status) as any}
                            />
                          </TableCell>
                        )}
                        {visibleColumns.includes('category') && (
                          <TableCell>{row.category}</TableCell>
                        )}
                        {visibleColumns.includes('author') && (
                          <TableCell>
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
                                {row.author.charAt(0)}
                              </Avatar>
                              <Typography variant="body2">{row.author}</Typography>
                            </Stack>
                          </TableCell>
                        )}
                        {visibleColumns.includes('date') && (
                          <TableCell>
                            {new Date(row.date).toLocaleDateString()}
                          </TableCell>
                        )}
                        {visibleColumns.includes('priority') && (
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box
                                sx={{
                                  width: 8,
                                  height: 8,
                                  borderRadius: '50%',
                                  bgcolor: getPriorityColor(row.priority),
                                }}
                              />
                              <Typography variant="body2">{row.priority}</Typography>
                            </Box>
                          </TableCell>
                        )}
                        <TableCell align="right">
                          {onEdit && (
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                onEdit(row);
                              }}
                            >
                              <Edit fontSize="small" />
                            </IconButton>
                          )}
                          <IconButton size="small">
                            <MoreVert fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={headCells.length + 3}>
                          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                            <Box sx={{ margin: 2 }}>
                              <Typography variant="h6" gutterBottom component="div">
                                Additional Details
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                This is where additional information about the row can be displayed.
                                You can add any content here including charts, detailed descriptions, or related data.
                              </Typography>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredData.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Export Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl) && selected.length === 0}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => { exportData('csv'); setAnchorEl(null); }}>
          Export as CSV
        </MenuItem>
        <MenuItem onClick={() => { exportData('json'); setAnchorEl(null); }}>
          Export as JSON
        </MenuItem>
        <MenuItem onClick={() => { window.print(); setAnchorEl(null); }}>
          <Print fontSize="small" sx={{ mr: 1 }} />
          Print
        </MenuItem>
      </Menu>

      {/* Column Visibility Menu */}
      <Menu
        anchorEl={columnAnchorEl}
        open={Boolean(columnAnchorEl)}
        onClose={() => setColumnAnchorEl(null)}
      >
        {headCells.map((column) => (
          <MenuItem key={column.id as string}>
            <Checkbox
              checked={visibleColumns.includes(column.id as string)}
              onChange={(e) => {
                if (e.target.checked) {
                  setVisibleColumns([...visibleColumns, column.id as string]);
                } else {
                  setVisibleColumns(visibleColumns.filter(col => col !== column.id));
                }
              }}
            />
            {column.label}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default AdvancedDataTable;