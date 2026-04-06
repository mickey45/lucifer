# PIN Authentication Guide - Lucifer AI

## Overview

Lucifer AI now includes a **PIN-based authentication system** to protect user access and data. Every time you run the chatbot, you must authenticate with your PIN before using any features.

## First-Time Setup

### Step 1: Initial PIN Registration
When you run Lucifer for the first time, you'll be prompted to create a PIN:

```
[Lucifer]: First time setup! Please create a PIN.
[*] PIN must be at least 4 digits for security.
Enter your PIN: ▮
```

### Step 2: PIN Requirements
- **Minimum Length**: 4 digits
- **Format**: Numbers only (0-9)
- **Examples**: `1234`, `9876`, `0000`, `5555`

### Step 3: Confirm PIN
You'll be asked to confirm your PIN:

```
Enter your PIN: 1234
Confirm PIN: ▮
```

### Step 4: Set Username
Finally, enter your name (optional):

```
Enter your name (or press Enter for 'User'): John
[Lucifer]: PIN registered successfully. Welcome, John.
```

## Subsequent Logins

### Standard Login
On subsequent runs, simply enter your PIN:

```
[Lucifer]: Please enter your PIN: ▮
```

### Successful Authentication
```
[Lucifer]: Please enter your PIN: 1234
[Lucifer]: Welcome back, John!
```

### Failed Authentication
If you enter an incorrect PIN:

```
[Lucifer]: Please enter your PIN: 5555
[!] Incorrect PIN. 2 attempts remaining.
[Lucifer]: Please enter your PIN: ▮
```

## Security Features

### 1. Failed Attempt Tracking
- **Count**: Tracks consecutive failed login attempts
- **Display**: Shows remaining attempts after each failure
- **Example**: "3 attempts remaining" → "2 attempts remaining" → "1 attempts remaining"

### 2. Account Lockout
- **Trigger**: 3 consecutive failed PIN attempts
- **Duration**: 5 minutes (300 seconds)
- **Behavior**: System automatically locks and shows countdown

```
[!] Too many failed attempts. System locked for 5 minutes.
[!] System locked. Try again in 298 seconds.
```

### 3. Automatic Unlock
- The system automatically unlocks after 5 minutes
- Failed attempt counter resets on successful login
- No manual intervention needed

### 4. Secure Storage

#### PIN Storage Location
- **File**: `~/.lucifer_auth.json` (in your home directory)
- **Permissions**: Restricted to owner only (mode 0600)
- **Format**: JSON with hashed PIN

#### PIN Hashing Algorithm
- **Method**: SHA-256
- **Security Level**: Cryptographically secure
- **Verification**: Safe comparison to prevent timing attacks

#### Example Storage File
```json
{
  "pin_hash": "03ac674216f3e15c131b1afbd707d5319a71bd3",
  "username": "John",
  "failed_attempts": 0,
  "locked_until": null
}
```

## Common Scenarios

### Scenario 1: Forgot Your PIN
If you forget your PIN, you must reset it:

1. Delete the authentication file:
   ```bash
   rm ~/.lucifer_auth.json
   ```

2. Run the chatbot again:
   ```bash
   python chatbot.py
   ```

3. You'll be prompted to set up a new PIN

### Scenario 2: Locked Out
If you've exceeded failed attempts:

```
[!] Too many failed attempts. System locked for 5 minutes.
```

Simply wait 5 minutes and try again.

### Scenario 3: Multiple Users
Each user has their own PIN stored in the same file. When you sign in:

```
Enter your PIN: 1234
Welcome back, John!
```

## Security Best Practices

### ✅ Do's
- ✅ Use a 4+ digit PIN (longer is better)
- ✅ Use a PIN you can remember
- ✅ Keep your PIN private
- ✅ Don't share your PIN with others
- ✅ Change your PIN periodically by deleting and resetting

### ❌ Don'ts
- ❌ Don't use simple sequences (1234, 0000, 1111)
- ❌ Don't use birthdates or anniversaries
- ❌ Don't share your PIN in chat or messages
- ❌ Don't write it down in plain text
- ❌ Don't leave the authentication file accessible

## Technical Details

### Authentication Flow

```
┌─────────────────┐
│ Start Lucifer   │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ Check Auth File      │
│ (~/.lucifer_auth.json)
└────────┬─────────────┘
         │
    ┌────┴────────┐
    │             │
    ▼             ▼
Exists     Doesn't Exist
    │             │
    ▼             ▼
Login        Setup PIN
    │             │
    ▼             ▼
Verify PIN   Register PIN
    │             │
    ▼             ▼
Success      Success
    │             │
    ▼             ▼
Run Chatbot  Run Chatbot
```

### PIN Hashing Process

```
User Input: "1234"
    │
    ▼
SHA-256 Hash Function
    │
    ▼
Hash: "03ac674216f3e15c131b1afbd707d5319a71bd3"
    │
    ▼
Compare with Stored Hash
    │
    ▼
Match / No Match
```

## Integration with Other Features

### Memory and Preferences
- After authentication, your personalized memory and preferences load
- Each user has separate data based on their username
- Memory is only accessible after successful PIN authentication

### System Commands
- All system automation features (opening apps, file operations, etc.) are protected by PIN
- PIN protects access to sensitive system information

### Chat History
- Conversation history is stored per user
- Only accessible after authentication

## FAQ

**Q: Can I reset my PIN without deleting the file?**  
A: Currently, you need to delete `~/.lucifer_auth.json` to reset. Future versions may include a PIN change command.

**Q: What if I lose the authentication file?**  
A: You'll be prompted to set up a new PIN on next run.

**Q: Is the PIN stored securely?**  
A: Yes, using SHA-256 hashing with restricted file permissions (0600).

**Q: Can someone guess my PIN?**  
A: The system locks after 3 failed attempts, preventing brute force attacks.

**Q: How long is the lockout?**  
A: 5 minutes (300 seconds) of automatic lockout.

## Support

For issues or questions about authentication:
1. Check this guide
2. Review the security test: `python security_test.py`
3. Open an issue on GitHub: https://github.com/mickey45/lucifer/issues

---

**Keep your PIN secure. Stay protected.** 🔐
