import discord
from discord import app_commands
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

    @commands.hybrid_command(name="setftpconfig")
    @commands.has_permissions(administrator=True)
    async def set_ftp_config(self, ctx: commands.Context):
        """Set FTP configuration using a modal window."""
        modal = FTPConfigModal(self.config, ctx.guild)
        await ctx.interaction.response.send_modal(modal)

    @commands.hybrid_command(name="ftpbackup")
    @commands.has_permissions(administrator=True)
    async def ftp_backup(self, ctx: commands.Context):
        """Backup files from FTP server to the current Discord channel."""
        # Get configuration
        guild_config = await self.config.guild(ctx.guild).all()
        
        # Check if FTP is configured
        if not guild_config["ftp_host"] or not guild_config["ftp_username"]:
            await ctx.send("❌ FTP configuration is not set. Use `/setftpconfig` first.")
            return
        
        # Check if backup paths are configured
        if not guild_config["backup_paths"]:
            await ctx.send("❌ No backup paths configured. Use `/addbackuppath` to add files to backup.")
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
                await status_msg.edit(content="✅ Connected to FTP server. Downloading files...")
                
                files_to_send = []
                
                # Download each file
                for file_path in guild_config["backup_paths"]:
                    try:
                        # Get file info
                        file_info = await client.stat(file_path)
                        if not file_info.is_file():
                            await ctx.send(f"⚠️ Path `{file_path}` is not a file, skipping...")
                            continue
                        
                        # Download file
                        file_data = io.BytesIO()
                        await client.download_stream(file_path, file_data)
                        file_data.seek(0)
                        
                        # Get filename from path
                        filename = os.path.basename(file_path)
                        
                        files_to_send.append((filename, file_data))
                        await ctx.send(f"✅ Downloaded: `{filename}`")
                        
                    except Exception as e:
                        await ctx.send(f"❌ Failed to download `{file_path}`: {str(e)}")
                
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
                        await ctx.send("📦 Sending files as ZIP archive:", file=zip_file)
                    else:
                        # Send individual files
                        for filename, file_data in files_to_send:
                            discord_file = discord.File(file_data, filename=filename)
                            await ctx.send(f"📄 File: `{filename}`", file=discord_file)
                    
                    await status_msg.edit(content="✅ Backup completed successfully!")
                else:
                    await status_msg.edit(content="❌ No files were downloaded successfully.")
                    
        except Exception as e:
            await status_msg.edit(content=f"❌ Failed to connect to FTP server: {str(e)}")

    @commands.hybrid_command(name="addbackuppath")
    @commands.has_permissions(administrator=True)
    async def add_backup_path(self, ctx: commands.Context, file_path: str):
        """Add a file path to the backup list."""
        async with self.config.guild(ctx.guild).backup_paths() as paths:
            if file_path not in paths:
                paths.append(file_path)
                await ctx.send(f"✅ Added `{file_path}` to backup paths.")
            else:
                await ctx.send(f"⚠️ `{file_path}` is already in the backup paths.")

    @commands.hybrid_command(name="removebackuppath")
    @commands.has_permissions(administrator=True)
    async def remove_backup_path(self, ctx: commands.Context, file_path: str):
        """Remove a file path from the backup list."""
        async with self.config.guild(ctx.guild).backup_paths() as paths:
            if file_path in paths:
                paths.remove(file_path)
                await ctx.send(f"✅ Removed `{file_path}` from backup paths.")
            else:
                await ctx.send(f"⚠️ `{file_path}` is not in the backup paths.")

    @commands.hybrid_command(name="listbackuppaths")
    @commands.has_permissions(administrator=True)
    async def list_backup_paths(self, ctx: commands.Context):
        """List all configured backup paths."""
        paths = await self.config.guild(ctx.guild).backup_paths()
        if paths:
            paths_text = "\n".join([f"• `{path}`" for path in paths])
            embed = discord.Embed(title="Backup Paths", description=paths_text, color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            await ctx.send("📝 No backup paths configured.")

    @commands.hybrid_command(name="usezipfile")
    @commands.has_permissions(administrator=True)
    async def use_zip_file(self, ctx: commands.Context, use_zip: bool):
        """Set whether to use ZIP files when sending multiple files."""
        await self.config.guild(ctx.guild).use_zip_file.set(use_zip)
        status = "enabled" if use_zip else "disabled"
        await ctx.send(f"✅ ZIP file mode {status}.")

    @commands.hybrid_command(name="ftpstatus")
    @commands.has_permissions(administrator=True)
    async def ftp_status(self, ctx: commands.Context):
        """Show current FTP configuration status."""
        config = await self.config.guild(ctx.guild).all()
        
        embed = discord.Embed(title="FTP Configuration Status", color=discord.Color.blue())
        
        # FTP connection info
        ftp_info = f"Host: `{config['ftp_host'] or 'Not set'}`\n"
        ftp_info += f"Port: `{config['ftp_port']}`\n"
        ftp_info += f"Username: `{config['ftp_username'] or 'Not set'}`\n"
        ftp_info += f"Password: `{'*' * len(config['ftp_password']) if config['ftp_password'] else 'Not set'}`"
        
        embed.add_field(name="FTP Connection", value=ftp_info, inline=False)
        
        # Backup paths
        paths = config['backup_paths']
        if paths:
            paths_text = "\n".join([f"• `{path}`" for path in paths])
        else:
            paths_text = "No paths configured"
        
        embed.add_field(name="Backup Paths", value=paths_text, inline=False)
        
        # ZIP setting
        zip_status = "Enabled" if config['use_zip_file'] else "Disabled"
        embed.add_field(name="ZIP Mode", value=zip_status, inline=False)
        
        await ctx.send(embed=embed)

class FTPConfigModal(discord.ui.Modal, title="FTP Configuration"):
    def __init__(self, config: Config, guild: discord.Guild):
        super().__init__()
        self.config = config
        self.guild = guild

    host = discord.ui.TextInput(
        label="FTP Host",
        placeholder="ftp.example.com",
        required=True,
        max_length=255
    )

    port = discord.ui.TextInput(
        label="FTP Port",
        placeholder="21",
        required=True,
        default="21",
        max_length=5
    )

    username = discord.ui.TextInput(
        label="FTP Username",
        placeholder="username",
        required=True,
        max_length=100
    )

    password = discord.ui.TextInput(
        label="FTP Password",
        placeholder="password",
        required=True,
        max_length=100,
        style=discord.TextStyle.password
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            port = int(self.port.value)
            if port <= 0 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        except ValueError:
            await interaction.response.send_message("❌ Invalid port number. Please use a number between 1 and 65535.", ephemeral=True)
            return

        # Save configuration
        await self.config.guild(self.guild).ftp_host.set(self.host.value)
        await self.config.guild(self.guild).ftp_port.set(port)
        await self.config.guild(self.guild).ftp_username.set(self.username.value)
        await self.config.guild(self.guild).ftp_password.set(self.password.value)

        embed = discord.Embed(
            title="✅ FTP Configuration Saved",
            description="Your FTP configuration has been updated successfully.",
            color=discord.Color.green()
        )
        embed.add_field(name="Host", value=self.host.value, inline=True)
        embed.add_field(name="Port", value=str(port), inline=True)
        embed.add_field(name="Username", value=self.username.value, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True) 