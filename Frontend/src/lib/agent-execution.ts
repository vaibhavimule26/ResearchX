/**
 * Central Agent Execution Controller
 *
 * Guarantees that only ONE agent can run at a time across the entire application.
 * When the user switches to another agent:
 * - Cancels/aborts the currently running agent's in-flight request.
 * - Starts only the newly selected agent.
 * - Discards cancelled/stale responses to prevent race conditions.
 * - Preserves previously completed agent outputs.
 */

export class AgentCancelledError extends Error {
  constructor(message = "Agent execution was cancelled") {
    super(message);
    this.name = "AgentCancelledError";
  }
}

export type AgentChangeListener = (activeAgent: string | null) => void;

class AgentExecutionManager {
  private currentAgent: string | null = null;
  private currentAbortController: AbortController | null = null;
  private executionGeneration = 0;
  private listeners: Set<AgentChangeListener> = new Set();

  /**
   * Start an agent execution.
   * Cancels any currently running agent and returns a unique execution ID and AbortSignal.
   */
  start(agentName: string): { signal: AbortSignal; executionId: number } {
    // 1. Cancel previous running agent if any
    this.stop();

    // 2. Start new execution generation
    this.currentAbortController = new AbortController();
    this.executionGeneration += 1;
    this.currentAgent = agentName;

    const executionId = this.executionGeneration;
    const signal = this.currentAbortController.signal;

    this.notify();
    return { signal, executionId };
  }

  /**
   * Stop/cancel the currently running agent.
   */
  stop(agentName?: string) {
    if (agentName && this.currentAgent !== agentName) {
      return;
    }

    if (this.currentAbortController) {
      try {
        this.currentAbortController.abort();
      } catch {
        // Ignore abort errors
      }
      this.currentAbortController = null;
    }

    this.currentAgent = null;
    this.notify();
  }

  /**
   * Check if a specific execution is still the active one and hasn't been aborted.
   */
  isActive(executionId: number): boolean {
    return (
      this.executionGeneration === executionId &&
      this.currentAbortController !== null &&
      !this.currentAbortController.signal.aborted
    );
  }

  /**
   * Get the name of the currently running agent, or null if idle.
   */
  getCurrentAgent(): string | null {
    return this.currentAgent;
  }

  /**
   * Subscribe to agent state changes.
   */
  subscribe(listener: AgentChangeListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.currentAgent);
      } catch (err) {
        console.error("Error in agent change listener:", err);
      }
    }
  }
}

export const agentExecutionManager = new AgentExecutionManager();
