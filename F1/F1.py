"""
F1 Cog - Formula 1 data and statistics using OpenF1 API
Provides real-time and historical F1 data including driver info, lap times, car telemetry, and more.
"""

import discord
from discord.ext import commands
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from typing import Optional, List, Dict, Any
import math


class F1(commands.Cog):
    """Formula 1 data and statistics using OpenF1 API."""
    
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://api.openf1.org/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def cog_load(self):
        """Initialize the aiohttp session when the cog loads."""
        self.session = aiohttp.ClientSession()
        
    async def cog_unload(self):
        """Close the aiohttp session when the cog unloads."""
        if self.session:
            await self.session.close()
            
    async def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> List[Dict]:
        """Fetch data from the OpenF1 API."""
        if not self.session:
            return []
            
        url = f"{self.base_url}/{endpoint}"
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return []
        except Exception as e:
            print(f"Error fetching data from {endpoint}: {e}")
            return []

    @commands.command(name="f1driver")
    async def f1driver(self, ctx, driver_number: int):
        """Get information about a specific F1 driver by their number."""
        async with ctx.typing():
            data = await self.fetch_data("drivers", {"driver_number": driver_number})
            
            if not data:
                await ctx.send(f"❌ No driver found with number {driver_number}")
                return
                
            driver = data[0]  # Get the first (and should be only) result
            
            embed = discord.Embed(
                title=f"🏎️ {driver['full_name']}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Driver Number", value=f"#{driver['driver_number']}", inline=True)
            embed.add_field(name="Team", value=driver['team_name'], inline=True)
            embed.add_field(name="Country", value=driver['country_code'], inline=True)
            embed.add_field(name="Acronym", value=driver['name_acronym'], inline=True)
            
            if driver.get('headshot_url'):
                embed.set_thumbnail(url=driver['headshot_url'])
                
            embed.set_footer(text="Data from OpenF1 API")
            await ctx.send(embed=embed)

    @commands.command(name="f1drivers")
    async def f1drivers(self, ctx, session_key: str = "latest"):
        """Get all drivers for a specific session."""
        async with ctx.typing():
            data = await self.fetch_data("drivers", {"session_key": session_key})
            
            if not data:
                await ctx.send("❌ No drivers found for this session")
                return
                
            embed = discord.Embed(
                title="🏎️ F1 Drivers",
                description=f"Session: {session_key}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            # Group drivers by team
            teams = {}
            for driver in data:
                team = driver['team_name']
                if team not in teams:
                    teams[team] = []
                teams[team].append(driver)
            
            for team, drivers in teams.items():
                driver_list = []
                for driver in drivers:
                    driver_list.append(f"#{driver['driver_number']} {driver['full_name']} ({driver['country_code']})")
                
                embed.add_field(
                    name=f"🏁 {team}",
                    value="\n".join(driver_list),
                    inline=False
                )
                
            embed.set_footer(text="Data from OpenF1 API")
            await ctx.send(embed=embed)

    @commands.command(name="f1sessions")
    async def f1sessions(self, ctx, year: int = None):
        """Get F1 sessions for a specific year (defaults to current year)."""
        async with ctx.typing():
            params = {}
            if year:
                params["year"] = year
                
            data = await self.fetch_data("sessions", params)
            
            if not data:
                await ctx.send("❌ No sessions found")
                return
                
            # Limit to recent sessions
            recent_sessions = data[-10:]  # Last 10 sessions
            
            embed = discord.Embed(
                title="🏁 F1 Sessions",
                description=f"Recent sessions{f' for {year}' if year else ''}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            for session in recent_sessions:
                session_date = datetime.fromisoformat(session['date_start'].replace('Z', '+00:00'))
                embed.add_field(
                    name=f"🏆 {session['session_name']}",
                    value=f"**Meeting:** {session['meeting_name']}\n"
                          f"**Date:** {session_date.strftime('%Y-%m-%d %H:%M UTC')}\n"
                          f"**Key:** {session['session_key']}",
                    inline=False
                )
                
            embed.set_footer(text="Data from OpenF1 API")
            await ctx.send(embed=embed)

    @commands.command(name="f1laps")
    async def f1laps(self, ctx, session_key: str, driver_number: int = None):
        """Get lap data for a session, optionally filtered by driver."""
        async with ctx.typing():
            params = {"session_key": session_key}
            if driver_number:
                params["driver_number"] = driver_number
                
            data = await self.fetch_data("laps", params)
            
            if not data:
                await ctx.send("❌ No lap data found")
                return
                
            # Get driver info if driver_number is specified
            driver_info = None
            if driver_number:
                driver_data = await self.fetch_data("drivers", {"driver_number": driver_number, "session_key": session_key})
                if driver_data:
                    driver_info = driver_data[0]
            
            embed = discord.Embed(
                title="⏱️ F1 Lap Data",
                description=f"Session: {session_key}" + (f" | Driver: {driver_info['full_name']}" if driver_info else ""),
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            # Show best lap and some statistics
            valid_laps = [lap for lap in data if lap.get('lap_duration')]
            if valid_laps:
                best_lap = min(valid_laps, key=lambda x: x['lap_duration'])
                avg_lap = sum(lap['lap_duration'] for lap in valid_laps) / len(valid_laps)
                
                embed.add_field(
                    name="🏆 Best Lap",
                    value=f"Lap {best_lap['lap_number']}: {best_lap['lap_duration']:.3f}s",
                    inline=True
                )
                embed.add_field(
                    name="📊 Average Lap",
                    value=f"{avg_lap:.3f}s",
                    inline=True
                )
                embed.add_field(
                    name="📈 Total Laps",
                    value=str(len(valid_laps)),
                    inline=True
                )
                
            embed.set_footer(text="Data from OpenF1 API")
            await ctx.send(embed=embed)

    @commands.command(name="f1weather")
    async def f1weather(self, ctx, meeting_key: str = "latest"):
        """Get weather data for a meeting."""
        async with ctx.typing():
            data = await self.fetch_data("weather", {"meeting_key": meeting_key})
            
            if not data:
                await ctx.send("❌ No weather data found")
                return
                
            # Get the most recent weather data
            latest_weather = data[-1]
            
            embed = discord.Embed(
                title="🌤️ F1 Weather Data",
                description=f"Meeting: {meeting_key}",
                color=discord.Color.light_blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="🌡️ Air Temperature", value=f"{latest_weather['air_temperature']}°C", inline=True)
            embed.add_field(name="🔥 Track Temperature", value=f"{latest_weather['track_temperature']}°C", inline=True)
            embed.add_field(name="💧 Humidity", value=f"{latest_weather['humidity']}%", inline=True)
            embed.add_field(name="🌪️ Wind Speed", value=f"{latest_weather['wind_speed']} m/s", inline=True)
            embed.add_field(name="🧭 Wind Direction", value=f"{latest_weather['wind_direction']}°", inline=True)
            embed.add_field(name="🌧️ Rainfall", value="Yes" if latest_weather['rainfall'] else "No", inline=True)
            
            embed.set_footer(text="Data from OpenF1 API")
            await ctx.send(embed=embed)

    @commands.command(name="f1telemetry")
    async def f1telemetry(self, ctx, session_key: str, driver_number: int, speed_threshold: int = 300):
        """Get car telemetry data for a driver, showing high-speed moments."""
        async with ctx.typing():
            params = {
                "session_key": session_key,
                "driver_number": driver_number,
                "speed>=": speed_threshold
            }
            
            data = await self.fetch_data("car_data", params)
            
            if not data:
                await ctx.send(f"❌ No telemetry data found for driver {driver_number} at speeds >= {speed_threshold} km/h")
                return
                
            # Get driver info
            driver_data = await self.fetch_data("drivers", {"driver_number": driver_number, "session_key": session_key})
            driver_info = driver_data[0] if driver_data else None
            
            embed = discord.Embed(
                title="📊 F1 Car Telemetry",
                description=f"Driver: {driver_info['full_name'] if driver_info else f'#{driver_number}'}\n"
                           f"Speed threshold: {speed_threshold} km/h",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            # Show some interesting telemetry points
            for i, point in enumerate(data[:5]):  # Show first 5 high-speed moments
                embed.add_field(
                    name=f"🚗 Speed Point {i+1}",
                    value=f"**Speed:** {point['speed']} km/h\n"
                          f"**RPM:** {point['rpm']}\n"
                          f"**Gear:** {point['n_gear']}\n"
                          f"**Throttle:** {point['throttle']}%\n"
                          f"**DRS:** {point['drs']}",
                    inline=True
                )
                
            embed.set_footer(text="Data from OpenF1 API")
            await ctx.send(embed=embed)

    @commands.command(name="f1radio")
    async def f1radio(self, ctx, session_key: str, driver_number: int = None):
        """Get team radio messages for a session, optionally filtered by driver."""
        async with ctx.typing():
            params = {"session_key": session_key}
            if driver_number:
                params["driver_number"] = driver_number
                
            data = await self.fetch_data("team_radio", params)
            
            if not data:
                await ctx.send("❌ No radio messages found")
                return
                
            embed = discord.Embed(
                title="📻 F1 Team Radio",
                description=f"Session: {session_key}" + (f" | Driver: #{driver_number}" if driver_number else ""),
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            # Show recent radio messages
            for i, message in enumerate(data[-5:]):  # Show last 5 messages
                message_time = datetime.fromisoformat(message['date'].replace('Z', '+00:00'))
                embed.add_field(
                    name=f"📢 Radio Message {i+1}",
                    value=f"**Time:** {message_time.strftime('%H:%M:%S')}\n"
                          f"**Driver:** #{message['driver_number']}\n"
                          f"**Recording:** [Listen]({message['recording_url']})",
                    inline=False
                )
                
            embed.set_footer(text="Data from OpenF1 API")
            await ctx.send(embed=embed)

    @commands.command(name="f1help")
    async def f1help(self, ctx):
        """Show help for F1 commands."""
        embed = discord.Embed(
            title="🏎️ F1 Cog Help",
            description="Commands for Formula 1 data using OpenF1 API",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        commands_info = [
            ("f1driver <number>", "Get information about a specific F1 driver"),
            ("f1drivers [session_key]", "Get all drivers for a session (default: latest)"),
            ("f1sessions [year]", "Get F1 sessions for a year (default: current)"),
            ("f1laps <session_key> [driver_number]", "Get lap data for a session"),
            ("f1weather [meeting_key]", "Get weather data for a meeting (default: latest)"),
            ("f1telemetry <session_key> <driver_number> [speed_threshold]", "Get car telemetry data"),
            ("f1radio <session_key> [driver_number]", "Get team radio messages"),
            ("f1help", "Show this help message")
        ]
        
        for cmd, desc in commands_info:
            embed.add_field(name=f"!{cmd}", value=desc, inline=False)
            
        embed.add_field(
            name="📝 Notes",
            value="• Use 'latest' for session_key/meeting_key to get current data\n"
                  "• Speed threshold for telemetry defaults to 300 km/h\n"
                  "• All data comes from the OpenF1 API",
            inline=False
        )
        
        embed.set_footer(text="Data from OpenF1 API")
        await ctx.send(embed=embed)

    @f1driver.error
    @f1drivers.error
    @f1sessions.error
    @f1laps.error
    @f1weather.error
    @f1telemetry.error
    @f1radio.error
    async def f1_error_handler(self, ctx, error):
        """Handle errors for F1 commands."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided. Please check your input.")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")


async def setup(bot):
    """Add the F1 cog to the bot."""
    await bot.add_cog(F1(bot)) 