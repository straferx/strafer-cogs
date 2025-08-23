# FTPSync Cog

A Red-DiscordBot cog for backing up files from an FTP server to Discord channels.

## Features

- Connect to FTP servers and download files
- Backup multiple files to Discord channels
- Optional ZIP compression for multiple files
- Guild-specific configuration
- Beautiful embed-based responses

## Commands

### FTP Configuration Commands

- `setftphost <host>` - Set FTP server hostname or IP address
- `setftpport <port>` - Set FTP server port (default: 21)
- `setftpusername <username>` - Set FTP username
- `setftppassword <password>` - Set FTP password

### Backup Commands

- `ftpbackup` - Downloads and sends all configured backup files to the current Discord channel
- `addbackuppath <file_path>` - Add a file path to the backup list
- `removebackuppath <file_path>` - Remove a file path from the backup list
- `listbackuppaths` - List all currently configured backup paths

### Utility Commands

- `usezipfile <true/false>` - Enable or disable ZIP compression when sending multiple files
- `ftpstatus` - Show current FTP configuration status including connection details and backup paths
- `testftp` - Test the FTP connection and show root directory contents

## Setup Instructions

1. **Install the cog** in your Red-DiscordBot
2. **Configure FTP settings** using the configuration commands:
   ```
   setftphost your-ftp-server.com
   setftpport 21
   setftpusername your-username
   setftppassword your-password
   ```
3. **Add backup paths** using `addbackuppath` for each file you want to backup
4. **Test connection** using `testftp` to verify everything works
5. **Run backup** using `ftpbackup`

## Example Usage

1. Set up FTP configuration:
   ```
   setftphost ftp.example.com
   setftpport 21
   setftpusername myuser
   setftppassword mypassword
   ```

2. Test the connection:
   ```
   testftp
   ```

3. Add files to backup:
   ```
   addbackuppath /var/log/application.log
   addbackuppath /backup/database.sql
   ```

4. Enable ZIP mode (optional):
   ```
   usezipfile true
   ```

5. Run backup:
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

- **Connection failed**: Use `testftp` to verify your FTP settings
- **File not found**: Verify the file paths exist on the FTP server
- **Permission denied**: Ensure the FTP user has read access to the specified files
- **Configuration issues**: Use `ftpstatus` to check your current settings 