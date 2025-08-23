import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
import asyncio
import aioftp
import io
import zipfile
from typing import List, Optional
import os

class FTPSync(commands.Cog):
    """FTP Sync cog for backing up files from FTP server to Discord channels."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20250823, force_registration=True)
        self.config.register_guild(
            ftp_host="",
            ftp_port=21,
            ftp_username="",
            ftp_password="",
            backup_paths=[],
            use_zip_file=False
        )

    @commands.command(name="setftphost")
    @commands.has_permissions(administrator=True)
    async def set_ftp_host(self, ctx: commands.Context, host: str):
        """Set the FTP host."""
        await self.config.guild(ctx.guild).ftp_host.set(host)
        embed = discord.Embed(
            title="✅ FTP Host Updated",
            description=f"FTP host has been set to: `{host}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setftpport")
    @commands.has_permissions(administrator=True)
    async def set_ftp_port(self, ctx: commands.Context, port: int):
        """Set the FTP port."""
        if port <= 0 or port > 65535:
            embed = discord.Embed(
                title="❌ Invalid Port",
                description="Port must be between 1 and 65535.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        await self.config.guild(ctx.guild).ftp_port.set(port)
        embed = discord.Embed(
            title="✅ FTP Port Updated",
            description=f"FTP port has been set to: `{port}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setftpusername")
    @commands.has_permissions(administrator=True)
    async def set_ftp_username(self, ctx: commands.Context, username: str):
        """Set the FTP username."""
        await self.config.guild(ctx.guild).ftp_username.set(username)
        embed = discord.Embed(
            title="✅ FTP Username Updated",
            description=f"FTP username has been set to: `{username}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setftppassword")
    @commands.has_permissions(administrator=True)
    async def set_ftp_password(self, ctx: commands.Context, password: str):
        """Set the FTP password."""
        await self.config.guild(ctx.guild).ftp_password.set(password)
        embed = discord.Embed(
            title="✅ FTP Password Updated",
            description="FTP password has been set successfully.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ftpbackup")
    @commands.has_permissions(administrator=True)
    async def ftp_backup(self, ctx: commands.Context):
        """Backup files from FTP server to the current Discord channel."""
        # Get configuration
        guild_config = await self.config.guild(ctx.guild).all()
        
        # Check if FTP is configured
        if not guild_config["ftp_host"] or not guild_config["ftp_username"]:
            embed = discord.Embed(
                title="❌ FTP Not Configured",
                description="FTP configuration is not complete. Please set up the following:\n"
                           "• `setftphost <host>`\n"
                           "• `setftpport <port>`\n"
                           "• `setftpusername <username>`\n"
                           "• `setftppassword <password>`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if backup paths are configured
        if not guild_config["backup_paths"]:
            embed = discord.Embed(
                title="❌ No Backup Paths",
                description="No backup paths configured. Use `addbackuppath <file_path>` to add files to backup.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Send initial message
        status_embed = discord.Embed(
            title="🔄 Connecting to FTP Server",
            description="Attempting to connect to the FTP server...",
            color=discord.Color.blue()
        )
        status_msg = await ctx.send(embed=status_embed)
        
        try:
            # Connect to FTP server
            async with aioftp.Client.context(
                guild_config["ftp_host"],
                guild_config["ftp_port"],
                user=guild_config["ftp_username"],
                password=guild_config["ftp_password"]
            ) as client:
                # Update status
                status_embed.title = "✅ Connected to FTP Server"
                status_embed.description = "Downloading files..."
                status_embed.color = discord.Color.green()
                await status_msg.edit(embed=status_embed)
                
                files_to_send = []
                failed_files = []
                
                # Download each file
                for file_path in guild_config["backup_paths"]:
                    try:
                        print(f"Attempting to download: {file_path}")
                        
                        # Get file info
                        file_info = await client.stat(file_path)
                        print(f"File info: {file_info}")
                        
                        # Check if it's a file (not a directory)
                        if file_info.get('type') == 'dir':
                            failed_files.append(f"`{file_path}` (not a file)")
                            continue
                        
                        # Log file info for debugging
                        file_size = file_info.get('size', 'unknown')
                        print(f"Downloading {file_path} (size: {file_size})")
                        
                        # Download file to temporary file
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_path = temp_file.name
                        
                        try:
                            # Use a simpler approach with BytesIO and download_stream
                            file_data = io.BytesIO()
                            
                            # Try to download using download_stream with a callback
                            def write_chunk(chunk):
                                file_data.write(chunk)
                            
                            await client.download_stream(file_path, write_chunk)
                            file_data.seek(0)
                            
                            # Check if we got any data
                            if file_data.getvalue() == b'':
                                raise Exception("Downloaded file is empty")
                                
                        except Exception as download_error:
                            import traceback
                            error_details = traceback.format_exc()
                            print(f"Download error for {file_path}: {error_details}")
                            # Truncate error message to avoid Discord embed limits
                            error_msg = str(download_error)
                            if len(error_msg) > 500:
                                error_msg = error_msg[:500] + "..."
                            raise Exception(f"Download failed: {error_msg}")
                        
                        # Get filename from path
                        filename = os.path.basename(file_path)
                        
                        files_to_send.append((filename, file_data))
                        
                        # Send individual success message
                        success_embed = discord.Embed(
                            title="✅ File Downloaded",
                            description=f"Successfully downloaded: `{filename}`",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=success_embed)
                        
                    except Exception as e:
                        failed_files.append(f"`{file_path}` ({str(e)})")
                        error_embed = discord.Embed(
                            title="❌ Download Failed",
                            description=f"Failed to download `{file_path}`: {str(e)}",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=error_embed)
                
                # Send files to Discord
                if files_to_send:
                    if guild_config["use_zip_file"] and len(files_to_send) > 1:
                        # Create zip file
                        zip_data = io.BytesIO()
                        with zipfile.ZipFile(zip_data, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for filename, file_data in files_to_send:
                                zip_file.writestr(filename, file_data.getvalue())
                        
                        zip_data.seek(0)
                        zip_file = discord.File(zip_data, filename="backup.zip")
                        
                        zip_embed = discord.Embed(
                            title="📦 Backup Complete",
                            description=f"Successfully backed up {len(files_to_send)} files as ZIP archive.",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=zip_embed, file=zip_file)
                    else:
                        # Send individual files
                        for filename, file_data in files_to_send:
                            discord_file = discord.File(file_data, filename=filename)
                            file_embed = discord.Embed(
                                title="📄 File Backup",
                                description=f"File: `{filename}`",
                                color=discord.Color.blue()
                            )
                            await ctx.send(embed=file_embed, file=discord_file)
                    
                    # Final status update
                    final_embed = discord.Embed(
                        title="✅ Backup Completed",
                        description=f"Successfully backed up {len(files_to_send)} files.",
                        color=discord.Color.green()
                    )
                    if failed_files:
                        final_embed.add_field(
                            name="Failed Files",
                            value="\n".join(failed_files),
                            inline=False
                        )
                    await status_msg.edit(embed=final_embed)
                else:
                    # No files downloaded
                    final_embed = discord.Embed(
                        title="❌ Backup Failed",
                        description="No files were downloaded successfully.",
                        color=discord.Color.red()
                    )
                    if failed_files:
                        final_embed.add_field(
                            name="Failed Files",
                            value="\n".join(failed_files),
                            inline=False
                        )
                    await status_msg.edit(embed=final_embed)
                    
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Connection Failed",
                description=f"Failed to connect to FTP server: {str(e)}",
                color=discord.Color.red()
            )
            await status_msg.edit(embed=error_embed)

    @commands.command(name="addbackuppath")
    @commands.has_permissions(administrator=True)
    async def add_backup_path(self, ctx: commands.Context, file_path: str):
        """Add a file path to the backup list."""
        async with self.config.guild(ctx.guild).backup_paths() as paths:
            if file_path not in paths:
                paths.append(file_path)
                embed = discord.Embed(
                    title="✅ Backup Path Added",
                    description=f"Added `{file_path}` to backup paths.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="⚠️ Path Already Exists",
                    description=f"`{file_path}` is already in the backup paths.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)

    @commands.command(name="removebackuppath")
    @commands.has_permissions(administrator=True)
    async def remove_backup_path(self, ctx: commands.Context, file_path: str):
        """Remove a file path from the backup list."""
        async with self.config.guild(ctx.guild).backup_paths() as paths:
            if file_path in paths:
                paths.remove(file_path)
                embed = discord.Embed(
                    title="✅ Backup Path Removed",
                    description=f"Removed `{file_path}` from backup paths.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="⚠️ Path Not Found",
                    description=f"`{file_path}` is not in the backup paths.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)

    @commands.command(name="listbackuppaths")
    @commands.has_permissions(administrator=True)
    async def list_backup_paths(self, ctx: commands.Context):
        """List all configured backup paths."""
        paths = await self.config.guild(ctx.guild).backup_paths()
        if paths:
            paths_text = "\n".join([f"• `{path}`" for path in paths])
            embed = discord.Embed(
                title="📝 Backup Paths",
                description=paths_text,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="📝 No Backup Paths",
                description="No backup paths configured.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

    @commands.command(name="usezipfile")
    @commands.has_permissions(administrator=True)
    async def use_zip_file(self, ctx: commands.Context, use_zip: bool):
        """Set whether to use ZIP files when sending multiple files."""
        await self.config.guild(ctx.guild).use_zip_file.set(use_zip)
        status = "enabled" if use_zip else "disabled"
        embed = discord.Embed(
            title="✅ ZIP Mode Updated",
            description=f"ZIP file mode has been {status}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ftpstatus")
    @commands.has_permissions(administrator=True)
    async def ftp_status(self, ctx: commands.Context):
        """Show current FTP configuration status."""
        config = await self.config.guild(ctx.guild).all()
        
        embed = discord.Embed(title="📊 FTP Configuration Status", color=discord.Color.blue())
        
        # FTP connection info
        ftp_info = f"**Host:** `{config['ftp_host'] or 'Not set'}`\n"
        ftp_info += f"**Port:** `{config['ftp_port']}`\n"
        ftp_info += f"**Username:** `{config['ftp_username'] or 'Not set'}`\n"
        ftp_info += f"**Password:** `{'*' * len(config['ftp_password']) if config['ftp_password'] else 'Not set'}`"
        
        embed.add_field(name="🔗 FTP Connection", value=ftp_info, inline=False)
        
        # Backup paths
        paths = config['backup_paths']
        if paths:
            paths_text = "\n".join([f"• `{path}`" for path in paths])
        else:
            paths_text = "No paths configured"
        
        embed.add_field(name="📁 Backup Paths", value=paths_text, inline=False)
        
        # ZIP setting
        zip_status = "✅ Enabled" if config['use_zip_file'] else "❌ Disabled"
        embed.add_field(name="📦 ZIP Mode", value=zip_status, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="testftp")
    @commands.has_permissions(administrator=True)
    async def test_ftp(self, ctx: commands.Context):
        """Test the FTP connection."""
        guild_config = await self.config.guild(ctx.guild).all()
        
        if not guild_config["ftp_host"] or not guild_config["ftp_username"]:
            embed = discord.Embed(
                title="❌ FTP Not Configured",
                description="Please configure FTP settings first using:\n"
                           "• `setftphost <host>`\n"
                           "• `setftpport <port>`\n"
                           "• `setftpusername <username>`\n"
                           "• `setftppassword <password>`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        status_embed = discord.Embed(
            title="🔄 Testing FTP Connection",
            description="Attempting to connect to the FTP server...",
            color=discord.Color.blue()
        )
        status_msg = await ctx.send(embed=status_embed)
        
        try:
            async with aioftp.Client.context(
                guild_config["ftp_host"],
                guild_config["ftp_port"],
                user=guild_config["ftp_username"],
                password=guild_config["ftp_password"]
            ) as client:
                # Test connection by listing root directory
                files = []
                async for file_info in client.list():
                    # file_info is a tuple, first element is the filename
                    files.append(file_info[0])
                
                success_embed = discord.Embed(
                    title="✅ FTP Connection Successful",
                    description=f"Successfully connected to FTP server.\n"
                               f"Found {len(files)} items in root directory.",
                    color=discord.Color.green()
                )
                if files:
                    files_text = "\n".join([f"• `{file}`" for file in files[:10]])  # Show first 10
                    if len(files) > 10:
                        files_text += f"\n... and {len(files) - 10} more"
                    success_embed.add_field(name="📁 Root Directory Contents", value=files_text, inline=False)
                
                await status_msg.edit(embed=success_embed)
                
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ FTP Connection Failed",
                description=f"Failed to connect to FTP server: {str(e)}",
                color=discord.Color.red()
            )
            await status_msg.edit(embed=error_embed) 