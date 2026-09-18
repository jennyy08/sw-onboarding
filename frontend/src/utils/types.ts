// Types for MCC frontend based on database schema

// Enums matching database schema
export type CommandStatus =
  "pending" | "scheduled" | "ongoing" | "cancelled" | "failed" | "completed";

export interface Command {
  id: string;
  status: CommandStatus;
  type_: number;
  params: string | null;
  created_at: string;
}

export interface MainCommand {
  id: number;
  name: string;
  params: string | null;
  format: string | null;
  data_size: number;
  total_size: number;
  priority: number;
}

export interface CommandHistory {
  id: string;
  command_id: string;
  status: CommandStatus;
  params: string | null;
  created_at: string;
}
