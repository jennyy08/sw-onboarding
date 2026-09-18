import { useQuery } from "@tanstack/react-query";
import type { UseQueryResult } from "@tanstack/react-query";
import type { CommandHistory } from "../utils/types";

export function useCommandHistory(
  commandId: string,
): UseQueryResult<CommandHistory[]> {
  const refetchInterval = 5_000;

  return useQuery({
    queryKey: ["commandHistory", commandId],
    queryFn: async (): Promise<CommandHistory[]> => {
      const response = await fetch(
        `http://localhost:8001/api/commands/${encodeURIComponent(commandId)}/history`,
      );

      if (!response.ok) {
        throw new Error(`Couldn't fetch command history: ${response.status}`);
      }

      const result: { data: CommandHistory[] } = await response.json();
      return result.data;
    },
    enabled: commandId.length > 0,
    refetchInterval,
  });
}
