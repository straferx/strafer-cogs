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

class Ftpsync(commands.Cog):
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
            split_large_files=False
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
        status_msg = await ctx.send("🔄 Connecting to FTP server...")
        
        try:
            # Connect to FTP server
            async with aioftp.Client.context(
                guild_config["ftp_host"],
                guild_config["ftp_port"],
                user=guild_config["ftp_username"],
                password=guild_config["ftp_password"]
            ) as client:
                # Update status
                await status_msg.edit(content="✅ Connected to FTP server. Downloading files...")
                
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
                            # Use ftplib for download instead of aioftp
                            import ftplib
                            import tempfile
                            import os
                            
                            # Create a temporary file
                            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                                temp_path = temp_file.name
                            
                            try:
                                # Use ftplib to download
                                ftp = ftplib.FTP()
                                ftp.connect(guild_config["ftp_host"], guild_config["ftp_port"])
                                ftp.login(guild_config["ftp_username"], guild_config["ftp_password"])
                                
                                with open(temp_path, 'wb') as f:
                                    ftp.retrbinary(f'RETR {file_path}', f.write)
                                
                                ftp.quit()
                                
                                # Check if file was downloaded
                                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                                    raise Exception("File download failed or file is empty")
                                
                                # Read into BytesIO
                                file_data = io.BytesIO()
                                with open(temp_path, 'rb') as f:
                                    file_data.write(f.read())
                                file_data.seek(0)
                                
                            finally:
                                # Clean up temp file
                                if os.path.exists(temp_path):
                                    try:
                                        os.unlink(temp_path)
                                    except:
                                        pass  # Ignore cleanup errors
                                    
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
                        
                        # Send simple success message
                        await ctx.send(f"✅ Downloaded: `{filename}`")
                        
                    except Exception as e:
                        failed_files.append(f"`{file_path}` ({str(e)})")
                        await ctx.send(f"❌ Failed to download `{file_path}`: {str(e)}")
                
                # Send files to Discord
                if files_to_send:
                    # Always create a ZIP archive with all files
                    zip_data = io.BytesIO()
                    with zipfile.ZipFile(zip_data, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
                        for filename, file_data in files_to_send:
                            zip_file.writestr(filename, file_data.getvalue())
                    
                    zip_data.seek(0)
                    zip_size = len(zip_data.getvalue())
                    zip_size_mb = zip_size / (1024 * 1024)
                    
                    # Check if ZIP is too large
                    max_size = 25 * 1024 * 1024  # 25MB limit
                    
                    if zip_size <= max_size:
                        # Send ZIP file
                        zip_file = discord.File(zip_data, filename="backup.zip")
                        await ctx.send(f"📦 Backup complete! {len(files_to_send)} files in backup.zip ({zip_size_mb:.1f}MB)", file=zip_file)
                    else:
                        # ZIP is too large, try individual compression or splitting
                        await ctx.send(f"⚠️ ZIP archive is too large ({zip_size_mb:.1f}MB). Trying individual file compression...")
                        
                        for filename, file_data in files_to_send:
                            file_size = len(file_data.getvalue())
                            file_size_mb = file_size / (1024 * 1024)
                            
                            if file_size > max_size:
                                # Try to compress individual file
                                try:
                                    compressed_data = io.BytesIO()
                                    with zipfile.ZipFile(compressed_data, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
                                        zip_file.writestr(filename, file_data.getvalue())
                                    
                                    compressed_data.seek(0)
                                    compressed_size = len(compressed_data.getvalue())
                                    compressed_mb = compressed_size / (1024 * 1024)
                                    
                                    if compressed_size <= max_size:
                                        # Send compressed file
                                        discord_file = discord.File(compressed_data, filename=f"{filename}.zip")
                                        await ctx.send(f"📦 Compressed: `{filename}` → `{filename}.zip` ({file_size_mb:.1f}MB → {compressed_mb:.1f}MB)", file=discord_file)
                                    else:
                                        # File is still too large, try splitting
                                        if guild_config.get("split_large_files", False):
                                            # Split the file into chunks
                                            chunk_size = 20 * 1024 * 1024  # 20MB chunks
                                            file_bytes = file_data.getvalue()
                                            total_chunks = (len(file_bytes) + chunk_size - 1) // chunk_size
                                            
                                            for i in range(total_chunks):
                                                start = i * chunk_size
                                                end = min(start + chunk_size, len(file_bytes))
                                                chunk_data = file_bytes[start:end]
                                                
                                                chunk_filename = f"{filename}.part{i+1:03d}of{total_chunks:03d}"
                                                chunk_io = io.BytesIO(chunk_data)
                                                
                                                discord_file = discord.File(chunk_io, filename=chunk_filename)
                                                chunk_embed = discord.Embed(
                                                    title="📄 File Chunk",
                                                    description=f"File: `{filename}` - Part {i+1} of {total_chunks}\n"
                                                               f"Size: {(len(chunk_data) / 1024 / 1024):.1f}MB",
                                                    color=discord.Color.purple()
                                                )
                                                await ctx.send(embed=chunk_embed, file=discord_file)
                                        else:
                                            await ctx.send(f"⚠️ File `{filename}` is too large ({file_size_mb:.1f}MB) even after compression ({compressed_mb:.1f}MB).\n"
                                                          f"Enable file splitting with `splitlargefiles true` to split large files into chunks.")
                                            
                                except Exception as compress_error:
                                    await ctx.send(f"⚠️ File `{filename}` is too large ({file_size_mb:.1f}MB) and compression failed: {str(compress_error)}")
                            else:
                                # File is small enough, send normally
                                try:
                                    discord_file = discord.File(file_data, filename=filename)
                                    file_embed = discord.Embed(
                                        title="📄 File Backup",
                                        description=f"File: `{filename}` ({file_size_mb:.1f}MB)",
                                        color=discord.Color.blue()
                                    )
                                    await ctx.send(embed=file_embed, file=discord_file)
                                except Exception as send_error:
                                    await ctx.send(f"❌ Failed to send `{filename}`: {str(send_error)}")
                    
                    # Final status update
                    final_embed = discord.Embed(
                        title="✅ Backup Completed",
                        description=f"Successfully backed up {len(files_to_send)} files.",
                        color=discord.Color.green()
                    )
                    if failed_files:
                        # Truncate failed files list if too long
                        failed_text = "\n".join(failed_files)
                        if len(failed_text) > 1000:
                            failed_text = failed_text[:1000] + "..."
                        final_embed.add_field(
                            name="Failed Files",
                            value=failed_text,
                            inline=False
                        )
                    await status_msg.edit(content="✅ Backup completed successfully!")
                else:
                    # No files downloaded
                    await status_msg.edit(content="❌ No files were downloaded successfully.")
                    
        except Exception as e:
            await status_msg.edit(content=f"❌ Failed to connect to FTP server: {str(e)}")

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
        embed.add_field(name="📦 ZIP Mode", value="Always Enabled", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="splitlargefiles")
    @commands.has_permissions(administrator=True)
    async def split_large_files(self, ctx: commands.Context, enabled: bool):
        """Enable or disable automatic splitting of large files into chunks."""
        await self.config.guild(ctx.guild).split_large_files.set(enabled)
        status = "enabled" if enabled else "disabled"
        embed = discord.Embed(
            title="✅ Large File Splitting Updated",
            description=f"Large file splitting has been {status}.",
            color=discord.Color.green()
        )
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
