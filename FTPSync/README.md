# FTPSync Cog

A Red-DiscordBot cog for backing up files from an FTP server to Discord channels.

## Features

- Connect to FTP servers and download files
- Backup multiple files to Discord channels
- Optional ZIP compression for multiple files
- Secure configuration using Discord modals
- Guild-specific configuration

## Commands

### `/setftpconfig`
Opens a modal window to configure FTP connection settings:
- **Host**: FTP server hostname or IP address
- **Port**: FTP server port (default: 21)
- **Username**: FTP username
- **Password**: FTP password (hidden input)

### `ftpbackup`
Downloads and sends all configured backup files to the current Discord channel.

### `addbackuppath <file_path>`
Adds a file path to the backup list. Example: `/addbackuppath /path/to/file.txt`

### `removebackuppath <file_path>`
Removes a file path from the backup list.

### `listbackuppaths`
Lists all currently configured backup paths.

### `usezipfile <true/false>`
Enables or disables ZIP compression when sending multiple files.

### `ftpstatus`
Shows the current FTP configuration status including connection details and backup paths.

## Setup Instructions

1. **Install the cog** in your Red-DiscordBot
2. **Configure FTP settings** using `setftpconfig`
3. **Add backup paths** using `addbackuppath` for each file you want to backup
4. **Run backup** using `ftpbackup`

## Example Usage

1. Set up FTP configuration:
   ```
   setftpconfig
   ```

2. Add files to backup:
   ```
   addbackuppath /var/log/application.log
   addbackuppath /backup/database.sql
   ```

3. Enable ZIP mode (optional):
   ```
   usezipfile true
   ```

4. Run backup:
   ```
   ftpbackup
   ```

## Requirements

- Red-DiscordBot
- `aioftp` library (for async FTP operations)
- Administrator permissions for all commands

## Security Notes

- FTP passwords are stored encrypted in the bot's configuration
- All commands require administrator permissions
- Configuration is guild-specific

## Troubleshooting

- **Connection failed**: Check your FTP host, port, username, and password
- **File not found**: Verify the file paths exist on the FTP server
- **Permission denied**: Ensure the FTP user has read access to the specified files 