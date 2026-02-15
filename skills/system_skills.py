def shutdown_agent():
    """Signals the agent to shut down and close the session."""
    print("\n--- Shutting Down Agent ---")
    return "Shutting down. Goodbye!"


def toggle_voice_mode(enabled: bool = True):
    """Toggles whether the agent responds with voice messages on Discord."""
    status = "enabled" if enabled else "disabled"
    return f"Voice mode has been {status}."
