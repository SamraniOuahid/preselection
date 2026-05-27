// src/components/common/DataTable.jsx
// Tableau générique avec tri, pagination et configuration de colonnes
import { useState } from 'react';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

export default function DataTable({
  columns,
  data,
  pageSize = 20,
  onRowClick,
  emptyMessage = 'Aucune donnée disponible',
}) {
  const [sortField, setSortField] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);

  // Tri
  const handleSort = (field) => {
    if (!field) return;
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
    setCurrentPage(1);
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortField) return 0;
    const aVal = a[sortField];
    const bVal = b[sortField];
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    if (typeof aVal === 'number') return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    return sortDirection === 'asc'
      ? String(aVal).localeCompare(String(bVal), 'fr')
      : String(bVal).localeCompare(String(aVal), 'fr');
  });

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize);
  const start = (currentPage - 1) * pageSize;
  const paginatedData = sortedData.slice(start, start + pageSize);

  if (data.length === 0) {
    return (
      <div className="card p-12 text-center">
        <p className="text-text-muted text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => col.sortable && handleSort(col.key)}
                  className={col.sortable ? 'cursor-pointer select-none hover:text-primary-700' : ''}
                  style={col.width ? { width: col.width } : undefined}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortField === col.key && (
                      sortDirection === 'asc'
                        ? <ChevronUp size={14} />
                        : <ChevronDown size={14} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rowIndex) => (
              <tr
                key={row.id || rowIndex}
                onClick={() => onRowClick?.(row)}
                className={onRowClick ? 'cursor-pointer' : ''}
              >
                {columns.map((col) => (
                  <td key={col.key}>
                    {col.render ? col.render(row[col.key], row, start + rowIndex) : row[col.key] ?? '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 px-2">
          <span className="text-sm text-text-muted">
            Affichage de {start + 1} à {Math.min(start + pageSize, data.length)} sur {data.length} résultats
          </span>
          <div className="flex items-center gap-1">
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              let page;
              if (totalPages <= 5) {
                page = i + 1;
              } else if (currentPage <= 3) {
                page = i + 1;
              } else if (currentPage >= totalPages - 2) {
                page = totalPages - 4 + i;
              } else {
                page = currentPage - 2 + i;
              }
              return (
                <button
                  key={page}
                  className={`btn btn-sm ${currentPage === page ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </button>
              );
            })}
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
