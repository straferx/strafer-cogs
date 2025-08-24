"""
F1 Cog - Formula 1 data and statistics using OpenF1 API
Provides real-time and historical F1 data including driver info, lap times, car telemetry, and more.
"""

import discord
from redbot.core import commands
from redbot.core.bot import Red
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from typing import Optional, List, Dict, Any
import math


class F1(commands.Cog):
    """Formula 1 data and statistics using OpenF1 API."""
    
    def __init__(self, bot: Red):
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

    @commands.command(name="f1")
    async def f1_overview(self, ctx):
        """Show current F1 overview with recent/upcoming sessions and useful stats."""
        async with ctx.typing():
            # Get current year sessions
            current_year = datetime.now().year
            data = await self.fetch_data("sessions", {"year": current_year})
            
            if not data:
                await ctx.send("❌ No F1 sessions found for this year")
                return
            
            # Sort sessions by date
            for session in data:
                session['date_start'] = datetime.fromisoformat(session['date_start'].replace('Z', '+00:00'))
            
            data.sort(key=lambda x: x['date_start'])
            
            # Get upcoming and recent sessions
            now = datetime.now().replace(tzinfo=None)
            upcoming_sessions = [s for s in data if s['date_start'] > now][:5]
            recent_sessions = [s for s in data if s['date_start'] <= now][-3:]
            
            embed = discord.Embed(
                title="🏎️ Formula 1 Overview",
                description=f"Current season: {current_year}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            # Show upcoming sessions
            if upcoming_sessions:
                upcoming_text = ""
                for session in upcoming_sessions:
                    time_until = session['date_start'] - now
                    days = time_until.days
                    hours = time_until.seconds // 3600
                    
                    if days > 0:
                        time_str = f"{days}d {hours}h"
                    else:
                        time_str = f"{hours}h"
                    
                    upcoming_text += f"**{session['session_name']}** - {session['meeting_name']}\n"
                    upcoming_text += f"📅 {session['date_start'].strftime('%Y-%m-%d %H:%M UTC')}\n"
                    upcoming_text += f"⏰ In {time_str} | 🔑 `{session['session_key']}`\n\n"
                
                embed.add_field(
                    name="🔄 Upcoming Sessions",
                    value=upcoming_text,
                    inline=False
                )
            
            # Show recent sessions
            if recent_sessions:
                recent_text = ""
                for session in recent_sessions:
                    recent_text += f"**{session['session_name']}** - {session['meeting_name']}\n"
                    recent_text += f"📅 {session['date_start'].strftime('%Y-%m-%d %H:%M UTC')}\n"
                    recent_text += f"🔑 `{session['session_key']}`\n\n"
                
                embed.add_field(
                    name="📊 Recent Sessions",
                    value=recent_text,
                    inline=False
                )
            
            # Add usage tips
            embed.add_field(
                name="💡 Quick Commands",
                value="• `f1driver <number>` - Get driver info\n"
                      "• `f1drivers latest` - Current session drivers\n"
                      "• `f1laps <session_key> [driver]` - Lap data\n"
                      "• `f1weather latest` - Current weather\n"
                      "• `f1telemetry <session_key> <driver> [speed]` - Car data\n"
                      "• `f1radio <session_key> [driver]` - Team radio",
                inline=False
            )
            
            embed.set_footer(text="Data from OpenF1 API • Use session keys from above for detailed commands")
            await ctx.send(embed=embed)

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



    @f1.error
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


 