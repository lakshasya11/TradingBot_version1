# Tick Confirmation Configuration
# Adjust these values to change confirmation requirements

# Number of consecutive ticks needed to confirm a signal (reduced to 1 for faster entry)
REQUIRED_CONFIRMATIONS = 0

# Time window in seconds to collect confirmations (10-15 recommended)
CONFIRMATION_WINDOW = 10

# Changed to 1-tick confirmation for faster entry after 2-tick momentum
# Total: 2 ticks for momentum + 1 tick confirmation = 3 ticks total, but effectively 2 ticks for entry

print(f"Tick Confirmation Config: {REQUIRED_CONFIRMATIONS} ticks in {CONFIRMATION_WINDOW} seconds")