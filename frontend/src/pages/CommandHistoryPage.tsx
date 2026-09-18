import { createColumnHelper } from "@tanstack/react-table";
import Table from "../components/Table";
import type { CommandHistory } from "../utils/types";
import { useCommandHistory } from "../hooks/useCommandHistory";
import { useState } from "react";

const columnHelper = createColumnHelper<CommandHistory>();

const columns = [
  columnHelper.accessor("status", {
    header: "Status",
  }),
  columnHelper.accessor("params", {
    header: "Parameters",
    cell: (info) => info.getValue() ?? "-",
  }),
  columnHelper.accessor("created_at", {
    header: "Recorded at",
    cell: (info) => new Date(info.getValue()).toLocaleString(),
  }),
];

/**
 * @brief CommandHistory component displaying the audit log table
 * @return tsx element of CommandHistory component
 */
function CommandHistoryPage() {
  const [commandIdInput, setCommandIdInput] = useState("");
  const [selectedCommandId, setSelectedCommandId] = useState("");

  const {
    data = [],
    isLoading,
    isError,
  } = useCommandHistory(selectedCommandId);

  return (
    <main className="flex justify-center px-4">
      <div className="w-full max-w-5xl text-white">
        <h1 className="mb-2 text-3xl font-bold">Command Audit Log</h1>
        <p className="mb-6 text-gray-300">See the lifecycle of a command</p>

        <form
          className="mb-6 flex gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            setSelectedCommandId(commandIdInput.trim());
          }}
        >
          <input
            type="text"
            value={commandIdInput}
            onChange={(e) => setCommandIdInput(e.target.value)}
            placeholder="Command ID"
            className="flex-1 rounded-lg border border-border bg-input px-4 py-2 text-foreground"
          />
          <button
            type="submit"
            className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground"
          >
            View history
          </button>
        </form>

        {!selectedCommandId && (
          <p className="mb-4 text-gray-300">
            Enter a command ID to view its audit log.
          </p>
        )}

        {selectedCommandId && isLoading && (
          <p className="mb-4">Loading history...</p>
        )}

        {selectedCommandId && isError && (
          <p className="mb-4 text-red-300">
            Could not load history for that command.
          </p>
        )}

        {!isLoading && !isError && <Table data={data} columns={columns} />}
      </div>
    </main>
  );
}

export default CommandHistoryPage;
