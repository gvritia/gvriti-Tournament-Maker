import { useEffect, useMemo, useState, type ReactNode } from "react";

type Column<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
};

type DataTableProps<T> = {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T) => string | number;
  emptyText?: string;
  isLoading?: boolean;
  pageSize?: number;
};

export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  emptyText = "Нет данных",
  isLoading = false,
  pageSize,
}: DataTableProps<T>) {
  const [page, setPage] = useState(1);
  const totalPages = pageSize ? Math.max(1, Math.ceil(rows.length / pageSize)) : 1;
  const visibleRows = useMemo(() => {
    if (!pageSize) {
      return rows;
    }

    const start = (page - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [page, pageSize, rows]);

  useEffect(() => {
    setPage(1);
  }, [pageSize, rows.length]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const hasPagination = Boolean(pageSize && rows.length > pageSize);

  return (
    <>
      {hasPagination ? (
        <TablePager
          page={page}
          pageSize={Number(pageSize)}
          totalPages={totalPages}
          totalRows={rows.length}
          onPageChange={setPage}
        />
      ) : null}

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key} className={column.className}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={columns.length} className="empty-cell">
                  Загрузка...
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="empty-cell">
                  {emptyText}
                </td>
              </tr>
            ) : (
              visibleRows.map((row) => (
                <tr key={getRowKey(row)}>
                  {columns.map((column) => (
                    <td key={column.key} className={column.className}>
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {hasPagination ? (
        <TablePager
          compact
          page={page}
          pageSize={Number(pageSize)}
          totalPages={totalPages}
          totalRows={rows.length}
          onPageChange={setPage}
        />
      ) : null}
    </>
  );
}

function TablePager({
  compact = false,
  page,
  pageSize,
  totalPages,
  totalRows,
  onPageChange,
}: {
  compact?: boolean;
  page: number;
  pageSize: number;
  totalPages: number;
  totalRows: number;
  onPageChange: (page: number) => void;
}) {
  const firstRow = (page - 1) * pageSize + 1;
  const lastRow = Math.min(page * pageSize, totalRows);

  return (
    <div className={`table-meta${compact ? " table-meta-bottom" : ""}`}>
      <span>
        {compact
          ? `Всего строк: ${totalRows}`
          : `Показаны ${firstRow}-${lastRow} из ${totalRows}`}
      </span>
      <div className="row-actions">
        <button
          className="button button-ghost"
          disabled={page === 1}
          type="button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          Назад
        </button>
        {!compact ? (
          <span className="mode-chip">
            {page} / {totalPages}
          </span>
        ) : null}
        <button
          className="button button-ghost"
          disabled={page === totalPages}
          type="button"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        >
          Вперед
        </button>
      </div>
    </div>
  );
}
